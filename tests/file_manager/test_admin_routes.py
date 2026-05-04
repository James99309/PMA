import io, json, pytest
from app import create_app, db
from app.models import User
from app.models.file_manager import FileLibrary, UserFileRef


@pytest.fixture
def app_ctx():
    app = create_app()
    with app.app_context():
        yield app


@pytest.fixture
def client(app_ctx):
    return app_ctx.test_client()


def _mk(role='user'):
    import uuid
    s = uuid.uuid4().hex[:8]
    u = User(username=f'testuser_{s}', password_hash='x', real_name=s, role=role, is_active=True)
    db.session.add(u); db.session.commit()
    return u


def _login(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
        sess['role'] = user.role


def _mk_lib_ref(user):
    import uuid
    sha = uuid.uuid4().hex
    lib = FileLibrary(sha256_hash=sha, original_filename='x.txt', file_size=100,
                     storage_path=f'/fake/{sha}', mime_type='text/plain', ref_count=1)
    db.session.add(lib); db.session.commit()
    ref = UserFileRef(user_id=user.id, file_library_id=lib.id, display_name='x.txt')
    db.session.add(ref); db.session.commit()
    return lib, ref


def test_users_endpoint_requires_admin(client):
    u = _mk(role='user'); _login(client, u)
    rv = client.get('/api/file-manager/admin/users')
    assert rv.status_code == 403
    User.query.filter_by(id=u.id).delete(); db.session.commit()


def test_users_endpoint_returns_list_for_admin(client):
    admin = _mk(role='admin'); user = _mk()
    lib, ref = _mk_lib_ref(user)
    _login(client, admin)
    try:
        rv = client.get('/api/file-manager/admin/users')
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['success']
        ids = [u['user_id'] for u in data['data']]
        assert user.id in ids
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter(User.id.in_([admin.id, user.id])).delete()
        db.session.commit()


def test_files_endpoint_returns_user_files(client):
    admin = _mk(role='admin'); user = _mk()
    lib, ref = _mk_lib_ref(user)
    _login(client, admin)
    try:
        rv = client.get(f'/api/file-manager/admin/files?user_id={user.id}')
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['success']
        assert len(data['data']) == 1
        assert data['data'][0]['file_ref_id'] == ref.id
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter(User.id.in_([admin.id, user.id])).delete()
        db.session.commit()


def test_lock_endpoint_toggles(client):
    admin = _mk(role='admin'); user = _mk()
    lib, ref = _mk_lib_ref(user)
    _login(client, admin)
    try:
        rv = client.post(f'/api/file-manager/admin/files/{ref.id}/lock', json={'locked': True})
        assert rv.status_code == 200
        db.session.refresh(ref)
        assert ref.is_admin_locked is True
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter(User.id.in_([admin.id, user.id])).delete()
        db.session.commit()


def test_transfer_endpoint(client):
    admin = _mk(role='admin'); a = _mk(); b = _mk()
    lib, ref = _mk_lib_ref(a)
    _login(client, admin)
    try:
        rv = client.patch(f'/api/file-manager/admin/files/{ref.id}/transfer', json={'to_user_id': b.id})
        assert rv.status_code == 200
        db.session.refresh(ref)
        assert ref.user_id == b.id
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter(User.id.in_([admin.id, a.id, b.id])).delete()
        db.session.commit()
