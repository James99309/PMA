# -*- coding: utf-8 -*-
"""Tests for the image replace API.

Route: POST /api/wiki/articles/<int:article_id>/image/<int:index>/replace

Asserts:
- 200 + file overwritten + .history backup + manifest updated + manually_edited=True
- 403 when user can't manage the article
- 404 when index not in manifest
- 400 for non-image mimetype
- 400 for empty upload
- 400 for oversize upload
"""
import io
import tempfile
import uuid
from pathlib import Path

import pytest

from app import create_app, db
from app.models.user import User
from app.models.knowledge import KnowledgeWikiArticle
from app.services.wiki import storage as wiki_storage


# ══════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════

@pytest.fixture
def wiki_root(monkeypatch):
    """临时 WIKI_ROOT，避免污染真实 storage/knowledge_base。"""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv('WIKI_ROOT', tmp)
        yield Path(tmp)


@pytest.fixture
def app_ctx(wiki_root):
    """Flask app context."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app


@pytest.fixture
def client(app_ctx):
    return app_ctx.test_client()


def _unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


def _create_user(role='user', department=None) -> User:
    suffix = _unique_suffix()
    user = User(
        username=f'testuser_{suffix}',
        password_hash='x',
        real_name=f'Test {suffix}',
        role=role,
        department=department,
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


def _create_article_with_image(
    owner: User,
    wiki_root: Path,
    *,
    topic='product',
    slug=None,
    scope='personal',
    image_bytes: bytes = b'OLD',
    index: int = 1,
    ext: str = 'png',
) -> KnowledgeWikiArticle:
    """创建一篇文章 + 写入对应的 _assets/<slug>/img-<index>.<ext> 文件 +
    image_manifest 中加入对应条目。
    """
    slug = slug or f'art-{_unique_suffix()}'
    rel = f'_assets/{slug}/img-{index}.{ext}'
    abs_path = wiki_root / 'wiki' / topic / rel
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(image_bytes)

    art = KnowledgeWikiArticle(
        topic=topic,
        slug=slug,
        title=f'Article {slug}',
        file_path=f'wiki/{topic}/{slug}.md',
        scope=scope,
        owner_id=owner.id,
        owner_department=owner.department,
        content_length=0,
        image_manifest=[
            {
                'index': index,
                'path': rel,
                'media_type': f'image/{ext if ext != "jpg" else "jpeg"}',
                'sha256': wiki_storage.sha256_bytes(image_bytes),
                'size_bytes': len(image_bytes),
            }
        ],
        manually_edited=False,
    )
    db.session.add(art)
    db.session.commit()
    return art


def _login(client, user: User):
    """复用 test_asset_route.py 的 session 登录方式。"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
        sess['role'] = user.role


# ══════════════════════════════════════════════════════════════════
# Tests
# ══════════════════════════════════════════════════════════════════

def test_replace_image_overwrites_file_and_sets_manually_edited(client, app_ctx, wiki_root):
    """正常路径：上传新图 → 文件被覆盖、旧文件备份到 .history/、
    manifest 与 manually_edited 字段同步更新。"""
    owner = _create_user()
    art = _create_article_with_image(owner, wiki_root, image_bytes=b'OLD', index=1, ext='png')
    _login(client, owner)

    new_bytes = b'NEWBYTES'
    resp = client.post(
        f'/api/wiki/articles/{art.id}/image/1/replace',
        data={'image': (io.BytesIO(new_bytes), 'new.png', 'image/png')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 200, resp.data
    payload = resp.get_json()
    assert payload['success'] is True
    assert payload['manually_edited'] is True
    assert payload['image']['manually_replaced'] is True
    assert payload['image']['size_bytes'] == len(new_bytes)
    assert payload['image']['sha256'] == wiki_storage.sha256_bytes(new_bytes)
    assert 'replaced_at' in payload['image']

    # 文件已被覆盖
    abs_path = wiki_root / 'wiki' / art.topic / f'_assets/{art.slug}/img-1.png'
    assert abs_path.read_bytes() == new_bytes

    # .history/ 中有一份旧文件备份
    history_dir = abs_path.parent / '.history'
    assert history_dir.is_dir()
    backups = list(history_dir.iterdir())
    assert len(backups) == 1
    assert backups[0].read_bytes() == b'OLD'

    # 数据库已更新（清掉缓存重新查询，避免 session 拿到旧对象）
    art_id = art.id
    db.session.expire_all()
    fresh = db.session.get(KnowledgeWikiArticle, art_id)
    assert fresh.manually_edited is True
    assert fresh.image_manifest[0]['manually_replaced'] is True
    assert fresh.image_manifest[0]['sha256'] == wiki_storage.sha256_bytes(new_bytes)
    assert fresh.image_manifest[0]['size_bytes'] == len(new_bytes)


def test_replace_image_403_for_non_owner_personal_article(client, app_ctx, wiki_root):
    """User B 没有管理 User A 的 personal 文章的权限 → 403。"""
    user_a = _create_user(department='dept-a')
    user_b = _create_user(department='dept-b')
    art = _create_article_with_image(user_a, wiki_root, scope='personal')

    _login(client, user_b)
    resp = client.post(
        f'/api/wiki/articles/{art.id}/image/1/replace',
        data={'image': (io.BytesIO(b'NEW'), 'new.png', 'image/png')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 403, resp.data


def test_replace_image_404_for_unknown_index(client, app_ctx, wiki_root):
    """manifest 只有 index=1，请求 index=99 → 404。"""
    owner = _create_user()
    art = _create_article_with_image(owner, wiki_root, index=1)
    _login(client, owner)

    resp = client.post(
        f'/api/wiki/articles/{art.id}/image/99/replace',
        data={'image': (io.BytesIO(b'NEW'), 'new.png', 'image/png')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 404, resp.data


def test_replace_image_400_for_non_image_mimetype(client, app_ctx, wiki_root):
    """非图片 mimetype（application/pdf）→ 400。"""
    owner = _create_user()
    art = _create_article_with_image(owner, wiki_root)
    _login(client, owner)

    resp = client.post(
        f'/api/wiki/articles/{art.id}/image/1/replace',
        data={'image': (io.BytesIO(b'%PDF-1.4'), 'foo.pdf', 'application/pdf')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400, resp.data


def test_replace_image_400_for_empty_file(client, app_ctx, wiki_root):
    """0 字节上传 → 400。"""
    owner = _create_user()
    art = _create_article_with_image(owner, wiki_root)
    _login(client, owner)

    resp = client.post(
        f'/api/wiki/articles/{art.id}/image/1/replace',
        data={'image': (io.BytesIO(b''), 'empty.png', 'image/png')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400, resp.data


def test_replace_image_400_for_oversized_file(client, app_ctx, wiki_root, monkeypatch):
    """超过大小限制 → 400。

    通过 monkeypatch 修改 MAX_BYTES？视图里是函数内局部变量，不便注入。
    改成实际发送 11MB 数据：开销可接受（一次性 IO）。
    """
    owner = _create_user()
    art = _create_article_with_image(owner, wiki_root)
    _login(client, owner)

    big = b'\x00' * (11 * 1024 * 1024)  # 11 MB > 10 MB
    resp = client.post(
        f'/api/wiki/articles/{art.id}/image/1/replace',
        data={'image': (io.BytesIO(big), 'big.png', 'image/png')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400, resp.data
    assert b'\xe8\xbf\x87\xe5\xa4\xa7' in resp.data or b'10MB' in resp.data or b'>10' in resp.data
