# -*- coding: utf-8 -*-
"""Wiki 文章、原始文件、index/log 的 I/O 层

所有路径读写都经过本模块，避免散落在各处直接操作磁盘。
读出的文章路径统一是相对 wiki_root 的字符串，例如
    wiki/product/gp328p-overview.md
    raw/product/2026-04-09-datasheet.pdf
"""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List
from zoneinfo import ZoneInfo

from app.services.wiki.paths import (
    get_index_path,
    get_log_path,
    get_raw_dir,
    get_wiki_dir,
    get_wiki_root,
    raw_file_path,
    wiki_article_path,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# slug 与 filename 规范化
# ══════════════════════════════════════════════════════════════════

_SAFE_FILENAME_RE = re.compile(r'[^A-Za-z0-9\u4e00-\u9fff._-]+')


def safe_filename(raw_name: str) -> str:
    """把任意字符串转成磁盘安全的文件名（保留汉字/数字/字母/. _ -）。"""
    name = _SAFE_FILENAME_RE.sub('_', raw_name.strip())
    return name or 'unnamed'


def dated_filename(original: str) -> str:
    """在文件名前加上 YYYY-MM-DD 前缀，便于按时间排序。"""
    today = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d')
    return f'{today}-{safe_filename(original)}'


# ══════════════════════════════════════════════════════════════════
# Wiki 文章读写
# ══════════════════════════════════════════════════════════════════

def read_article_content(file_path: str) -> str:
    """按相对路径读文章。file_path 形如 'wiki/product/xxx.md'。

    读不到时返回空字符串，方便调用方做降级。
    """
    if not file_path:
        return ''
    abs_path = get_wiki_root() / file_path
    if not abs_path.exists():
        logger.warning(f'Wiki 文章文件不存在: {abs_path}')
        return ''
    return abs_path.read_text(encoding='utf-8')


def write_article(topic: str, slug: str, content: str) -> str:
    """写一篇文章到 wiki/<topic>/<slug>.md。

    返回相对 wiki_root 的路径字符串，用于存入 KnowledgeWikiArticle.file_path。
    """
    path = wiki_article_path(topic, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return str(path.relative_to(get_wiki_root()))


def delete_article(topic: str, slug: str) -> bool:
    """删除一篇文章文件。返回是否成功删除（文件不存在也算 False）。"""
    path = wiki_article_path(topic, slug)
    if path.exists():
        path.unlink()
        return True
    return False


def list_topics() -> List[str]:
    """列出 wiki/ 目录下所有 topic（一级子目录）。"""
    wiki_dir = get_wiki_dir()
    if not wiki_dir.exists():
        return []
    return sorted([p.name for p in wiki_dir.iterdir() if p.is_dir()])


def list_articles_in_topic(topic: str) -> List[str]:
    """列出某个 topic 下所有文章的 slug（不含 .md）。"""
    topic_dir = get_wiki_dir() / topic
    if not topic_dir.exists():
        return []
    return sorted([p.stem for p in topic_dir.glob('*.md')])


# ══════════════════════════════════════════════════════════════════
# index.md 与 log.md
# ══════════════════════════════════════════════════════════════════

def read_index() -> str:
    """读 wiki/index.md。不存在时返回空字符串。"""
    idx = get_index_path()
    return idx.read_text(encoding='utf-8') if idx.exists() else ''


def write_index(content: str):
    """覆盖写 wiki/index.md。"""
    idx = get_index_path()
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(content, encoding='utf-8')


def append_log(operation: str, details: str):
    """往 wiki/log.md 追加一条操作记录。

    格式：
        ## 2026-04-09 12:34:56 — ingest
        <details>
    """
    now = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    entry = f'\n## {now} — {operation}\n\n{details.rstrip()}\n'
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('a', encoding='utf-8') as f:
        f.write(entry)


# ══════════════════════════════════════════════════════════════════
# 原始文件 I/O
# ══════════════════════════════════════════════════════════════════

def save_raw_file(topic: str, filename: str, data: bytes) -> str:
    """把二进制内容写入 raw/<topic>/<filename>。

    Args:
        topic: topic 名称（将作为目录）
        filename: 建议调用方先 dated_filename(original) 规范化过
        data: 文件字节

    Returns:
        相对 wiki_root 的路径字符串，例如 'raw/product/2026-04-09-datasheet.pdf'
    """
    path = raw_file_path(topic, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(path.relative_to(get_wiki_root()))


def read_raw_file_text(raw_path: str) -> str:
    """读原始文件并尽力提取成纯文本，给 LLM 编译用。

    支持：.md / .txt / .pdf / .docx。
    其他类型抛 ValueError。
    """
    if not raw_path:
        raise ValueError('raw_path 不能为空')

    abs_path = get_wiki_root() / raw_path
    if not abs_path.exists():
        raise FileNotFoundError(f'原始文件不存在: {abs_path}')

    ext = abs_path.suffix.lower()

    if ext in ('.md', '.txt'):
        return abs_path.read_text(encoding='utf-8', errors='replace')

    if ext == '.pdf':
        # PMA 已安装 pymupdf（fitz），提取质量和性能都优于 pypdf
        try:
            import fitz  # pymupdf
        except ImportError:
            raise ImportError('需要 pymupdf 才能读取 PDF，请 pip install pymupdf')
        pages = []
        with fitz.open(str(abs_path)) as doc:
            for page in doc:
                try:
                    pages.append(page.get_text() or '')
                except Exception as e:
                    logger.warning(f'PDF 页面提取失败: {e}')
                    pages.append('')
        return '\n\n'.join(pages)

    if ext == '.docx':
        try:
            from docx import Document
        except ImportError:
            raise ImportError('需要 python-docx 包才能读取 DOCX，请 pip install python-docx')
        doc = Document(str(abs_path))
        return '\n\n'.join(p.text for p in doc.paragraphs)

    raise ValueError(f'不支持的原始文件类型: {ext}（支持 .md/.txt/.pdf/.docx）')


def delete_raw_file(raw_path: str) -> bool:
    """删除原始文件。返回是否真的删除。"""
    abs_path = get_wiki_root() / raw_path
    if abs_path.exists():
        abs_path.unlink()
        return True
    return False
