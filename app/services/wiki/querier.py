# -*- coding: utf-8 -*-
"""Wiki Query 问答服务

对着 Wiki 提问，返回基于文章内容的回答 + 引用来源。

流程：
    1. PG 全文检索命中 top-k 文章（GIN 索引 on title+summary）
    2. 如无命中，退化为取 topic 全部或整库少量文章，避免空上下文
    3. 读这些文章全文
    4. 组装 prompt（index.md + 文章全文 + 问题）
    5. 调 Claude Opus 生成回答
    6. 返回 {answer, cited_articles, usage}

搜索策略：
- 第一次用 plainto_tsquery 做自然语言查询
- 命中 < top_k 时用 topic filter 和最近更新补齐
"""
import logging
import re
from typing import Any

from sqlalchemy import text

from app import db
from app.models.knowledge import KnowledgeWikiArticle
from app.services.wiki import claude_client, prompts, storage

logger = logging.getLogger(__name__)


class QueryError(RuntimeError):
    pass


DEFAULT_TOP_K = 5


# ══════════════════════════════════════════════════════════════════
# 公开入口
# ══════════════════════════════════════════════════════════════════

def query_wiki(
    question: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    topic: str | None = None,
    claude: claude_client.WikiClaudeClient | None = None,
    current_user_id: int | None = None,
) -> dict[str, Any]:
    """对 Wiki 发起一次问答。

    Args:
        question: 用户自然语言问题
        top_k: 全文检索召回的文章数上限
        topic: 可选过滤 topic，为 None 时全库搜索
        claude: 可选 Claude 客户端（测试用 mock）

    Returns:
        {
            'answer': str,              # Claude 回答的 Markdown
            'cited_articles': [...],    # [{id, topic, slug, title, summary, images}, ...]
            'usage': {...},
            'search_hit_count': int,    # 全文检索命中数（0 = 退化）
        }
    """
    question = (question or '').strip()
    if not question:
        raise QueryError('问题不能为空')

    # 1. 全文检索
    hits = _full_text_search(question, top_k, topic)
    fts_count = len(hits)

    # 2. 退化策略：命中为 0 就取最近更新的 top_k 篇
    if not hits:
        logger.info('[Query] 全文检索 0 命中，退化为最近更新的 top_k 文章')
        q = KnowledgeWikiArticle.query
        if topic:
            q = q.filter_by(topic=topic)
        hits = q.order_by(KnowledgeWikiArticle.updated_at.desc()).limit(top_k).all()

    if not hits:
        return {
            'answer': 'Wiki 中暂无任何文章，请先上传原始资料并触发编译。',
            'cited_articles': [],
            'usage': {'input_tokens': 0, 'output_tokens': 0, 'model': 'n/a'},
            'search_hit_count': 0,
        }

    # 3. 读正文
    cited_articles: list[dict] = []
    articles_with_content: list[tuple[KnowledgeWikiArticle, str]] = []
    for art in hits:
        content = storage.read_article_content(art.file_path)
        articles_with_content.append((art, content))
        cited_articles.append({
            'id': art.id,
            'topic': art.topic,
            'slug': art.slug,
            'title': art.title,
            'summary': art.summary,
            'images': [
                {'index': m['index'], 'path': m['path'], 'caption': m.get('caption', '')}
                for m in (art.image_manifest or [])
            ],
        })

    # 4. 组装 prompt
    user_msg = _build_query_user_prompt(
        question=question,
        index_md=storage.read_index(),
        articles=articles_with_content,
    )

    # 5. 调 Claude
    own_client = False
    if claude is None:
        claude = claude_client.WikiClaudeClient()
        own_client = True
    try:
        logger.info(
            f'[Query] question={question[:60]!r} articles={len(articles_with_content)} '
            f'prompt={len(user_msg)}B fts_hits={fts_count}'
        )
        resp = claude.complete(
            system=prompts.get_query_system(),
            user=user_msg,
            model=claude_client.QUERY_MODEL,
            max_tokens=4000,
        )
    finally:
        if own_client:
            claude.close()

    # 发放 wiki_cited_qa 积分（过滤自引）
    if current_user_id:
        try:
            from app.services.points_service import award_points
            for art, _ in articles_with_content:
                if art.owner_id and art.owner_id != current_user_id:
                    award_points(
                        user_id=art.owner_id,
                        behavior_code='wiki_cited_qa',
                        source_type='wiki_qa_session',
                        source_id=f'qa_{art.id}_{current_user_id}',
                        memo=f'问答引用: {art.title}',
                    )
            db.session.commit()
        except Exception as _pts_err:
            logger.warning(f'wiki_cited_qa积分发放失败: {_pts_err}')

    return {
        'answer': resp.text,
        'cited_articles': cited_articles,
        'usage': resp.usage,
        'search_hit_count': fts_count,
    }


# ══════════════════════════════════════════════════════════════════
# 内部：PG 全文检索
# ══════════════════════════════════════════════════════════════════

def _tokenize_query(question: str) -> list[str]:
    """把用户问题拆成 FTS 友好的 token 列表。

    策略：把连续的英文/数字视为一个 token，连续的 CJK 字符按 2~4 字 n-gram
    切分以提高中文命中率。PG 'simple' 分词器不会分 CJK，所以我们在客户端做。
    """
    tokens: list[str] = []
    # 先把英文/数字拉出来
    for m in re.findall(r'[A-Za-z][A-Za-z0-9_\-]*|\d[\w\-]*', question):
        if len(m) >= 2:
            tokens.append(m.lower())
    # 再把连续 CJK 按 2-gram 拆（粗暴但有效：覆盖"防护"、"等级"、"对讲"等常见词）
    for run in re.findall(r'[\u4e00-\u9fff]{2,}', question):
        for i in range(len(run) - 1):
            tokens.append(run[i:i + 2])
    return list(dict.fromkeys(tokens))  # 去重保序


def _full_text_search(
    question: str,
    top_k: int,
    topic: str | None,
) -> list[KnowledgeWikiArticle]:
    """对 title+summary 的 GIN 索引做多 token OR 匹配。

    PG 'simple' 分词器不会拆分 CJK，所以在 Python 里先把问题拆成英文
    token + 中文 2-gram，然后用 OR 去 to_tsquery 检索。任意一个 token
    命中即返回，ts_rank 按命中度排序。
    """
    tokens = _tokenize_query(question)
    if not tokens:
        return []

    # 转义 to_tsquery 的特殊字符并用 | 拼成 OR 查询
    def _esc(tok: str) -> str:
        # 去掉 to_tsquery 会爆炸的字符
        return re.sub(r"[!&|<>:()'\"\\*]", '', tok)

    safe_tokens = [_esc(t) for t in tokens if _esc(t)]
    if not safe_tokens:
        return []
    ts_query_expr = ' | '.join(safe_tokens)

    where_topic = 'AND topic = :topic' if topic else ''
    sql = text(f"""
        SELECT id,
               ts_rank(
                   to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, '')),
                   to_tsquery('simple', :q)
               ) AS rank
        FROM knowledge_wiki_articles
        WHERE to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, ''))
              @@ to_tsquery('simple', :q)
              {where_topic}
        ORDER BY rank DESC
        LIMIT :k
    """)
    params = {'q': ts_query_expr, 'k': top_k}
    if topic:
        params['topic'] = topic
    try:
        rows = db.session.execute(sql, params).fetchall()
    except Exception as e:
        logger.warning(f'[Query] to_tsquery 失败，退化为空结果: {e}; expr={ts_query_expr!r}')
        return []
    if not rows:
        return []
    ids = [r.id for r in rows]
    # 按原 rank 顺序取 ORM 对象
    arts = {a.id: a for a in KnowledgeWikiArticle.query.filter(
        KnowledgeWikiArticle.id.in_(ids)
    ).all()}
    return [arts[i] for i in ids if i in arts]


# ══════════════════════════════════════════════════════════════════
# 内部：prompt 组装
# ══════════════════════════════════════════════════════════════════

def _build_query_user_prompt(
    *,
    question: str,
    index_md: str,
    articles: list[tuple[KnowledgeWikiArticle, str]],
) -> str:
    parts: list[str] = []

    parts.append('## 当前 index.md')
    parts.append(index_md if index_md.strip() else '（空索引）')
    parts.append('')

    parts.append('## 相关文章')
    if not articles:
        parts.append('（未找到相关文章）')
    else:
        for art, content in articles:
            parts.append(f'### {art.topic}/{art.slug}.md — {art.title}')
            parts.append('')
            parts.append(content or '（空文件）')
            parts.append('')

    parts.append('## 用户问题')
    parts.append(question)

    return '\n'.join(parts)
