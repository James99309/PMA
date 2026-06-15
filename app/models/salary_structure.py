# -*- coding: utf-8 -*-
"""结构化薪资(2026-06):全局基础薪资结构 + 个人金额/试用期

设计(2026-06-13 用户确认):
- 薪资结构是一套全局模板(不分岗位):主薪资项 + 子项(组成部分),只定项目与发放方式,不含金额
- 主项有子项 → 主项金额 = 各子项之和(汇总);主项无子项 → 主项为叶子,自身可填金额
- 发放方式(月/季/年)由每个「可填金额的叶子项」各自设定
- 固定项(基础薪资 / 绩效薪资)不可删,但个人可不填(= 没有该项)
- 金额全部在个人薪资页填(套用全局结构);个人可加专属项;试用期为个人级开关

仅 admin / ceo / hr_manager 可见可配(SALARY_ADMIN_ROLES)。
"""
from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, Boolean, JSON, ForeignKey, UniqueConstraint

# 薪资模块准入角色(页面/tab/API 统一引用)
SALARY_ADMIN_ROLES = ('admin', 'ceo', 'hr_manager')

# 固定主项(不可删 / 不可改名,可挂子项;个人可不填)
SALARY_LOCKED_ITEMS = [
    {'item_code': 'base_salary',        'item_name': '基础薪资'},
    {'item_code': 'performance_salary', 'item_name': '绩效薪资'},
]
SALARY_LOCKED_CODES = tuple(it['item_code'] for it in SALARY_LOCKED_ITEMS)

SALARY_CYCLES = {'monthly': '月发', 'quarterly': '季发', 'yearly': '年发'}


class SalaryStructureItem(db.Model):
    """全局薪资结构项(主项 / 子项;无金额、无岗位、无年份)"""
    __tablename__ = 'salary_structure_items'

    id = Column(Integer, primary_key=True)
    item_code = Column(String(50), nullable=False, unique=True)
    item_name = Column(String(100), nullable=False)
    parent_code = Column(String(50))                     # null=主项;否则=所属主项 item_code
    pay_cycle = Column(String(10), default='monthly')    # monthly|quarterly|yearly(汇总主项忽略)
    is_locked = Column(Boolean, default=False)           # 固定项(基础/绩效)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    def to_dict(self):
        return {
            'item_code': self.item_code,
            'item_name': self.item_name,
            'parent_code': self.parent_code,
            'pay_cycle': self.pay_cycle or 'monthly',
            'is_locked': bool(self.is_locked),
            'sort_order': self.sort_order or 0,
        }


class UserSalaryItem(db.Model):
    """个人薪资金额:套用全局结构项的金额 + 个人专属项

    item_code 关联全局结构 SalaryStructureItem;is_personal=True 为个人专属项(主项叶子)。
    主子层级、发放方式从全局结构取(专属项自带 pay_cycle/item_name)。
    """
    __tablename__ = 'user_salary_items'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    item_code = Column(String(50), nullable=False)
    item_name = Column(String(100))                      # 个人专属项名;结构项行可空
    category = Column(String(20))                        # 兼容旧列(不再使用)
    pay_cycle = Column(String(10))                       # 个人专属项的发放方式
    amount = Column(Numeric(15, 2))                       # 旧:标准单期金额(已弃用,保留兼容)
    probation_amount = Column(Numeric(15, 2))           # 旧:试用期单期金额(已弃用,保留兼容)
    monthly_amounts = Column(JSON)                       # 月度实发 {"1":x,...,"12":y}
    is_personal = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    __table_args__ = (UniqueConstraint('user_id', 'year', 'item_code', name='uq_user_salary_item'),)

    user = db.relationship('User', foreign_keys=[user_id])


class UserSalaryProfile(db.Model):
    """个人薪资元信息(按年):试用期开关 + 周期。与结构无关。"""
    __tablename__ = 'user_salary_profile'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    is_probation = Column(Boolean, default=False)        # 当前薪资是否按试用期发放
    probation_months = Column(Integer)                   # 旧:试用期周期(月);已弃用,保留兼容
    probation_start = Column(Date)                        # 试用期开始日期
    probation_end = Column(Date)                          # 试用期结束日期
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    __table_args__ = (UniqueConstraint('user_id', 'year', name='uq_user_salary_profile'),)


# 薪资月度审批的审批链(角色,按顺序);用户确认 2026-06-13
SALARY_RUN_APPROVER_ROLES = ['finance_supervisor', 'finace_director', 'ceo']
SALARY_RUN_INITIATOR_ROLES = ('admin', 'hr_manager')


class SalaryRun(db.Model):
    """月度薪资审批批次(按 公司+年+月)。HR 生成当月全员薪资表 → 提交审批 →
    财务主管 → 财务总监 → 总经理。提交即锁定该公司该月个人薪资(召回解锁,通过永久锁)。
    snapshot 固化提交时各人各项当月应发,后续改标准额/结构/考核方法不影响已锁定月份。
    """
    __tablename__ = 'salary_runs'

    id = Column(Integer, primary_key=True)
    company_name = Column(String(200), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)              # 1-12
    status = Column(String(20), default='pending')       # draft|pending|approved|rejected
    is_locked = Column(Boolean, default=False)            # 提交即 True(锁定个人薪资该月);召回/驳回 False
    snapshot = Column(JSON)                               # [{user_id,name,department,role,items:{code:amt},total}]
    total_amount = Column(Numeric(15, 2))                # 批次应发合计(元)
    headcount = Column(Integer)                           # 批次人数
    initiated_by = Column(Integer, ForeignKey('users.id'))
    approval_instance_id = Column(Integer)
    settled_at = Column(DateTime)                         # 终审通过时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint('company_name', 'year', 'month', name='uq_salary_run'),)

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'year': self.year,
            'month': self.month,
            'status': self.status,
            'is_locked': bool(self.is_locked),
            'total_amount': float(self.total_amount) if self.total_amount is not None else 0.0,
            'headcount': self.headcount or 0,
            'snapshot': self.snapshot or [],
            'approval_instance_id': self.approval_instance_id,
            'settled_at': self.settled_at.isoformat() if self.settled_at else None,
        }
