# -*- coding: utf-8 -*-
"""钉钉集成相关模型。

- DingtalkUserMapping: PMA 用户 ↔ 钉钉 userid
- DingtalkSyncQueue: WorkItem 推钉钉的异步队列 + 失败重试
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from app import db


def _now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class DingtalkUserMapping(db.Model):
    """PMA 用户与钉钉 userid 的映射表。"""
    __tablename__ = 'dingtalk_user_mappings'

    id = Column(Integer, primary_key=True)
    pma_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    dingtalk_userid = Column(String(128), nullable=False, unique=True)
    dingtalk_unionid = Column(String(128))
    matched_by = Column(String(20), default='mobile')   # mobile / manual / name
    note = Column(String(200))
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)
    last_verified_at = Column(DateTime)

    pma_user = relationship('User', backref=db.backref('dingtalk_mapping', uselist=False))


class DingtalkSyncQueue(db.Model):
    """WorkItem → 钉钉日程的推送队列（失败重试）。"""
    __tablename__ = 'dingtalk_sync_queue'

    id = Column(Integer, primary_key=True)
    work_item_id = Column(Integer, ForeignKey('work_items.id'), nullable=True, index=True)
    action = Column(String(20), nullable=False)          # create / update / delete
    dingtalk_event_id = Column(String(128))              # delete 时需要
    dingtalk_userid = Column(String(128))                # 所属用户 (delete 也要)
    payload_snapshot = Column(Text)                      # JSON 字符串，用于事后排查

    status = Column(String(20), default='pending', index=True)   # pending / running / success / failed
    attempts = Column(Integer, default=0)
    last_error = Column(Text)

    created_at = Column(DateTime, default=_now, index=True)
    updated_at = Column(DateTime, default=_now, onupdate=_now)
    next_retry_at = Column(DateTime, index=True)

    __table_args__ = (
        Index('ix_dingtalk_sync_queue_status_retry', 'status', 'next_retry_at'),
    )
