from datetime import datetime
from app.extensions import db


class PointsBehaviorConfig(db.Model):
    __tablename__ = 'points_behavior_config'

    id = db.Column(db.Integer, primary_key=True)
    behavior_code = db.Column(db.String(64), unique=True, nullable=False)
    behavior_name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(32), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=10)
    daily_cap = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    CATEGORIES = {
        'knowledge': '知识贡献',
        'business': '业务推进',
        'task': '任务达成',
        'content': '内容创作',
    }


class PointsTransaction(db.Model):
    __tablename__ = 'points_transaction'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    behavior_code = db.Column(db.String(64), nullable=False)
    source_type = db.Column(db.String(64), nullable=True)
    source_id = db.Column(db.Integer, nullable=True)
    points = db.Column(db.Integer, nullable=False)
    memo = db.Column(db.String(256), nullable=True)
    year = db.Column(db.SmallInteger, nullable=False)
    month = db.Column(db.SmallInteger, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('points_transactions', lazy='dynamic'))

    __table_args__ = (
        db.Index('ix_pt_user_year_month', 'user_id', 'year', 'month'),
        db.Index('ix_pt_year_month', 'year', 'month'),
        db.Index('ix_pt_source', 'source_type', 'source_id'),
    )


class UserPointsSummary(db.Model):
    __tablename__ = 'user_points_summary'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    year = db.Column(db.SmallInteger, primary_key=True)
    month = db.Column(db.SmallInteger, primary_key=True)
    total_points = db.Column(db.Integer, nullable=False, default=0)
    behavior_breakdown = db.Column(db.JSON, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
