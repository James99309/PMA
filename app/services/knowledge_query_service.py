# -*- coding: utf-8 -*-
"""
知识库 RAG 查询管道

用户提问 → Embedding → pgvector 语义搜索 → 组装 Prompt → DeepSeek Chat → 回答+来源
"""
import os
import logging
from typing import List, Generator, Optional

from sqlalchemy import text as sa_text

from app import db
from app.models.knowledge import (
    KnowledgeTag, KnowledgeDocument, KnowledgeChunk,
    knowledge_document_tags
)
from app.services.knowledge_ai_service import generate_embeddings, chat_completion_stream, chat_completion

logger = logging.getLogger(__name__)

MAX_CONTEXT_CHUNKS = int(os.getenv('KNOWLEDGE_MAX_CONTEXT_CHUNKS', '8'))

SYSTEM_PROMPT = """你是公司内部知识助手。请严格基于下方提供的文档内容回答问题。

规则:
1. 只使用提供的文档内容回答，不要编造信息
2. 如果文档中没有相关内容，请明确说明"根据现有知识库文档，未找到相关信息"
3. 回答中必须引用来源文档的标题
4. 使用简洁、专业的中文回答
5. 如果多个文档有相关信息，综合后回答并分别引用"""


def get_accessible_document_ids(user) -> List[int]:
    """获取用户可访问的知识文档 ID 列表

    - admin/ceo: 可访问所有 status='ready' 且未过期的文档
    - 其他用户: 仅可访问自己添加的 status='ready' 且未过期的文档
    """
    query = KnowledgeDocument.query.filter(
        KnowledgeDocument.status == 'ready',
        KnowledgeDocument.expired_at.is_(None),
    )

    role = getattr(user, 'role', '')
    if role not in ('admin', 'ceo'):
        query = query.filter(KnowledgeDocument.added_by == user.id)

    return [doc.id for doc in query.with_entities(KnowledgeDocument.id).all()]


def semantic_search(query: str, tag_ids: Optional[List[int]] = None,
                    user=None, top_k: int = None) -> List[dict]:
    """
    语义搜索：生成问题向量 → pgvector 余弦相似度搜索

    Args:
        query: 用户问题
        tag_ids: 限定的标签 ID 列表（None=不按标签过滤）
        user: 当前用户（权限过滤）
        top_k: 返回条数

    Returns:
        [{"chunk_id", "content", "score", "doc_id", "doc_title", ...}]
    """
    top_k = top_k or MAX_CONTEXT_CHUNKS

    # 1. 确定用户可访问的文档
    if user:
        accessible_doc_ids = get_accessible_document_ids(user)
    else:
        accessible_doc_ids = []

    if not accessible_doc_ids:
        return []

    # 2. 生成问题向量
    try:
        embeddings = generate_embeddings([query])
        if not embeddings:
            return []
        query_embedding = embeddings[0]
    except Exception as e:
        logger.error(f"生成问题向量失败: {e}")
        return []

    # 3. pgvector 余弦相似度搜索
    doc_ids_str = ','.join(str(d) for d in accessible_doc_ids)

    # 构建可选的标签过滤
    tag_join = ''
    tag_filter = ''
    if tag_ids:
        tag_ids_str = ','.join(str(t) for t in tag_ids)
        tag_join = f'JOIN knowledge_document_tags kdt ON kdt.document_id = kd.id'
        tag_filter = f'AND kdt.tag_id IN ({tag_ids_str})'

    sql = sa_text(f"""
        SELECT DISTINCT
            kc.id AS chunk_id,
            kc.content,
            kc.metadata,
            kc.chunk_index,
            kd.id AS doc_id,
            kd.title AS doc_title,
            kd.file_library_id,
            1 - (kc.embedding <=> :query_vec) AS similarity
        FROM knowledge_chunks kc
        JOIN knowledge_documents kd ON kd.id = kc.document_id
        {tag_join}
        WHERE kd.id IN ({doc_ids_str})
          AND kd.status = 'ready'
          AND kd.expired_at IS NULL
          {tag_filter}
        ORDER BY
            (1 - (kc.embedding <=> :query_vec)) DESC
        LIMIT :top_k
    """)

    try:
        results = db.session.execute(sql, {
            'query_vec': str(query_embedding),
            'top_k': top_k * 2,  # 多取一些用于去重
        }).fetchall()
    except Exception as e:
        logger.error(f"pgvector 搜索失败: {e}")
        return []

    # 4. 去重同文档，保留分数最高的 chunk
    seen_docs = {}
    final_results = []
    for row in results:
        doc_id = row.doc_id
        if doc_id not in seen_docs:
            seen_docs[doc_id] = 0
        seen_docs[doc_id] += 1
        # 同一文档最多保留 2 个 chunk
        if seen_docs[doc_id] > 2:
            continue
        if len(final_results) >= top_k:
            break
        final_results.append({
            'chunk_id': row.chunk_id,
            'content': row.content,
            'metadata': row.metadata,
            'chunk_index': row.chunk_index,
            'doc_id': row.doc_id,
            'doc_title': row.doc_title,
            'file_library_id': row.file_library_id,
            'score': round(float(row.similarity), 4),
        })

    return final_results


def build_rag_prompt(question: str, chunks: List[dict]) -> list:
    """
    组装 RAG Prompt

    Returns:
        OpenAI 格式的 messages 列表
    """
    # 组装文档上下文
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_info = f"[来源{i}: {chunk['doc_title']}]"
        context_parts.append(f"{source_info}\n{chunk['content']}")

    context = '\n\n---\n\n'.join(context_parts)

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f"## 参考文档\n\n{context}\n\n## 用户问题\n\n{question}"},
    ]

    return messages


def ask_stream(question: str, user=None,
               tag_ids: Optional[List[int]] = None) -> Generator[str, None, None]:
    """
    流式问答 — SSE 使用

    Args:
        question: 用户问题
        user: 当前用户
        tag_ids: 可选标签过滤

    Yields:
        SSE data 格式的 JSON 字符串
    """
    import json

    # 1. 搜索相关文档
    chunks = semantic_search(question, tag_ids=tag_ids, user=user)

    if not chunks:
        yield f"data: {json.dumps({'type': 'content', 'text': '根据现有知识库文档，未找到与您问题相关的信息。请尝试其他关键词或扩大搜索范围。'}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'sources': []})}\n\n"
        return

    # 2. 组装 Prompt
    messages = build_rag_prompt(question, chunks)

    # 3. 流式调用 DeepSeek
    sources = [
        {
            'doc_id': c['doc_id'],
            'title': c['doc_title'],
            'score': c['score'],
            'file_library_id': c.get('file_library_id'),
        }
        for c in chunks
    ]
    # 去重
    seen = set()
    unique_sources = []
    for s in sources:
        if s['doc_id'] not in seen:
            seen.add(s['doc_id'])
            unique_sources.append(s)

    for token in chat_completion_stream(messages):
        yield f"data: {json.dumps({'type': 'content', 'text': token}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done', 'sources': unique_sources}, ensure_ascii=False)}\n\n"


def ask(question: str, user=None,
        tag_ids: Optional[List[int]] = None) -> dict:
    """
    非流式问答

    Args:
        question: 用户问题
        user: 当前用户
        tag_ids: 可选标签过滤

    Returns:
        {"answer": str, "sources": [...], "tokens_used": int}
    """
    chunks = semantic_search(question, tag_ids=tag_ids, user=user)

    if not chunks:
        return {
            'answer': '根据现有知识库文档，未找到与您问题相关的信息。请尝试其他关键词或扩大搜索范围。',
            'sources': [],
            'tokens_used': 0,
        }

    messages = build_rag_prompt(question, chunks)
    answer, tokens_used = chat_completion(messages)

    sources = []
    seen = set()
    for c in chunks:
        if c['doc_id'] not in seen:
            seen.add(c['doc_id'])
            sources.append({
                'doc_id': c['doc_id'],
                'title': c['doc_title'],
                'score': c['score'],
                'file_library_id': c.get('file_library_id'),
            })

    return {
        'answer': answer,
        'sources': sources,
        'tokens_used': tokens_used,
    }
