"""绩效手工录入模型

人事将辅助指标数据手工录入系统，支持月度和季度两种录入粒度。
"""

from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, UniqueConstraint


class PerformanceManualEntry(db.Model):
    """绩效手工录入记录"""
    __tablename__ = 'performance_manual_entries'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    metric_code = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    period_type = Column(String(10), nullable=False)  # 'monthly' / 'quarterly'
    period = Column(Integer, nullable=False)           # 月(1-12) 或 季度(1-4)
    value = Column(Numeric(10, 2))
    note = Column(String(500))
    entered_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'metric_code', 'year', 'period_type', 'period',
                         name='uq_manual_entry'),
    )

    user = db.relationship('User', foreign_keys=[user_id], backref='manual_entries')
    entered_by_user = db.relationship('User', foreign_keys=[entered_by])
    attachments = db.relationship('PerformanceManualAttachment', backref='entry',
                                  cascade='all, delete-orphan', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric_code': self.metric_code,
            'year': self.year,
            'period_type': self.period_type,
            'period': self.period,
            'value': float(self.value) if self.value is not None else None,
            'note': self.note,
            'entered_by': self.entered_by,
            'attachments': [a.to_dict() for a in self.attachments.all()],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PerformanceManualAttachment(db.Model):
    """绩效手工录入附件"""
    __tablename__ = 'performance_manual_attachments'

    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('performance_manual_entries.id', ondelete='CASCADE'),
                      nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String(100))
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    def to_dict(self):
        return {
            'id': self.id,
            'entry_id': self.entry_id,
            'filename': self.filename,
            'storage_path': self.storage_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'uploaded_by': self.uploaded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
