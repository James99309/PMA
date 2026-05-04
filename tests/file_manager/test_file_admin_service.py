# -*- coding: utf-8 -*-
import pytest
from app import create_app, db
from app.models import User
from app.models.file_manager import FileLibrary, UserFileRef, UserFolder


@pytest.fixture
def app_ctx():
    app = create_app()
    with app.app_context():
        yield app


def _mk_user(role='user', dept=None):
    import uuid
    suffix = uuid.uuid4().hex[:8]
    u = User(username=f'testuser_{suffix}', password_hash='x', real_name=f'Test {suffix}', role=role, department=dept, is_active=True)
    db.session.add(u); db.session.commit()
    return u


def _mk_lib(filename='x.txt', size=100):
    import uuid
    sha = uuid.uuid4().hex
    lib = FileLibrary(sha256_hash=sha, original_filename=filename, file_size=size, storage_path=f'/fake/{sha}', mime_type='text/plain')
    db.session.add(lib); db.session.commit()
    return lib


def _mk_ref(user, lib, folder=None):
    ref = UserFileRef(user_id=user.id, file_library_id=lib.id, folder_id=folder.id if folder else None, display_name=lib.original_filename)
    db.session.add(ref); db.session.commit()
    return ref


def test_list_users_with_stats_returns_only_users_with_files(app_ctx):
    from app.services.file_admin_service import list_users_with_stats
    a = _mk_user(); b = _mk_user()
    lib = _mk_lib(size=1000)
    _mk_ref(a, lib)
    try:
        rows = list_users_with_stats()
        ids = [r['user_id'] for r in rows]
        assert a.id in ids
        a_row = next(r for r in rows if r['user_id'] == a.id)
        assert a_row['file_count'] == 1
        assert a_row['total_size'] == 1000
        assert 'real_name' in a_row
        assert 'department' in a_row
    finally:
        UserFileRef.query.filter(UserFileRef.user_id.in_([a.id, b.id])).delete(synchronize_session=False)
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter(User.id.in_([a.id, b.id])).delete()
        db.session.commit()


def test_list_user_files_flat_includes_folder_path(app_ctx):
    from app.services.file_admin_service import list_user_files_flat
    u = _mk_user()
    root_folder = UserFolder(user_id=u.id, name='项目', parent_id=None)
    db.session.add(root_folder); db.session.commit()
    sub = UserFolder(user_id=u.id, name='2026', parent_id=root_folder.id, depth=1)
    db.session.add(sub); db.session.commit()
    lib = _mk_lib('report.docx', 5000)
    ref = _mk_ref(u, lib, sub)
    try:
        rows = list_user_files_flat(u.id)
        assert len(rows) == 1
        r = rows[0]
        assert r['file_ref_id'] == ref.id
        assert r['original_filename'] == 'report.docx'
        assert r['folder_path'] == '/项目/2026'
        assert r['folder_id'] == sub.id
        assert 'is_admin_locked' in r
        assert 'is_in_wiki' in r
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        UserFolder.query.filter(UserFolder.id.in_([sub.id, root_folder.id])).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter_by(id=u.id).delete()
        db.session.commit()


def test_list_user_files_root_files_have_root_path(app_ctx):
    from app.services.file_admin_service import list_user_files_flat
    u = _mk_user()
    lib = _mk_lib()
    ref = _mk_ref(u, lib, folder=None)
    try:
        rows = list_user_files_flat(u.id)
        assert rows[0]['folder_path'] == '/'
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter_by(id=u.id).delete()
        db.session.commit()


def test_list_user_files_marks_wiki_status(app_ctx):
    from app.models.knowledge import KnowledgeRawFile
    from app.services.file_admin_service import list_user_files_flat
    u = _mk_user()
    lib = _mk_lib()
    ref = _mk_ref(u, lib)
    raw = KnowledgeRawFile(file_library_id=lib.id, topic='product',
                           raw_path=f'raw/product/{lib.original_filename}',
                           title='test', added_by=u.id, owner_id=u.id)
    db.session.add(raw); db.session.commit()
    try:
        rows = list_user_files_flat(u.id)
        assert rows[0]['is_in_wiki'] is True
    finally:
        KnowledgeRawFile.query.filter_by(id=raw.id).delete()
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter_by(id=u.id).delete()
        db.session.commit()


def test_list_user_files_excludes_deleted(app_ctx):
    from app.services.file_admin_service import list_user_files_flat
    u = _mk_user()
    lib = _mk_lib()
    ref = _mk_ref(u, lib)
    ref.is_deleted = True
    db.session.commit()
    try:
        rows = list_user_files_flat(u.id)
        assert rows == []
        rows2 = list_user_files_flat(u.id, include_deleted=True)
        assert len(rows2) == 1
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter_by(id=u.id).delete()
        db.session.commit()
