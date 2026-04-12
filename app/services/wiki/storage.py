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
# 安全性：topic / slug / 文件名验证
# ══════════════════════════════════════════════════════════════════
#
# topic 和 slug 最终会被拼到磁盘路径里，必须严格校验防止路径穿越。
# 输入来源包括用户表单（add_raw_file 视图）和 Claude 返回的 JSON
# （对抗性 PDF 的 prompt injection 可能操纵 Claude 输出恶意 slug）。
#
# 规则（通过才放行）：
# - topic: [A-Za-z0-9_-]+，长度 1-100
# - slug:  [A-Za-z0-9._-]+，长度 1-200，不能以 . 开头（禁止 ../ 或隐藏文件）
#
# 不允许 CJK 的原因：主流场景下 topic/slug 都是英文短标识符（product、
# gp328p-overview 这种），保留 ASCII 限制可以完全杜绝各种 Unicode 同形
# 字符绕过。raw 文件的原始标题允许 CJK（走 safe_filename 另一条路径）。

_TOPIC_RE = re.compile(r'^[A-Za-z0-9_-]{1,100}$')
_SLUG_RE = re.compile(r'^[A-Za-z0-9._-]{1,200}$')
_SAFE_FILENAME_RE = re.compile(r'[^A-Za-z0-9\u4e00-\u9fff._-]+')


class WikiPathError(ValueError):
    """topic/slug/文件名非法时抛出"""


def validate_topic(topic: str) -> None:
    """校验 topic。不合规则抛 WikiPathError。"""
    if not isinstance(topic, str) or not _TOPIC_RE.match(topic):
        raise WikiPathError(
            f'非法 topic: {topic!r}（仅允许 1-100 个 ASCII 字母/数字/_/-）'
        )


def validate_slug(slug: str) -> None:
    """校验 slug。不合规则抛 WikiPathError。"""
    if not isinstance(slug, str) or not _SLUG_RE.match(slug) or slug.startswith('.'):
        raise WikiPathError(
            f'非法 slug: {slug!r}（仅允许 1-200 个 ASCII 字母/数字/./_/-，不能以 . 开头）'
        )


def validate_topic_slug(topic: str, slug: str) -> None:
    """同时校验 topic 和 slug。"""
    validate_topic(topic)
    validate_slug(slug)


def safe_filename(raw_name: str) -> str:
    """把任意字符串转成磁盘安全的文件名（保留汉字/数字/字母/. _ -）。

    用于 raw 文件的原始文件名保留显示。注意这不是 slug —— slug 必须走
    validate_slug，CJK 是不允许的。
    """
    name = _SAFE_FILENAME_RE.sub('_', raw_name.strip())
    # 防止跨目录：去掉路径分隔符和前导 .
    name = name.replace('/', '_').replace('\\', '_').lstrip('.')
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

    Raises:
        WikiPathError: topic/slug 非法
    """
    validate_topic_slug(topic, slug)
    path = wiki_article_path(topic, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return str(path.relative_to(get_wiki_root()))


def delete_article(topic: str, slug: str) -> bool:
    """删除一篇文章文件。返回是否成功删除（文件不存在也算 False）。

    Raises:
        WikiPathError: topic/slug 非法
    """
    validate_topic_slug(topic, slug)
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

    Raises:
        WikiPathError: topic 非法
    """
    validate_topic(topic)
    # filename 走 safe_filename 做二次清洗（调用方通常已经调过了，这里兜底）
    filename = safe_filename(filename)
    path = raw_file_path(topic, filename)
    # 确认最终路径仍然在 raw_dir 下（双保险）
    try:
        path.resolve().relative_to(get_raw_dir().resolve())
    except ValueError:
        raise WikiPathError(f'解析后路径越出 raw 根目录: {path}')
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

    # 防止有人绕过 save_raw_file 直接调这个函数读 wiki_root 以外的文件
    abs_path = (get_wiki_root() / raw_path).resolve()
    try:
        abs_path.relative_to(get_wiki_root().resolve())
    except ValueError:
        raise WikiPathError(f'raw_path 越出 wiki 根目录: {raw_path!r}')

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
    """删除原始文件。返回是否真的删除。

    防止路径穿越：解析后必须仍在 raw_dir 下。
    """
    if not raw_path:
        return False
    abs_path = (get_wiki_root() / raw_path).resolve()
    try:
        abs_path.relative_to(get_raw_dir().resolve())
    except ValueError:
        logger.warning(f'[Wiki] delete_raw_file 拒绝越界路径: {raw_path!r}')
        return False
    if abs_path.exists():
        abs_path.unlink()
        return True
    return False
