# -*- coding: utf-8 -*-
"""app/services/wiki/storage.py 的单元测试

用临时目录做 WIKI_ROOT，避免污染真实的 storage/knowledge_base。
"""
import os
import tempfile
from pathlib import Path

import pytest

from app import create_app


@pytest.fixture
def wiki_root(monkeypatch):
    """给每个测试用一个临时 WIKI_ROOT。"""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv('WIKI_ROOT', tmp)
        yield Path(tmp)


@pytest.fixture
def app_ctx(wiki_root):
    """PMA Flask app context —— storage 模块通过 current_app 解析路径，需要。"""
    app = create_app()
    with app.app_context():
        yield app


# ══════════════════════════════════════════════════════════════════
# ensure_wiki_structure 首次建目录
# ══════════════════════════════════════════════════════════════════

def test_ensure_wiki_structure_creates_dirs_and_placeholders(app_ctx, wiki_root):
    from app.services.wiki.paths import (
        ensure_wiki_structure, get_raw_dir, get_wiki_dir, get_index_path, get_log_path
    )

    ensure_wiki_structure()

    assert get_raw_dir().exists() and get_raw_dir().is_dir()
    assert get_wiki_dir().exists() and get_wiki_dir().is_dir()
    assert get_index_path().exists()
    assert get_log_path().exists()

    idx = get_index_path().read_text(encoding='utf-8')
    assert '# PMA Wiki 知识库索引' in idx


def test_ensure_wiki_structure_is_idempotent(app_ctx):
    from app.services.wiki.paths import ensure_wiki_structure, get_index_path

    ensure_wiki_structure()
    # 人工改动 index.md 的内容
    get_index_path().write_text('# 我的自定义索引\n', encoding='utf-8')

    # 再次调用不应覆盖已有文件
    ensure_wiki_structure()
    assert '我的自定义索引' in get_index_path().read_text(encoding='utf-8')


# ══════════════════════════════════════════════════════════════════
# write_article / read_article_content 往返一致
# ══════════════════════════════════════════════════════════════════

def test_write_and_read_article(app_ctx):
    from app.services.wiki.storage import write_article, read_article_content

    body = '# GP328P 产品概述\n\n核心规格 ...\n'
    rel_path = write_article('product', 'gp328p', body)

    assert rel_path == 'wiki/product/gp328p.md'
    assert read_article_content(rel_path) == body


def test_read_article_missing_returns_empty(app_ctx):
    from app.services.wiki.storage import read_article_content

    assert read_article_content('wiki/does/not/exist.md') == ''


def test_list_topics_and_articles(app_ctx):
    from app.services.wiki.storage import write_article, list_topics, list_articles_in_topic

    write_article('product', 'gp328p', '# A\n')
    write_article('product', 'gp538', '# B\n')
    write_article('competitor', 'hytera', '# C\n')

    assert list_topics() == ['competitor', 'product']
    assert list_articles_in_topic('product') == ['gp328p', 'gp538']
    assert list_articles_in_topic('empty') == []


# ══════════════════════════════════════════════════════════════════
# append_log 追加
# ══════════════════════════════════════════════════════════════════

def test_append_log_accumulates(app_ctx):
    from app.services.wiki.storage import append_log
    from app.services.wiki.paths import get_log_path

    append_log('ingest', '吸收了 gp328p-datasheet.pdf')
    append_log('lint', '发现 2 个孤岛文章')

    content = get_log_path().read_text(encoding='utf-8')
    assert '— ingest' in content
    assert '— lint' in content
    assert 'gp328p-datasheet.pdf' in content
    assert '孤岛文章' in content


# ══════════════════════════════════════════════════════════════════
# save_raw_file / read_raw_file_text
# ══════════════════════════════════════════════════════════════════

def test_save_and_read_md_raw(app_ctx):
    from app.services.wiki.storage import save_raw_file, read_raw_file_text

    rel = save_raw_file('product', 'sample.md', b'# Hello\n\nWorld')
    assert rel == 'raw/product/sample.md'

    text = read_raw_file_text(rel)
    assert 'Hello' in text
    assert 'World' in text


def test_save_and_read_txt_raw(app_ctx):
    from app.services.wiki.storage import save_raw_file, read_raw_file_text

    rel = save_raw_file('notes', 'test.txt', '纯文本内容\n第二行'.encode('utf-8'))
    text = read_raw_file_text(rel)
    assert '纯文本内容' in text
    assert '第二行' in text


def test_read_raw_unsupported_type_raises(app_ctx):
    from app.services.wiki.storage import save_raw_file, read_raw_file_text

    rel = save_raw_file('misc', 'weird.xyz', b'binary')
    with pytest.raises(ValueError, match='不支持的原始文件类型'):
        read_raw_file_text(rel)


def test_read_raw_missing_file_raises(app_ctx):
    from app.services.wiki.storage import read_raw_file_text

    with pytest.raises(FileNotFoundError):
        read_raw_file_text('raw/nowhere/ghost.md')


# ══════════════════════════════════════════════════════════════════
# 文件名规范化
# ══════════════════════════════════════════════════════════════════

def test_safe_filename_keeps_cjk(app_ctx):
    from app.services.wiki.storage import safe_filename
    assert safe_filename('产品手册 v2.pdf') == '产品手册_v2.pdf'


def test_dated_filename_prefix(app_ctx):
    from app.services.wiki.storage import dated_filename
    import re
    out = dated_filename('abc.pdf')
    assert re.match(r'\d{4}-\d{2}-\d{2}-abc\.pdf', out)


# ══════════════════════════════════════════════════════════════════
# delete 操作
# ══════════════════════════════════════════════════════════════════

def test_delete_article(app_ctx):
    from app.services.wiki.storage import write_article, delete_article, read_article_content

    write_article('product', 'temp', '# tmp\n')
    assert delete_article('product', 'temp') is True
    assert read_article_content('wiki/product/temp.md') == ''
    # 再删一次返回 False
    assert delete_article('product', 'temp') is False


# ══════════════════════════════════════════════════════════════════
# C1: 路径穿越防护（安全测试）
# ══════════════════════════════════════════════════════════════════

def test_validate_topic_rejects_traversal(app_ctx):
    from app.services.wiki.storage import validate_topic, WikiPathError

    # 合法
    validate_topic('product')
    validate_topic('competitor_v2')
    validate_topic('test-123')

    # 非法
    for bad in [
        '../etc',
        '../../etc',
        'foo/bar',
        'foo\\bar',
        '',
        ' product ',
        'foo bar',
        '产品',  # CJK 不允许在 topic
        'a' * 101,  # 超长
        None,
    ]:
        with pytest.raises(WikiPathError):
            validate_topic(bad)


def test_validate_slug_rejects_traversal(app_ctx):
    from app.services.wiki.storage import validate_slug, WikiPathError

    validate_slug('gp328p-overview')
    validate_slug('v2.1')
    validate_slug('abc_def')

    for bad in [
        '../secrets',
        '.hidden',
        '',
        ' slug ',
        'has/slash',
        '产品',
        'a' * 201,
    ]:
        with pytest.raises(WikiPathError):
            validate_slug(bad)


def test_write_article_blocks_traversal(app_ctx, wiki_root):
    from app.services.wiki.storage import write_article, WikiPathError

    # 恶意 topic
    with pytest.raises(WikiPathError):
        write_article('../../../etc', 'passwd', 'hacked')

    # 恶意 slug
    with pytest.raises(WikiPathError):
        write_article('product', '../evil', 'hacked')

    # 隐藏文件 slug
    with pytest.raises(WikiPathError):
        write_article('product', '.secret', 'hacked')

    # 确认恶意路径都没被创建
    assert not (wiki_root / 'etc').exists()
    assert not (wiki_root / 'wiki' / 'evil').exists()


def test_save_raw_file_blocks_traversal(app_ctx, wiki_root):
    from app.services.wiki.storage import save_raw_file, WikiPathError

    with pytest.raises(WikiPathError):
        save_raw_file('../../../tmp', 'pwn.md', b'hacked')

    assert not (wiki_root.parent / 'tmp' / 'pwn.md').exists()


def test_read_raw_file_blocks_traversal(app_ctx):
    from app.services.wiki.storage import read_raw_file_text, WikiPathError

    with pytest.raises(WikiPathError):
        read_raw_file_text('../../../../etc/passwd')


def test_delete_raw_file_refuses_out_of_root(app_ctx, wiki_root):
    """若 raw_path 指向 wiki_root 以外，delete 返回 False 不执行。"""
    from app.services.wiki.storage import delete_raw_file
    assert delete_raw_file('../../../etc/passwd') is False


def test_safe_filename_cleans_path_separators(app_ctx):
    from app.services.wiki.storage import safe_filename
    assert '/' not in safe_filename('path/to/evil.pdf')
    assert '\\' not in safe_filename('path\\to\\evil.pdf')
    # 前导 . 被去掉
    assert not safe_filename('.hidden').startswith('.')


# ══════════════════════════════════════════════════════════════════
# 资源目录 / 图片保存 / .history 备份 / sha256
# ══════════════════════════════════════════════════════════════════

def test_assets_dir_path(app_ctx):
    from app.services.wiki.paths import assets_dir_for_article
    p = assets_dir_for_article('product', 'gp328p')
    assert p.name == 'gp328p'
    assert p.parent.name == '_assets'
    assert p.parent.parent.name == 'product'


def test_save_article_image_creates_file_and_returns_relative_path(app_ctx, wiki_root):
    from app.services.wiki.storage import save_article_image
    rel = save_article_image('product', 'gp328p', 1, b'\x89PNG\r\n\x1a\n...', 'image/png')
    assert rel == '_assets/gp328p/img-1.png'
    abs_path = wiki_root / 'wiki' / 'product' / rel
    assert abs_path.exists()
    assert abs_path.read_bytes() == b'\x89PNG\r\n\x1a\n...'


def test_replace_article_image_backs_up_old_to_history(app_ctx, wiki_root):
    from app.services.wiki.storage import save_article_image, replace_article_image
    save_article_image('product', 'gp328p', 1, b'OLD', 'image/png')
    replace_article_image('product', 'gp328p', 1, b'NEW', 'image/png')
    abs_path = wiki_root / 'wiki' / 'product' / '_assets' / 'gp328p' / 'img-1.png'
    assert abs_path.read_bytes() == b'NEW'
    history = list((abs_path.parent / '.history').glob('img-1.png.*.bak'))
    assert len(history) == 1
    assert history[0].read_bytes() == b'OLD'


def test_save_article_image_rejects_unsupported_media_type(app_ctx):
    from app.services.wiki.storage import save_article_image
    with pytest.raises(ValueError):
        save_article_image('product', 'gp328p', 1, b'data', 'application/pdf')


def test_save_article_image_rejects_zero_or_negative_index(app_ctx):
    from app.services.wiki.storage import save_article_image
    with pytest.raises(ValueError):
        save_article_image('product', 'gp328p', 0, b'd', 'image/png')


def test_sha256_bytes_returns_hex_digest(app_ctx):
    from app.services.wiki.storage import sha256_bytes
    h = sha256_bytes(b'hello')
    assert len(h) == 64
    assert h == '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
