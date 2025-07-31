from app import db
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import event, Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, Date
from sqlalchemy.orm import relationship

def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)

def generate_expense_number():
    """生成报销单编号：BX + 年月日 + 2位序号"""
    from datetime import datetime
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    
    # 查询当天最大的序号
    latest_expense = Expense.query.filter(
        Expense.expense_number.like(f'BX{date_str}%')
    ).order_by(Expense.id.desc()).first()
    
    if latest_expense:
        try:
            # 提取最后2位数字并加1
            sequence_num = int(latest_expense.expense_number[-2:]) + 1
        except (ValueError, IndexError):
            sequence_num = 1
    else:
        sequence_num = 1
    
    return f'BX{date_str}{sequence_num:02d}'

class Expense(db.Model):
    """报销单主表模型"""
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    expense_number = Column(String(20), unique=True, nullable=False, index=True)  # 报销单编号
    title = Column(String(200), nullable=False)  # 报销主题/标题
    description = Column(Text)  # 报销说明
    
    # 关联信息
    customer_id = Column(Integer, ForeignKey('companies.id'), nullable=False)  # 客户（必须）
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)  # 项目（可选）
    # 移除action_id，因为明细表中会有具体的描述
    
    # 汇总金额（从明细表计算得出）
    total_amount = Column(Float, nullable=False, default=0.0)  # 报销总金额
    
    # 审批状态
    status = Column(String(20), default='draft', nullable=False)  # draft, pending, approved, rejected
    
    # 锁定状态
    is_locked = Column(Boolean, default=False, nullable=False)  # 锁定状态，草稿状态下默认未锁定
    
    # 审批信息
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # 审批人
    approved_at = Column(DateTime, nullable=True)  # 审批时间
    approval_notes = Column(Text)  # 审批备注
    
    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 申请人
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)
    
    # 关系定义
    customer = relationship('Company', backref='expenses')
    project = relationship('Project', backref='expenses')
    owner = relationship('User', foreign_keys=[owner_id], backref='owned_expenses')
    approver = relationship('User', foreign_keys=[approved_by])
    
    # 一对多关系：报销单明细
    details = relationship('ExpenseDetail', backref='expense', cascade='all, delete-orphan', 
                          order_by='ExpenseDetail.expense_date, ExpenseDetail.id')
    
    def __init__(self, **kwargs):
        if 'expense_number' not in kwargs:
            kwargs['expense_number'] = generate_expense_number()
        super(Expense, self).__init__(**kwargs)
    
    def __repr__(self):
        return f'<Expense {self.expense_number}>'
    
    @property
    def formatted_total_amount(self):
        """格式化总金额显示"""
        return f'¥{self.total_amount:,.2f}'
    
    def calculate_total_amount(self):
        """计算总金额（从明细表汇总）"""
        total = sum(detail.amount for detail in self.details)
        self.total_amount = total
        return total
    
    @property
    def detail_count(self):
        """获取明细数量"""
        return len(self.details)
    
    @property
    def formatted_approved_at(self):
        """格式化审批时间"""
        try:
            return self.approved_at.strftime('%Y-%m-%d %H:%M') if self.approved_at else ''
        except (AttributeError, ValueError):
            return ''

class ExpenseDetail(db.Model):
    """报销单明细表模型"""
    __tablename__ = 'expense_details'
    
    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey('expenses.id'), nullable=False)  # 报销单ID
    
    # 明细信息
    expense_date = Column(Date, nullable=False)  # 发生日期
    expense_category = Column(String(50), nullable=False)  # 报销科目
    description = Column(Text, nullable=False)  # 明细描述
    document_count = Column(Integer, default=1)  # 单据数量
    amount = Column(Float, nullable=False)  # 金额
    
    # 明细状态
    status = Column(String(20), default='draft', nullable=False)  # draft, pending, approved, rejected
    
    # 系统字段
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    
    def __repr__(self):
        return f'<ExpenseDetail {self.id}: {self.description}>'
    
    @property
    def formatted_amount(self):
        """格式化金额显示"""
        return f'¥{self.amount:,.2f}'
    
    @property
    def formatted_expense_date(self):
        """格式化发生日期"""
        try:
            return self.expense_date.strftime('%Y-%m-%d') if self.expense_date else ''
        except (AttributeError, ValueError):
            return ''

class Department(db.Model):
    """部门模型"""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)  # 部门名称
    code = Column(String(20), nullable=False, unique=True)  # 部门代码
    parent_id = Column(Integer, ForeignKey('departments.id'), nullable=True)  # 上级部门
    manager_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 部门经理
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    
    # 关系定义
    parent = relationship('Department', remote_side=[id], backref='children')
    manager = relationship('User', backref='managed_departments')
    
    def __repr__(self):
        return f'<Department {self.name}>'

# 报销科目配置
EXPENSE_CATEGORIES = [
    ('entertainment', '招待费'),
    ('local_transport', '市内交通'),
    ('travel_accommodation', '差旅住宿'),
    ('office_supplies', '办公用品'),
    ('communication', '通讯费'),
    ('fuel', '油费'),
    ('parking', '停车费'),
    ('meals', '餐费'),
    ('other', '其他')
]

# 报销状态配置
EXPENSE_STATUS = [
    ('draft', '草稿'),
    ('pending', '待审批'),
    ('approved', '已通过'),
    ('rejected', '已驳回')
]

# 添加SQLAlchemy事件监听器，在明细变化时自动更新主表总额
@event.listens_for(ExpenseDetail, 'after_insert')
@event.listens_for(ExpenseDetail, 'after_update')
@event.listens_for(ExpenseDetail, 'after_delete')
def update_expense_total_amount(mapper, connection, target):
    """明细变化时自动更新报销单总金额"""
    try:
        expense_id = target.expense_id
        if expense_id:
            from sqlalchemy import text
            # 计算该报销单的总金额
            result = connection.execute(text("""
                SELECT COALESCE(SUM(amount), 0.0) 
                FROM expense_details 
                WHERE expense_id = :expense_id
            """), {"expense_id": expense_id})
            
            total_amount = result.scalar() or 0.0
            
            # 更新主表的总金额和更新时间
            connection.execute(text("""
                UPDATE expenses 
                SET total_amount = :total_amount,
                    updated_at = :now
                WHERE id = :expense_id
            """), {
                "expense_id": expense_id, 
                "total_amount": total_amount,
                "now": get_local_time()
            })
    except Exception as e:
        print(f"更新报销单总金额时发生错误: {str(e)}")