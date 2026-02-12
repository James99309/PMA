"""用户积分流水表 - 持久化存储积分快照

积分按年度计算，跨年清零，历史年度永久保留。
报价单创建/更新时写入快照，导航栏API从此表SUM读取。
"""
from datetime import datetime
from app.extensions import db


class UserPointsLedger(db.Model):
    __tablename__ = 'user_points_ledger'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    source_type = db.Column(db.String(50), nullable=False, default='quotation')
    source_id = db.Column(db.Integer, nullable=True)
    points = db.Column(db.Integer, nullable=False, default=0)
    memo = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'source_type', 'source_id', 'year', name='uq_user_points_source_year'),
        db.Index('ix_user_points_year', 'user_id', 'year'),
    )

    def __repr__(self):
        return f'<UserPointsLedger user={self.user_id} src={self.source_type}:{self.source_id} pts={self.points}>'
