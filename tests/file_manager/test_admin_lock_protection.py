# -*- coding: utf-8 -*-
import pytest
from app import create_app, db
from app.models import User
from app.models.file_manager import FileLibrary, UserFileRef


@pytest.fixture
def app_ctx():
    app = create_app()
    with app.app_context():
        yield app


def _mk(role='user'):
    import uuid
    s = uuid.uuid4().hex[:8]
    u = User(username=f'testuser_{s}', password_hash='x', real_name=s, role=role, is_active=True)
    db.session.add(u); db.session.commit()
    return u


def _mk_lib_ref(user, locked=False):
    """创建 lib + ref（已在回收站，可被永久清理）。"""
    import uuid
    sha = uuid.uuid4().hex
    lib = FileLibrary(sha256_hash=sha, original_filename='x.txt', file_size=100,
                     storage_path=f'/fake/{sha}', mime_type='text/plain', ref_count=1)
    db.session.add(lib); db.session.commit()
    ref = UserFileRef(user_id=user.id, file_library_id=lib.id, display_name='x.txt',
                      is_deleted=True, is_admin_locked=locked)
    db.session.add(ref); db.session.commit()
    return lib, ref


def test_permanent_delete_skips_locked_file(app_ctx):
    """已锁定的文件 permanent_delete 时被拒绝。"""
    from app.services.file_manager_service import FileManagerService
    u = _mk()
    lib, ref = _mk_lib_ref(u, locked=True)
    ref_id = ref.id
    try:
        ok, msg = FileManagerService.permanent_delete(u, ref_id)
        assert not ok
        assert '锁定' in msg
        # ref 仍然存在
        assert UserFileRef.query.filter_by(id=ref_id).first() is not None
        # lib 仍然存在
        assert FileLibrary.query.filter_by(id=lib.id).first() is not None
    finally:
        UserFileRef.query.filter_by(id=ref_id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter_by(id=u.id).delete()
        db.session.commit()


def test_empty_trash_preserves_locked_files(app_ctx):
    """清空回收站时已锁定文件保留，未锁定的仍被清理。"""
    from app.services.file_manager_service import FileManagerService
    u = _mk()
    lib1, ref1 = _mk_lib_ref(u, locked=False)  # 普通
    lib2, ref2 = _mk_lib_ref(u, locked=True)   # 锁定
    try:
        FileManagerService.empty_trash(u)
        # ref2 应当仍然存在
        ref2_after = UserFileRef.query.filter_by(id=ref2.id).first()
        assert ref2_after is not None, '锁定文件不应被 empty_trash 删除'
        assert ref2_after.is_admin_locked is True
        # ref1（普通）应被删除
        assert UserFileRef.query.filter_by(id=ref1.id).first() is None
    finally:
        # 清理可能的残留
        UserFileRef.query.filter(UserFileRef.id.in_([ref1.id, ref2.id])).delete(synchronize_session=False)
        FileLibrary.query.filter(FileLibrary.id.in_([lib1.id, lib2.id])).delete(synchronize_session=False)
        User.query.filter_by(id=u.id).delete()
        db.session.commit()
