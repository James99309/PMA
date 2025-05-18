from app.extensions import db
from datetime import datetime

class EventRegistry(db.Model):
    """事件类型注册表，用于管理可订阅的事件类型"""
    __tablename__ = 'event_registry'
    
    id = db.Column(db.Integer, primary_key=True)
    event_key = db.Column(db.String(50), unique=True, nullable=False, comment='事件唯一键')
    label_zh = db.Column(db.String(100), nullable=False, comment='中文名称')
    label_en = db.Column(db.String(100), nullable=False, comment='英文名称')
    default_enabled = db.Column(db.Boolean, default=True, comment='是否默认开启')
    enabled = db.Column(db.Boolean, default=True, comment='是否在通知中心展示')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EventRegistry {self.event_key}>'

class UserEventSubscription(db.Model):
    """用户事件订阅表，记录用户订阅了哪些账户的哪些事件"""
    __tablename__ = 'user_event_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='订阅者用户ID')
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='被订阅的用户ID')
    event_id = db.Column(db.Integer, db.ForeignKey('event_registry.id'), nullable=False, comment='事件ID')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用订阅')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键关系
    user = db.relationship('User', foreign_keys=[user_id], backref='subscriptions')
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='subscribers')
    event = db.relationship('EventRegistry', backref='subscriptions')
    
    # 联合唯一约束，防止重复订阅
    __table_args__ = (
        db.UniqueConstraint('user_id', 'target_user_id', 'event_id', name='uq_user_target_event'),
    )
    
    def __repr__(self):
        return f'<UserEventSubscription {self.user_id} -> {self.target_user_id}:{self.event_id}>' 