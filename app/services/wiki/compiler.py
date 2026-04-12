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
        IngestError: 记录不存在、文件读取失败、Claude 返回非法 JSON 等
    """
    raw = KnowledgeRawFile.query.get(raw_file_id)
    if not raw:
        raise IngestError(f'KnowledgeRawFile id={raw_file_id} 不存在')

    raw.ingest_status = 'processing'
    raw.ingest_error = None
    db.session.commit()

    own_client = False
    if claude is None:
        claude = claude_client.WikiClaudeClient()
        own_client = True

    try:
        ensure_wiki_structure()

        # 1. 读原始文本
        try:
            raw_text = storage.read_raw_file_text(raw.raw_path)
        except Exception as e:
            raise IngestError(f'读取原始文件失败: {e}') from e

        if not raw_text.strip():
            raise IngestError('原始文件内容为空或无法提取文本')

        raw_text_truncated = raw_text[:MAX_RAW_TEXT_CHARS]
        truncated = len(raw_text) > MAX_RAW_TEXT_CHARS
        if truncated:
            logger.warning(
                f'[Ingest] raw {raw.id} 文本 {len(raw_text)} 字符超上限 {MAX_RAW_TEXT_CHARS}，已截断'
            )

        # 2. 当前 index.md
        index_md = storage.read_index()

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

        # 4. 组装 user prompt
        user_msg = _build_ingest_user_prompt(
            raw_meta={
                'raw_id': raw.id,
                'topic': raw.topic,
                'filename': raw.title,
                'truncated': truncated,
            },
            raw_text=raw_text_truncated,
            index_md=index_md,
            related_articles=related_context,
        )

        # 5. 调 Opus
        logger.info(
            f'[Ingest] raw_id={raw.id} topic={raw.topic} 相关文章数={len(related_context)} '
            f'raw_text={len(raw_text_truncated)}B prompt={len(user_msg)}B'
        )
        resp = claude.complete(
            system=prompts.INGEST_SYSTEM,
            user=user_msg,
            model=claude_client.INGEST_MODEL,
            max_tokens=32000,
        )

        # 6. 解析 JSON
        result = _parse_ingest_response(resp.text)

        # 7. 应用 operations
        operations = result.get('operations') or []
        _apply_operations(operations, raw_id=raw.id)

        # 8. 写 index.md
        index_updated = False
        new_index = result.get('index_update')
        if new_index:
            storage.write_index(new_index)
            index_updated = True

        # 9. 追加 log.md
        log_entry = result.get('log_entry') or ''
        storage.append_log(
            'ingest',
            f'- raw_id={raw.id} title={raw.title!r} topic={raw.topic}\n'
            f'- operations: {len(operations)}\n'
            f'- {log_entry}',
        )

        # 10. 标记完成
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
        # 任何异常都标记失败，并把原因存到 DB 方便前端显示
        db.session.rollback()
        raw.ingest_status = 'error'
        raw.ingest_error = str(e)[:2000]
        db.session.commit()
        logger.exception(f'[Ingest] raw_id={raw_file_id} 失败')
        raise
    finally:
        if own_client:
            claude.close()


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
    """构造传给 Claude 的 user 消息（Markdown 章节格式）。"""
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


# ══════════════════════════════════════════════════════════════════
# 内部：JSON 解析
# ══════════════════════════════════════════════════════════════════

def _parse_ingest_response(text: str) -> dict[str, Any]:
    """解析 Claude 返回的 JSON。

    Claude 有时会把 JSON 包在 ```json ... ``` 代码块里，尽管 prompt 要求
    直接输出。这里做一次宽容剥离。
    """
    s = (text or '').strip()
    if not s:
        raise IngestError('Claude 返回空响应')

    # 剥 markdown 代码块围栏
    if s.startswith('```'):
        # 去掉开头的 ```json 或 ``` 这一行
        first_nl = s.find('\n')
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.rstrip().endswith('```'):
            s = s.rstrip()[:-3]
        s = s.strip()

    try:
        data = json.loads(s)
    except json.JSONDecodeError as e:
        raise IngestError(
            f'Claude 返回非法 JSON: {e}；响应前 500 字符:\n{s[:500]}'
        ) from e

    if not isinstance(data, dict):
        raise IngestError(f'Claude 返回顶层不是 JSON 对象: {type(data).__name__}')

    # operations 至少要存在
    if 'operations' not in data:
        raise IngestError('Claude 返回缺少 operations 字段')

    return data


# ══════════════════════════════════════════════════════════════════
# 内部：应用 operations
# ══════════════════════════════════════════════════════════════════

def _apply_operations(operations: list[dict], *, raw_id: int):
    """把 Claude 返回的 operations 应用到 Wiki（磁盘 + 数据库）。

    支持三种 action：
    - create: 新建文章文件 + 新增 KnowledgeWikiArticle 记录
    - update: 覆盖文件 + 更新记录（source_raw_ids 合并）
    - noop:   不做任何写入
    """
    now = datetime.utcnow()
    compile_model = claude_client.INGEST_MODEL

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
            file_path = storage.write_article(topic, slug, content)
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

    db.session.commit()
