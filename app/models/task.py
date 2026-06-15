# -*- coding: utf-8 -*-
"""
通用任务模型

Task: 独立于行程的任务管理
TaskAttachment: 任务附件
TaskReply: 任务回复
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, Float, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class Task(db.Model):
    """通用任务模型"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)

    # 核心
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # 人员
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    creator = relationship('User', foreign_keys=[creator_id], backref='created_tasks')

    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assignee = relationship('User', foreign_keys=[assignee_id], backref='assigned_tasks')

    # 状态
    status = Column(String(20), default='pending', nullable=False, index=True)
    # pending(等待开始) / in_progress / paused / pending_review / completed
    priority = Column(String(20), default='normal', nullable=False)
    # normal / high / urgent （UI 仅提供三级，low 保留兼容）

    # 时间
    start_date = Column(Date, nullable=True, comment='任务开始日期')
    due_date = Column(DateTime, nullable=True)
    calendar_date = Column(Date, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)

    # 外部链接
    external_link = Column(String(500), nullable=True)
    external_link_label = Column(String(100), nullable=True)

    # 关联（均可空）
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    project = relationship('Project', backref='tasks')

    quotation_id = Column(Integer, ForeignKey('quotations.id'), nullable=True)
    quotation = relationship('Quotation', backref='tasks')

    customer_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    customer = relationship('Company', backref='tasks')

    # 协助人 & 类型
    shared_with_users = Column(JSON, default=list, comment='协助人员ID列表')
    task_type = Column(String(30), default='general', comment='任务类型: general/product_dev/custom')

    # 审计（会审：多人并行审核）
    review_status = Column(String(20), nullable=True, comment='pending_review/approved/rejected')
    review_score = Column(Float, nullable=True, comment='审核通过时各审计人评价权重均值(below0.5/meet1/exceed1.5)')
    reviewed_at = Column(DateTime, nullable=True)
    # 保留旧字段兼容迁移，新逻辑使用 task_reviewers 表
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='[废弃]旧单审计人')
    review_comment = Column(Text, nullable=True, comment='[废弃]旧审计意见')

    # 系统
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    # 关联
    attachments = relationship('TaskAttachment', backref='task', lazy='dynamic',
                               cascade='all, delete-orphan',
                               order_by='TaskAttachment.created_at.desc()')
    replies = relationship('TaskReply', backref='task', lazy='dynamic',
                           cascade='all, delete-orphan',
                           order_by='TaskReply.created_at.asc()')
    subtasks = relationship('SubTask', backref='task', lazy='dynamic',
                            cascade='all, delete-orphan',
                            order_by='SubTask.sort_order, SubTask.created_at')
    task_reviewers = relationship('TaskReviewer', backref='task', lazy='joined',
                                  cascade='all, delete-orphan',
                                  order_by='TaskReviewer.created_at')

    __table_args__ = (
        Index('ix_tasks_assignee_status', 'assignee_id', 'status'),
        Index('ix_tasks_creator_status', 'creator_id', 'status'),
    )

    @property
    def effective_status(self):
        """开始时间到达后 pending 自动变为 in_progress"""
        if self.status == 'pending' and self.start_date:
            from datetime import date as _date
            if self.start_date <= _date.today():
                return 'in_progress'
        return self.status

    def to_dict(self):
        """完整序列化"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'creator_id': self.creator_id,
            'creator_name': (self.creator.real_name or self.creator.username) if self.creator else None,
            'assignee_id': self.assignee_id,
            'assignee_name': (self.assignee.real_name or self.assignee.username) if self.assignee else None,
            'status': self.effective_status,
            'priority': self.priority,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'calendar_date': self.calendar_date.isoformat() if self.calendar_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'external_link': self.external_link,
            'external_link_label': self.external_link_label,
            'project_id': self.project_id,
            'project_name': self.project.project_name if self.project else None,
            'quotation_id': self.quotation_id,
            'quotation_number': self.quotation.quotation_number if self.quotation else None,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'shared_with_users': self.shared_with_users or [],
            'task_type': self.task_type or 'general',
            'review_status': self.review_status,
            'review_score': self.review_score,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'is_audit_task': len(self.task_reviewers) > 0,
            'reviewers': [r.to_dict() for r in self.task_reviewers],
            'attachment_count': self.attachments.filter_by(is_deleted=False).count() if self.attachments else 0,
            'reply_count': self.replies.filter_by(is_deleted=False).count() if self.replies else 0,
            'subtask_count': self.subtasks.filter_by(is_deleted=False).count(),
            'subtask_completed': self.subtasks.filter_by(is_deleted=False, status='completed').count(),
            'milestone_count': self.subtasks.filter_by(is_deleted=False, is_milestone=True).count(),
            'milestone_confirmed': self.subtasks.filter_by(is_deleted=False, is_milestone=True, milestone_status='confirmed').count(),
        }

    def to_calendar_event(self):
        """FullCalendar 事件格式"""
        # 使用 calendar_date 或 due_date
        event_date = self.calendar_date or (self.due_date.date() if self.due_date else None)
        if not event_date:
            return None

        priority_colors = {
            'urgent': '#c2410c',   # orange-700 深橙
            'high': '#ea580c',     # orange-600
            'normal': '#f97316',   # orange-500
            'low': '#fb923c',      # orange-400 浅橙
        }
        color = priority_colors.get(self.priority, '#f97316')

        # 已完成用绿色，已暂停用琥珀色
        es = self.effective_status
        if es == 'completed':
            color = '#16a34a'  # green-600
        elif es == 'paused':
            color = '#d97706'  # amber-600
        elif es == 'pending':
            color = '#94a3b8'  # slate-400

        return {
            'id': f'task-{self.id}',
            'title': self.title,
            'start': event_date.isoformat(),
            'allDay': True,
            'color': color,
            'textColor': '#ffffff',
            'classNames': ['fc-event-task'],
            'extendedProps': {
                'event_type': 'task',
                'task_id': self.id,
                'status': es,
                'priority': self.priority,
                'assignee_name': (self.assignee.real_name or self.assignee.username) if self.assignee else None,
            }
        }


class TaskAttachment(db.Model):
    """任务附件"""
    __tablename__ = 'task_attachments'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, index=True)
    subtask_id = Column(Integer, ForeignKey('subtasks.id', ondelete='SET NULL'), nullable=True, comment='关联子任务')
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String(100))
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    uploader = relationship('User', foreign_keys=[uploaded_by])
    subtask = relationship('SubTask', foreign_keys=[subtask_id], lazy='joined')
    created_at = Column(DateTime, default=get_local_time)
    is_deleted = Column(Boolean, default=False)


class TaskReviewer(db.Model):
    """任务审计人（会审）"""
    __tablename__ = 'task_reviewers'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='pending', nullable=False, comment='pending/approved/rejected')
    rating = Column(String(10), nullable=True, comment='below/meet/exceed 低于/符合/超出预期')
    comment = Column(Text, nullable=True, comment='审计意见')
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_local_time)

    reviewer = relationship('User', foreign_keys=[reviewer_id], lazy='joined')

    __table_args__ = (
        Index('ix_task_reviewers_task_reviewer', 'task_id', 'reviewer_id', unique=True),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'reviewer_id': self.reviewer_id,
            'reviewer_name': (self.reviewer.real_name or self.reviewer.username) if self.reviewer else None,
            'status': self.status,
            'rating': self.rating,
            'comment': self.comment,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class TaskReply(db.Model):
    """任务回复"""
    __tablename__ = 'task_replies'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, index=True)
    subtask_id = Column(Integer, ForeignKey('subtasks.id', ondelete='SET NULL'), nullable=True, comment='关联子任务')
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    author = relationship('User', foreign_keys=[author_id])
    subtask = relationship('SubTask', foreign_keys=[subtask_id], lazy='joined')
    content = Column(Text, nullable=False)
    reply_type = Column(String(20), default='comment', nullable=False, server_default='comment')
    created_at = Column(DateTime, default=get_local_time)
    is_deleted = Column(Boolean, default=False)
