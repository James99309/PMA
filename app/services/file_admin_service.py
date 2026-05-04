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
    每条 dict: {user_id, username, real_name, department, file_count, total_size, has_locked}
    按 file_count 降序。
    """
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
    """返回某用户所有文件（平铺），含文件夹路径 + wiki 状态。"""
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
            'display_name': ref.display_name,
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


from app.models.file_manager import get_local_time


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
    import logging
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
    from app.services.wiki.paths import get_wiki_root

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

    # 读字节
    content = FileManagerService.read_file_content_auto_decompress(lib)
    if content is None:
        return False, '无法读取文件内容'

    # 落 raw 目录
    safe_name = wiki_storage.dated_filename(lib.original_filename)
    raw_path = wiki_storage.save_raw_file(topic, safe_name, content)

    # 体量校验
    abs_path = get_wiki_root() / raw_path
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
