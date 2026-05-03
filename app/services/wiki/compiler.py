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

from flask import current_app

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
    force: bool = False,
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
        'old_index': None,          # 旧 index.md 内容(str),便于恢复
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
                embedded_images=raw_content.embedded_images,
            )

        # 5. 调 Opus
        logger.info(
            f'[Ingest] raw_id={raw.id} topic={raw.topic} 相关文章数={len(related_context)} '
            f'mode={"vision" if is_vision else "text"} '
            f'{"images=" + str(len(raw_content.images)) + "p" if is_vision else "text=" + str(len(raw_text)) + "B"}'
        )
        # 释放上面查 related_articles 打开的只读事务，防止 LLM 长调用期间
        # 被 PG 的 idle_in_transaction_session_timeout 杀连接（实测 Opus
        # 对大文档可能跑 400s+，远超默认 300s）
        db.session.commit()
        is_ovs = bool(current_app.config.get('IS_OVS', False))
        resp = claude_instance.complete(
            system=prompts.get_ingest_system(is_ovs=is_ovs),
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

        # 7.5 落盘嵌入图 + 重写 AUTO_IMG: 占位符（text 和 vision 两种模式都走这里）
        op_manifests = _persist_embedded_images_and_rewrite_md(
            operations,
            raw_content.embedded_images,
            rollback_state,
        )

        # 8. 应用 operations(追踪 rollback 状态,但不 commit)
        _apply_operations(operations, raw_id=raw.id, rollback_state=rollback_state,
                         scope=raw.scope, owner_id=raw.owner_id,
                         owner_department=raw.owner_department,
                         op_manifests=op_manifests, force=force)

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
    """失败回滚:删除新建的文件,恢复被修改的文件和 index.md。"""
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
    embedded_images: list | None = None,
) -> str:
    """构造传给 Claude 的 user 消息（纯文本模式，Markdown 章节格式）。

    若 embedded_images 非空（来自 docx 嵌入图），会附加 `## 嵌入图片清单` 段，
    Claude 应按 system prompt 用 `![描述](AUTO_IMG:N)` 在文章正文中引用。
    """
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

    if embedded_images:
        parts.append('## 嵌入图片清单')
        parts.append(
            '原始资料含以下嵌入图片，按出现顺序编号。请按 system prompt'
            '「图片处理规则」用 `![描述](AUTO_IMG:N)` 在文章正文中嵌入引用。'
        )
        parts.append('')
        for img in embedded_images:
            parts.append(
                f'- 图 #{img["order"]}: 出现在第 {img["paragraph_index"]} 段附近, '
                f'类型 {img["media_type"]}, 原文件名 {img.get("original_name", "?")}'
            )
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

    # 嵌入图片清单 - 教 Claude 如何用 AUTO_IMG:N 引用各页（与 text 模式 docx 一致）
    if images:
        img_list_lines = [
            '',
            '## 嵌入图片清单',
            '上述每页 PNG 在文章正文中可用 `![描述](AUTO_IMG:N)` 引用，N 为页码。'
            '请按 system prompt「图片处理规则」就近放置，每张图给一个简洁有信息的中文 caption。',
            '',
        ]
        for img in images:
            img_list_lines.append(
                f'- 图 #{img["page"] + 1}: 来自 PDF 第 {img["page"] + 1} 页, 类型 {img["media_type"]}'
            )
        blocks.append({'type': 'text', 'text': '\n'.join(img_list_lines)})

    return blocks


# ══════════════════════════════════════════════════════════════════
# 内部：JSON 解析
# ══════════════════════════════════════════════════════════════════

def _parse_ingest_response(text: str) -> dict[str, Any]:
    """解析 Claude 返回的 JSON。

    Claude 有时会：
    1. 把 JSON 包在 ```json ... ``` 代码块里
    2. 在 content 字段的 Markdown 里写未转义的双引号（JSON 语法错误）
    3. 输出被 max_tokens 截断（JSON 不完整）

    多层宽容处理：剥代码块 → json.loads → json_repair → 截断修复。
    """
    import re

    s = (text or '').strip()
    if not s:
        raise IngestError('Claude 返回空响应')

    # 剥 markdown 代码块围栏（用正则更可靠）
    fence_match = re.match(r'^```(?:json)?\s*\n(.*?)```\s*$', s, re.DOTALL)
    if fence_match:
        s = fence_match.group(1).strip()
    elif s.startswith('```'):
        # 兜底：可能是截断导致没有闭合围栏
        first_nl = s.find('\n')
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.rstrip().endswith('```'):
            s = s.rstrip()[:-3]
        s = s.strip()

    if not s:
        raise IngestError('Claude 返回的响应剥离代码块后为空')

    # 第一次尝试：直接解析
    try:
        data = json.loads(s)
        return _validate_ingest_data(data)
    except json.JSONDecodeError:
        pass

    # 第二次尝试：json_repair 库（处理未转义引号、控制字符等）
    try:
        data = _repair_and_parse_json(s)
        logger.warning('[Ingest] Claude 返回的 JSON 需要修复后才能解析（已自动修复）')
        return _validate_ingest_data(data)
    except Exception:
        pass

    # 第三次尝试：截断修复 —— 找到最后一个完整的 operation 对象
    try:
        data = _salvage_truncated_json(s)
        logger.warning('[Ingest] Claude 返回的 JSON 被截断，已抢救部分 operations')
        return _validate_ingest_data(data)
    except Exception:
        pass

    raise IngestError(
        f'Claude 返回非法 JSON，所有修复策略均失败；响应前 500 字符:\n{s[:500]}'
    )


def _validate_ingest_data(data: Any) -> dict:
    """校验解析后的数据结构。"""
    if not isinstance(data, dict):
        raise IngestError(f'Claude 返回顶层不是 JSON 对象: {type(data).__name__}')
    if 'operations' not in data:
        raise IngestError('Claude 返回缺少 operations 字段')
    return data


def _repair_and_parse_json(s: str) -> dict:
    """用 json_repair 库修复 Claude 输出的半合法 JSON。

    常见问题：content 字段里有未转义双引号、反斜杠、控制字符。
    json_repair 能处理绝大多数情况。
    """
    from json_repair import repair_json
    repaired = repair_json(s, return_objects=False)
    return json.loads(repaired)


def _salvage_truncated_json(s: str) -> dict:
    """从截断的 JSON 中抢救已完整的 operations。

    当 stop_reason == max_tokens 时，JSON 被截断在某个 operation 中间。
    策略：找到 operations 数组中最后一个完整的 `}` 对象边界，截断后补全 JSON 结构。
    """
    import re
    from json_repair import repair_json

    # 找 "operations" 数组的起始位置
    ops_match = re.search(r'"operations"\s*:\s*\[', s)
    if not ops_match:
        raise ValueError('找不到 operations 数组')

    ops_start = ops_match.end()

    # 从 operations 数组开始，逐个找完整的 {...} 对象
    # 用括号深度追踪法
    last_complete_end = -1
    depth = 0
    in_str = False
    esc = False
    i = ops_start

    while i < len(s):
        ch = s[i]
        if esc:
            esc = False
            i += 1
            continue
        if ch == '\\' and in_str:
            esc = True
            i += 1
            continue
        if ch == '"':
            in_str = not in_str
            i += 1
            continue
        if in_str:
            i += 1
            continue
        # 不在字符串内
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                last_complete_end = i + 1
        elif ch == ']' and depth == 0:
            # 数组正常结束
            last_complete_end = i + 1
            break
        i += 1

    if last_complete_end <= ops_start:
        raise ValueError('没有找到任何完整的 operation 对象')

    # 用找到的最后完整对象位置截断，补全 JSON
    truncated_ops = s[ops_start:last_complete_end].rstrip().rstrip(',')
    # 构造最小可解析 JSON
    salvaged = '{"operations":[' + truncated_ops + ']}'

    try:
        return json.loads(salvaged)
    except json.JSONDecodeError:
        # 最后一搏：用 json_repair 修复截断后的结果
        repaired = repair_json(salvaged, return_objects=False)
        return json.loads(repaired)


# ══════════════════════════════════════════════════════════════════
# 内部：应用 operations
# ══════════════════════════════════════════════════════════════════

def _award_wiki_cited(old_refs: list, new_refs: list):
    """对 outbound_refs 中新增的被引用文章的 owner 发放 wiki_cited 积分。

    old_refs / new_refs 格式为 "<topic>/<slug>" 字符串列表。
    本函数在 _apply_operations 内调用，不负责 commit，由调用方统一提交。
    """
    new_cited = set(new_refs) - set(old_refs)
    if not new_cited:
        return
    try:
        from app.services.points_service import award_points
        for ref in new_cited:
            parts = ref.split('/', 1)
            if len(parts) != 2:
                continue
            ref_topic, ref_slug = parts
            cited_art = KnowledgeWikiArticle.query.filter_by(
                topic=ref_topic, slug=ref_slug
            ).first()
            if cited_art and cited_art.owner_id:
                try:
                    award_points(
                        user_id=cited_art.owner_id,
                        behavior_code='wiki_cited',
                        source_type='wiki_article',
                        source_id=cited_art.id,
                        memo=f'Wiki文章被引用: {cited_art.title}'
                    )
                except Exception as pts_err:
                    logger.warning(f"[Ingest] 发放wiki_cited积分失败 article={cited_art.id}: {pts_err}")
    except Exception as e:
        logger.warning(f"[Ingest] _award_wiki_cited 整体失败: {e}")


def _persist_embedded_images_and_rewrite_md(
    operations: list[dict],
    embedded_images: list[dict],
    rollback_state: dict,
) -> dict[int, list[dict]]:
    """把每个 create/update op 内容里的 `![cap](AUTO_IMG:N)` 替换为真实
    `_assets/<slug>/img-N.<ext>` 路径，把图片字节落盘，并构造 manifest 条目。

    Returns:
        {op_index: [manifest_entry, ...]}

    Manifest entry 形如：
      {'index': N, 'path': str (相对文章 .md),
       'caption': str, 'source': {'type':'docx_para','paragraph_index':int},
       'manually_replaced': False, 'replaced_at': None,
       'sha256': str, 'size_bytes': int}

    落盘的文件路径（相对 wiki_root）会追加到 rollback_state['created_files']
    以便失败时被 _rollback_file_changes 删除。
    """
    import re

    if not embedded_images:
        return {}

    pattern = re.compile(r'!\[([^\]]*)\]\(AUTO_IMG:(\d+)\)')
    img_by_order = {img['order']: img for img in embedded_images}
    manifests: dict[int, list[dict]] = {}

    for op_idx, op in enumerate(operations):
        action = (op.get('action') or '').lower()
        if action not in ('create', 'update'):
            continue
        body = op.get('content') or ''
        topic = op.get('topic')
        slug = op.get('slug')
        if not topic or not slug:
            continue

        used_indices: set[int] = set()
        used_entries: list[dict] = []

        def _sub(m, _topic=topic, _slug=slug):
            caption = m.group(1).strip()
            order = int(m.group(2))
            img = img_by_order.get(order)
            if not img:
                # 引用未知图片 → 静默丢弃整个 markdown 引用
                return ''
            if order in used_indices:
                # 同一张图被多次引用 → 复用首次落盘路径
                existing = next((e for e in used_entries if e['index'] == order), None)
                if existing:
                    return f'![{caption}]({existing["path"]})'
                return ''
            used_indices.add(order)
            rel = storage.save_article_image(_topic, _slug, order, img['data'], img['media_type'])
            # rel 形如 '_assets/<slug>/img-N.png'，相对文章 .md
            # rollback 路径需要相对 wiki_root（即加上 wiki/<topic>/ 前缀）
            rollback_state['created_files'].append(f'wiki/{_topic}/{rel}')
            # 区分图片来源（docx 段落 / pdf 页图）
            if 'paragraph_index' in img:
                source = {'type': 'docx_para', 'paragraph_index': img['paragraph_index']}
            elif 'page_index' in img:
                source = {'type': 'pdf_page', 'page_index': img['page_index']}
            else:
                source = {'type': 'unknown'}
            used_entries.append({
                'index': order,
                'path': rel,
                'caption': caption,
                'source': source,
                'manually_replaced': False,
                'replaced_at': None,
                'sha256': storage.sha256_bytes(img['data']),
                'size_bytes': len(img['data']),
            })
            return f'![{caption}]({rel})'

        new_body = pattern.sub(_sub, body)
        op['content'] = new_body
        if used_entries:
            manifests[op_idx] = used_entries

    return manifests


def _apply_operations(operations: list[dict], *, raw_id: int, rollback_state: dict,
                      scope: str = 'company', owner_id: int = 1,
                      owner_department: str | None = None,
                      op_manifests: dict[int, list[dict]] | None = None,
                      force: bool = False):
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
    op_manifests = op_manifests or {}

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
                # Respect manual edits (Task 13): skip if user has hand-edited this article and force=False.
                if existing_art.manually_edited and not force:
                    op['skipped_reason'] = 'manually_edited'
                    op['action'] = 'noop'
                    logger.info(
                        f'[Ingest] skipping {topic}/{slug} — manually_edited=True (force=False)'
                    )
                    continue
                old_content = storage.read_article_content(existing_art.file_path)
                updated_backups[existing_art.file_path] = old_content
                # 更新已有记录,不创建新 row(避免 unique constraint 冲突)
                storage.write_article(topic, slug, content)
                existing_art.title = title
                if summary is not None:
                    existing_art.summary = summary
                existing_art.content_length = len(content)
                merged = set(existing_art.source_raw_ids or [])
                merged.update(source_ids)
                existing_art.source_raw_ids = sorted(merged)
                # 检测新增被引用的文章，发放 wiki_cited 积分
                _award_wiki_cited(existing_art.outbound_refs or [], list(outbound_refs))
                existing_art.outbound_refs = list(outbound_refs)
                existing_art.last_compiled_at = now
                existing_art.compile_model = compile_model
                # 重新 ingest 视为新一轮图片集合，覆盖旧 manifest（仅当本次有图）
                manifest = op_manifests.get(i)
                if manifest is not None:
                    existing_art.image_manifest = manifest
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
                    scope=scope,
                    owner_id=owner_id,
                    owner_department=owner_department,
                    image_manifest=op_manifests.get(i),
                )
                db.session.add(art)
                db.session.flush()  # 确保 art.id 已生成
                if art.owner_id:
                    try:
                        from app.services.points_service import award_points
                        award_points(user_id=art.owner_id, behavior_code='wiki_create',
                                     source_type='wiki_article', source_id=art.id,
                                     memo=f'创建Wiki文章: {art.title}')
                    except Exception as _pts_err:
                        logger.warning(f'wiki_create积分发放失败: {_pts_err}')
                logger.info(f'[Ingest] create {topic}/{slug}')

        elif action == 'update':
            if not content:
                logger.warning(f'[Ingest] update 缺少 content，跳过: {topic}/{slug}')
                continue
            art = KnowledgeWikiArticle.query.filter_by(topic=topic, slug=slug).first()
            if art is None:
                # 回退为 create(Claude 误判或 slug 改名)
                logger.info(f'[Ingest] update 目标不存在,回退为 create: {topic}/{slug}')
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
                    scope=scope,
                    owner_id=owner_id,
                    owner_department=owner_department,
                    image_manifest=op_manifests.get(i),
                )
                db.session.add(art)
            else:
                # Respect manual edits (Task 13): skip if user has hand-edited this article and force=False.
                if art.manually_edited and not force:
                    op['skipped_reason'] = 'manually_edited'
                    op['action'] = 'noop'
                    logger.info(
                        f'[Ingest] skipping {topic}/{slug} — manually_edited=True (force=False)'
                    )
                    continue
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
                    # 检测新增被引用的文章，发放 wiki_cited 积分
                    _award_wiki_cited(art.outbound_refs or [], list(outbound_refs))
                    art.outbound_refs = list(outbound_refs)
                art.last_compiled_at = now
                art.compile_model = compile_model
                # 重新 ingest 视为新一轮图片集合，覆盖旧 manifest（仅当本次有图）
                manifest = op_manifests.get(i)
                if manifest is not None:
                    art.image_manifest = manifest
                logger.info(f'[Ingest] update {topic}/{slug}')

        else:
            logger.warning(f'[Ingest] operation[{i}] 未知 action={action!r}，跳过')

    # 重要：不在这里 commit，由调用方在 ingest_raw_file 末尾合并 commit
