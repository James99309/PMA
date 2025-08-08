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
    customer_id = Column(Integer, ForeignKey('companies.id'), nullable=True)  # 客户（支持不关联模式）
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=True)  # 联系人（支持不关联模式）
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)  # 项目（可选）
    # 移除action_id，因为明细表中会有具体的描述
    
    # 货币和汇总金额（从明细表计算得出）
    currency = Column(String(10), default='CNY', nullable=False)  # 货币类型
    total_amount = Column(Float, nullable=False, default=0.0)  # 报销总金额
    
    # 审批状态
    status = Column(String(20), default='draft', nullable=False)  # draft, pending, approved, rejected
    
    # 锁定状态
    is_locked = Column(Boolean, default=False, nullable=False)  # 锁定状态，草稿状态下默认未锁定
    
    # 审批信息
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # 审批人
    approved_at = Column(DateTime, nullable=True)  # 审批时间
    approval_notes = Column(Text)  # 审批备注
    
    # 支付相关字段
    payment_status = Column(String(20), default='unpaid', nullable=False)  # unpaid, awaiting, paid
    payment_amount = Column(Float, nullable=True)  # 实际支付金额
    payment_date = Column(DateTime, nullable=True)  # 支付日期
    payment_method = Column(String(50), nullable=True)  # 支付方式
    payment_reference = Column(String(100), nullable=True)  # 支付凭证号
    payment_notes = Column(Text)  # 支付备注
    paid_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # 支付操作人
    
    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 申请人
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)
    
    # 关系定义
    customer = relationship('Company', backref='expenses')
    contact = relationship('Contact', backref='expenses')
    project = relationship('Project', backref='expenses')
    owner = relationship('User', foreign_keys=[owner_id], backref='owned_expenses')
    approver = relationship('User', foreign_keys=[approved_by])
    payer = relationship('User', foreign_keys=[paid_by], backref='paid_expenses')
    
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
        from app.utils.dictionary_helpers import get_currency_symbol
        symbol = get_currency_symbol(self.currency)
        return f'{symbol}{self.total_amount:,.2f}'
    
    def calculate_total_amount(self):
        """计算总金额（从明细表汇总当前金额）"""
        total = sum(detail.current_amount for detail in self.details)
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
    
    # 货币和金额字段
    currency = Column(String(10), default='CNY', nullable=False)  # 发票货币类型
    invoice_amount = Column(Float, nullable=False, default=0.0)  # 发票金额（原始货币）
    current_amount = Column(Float, nullable=False, default=0.0)  # 当前金额（报销单货币）
    exchange_rate = Column(Float, default=1.0, nullable=False)  # 汇率（发票货币→报销单货币）
    
    # 向后兼容：保留原有的amount字段（数据库实际字段）
    amount = Column(Float, nullable=False, default=0.0)  # 向后兼容的金额字段
    
    # 发票图片字段 - 支持多张图片，使用JSON数组存储
    invoice_images = Column(Text)  # JSON格式：[{"filename": "xxx.jpg", "url": "http://...", "size": 123456}]
    
    # 明细状态
    status = Column(String(20), default='draft', nullable=False)  # draft, pending, approved, rejected
    
    # 系统字段
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    
    def __repr__(self):
        return f'<ExpenseDetail {self.id}: {self.description}>'
    
    @property
    def formatted_amount(self):
        """格式化当前金额显示（报销单货币）"""
        if hasattr(self, 'expense') and self.expense:
            from app.utils.dictionary_helpers import get_currency_symbol
            symbol = get_currency_symbol(self.expense.currency)
            return f'{symbol}{self.current_amount:,.2f}'
        return f'¥{self.current_amount:,.2f}'
    
    @property
    def formatted_invoice_amount(self):
        """格式化发票金额显示（发票货币）"""
        from app.utils.dictionary_helpers import get_currency_symbol
        symbol = get_currency_symbol(self.currency)
        return f'{symbol}{self.invoice_amount:,.2f}'
    
    @property
    def formatted_expense_date(self):
        """格式化发生日期"""
        try:
            return self.expense_date.strftime('%Y-%m-%d') if self.expense_date else ''
        except (AttributeError, ValueError):
            return ''
    
    @property
    def formatted_exchange_rate(self):
        """格式化汇率显示"""
        if self.exchange_rate == 1.0:
            return '1:1'
        return f'{self.exchange_rate:.4f}'
    
    @property
    def invoice_images_list(self):
        """获取发票图片列表"""
        import json
        try:
            if self.invoice_images:
                return json.loads(self.invoice_images)
            return []
        except (json.JSONDecodeError, TypeError):
            return []
    
    @property
    def invoice_count(self):
        """获取发票图片数量"""
        return len(self.invoice_images_list)
    
    def add_invoice_image(self, filename, url, size):
        """添加发票图片"""
        import json
        images = self.invoice_images_list
        images.append({
            'filename': filename,
            'url': url,
            'size': size,
            'uploaded_at': get_local_time().isoformat()
        })
        self.invoice_images = json.dumps(images)
    
    def remove_invoice_image(self, index):
        """移除指定索引的发票图片"""
        import json
        images = self.invoice_images_list
        if 0 <= index < len(images):
            images.pop(index)
            self.invoice_images = json.dumps(images) if images else None
    
    def update_currency_amount(self, new_currency, new_invoice_amount=None):
        """更新货币和金额
        
        Args:
            new_currency: 新的发票货币
            new_invoice_amount: 新的发票金额（可选）
        """
        if new_invoice_amount is not None:
            self.invoice_amount = new_invoice_amount
        
        # 如果货币改变，需要重新计算当前金额
        if new_currency != self.currency:
            self.currency = new_currency
            self._recalculate_current_amount()
    
    def _recalculate_current_amount(self):
        """重新计算当前金额（发票货币转报销单货币）"""
        if not hasattr(self, 'expense') or not self.expense:
            # 如果没有关联的报销单，默认使用1:1汇率
            self.current_amount = self.invoice_amount
            self.exchange_rate = 1.0
            return
        
        from_currency = self.currency
        to_currency = self.expense.currency
        
        if from_currency == to_currency:
            # 同一货币，直接使用发票金额
            self.current_amount = self.invoice_amount
            self.exchange_rate = 1.0
        else:
            # 不同货币，需要转换
            try:
                from app.services.exchange_rate_service import ExchangeRateService
                exchange_service = ExchangeRateService()
                
                # 获取汇率并转换金额
                rate = exchange_service.get_exchange_rate(from_currency, to_currency)
                self.exchange_rate = rate
                self.current_amount = self.invoice_amount * rate
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"货币转换失败 {from_currency} -> {to_currency}: {e}")
                
                # 转换失败时使用1:1汇率
                self.current_amount = self.invoice_amount
                self.exchange_rate = 1.0

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