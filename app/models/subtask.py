# -*- coding: utf-8 -*-
"""
子任务模型

SubTask: 任务下的节点/子任务，支持里程碑确认
SubTaskUpdate: 子任务跟进记录
SubTaskAttachment: 子任务跟进附件
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class SubTask(db.Model):
    """子任务/节点"""
    __tablename__ = 'subtasks'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 人员
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # 时间
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)

    # 状态: pending / in_progress / completed / delayed
    status = Column(String(20), default='pending', nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # 排序
    sort_order = Column(Integer, default=0)

    # 里程碑
    is_milestone = Column(Boolean, default=False, nullable=False)
    milestone_confirmer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    milestone_status = Column(String(20), nullable=True, comment='pending_confirmation/confirmed/rejected')
    milestone_confirmed_at = Column(DateTime, nullable=True)
    milestone_comment = Column(Text, nullable=True, comment='确认/驳回意见')

    # 系统字段
    created_at = Column(DateTime, default=get_local_time, nullable=False)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 关系
    assignee = relationship('User', foreign_keys=[assignee_id], lazy='joined')
    milestone_confirmer = relationship('User', foreign_keys=[milestone_confirmer_id], lazy='joined')
    updates = relationship('SubTaskUpdate', backref='subtask', lazy='dynamic',
                           cascade='all, delete-orphan',
                           order_by='SubTaskUpdate.created_at.desc()')

    __table_args__ = (
        Index('ix_subtasks_task_status', 'task_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'assignee_id': self.assignee_id,
            'assignee_name': (self.assignee.real_name or self.assignee.username) if self.assignee else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'sort_order': self.sort_order,
            'is_milestone': self.is_milestone,
            'milestone_confirmer_id': self.milestone_confirmer_id,
            'milestone_confirmer_name': (self.milestone_confirmer.real_name or self.milestone_confirmer.username) if self.milestone_confirmer else None,
            'milestone_status': self.milestone_status,
            'milestone_confirmed_at': self.milestone_confirmed_at.isoformat() if self.milestone_confirmed_at else None,
            'milestone_comment': self.milestone_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'update_count': self.updates.filter_by(is_deleted=False).count(),
        }


class SubTaskUpdate(db.Model):
    """子任务跟进记录"""
    __tablename__ = 'subtask_updates'

    id = Column(Integer, primary_key=True)
    subtask_id = Column(Integer, ForeignKey('subtasks.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=get_local_time, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 关系
    author = relationship('User', lazy='joined')
    attachments = relationship('SubTaskAttachment', backref='update', lazy='joined',
                               cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'subtask_id': self.subtask_id,
            'author_id': self.author_id,
            'author_name': (self.author.real_name or self.author.username) if self.author else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'attachments': [a.to_dict() for a in self.attachments if not a.is_deleted],
        }


class SubTaskAttachment(db.Model):
    """子任务跟进附件"""
    __tablename__ = 'subtask_attachments'

    id = Column(Integer, primary_key=True)
    update_id = Column(Integer, ForeignKey('subtask_updates.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String(100), nullable=True)
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False)

    created_at = Column(DateTime, default=get_local_time, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    uploader = relationship('User', lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'storage_path': self.storage_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'uploaded_by': self.uploaded_by,
            'uploader_name': (self.uploader.real_name or self.uploader.username) if self.uploader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
