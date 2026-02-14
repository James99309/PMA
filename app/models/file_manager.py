# -*- coding: utf-8 -*-
"""
文件管理系统数据模型

FileLibrary: 物理文件库（SHA256去重存储）
UserFolder: 用户文件夹
UserFileRef: 用户文件引用
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship, backref

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class FileLibrary(db.Model):
    """物理文件库 - SHA256去重存储"""
    __tablename__ = 'file_library'

    id = Column(Integer, primary_key=True)
    sha256_hash = Column(String(64), unique=True, nullable=False, index=True)
    original_filename = Column(String(500), nullable=False)  # 首次上传时的原始文件名
    file_size = Column(BigInteger, nullable=False)  # 文件大小(字节)
    mime_type = Column(String(100))
    storage_path = Column(String(1000), nullable=False)  # NAS存储路径
    storage_type = Column(String(20), default='nas')  # nas / supabase
    ref_count = Column(Integer, default=1)  # 引用计数
    created_at = Column(DateTime, default=get_local_time)

    # 归档压缩相关
    is_archived = Column(Boolean, default=False, index=True)     # 是否已压缩归档
    archived_at = Column(DateTime, nullable=True)                 # 归档时间
    archive_reason = Column(String(20), nullable=True)            # 'deleted' | 'inactive'
    original_size = Column(BigInteger, nullable=True)             # 压缩前原始大小
    last_accessed_at = Column(DateTime, nullable=True)            # 上次访问时间

    def to_dict(self):
        return {
            'id': self.id,
            'sha256_hash': self.sha256_hash,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'storage_path': self.storage_path,
            'storage_type': self.storage_type,
            'ref_count': self.ref_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_archived': self.is_archived or False,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'archive_reason': self.archive_reason,
            'original_size': self.original_size,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
        }


class UserFolder(db.Model):
    """用户文件夹"""
    __tablename__ = 'user_folders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey('user_folders.id'), nullable=True)  # NULL=根目录
    name = Column(String(200), nullable=False)
    depth = Column(Integer, default=0)  # 层级深度: 0,1,2 (最多3层)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    # 关系
    user = relationship('User', backref=backref('folders', lazy='dynamic'))
    parent = relationship('UserFolder', remote_side=[id],
                          backref=backref('children', lazy='dynamic'))

    __table_args__ = (
        Index('ix_user_folders_user_parent', 'user_id', 'parent_id'),
    )

    def to_dict(self, include_children=False):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'name': self.name,
            'depth': self.depth,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_children:
            result['children'] = [
                c.to_dict(include_children=True)
                for c in self.children.filter_by(is_deleted=False).order_by(UserFolder.sort_order)
            ]
        return result


class UserFileRef(db.Model):
    """用户文件引用 - 关联用户、文件夹、物理文件"""
    __tablename__ = 'user_file_refs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    folder_id = Column(Integer, ForeignKey('user_folders.id'), nullable=True)  # NULL=根目录
    file_library_id = Column(Integer, ForeignKey('file_library.id'), nullable=False)
    display_name = Column(String(500), nullable=False)  # 用户可重命名的显示名
    is_deleted = Column(Boolean, default=False)  # 软删除（回收站）
    deleted_at = Column(DateTime, nullable=True)  # 删除时间
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)

    # 关系
    user = relationship('User', backref=backref('file_refs', lazy='dynamic'))
    folder = relationship('UserFolder', backref=backref('files', lazy='dynamic'))
    file_library = relationship('FileLibrary', backref=backref('refs', lazy='dynamic'))

    __table_args__ = (
        Index('ix_user_file_refs_user_folder', 'user_id', 'folder_id'),
        Index('ix_user_file_refs_user_deleted', 'user_id', 'is_deleted'),
    )

    def to_dict(self):
        lib = self.file_library
        return {
            'id': self.id,
            'user_id': self.user_id,
            'folder_id': self.folder_id,
            'display_name': self.display_name,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # 物理文件信息
            'file_library_id': lib.id if lib else None,
            'sha256_hash': lib.sha256_hash if lib else None,
            'file_size': lib.file_size if lib else None,
            'mime_type': lib.mime_type if lib else None,
            'storage_path': lib.storage_path if lib else None,
            'storage_type': lib.storage_type if lib else None,
            'is_archived': lib.is_archived if lib else False,
            'original_size': lib.original_size if lib else None,
        }
