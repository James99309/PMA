# -*- coding: utf-8 -*-
"""
资源池访问请求模型 - 用于客户/项目跨权限访问请求

AccessRequest: 记录用户对无权限客户/项目的访问请求
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class AccessRequest(db.Model):
    """资源池访问请求模型"""
    __tablename__ = 'access_requests'

    id = Column(Integer, primary_key=True)

    # 请求人
    requester_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    requester = db.relationship('User', foreign_keys=[requester_id],
                                backref=db.backref('access_requests_sent', lazy='dynamic'))

    # 审批人（归属人或商务经理）
    approver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approver = db.relationship('User', foreign_keys=[approver_id],
                               backref=db.backref('access_requests_received', lazy='dynamic'))

    # 目标实体
    entity_type = Column(String(20), nullable=False)  # 'customer' | 'project'
    entity_id = Column(Integer, nullable=False)

    # 状态
    status = Column(String(20), nullable=False, default='pending')  # pending | approved | rejected

    # 请求说明
    request_message = Column(Text)

    # 请求方希望获得的数据选项
    requested_options = Column(JSON)

    # 批准时的共享内容选择
    share_options = Column(JSON)

    # 时间戳
    created_at = Column(DateTime, default=get_local_time)
    resolved_at = Column(DateTime)

    __table_args__ = (
        Index('ix_access_requests_requester_status', 'requester_id', 'status'),
        Index('ix_access_requests_approver_status', 'approver_id', 'status'),
        Index('ix_access_requests_entity', 'entity_type', 'entity_id'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'requester_id': self.requester_id,
            'requester_name': (self.requester.real_name or self.requester.username) if self.requester else None,
            'approver_id': self.approver_id,
            'approver_name': (self.approver.real_name or self.approver.username) if self.approver else None,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'status': self.status,
            'request_message': self.request_message,
            'requested_options': self.requested_options,
            'share_options': self.share_options,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
        }
