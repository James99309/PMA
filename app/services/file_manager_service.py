# -*- coding: utf-8 -*-
"""
文件管理服务

提供文件上传（SHA256去重）、文件夹管理、配额控制、回收站等功能。
支持归档压缩（gzip）替代永久删除、不活跃文件自动压缩、透明解压。
"""
import gzip
import hashlib
import logging
import mimetypes
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import current_app
from app import db
from app.models.file_manager import FileLibrary, UserFolder, UserFileRef

logger = logging.getLogger(__name__)

MAX_FOLDER_DEPTH = 2  # 0,1,2 = 三层


def get_local_time():
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class FileManagerService:
    """文件管理核心服务"""

    # ------------------------------------------------------------------
    # 配额
    # ------------------------------------------------------------------
    @staticmethod
    def get_quota_info(user):
        """获取用户配额信息"""
        quota = user.storage_quota or 10737418240  # 10GB
        used = user.storage_used or 0
        return {
            'quota': quota,
            'used': used,
            'remaining': max(quota - used, 0),
            'percent': round(used / quota * 100, 1) if quota > 0 else 0,
        }

    @staticmethod
    def check_quota(user, file_size):
        """检查是否超出配额，返回 (ok, msg)"""
        info = FileManagerService.get_quota_info(user)
        if file_size > info['remaining']:
            return False, f"存储空间不足。剩余 {FileManagerService.format_size(info['remaining'])}，文件大小 {FileManagerService.format_size(file_size)}"
        return True, ''

    @staticmethod
    def update_used_storage(user):
        """重新计算并更新用户已用存储"""
        total = db.session.query(
            db.func.coalesce(db.func.sum(FileLibrary.file_size), 0)
        ).join(
            UserFileRef, UserFileRef.file_library_id == FileLibrary.id
        ).filter(
            UserFileRef.user_id == user.id,
            UserFileRef.is_deleted == False
        ).scalar()
        user.storage_used = total
        return total

    @staticmethod
    def format_size(size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1048576:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1073741824:
            return f"{size_bytes / 1048576:.1f} MB"
        else:
            return f"{size_bytes / 1073741824:.2f} GB"

    # ------------------------------------------------------------------
    # 文件上传（SHA256 去重）
    # ------------------------------------------------------------------
    @staticmethod
    def upload_file(user, file_obj, folder_id=None):
        """
        上传文件，SHA256去重。

        Args:
            user: 当前用户
            file_obj: Flask request.files 对象
            folder_id: 目标文件夹ID，None=根目录

        Returns:
            (success, data_or_error)
        """
        filename = file_obj.filename
        if not filename:
            return False, '文件名不能为空'

        # 读取文件数据并计算 SHA256
        file_obj.seek(0)
        file_data = file_obj.read()
        file_size = len(file_data)
        file_obj.seek(0)

        if file_size == 0:
            return False, '文件不能为空'

        # 检查配额
        ok, msg = FileManagerService.check_quota(user, file_size)
        if not ok:
            return False, msg

        # 验证文件夹
        if folder_id:
            folder = UserFolder.query.filter_by(
                id=folder_id, user_id=user.id, is_deleted=False
            ).first()
            if not folder:
                return False, '文件夹不存在'

        sha256 = hashlib.sha256(file_data).hexdigest()
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        # 查找是否已有相同文件
        existing_lib = FileLibrary.query.filter_by(sha256_hash=sha256).first()

        if existing_lib:
            # 文件已存在，增加引用计数
            existing_lib.ref_count += 1
            lib_entry = existing_lib
        else:
            # 新文件，上传到 NAS
            storage_result = FileManagerService._upload_to_storage(
                user.id, file_data, filename, mime_type
            )
            if not storage_result:
                return False, '文件上传到存储失败'

            lib_entry = FileLibrary(
                sha256_hash=sha256,
                original_filename=filename,
                file_size=file_size,
                mime_type=mime_type,
                storage_path=storage_result['storage_path'],
                storage_type=storage_result.get('storage', 'nas'),
                last_accessed_at=get_local_time(),
            )
            db.session.add(lib_entry)
            db.session.flush()

        # 创建用户文件引用
        ref = UserFileRef(
            user_id=user.id,
            folder_id=folder_id,
            file_library_id=lib_entry.id,
            display_name=filename,
        )
        db.session.add(ref)

        # 更新配额
        user.storage_used = (user.storage_used or 0) + file_size

        db.session.commit()
        return True, ref.to_dict()

    @staticmethod
    def _upload_to_storage(user_id, file_data, filename, mime_type):
        """上传文件到 NAS/Supabase"""
        try:
            from app.utils.smart_storage_manager import SmartStorageManager
            storage = SmartStorageManager()

            # 根据 mime_type 选择正确的 file_type，匹配存储层白名单
            if mime_type and mime_type.startswith('image/'):
                file_type = 'image'
            elif mime_type == 'application/pdf':
                file_type = 'pdf'
            else:
                file_type = 'attachment'

            result = storage.upload_file(
                object_id=user_id,
                file=file_data,
                filename=filename,
                file_type=file_type,
                bucket_type='file_library',
                business_type='file_manager',
            )
            return result
        except Exception as e:
            logger.error(f"文件存储上传失败: {e}")
            return None

    # ------------------------------------------------------------------
    # 文件夹 CRUD
    # ------------------------------------------------------------------
    @staticmethod
    def create_folder(user, name, parent_id=None):
        """创建文件夹"""
        name = name.strip()
        if not name:
            return False, '文件夹名称不能为空'
        if len(name) > 200:
            return False, '文件夹名称过长'

        depth = 0
        if parent_id:
            parent = UserFolder.query.filter_by(
                id=parent_id, user_id=user.id, is_deleted=False
            ).first()
            if not parent:
                return False, '父文件夹不存在'
            if parent.depth >= MAX_FOLDER_DEPTH:
                return False, f'文件夹层级不能超过{MAX_FOLDER_DEPTH + 1}层'
            depth = parent.depth + 1

        # 同级同名检查
        exists = UserFolder.query.filter_by(
            user_id=user.id, parent_id=parent_id, name=name, is_deleted=False
        ).first()
        if exists:
            return False, '同级已存在同名文件夹'

        folder = UserFolder(
            user_id=user.id,
            parent_id=parent_id,
            name=name,
            depth=depth,
        )
        db.session.add(folder)
        db.session.commit()
        return True, folder.to_dict()

    @staticmethod
    def rename_folder(user, folder_id, new_name):
        """重命名文件夹"""
        new_name = new_name.strip()
        if not new_name:
            return False, '文件夹名称不能为空'

        folder = UserFolder.query.filter_by(
            id=folder_id, user_id=user.id, is_deleted=False
        ).first()
        if not folder:
            return False, '文件夹不存在'

        # 同级同名检查
        exists = UserFolder.query.filter_by(
            user_id=user.id, parent_id=folder.parent_id, name=new_name, is_deleted=False
        ).filter(UserFolder.id != folder_id).first()
        if exists:
            return False, '同级已存在同名文件夹'

        folder.name = new_name
        folder.updated_at = get_local_time()
        db.session.commit()
        return True, folder.to_dict()

    @staticmethod
    def delete_folder(user, folder_id):
        """删除文件夹（递归软删除子文件夹和文件）"""
        folder = UserFolder.query.filter_by(
            id=folder_id, user_id=user.id, is_deleted=False
        ).first()
        if not folder:
            return False, '文件夹不存在'

        now = get_local_time()
        FileManagerService._recursive_delete_folder(folder, now)
        db.session.commit()
        return True, '文件夹已删除'

    @staticmethod
    def _recursive_delete_folder(folder, now):
        """递归软删除文件夹及其内容"""
        # 删除子文件夹
        for child in folder.children.filter_by(is_deleted=False):
            FileManagerService._recursive_delete_folder(child, now)

        # 软删除该文件夹中的文件
        for ref in folder.files.filter_by(is_deleted=False):
            ref.is_deleted = True
            ref.deleted_at = now

        folder.is_deleted = True
        folder.updated_at = now

    @staticmethod
    def get_folder_tree(user):
        """获取用户完整的文件夹树"""
        root_folders = UserFolder.query.filter_by(
            user_id=user.id, parent_id=None, is_deleted=False
        ).order_by(UserFolder.sort_order, UserFolder.name).all()

        return [f.to_dict(include_children=True) for f in root_folders]

    # ------------------------------------------------------------------
    # 文件操作
    # ------------------------------------------------------------------
    @staticmethod
    def list_files(user, folder_id=None, include_deleted=False):
        """列出文件夹内容"""
        # 文件夹列表
        folders = UserFolder.query.filter_by(
            user_id=user.id, parent_id=folder_id, is_deleted=False
        ).order_by(UserFolder.sort_order, UserFolder.name).all()

        # 文件列表
        query = UserFileRef.query.filter_by(
            user_id=user.id, folder_id=folder_id
        )
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        files = query.order_by(UserFileRef.created_at.desc()).all()

        return {
            'folders': [f.to_dict() for f in folders],
            'files': [f.to_dict() for f in files],
        }

    @staticmethod
    def get_breadcrumbs(user, folder_id):
        """获取面包屑导航路径"""
        crumbs = []
        current = UserFolder.query.filter_by(
            id=folder_id, user_id=user.id
        ).first() if folder_id else None

        while current:
            crumbs.insert(0, {'id': current.id, 'name': current.name})
            current = current.parent if current.parent_id else None

        return crumbs

    @staticmethod
    def rename_file(user, file_ref_id, new_name):
        """重命名文件"""
        new_name = new_name.strip()
        if not new_name:
            return False, '文件名不能为空'

        ref = UserFileRef.query.filter_by(
            id=file_ref_id, user_id=user.id, is_deleted=False
        ).first()
        if not ref:
            return False, '文件不存在'

        ref.display_name = new_name
        ref.updated_at = get_local_time()
        db.session.commit()
        return True, ref.to_dict()

    @staticmethod
    def move_file(user, file_ref_id, target_folder_id):
        """移动文件到另一个文件夹"""
        ref = UserFileRef.query.filter_by(
            id=file_ref_id, user_id=user.id, is_deleted=False
        ).first()
        if not ref:
            return False, '文件不存在'

        # 验证目标文件夹
        if target_folder_id:
            folder = UserFolder.query.filter_by(
                id=target_folder_id, user_id=user.id, is_deleted=False
            ).first()
            if not folder:
                return False, '目标文件夹不存在'

        ref.folder_id = target_folder_id
        ref.updated_at = get_local_time()
        db.session.commit()
        return True, ref.to_dict()

    @staticmethod
    def move_files_batch(user, file_ref_ids, target_folder_id):
        """批量移动文件"""
        if target_folder_id:
            folder = UserFolder.query.filter_by(
                id=target_folder_id, user_id=user.id, is_deleted=False
            ).first()
            if not folder:
                return False, '目标文件夹不存在'

        refs = UserFileRef.query.filter(
            UserFileRef.id.in_(file_ref_ids),
            UserFileRef.user_id == user.id,
            UserFileRef.is_deleted == False
        ).all()

        now = get_local_time()
        for ref in refs:
            ref.folder_id = target_folder_id
            ref.updated_at = now

        db.session.commit()
        return True, f'已移动 {len(refs)} 个文件'

    # ------------------------------------------------------------------
    # 回收站
    # ------------------------------------------------------------------
    @staticmethod
    def soft_delete_file(user, file_ref_id):
        """软删除文件（移入回收站）"""
        ref = UserFileRef.query.filter_by(
            id=file_ref_id, user_id=user.id, is_deleted=False
        ).first()
        if not ref:
            return False, '文件不存在'

        ref.is_deleted = True
        ref.deleted_at = get_local_time()
        db.session.commit()
        return True, '已移入回收站'

    @staticmethod
    def soft_delete_files_batch(user, file_ref_ids):
        """批量软删除"""
        refs = UserFileRef.query.filter(
            UserFileRef.id.in_(file_ref_ids),
            UserFileRef.user_id == user.id,
            UserFileRef.is_deleted == False
        ).all()

        now = get_local_time()
        for ref in refs:
            ref.is_deleted = True
            ref.deleted_at = now

        db.session.commit()
        return True, f'已将 {len(refs)} 个文件移入回收站'

    @staticmethod
    def restore_file(user, file_ref_id):
        """从回收站恢复文件"""
        ref = UserFileRef.query.filter_by(
            id=file_ref_id, user_id=user.id, is_deleted=True
        ).first()
        if not ref:
            return False, '文件不存在'

        # 如果原文件夹已删除，恢复到根目录
        if ref.folder_id:
            folder = UserFolder.query.filter_by(
                id=ref.folder_id, is_deleted=False
            ).first()
            if not folder:
                ref.folder_id = None

        ref.is_deleted = False
        ref.deleted_at = None
        db.session.commit()
        return True, ref.to_dict()

    @staticmethod
    def list_trash(user):
        """列出回收站内容"""
        files = UserFileRef.query.filter_by(
            user_id=user.id, is_deleted=True
        ).order_by(UserFileRef.deleted_at.desc()).all()
        return [f.to_dict() for f in files]

    @staticmethod
    def permanent_delete(user, file_ref_id):
        """永久删除文件（实际为归档压缩，物理文件不真删）"""
        ref = UserFileRef.query.filter_by(
            id=file_ref_id, user_id=user.id, is_deleted=True
        ).first()
        if not ref:
            return False, '文件不存在或不在回收站中'

        lib = ref.file_library
        file_size = lib.file_size if lib else 0

        # 减少引用计数
        if lib:
            lib.ref_count = max(lib.ref_count - 1, 0)
            if lib.ref_count <= 0 and not lib.is_archived:
                # 无引用，归档压缩而非删除
                FileManagerService._compress_and_archive(lib, reason='deleted')

        # 删除用户引用（用户看不到了）
        db.session.delete(ref)

        # 释放配额
        user.storage_used = max((user.storage_used or 0) - file_size, 0)
        db.session.commit()
        return True, '已永久删除'

    @staticmethod
    def empty_trash(user):
        """清空回收站（归档压缩而非真删）"""
        refs = UserFileRef.query.filter_by(
            user_id=user.id, is_deleted=True
        ).all()

        total_freed = 0
        for ref in refs:
            lib = ref.file_library
            if lib:
                total_freed += lib.file_size
                lib.ref_count = max(lib.ref_count - 1, 0)
                if lib.ref_count <= 0 and not lib.is_archived:
                    FileManagerService._compress_and_archive(lib, reason='deleted')
            db.session.delete(ref)

        user.storage_used = max((user.storage_used or 0) - total_freed, 0)
        db.session.commit()
        return True, f'已清空回收站，释放 {FileManagerService.format_size(total_freed)}'

    @staticmethod
    def _delete_from_storage(storage_path, storage_type='nas'):
        """从存储删除物理文件（根据 storage_type 决定 NAS 或本地）"""
        try:
            import os
            if storage_type == 'nas':
                from app.utils.smart_storage_manager import SmartStorageManager
                storage = SmartStorageManager()
                nas_subdir = storage.bucket_mapping.get('file_library', 'file-library')
                full_path = f"{nas_subdir}/{storage_path}"
                storage.nas_client.delete_file(full_path)
                logger.info(f"已删除 NAS 文件: {full_path}")
            else:
                local_path = os.path.join('./storage', storage_path)
                if os.path.exists(local_path):
                    os.remove(local_path)
                    logger.info(f"已删除本地文件: {local_path}")
        except Exception as e:
            logger.error(f"删除存储文件失败: {e}")

    # ------------------------------------------------------------------
    # 归档压缩
    # ------------------------------------------------------------------
    @staticmethod
    def _compress_and_archive(lib, reason):
        """将文件 gzip 压缩并标记为归档"""
        try:
            # 幂等检查：已归档则跳过
            if lib.is_archived:
                return True

            content = FileManagerService._read_library_content(lib)
            if not content:
                logger.warning(f"归档失败: 无法读取文件 {lib.storage_path}")
                return False

            compressed = gzip.compress(content)
            new_path = lib.storage_path + '.gz'

            # 先上传压缩文件（DB 未变，失败无副作用）
            ok = FileManagerService._upload_raw_to_storage(compressed, new_path, lib.storage_type)
            if not ok:
                logger.error(f"归档失败: 无法上传压缩文件 {new_path}")
                return False

            # 上传成功后更新 DB
            old_path = lib.storage_path
            lib.original_size = lib.file_size
            lib.file_size = len(compressed)
            lib.storage_path = new_path
            lib.is_archived = True
            lib.archived_at = get_local_time()
            lib.archive_reason = reason
            db.session.flush()

            # 删除原始文件（非关键操作，失败不影响归档状态）
            FileManagerService._delete_from_storage(old_path, lib.storage_type)
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"归档压缩异常: {e}")
            return False

    @staticmethod
    def _read_library_content(lib):
        """从存储后端读取 FileLibrary 的原始内容（不解压）"""
        try:
            from app.utils.smart_storage_manager import SmartStorageManager
            import os

            if lib.storage_type == 'nas':
                storage = SmartStorageManager()
                if storage.nas_enabled and storage.is_nas_available():
                    nas_subdir = storage.bucket_mapping.get('file_library', 'file-library')
                    full_path = f"{nas_subdir}/{lib.storage_path}"
                    return storage.nas_client.download_file(full_path)
            else:
                local_path = os.path.join('./storage', lib.storage_path)
                if os.path.exists(local_path):
                    with open(local_path, 'rb') as f:
                        return f.read()
        except Exception as e:
            logger.error(f"读取文件内容失败: {e}")
        return None

    @staticmethod
    def _upload_raw_to_storage(data, storage_path, storage_type):
        """直接上传原始字节到存储"""
        try:
            from app.utils.smart_storage_manager import SmartStorageManager
            import os

            if storage_type == 'nas':
                storage = SmartStorageManager()
                if storage.nas_enabled and storage.is_nas_available():
                    nas_subdir = storage.bucket_mapping.get('file_library', 'file-library')
                    full_path = f"{nas_subdir}/{storage_path}"
                    result = storage.nas_client.upload_file(
                        file_content=data,
                        remote_path=full_path,
                        content_type='application/gzip'
                    )
                    return bool(result)
            else:
                local_path = os.path.join('./storage', storage_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(data)
                return True
        except Exception as e:
            logger.error(f"上传原始文件失败: {e}")
        return False

    @staticmethod
    def read_file_content_auto_decompress(lib):
        """读取文件内容，如果是归档文件则自动解压"""
        content = FileManagerService._read_library_content(lib)
        if not content:
            return None

        # 如果是归档文件，自动解压
        if lib.is_archived and lib.storage_path.endswith('.gz'):
            try:
                content = gzip.decompress(content)
            except Exception as e:
                logger.error(f"解压文件失败: {e}")
                return None

        # 更新访问时间
        lib.last_accessed_at = get_local_time()
        db.session.commit()

        # 如果是不活跃归档，异步恢复为非归档
        if lib.is_archived and lib.archive_reason == 'inactive':
            FileManagerService._async_restore_inactive(lib.id)

        return content

    @staticmethod
    def _async_restore_inactive(lib_id):
        """在后台线程恢复不活跃归档文件"""
        from flask import current_app
        app = current_app._get_current_object()

        def _restore():
            with app.app_context():
                try:
                    from sqlalchemy import text
                    # 使用行级锁防止并发恢复
                    lib = db.session.query(FileLibrary).filter_by(
                        id=lib_id, is_archived=True, archive_reason='inactive'
                    ).with_for_update(skip_locked=True).first()
                    if not lib:
                        return

                    content = FileManagerService._read_library_content(lib)
                    if not content:
                        return
                    original = gzip.decompress(content)
                    original_path = lib.storage_path[:-3]  # 去掉 .gz

                    # 先更新 DB（指向新路径），再操作存储
                    old_gz_path = lib.storage_path
                    lib.file_size = lib.original_size or len(original)
                    lib.storage_path = original_path
                    lib.is_archived = False
                    lib.archived_at = None
                    lib.archive_reason = None
                    lib.original_size = None
                    db.session.flush()

                    # 上传原始文件
                    ok = FileManagerService._upload_raw_to_storage(original, original_path, lib.storage_type)
                    if not ok:
                        db.session.rollback()
                        return

                    db.session.commit()

                    # 删除压缩文件（非关键，失败也不影响）
                    FileManagerService._delete_from_storage(old_gz_path)
                    logger.info(f"已自动恢复不活跃归档文件: {original_path}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"异步恢复归档文件失败: {e}")

        threading.Thread(target=_restore, daemon=True).start()

    @staticmethod
    def archive_inactive_files(days=90):
        """压缩超过 N 天未访问的文件"""
        cutoff = get_local_time() - timedelta(days=days)
        libs = FileLibrary.query.filter(
            FileLibrary.is_archived == False,
            FileLibrary.ref_count > 0,
            FileLibrary.file_size > 4096,  # 跳过 <4KB 的小文件（gzip 开销大于收益）
            db.or_(
                FileLibrary.last_accessed_at < cutoff,
                db.and_(
                    FileLibrary.last_accessed_at == None,
                    FileLibrary.created_at < cutoff
                )
            )
        ).all()

        archived_count = 0
        for lib in libs:
            try:
                ok = FileManagerService._compress_and_archive(lib, reason='inactive')
                if ok:
                    db.session.commit()
                    archived_count += 1
            except Exception as e:
                db.session.rollback()
                logger.error(f"归档文件 {lib.id} 失败: {e}")

        return archived_count

    @staticmethod
    def admin_restore_archived_file(admin_user, lib_id, target_user_id):
        """管理员恢复已归档文件给指定用户"""
        if admin_user.role != 'admin':
            return False, '权限不足'

        lib = FileLibrary.query.get(lib_id)
        if not lib:
            return False, '文件不存在'
        if not lib.is_archived:
            return False, '文件未被归档'

        # 读取并解压
        content = FileManagerService._read_library_content(lib)
        if not content:
            return False, '无法读取归档文件'

        try:
            original = gzip.decompress(content)
        except Exception:
            return False, '解压失败'

        # 上传原始文件
        original_path = lib.storage_path[:-3] if lib.storage_path.endswith('.gz') else lib.storage_path
        ok = FileManagerService._upload_raw_to_storage(original, original_path, lib.storage_type)
        if not ok:
            return False, '恢复文件上传失败'

        # 删除压缩文件
        FileManagerService._delete_from_storage(lib.storage_path)

        # 更新 FileLibrary
        lib.file_size = lib.original_size or len(original)
        lib.storage_path = original_path
        lib.is_archived = False
        lib.archived_at = None
        lib.archive_reason = None
        lib.original_size = None
        lib.ref_count = max(lib.ref_count, 1)

        # 创建新的 UserFileRef
        from app.models.user import User
        target_user = User.query.get(target_user_id)
        if not target_user:
            return False, '目标用户不存在'

        ref = UserFileRef(
            user_id=target_user_id,
            folder_id=None,
            file_library_id=lib.id,
            display_name=lib.original_filename,
        )
        db.session.add(ref)

        # 更新配额
        target_user.storage_used = (target_user.storage_used or 0) + lib.file_size

        db.session.commit()
        return True, ref.to_dict()

    @staticmethod
    def list_archived_files(page=1, per_page=50):
        """列出所有归档文件（管理员用）"""
        query = FileLibrary.query.filter(
            FileLibrary.is_archived == True
        ).order_by(FileLibrary.archived_at.desc())

        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'items': [lib.to_dict() for lib in items],
        }

    # ------------------------------------------------------------------
    # 搜索
    # ------------------------------------------------------------------
    @staticmethod
    def search_files(user, keyword):
        """按文件名搜索用户所有文件"""
        keyword = keyword.strip()
        if not keyword:
            return []

        refs = UserFileRef.query.filter(
            UserFileRef.user_id == user.id,
            UserFileRef.is_deleted == False,
            UserFileRef.display_name.ilike(f'%{keyword}%')
        ).order_by(UserFileRef.updated_at.desc()).limit(50).all()

        results = []
        for ref in refs:
            d = ref.to_dict()
            # 附加文件夹路径
            d['folder_path'] = FileManagerService._get_folder_path(ref.folder_id, user.id)
            results.append(d)
        return results

    @staticmethod
    def _get_folder_path(folder_id, user_id):
        """获取文件夹的路径字符串"""
        if not folder_id:
            return '/'
        parts = []
        current = UserFolder.query.get(folder_id)
        while current and current.user_id == user_id:
            parts.insert(0, current.name)
            current = current.parent if current.parent_id else None
        return '/' + '/'.join(parts) if parts else '/'

    # 知识库状态查询方法已在 2026-04-09 迁移期间移除。
    # 旧 KnowledgeDocument 已下线，新的 Wiki 方案不通过文件引用来标记"是否在知识库"。
    # 如果前端需要知识库状态，改走 /api/knowledge/documents/file-status（返回空）。
