# -*- coding: utf-8 -*-
"""
公告模型 - 系统公告发布和管理

Announcement: 公告主表
AnnouncementRead: 公告阅读记录
AnnouncementAttachment: 公告附件
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Index

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class Announcement(db.Model):
    """公告模型"""
    __tablename__ = 'announcements'

    id = Column(Integer, primary_key=True)

    # 公告基本信息
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # 公告类型: system(系统通知), business(业务公告), urgent(紧急通知)
    announcement_type = Column(String(20), nullable=False, default='system', index=True)

    # 发布范围数据（JSON格式存储用户ID列表）
    target_users = Column(JSON, default=list)

    # 发布状态: draft(草稿), published(已发布)
    status = Column(String(20), nullable=False, default='draft', index=True)

    # 定时发布时间（为空则立即发布）
    scheduled_time = Column(DateTime, nullable=True)

    # 实际发布时间
    published_at = Column(DateTime, nullable=True)

    # 创建者
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    creator = db.relationship('User', backref='created_announcements')

    # 系统字段
    created_at = Column(DateTime, default=get_local_time, index=True)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    # 关系
    attachments = db.relationship('AnnouncementAttachment', back_populates='announcement',
                                  cascade='all, delete-orphan')
    read_records = db.relationship('AnnouncementRead', back_populates='announcement',
                                   cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_announcements_status_published', 'status', 'published_at'),
    )

    @property
    def is_readonly(self):
        """检查公告是否只读（已发布）"""
        return self.status == 'published'

    @property
    def read_count(self):
        """已读人数"""
        return sum(1 for r in self.read_records if r.is_read)

    @property
    def unread_count(self):
        """未读人数"""
        return sum(1 for r in self.read_records if not r.is_read)

    @property
    def target_user_count(self):
        """目标用户总数"""
        return len(self.read_records)

    @property
    def target_users_info(self):
        """获取目标用户详细信息"""
        if not self.target_users:
            return []
        from app.models.user import User
        users = User.query.filter(User.id.in_(self.target_users)).all()
        return [
            {
                'id': u.id,
                'name': u.real_name or u.username,
                'username': u.username
            }
            for u in users
        ]

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'announcement_type': self.announcement_type,
            'target_users': self.target_users,
            'target_users_info': self.target_users_info,
            'status': self.status,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.real_name or self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_readonly': self.is_readonly,
            'read_count': self.read_count,
            'unread_count': self.unread_count,
            'target_user_count': self.target_user_count,
            'attachments': [a.to_dict() for a in self.attachments]
        }


class AnnouncementRead(db.Model):
    """公告阅读记录模型"""
    __tablename__ = 'announcement_reads'

    id = Column(Integer, primary_key=True)

    # 关联公告
    announcement_id = Column(Integer, ForeignKey('announcements.id'), nullable=False, index=True)
    announcement = db.relationship('Announcement', back_populates='read_records')

    # 目标用户
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    user = db.relationship('User', backref='announcement_reads')

    # 阅读状态
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # 创建时间（公告发布时创建记录）
    created_at = Column(DateTime, default=get_local_time)

    __table_args__ = (
        db.UniqueConstraint('announcement_id', 'user_id', name='uq_announcement_user'),
        Index('ix_announcement_reads_user_unread', 'user_id', 'is_read'),
    )

    @classmethod
    def mark_as_read(cls, announcement_id, user_id):
        """标记公告为已读"""
        record = cls.query.filter_by(
            announcement_id=announcement_id,
            user_id=user_id
        ).first()

        if record and not record.is_read:
            record.is_read = True
            record.read_at = get_local_time()
            return record
        return None

    @classmethod
    def get_unread_count(cls, user_id):
        """获取用户未读公告数量（仅计算已发布且未删除的公告）"""
        return cls.query.filter(
            cls.user_id == user_id,
            cls.is_read == False
        ).join(Announcement).filter(
            Announcement.status == 'published',
            Announcement.is_deleted == False
        ).count()


class AnnouncementAttachment(db.Model):
    """公告附件模型"""
    __tablename__ = 'announcement_attachments'

    id = Column(Integer, primary_key=True)

    # 关联公告
    announcement_id = Column(Integer, ForeignKey('announcements.id'), nullable=False, index=True)
    announcement = db.relationship('Announcement', back_populates='attachments')

    # 文件信息
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))

    # 系统字段
    created_at = Column(DateTime, default=get_local_time)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
