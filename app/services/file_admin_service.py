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
    # 与个人侧 file_wiki_status 接口语义一致：
    #   in_wiki=True 仅在编译完成 (ingest_status='ingested') 时为 true，
    #   pending/processing 时显示为 "编译中"
    wiki_status_by_lib: dict[int, str] = {}
    raw_rows = (db.session.query(KnowledgeRawFile.file_library_id, KnowledgeRawFile.ingest_status)
                          .filter(KnowledgeRawFile.file_library_id.in_(lib_ids))
                          .all()) if lib_ids else []
    for fl_id, status in raw_rows:
        # 同一 file_library 可能有多条 raw_file，只要任一已 ingested 视为 in_wiki
        prev = wiki_status_by_lib.get(fl_id)
        if status == 'ingested' or prev != 'ingested':
            wiki_status_by_lib[fl_id] = status

    rows = []
    for ref, lib, folder in triples:
        wiki_status = wiki_status_by_lib.get(lib.id)
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
            'is_in_wiki': wiki_status == 'ingested',
            'wiki_status': wiki_status,  # None / pending / processing / ingested / failed
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


# 已移除 ingest_to_wiki —— 管理员前端现在直接调用个人侧
# /api/wiki/raw-files/from-file-ref，复用其异步编译 + 通知逻辑，
# 避免双份实现造成的状态/编译触发不一致。
