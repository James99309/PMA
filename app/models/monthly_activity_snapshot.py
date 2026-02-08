"""月度活跃度快照模型

保存每月客户/项目活跃度历史数据，用于绩效趋势图展示真实历史值。
"""

from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint, Index


class MonthlyActivitySnapshot(db.Model):
    """月度活跃度快照 - 保存每月客户/项目活跃度历史数据"""
    __tablename__ = 'monthly_activity_snapshots'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12

    # 客户活跃度
    customer_total = Column(Integer, default=0)
    customer_highly_active = Column(Integer, default=0)
    customer_active = Column(Integer, default=0)
    customer_normal = Column(Integer, default=0)
    customer_to_follow = Column(Integer, default=0)
    customer_dormant = Column(Integer, default=0)
    customer_churned = Column(Integer, default=0)
    customer_activity_rate = Column(Numeric(10, 4), default=0)

    # 项目活跃度
    project_total = Column(Integer, default=0)
    project_highly_active = Column(Integer, default=0)
    project_active = Column(Integer, default=0)
    project_normal = Column(Integer, default=0)
    project_to_follow = Column(Integer, default=0)
    project_dormant = Column(Integer, default=0)
    project_churned = Column(Integer, default=0)
    project_frozen = Column(Integer, default=0)
    project_activity_rate = Column(Numeric(10, 4), default=0)

    # 元数据
    calculated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'year', 'month', name='uq_monthly_activity_snapshot'),
        Index('idx_activity_snapshot_user_year', 'user_id', 'year'),
    )

    def __repr__(self):
        return f'<MonthlyActivitySnapshot user={self.user_id} {self.year}-{self.month:02d}>'
