# -*- coding: utf-8 -*-
"""
日志阅读记录模型 - 跟踪谁阅读了谁的日志

WorklogRead: 日志阅读记录
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class WorklogRead(db.Model):
    """日志阅读记录模型 - 跟踪谁阅读了谁的日志"""
    __tablename__ = 'worklog_reads'

    id = Column(Integer, primary_key=True)

    # 被阅读的日志
    worklog_id = Column(Integer, ForeignKey('worklogs.id'), nullable=False, index=True)
    worklog = db.relationship('WorkLog', backref='read_records')

    # 阅读者
    reader_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    reader = db.relationship('User', backref='worklog_reads')

    # 阅读时间
    read_at = Column(DateTime, default=get_local_time)

    # 唯一约束：每个用户对每条日志只有一条阅读记录
    __table_args__ = (
        db.UniqueConstraint('worklog_id', 'reader_id', name='uq_worklog_reader'),
        Index('ix_worklog_reads_worklog_reader', 'worklog_id', 'reader_id'),
    )

    @classmethod
    def mark_as_read(cls, worklog_id, reader_id):
        """标记日志为已读

        Args:
            worklog_id: 日志ID
            reader_id: 阅读者ID

        Returns:
            WorklogRead: 阅读记录对象
        """
        # 检查是否已有记录
        existing = cls.query.filter_by(
            worklog_id=worklog_id,
            reader_id=reader_id
        ).first()

        if existing:
            # 更新阅读时间
            existing.read_at = get_local_time()
            return existing

        # 创建新记录
        record = cls(
            worklog_id=worklog_id,
            reader_id=reader_id
        )
        db.session.add(record)
        return record

    @classmethod
    def get_read_worklog_ids(cls, reader_id, worklog_ids):
        """获取用户已读的日志ID列表

        Args:
            reader_id: 阅读者ID
            worklog_ids: 要检查的日志ID列表

        Returns:
            set: 已读的日志ID集合
        """
        if not worklog_ids:
            return set()

        records = cls.query.filter(
            cls.reader_id == reader_id,
            cls.worklog_id.in_(worklog_ids)
        ).all()

        return set(r.worklog_id for r in records)

    @classmethod
    def is_read(cls, worklog_id, reader_id):
        """检查日志是否已被阅读

        Args:
            worklog_id: 日志ID
            reader_id: 阅读者ID

        Returns:
            bool: 是否已读
        """
        return cls.query.filter_by(
            worklog_id=worklog_id,
            reader_id=reader_id
        ).first() is not None
