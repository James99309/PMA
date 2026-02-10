# -*- coding: utf-8 -*-
"""
报价单产品确认任务模型

QuotationConfirmationTask: 报价单产品确认任务记录
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class QuotationConfirmationTask(db.Model):
    """报价单产品确认任务"""
    __tablename__ = 'quotation_confirmation_tasks'

    id = Column(Integer, primary_key=True)
    quotation_id = Column(Integer, ForeignKey('quotations.id'), nullable=False, index=True)
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    requester_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(Text)
    due_date = Column(DateTime)
    status = Column(String(20), default='pending', index=True)  # pending / confirmed / expired
    confirmed_at = Column(DateTime)
    workitem_id = Column(Integer, ForeignKey('work_items.id'))
    created_at = Column(DateTime, default=get_local_time)

    # Relationships
    quotation = relationship('Quotation', backref='confirmation_tasks')
    assignee = relationship('User', foreign_keys=[assignee_id], backref='assigned_confirmation_tasks')
    requester = relationship('User', foreign_keys=[requester_id], backref='requested_confirmation_tasks')
    workitem = relationship('WorkItem', backref='confirmation_task')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'quotation_id': self.quotation_id,
            'assignee_id': self.assignee_id,
            'assignee_name': (self.assignee.real_name or self.assignee.username) if self.assignee else None,
            'requester_id': self.requester_id,
            'requester_name': (self.requester.real_name or self.requester.username) if self.requester else None,
            'message': self.message,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
