from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey, String
from sqlalchemy.orm import relationship


class RoleExpenseBudget(db.Model):
    """角色级别费用预算配置（默认值）"""
    __tablename__ = 'role_expense_budgets'

    id = Column(Integer, primary_key=True)
    role_code = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)

    # 各类预算 - 与用户预算字段对应
    total_budget = Column(Numeric(15, 2), default=0)
    entertainment_budget = Column(Numeric(15, 2), default=0, comment='招待费预算')
    travel_budget = Column(Numeric(15, 2), default=0, comment='差旅费预算')
    transport_budget = Column(Numeric(15, 2), default=0, comment='交通费预算')
    office_budget = Column(Numeric(15, 2), default=0, comment='办公费预算')
    communication_budget = Column(Numeric(15, 2), default=0, comment='通讯费预算')
    other_budget = Column(Numeric(15, 2), default=0, comment='其他费用预算')

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    # 关系
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by], post_update=True)

    __table_args__ = (
        db.UniqueConstraint('role_code', 'year', name='uq_role_expense_budget'),
    )

    def __repr__(self):
        return f'<RoleExpenseBudget {self.role_code} {self.year}>'

    def get_budget_dict(self):
        """获取预算字典"""
        return {
            'total': float(self.total_budget or 0),
            'entertainment': float(self.entertainment_budget or 0),
            'travel': float(self.travel_budget or 0),
            'transport': float(self.transport_budget or 0),
            'office': float(self.office_budget or 0),
            'communication': float(self.communication_budget or 0),
            'other': float(self.other_budget or 0),
        }

    def get_category_budgets(self):
        """获取各科目预算字典（与ExpenseBudget保持一致的接口）"""
        return {
            'entertainment': float(self.entertainment_budget or 0),
            'travel': float(self.travel_budget or 0),
            'transport': float(self.transport_budget or 0),
            'office': float(self.office_budget or 0),
            'communication': float(self.communication_budget or 0),
            'other': float(self.other_budget or 0),
        }


class ExpenseBudget(db.Model):
    """年度报销预算表"""
    __tablename__ = 'expense_budgets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False)

    # 年度总预算（存储元，显示万元时除以10000）
    total_budget = Column(Numeric(15, 2), default=0)

    # 按科目预算（可选细分）
    entertainment_budget = Column(Numeric(15, 2), default=0, comment='招待费预算')
    travel_budget = Column(Numeric(15, 2), default=0, comment='差旅费预算')
    transport_budget = Column(Numeric(15, 2), default=0, comment='交通费预算')
    office_budget = Column(Numeric(15, 2), default=0, comment='办公费预算')
    communication_budget = Column(Numeric(15, 2), default=0, comment='通讯费预算')
    other_budget = Column(Numeric(15, 2), default=0, comment='其他费用预算')

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='expense_budgets')
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by], post_update=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'year', name='uq_expense_budget_user_year'),
    )

    def __repr__(self):
        return f'<ExpenseBudget {self.user_id} {self.year}>'

    @property
    def total_budget_wan(self):
        """获取万元单位的总预算"""
        return float(self.total_budget or 0) / 10000

    def get_category_budgets(self):
        """获取各科目预算字典"""
        return {
            'entertainment': float(self.entertainment_budget or 0),
            'travel': float(self.travel_budget or 0),
            'transport': float(self.transport_budget or 0),
            'office': float(self.office_budget or 0),
            'communication': float(self.communication_budget or 0),
            'other': float(self.other_budget or 0),
        }
