# Admin File Manager Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 给 PMA 管理员/CEO 加一个独立 UI 页面，按用户分组平铺显示所有人员的文件，每行可点击下载、锁定（避免被永久清理）、转移给其他人、转知识库。

**Architecture:** 新增 admin 专属服务层（避免污染现有 `file_manager_service.py` 的"按 user_id 隔离"逻辑） + 5 个 admin API 端点 + 独立模板。`UserFileRef` 增加 3 字段（`is_admin_locked / admin_locked_at / admin_locked_by`），用于"锁定"语义——锁定的文件在所有自动清理路径（永久删除、压缩归档）里被保护。**重要：复用 `FileLibrary.is_archived` 字段会与现有"自动压缩归档"机制冲突，必须用独立字段。**

**Tech Stack:** Flask + SQLAlchemy 2.x + Flask-Migrate (Alembic) + Tailwind + Alpine.js + Material Symbols icons + 复用现有 `tw_file_preview.html` / `confirmModal` 组件

**Branch strategy:** 在新建 feature 分支上工作（如 `feature/admin-file-manager`），避免污染 main。最后合并 + push 走标准 PR 流程。

---

## Phase 1 — DB 字段

### Task 1: UserFileRef 加 admin_locked 字段

**Files:**
- Modify: `app/models/file_manager.py:104` 附近 (UserFileRef class)
- Create: `migrations/versions/xxxx_add_admin_locked_to_user_file_refs.py`

**Background — why not reuse FileLibrary.is_archived:**
现有 `FileLibrary.is_archived/archived_at/archive_reason` 表示"物理文件已被压缩节省空间"——是**自动空间管理**的产物（`archive_reason='deleted'|'inactive'`）。我们要的语义不同：admin 手动锁定，**禁止文件被永久清理**。两个语义同表会混乱。新字段放 `UserFileRef`（用户引用层），不放 `FileLibrary`（共享存储层）。

**Step 1: 修改模型**

打开 `app/models/file_manager.py`，找到 `UserFileRef` 类（约 line 104+）。在合适位置（`is_deleted` 字段附近）添加：

```python
# 管理员锁定标记：被锁定的 ref 在永久清理 / 自动压缩路径中被保护
is_admin_locked = Column(Boolean, nullable=False, default=False, server_default='false', index=True)
admin_locked_at = Column(DateTime, nullable=True)
admin_locked_by = Column(Integer, ForeignKey('users.id'), nullable=True)
```

`to_dict()` 中追加：
```python
'is_admin_locked': bool(self.is_admin_locked),
'admin_locked_at': self.admin_locked_at.isoformat() if self.admin_locked_at else None,
'admin_locked_by': self.admin_locked_by,
```

**Step 2: 生成 migration**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  flask db migrate -m "add admin_locked fields to user_file_refs"
```

**Step 3: 审查 migration 文件**

打开新生成的 `migrations/versions/xxxx_add_admin_locked_to_user_file_refs.py`。预期内容只有 3 个 add_column。如果 autogenerate 引入其它无关 schema drift（PMA 历史 drift 已知问题），**手动删掉无关变更**，只保留：

```python
def upgrade():
    op.add_column('user_file_refs', sa.Column('is_admin_locked', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('user_file_refs', sa.Column('admin_locked_at', sa.DateTime(), nullable=True))
    op.add_column('user_file_refs', sa.Column('admin_locked_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.create_index('ix_user_file_refs_is_admin_locked', 'user_file_refs', ['is_admin_locked'])

def downgrade():
    op.drop_index('ix_user_file_refs_is_admin_locked', table_name='user_file_refs')
    op.drop_column('user_file_refs', 'admin_locked_by')
    op.drop_column('user_file_refs', 'admin_locked_at')
    op.drop_column('user_file_refs', 'is_admin_locked')
```

注意 `server_default=sa.text('false')`（不是 Python 字符串 `'false'`）。

**Step 4: 应用到本地**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

**Step 5: 验证**

```bash
psql $DATABASE_URL -c "\d user_file_refs" | grep -E "is_admin_locked|admin_locked"
```

预期：3 行新列，`is_admin_locked` 默认 `false` not null。

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 -c "
from app import create_app
from app.models.file_manager import UserFileRef
app = create_app()
with app.app_context():
    ref = UserFileRef.query.first()
    if ref:
        print('is_admin_locked:', ref.is_admin_locked)
        print('to_dict has fields:', all(k in ref.to_dict() for k in ('is_admin_locked','admin_locked_at','admin_locked_by')))
"
```

**Step 6: Commit**

```bash
git checkout -b feature/admin-file-manager
git add app/models/file_manager.py migrations/versions/
git commit -m "feat(file-manager): add admin_locked fields to user_file_refs"
```

---

## Phase 2 — Service 层 (admin 专属)

### Task 2: 新 admin 服务模块 — 用户列表 + 文件平铺

**Files:**
- Create: `app/services/file_admin_service.py`
- Test: `tests/file_manager/test_file_admin_service.py`

**理由**：不在现有 `file_manager_service.py` 加 admin 分支——避免每个方法都要 `if is_admin: bypass user_id filter`。新模块只服务 admin 路径，逻辑清晰。

**Step 1: 写失败测试**

`tests/file_manager/test_file_admin_service.py` (创建文件)：

```python
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
    ref = UserFileRef(user_id=user.id, file_library_id=lib.id, folder_id=folder.id if folder else None, custom_filename=lib.original_filename)
    db.session.add(ref); db.session.commit()
    return ref


def test_list_users_with_stats_returns_only_users_with_files(app_ctx):
    from app.services.file_admin_service import list_users_with_stats
    a = _mk_user(); b = _mk_user()  # b has no files
    lib = _mk_lib(size=1000)
    _mk_ref(a, lib)
    try:
        rows = list_users_with_stats()
        ids = [r['user_id'] for r in rows]
        assert a.id in ids, '用户 A 有文件应该出现'
        # B 没文件不出现（产品决策：仅显示有文件的用户）
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
        assert r['folder_path'] == '/项目/2026'  # 根目录开头的相对路径
        assert r['folder_id'] == sub.id
        assert 'is_admin_locked' in r
        assert 'is_in_wiki' in r  # 是否已转知识库
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
        assert rows == [], '默认不返回回收站文件'
        # 但带 include_deleted=True 时返回
        rows2 = list_user_files_flat(u.id, include_deleted=True)
        assert len(rows2) == 1
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter_by(id=u.id).delete()
        db.session.commit()
```

**Step 2: 运行测试 → 失败**

```bash
cd /Users/nijie/Documents/PMA && \
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  python3 -m pytest tests/file_manager/test_file_admin_service.py -v
```

预期: 全部 FAIL (`ModuleNotFoundError: file_admin_service`).

**Step 3: 实现服务**

`app/services/file_admin_service.py` (创建新文件)：

```python
# -*- coding: utf-8 -*-
"""管理员视角的文件管理服务。

不复用 file_manager_service 的"按 user_id 隔离"逻辑——这里默认看所有用户。
仅 admin/ceo 调用，权限检查在路由层。
"""
from sqlalchemy import func
from app import db
from app.models import User
from app.models.file_manager import FileLibrary, UserFileRef, UserFolder
from app.models.knowledge import KnowledgeRawFile


def list_users_with_stats():
    """返回所有有文件的用户列表 + 统计。
    每条 dict: {user_id, username, real_name, department, file_count, total_size, has_locked, has_in_wiki}
    """
    # 子查询：每个用户的活跃文件统计
    stats = (
        db.session.query(
            UserFileRef.user_id.label('user_id'),
            func.count(UserFileRef.id).label('file_count'),
            func.coalesce(func.sum(FileLibrary.file_size), 0).label('total_size'),
            func.bool_or(UserFileRef.is_admin_locked).label('has_locked'),
        )
        .join(FileLibrary, FileLibrary.id == UserFileRef.file_library_id)
        .filter(UserFileRef.is_deleted == False)  # noqa: E712
        .group_by(UserFileRef.user_id)
        .subquery()
    )

    rows = (
        db.session.query(
            User.id, User.username, User.real_name, User.department,
            stats.c.file_count, stats.c.total_size, stats.c.has_locked,
        )
        .join(stats, stats.c.user_id == User.id)
        .order_by(stats.c.file_count.desc())
        .all()
    )

    return [
        {
            'user_id': r.id,
            'username': r.username,
            'real_name': r.real_name,
            'department': r.department,
            'file_count': int(r.file_count or 0),
            'total_size': int(r.total_size or 0),
            'has_locked': bool(r.has_locked),
        }
        for r in rows
    ]


def list_user_files_flat(user_id: int, *, include_deleted: bool = False,
                        search: str = '', file_type: str = '',
                        sort: str = 'recent') -> list[dict]:
    """返回某用户所有文件（平铺），含文件夹路径 + wiki 状态。

    Args:
        user_id: 目标用户
        include_deleted: 是否包含回收站文件
        search: 文件名模糊搜索
        file_type: 'office' | 'pdf' | 'image' | 'video' | 'other' | ''
        sort: 'recent' | 'name' | 'size'
    """
    q = (
        db.session.query(UserFileRef, FileLibrary, UserFolder)
        .join(FileLibrary, FileLibrary.id == UserFileRef.file_library_id)
        .outerjoin(UserFolder, UserFolder.id == UserFileRef.folder_id)
        .filter(UserFileRef.user_id == user_id)
    )
    if not include_deleted:
        q = q.filter(UserFileRef.is_deleted == False)  # noqa: E712

    if search:
        q = q.filter(FileLibrary.original_filename.ilike(f'%{search}%'))

    if file_type:
        # 简化：用 mime_type 前缀匹配
        type_map = {
            'pdf': ['application/pdf'],
            'office': ['application/vnd.openxmlformats',
                       'application/vnd.ms-', 'application/msword'],
            'image': ['image/'],
            'video': ['video/'],
        }
        prefixes = type_map.get(file_type, [])
        if prefixes:
            from sqlalchemy import or_
            q = q.filter(or_(*(FileLibrary.mime_type.like(f'{p}%') for p in prefixes)))

    if sort == 'name':
        q = q.order_by(FileLibrary.original_filename)
    elif sort == 'size':
        q = q.order_by(FileLibrary.file_size.desc())
    else:
        q = q.order_by(UserFileRef.created_at.desc())

    triples = q.all()
    if not triples:
        return []

    # 一次性查 wiki 状态（按 file_library_id 去重）
    lib_ids = {t[1].id for t in triples}
    wiki_lib_ids = set(
        r[0] for r in db.session.query(KnowledgeRawFile.file_library_id)
                                .filter(KnowledgeRawFile.file_library_id.in_(lib_ids)).all()
    )

    rows = []
    for ref, lib, folder in triples:
        rows.append({
            'file_ref_id': ref.id,
            'file_library_id': lib.id,
            'original_filename': lib.original_filename,
            'custom_filename': ref.custom_filename,
            'file_size': lib.file_size,
            'mime_type': lib.mime_type,
            'created_at': ref.created_at.isoformat() if ref.created_at else None,
            'folder_id': folder.id if folder else None,
            'folder_path': _folder_path(folder) if folder else '/',
            'is_deleted': bool(ref.is_deleted),
            'is_admin_locked': bool(ref.is_admin_locked),
            'admin_locked_at': ref.admin_locked_at.isoformat() if ref.admin_locked_at else None,
            'is_in_wiki': lib.id in wiki_lib_ids,
        })
    return rows


def _folder_path(folder: UserFolder) -> str:
    """构造文件夹绝对路径，'/项目/2026' 这种。"""
    parts = []
    cur = folder
    while cur:
        parts.append(cur.name)
        cur = cur.parent if cur.parent_id else None
    return '/' + '/'.join(reversed(parts))
```

**Step 4: 运行测试 → 通过**

```bash
cd /Users/nijie/Documents/PMA && \
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  python3 -m pytest tests/file_manager/test_file_admin_service.py -v
```

预期: 5 passed.

**Step 5: 清理测试残留 + Commit**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    User.query.filter(User.username.like('testuser_%')).delete(synchronize_session=False)
    db.session.commit()
"
git add app/services/file_admin_service.py tests/file_manager/test_file_admin_service.py
git commit -m "feat(file-manager): admin service - list users + flat file listing"
```

---

### Task 3: lock/unlock + transfer + wiki-ingest 服务方法

**Files:**
- Modify: `app/services/file_admin_service.py`
- Modify: `tests/file_manager/test_file_admin_service.py`

**Step 1: 写失败测试**

追加到 `tests/file_manager/test_file_admin_service.py`：

```python
def test_set_admin_lock_records_actor_and_time(app_ctx):
    from app.services.file_admin_service import set_admin_lock
    u = _mk_user(); admin = _mk_user(role='admin')
    lib = _mk_lib(); ref = _mk_ref(u, lib)
    try:
        ok, msg = set_admin_lock(ref.id, locked=True, by_user=admin)
        assert ok, msg
        db.session.refresh(ref)
        assert ref.is_admin_locked is True
        assert ref.admin_locked_by == admin.id
        assert ref.admin_locked_at is not None
        # 取消锁定
        ok2, msg2 = set_admin_lock(ref.id, locked=False, by_user=admin)
        assert ok2, msg2
        db.session.refresh(ref)
        assert ref.is_admin_locked is False
        assert ref.admin_locked_at is None
        assert ref.admin_locked_by is None
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter(User.id.in_([u.id, admin.id])).delete()
        db.session.commit()


def test_transfer_changes_owner(app_ctx):
    from app.services.file_admin_service import transfer_file
    a = _mk_user(); b = _mk_user(); admin = _mk_user(role='admin')
    lib = _mk_lib(); ref = _mk_ref(a, lib)
    try:
        ok, msg = transfer_file(ref.id, to_user_id=b.id, to_folder_id=None, by_user=admin)
        assert ok, msg
        db.session.refresh(ref)
        assert ref.user_id == b.id
        assert ref.folder_id is None  # 目标用户根目录
    finally:
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter(User.id.in_([a.id, b.id, admin.id])).delete()
        db.session.commit()


def test_transfer_rejects_invalid_target_folder(app_ctx):
    """目标文件夹必须属于目标用户。"""
    from app.services.file_admin_service import transfer_file
    a = _mk_user(); b = _mk_user(); admin = _mk_user(role='admin')
    lib = _mk_lib(); ref = _mk_ref(a, lib)
    a_folder = UserFolder(user_id=a.id, name='A的文件夹', parent_id=None)
    db.session.add(a_folder); db.session.commit()
    try:
        ok, msg = transfer_file(ref.id, to_user_id=b.id, to_folder_id=a_folder.id, by_user=admin)
        assert not ok
        assert '不属于目标用户' in msg
    finally:
        UserFolder.query.filter_by(id=a_folder.id).delete()
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter(User.id.in_([a.id, b.id, admin.id])).delete()
        db.session.commit()


def test_ingest_to_wiki_creates_raw_file(app_ctx):
    from app.services.file_admin_service import ingest_to_wiki
    from app.models.knowledge import KnowledgeRawFile
    u = _mk_user(); admin = _mk_user(role='admin')
    lib = _mk_lib('test.docx')
    ref = _mk_ref(u, lib)
    try:
        ok, raw_id_or_msg = ingest_to_wiki(ref.id, topic='product', scope='personal', by_user=admin)
        assert ok, raw_id_or_msg
        raw = KnowledgeRawFile.query.get(raw_id_or_msg)
        assert raw is not None
        assert raw.file_library_id == lib.id
        assert raw.added_by == admin.id
        assert raw.owner_id == admin.id
        # 不立即触发 ingest（只创建 raw_file 记录）
        assert raw.ingest_status == 'pending'
    finally:
        from app.models.knowledge import KnowledgeRawFile
        KnowledgeRawFile.query.filter_by(file_library_id=lib.id).delete()
        UserFileRef.query.filter_by(id=ref.id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter(User.id.in_([u.id, admin.id])).delete()
        db.session.commit()
```

**Step 2: 运行 → 失败**

**Step 3: 实现**

追加到 `app/services/file_admin_service.py`：

```python
from datetime import datetime
from app.utils.timezone_helper import get_local_time


def set_admin_lock(file_ref_id: int, *, locked: bool, by_user) -> tuple[bool, str]:
    """锁定/取消锁定 UserFileRef。锁定后被永久清理路径保护。"""
    ref = UserFileRef.query.get(file_ref_id)
    if ref is None:
        return False, '文件不存在'
    if locked:
        ref.is_admin_locked = True
        ref.admin_locked_at = get_local_time()
        ref.admin_locked_by = by_user.id
    else:
        ref.is_admin_locked = False
        ref.admin_locked_at = None
        ref.admin_locked_by = None
    db.session.commit()
    return True, '已锁定' if locked else '已取消锁定'


def transfer_file(file_ref_id: int, *, to_user_id: int, to_folder_id: int | None,
                  by_user) -> tuple[bool, str]:
    """转移文件到其他用户的文件夹（或根目录）。"""
    ref = UserFileRef.query.get(file_ref_id)
    if ref is None:
        return False, '文件不存在'

    target_user = User.query.get(to_user_id)
    if target_user is None or not target_user.is_active:
        return False, '目标用户不存在或已停用'

    if to_folder_id is not None:
        folder = UserFolder.query.get(to_folder_id)
        if folder is None or folder.is_deleted:
            return False, '目标文件夹不存在'
        if folder.user_id != to_user_id:
            return False, '目标文件夹不属于目标用户'

    ref.user_id = to_user_id
    ref.folder_id = to_folder_id
    db.session.commit()
    import logging
    logging.getLogger(__name__).info(
        f'[FileAdmin] user={by_user.id} 转移 file_ref={ref.id} → user={to_user_id} folder={to_folder_id}'
    )
    return True, '已转移'


def ingest_to_wiki(file_ref_id: int, *, topic: str, scope: str, by_user) -> tuple[bool, object]:
    """把 file_ref 对应的 file_library 文件登记为 wiki raw file（不立即编译）。
    返回 (True, raw_id) 或 (False, error_msg)。
    """
    from app.services.file_manager_service import FileManagerService
    from app.models.knowledge import KnowledgeRawFile
    from app.services.wiki import storage as wiki_storage

    ref = UserFileRef.query.get(file_ref_id)
    if ref is None:
        return False, '文件不存在'

    lib = ref.file_library
    if lib is None:
        return False, '文件库记录缺失'

    # 校验 topic
    try:
        wiki_storage.validate_topic(topic)
    except wiki_storage.WikiPathError as e:
        return False, str(e)

    if scope not in ('personal', 'department', 'company', 'system'):
        return False, '非法 scope'

    # 读字节 + 落到 raw 目录
    content = FileManagerService.read_file_content_auto_decompress(lib)
    if content is None:
        return False, '无法读取文件内容'

    safe_name = wiki_storage.dated_filename(lib.original_filename)
    raw_path = wiki_storage.save_raw_file(topic, safe_name, content)

    # 体量校验（拒绝过大/不合适文件）
    abs_path = wiki_storage.get_wiki_root() / raw_path
    reason = wiki_storage.validate_raw_file_for_wiki(abs_path)
    if reason:
        try:
            abs_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False, reason

    raw = KnowledgeRawFile(
        file_library_id=lib.id, topic=topic, raw_path=raw_path,
        title=lib.original_filename, added_by=by_user.id,
        scope=scope, owner_id=by_user.id,
        owner_department=getattr(by_user, 'department', None),
    )
    db.session.add(raw); db.session.commit()
    return True, raw.id
```

注意：`get_wiki_root` 需要从 `app.services.wiki.paths` 导入（在 wiki_storage 内部已被使用，所以直接 `wiki_storage.get_wiki_root` 不行——是 paths 模块的）。需要：

```python
from app.services.wiki.paths import get_wiki_root
# 或者：from app.services.wiki import storage as wiki_storage; wiki_storage 没有 get_wiki_root
# → 改用 paths 模块
```

修复方法：在 `ingest_to_wiki` 顶部加 `from app.services.wiki.paths import get_wiki_root`。

**Step 4: 运行测试 → 通过**

预期：4 个新测试全过 + 之前 5 个仍过。

**Step 5: 清理 + Commit**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    User.query.filter(User.username.like('testuser_%')).delete(synchronize_session=False)
    db.session.commit()
"
git add app/services/file_admin_service.py tests/file_manager/test_file_admin_service.py
git commit -m "feat(file-manager): admin service - lock/transfer/wiki-ingest"
```

---

## Phase 3 — 清理路径保护

### Task 4: 永久清理时跳过 admin_locked

**Files:**
- Modify: `app/services/file_manager_service.py:531` (permanent_delete)
- Modify: `app/services/file_manager_service.py:558` (empty_trash)
- Modify: 自动归档逻辑（如果有，约 line 700+）
- Test: `tests/file_manager/test_admin_lock_protection.py` (创建新文件)

**Step 1: 写失败测试**

```python
# tests/file_manager/test_admin_lock_protection.py
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


def _mk_lib_ref(user):
    import uuid
    sha = uuid.uuid4().hex
    lib = FileLibrary(sha256_hash=sha, original_filename='x.txt', file_size=100,
                     storage_path=f'/fake/{sha}', mime_type='text/plain')
    db.session.add(lib); db.session.commit()
    ref = UserFileRef(user_id=user.id, file_library_id=lib.id, custom_filename='x.txt',
                      is_deleted=True)  # 已在回收站
    db.session.add(ref); db.session.commit()
    return lib, ref


def test_permanent_delete_skips_locked_file(app_ctx):
    """已锁定的文件永久删除时应被保护，不真删。"""
    from app.services.file_manager_service import FileManagerService
    u = _mk()
    lib, ref = _mk_lib_ref(u)
    ref.is_admin_locked = True
    db.session.commit()
    ref_id = ref.id
    try:
        ok, msg = FileManagerService.permanent_delete(u, ref_id)
        # 当前实现是"压缩归档而非真删"，加保护后应返回提示性 False/带保护标记的 True
        # 这里期望：返回 False，msg 含"锁定"
        assert (not ok) or '锁定' in msg or 'locked' in msg.lower()
        # 文件库仍然存在
        assert FileLibrary.query.filter_by(id=lib.id).first() is not None
    finally:
        UserFileRef.query.filter_by(id=ref_id).delete()
        FileLibrary.query.filter_by(id=lib.id).delete()
        User.query.filter_by(id=u.id).delete()
        db.session.commit()


def test_empty_trash_preserves_locked_files(app_ctx):
    """清空回收站时，已锁定的文件应保留（lib 不被压缩，ref 不被永久删）。"""
    from app.services.file_manager_service import FileManagerService
    u = _mk()
    # 一个普通 + 一个锁定
    lib1, ref1 = _mk_lib_ref(u)
    lib2, ref2 = _mk_lib_ref(u)
    ref2.is_admin_locked = True
    db.session.commit()
    try:
        FileManagerService.empty_trash(u)
        # ref2 应当仍然存在（保护）
        ref2_after = UserFileRef.query.filter_by(id=ref2.id).first()
        assert ref2_after is not None
        assert ref2_after.is_admin_locked is True
        # lib2 应当未被 is_archived 修改（用 archive_reason 检查）
        lib2_after = FileLibrary.query.get(lib2.id)
        assert lib2_after is not None
    finally:
        UserFileRef.query.filter(UserFileRef.id.in_([ref1.id, ref2.id])).delete(synchronize_session=False)
        FileLibrary.query.filter(FileLibrary.id.in_([lib1.id, lib2.id])).delete(synchronize_session=False)
        User.query.filter_by(id=u.id).delete()
        db.session.commit()
```

**Step 2: 运行 → 失败**

```bash
python3 -m pytest tests/file_manager/test_admin_lock_protection.py -v
```

**Step 3: 实现保护**

修改 `app/services/file_manager_service.py`：

(a) 在 `permanent_delete` 函数顶部（约 line 531-545），找到拿到 `ref` 之后的位置，加一段：

```python
# Admin 锁定保护：拒绝清理
if ref.is_admin_locked:
    return False, '该文件已被管理员锁定，禁止永久删除'
```

(b) 在 `empty_trash` 函数（约 line 558-580），把 `for ref in refs:` 循环里的清理跳过锁定文件：

```python
for ref in refs:
    if ref.is_admin_locked:
        continue  # admin 锁定的文件保留
    # ...原清理逻辑
```

(c) 自动归档逻辑（搜索 `is_archived = True` + `archive_reason='inactive'` 那段，约 line 728），在选 lib 候选时排除有锁定 ref 的：

```python
# 找出长期不访问的 lib
candidates = (
    FileLibrary.query
    .filter(FileLibrary.last_accessed_at < cutoff)
    .filter(FileLibrary.is_archived == False)
    .all()
)
# 过滤：任何引用该 lib 的 ref 被锁定，则保护
locked_lib_ids = {
    r.file_library_id for r in
    UserFileRef.query.filter(
        UserFileRef.file_library_id.in_([c.id for c in candidates]),
        UserFileRef.is_admin_locked == True,
    ).all()
}
candidates = [c for c in candidates if c.id not in locked_lib_ids]
# ...继续原逻辑
```

具体修改位置看实际代码——以 grep 找到的 line 700+ 为准。

**Step 4: 运行测试 → 通过**

**Step 5: 跑完整 file_manager test 看无回归**

```bash
python3 -m pytest tests/ -k "file_manager" -v
```

**Step 6: Commit**

```bash
git add app/services/file_manager_service.py tests/file_manager/test_admin_lock_protection.py
git commit -m "feat(file-manager): protect admin_locked files from permanent delete + auto-archive"
```

---

## Phase 4 — Backend 路由

### Task 5: 5 个 admin API 端点

**Files:**
- Create: `app/views/file_manager_admin.py`
- Modify: `app/__init__.py` (注册新蓝图)

**Step 1: 写测试**

`tests/file_manager/test_admin_routes.py` (创建)：

```python
# -*- coding: utf-8 -*-
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
                     storage_path=f'/fake/{sha}', mime_type='text/plain')
    db.session.add(lib); db.session.commit()
    ref = UserFileRef(user_id=user.id, file_library_id=lib.id, custom_filename='x.txt')
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
```

**Step 2: 运行 → 失败**

**Step 3: 实现路由**

`app/views/file_manager_admin.py` (创建)：

```python
# -*- coding: utf-8 -*-
"""管理员视角的文件管理路由。仅 admin/ceo 可访问。"""
import logging
from flask import Blueprint, jsonify, request, render_template, send_file, abort
from flask_login import current_user, login_required

from app.models import User
from app.models.file_manager import UserFileRef
from app.services.file_admin_service import (
    list_users_with_stats, list_user_files_flat,
    set_admin_lock, transfer_file, ingest_to_wiki,
)

logger = logging.getLogger(__name__)
file_manager_admin_bp = Blueprint('file_manager_admin', __name__)


def _require_admin():
    if current_user.role not in ('admin', 'ceo'):
        return jsonify({'success': False, 'message': '仅管理员可访问'}), 403
    return None


@file_manager_admin_bp.route('/file-manager/admin')
@login_required
def admin_page():
    if current_user.role not in ('admin', 'ceo'):
        abort(403)
    return render_template('files/tw_file_manager_admin.html')


@file_manager_admin_bp.route('/api/file-manager/admin/users', methods=['GET'])
@login_required
def list_users():
    deny = _require_admin()
    if deny: return deny
    return jsonify({'success': True, 'data': list_users_with_stats()})


@file_manager_admin_bp.route('/api/file-manager/admin/files', methods=['GET'])
@login_required
def list_files():
    deny = _require_admin()
    if deny: return deny
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'success': False, 'message': '缺少 user_id'}), 400
    rows = list_user_files_flat(
        user_id,
        include_deleted=request.args.get('include_deleted', '0') == '1',
        search=(request.args.get('search') or '').strip(),
        file_type=(request.args.get('file_type') or '').strip(),
        sort=(request.args.get('sort') or 'recent').strip(),
    )
    return jsonify({'success': True, 'data': rows})


@file_manager_admin_bp.route('/api/file-manager/admin/files/<int:file_ref_id>/lock', methods=['POST'])
@login_required
def lock_file(file_ref_id):
    deny = _require_admin()
    if deny: return deny
    locked = bool((request.get_json(silent=True) or {}).get('locked', True))
    ok, msg = set_admin_lock(file_ref_id, locked=locked, by_user=current_user)
    return jsonify({'success': ok, 'message': msg}), (200 if ok else 400)


@file_manager_admin_bp.route('/api/file-manager/admin/files/<int:file_ref_id>/transfer', methods=['PATCH'])
@login_required
def transfer(file_ref_id):
    deny = _require_admin()
    if deny: return deny
    data = request.get_json(silent=True) or {}
    to_user_id = data.get('to_user_id')
    to_folder_id = data.get('to_folder_id')
    if not to_user_id:
        return jsonify({'success': False, 'message': '缺少 to_user_id'}), 400
    ok, msg = transfer_file(file_ref_id, to_user_id=int(to_user_id),
                             to_folder_id=int(to_folder_id) if to_folder_id else None,
                             by_user=current_user)
    return jsonify({'success': ok, 'message': msg}), (200 if ok else 400)


@file_manager_admin_bp.route('/api/file-manager/admin/files/<int:file_ref_id>/wiki-ingest', methods=['POST'])
@login_required
def wiki_ingest(file_ref_id):
    deny = _require_admin()
    if deny: return deny
    data = request.get_json(silent=True) or {}
    topic = (data.get('topic') or '').strip()
    scope = (data.get('scope') or 'personal').strip()
    if not topic:
        return jsonify({'success': False, 'message': '缺少 topic'}), 400
    ok, result = ingest_to_wiki(file_ref_id, topic=topic, scope=scope, by_user=current_user)
    if ok:
        return jsonify({'success': True, 'data': {'raw_id': result}})
    return jsonify({'success': False, 'message': str(result)}), 400


@file_manager_admin_bp.route('/api/file-manager/admin/files/<int:file_ref_id>/download', methods=['GET'])
@login_required
def download(file_ref_id):
    deny = _require_admin()
    if deny: return deny
    ref = UserFileRef.query.get(file_ref_id)
    if not ref:
        abort(404)
    lib = ref.file_library
    if not lib:
        abort(404)
    from app.services.file_manager_service import FileManagerService
    content = FileManagerService.read_file_content_auto_decompress(lib)
    if content is None:
        abort(500)
    from io import BytesIO
    return send_file(BytesIO(content), download_name=lib.original_filename, as_attachment=True)
```

**Step 4: 注册蓝图**

修改 `app/__init__.py`，找到其他蓝图注册的位置（搜索 `file_manager_bp`），加：

```python
from app.views.file_manager_admin import file_manager_admin_bp
app.register_blueprint(file_manager_admin_bp)
```

**Step 5: 运行测试**

```bash
python3 -m pytest tests/file_manager/test_admin_routes.py -v
```

预期: 5 passed.

**Step 6: 清理测试残留 + Commit**

```bash
git add app/views/file_manager_admin.py app/__init__.py tests/file_manager/test_admin_routes.py
git commit -m "feat(file-manager): admin routes - users/files/lock/transfer/wiki-ingest/download"
```

---

## Phase 5 — Frontend

### Task 6: 管理页 HTML 结构 + 用户列表面板

**Files:**
- Create: `app/templates/files/tw_file_manager_admin.html`
- Modify: `app/templates/files/tw_file_manager.html` (顶部加入口按钮)

**Step 1: 创建模板骨架**

`app/templates/files/tw_file_manager_admin.html`：

```html
{% extends "base.html" %}
{% from 'macros/tw_layout.html' import render_tw_layout %}

{% block title %}{{ _('文件管理 - 全部用户') }}{% endblock %}

{% block content %}
{% call(slot) render_tw_layout(active_page='file_manager', show_search=false) %}
  {% if slot == 'content' %}
  <div class="flex h-full" x-data="adminFileManager()" x-init="init()">

    <!-- 左侧：用户列表 -->
    <aside class="w-64 xl:w-72 border-r border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 overflow-y-auto flex-shrink-0">
      <div class="p-3">
        <a href="{{ url_for('file_manager.file_manager_page') }}"
           class="flex items-center gap-1 text-xs text-slate-500 hover:text-primary mb-2">
          <span class="material-symbols-outlined text-base">arrow_back</span>
          {{ _('返回我的文件') }}
        </a>
        <h2 class="text-sm font-semibold mb-2">{{ _('全部用户') }} (<span x-text="users.length"></span>)</h2>
        <input x-model="userSearch" type="text" placeholder="{{ _('搜索用户') }}"
               class="w-full px-2 py-1 text-xs border border-slate-200 dark:border-slate-700 rounded mb-2 bg-transparent">
        <ul class="space-y-1">
          <template x-for="u in filteredUsers()" :key="u.user_id">
            <li>
              <button @click="selectUser(u.user_id)"
                      :class="selectedUserId === u.user_id ? 'bg-primary/10 text-primary' : 'hover:bg-slate-50 dark:hover:bg-slate-800'"
                      class="w-full text-left px-2 py-2 rounded">
                <div class="flex items-center justify-between">
                  <span class="font-medium text-sm" x-text="u.real_name || u.username"></span>
                  <span class="text-[10px] text-slate-400" x-text="u.file_count + ' 个'"></span>
                </div>
                <div class="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-2">
                  <span x-text="u.department || '-'"></span>
                  <span x-text="formatSize(u.total_size)"></span>
                  <span x-show="u.has_locked" class="text-amber-500" title="{{ _('有已锁定文件') }}">🔒</span>
                </div>
              </button>
            </li>
          </template>
        </ul>
      </div>
    </aside>

    <!-- 右侧：文件平铺 -->
    <main class="flex-1 flex flex-col overflow-hidden bg-white dark:bg-slate-900">
      <!-- 工具条 -->
      <div class="flex items-center gap-2 px-4 py-3 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
        <h1 class="text-base font-semibold" x-text="selectedUserName || '{{ _('请选择用户') }}'"></h1>
        <span class="text-xs text-slate-500" x-text="selectedUserId ? '(' + files.length + ' 个文件)' : ''"></span>
        <div class="ml-auto flex items-center gap-2">
          <input x-model="fileSearch" @input.debounce.300ms="loadFiles()"
                 type="text" placeholder="{{ _('搜索文件') }}"
                 class="px-2 py-1 text-xs border border-slate-200 dark:border-slate-700 rounded bg-transparent">
          <select x-model="fileType" @change="loadFiles()"
                  class="px-2 py-1 text-xs border border-slate-200 dark:border-slate-700 rounded bg-transparent">
            <option value="">{{ _('全部类型') }}</option>
            <option value="pdf">PDF</option>
            <option value="office">Office</option>
            <option value="image">{{ _('图片') }}</option>
            <option value="video">{{ _('视频') }}</option>
          </select>
          <select x-model="sort" @change="loadFiles()"
                  class="px-2 py-1 text-xs border border-slate-200 dark:border-slate-700 rounded bg-transparent">
            <option value="recent">{{ _('最新') }}</option>
            <option value="name">{{ _('文件名') }}</option>
            <option value="size">{{ _('大小') }}</option>
          </select>
        </div>
      </div>

      <!-- 文件列表 -->
      <div class="flex-1 overflow-y-auto">
        <template x-if="!selectedUserId">
          <div class="p-8 text-center text-slate-500">{{ _('从左侧选择用户查看其文件') }}</div>
        </template>

        <template x-if="selectedUserId && files.length === 0">
          <div class="p-8 text-center text-slate-500">{{ _('该用户没有文件') }}</div>
        </template>

        <ul class="divide-y divide-slate-100 dark:divide-slate-800">
          <template x-for="f in files" :key="f.file_ref_id">
            <li class="px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 group">
              <div class="flex items-start gap-3">
                <span class="material-symbols-outlined text-2xl text-slate-400 mt-0.5" x-text="iconFor(f)"></span>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-sm truncate" x-text="f.original_filename"></span>
                    <span x-show="f.is_admin_locked"
                          class="px-1.5 py-0.5 text-[10px] rounded bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                      🔒 {{ _('已锁定') }}
                    </span>
                    <span x-show="f.is_in_wiki"
                          class="px-1.5 py-0.5 text-[10px] rounded bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400">
                      📚 {{ _('已入知识库') }}
                    </span>
                  </div>
                  <div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    <span class="material-symbols-outlined text-[12px] align-middle">folder</span>
                    <span x-text="f.folder_path"></span>
                    <span class="mx-1">·</span>
                    <span x-text="formatSize(f.file_size)"></span>
                    <span class="mx-1">·</span>
                    <span x-text="formatDate(f.created_at)"></span>
                  </div>
                </div>
                <!-- 操作按钮：默认隐藏，hover 显示 -->
                <div class="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 flex-shrink-0">
                  <button @click="downloadFile(f)" :title="'{{ _('下载') }}'"
                          class="p-1.5 rounded hover:bg-slate-200 dark:hover:bg-slate-700">
                    <span class="material-symbols-outlined text-sm">download</span>
                  </button>
                  <button @click="openWikiModal(f)" :title="'{{ _('转知识库') }}'"
                          class="p-1.5 rounded hover:bg-violet-100 dark:hover:bg-violet-900/30">
                    <span class="material-symbols-outlined text-sm text-violet-600">menu_book</span>
                  </button>
                  <button @click="openTransferModal(f)" :title="'{{ _('转移') }}'"
                          class="p-1.5 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30">
                    <span class="material-symbols-outlined text-sm text-blue-600">forward</span>
                  </button>
                  <button @click="toggleLock(f)" :title="f.is_admin_locked ? '{{ _('取消锁定') }}' : '{{ _('锁定') }}'"
                          class="p-1.5 rounded hover:bg-amber-100 dark:hover:bg-amber-900/30">
                    <span class="material-symbols-outlined text-sm" :class="f.is_admin_locked ? 'text-amber-600' : ''"
                          x-text="f.is_admin_locked ? 'lock_open' : 'lock'"></span>
                  </button>
                </div>
              </div>
            </li>
          </template>
        </ul>
      </div>
    </main>

    <!-- 转移弹层 -->
    <div x-show="transferModal.open" x-cloak
         class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center" @click.self="transferModal.open = false">
      <div class="bg-white dark:bg-slate-800 rounded-lg p-6 w-96 max-w-full">
        <h3 class="font-semibold mb-3">{{ _('转移文件给其他用户') }}</h3>
        <p class="text-xs text-slate-500 mb-3" x-text="'文件: ' + (transferModal.file?.original_filename || '')"></p>
        <select x-model="transferModal.targetUserId"
                class="w-full px-2 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded mb-3 bg-transparent">
          <option value="">{{ _('选择目标用户') }}</option>
          <template x-for="u in users.filter(x => x.user_id !== selectedUserId)" :key="u.user_id">
            <option :value="u.user_id" x-text="(u.real_name || u.username) + ' (' + (u.department || '-') + ')'"></option>
          </template>
        </select>
        <div class="flex justify-end gap-2">
          <button @click="transferModal.open = false" class="px-3 py-1.5 text-xs border rounded">{{ _('取消') }}</button>
          <button @click="confirmTransfer()" :disabled="!transferModal.targetUserId"
                  class="px-3 py-1.5 text-xs bg-primary text-white rounded disabled:opacity-50">{{ _('确认转移') }}</button>
        </div>
      </div>
    </div>

    <!-- 转知识库弹层 -->
    <div x-show="wikiModal.open" x-cloak
         class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center" @click.self="wikiModal.open = false">
      <div class="bg-white dark:bg-slate-800 rounded-lg p-6 w-96 max-w-full">
        <h3 class="font-semibold mb-3">{{ _('转入 Wiki 知识库') }}</h3>
        <p class="text-xs text-slate-500 mb-3" x-text="'文件: ' + (wikiModal.file?.original_filename || '')"></p>
        <label class="block text-xs mb-1">{{ _('Topic（分类目录）') }}</label>
        <input x-model="wikiModal.topic" type="text" placeholder="例如: product / sales / HR"
               class="w-full px-2 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded mb-3 bg-transparent">
        <label class="block text-xs mb-1">{{ _('权限范围') }}</label>
        <select x-model="wikiModal.scope"
                class="w-full px-2 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded mb-3 bg-transparent">
          <option value="personal">{{ _('个人') }}</option>
          <option value="department">{{ _('部门') }}</option>
          <option value="company">{{ _('公司') }}</option>
          <option value="system">{{ _('系统') }}</option>
        </select>
        <div class="flex justify-end gap-2">
          <button @click="wikiModal.open = false" class="px-3 py-1.5 text-xs border rounded">{{ _('取消') }}</button>
          <button @click="confirmWiki()" :disabled="!wikiModal.topic"
                  class="px-3 py-1.5 text-xs bg-violet-600 text-white rounded disabled:opacity-50">{{ _('确认转入') }}</button>
        </div>
      </div>
    </div>
  </div>
  {% endif %}
{% endcall %}

<script>
function adminFileManager() {
  return {
    users: [],
    userSearch: '',
    selectedUserId: null,
    files: [],
    fileSearch: '',
    fileType: '',
    sort: 'recent',
    transferModal: { open: false, file: null, targetUserId: '' },
    wikiModal: { open: false, file: null, topic: '', scope: 'personal' },

    async init() {
      await this.loadUsers();
    },

    async loadUsers() {
      const r = await fetch('/api/file-manager/admin/users');
      const j = await r.json();
      if (j.success) this.users = j.data;
    },

    filteredUsers() {
      const q = this.userSearch.toLowerCase();
      if (!q) return this.users;
      return this.users.filter(u =>
        (u.real_name || '').toLowerCase().includes(q) ||
        (u.username || '').toLowerCase().includes(q) ||
        (u.department || '').toLowerCase().includes(q)
      );
    },

    get selectedUserName() {
      const u = this.users.find(x => x.user_id === this.selectedUserId);
      return u ? (u.real_name || u.username) : '';
    },

    async selectUser(uid) {
      this.selectedUserId = uid;
      await this.loadFiles();
    },

    async loadFiles() {
      if (!this.selectedUserId) { this.files = []; return; }
      const params = new URLSearchParams({
        user_id: this.selectedUserId,
        search: this.fileSearch,
        file_type: this.fileType,
        sort: this.sort,
      });
      const r = await fetch('/api/file-manager/admin/files?' + params);
      const j = await r.json();
      if (j.success) this.files = j.data;
    },

    iconFor(f) {
      const ext = (f.original_filename || '').split('.').pop().toLowerCase();
      if (ext === 'pdf') return 'picture_as_pdf';
      if (['doc','docx'].includes(ext)) return 'description';
      if (['xls','xlsx'].includes(ext)) return 'table_chart';
      if (['png','jpg','jpeg','gif','webp'].includes(ext)) return 'image';
      if (['mp4','mov','avi'].includes(ext)) return 'movie';
      return 'insert_drive_file';
    },

    formatSize(b) {
      if (!b) return '0 B';
      const u = ['B','KB','MB','GB'];
      let i = 0; while (b >= 1024 && i < u.length-1) { b /= 1024; i++; }
      return b.toFixed(1) + ' ' + u[i];
    },

    formatDate(s) {
      if (!s) return '-';
      return new Date(s).toLocaleDateString();
    },

    downloadFile(f) {
      window.location = `/api/file-manager/admin/files/${f.file_ref_id}/download`;
    },

    async toggleLock(f) {
      const r = await fetch(`/api/file-manager/admin/files/${f.file_ref_id}/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ locked: !f.is_admin_locked }),
      });
      const j = await r.json();
      if (j.success) {
        f.is_admin_locked = !f.is_admin_locked;
      } else {
        alert(j.message || '操作失败');
      }
    },

    openTransferModal(f) {
      this.transferModal = { open: true, file: f, targetUserId: '' };
    },

    async confirmTransfer() {
      if (!this.transferModal.targetUserId) return;
      const r = await fetch(`/api/file-manager/admin/files/${this.transferModal.file.file_ref_id}/transfer`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_user_id: parseInt(this.transferModal.targetUserId) }),
      });
      const j = await r.json();
      if (j.success) {
        this.transferModal.open = false;
        await this.loadUsers();
        await this.loadFiles();
      } else {
        alert(j.message || '转移失败');
      }
    },

    openWikiModal(f) {
      this.wikiModal = { open: true, file: f, topic: '', scope: 'personal' };
    },

    async confirmWiki() {
      if (!this.wikiModal.topic) return;
      const r = await fetch(`/api/file-manager/admin/files/${this.wikiModal.file.file_ref_id}/wiki-ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: this.wikiModal.topic, scope: this.wikiModal.scope }),
      });
      const j = await r.json();
      if (j.success) {
        this.wikiModal.open = false;
        this.wikiModal.file.is_in_wiki = true;
        alert('已加入知识库');
      } else {
        alert(j.message || '加入失败');
      }
    },
  };
}
</script>
{% endblock %}
```

**Step 2: 主文件管理页加入口（仅 admin/ceo 可见）**

在 `app/templates/files/tw_file_manager.html` 顶部工具条找一个合适位置（约 line 160-170），加：

```html
{% if current_user.role in ('admin', 'ceo') %}
<a href="{{ url_for('file_manager_admin.admin_page') }}"
   class="ml-auto inline-flex items-center gap-1 px-3 py-1 text-xs bg-violet-600 text-white rounded hover:bg-violet-700">
  <span class="material-symbols-outlined text-sm">manage_accounts</span>
  {{ _('全部用户视图') }}
</a>
{% endif %}
```

**Step 3: 模板渲染验证**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 -c "
from app import create_app
from flask import render_template
app = create_app()
with app.test_request_context():
    try:
        html = render_template('files/tw_file_manager_admin.html')
        print('admin 模板渲染 OK，长度:', len(html))
    except Exception as e:
        print('渲染异常:', type(e).__name__, e)
"
```

预期: 模板渲染 OK 或仅 RuntimeError（缺少登录用户上下文，但模板语法没错）。

**Step 4: 启动本地 server 手工 smoke 测试**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 run.py
```

浏览器登录管理员账号 → `/file-manager/admin` 应能打开页面，左侧用户列表自动加载，点击用户右侧出现文件。

**Step 5: Commit**

```bash
git add app/templates/files/tw_file_manager_admin.html app/templates/files/tw_file_manager.html
git commit -m "feat(file-manager): admin UI - user list + flat files + actions"
```

---

## Phase 6 — 验收

### Task 7: 端到端验收

**Step 1: 跑全套测试**

```bash
cd /Users/nijie/Documents/PMA && \
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  python3 -m pytest tests/file_manager/ -v
```

预期: 14+ 测试全过（无新 regression）。

**Step 2: 浏览器手工测试 5 个动作**

启动本地实例，作为 admin 登录：
- ✅ 打开 `/file-manager/admin`，左侧用户列表正常加载
- ✅ 点选某个用户，右侧出现该用户的文件平铺
- ✅ 点 ⬇ 下载，文件正确下载
- ✅ 点 🔒 锁定，刷新看到 🟡 已锁定徽章
- ✅ 点 ↗ 转移给 user B，刷新看到文件从 A 消失，B 那边出现
- ✅ 点 📚 转知识库，填 topic+scope，确认后 wiki 后台出现新 raw_file
- ✅ 锁定的文件，去普通用户视图清空回收站，不应丢

**Step 3: PR / 合并 / 部署**

```bash
git push origin feature/admin-file-manager
gh pr create --title "feat: admin file manager - 全部用户视图 + 锁定/转移/转知识库"
# 等 review 通过后合并 main 部署到 NAS
```

---

## 风险与回滚

| 风险 | 影响 | 应对 |
|------|------|------|
| Migration 引入意外 schema drift | 部署中断 | autogenerate 后人工审查，只保留 3 个 add_column |
| 锁定保护逻辑漏到其他清理路径 | 锁定文件被误清理 | 全局 grep `permanent_delete\|empty_trash\|is_archived = True` 检查所有清理点 |
| 转移操作失误（admin 误点） | 文件归属错乱 | 当前未做 confirm dialog；可后续补"二次确认" |
| 转知识库时拒绝（>10MB 等） | 用户困惑 | 错误信息会原样显示在前端 alert |
| 大量用户/文件时左侧列表性能 | 慢 | 现阶段没分页；用户上百再考虑 |

---

## 完成定义 (Definition of Done)

- [ ] DB migration 5286→新 head，3 个新列就位
- [ ] 14+ 测试通过（5 service + 4 service-2 + 2 protection + 5 routes）
- [ ] /file-manager/admin 页面能打开（admin/ceo），普通用户 403
- [ ] 5 个动作（下载/锁定/取消锁定/转移/转知识库）端到端跑通
- [ ] 锁定保护 = 普通用户清空回收站时不删该锁定文件
- [ ] 主文件管理页有"全部用户视图"入口（仅 admin 可见）
- [ ] PR 合并到 main + 推送 origin
