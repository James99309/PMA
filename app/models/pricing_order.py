from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum


class PricingOrderStatus(enum.Enum):
    """批价单状态枚举"""
    DRAFT = 'draft'           # 草稿
    PENDING = 'pending'       # 审批中
    APPROVED = 'approved'     # 已批准
    REJECTED = 'rejected'     # 已拒绝


class PricingOrderApprovalFlowType(enum.Enum):
    """批价单审批流程类型枚举"""
    CHANNEL_FOLLOW = 'channel_follow'      # 渠道跟进类
    SALES_KEY = 'sales_key'               # 销售重点类  
    SALES_OPPORTUNITY = 'sales_opportunity' # 销售机会类


class SettlementOrderStatus(enum.Enum):
    """结算单状态枚举"""
    DRAFT = 'draft'           # 草稿
    PENDING = 'pending'       # 审批中
    APPROVED = 'approved'     # 已批准
    REJECTED = 'rejected'     # 已拒绝


class PricingOrder(db.Model):
    """批价单主表（面向经销商）"""
    __tablename__ = 'pricing_orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(64), unique=True, nullable=False, comment='批价单号')
    
    # 关联项目和报价单
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    quotation_id = Column(Integer, ForeignKey('quotations.id'), nullable=False, comment='报价单ID')
    
    # 客户信息（经销商为主，分销商为辅）
    dealer_id = Column(Integer, ForeignKey('companies.id'), nullable=True, comment='经销商ID')
    distributor_id = Column(Integer, ForeignKey('companies.id'), nullable=True, comment='分销商ID')
    
    # 新增字段：厂商直签和厂家提货
    is_direct_contract = Column(Boolean, default=False, comment='厂商直签')
    is_factory_pickup = Column(Boolean, default=False, comment='厂家提货')
    
    # 审批流程信息
    approval_flow_type = Column(String(32), nullable=False, comment='审批流程类型')
    status = Column(String(20), default='draft', comment='批价单状态')
    current_approval_step = Column(Integer, default=0, comment='当前审批步骤')
    
    # 金额信息
    pricing_total_amount = Column(Float, default=0.0, comment='批价单总金额')
    pricing_total_discount_rate = Column(Float, default=1.0, comment='批价单总折扣率')
    settlement_total_amount = Column(Float, default=0.0, comment='结算单总金额')
    settlement_total_discount_rate = Column(Float, default=1.0, comment='结算单总折扣率')
    
    # 审批相关
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='最终批准人')
    approved_at = Column(DateTime, nullable=True, comment='批准时间')
    
    # 基础信息
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系定义
    project = relationship('Project', backref='pricing_orders')
    quotation = relationship('Quotation', backref='pricing_orders')
    dealer = relationship('Company', foreign_keys=[dealer_id], backref='dealer_pricing_orders')
    distributor = relationship('Company', foreign_keys=[distributor_id], backref='distributor_pricing_orders')
    creator = relationship('User', foreign_keys=[created_by], backref='created_pricing_orders')
    approver = relationship('User', foreign_keys=[approved_by], backref='approved_pricing_orders')
    
    # 明细和审批记录关系
    pricing_details = relationship('PricingOrderDetail', backref='pricing_order', cascade='all, delete-orphan', order_by='PricingOrderDetail.id')
    settlement_details = relationship('SettlementOrderDetail', backref='pricing_order', cascade='all, delete-orphan', order_by='SettlementOrderDetail.id')
    approval_records = relationship('PricingOrderApprovalRecord', backref='pricing_order', cascade='all, delete-orphan')
    # 结算单关系（一对一或一对多关系）
    settlement_orders = relationship('SettlementOrder', backref='pricing_order_ref', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
    
    @staticmethod
    def generate_order_number():
        """生成批价单号"""
        today = datetime.now()
        prefix = f"PO{today.strftime('%Y%m')}"
        
        # 查找当月最大序号
        latest_order = PricingOrder.query.filter(
            PricingOrder.order_number.like(f"{prefix}%")
        ).order_by(PricingOrder.order_number.desc()).first()
        
        if latest_order:
            latest_num = int(latest_order.order_number[-3:])
            new_num = latest_num + 1
        else:
            new_num = 1
            
        return f"{prefix}-{new_num:03d}"
    
    def calculate_pricing_totals(self, recalculate_discount_rate=True):
        """计算批价单总金额
        
        Args:
            recalculate_discount_rate: 是否重新计算总折扣率，默认True
                                     当用户手动设置总折扣率时应传入False
        """
        total_amount = sum(detail.total_price for detail in self.pricing_details)
        total_market_amount = sum(detail.market_price * detail.quantity for detail in self.pricing_details)
        
        self.pricing_total_amount = total_amount
        
        # 只有在需要重新计算时才更新总折扣率
        if recalculate_discount_rate and total_market_amount > 0:
            self.pricing_total_discount_rate = total_amount / total_market_amount
    
    def calculate_settlement_totals(self, recalculate_discount_rate=True):
        """计算结算单总金额
        
        Args:
            recalculate_discount_rate: 是否重新计算总折扣率，默认True
                                     当用户手动设置总折扣率时应传入False
        """
        total_amount = sum(detail.total_price for detail in self.settlement_details)
        total_market_amount = sum(detail.market_price * detail.quantity for detail in self.settlement_details)
        
        self.settlement_total_amount = total_amount
        
        # 只有在需要重新计算时才更新总折扣率
        if recalculate_discount_rate and total_market_amount > 0:
            self.settlement_total_discount_rate = total_amount / total_market_amount
    
    @property
    def formatted_pricing_total_amount(self):
        """格式化的批价单总金额"""
        return f"{self.pricing_total_amount or 0:,.2f}"
    
    @property
    def formatted_settlement_total_amount(self):
        """格式化的结算单总金额"""
        return f"{self.settlement_total_amount or 0:,.2f}"
    
    @property
    def pricing_discount_percentage(self):
        """批价单折扣率百分比"""
        return round((self.pricing_total_discount_rate or 1.0) * 100, 2)
    
    @property
    def settlement_discount_percentage(self):
        """结算单折扣率百分比"""
        return round((self.settlement_total_discount_rate or 1.0) * 100, 2)
    
    @property
    def status_label(self):
        """状态标签"""
        status_map = {
            'draft': {'zh': '草稿', 'color': '#6c757d'},
            'pending': {'zh': '审批中', 'color': '#ffc107'},
            'approved': {'zh': '已批准', 'color': '#28a745'},
            'rejected': {'zh': '已拒绝', 'color': '#dc3545'},
        }
        return status_map.get(self.status, {'zh': '未知', 'color': '#6c757d'})
    
    @property
    def flow_type_label(self):
        """流程类型标签"""
        type_map = {
            'channel_follow': '渠道跟进类',
            'sales_key': '销售重点类',
            'sales_opportunity': '销售机会类',
        }
        return type_map.get(self.approval_flow_type, '未知类型')


class SettlementOrder(db.Model):
    """结算单主表（面向分销商）"""
    __tablename__ = 'settlement_orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(64), unique=True, nullable=False, comment='结算单号')
    
    # 关联批价单
    pricing_order_id = Column(Integer, ForeignKey('pricing_orders.id'), nullable=False, comment='关联批价单ID')
    
    # 项目和报价单信息（冗余存储便于查询）
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    quotation_id = Column(Integer, ForeignKey('quotations.id'), nullable=False, comment='报价单ID')
    
    # 分销商信息（结算单主要面向分销商）
    distributor_id = Column(Integer, ForeignKey('companies.id'), nullable=False, comment='分销商ID')
    dealer_id = Column(Integer, ForeignKey('companies.id'), nullable=True, comment='经销商ID（辅助信息）')
    
    # 结算信息
    total_amount = Column(Float, default=0.0, comment='结算总金额')
    total_discount_rate = Column(Float, default=1.0, comment='结算总折扣率')
    
    # 状态信息
    status = Column(String(20), default='draft', comment='结算单状态')
    
    # 审批相关
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='批准人')
    approved_at = Column(DateTime, nullable=True, comment='批准时间')
    
    # 基础信息
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系定义
    project = relationship('Project', backref='settlement_orders')
    quotation = relationship('Quotation', backref='settlement_orders')
    distributor = relationship('Company', foreign_keys=[distributor_id], backref='distributor_settlement_orders')
    dealer = relationship('Company', foreign_keys=[dealer_id], backref='dealer_settlement_orders')
    creator = relationship('User', foreign_keys=[created_by], backref='created_settlement_orders')
    approver = relationship('User', foreign_keys=[approved_by], backref='approved_settlement_orders')
    
    # 明细关系
    details = relationship('SettlementOrderDetail', backref='settlement_order', cascade='all, delete-orphan', order_by='SettlementOrderDetail.id')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
    
    @staticmethod
    def generate_order_number():
        """生成结算单号"""
        today = datetime.now()
        prefix = f"SO{today.strftime('%Y%m')}"
        
        # 查找当月最大序号
        latest_order = SettlementOrder.query.filter(
            SettlementOrder.order_number.like(f"{prefix}%")
        ).order_by(SettlementOrder.order_number.desc()).first()
        
        if latest_order:
            latest_num = int(latest_order.order_number[-3:])
            new_num = latest_num + 1
        else:
            new_num = 1
            
        return f"{prefix}-{new_num:03d}"
    
    def calculate_totals(self):
        """计算结算单总金额"""
        total_amount = sum(detail.total_price for detail in self.details)
        total_market_amount = sum(detail.market_price * detail.quantity for detail in self.details)
        
        self.total_amount = total_amount
        if total_market_amount > 0:
            self.total_discount_rate = total_amount / total_market_amount
    
    @property
    def formatted_total_amount(self):
        """格式化的总金额"""
        return f"{self.total_amount or 0:,.2f}"
    
    @property
    def discount_percentage(self):
        """折扣率百分比"""
        return round((self.total_discount_rate or 1.0) * 100, 2)
    
    @property
    def status_label(self):
        """状态标签"""
        status_map = {
            'draft': {'zh': '草稿', 'color': '#6c757d'},
            'pending': {'zh': '审批中', 'color': '#ffc107'},
            'approved': {'zh': '已批准', 'color': '#28a745'},
            'rejected': {'zh': '已拒绝', 'color': '#dc3545'},
        }
        return status_map.get(self.status, {'zh': '未知', 'color': '#6c757d'})


class PricingOrderDetail(db.Model):
    """批价单明细表"""
    __tablename__ = 'pricing_order_details'
    
    id = Column(Integer, primary_key=True)
    pricing_order_id = Column(Integer, ForeignKey('pricing_orders.id'), nullable=False, comment='批价单ID')
    
    # 产品信息
    product_name = Column(String(255), nullable=False, comment='产品名称')
    product_model = Column(String(128), nullable=True, comment='产品型号')
    product_desc = Column(Text, nullable=True, comment='产品描述')
    brand = Column(String(64), nullable=True, comment='品牌')
    unit = Column(String(16), nullable=True, comment='单位')
    product_mn = Column(String(64), nullable=True, comment='产品MN编码')
    
    # 价格和数量
    market_price = Column(Float, nullable=False, comment='市场价')
    unit_price = Column(Float, nullable=False, comment='单价')
    quantity = Column(Integer, nullable=False, comment='数量')
    discount_rate = Column(Float, default=1.0, comment='折扣率')
    total_price = Column(Float, nullable=False, comment='小计金额')
    
    # 数据来源
    source_type = Column(String(32), default='quotation', comment='数据来源：quotation/manual')
    source_quotation_detail_id = Column(Integer, nullable=True, comment='来源报价单明细ID')
    
    def calculate_prices(self):
        """计算价格"""
        self.unit_price = self.market_price * self.discount_rate
        self.total_price = self.unit_price * self.quantity
    
    @property
    def is_deletable(self):
        """是否可删除（允许删除所有品牌的产品）"""
        return True


class SettlementOrderDetail(db.Model):
    """结算单明细表"""
    __tablename__ = 'settlement_order_details'
    
    id = Column(Integer, primary_key=True)
    pricing_order_id = Column(Integer, ForeignKey('pricing_orders.id'), nullable=False, comment='批价单ID')
    settlement_order_id = Column(Integer, ForeignKey('settlement_orders.id'), nullable=True, comment='结算单ID')
    
    # 产品信息（从批价单同步）
    product_name = Column(String(255), nullable=False, comment='产品名称')
    product_model = Column(String(128), nullable=True, comment='产品型号')
    product_desc = Column(Text, nullable=True, comment='产品描述')
    brand = Column(String(64), nullable=True, comment='品牌')
    unit = Column(String(16), nullable=True, comment='单位')
    product_mn = Column(String(64), nullable=True, comment='产品MN编码')
    
    # 价格和数量
    market_price = Column(Float, nullable=False, comment='市场价')
    unit_price = Column(Float, nullable=False, comment='单价')
    quantity = Column(Integer, nullable=False, comment='数量')
    discount_rate = Column(Float, default=1.0, comment='折扣率')
    total_price = Column(Float, nullable=False, comment='小计金额')
    
    # 关联批价单明细
    pricing_detail_id = Column(Integer, ForeignKey('pricing_order_details.id'), nullable=False, comment='关联批价单明细ID')
    
    # 结算相关字段
    settlement_company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, comment='结算目标公司ID')
    settlement_status = Column(String(20), default='draft', comment='结算状态: draft, pending, settled')
    settlement_date = Column(DateTime, nullable=True, comment='结算完成时间')
    settlement_notes = Column(Text, nullable=True, comment='结算备注')
    
    # 关系
    pricing_detail = relationship('PricingOrderDetail', backref='settlement_details')
    settlement_company = relationship('Company', foreign_keys=[settlement_company_id], backref='settlement_details')
    
    def calculate_prices(self):
        """计算价格"""
        self.unit_price = self.market_price * self.discount_rate
        self.total_price = self.unit_price * self.quantity
    
    @property
    def is_settled(self):
        """是否已结算"""
        return self.settlement_status == 'settled'
    
    @property
    def settlement_status_label(self):
        """结算状态标签"""
        status_map = {
            'draft': {'zh': '草稿', 'color': '#6c757d'},
            'pending': {'zh': '待结算', 'color': '#ffc107'},
            'settled': {'zh': '已结算', 'color': '#28a745'},
        }
        return status_map.get(self.settlement_status, {'zh': '未知', 'color': '#6c757d'})


class PricingOrderApprovalRecord(db.Model):
    """批价单审批记录表"""
    __tablename__ = 'pricing_order_approval_records'
    
    id = Column(Integer, primary_key=True)
    pricing_order_id = Column(Integer, ForeignKey('pricing_orders.id'), nullable=False, comment='批价单ID')
    
    # 审批步骤信息
    step_order = Column(Integer, nullable=False, comment='审批步骤顺序')
    step_name = Column(String(64), nullable=False, comment='审批步骤名称')
    approver_role = Column(String(64), nullable=False, comment='审批人角色')
    approver_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='审批人ID')
    
    # 审批结果
    action = Column(String(16), nullable=True, comment='审批动作：approve/reject')
    comment = Column(Text, nullable=True, comment='审批意见')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')
    
    # 快速通过标识
    is_fast_approval = Column(Boolean, default=False, comment='是否快速通过')
    fast_approval_reason = Column(String(255), nullable=True, comment='快速通过原因')
    
    # 关系
    approver = relationship('User', backref='pricing_approval_records')
    
    @property
    def status_display(self):
        """状态显示"""
        if not self.action:
            return '待审批'
        elif self.action == 'approve':
            return '✅ 通过'
        elif self.action == 'reject':
            return '❌ 拒绝'
        return '未知'
    
    @property
    def formatted_approved_at(self):
        """格式化审批时间"""
        if self.approved_at:
            return self.approved_at.strftime('%Y-%m-%d %H:%M:%S')
        return '' 