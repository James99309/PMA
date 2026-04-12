# -*- coding: utf-8 -*-
"""Query 问答服务单元测试（mock Claude，实 PG）"""
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
    """塞几篇测试文章到 DB + 磁盘，yield 前先清理残留，yield 后再清理。"""
    from app import db
    from app.models.knowledge import KnowledgeWikiArticle
    from app.services.wiki.storage import write_article

    def _cleanup():
        KnowledgeWikiArticle.query.filter(
            KnowledgeWikiArticle.slug.like('test-q-%')
        ).delete(synchronize_session=False)
        db.session.commit()

    # 前置清理 —— 防止上一次失败的测试残留卡 unique constraint
    _cleanup()

    fixtures = [
        ('product', 'test-q-gp328p', 'GP328P 产品概述',
         'GP328P 是 VHF 5W 对讲机，IP67 防护',
         '# GP328P\n\n频段 VHF 136-174 MHz，功率 5W，防护 IP67，电池 2000mAh 待机 16 小时。\n'),
        ('product', 'test-q-gp538', 'GP538 高功率型号',
         'GP538 UHF 8W 高功率商用对讲机',
         '# GP538\n\n频段 UHF 400-470 MHz，功率 8W，适合大型活动和远距离通信。\n'),
        ('competitor', 'test-q-hytera', 'Hytera TC-320 对比分析',
         'Hytera TC-320 vs Evertac GP328P 销售对比',
         '# Hytera TC-320 对比\n\nTC-320 支持加密通话，价格比 GP328P 高 15%。\n'),
    ]
    for topic, slug, title, summary, content in fixtures:
        fp = write_article(topic, slug, content)
        art = KnowledgeWikiArticle(
            topic=topic, slug=slug, title=title, file_path=fp,
            summary=summary, content_length=len(content),
            source_raw_ids=[], outbound_refs=[],
        )
        db.session.add(art)
    db.session.commit()
    created_ids = [a.id for a in KnowledgeWikiArticle.query.filter(
        KnowledgeWikiArticle.slug.like('test-q-%')
    ).all()]

    yield created_ids

    _cleanup()


# ══════════════════════════════════════════════════════════════════
# 测试
# ══════════════════════════════════════════════════════════════════

def test_query_hits_by_keyword(app_ctx, test_articles):
    """关键词能召回对应文章。"""
    from app.services.wiki.querier import query_wiki

    fake_resp = MagicMock()
    fake_resp.text = '根据 Wiki，GP328P 是 VHF 5W 对讲机...[GP328P 产品概述](product/test-q-gp328p.md)'
    fake_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = fake_resp

    result = query_wiki('GP328P 的防护等级', claude=fake_client)

    assert result['search_hit_count'] >= 1
    slugs = [c['slug'] for c in result['cited_articles']]
    assert 'test-q-gp328p' in slugs

    # prompt 里应该包含该文章的正文
    user_prompt = fake_client.complete.call_args.kwargs['user']
    assert 'IP67' in user_prompt
    assert '用户问题' in user_prompt


def test_query_topic_filter(app_ctx, test_articles):
    from app.services.wiki.querier import query_wiki

    fake_resp = MagicMock()
    fake_resp.text = 'answer'
    fake_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = fake_resp

    result = query_wiki('对讲机', topic='competitor', claude=fake_client)

    # 只应命中 competitor topic
    for c in result['cited_articles']:
        assert c['topic'] == 'competitor'


def test_query_no_hit_falls_back(app_ctx, test_articles):
    """全文检索 0 命中，退化为最近更新的 top_k 文章。"""
    from app.services.wiki.querier import query_wiki

    fake_resp = MagicMock()
    fake_resp.text = 'fallback answer'
    fake_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = fake_resp

    # 查询一个跟测试数据完全无关的词
    result = query_wiki('quantum cryptography elephant', claude=fake_client)

    assert result['search_hit_count'] == 0
    assert len(result['cited_articles']) > 0  # 退化不是空


def test_query_empty_wiki_returns_no_data(app_ctx):
    """空 Wiki 直接返回提示，不调用 Claude。"""
    from app.services.wiki.querier import query_wiki

    fake_client = MagicMock()
    result = query_wiki('任何问题', claude=fake_client)

    fake_client.complete.assert_not_called()
    assert '暂无任何文章' in result['answer']


def test_query_empty_question_raises(app_ctx):
    from app.services.wiki.querier import query_wiki, QueryError
    with pytest.raises(QueryError, match='不能为空'):
        query_wiki('  ')
