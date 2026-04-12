# -*- coding: utf-8 -*-
"""Wiki Ingest 编译服务

把一份原始文件通过 Claude Opus 编译为结构化 Wiki 文章。

核心流程：
    1. 读 raw 文件纯文本
    2. 读当前 index.md
    3. 读同 topic 下的所有相关文章全文
    4. 组装 user prompt → 调 Opus
    5. 解析 Claude 返回的 JSON
    6. 按 operations 执行 create/update/noop
    7. 覆盖写 index.md，追加 log.md
    8. 更新 KnowledgeRawFile.ingest_status

**级联更新**：Claude 可以在 operations 里同时产出多篇文章的新版本，
这是 Karpathy 方案的核心价值（一份新资料可能影响多篇既有文章）。

v1 简化：相关文章范围 = 同 topic 下所有文章。未来如果 Wiki 变大，
可以按 title/summary 的全文检索相似度先粗筛。
"""
import json
import logging
from datetime import datetime
from typing import Any

from app import db
from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle
from app.services.wiki import claude_client, prompts, storage
from app.services.wiki.paths import ensure_wiki_structure

logger = logging.getLogger(__name__)


class IngestError(RuntimeError):
    """Ingest 过程中的可预期错误"""


# 每篇原始文本最多塞进 prompt 的字符数，避免超上下文
MAX_RAW_TEXT_CHARS = 200_000


# ══════════════════════════════════════════════════════════════════
# 公开入口
# ══════════════════════════════════════════════════════════════════

def ingest_raw_file(
    raw_file_id: int,
    *,
    claude: claude_client.WikiClaudeClient | None = None,
) -> dict:
    """把一个原始文件编译入 Wiki。

    事务语义（修复 C3）：
    - 所有 DB 变更在**单次 commit** 里完成，_apply_operations 本身不 commit
    - 如果中途失败：
      * DB 自动 rollback（SQLAlchemy session）
      * 新创建的磁盘文件会被 unlink 撤销
      * 被更新的磁盘文件会从内存备份恢复
      * raw.ingest_status 单独开一个事务标记为 'error'

    并发安全（修复 I1）：用 SELECT FOR UPDATE 行锁，拒绝重复 ingest。

    Args:
        raw_file_id: KnowledgeRawFile.id
        claude: 可选的 Claude 客户端实例；**测试时传 mock**。
                生产调用不传，内部自行创建和关闭。

    Returns:
        {
            'raw_id': int,
            'operations': [ {action, topic, slug, ...}, ... ],
            'index_updated': bool,
            'usage': {'input_tokens': int, 'output_tokens': int, 'model': str},
        }

    Raises:
        IngestError: 记录不存在、已在编译中、文件读取失败、Claude 返回非法 JSON 等
    """
    # 并发锁 + 存在性检查
    raw = (
        KnowledgeRawFile.query
        .filter_by(id=raw_file_id)
        .with_for_update()
        .first()
    )
    if not raw:
        raise IngestError(f'KnowledgeRawFile id={raw_file_id} 不存在')
    if raw.ingest_status == 'processing':
        raise IngestError('该资料已经在编译中，请稍候再试')

    raw.ingest_status = 'processing'
    raw.ingest_error = None
    db.session.commit()

    own_client = False
    claude_instance = claude

    # 所有可能产生副作用的磁盘写入都记录下来，以便异常时撤销
    rollback_state: dict = {
        'created_files': [],        # List[str] — 需要 unlink 的相对路径
        'updated_backups': {},      # Dict[str, str] — 相对路径 → 旧正文
        'old_index': None,          # 旧 index.md 内容（str），便于恢复
    }

    try:
        ensure_wiki_structure()

        # 先备份当前 index.md，便于失败回滚
        rollback_state['old_index'] = storage.read_index()

        # Claude 客户端构造放在 try: 内（修复 C2）
        if claude_instance is None:
            claude_instance = claude_client.WikiClaudeClient()
            own_client = True

        # 1. 读原始文件内容（自动判断 text 或 vision 模式）
        try:
            raw_content = storage.extract_raw_file_content(raw.raw_path)
        except Exception as e:
            raise IngestError(f'读取原始文件失败: {e}') from e

        is_vision = raw_content.content_type == 'images'

        if not is_vision:
            if not raw_content.text.strip():
                raise IngestError('原始文件内容为空或无法提取文本')
            raw_text = raw_content.text[:MAX_RAW_TEXT_CHARS]
            truncated = len(raw_content.text) > MAX_RAW_TEXT_CHARS
            if truncated:
                logger.warning(
                    f'[Ingest] raw {raw.id} 文本 {len(raw_content.text)} 字符超上限 {MAX_RAW_TEXT_CHARS}，已截断'
                )
        else:
            raw_text = ''
            truncated = raw_content.extracted_pages < raw_content.total_pages
            if not raw_content.images:
                raise IngestError('PDF 扫描件无法提取任何页面图片')
            logger.info(
                f'[Ingest] raw {raw.id} Vision 模式: {raw_content.extracted_pages}/{raw_content.total_pages} 页'
            )

        # 2. 当前 index.md
        index_md = rollback_state['old_index']

        # 3. 同 topic 下的相关文章（v1 粗筛）
        related_articles = (
            KnowledgeWikiArticle.query
            .filter_by(topic=raw.topic)
            .order_by(KnowledgeWikiArticle.slug)
            .all()
        )
        related_context = []
        for art in related_articles:
            content = storage.read_article_content(art.file_path)
            related_context.append({
                'topic': art.topic,
                'slug': art.slug,
                'title': art.title,
                'content': content,
            })

        # 4. 组装 user prompt（text 或 vision 模式）
        raw_filename = raw.raw_path.rsplit('/', 1)[-1] if raw.raw_path else raw.title
        raw_meta = {
            'raw_id': raw.id,
            'topic': raw.topic,
            'filename': raw_filename,
            'title': raw.title,
            'truncated': truncated,
            'vision_mode': is_vision,
        }

        if is_vision:
            # Vision 模式：user message 是 content blocks 列表（text + images 混合）
            user_msg = _build_ingest_vision_prompt(
                raw_meta=raw_meta,
                images=raw_content.images,
                index_md=index_md,
                related_articles=related_context,
            )
        else:
            # Text 模式：user message 是纯字符串
            user_msg = _build_ingest_user_prompt(
                raw_meta=raw_meta,
                raw_text=raw_text,
                index_md=index_md,
                related_articles=related_context,
            )

        # 5. 调 Opus
        logger.info(
            f'[Ingest] raw_id={raw.id} topic={raw.topic} 相关文章数={len(related_context)} '
            f'mode={"vision" if is_vision else "text"} '
            f'{"images=" + str(len(raw_content.images)) + "p" if is_vision else "text=" + str(len(raw_text)) + "B"}'
        )
        resp = claude_instance.complete(
            system=prompts.INGEST_SYSTEM,
            user=user_msg,
            model=claude_client.INGEST_MODEL,
            max_tokens=32000,
        )

        # 6. 解析 JSON
        result = _parse_ingest_response(resp.text)

        # 7. 预校验所有 op 的 topic/slug，避免写一半发现非法
        operations = result.get('operations') or []
        for i, op in enumerate(operations):
            action = (op.get('action') or '').lower()
            if action == 'noop':
                continue
            try:
                storage.validate_topic_slug(op.get('topic', ''), op.get('slug', ''))
            except storage.WikiPathError as e:
                raise IngestError(f'Claude 返回的 operations[{i}] 非法: {e}') from e

        # 8. 应用 operations（追踪 rollback 状态，但不 commit）
        _apply_operations(operations, raw_id=raw.id, rollback_state=rollback_state)

        # 9. 写 index.md（记入 rollback_state 以便失败恢复）
        index_updated = False
        new_index = result.get('index_update')
        if new_index:
            storage.write_index(new_index)
            index_updated = True

        # 10. 追加 log.md（失败也保留，这个不回滚）
        log_entry = result.get('log_entry') or ''
        storage.append_log(
            'ingest',
            f'- raw_id={raw.id} title={raw.title!r} topic={raw.topic}\n'
            f'- operations: {len(operations)}\n'
            f'- {log_entry}',
        )

        # 11. 单次 commit：合并 _apply_operations 的 stage 和 raw 状态（修复 I4）
        raw.ingest_status = 'ingested'
        raw.ingested_at = datetime.utcnow()
        raw.ingest_error = None
        db.session.commit()

        logger.info(
            f'[Ingest] raw_id={raw.id} 完成，ops={len(operations)}, '
            f'usage in={resp.usage["input_tokens"]} out={resp.usage["output_tokens"]}'
        )

        return {
            'raw_id': raw.id,
            'operations': operations,
            'index_updated': index_updated,
            'usage': resp.usage,
        }

    except Exception as e:
        # ── 1. DB 回滚（撤销 _apply_operations 里的 session 变更）
        db.session.rollback()

        # ── 2. 磁盘回滚（撤销已创建和已修改的文件）
        _rollback_file_changes(rollback_state)

        # ── 3. 单独事务标记 raw 为 error，让前端能看到失败原因
        try:
            raw_err = db.session.get(KnowledgeRawFile, raw_file_id)
            if raw_err is not None:
                raw_err.ingest_status = 'error'
                raw_err.ingest_error = str(e)[:2000]
                db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception(f'[Ingest] raw_id={raw_file_id} 标记 error 状态失败')

        logger.exception(f'[Ingest] raw_id={raw_file_id} 失败')
        raise
    finally:
        if own_client and claude_instance is not None:
            claude_instance.close()


def _rollback_file_changes(rollback_state: dict):
    """失败回滚：删除新建的文件，恢复被修改的文件和 index.md。"""
    from app.services.wiki.paths import get_wiki_root

    root = get_wiki_root()

    for rel_path in rollback_state.get('created_files') or []:
        try:
            (root / rel_path).unlink(missing_ok=True)
            logger.info(f'[Ingest rollback] 删除新建文件: {rel_path}')
        except Exception:
            logger.exception(f'[Ingest rollback] 删除文件失败: {rel_path}')

    for rel_path, old_content in (rollback_state.get('updated_backups') or {}).items():
        try:
            (root / rel_path).write_text(old_content, encoding='utf-8')
            logger.info(f'[Ingest rollback] 恢复更新前文件: {rel_path}')
        except Exception:
            logger.exception(f'[Ingest rollback] 恢复文件失败: {rel_path}')

    old_index = rollback_state.get('old_index')
    if old_index is not None:
        try:
            storage.write_index(old_index)
        except Exception:
            logger.exception('[Ingest rollback] 恢复 index.md 失败')


# ══════════════════════════════════════════════════════════════════
# 内部：prompt 组装
# ══════════════════════════════════════════════════════════════════

def _build_ingest_user_prompt(
    *,
    raw_meta: dict,
    raw_text: str,
    index_md: str,
    related_articles: list[dict],
) -> str:
    """构造传给 Claude 的 user 消息（纯文本模式，Markdown 章节格式）。"""
    parts: list[str] = []

    parts.append('## 原始资料元数据')
    parts.append('```json')
    parts.append(json.dumps(raw_meta, ensure_ascii=False, indent=2))
    parts.append('```')
    parts.append('')

    parts.append('## 原始资料正文')
    parts.append(raw_text)
    parts.append('')

    parts.append('## 当前 index.md')
    parts.append(index_md if index_md.strip() else '（空索引，本次可能是首次编译）')
    parts.append('')

    parts.append('## 相关已有文章')
    if not related_articles:
        parts.append('（该 topic 下暂无已有文章，本次编译可以自由新建）')
    else:
        for art in related_articles:
            parts.append(f'### {art["topic"]}/{art["slug"]}.md — {art["title"]}')
            parts.append('')
            parts.append(art['content'] or '（空文件）')
            parts.append('')

    return '\n'.join(parts)


def _build_ingest_vision_prompt(
    *,
    raw_meta: dict,
    images: list[dict],
    index_md: str,
    related_articles: list[dict],
) -> list[dict]:
    """构造传给 Claude 的 user 消息（Vision 模式，content blocks 列表）。

    对于扫描件 PDF，把每页 PNG 作为 image block 传给 Claude Opus，
    让 Vision 能力直接读取图片内容。文字上下文（index.md、已有文章）
    仍用 text block。

    返回 Anthropic messages API 的 content 列表格式。
    """
    blocks: list[dict] = []

    # 元数据（text block）
    meta_text = (
        '## 原始资料元数据\n\n'
        '```json\n'
        + json.dumps(raw_meta, ensure_ascii=False, indent=2) + '\n'
        '```\n\n'
        '## 原始资料页面图片\n\n'
        '以下是原始 PDF 文件的每一页扫描图片。请仔细阅读所有页面，'
        '提取完整的文字内容和结构化信息，然后编译成 Wiki 文章。\n'
    )
    blocks.append({'type': 'text', 'text': meta_text})

    # 每页图片（image blocks）
    for img in images:
        blocks.append({
            'type': 'image',
            'source': {
                'type': 'base64',
                'media_type': img['media_type'],
                'data': img['base64'],
            },
        })
        blocks.append({
            'type': 'text',
            'text': f'（以上是第 {img["page"] + 1} 页）',
        })

    # index.md + 已有文章（text block）
    context_parts: list[str] = ['', '## 当前 index.md']
    context_parts.append(index_md if index_md.strip() else '（空索引，本次可能是首次编译）')
    context_parts.append('')
    context_parts.append('## 相关已有文章')
    if not related_articles:
        context_parts.append('（该 topic 下暂无已有文章，本次编译可以自由新建）')
    else:
        for art in related_articles:
            context_parts.append(f'### {art["topic"]}/{art["slug"]}.md — {art["title"]}')
            context_parts.append('')
            context_parts.append(art['content'] or '（空文件）')
            context_parts.append('')

    blocks.append({'type': 'text', 'text': '\n'.join(context_parts)})

    return blocks


# ══════════════════════════════════════════════════════════════════
# 内部：JSON 解析
# ══════════════════════════════════════════════════════════════════

def _parse_ingest_response(text: str) -> dict[str, Any]:
    """解析 Claude 返回的 JSON。

    Claude 有时会：
    1. 把 JSON 包在 ```json ... ``` 代码块里
    2. 在 content 字段的 Markdown 里写未转义的双引号（JSON 语法错误）

    所以这里做多层宽容处理：先剥代码块 → json.loads → 失败则 json 修复重试。
    """
    s = (text or '').strip()
    if not s:
        raise IngestError('Claude 返回空响应')

    # 剥 markdown 代码块围栏
    if s.startswith('```'):
        first_nl = s.find('\n')
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.rstrip().endswith('```'):
            s = s.rstrip()[:-3]
        s = s.strip()

    # 第一次尝试：直接解析
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        # 第二次尝试：修复常见 JSON 问题
        try:
            data = _repair_and_parse_json(s)
            logger.warning('[Ingest] Claude 返回的 JSON 需要修复后才能解析（已自动修复）')
        except Exception as e2:
            raise IngestError(
                f'Claude 返回非法 JSON: {e2}；响应前 500 字符:\n{s[:500]}'
            ) from e2

    if not isinstance(data, dict):
        raise IngestError(f'Claude 返回顶层不是 JSON 对象: {type(data).__name__}')

    if 'operations' not in data:
        raise IngestError('Claude 返回缺少 operations 字段')

    return data


def _repair_and_parse_json(s: str) -> dict:
    """尝试修复 Claude 输出的半合法 JSON。

    常见问题：Markdown content 字段里有未转义的双引号或换行。
    策略：用正则逐个提取 JSON 字符串值，对其中的控制字符做转义。

    如果 json_repair 库可用优先使用（更健壮），否则用自建修复。
    """
    # 策略 1：尝试 json_repair 库
    try:
        from json_repair import repair_json
        repaired = repair_json(s, return_objects=False)
        return json.loads(repaired)
    except ImportError:
        pass
    except Exception:
        pass

    # 策略 2：逐字符状态机提取，找到 JSON 字符串边界后手动转义内部问题
    # 先处理最常见的问题：content 字段内部有原始换行（应该是 \n）
    # 和未转义的双引号
    fixed = []
    i = 0
    in_string = False
    escape_next = False

    for i, ch in enumerate(s):
        if escape_next:
            fixed.append(ch)
            escape_next = False
            continue
        if ch == '\\':
            fixed.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            fixed.append(ch)
            continue
        if in_string:
            # 在字符串内部的原始换行 → \n
            if ch == '\n':
                fixed.append('\\n')
                continue
            if ch == '\r':
                fixed.append('\\r')
                continue
            if ch == '\t':
                fixed.append('\\t')
                continue
        fixed.append(ch)

    try:
        return json.loads(''.join(fixed))
    except json.JSONDecodeError:
        pass

    # 策略 3：暴力提取 —— 找到 operations 数组的每个元素，用宽松方式解析
    raise json.JSONDecodeError('所有修复策略失败', s, 0)


# ══════════════════════════════════════════════════════════════════
# 内部：应用 operations
# ══════════════════════════════════════════════════════════════════

def _apply_operations(operations: list[dict], *, raw_id: int, rollback_state: dict):
    """把 Claude 返回的 operations 应用到 Wiki（磁盘 + 数据库）。

    支持三种 action：
    - create: 新建文章文件 + 新增 KnowledgeWikiArticle 记录
    - update: 覆盖文件 + 更新记录（source_raw_ids 合并）
    - noop:   不做任何写入

    事务规则（**不 commit**）：
    - DB 变更都 stage 到 session 里，由调用方在整个 ingest 成功后统一 commit
    - 每次写磁盘前把 rollback 信息追加到 rollback_state：
      * create 的文件 → rollback_state['created_files']
      * update 的旧正文 → rollback_state['updated_backups']
    - 调用方失败时会根据这些状态恢复磁盘

    前置条件：调用方已经对所有 operations 的 topic/slug 做过 validate_topic_slug。
    """
    now = datetime.utcnow()
    compile_model = claude_client.INGEST_MODEL
    created_files = rollback_state['created_files']
    updated_backups = rollback_state['updated_backups']

    for i, op in enumerate(operations):
        action = (op.get('action') or '').lower()
        topic = op.get('topic')
        slug = op.get('slug')

        if not topic or not slug:
            logger.warning(f'[Ingest] operation[{i}] 缺少 topic 或 slug，跳过: {op}')
            continue

        if action == 'noop':
            logger.info(f'[Ingest] noop {topic}/{slug}: {op.get("rationale", "")}')
            continue

        content = op.get('content')
        title = op.get('title')
        summary = op.get('summary')
        source_ids = op.get('source_raw_ids') or [raw_id]
        outbound_refs = op.get('outbound_refs') or []

        if action == 'create':
            if not content or not title:
                logger.warning(f'[Ingest] create 缺少 content 或 title，跳过: {topic}/{slug}')
                continue
            # 先检查目标文件是否已存在 —— 若存在，这是 update 伪装成 create
            # 的情况，需要备份旧内容以便回滚
            existing_art = KnowledgeWikiArticle.query.filter_by(
                topic=topic, slug=slug
            ).first()
            if existing_art is not None:
                old_content = storage.read_article_content(existing_art.file_path)
                updated_backups[existing_art.file_path] = old_content
                # 更新已有记录，不创建新 row（避免 unique constraint 冲突）
                storage.write_article(topic, slug, content)
                existing_art.title = title
                if summary is not None:
                    existing_art.summary = summary
                existing_art.content_length = len(content)
                merged = set(existing_art.source_raw_ids or [])
                merged.update(source_ids)
                existing_art.source_raw_ids = sorted(merged)
                existing_art.outbound_refs = list(outbound_refs)
                existing_art.last_compiled_at = now
                existing_art.compile_model = compile_model
                logger.info(f'[Ingest] create(→update) {topic}/{slug}')
            else:
                file_path = storage.write_article(topic, slug, content)
                created_files.append(file_path)
                art = KnowledgeWikiArticle(
                    topic=topic,
                    slug=slug,
                    title=title,
                    file_path=file_path,
                    summary=summary,
                    content_length=len(content),
                    source_raw_ids=list(source_ids),
                    outbound_refs=list(outbound_refs),
                    last_compiled_at=now,
                    compile_model=compile_model,
                )
                db.session.add(art)
                logger.info(f'[Ingest] create {topic}/{slug}')

        elif action == 'update':
            if not content:
                logger.warning(f'[Ingest] update 缺少 content，跳过: {topic}/{slug}')
                continue
            art = KnowledgeWikiArticle.query.filter_by(topic=topic, slug=slug).first()
            if art is None:
                # 回退为 create（Claude 误判或 slug 改名）
                logger.info(f'[Ingest] update 目标不存在，回退为 create: {topic}/{slug}')
                file_path = storage.write_article(topic, slug, content)
                created_files.append(file_path)
                art = KnowledgeWikiArticle(
                    topic=topic,
                    slug=slug,
                    title=title or slug,
                    file_path=file_path,
                    summary=summary,
                    content_length=len(content),
                    source_raw_ids=list(source_ids),
                    outbound_refs=list(outbound_refs),
                    last_compiled_at=now,
                    compile_model=compile_model,
                )
                db.session.add(art)
            else:
                # 备份旧正文用于回滚
                old_content = storage.read_article_content(art.file_path)
                updated_backups[art.file_path] = old_content

                storage.write_article(topic, slug, content)
                if title:
                    art.title = title
                if summary is not None:
                    art.summary = summary
                art.content_length = len(content)
                # 合并 source_raw_ids（并集，保留历史）
                existing = set(art.source_raw_ids or [])
                existing.update(source_ids)
                art.source_raw_ids = sorted(existing)
                if 'outbound_refs' in op:
                    art.outbound_refs = list(outbound_refs)
                art.last_compiled_at = now
                art.compile_model = compile_model
                logger.info(f'[Ingest] update {topic}/{slug}')

        else:
            logger.warning(f'[Ingest] operation[{i}] 未知 action={action!r}，跳过')

    # 重要：不在这里 commit，由调用方在 ingest_raw_file 末尾合并 commit
