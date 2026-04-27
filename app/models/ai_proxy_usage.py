"""AI 代理用量缓存表

缓存 Mac mini 上 oat_proxy 的每日用量数据。
PMA 通过定时任务从 Mac mini admin_server 拉取数据写入此表，
供管理员后台和用户自助页面展示。
"""
from app import db
from datetime import datetime


class AIProxyUsage(db.Model):
    __tablename__ = 'ai_proxy_usage'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    provider = db.Column(db.String(32), nullable=False, default='claude')  # 预留 'openai' 等
    date = db.Column(db.Date, nullable=False, index=True)
    input_tokens = db.Column(db.BigInteger, default=0, nullable=False)
    output_tokens = db.Column(db.BigInteger, default=0, nullable=False)
    request_count = db.Column(db.Integer, default=0, nullable=False)
    last_seen_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'provider', 'date', name='uq_ai_proxy_usage_user_provider_date'),
    )

    user = db.relationship('User', backref=db.backref('ai_proxy_usage_records', lazy='dynamic', cascade='all, delete-orphan'))

    @property
    def total_tokens(self):
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'date': self.date.isoformat() if self.date else None,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
            'request_count': self.request_count,
            'last_seen_at': self.last_seen_at.isoformat() if self.last_seen_at else None,
        }

    def __repr__(self):
        return f'<AIProxyUsage user={self.user_id} provider={self.provider} date={self.date} tokens={self.total_tokens}>'
