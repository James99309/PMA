from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship


class PerformanceTarget(db.Model):
    """绩效目标表"""
    __tablename__ = 'performance_targets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # 目标值
    implant_amount_target = Column(Numeric(15, 2), default=0)
    sales_amount_target = Column(Numeric(15, 2), default=0)
    new_customers_target = Column(Integer, default=0)
    new_projects_target = Column(Integer, default=0)
    five_star_projects_target = Column(Integer, default=0)
    
    # 显示货币
    display_currency = Column(String(10), default='CNY')
    
    # 创建和更新信息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    
    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='performance_targets')
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by], post_update=True)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'year', 'month', name='uq_performance_target_user_year_month'),
    )


class PerformanceStatistics(db.Model):
    """绩效统计表"""
    __tablename__ = 'performance_statistics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # 实际值
    implant_amount_actual = Column(Numeric(15, 2), default=0)
    sales_amount_actual = Column(Numeric(15, 2), default=0)
    new_customers_actual = Column(Integer, default=0)
    new_projects_actual = Column(Integer, default=0)
    five_star_projects_actual = Column(Integer, default=0)
    
    # 行业统计JSON
    industry_statistics = Column(JSON)
    
    # 创建和更新信息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='performance_statistics')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'year', 'month', name='uq_performance_stats_user_year_month'),
    )


class FiveStarProjectBaseline(db.Model):
    """五星项目基准表"""
    __tablename__ = 'five_star_project_baselines'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    baseline_year = Column(Integer, nullable=False)
    baseline_month = Column(Integer, nullable=False)
    baseline_count = Column(Integer, default=0)
    
    # 创建信息
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='five_star_baselines')
    creator = relationship('User', foreign_keys=[created_by]) 