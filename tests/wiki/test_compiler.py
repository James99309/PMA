# -*- coding: utf-8 -*-
"""Ingest 编译服务的单元测试（mock Claude，实 PG 数据库）

策略：
- Claude 客户端用 fake 对象代替，返回预定义 JSON
- 数据库用本地真实 PG（DATABASE_URL 指向 pma_local），测试后清理自己写的记录
- WIKI_ROOT 用 tempdir，不污染真实目录

这样既验证 compiler 的 DB 写入逻辑，又不依赖任何外网 API 调用。
"""
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
def test_raw_file(app_ctx):
    """建一条 KnowledgeRawFile 记录 + 把文件写到 raw 目录，返回 raw_id。"""
    from app import db
    from app.models import User
    from app.models.file_manager import FileLibrary
    from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle
    from app.services.wiki.storage import save_raw_file

    # 前置清理防止上次失败残留
    KnowledgeWikiArticle.query.filter(
        KnowledgeWikiArticle.slug.like('test-%')
    ).delete(synchronize_session=False)
    db.session.commit()

    admin = User.query.filter_by(role='admin').first()
    assert admin, '测试需要至少一个 admin 用户'
    fl = FileLibrary.query.first()
    assert fl, '测试需要至少一个 file_library 记录'

    raw_bytes = (
        '# GP328P 产品技术白皮书\n\n'
        '## 核心规格\n'
        '- 频段：VHF 136-174 MHz\n'
        '- 功率：5W\n'
        '- 防护等级：IP67\n'
        '- 电池：2000mAh 可更换\n\n'
        '## 应用场景\n'
        '- 工地施工调度\n'
        '- 仓储物流\n'
        '- 小型活动安保\n\n'
        '## 价格定位\n'
        '单价 680 元，面向中小企业客户。\n'
    ).encode('utf-8')

    raw_path = save_raw_file('product', '2026-04-12-gp328p-spec.md', raw_bytes)

    raw = KnowledgeRawFile(
        file_library_id=fl.id,
        topic='product',
        raw_path=raw_path,
        title='GP328P 产品技术白皮书（测试用）',
        added_by=admin.id,
    )
    db.session.add(raw)
    db.session.commit()
    raw_id = raw.id

    yield raw_id

    # 清理：删除测试产生的 KnowledgeRawFile + KnowledgeWikiArticle
    from app.models.knowledge import KnowledgeWikiArticle
    KnowledgeWikiArticle.query.filter_by(topic='product').filter(
        KnowledgeWikiArticle.slug.like('test-%')
    ).delete(synchronize_session=False)
    KnowledgeRawFile.query.filter_by(id=raw_id).delete()
    db.session.commit()


# ══════════════════════════════════════════════════════════════════
# 测试
# ══════════════════════════════════════════════════════════════════

def _fake_claude_response_create(raw_id: int):
    """构造一个 "create new article" 的 fake Claude 响应。"""
    payload = {
        'operations': [
            {
                'action': 'create',
                'topic': 'product',
                'slug': 'test-gp328p-overview',
                'title': 'GP328P 产品概述（测试）',
                'content': (
                    '# GP328P 产品概述\n\n'
                    'GP328P 是 VHF 频段的 5W 对讲机，面向中小企业用户...\n\n'
                    '## 核心规格\n'
                    '| 参数 | 数值 |\n|------|------|\n'
                    '| 频段 | VHF 136-174 MHz |\n| 功率 | 5W |\n| 防护 | IP67 |\n\n'
                    '## 应用场景\n- 工地施工调度\n- 仓储物流\n\n'
                    '## See Also\n（暂无）\n'
                ),
                'summary': 'GP328P 是 VHF 频段 5W 对讲机，IP67 防护，面向中小企业客户',
                'source_raw_ids': [raw_id],
                'outbound_refs': [],
                'rationale': '新产品文档，首次入库，新建文章',
            }
        ],
        'index_update': (
            '# PMA Wiki 知识库索引\n\n'
            '## product\n\n'
            '- [GP328P 产品概述（测试）](product/test-gp328p-overview.md) '
            '— GP328P 是 VHF 频段 5W 对讲机...\n'
        ),
        'log_entry': '首次导入 gp328p 文档，新建 product/test-gp328p-overview',
    }
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(payload, ensure_ascii=False)
    mock_resp.usage = {'input_tokens': 1234, 'output_tokens': 567, 'model': 'fake'}
    return mock_resp


def test_ingest_creates_new_article(app_ctx, wiki_root, test_raw_file):
    from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle
    from app.services.wiki.compiler import ingest_raw_file
    from app.services.wiki.storage import read_index, read_article_content

    raw_id = test_raw_file

    fake_client = MagicMock()
    fake_client.complete.return_value = _fake_claude_response_create(raw_id)

    result = ingest_raw_file(raw_id, claude=fake_client)

    # 1. Claude 被调用了
    fake_client.complete.assert_called_once()
    call_kwargs = fake_client.complete.call_args.kwargs
    assert 'INGEST_SYSTEM' or call_kwargs.get('system')
    assert 'product' in call_kwargs['user']
    assert 'IP67' in call_kwargs['user']  # 原始文本应该被塞进 user prompt

    # 2. 返回值正确
    assert result['raw_id'] == raw_id
    assert len(result['operations']) == 1
    assert result['operations'][0]['action'] == 'create'
    assert result['index_updated'] is True
    assert result['usage']['input_tokens'] == 1234

    # 3. DB 记录创建
    art = KnowledgeWikiArticle.query.filter_by(
        topic='product', slug='test-gp328p-overview'
    ).first()
    assert art is not None
    assert art.title == 'GP328P 产品概述（测试）'
    assert art.source_raw_ids == [raw_id]
    assert art.compile_model  # 不为空
    assert art.content_length > 0

    # 4. 文件写到磁盘
    article_file = wiki_root / 'wiki' / 'product' / 'test-gp328p-overview.md'
    assert article_file.exists()
    content = read_article_content('wiki/product/test-gp328p-overview.md')
    assert '# GP328P 产品概述' in content
    assert 'IP67' in content

    # 5. index.md 被覆盖
    index = read_index()
    assert 'test-gp328p-overview' in index

    # 6. log.md 被追加
    log_file = wiki_root / 'wiki' / 'log.md'
    assert log_file.exists()
    log_content = log_file.read_text(encoding='utf-8')
    assert 'ingest' in log_content
    assert f'raw_id={raw_id}' in log_content

    # 7. KnowledgeRawFile 状态更新
    raw = KnowledgeRawFile.query.get(raw_id)
    assert raw.ingest_status == 'ingested'
    assert raw.ingested_at is not None
    assert raw.ingest_error is None


def test_ingest_update_existing_article(app_ctx, wiki_root, test_raw_file):
    from app import db
    from app.models.knowledge import KnowledgeWikiArticle
    from app.services.wiki.compiler import ingest_raw_file
    from app.services.wiki.storage import write_article

    raw_id = test_raw_file

    # 先手动建一篇已有文章
    file_path = write_article(
        'product', 'test-gp328p-overview', '# 旧版\n\n旧内容\n'
    )
    existing = KnowledgeWikiArticle(
        topic='product',
        slug='test-gp328p-overview',
        title='旧标题',
        file_path=file_path,
        summary='旧摘要',
        content_length=10,
        source_raw_ids=[999],  # 假设的历史 raw_id
        outbound_refs=[],
    )
    db.session.add(existing)
    db.session.commit()
    existing_id = existing.id

    # 让 fake Claude 返回 update
    payload = {
        'operations': [
            {
                'action': 'update',
                'topic': 'product',
                'slug': 'test-gp328p-overview',
                'title': 'GP328P 产品概述（更新版）',
                'content': '# GP328P 产品概述（更新版）\n\n新的完整内容...\n',
                'summary': '更新后的摘要',
                'source_raw_ids': [raw_id],
                'outbound_refs': ['competitor/hytera'],
            }
        ],
        'index_update': '# 索引\n（更新）\n',
        'log_entry': '更新 gp328p 文章',
    }
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(payload, ensure_ascii=False)
    mock_resp.usage = {'input_tokens': 500, 'output_tokens': 200, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = mock_resp

    ingest_raw_file(raw_id, claude=fake_client)

    # 验证更新
    updated = KnowledgeWikiArticle.query.get(existing_id)
    assert updated.title == 'GP328P 产品概述（更新版）'
    assert updated.summary == '更新后的摘要'
    assert set(updated.source_raw_ids) == {999, raw_id}  # 合并
    assert updated.outbound_refs == ['competitor/hytera']
    assert '新的完整内容' in (wiki_root / 'wiki' / 'product' / 'test-gp328p-overview.md').read_text(encoding='utf-8')


def test_ingest_parses_fenced_json(app_ctx, wiki_root, test_raw_file):
    """Claude 把 JSON 包在 ```json ... ``` 代码块时应该也能解析。"""
    from app.services.wiki.compiler import ingest_raw_file
    from app.models.knowledge import KnowledgeWikiArticle

    raw_id = test_raw_file
    payload = {
        'operations': [{
            'action': 'create',
            'topic': 'product',
            'slug': 'test-fenced-case',
            'title': 'Fenced JSON 测试',
            'content': '# Fenced\n',
            'summary': 'test',
            'source_raw_ids': [raw_id],
            'outbound_refs': [],
        }],
        'index_update': '# idx\n',
        'log_entry': 'fenced',
    }
    fenced_text = '```json\n' + json.dumps(payload, ensure_ascii=False) + '\n```'
    mock_resp = MagicMock()
    mock_resp.text = fenced_text
    mock_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}

    fake_client = MagicMock()
    fake_client.complete.return_value = mock_resp

    ingest_raw_file(raw_id, claude=fake_client)

    art = KnowledgeWikiArticle.query.filter_by(
        topic='product', slug='test-fenced-case'
    ).first()
    assert art is not None


def test_ingest_invalid_json_marks_error(app_ctx, wiki_root, test_raw_file):
    from app.models.knowledge import KnowledgeRawFile
    from app.services.wiki.compiler import ingest_raw_file, IngestError

    raw_id = test_raw_file

    fake_client = MagicMock()
    bad_resp = MagicMock()
    bad_resp.text = 'this is not json at all'
    bad_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}
    fake_client.complete.return_value = bad_resp

    with pytest.raises(IngestError, match='非法 JSON'):
        ingest_raw_file(raw_id, claude=fake_client)

    # raw 状态应为 error
    raw = KnowledgeRawFile.query.get(raw_id)
    assert raw.ingest_status == 'error'
    assert 'JSON' in (raw.ingest_error or '')


def test_ingest_noop_operation(app_ctx, wiki_root, test_raw_file):
    """noop action 不应写任何文件或 DB 记录，但依然更新 index.md + log.md + raw 状态。"""
    from app.services.wiki.compiler import ingest_raw_file
    from app.models.knowledge import KnowledgeWikiArticle, KnowledgeRawFile

    raw_id = test_raw_file
    payload = {
        'operations': [{
            'action': 'noop',
            'topic': 'product',
            'slug': 'test-skipped',
            'rationale': '资料与现有无新增价值',
        }],
        'index_update': '# idx\n',
        'log_entry': 'noop test',
    }
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(payload, ensure_ascii=False)
    mock_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}

    fake_client = MagicMock()
    fake_client.complete.return_value = mock_resp

    ingest_raw_file(raw_id, claude=fake_client)

    assert KnowledgeWikiArticle.query.filter_by(
        topic='product', slug='test-skipped'
    ).first() is None
    assert KnowledgeRawFile.query.get(raw_id).ingest_status == 'ingested'


# ══════════════════════════════════════════════════════════════════
# C1: Claude 返回恶意 slug 时 ingest 应拒绝
# ══════════════════════════════════════════════════════════════════

def test_ingest_rejects_malicious_slug_from_claude(app_ctx, wiki_root, test_raw_file):
    """对抗性 PDF 诱导 Claude 输出 `../evil` 这种 slug，应该被拦下。"""
    from app.services.wiki.compiler import ingest_raw_file, IngestError
    from app.models.knowledge import KnowledgeRawFile

    raw_id = test_raw_file
    payload = {
        'operations': [{
            'action': 'create',
            'topic': '../../../../etc',
            'slug': 'passwd',
            'title': 'pwn',
            'content': '# pwn\n',
            'summary': 'x',
            'source_raw_ids': [raw_id],
            'outbound_refs': [],
        }],
        'index_update': '# idx\n',
        'log_entry': 'malicious',
    }
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(payload, ensure_ascii=False)
    mock_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = mock_resp

    with pytest.raises(IngestError, match='非法'):
        ingest_raw_file(raw_id, claude=fake_client)

    # 恶意路径不能被创建
    assert not (wiki_root / 'etc').exists()
    # raw 状态应为 error
    raw = KnowledgeRawFile.query.get(raw_id)
    assert raw.ingest_status == 'error'


# ══════════════════════════════════════════════════════════════════
# C2: Claude 客户端构造失败时，raw 应落入 error 而非卡在 processing
# ══════════════════════════════════════════════════════════════════

def test_ingest_claude_client_construction_failure(app_ctx, wiki_root, test_raw_file, monkeypatch):
    from app.services.wiki import claude_client, compiler
    from app.models.knowledge import KnowledgeRawFile

    raw_id = test_raw_file

    # 把 WikiClaudeClient 替换成一个构造时爆炸的类
    class BoomClient:
        def __init__(self, *a, **kw):
            raise RuntimeError('ANTHROPIC_API_KEY 缺失（模拟）')

    monkeypatch.setattr(claude_client, 'WikiClaudeClient', BoomClient)

    # 不传 claude 参数，让 compiler 自己去构造
    with pytest.raises(Exception, match='ANTHROPIC_API_KEY'):
        compiler.ingest_raw_file(raw_id)

    raw = KnowledgeRawFile.query.get(raw_id)
    assert raw.ingest_status == 'error'
    assert 'ANTHROPIC_API_KEY' in (raw.ingest_error or '')


# ══════════════════════════════════════════════════════════════════
# C3: 中途失败时磁盘回滚（update 的旧文件应被恢复）
# ══════════════════════════════════════════════════════════════════

def test_ingest_rollback_restores_file_on_failure(app_ctx, wiki_root, test_raw_file):
    """模拟第二个 operation 失败，验证第一个 operation 对现有文件的改动被恢复。"""
    from app import db
    from app.services.wiki.compiler import ingest_raw_file, IngestError
    from app.services.wiki.storage import write_article
    from app.models.knowledge import KnowledgeWikiArticle

    raw_id = test_raw_file

    # 先建一篇已有文章
    original_content = '# GP328P 原版\n\n这是原来的内容。\n'
    fp = write_article('product', 'test-gp328p-orig', original_content)
    art = KnowledgeWikiArticle(
        topic='product', slug='test-gp328p-orig', title='GP328P 原版',
        file_path=fp, summary='原始', content_length=len(original_content),
        source_raw_ids=[], outbound_refs=[],
    )
    db.session.add(art)
    db.session.commit()

    # Claude 返回两个 operation：第一个是合法 update，第二个是非法 slug
    payload = {
        'operations': [
            {
                'action': 'update',
                'topic': 'product',
                'slug': 'test-gp328p-orig',
                'title': 'GP328P 更新版',
                'content': '# GP328P 更新版\n\n恶意修改的内容。\n',
                'summary': '被改掉了',
                'source_raw_ids': [raw_id],
                'outbound_refs': [],
            },
            {
                'action': 'create',
                'topic': '../../../evil',  # 非法，会触发预校验失败
                'slug': 'pwn',
                'title': 'pwn',
                'content': 'x',
            },
        ],
        'index_update': '# new idx\n',
        'log_entry': 'partial failure test',
    }
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(payload, ensure_ascii=False)
    mock_resp.usage = {'input_tokens': 1, 'output_tokens': 1, 'model': 'fake'}
    fake_client = MagicMock()
    fake_client.complete.return_value = mock_resp

    with pytest.raises(IngestError):
        ingest_raw_file(raw_id, claude=fake_client)

    # 预校验在任何磁盘写入之前就挂了，因此文件完全没动
    restored = (wiki_root / 'wiki' / 'product' / 'test-gp328p-orig.md').read_text(encoding='utf-8')
    assert restored == original_content
    assert '恶意修改' not in restored

    # DB 也应该没变
    art_db = KnowledgeWikiArticle.query.filter_by(
        topic='product', slug='test-gp328p-orig'
    ).first()
    assert art_db.title == 'GP328P 原版'
