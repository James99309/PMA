# -*- coding: utf-8 -*-
"""
知识库 RAG 查询管道

用户提问 → Embedding → pgvector 语义搜索 → 组装 Prompt → DeepSeek Chat → 回答+来源
"""
import os
import logging
from typing import List, Generator

from flask_login import current_user
from sqlalchemy import text as sa_text

from app import db
from app.models.knowledge import (
    KnowledgeSpace, KnowledgeDocument, KnowledgeChunk,
    KnowledgeChatSession, KnowledgeChatMessage
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


def get_accessible_space_ids(user) -> List[int]:
    """获取用户可访问的知识空间 ID 列表"""
    spaces = KnowledgeSpace.query.filter_by(is_active=True).all()
    accessible = []

    for space in spaces:
        if space.access_level == 'all':
            accessible.append(space.id)
        elif space.access_level == 'admin_only':
            if getattr(user, 'role', '') in ('admin', 'ceo'):
                accessible.append(space.id)
        elif space.access_level == 'role':
            allowed = space.allowed_roles or []
            if getattr(user, 'role', '') in allowed:
                accessible.append(space.id)
        elif space.access_level == 'department':
            allowed = space.allowed_departments or []
            user_dept = getattr(user, 'department', '')
            if user_dept in allowed:
                accessible.append(space.id)

    return accessible


def semantic_search(query: str, space_ids: List[int] = None,
                    user=None, top_k: int = None) -> List[dict]:
    """
    语义搜索：生成问题向量 → pgvector 余弦相似度搜索

    Args:
        query: 用户问题
        space_ids: 限定的知识空间（None=用户可访问的全部）
        user: 当前用户（权限过滤）
        top_k: 返回条数

    Returns:
        [{"chunk_id", "content", "score", "doc_id", "doc_title", "space_name", ...}]
    """
    top_k = top_k or MAX_CONTEXT_CHUNKS

    # 1. 确定可搜索的空间
    if user:
        accessible = get_accessible_space_ids(user)
        if space_ids:
            space_ids = [s for s in space_ids if s in accessible]
        else:
            space_ids = accessible

    if not space_ids:
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
    # 使用原生 SQL（pgvector 操作符 <=>）
    space_ids_str = ','.join(str(s) for s in space_ids)

    sql = sa_text(f"""
        SELECT
            kc.id AS chunk_id,
            kc.content,
            kc.metadata,
            kc.chunk_index,
            kd.id AS doc_id,
            kd.title AS doc_title,
            kd.is_authoritative,
            kd.priority_weight,
            kd.file_library_id,
            ks.name AS space_name,
            1 - (kc.embedding <=> :query_vec) AS similarity
        FROM knowledge_chunks kc
        JOIN knowledge_documents kd ON kd.id = kc.document_id
        JOIN knowledge_spaces ks ON ks.id = kd.space_id
        WHERE kd.space_id IN ({space_ids_str})
          AND kd.status = 'ready'
          AND kd.expired_at IS NULL
        ORDER BY
            (1 - (kc.embedding <=> :query_vec))
            * kd.priority_weight
            * CASE WHEN kd.is_authoritative THEN 2.0 ELSE 1.0 END
            DESC
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
            'is_authoritative': row.is_authoritative,
            'file_library_id': row.file_library_id,
            'space_name': row.space_name,
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
        if chunk.get('space_name'):
            source_info += f" (知识空间: {chunk['space_name']})"
        context_parts.append(f"{source_info}\n{chunk['content']}")

    context = '\n\n---\n\n'.join(context_parts)

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f"## 参考文档\n\n{context}\n\n## 用户问题\n\n{question}"},
    ]

    return messages


def ask_stream(question: str, user=None, space_ids: List[int] = None,
               session_id: int = None) -> Generator[str, None, None]:
    """
    流式问答 — SSE 使用

    Yields:
        SSE data 格式的 JSON 字符串
    """
    import json

    # 1. 搜索相关文档
    chunks = semantic_search(question, space_ids=space_ids, user=user)

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
            'space_name': c.get('space_name', ''),
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

    full_answer = ''
    for token in chat_completion_stream(messages):
        full_answer += token
        yield f"data: {json.dumps({'type': 'content', 'text': token}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done', 'sources': unique_sources}, ensure_ascii=False)}\n\n"

    # 4. 保存到会话历史
    if user and session_id:
        _save_message(session_id, user.id, question, full_answer, unique_sources)


def ask(question: str, user=None, space_ids: List[int] = None,
        session_id: int = None) -> dict:
    """
    非流式问答

    Returns:
        {"answer": str, "sources": [...], "tokens_used": int}
    """
    chunks = semantic_search(question, space_ids=space_ids, user=user)

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
                'space_name': c.get('space_name', ''),
                'file_library_id': c.get('file_library_id'),
            })

    if user and session_id:
        _save_message(session_id, user.id, question, answer, sources)

    return {
        'answer': answer,
        'sources': sources,
        'tokens_used': tokens_used,
    }


def _save_message(session_id: int, user_id: int, question: str,
                  answer: str, sources: list):
    """保存问答消息到会话"""
    try:
        session = KnowledgeChatSession.query.get(session_id)
        if not session or session.user_id != user_id:
            return

        # 用户消息
        user_msg = KnowledgeChatMessage(
            session_id=session_id,
            role='user',
            content=question,
        )
        db.session.add(user_msg)

        # AI 回答
        ai_msg = KnowledgeChatMessage(
            session_id=session_id,
            role='assistant',
            content=answer,
            sources=sources,
        )
        db.session.add(ai_msg)

        # 更新会话标题（首次提问时）
        if not session.title:
            session.title = question[:50] + ('...' if len(question) > 50 else '')

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存消息失败: {e}")
