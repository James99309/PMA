# -*- coding: utf-8 -*-
"""Lint 质检服务单元测试（mock Claude，实 PG）"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv


@pytest.fixture(scope='session', autouse=True)
def _load_env():
    load_dotenv('.env')
    load_dotenv('.env.local', override=True)


@pytest.fixture
def wiki_root(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv('WIKI_ROOT', tmp)
        yield Path(tmp)


@pytest.fixture
def app_ctx(wiki_root):
    from app import create_app
    app = create_app()
    with app.app_context():
        yield app


@pytest.fixture
def test_articles(app_ctx):
    from app import db
    from app.models.knowledge import KnowledgeWikiArticle
    from app.services.wiki.storage import write_article

    # 前置清理防止残留
    KnowledgeWikiArticle.query.filter(
        KnowledgeWikiArticle.slug.like('test-l-%')
    ).delete(synchronize_session=False)
    db.session.commit()

    write_article('product', 'test-l-gp328p', '# GP328P\n\n内容\n')
    a1 = KnowledgeWikiArticle(
        topic='product', slug='test-l-gp328p', title='GP328P 概述',
        file_path='wiki/product/test-l-gp328p.md',
        summary='VHF 5W 对讲机',
        outbound_refs=['product/test-l-ghost'],  # 坏链接
    )
    write_article('product', 'test-l-gp538', '# GP538\n\n内容\n')
    a2 = KnowledgeWikiArticle(
        topic='product', slug='test-l-gp538', title='GP538 概述',
        file_path='wiki/product/test-l-gp538.md',
        summary='',  # 空 summary
        outbound_refs=[],
    )
    db.session.add_all([a1, a2])
    db.session.commit()
    yield

    KnowledgeWikiArticle.query.filter(
        KnowledgeWikiArticle.slug.like('test-l-%')
    ).delete(synchronize_session=False)
    db.session.commit()


# ══════════════════════════════════════════════════════════════════
# 测试
# ══════════════════════════════════════════════════════════════════

def test_lint_reports_issues_without_auto_fix(app_ctx, wiki_root, test_articles):
    from app.services.wiki.linter import lint_wiki

    fake_payload = {
        'issues': [
            {
                'severity': 'error',
                'type': 'broken_link',
                'article': 'product/test-l-gp328p',
                'message': '指向 product/test-l-ghost 的链接不存在',
                'auto_fixable': True,
            },
            {
                'severity': 'warning',
                'type': 'missing_summary',
                'article': 'product/test-l-gp538',
                'message': 'summary 为空',
                'auto_fixable': False,
            },
        ],
        'auto_fixes': [
            {
                'article': 'product/test-l-gp328p',
                'new_content': '# GP328P\n\n修复后内容\n',
                'description': '删除坏链接',
            }
        ],
        'summary': '2 个问题，其中 1 个可自动修复',
    }
    fake_resp = MagicMock()
    fake_resp.text = json.dumps(fake_payload, ensure_ascii=False)
    fake_resp.usage = {'input_tokens': 100, 'output_tokens': 50, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = fake_resp

    result = lint_wiki(apply_auto_fixes=False, claude=fake_client)

    assert len(result['issues']) == 2
    assert result['auto_fixes_applied'] == 0  # 没有应用
    assert result['article_count'] == 2

    # 磁盘文件没被修改
    content = (wiki_root / 'wiki' / 'product' / 'test-l-gp328p.md').read_text()
    assert '修复后内容' not in content


def test_lint_applies_auto_fixes(app_ctx, wiki_root, test_articles):
    from app.services.wiki.linter import lint_wiki
    from app.models.knowledge import KnowledgeWikiArticle

    fake_payload = {
        'issues': [],
        'auto_fixes': [
            {
                'article': 'product/test-l-gp328p',
                'new_content': '# GP328P 修复版\n\n删除了坏链接\n',
                'description': '删除 See Also 的坏链接',
            }
        ],
        'summary': 'auto-fix 应用',
    }
    fake_resp = MagicMock()
    fake_resp.text = json.dumps(fake_payload, ensure_ascii=False)
    fake_resp.usage = {'input_tokens': 100, 'output_tokens': 50, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = fake_resp

    result = lint_wiki(apply_auto_fixes=True, claude=fake_client)

    assert result['auto_fixes_applied'] == 1

    # 磁盘文件被修改
    content = (wiki_root / 'wiki' / 'product' / 'test-l-gp328p.md').read_text()
    assert 'GP328P 修复版' in content

    # DB 记录更新
    art = KnowledgeWikiArticle.query.filter_by(slug='test-l-gp328p').first()
    assert art.content_length == len('# GP328P 修复版\n\n删除了坏链接\n')
    assert art.last_compiled_at is not None


def test_lint_empty_wiki(app_ctx):
    from app.services.wiki.linter import lint_wiki
    fake_client = MagicMock()
    result = lint_wiki(claude=fake_client)
    fake_client.complete.assert_not_called()
    assert result['article_count'] == 0
    assert result['issues'] == []


def test_lint_topic_filter(app_ctx, test_articles):
    from app.services.wiki.linter import lint_wiki

    fake_resp = MagicMock()
    fake_resp.text = '{"issues": [], "auto_fixes": [], "summary": "ok"}'
    fake_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = fake_resp

    result = lint_wiki(topic='nonexistent', claude=fake_client)
    assert result['article_count'] == 0


def test_lint_auto_fix_skip_nonexistent_article(app_ctx, wiki_root, test_articles):
    """auto_fix 指向不存在的文章应该跳过而不是崩溃。"""
    from app.services.wiki.linter import lint_wiki

    fake_payload = {
        'issues': [],
        'auto_fixes': [
            {
                'article': 'product/not-existing-slug',
                'new_content': '# ghost\n',
                'description': '幽灵修复',
            }
        ],
        'summary': 'test',
    }
    fake_resp = MagicMock()
    fake_resp.text = json.dumps(fake_payload, ensure_ascii=False)
    fake_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = fake_resp

    result = lint_wiki(apply_auto_fixes=True, claude=fake_client)
    assert result['auto_fixes_applied'] == 0  # 跳过，不计入
