# -*- coding: utf-8 -*-
"""
知识库文档处理服务 — 分块 + 向量化 + 后台队列

处理流程:
1. 从 FileLibrary 读取文件内容
2. 文本提取 (knowledge_extraction_service)
3. 按段落/句子分块 (800字符/块, 100字符重叠)
4. 调用 Embedding API 生成向量
5. 存入 knowledge_chunks (pgvector)
"""
import os
import re
import logging
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Tuple

from flask import current_app

logger = logging.getLogger(__name__)

# 分块参数（可通过环境变量覆盖）
CHUNK_SIZE = int(os.getenv('KNOWLEDGE_CHUNK_SIZE', '800'))
CHUNK_OVERLAP = int(os.getenv('KNOWLEDGE_CHUNK_OVERLAP', '100'))
MIN_CHUNK_SIZE = 50


# ── 文本分块 ─────────────────────────────────────────────────────

def split_text_into_chunks(text: str, chunk_size: int = None, overlap: int = None) -> List[dict]:
    """
    将文本分割为固定大小的块，保留元数据。

    策略:
    1. 按双换行分段
    2. 超长段落按句子分割
    3. 相邻块重叠保持上下文

    Returns:
        [{"content": str, "metadata": {"page": int|None, ...}}]
    """
    chunk_size = chunk_size or CHUNK_SIZE
    overlap = overlap or CHUNK_OVERLAP

    if not text or not text.strip():
        return []

    # 提取页码信息
    page_pattern = re.compile(r'\[第(\d+)页\]')

    # 按双换行分段
    paragraphs = re.split(r'\n{2,}', text)

    # 将段落关联到页码
    current_page = None
    tagged_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        page_match = page_pattern.match(para)
        if page_match:
            current_page = int(page_match.group(1))
            # 去掉页码标记
            para = page_pattern.sub('', para).strip()
            if not para:
                continue
        tagged_paragraphs.append((para, current_page))

    # 合并段落为块
    chunks = []
    current_chunk = ''
    current_meta = {'page': None}

    for para, page in tagged_paragraphs:
        # 如果段落本身就超长，按句子分割
        if len(para) > chunk_size:
            # 先保存当前块
            if current_chunk.strip() and len(current_chunk.strip()) >= MIN_CHUNK_SIZE:
                chunks.append({'content': current_chunk.strip(), 'metadata': dict(current_meta)})

            sentences = _split_into_sentences(para)
            sent_chunk = ''
            for sent in sentences:
                if len(sent_chunk) + len(sent) + 1 > chunk_size and sent_chunk:
                    chunks.append({'content': sent_chunk.strip(), 'metadata': {'page': page}})
                    # 重叠
                    sent_chunk = sent_chunk[-overlap:] if overlap else ''
                sent_chunk += sent + ' '
            if sent_chunk.strip() and len(sent_chunk.strip()) >= MIN_CHUNK_SIZE:
                current_chunk = sent_chunk
                current_meta = {'page': page}
            else:
                current_chunk = ''
                current_meta = {'page': page}
            continue

        # 判断是否需要开新块
        if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
            chunks.append({'content': current_chunk.strip(), 'metadata': dict(current_meta)})
            # 重叠
            current_chunk = current_chunk[-overlap:] + '\n\n' if overlap else ''
            current_meta = {'page': page}

        current_chunk += para + '\n\n'
        if page is not None:
            current_meta['page'] = page

    # 最后一块
    if current_chunk.strip() and len(current_chunk.strip()) >= MIN_CHUNK_SIZE:
        chunks.append({'content': current_chunk.strip(), 'metadata': dict(current_meta)})

    # 为每个块编号
    for i, chunk in enumerate(chunks):
        chunk['chunk_index'] = i

    return chunks


def _split_into_sentences(text: str) -> List[str]:
    """按句子分割（中英文混合）"""
    pattern = r'(?<=[。？！.?!])\s*'
    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]


# ── 文档处理 ─────────────────────────────────────────────────────

def process_document(document_id: int, app=None):
    """
    处理单个文档：提取文本 → 分块 → 向量化 → 存入数据库。

    在后台线程中调用，需要传入 app 以获取应用上下文。
    """
    if app is None:
        app = current_app._get_current_object()

    with app.app_context():
        from app import db
        from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
        from app.services.knowledge_extraction_service import extract_text
        from app.services.knowledge_ai_service import generate_embeddings

        doc = KnowledgeDocument.query.get(document_id)
        if not doc:
            logger.error(f"文档不存在: {document_id}")
            return

        try:
            # 更新状态
            doc.status = 'processing'
            db.session.commit()

            # 1. 读取文件内容
            file_bytes = _read_file_content(doc.file_library)
            if not file_bytes:
                raise ValueError("无法读取文件内容")

            # 2. 提取文本
            text = extract_text(
                file_bytes,
                doc.file_library.original_filename,
                doc.file_library.mime_type or ''
            )
            if not text or not text.strip():
                raise ValueError("文件内容为空或不支持的格式")

            # 3. 分块
            chunks = split_text_into_chunks(text)
            if not chunks:
                raise ValueError("文本分块结果为空")

            # 4. 生成向量
            chunk_texts = [c['content'] for c in chunks]
            embeddings = generate_embeddings(chunk_texts)

            if len(embeddings) != len(chunks):
                raise ValueError(f"向量数量({len(embeddings)})与分块数量({len(chunks)})不一致")

            # 5. 事务内：删旧块 → 存新块 → 更新文档
            # 删除旧版本的 chunks
            KnowledgeChunk.query.filter_by(document_id=doc.id).delete()

            # 批量创建新 chunks
            from sqlalchemy import text as sa_text
            for chunk_data, embedding in zip(chunks, embeddings):
                # 使用原生 SQL 插入（因为 pgvector 列需要特殊处理）
                db.session.execute(
                    sa_text("""
                        INSERT INTO knowledge_chunks
                            (document_id, chunk_index, content, embedding, token_count, metadata)
                        VALUES
                            (:doc_id, :idx, :content, :embedding, :token_count, :meta)
                    """),
                    {
                        'doc_id': doc.id,
                        'idx': chunk_data['chunk_index'],
                        'content': chunk_data['content'],
                        'embedding': str(embedding),
                        'token_count': _count_tokens(chunk_data['content']),
                        'meta': _json_dumps(chunk_data.get('metadata')),
                    }
                )

            # 更新文档状态
            doc.status = 'ready'
            doc.chunk_count = len(chunks)
            doc.processing_error = None
            doc.processed_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
            doc.version += 1
            db.session.commit()

            logger.info(f"文档处理完成: {doc.title} ({len(chunks)} chunks)")

        except Exception as e:
            db.session.rollback()
            logger.error(f"文档处理失败 [{document_id}]: {e}")
            try:
                doc = KnowledgeDocument.query.get(document_id)
                if doc:
                    doc.status = 'error'
                    doc.processing_error = str(e)[:500]
                    db.session.commit()
            except Exception:
                db.session.rollback()


def process_document_async(document_id: int):
    """异步处理文档（后台线程）"""
    from flask import current_app
    app = current_app._get_current_object()

    thread = threading.Thread(
        target=process_document,
        args=(document_id, app),
        daemon=True,
        name=f'knowledge-process-{document_id}'
    )
    thread.start()
    return thread


# ── 批量处理队列 ─────────────────────────────────────────────────

def process_pending_documents(app=None):
    """处理所有 pending 状态的文档"""
    if app is None:
        app = current_app._get_current_object()

    with app.app_context():
        from app.models.knowledge import KnowledgeDocument
        pending = KnowledgeDocument.query.filter_by(status='pending').order_by(
            KnowledgeDocument.created_at
        ).limit(10).all()

        for doc in pending:
            logger.info(f"开始处理文档: {doc.title} (id={doc.id})")
            process_document(doc.id, app)


# ── 清理 ─────────────────────────────────────────────────────────

def cleanup_file_vectors(file_library_id: int):
    """当文件被永久删除时，清理对应的知识库数据"""
    from app import db
    from app.models.knowledge import KnowledgeDocument, KnowledgeChunk

    docs = KnowledgeDocument.query.filter_by(file_library_id=file_library_id).all()
    for doc in docs:
        KnowledgeChunk.query.filter_by(document_id=doc.id).delete()
        db.session.delete(doc)

    if docs:
        db.session.commit()
        logger.info(f"已清理文件 {file_library_id} 的知识库数据 ({len(docs)} 文档)")


# ── 辅助函数 ─────────────────────────────────────────────────────

def _read_file_content(file_library) -> bytes:
    """通过 SmartStorageManager 读取文件内容"""
    try:
        from app.utils.smart_storage_manager import SmartStorageManager
        manager = SmartStorageManager()

        storage_path = file_library.storage_path
        if not storage_path:
            return None

        # 如果文件已归档，先解压
        if file_library.is_archived:
            from app.services.file_manager_service import FileManagerService
            restored = FileManagerService._restore_archived_file(file_library)
            if not restored:
                return None

        content = manager.download_file(storage_path)
        return content
    except Exception as e:
        logger.error(f"读取文件内容失败 [{file_library.id}]: {e}")
        return None


def _count_tokens(text: str) -> int:
    """估算 token 数量"""
    try:
        import tiktoken
        enc = tiktoken.get_encoding('cl100k_base')
        return len(enc.encode(text))
    except Exception:
        # 粗略估算：中文1字≈1.5token, 英文1词≈1token
        return int(len(text) * 0.75)


def _json_dumps(obj) -> str:
    """JSON 序列化"""
    import json
    if obj is None:
        return None
    return json.dumps(obj, ensure_ascii=False)
