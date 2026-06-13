# -*- coding: utf-8 -*-
"""季度绩效结算单(2026-06)

每季度 HR 发起,经直属上级 + 总经理审批,通过后按「绩效基数 × 得分%」折算成
绩效薪资金额写入个人薪资,并锁定该季度薪资绩效部分。设计见
docs/plans/2026-06-13-quarterly-perf-settlement-design.md
"""
from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, JSON, ForeignKey, UniqueConstraint


class PerformanceSettlement(db.Model):
    __tablename__ = 'performance_settlements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)            # 1-4

    score = Column(Numeric(6, 2))                         # 季度得分快照(0-100)
    base_amount = Column(Numeric(15, 2))                  # 季度绩效基数快照(元)
    settled_amount = Column(Numeric(15, 2))              # 折算金额 = base × score/100(元)
    score_snapshot = Column(JSON)                         # 每项明细留痕

    status = Column(String(20), default='pending')       # draft|pending|approved|rejected
    is_locked = Column(Boolean, default=False)            # 通过后锁定薪资绩效部分
    initiated_by = Column(Integer, ForeignKey('users.id'))   # HR
    approval_instance_id = Column(Integer)               # 关联审批实例
    settled_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint('user_id', 'year', 'quarter', name='uq_perf_settlement'),)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'year': self.year,
            'quarter': self.quarter,
            'score': float(self.score) if self.score is not None else None,
            'base_amount': float(self.base_amount) if self.base_amount is not None else None,
            'settled_amount': float(self.settled_amount) if self.settled_amount is not None else None,
            'status': self.status,
            'is_locked': bool(self.is_locked),
            'approval_instance_id': self.approval_instance_id,
            'settled_at': self.settled_at.isoformat() if self.settled_at else None,
        }
