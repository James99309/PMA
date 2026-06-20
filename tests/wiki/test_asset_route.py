# -*- coding: utf-8 -*-
"""Tests for the authenticated wiki asset route.

Route: GET /api/wiki/articles/<int:article_id>/asset/<path:rel>

Asserts:
- 200 + image/* mimetype for the article owner with the correct path
- 404 when article doesn't exist
- 404 (not 403) when the article exists but the user can't see it (existence leak)
- 400 for path traversal or paths not starting with _assets/<slug>/
- 404 when the file is missing on disk
"""
import os
import tempfile
import uuid
from pathlib import Path

import pytest

from app import create_app, db
from app.models.user import User
from app.models.knowledge import KnowledgeWikiArticle


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


def _create_article(owner: User, *, topic='product', slug=None, scope='personal') -> KnowledgeWikiArticle:
    slug = slug or f'art-{_unique_suffix()}'
    art = KnowledgeWikiArticle(
        topic=topic,
        slug=slug,
        title=f'Article {slug}',
        file_path=f'wiki/{topic}/{slug}.md',
        scope=scope,
        owner_id=owner.id,
        owner_department=owner.department,
        content_length=0,
    )
    db.session.add(art)
    db.session.commit()
    return art


def _login(client, user: User):
    """Use Flask-Login's session manipulation directly via test client.

    Also sets `role` in session because the app's before_request handler enforces
    consistency between session role and DB role (see app/__init__.py).
    """
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
        sess['role'] = user.role


def _write_image(wiki_root: Path, topic: str, slug: str, index: int = 1, ext: str = 'png',
                 data: bytes = b'\x89PNG\r\n\x1a\nFAKE') -> Path:
    rel = f'_assets/{slug}/img-{index}.{ext}'
    abs_path = wiki_root / 'wiki' / topic / rel
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(data)
    return abs_path


# ══════════════════════════════════════════════════════════════════
# Tests
# ══════════════════════════════════════════════════════════════════

def test_asset_route_serves_image_for_owner(client, app_ctx, wiki_root):
    """Owner of article can fetch the image."""
    owner = _create_user()
    art = _create_article(owner)
    _write_image(wiki_root, art.topic, art.slug, index=1, ext='png')
    _login(client, owner)

    resp = client.get(f'/api/wiki/articles/{art.id}/asset/_assets/{art.slug}/img-1.png')
    assert resp.status_code == 200, resp.data
    assert (resp.mimetype or '').startswith('image/'), f'mimetype={resp.mimetype}'
    assert resp.data.startswith(b'\x89PNG')


def test_asset_route_404_for_nonexistent_article(client, app_ctx, wiki_root):
    user = _create_user()
    _login(client, user)

    resp = client.get('/api/wiki/articles/99999999/asset/_assets/x/img-1.png')
    assert resp.status_code == 404


def test_asset_route_404_for_personal_article_other_user(client, app_ctx, wiki_root):
    """User B can't see User A's personal article — should return 404 (not 403)."""
    user_a = _create_user(department='dept-a')
    user_b = _create_user(department='dept-b')
    art = _create_article(user_a, scope='personal')
    _write_image(wiki_root, art.topic, art.slug)

    _login(client, user_b)
    resp = client.get(f'/api/wiki/articles/{art.id}/asset/_assets/{art.slug}/img-1.png')
    assert resp.status_code == 404, (
        f'Expected 404 (existence leak avoidance), got {resp.status_code}'
    )


def test_asset_route_400_for_path_traversal(client, app_ctx, wiki_root):
    owner = _create_user()
    art = _create_article(owner)
    _login(client, owner)

    # Contains ".." -> 400
    resp = client.get(
        f'/api/wiki/articles/{art.id}/asset/_assets/{art.slug}/../../../etc/passwd'
    )
    assert resp.status_code == 400, resp.data

    # Doesn't start with _assets/<slug>/ -> 400
    resp = client.get(f'/api/wiki/articles/{art.id}/asset/somewhere/else.png')
    assert resp.status_code == 400, resp.data

    # Different slug under _assets/ -> 400 (must be exactly this article's slug)
    resp = client.get(f'/api/wiki/articles/{art.id}/asset/_assets/other-slug/img-1.png')
    assert resp.status_code == 400, resp.data


def test_asset_route_404_for_missing_file(client, app_ctx, wiki_root):
    """Article exists, prefix correct, but file missing on disk -> 404."""
    owner = _create_user()
    art = _create_article(owner)
    _login(client, owner)

    # Note: no _write_image call
    resp = client.get(f'/api/wiki/articles/{art.id}/asset/_assets/{art.slug}/img-1.png')
    assert resp.status_code == 404
