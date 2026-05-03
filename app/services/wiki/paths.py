# -*- coding: utf-8 -*-
"""Wiki 磁盘路径管理

默认根目录：<PMA_BASE>/storage/knowledge_base
可通过环境变量 WIKI_ROOT 覆盖（NAS 部署时指向挂载点）。

目录结构：
    <wiki_root>/
    ├── raw/
    │   └── <topic>/
    │       └── YYYY-MM-DD-slug.ext
    └── wiki/
        ├── index.md
        ├── log.md
        └── <topic>/
            └── <slug>.md
"""
import os
from pathlib import Path

from flask import current_app


def get_wiki_root() -> Path:
    """返回 knowledge_base 根目录。可用 WIKI_ROOT 环境变量覆盖。"""
    env = os.environ.get('WIKI_ROOT', '').strip()
    if env:
        return Path(env)
    # PMA 项目根：app/__init__.py 里的 basedir = 项目根目录
    basedir = Path(current_app.root_path).parent
    return basedir / 'storage' / 'knowledge_base'


def get_raw_dir() -> Path:
    return get_wiki_root() / 'raw'


def get_wiki_dir() -> Path:
    return get_wiki_root() / 'wiki'


def get_index_path() -> Path:
    return get_wiki_dir() / 'index.md'


def get_log_path() -> Path:
    return get_wiki_dir() / 'log.md'


def raw_file_path(topic: str, filename: str) -> Path:
    """返回某个原始文件的绝对路径。"""
    return get_raw_dir() / topic / filename


def wiki_article_path(topic: str, slug: str) -> Path:
    """返回某篇 wiki 文章的绝对路径。"""
    return get_wiki_dir() / topic / f'{slug}.md'


def assets_dir_for_article(topic: str, slug: str) -> Path:
    """返回某篇文章的 _assets 目录绝对路径，如 wiki/product/_assets/gp328p/"""
    return get_wiki_dir() / topic / '_assets' / slug


def article_image_relative_path(slug: str, index: int, ext: str) -> str:
    """返回相对 article .md 的 markdown 引用路径，如 _assets/gp328p/img-1.png"""
    return f'_assets/{slug}/img-{index}.{ext.lstrip(".")}'


def ensure_wiki_structure():
    """首次初始化目录结构与 index/log 占位内容。

    已存在的文件不会被覆盖。幂等。
    """
    get_raw_dir().mkdir(parents=True, exist_ok=True)
    get_wiki_dir().mkdir(parents=True, exist_ok=True)

    idx = get_index_path()
    if not idx.exists():
        idx.write_text(
            '# PMA Wiki 知识库索引\n\n（尚未建立文章。上传原始资料并触发 Ingest 后，LLM 会自动维护此索引。）\n',
            encoding='utf-8',
        )

    log = get_log_path()
    if not log.exists():
        log.write_text('# 操作日志\n\n本文件由 Wiki 编译器追加写入，记录每次 ingest / lint 的结果。\n',
                       encoding='utf-8')
