# -*- coding: utf-8 -*-
"""
Chat 文件处理器：把 ChatMessage 附件转成 Claude content block

支持：
    - 图片 (jpg/png/webp/gif) → image content block (Claude Vision)
    - PDF → document content block (Claude 原生解析，文字+扫描都行)
    - docx → 提取文本 → text content block
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from app.services.cli_agent import conversation as conv

logger = logging.getLogger(__name__)

# ─── 限制 ──────────────────────────────────────────────────────────────
MAX_FILES_PER_MESSAGE = 5
MAX_IMAGE_SIZE = 20 * 1024 * 1024   # 20 MB (Claude 限制)
MAX_PDF_SIZE = 32 * 1024 * 1024     # 32 MB
MAX_SPREADSHEET_ROWS = 500  # 表格最多读取行数，避免 token 爆炸
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
PDF_EXTS = {'.pdf'}
DOCX_EXTS = {'.docx'}
EXCEL_EXTS = {'.xlsx', '.xls'}
CSV_EXTS = {'.csv'}
SUPPORTED_EXTS = IMAGE_EXTS | PDF_EXTS | DOCX_EXTS | EXCEL_EXTS | CSV_EXTS

# 图片扩展名 → MIME
_IMAGE_MIME = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
}


def get_pending_file_messages(conversation_id: int, limit: int = MAX_FILES_PER_MESSAGE) -> list:
    """查询对话中尚未被 AI 处理的文件/图片消息（按时间正序）。"""
    from app.models.chat import ChatMessage

    return (
        ChatMessage.query
        .filter_by(conversation_id=conversation_id, is_deleted=False, ai_processed=False)
        .filter(ChatMessage.message_type.in_(['image', 'file']))
        .filter(ChatMessage.file_url.isnot(None))
        .order_by(ChatMessage.id.asc())
        .limit(limit)
        .all()
    )


def build_file_content_blocks(file_messages: list) -> list[dict]:
    """把一批 ChatMessage 文件消息转成 Claude content block 列表。

    返回: [content_block, ...] — 可直接拼入 user message 的 content 数组。
    跳过不支持 / 读取失败的文件（静默 warn，不中断对话）。
    """
    blocks: list[dict] = []
    for msg in file_messages:
        try:
            block = _process_single_file(msg)
            if block:
                blocks.append(block)
        except Exception:
            logger.warning(f'[FileProcessor] 处理文件失败 msg_id={msg.id}', exc_info=True)
    return blocks


def mark_files_processed(file_messages: list) -> None:
    """把这些文件消息标记为已处理。调用方负责 commit。"""
    for msg in file_messages:
        msg.ai_processed = True


# ─── 内部实现 ──────────────────────────────────────────────────────────

def _process_single_file(msg) -> dict | None:
    """处理单条文件消息，返回一个 content block 或 None。"""
    file_name = msg.file_name or ''
    ext = Path(file_name).suffix.lower()

    if ext not in SUPPORTED_EXTS:
        logger.info(f'[FileProcessor] 跳过不支持的文件类型: {file_name} ({ext})')
        return None

    file_bytes = _read_file_bytes(msg.file_url)
    if not file_bytes:
        logger.warning(f'[FileProcessor] 无法读取文件: {msg.file_url}')
        return None

    if ext in IMAGE_EXTS:
        return _build_image_block(file_bytes, ext)
    elif ext in PDF_EXTS:
        return _build_pdf_block(file_bytes)
    elif ext in DOCX_EXTS:
        return _build_docx_block(file_bytes, file_name)
    elif ext in EXCEL_EXTS:
        return _build_excel_block(file_bytes, file_name)
    elif ext in CSV_EXTS:
        return _build_csv_block(file_bytes, file_name)
    return None


def _read_file_bytes(file_url: str) -> bytes | None:
    """从 NAS 或本地存储读取文件内容。"""
    if not file_url:
        return None

    # 本地回退路径: chat_files/123/xxx.png → ./storage/chat_files/123/xxx.png
    if file_url.startswith('chat_files/'):
        local_path = os.path.join('.', 'storage', file_url)
        if os.path.exists(local_path):
            with open(local_path, 'rb') as f:
                return f.read()

    # NAS 存储
    try:
        from app.utils.smart_storage_manager import get_smart_storage
        data = get_smart_storage().download_file(file_url, bucket_type='chat')
        if data:
            return data
    except Exception:
        logger.warning(f'[FileProcessor] NAS 下载失败: {file_url}', exc_info=True)

    return None


def _detect_image_mime(data: bytes, ext: str) -> str:
    """用 magic bytes 检测真实图片格式（微信等应用常把 JPEG 存成 .png）。"""
    if data[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if data[:4] == b'GIF8':
        return 'image/gif'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    return _IMAGE_MIME.get(ext, 'image/png')


def _build_image_block(data: bytes, ext: str) -> dict | None:
    if len(data) > MAX_IMAGE_SIZE:
        logger.warning(f'[FileProcessor] 图片超过 {MAX_IMAGE_SIZE // 1024 // 1024}MB 限制，跳过')
        return None
    media_type = _detect_image_mime(data, ext)
    b64 = base64.b64encode(data).decode('ascii')
    return conv.image_block(b64, media_type)


def _build_pdf_block(data: bytes) -> dict | None:
    if len(data) > MAX_PDF_SIZE:
        logger.warning(f'[FileProcessor] PDF 超过 {MAX_PDF_SIZE // 1024 // 1024}MB 限制，跳过')
        return None
    b64 = base64.b64encode(data).decode('ascii')
    return conv.document_block(b64, 'application/pdf')


def _build_docx_block(data: bytes, file_name: str) -> dict | None:
    """提取 docx 文本，返回 text block。"""
    try:
        from docx import Document
        import io
        doc = Document(io.BytesIO(data))
        text = '\n\n'.join(p.text for p in doc.paragraphs if p.text.strip())
        if not text.strip():
            logger.info(f'[FileProcessor] docx 无可提取文本: {file_name}')
            return None
        return conv.text_block(f'[文件: {file_name}]\n{text}')
    except ImportError:
        logger.warning('[FileProcessor] python-docx 未安装，无法处理 docx')
        return None


def _build_excel_block(data: bytes, file_name: str) -> dict | None:
    """读取 Excel 表格，转成 Markdown 表格文本。"""
    try:
        import pandas as pd
        import io

        xlsx = pd.ExcelFile(io.BytesIO(data), engine='openpyxl')
        parts: list[str] = []
        for sheet_name in xlsx.sheet_names:
            df = pd.read_excel(xlsx, sheet_name=sheet_name, nrows=MAX_SPREADSHEET_ROWS)
            if df.empty:
                continue
            header = f'### Sheet: {sheet_name} ({len(df)} 行)'
            table = df.to_markdown(index=False)
            parts.append(f'{header}\n{table}')
            if len(df) >= MAX_SPREADSHEET_ROWS:
                parts.append(f'（仅显示前 {MAX_SPREADSHEET_ROWS} 行）')

        if not parts:
            logger.info(f'[FileProcessor] Excel 无数据: {file_name}')
            return None
        return conv.text_block(f'[文件: {file_name}]\n\n' + '\n\n'.join(parts))
    except Exception:
        logger.warning(f'[FileProcessor] Excel 解析失败: {file_name}', exc_info=True)
        return None


def _build_csv_block(data: bytes, file_name: str) -> dict | None:
    """读取 CSV 文件，转成 Markdown 表格文本。"""
    try:
        import pandas as pd
        import io

        for encoding in ('utf-8', 'gbk', 'gb2312', 'latin-1'):
            try:
                df = pd.read_csv(io.BytesIO(data), encoding=encoding, nrows=MAX_SPREADSHEET_ROWS)
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        else:
            logger.warning(f'[FileProcessor] CSV 编码识别失败: {file_name}')
            return None

        if df.empty:
            return None
        table = df.to_markdown(index=False)
        header = f'[文件: {file_name}] ({len(df)} 行)'
        if len(df) >= MAX_SPREADSHEET_ROWS:
            header += f'（仅显示前 {MAX_SPREADSHEET_ROWS} 行）'
        return conv.text_block(f'{header}\n{table}')
    except Exception:
        logger.warning(f'[FileProcessor] CSV 解析失败: {file_name}', exc_info=True)
        return None
