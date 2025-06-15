from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Inventory(db.Model):
    """库存表 - 记录每个公司的产品库存"""
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)  # 关联公司表
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)  # 关联标准产品库
    quantity = Column(Integer, default=0, nullable=False)  # 当前库存数量
    unit = Column(String(20), nullable=True)  # 单位
    location = Column(String(100), nullable=True)  # 存储位置
    min_stock = Column(Integer, default=0)  # 最低库存警戒线
    max_stock = Column(Integer, default=0)  # 最高库存限制
    notes = Column(Text, nullable=True)  # 备注
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 关系
    company = relationship('Company', backref='inventories')
    product = relationship('Product', backref='inventories')
    created_by = relationship('User', backref='created_inventories')
    
    # 索引约束：每个公司的每个产品只能有一条库存记录
    __table_args__ = (
        db.UniqueConstraint('company_id', 'product_id', name='unique_company_product_inventory'),
    )
    
    def __repr__(self):
        return f'<Inventory {self.company.company_name if self.company else "Unknown"} - {self.product.product_name if self.product else "Unknown"}: {self.quantity}>'

class InventoryTransaction(db.Model):
    """库存变动记录表 - 记录所有入库和出库操作"""
    __tablename__ = 'inventory_transactions'
    
    id = Column(Integer, primary_key=True)
    inventory_id = Column(Integer, ForeignKey('inventory.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'in' 入库, 'out' 出库, 'settlement' 结算出库
    quantity = Column(Integer, nullable=False)  # 变动数量（正数入库，负数出库）
    quantity_before = Column(Integer, nullable=False)  # 变动前库存
    quantity_after = Column(Integer, nullable=False)  # 变动后库存
    reference_type = Column(String(50), nullable=True)  # 关联单据类型：'manual', 'settlement', 'order', 'adjustment'
    reference_id = Column(Integer, nullable=True)  # 关联单据ID
    description = Column(Text, nullable=True)  # 变动说明
    transaction_date = Column(DateTime, default=func.now())
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 关系
    inventory = relationship('Inventory', backref='transactions')
    created_by = relationship('User', backref='inventory_transactions')
    
    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type}: {self.quantity}>'

class Settlement(db.Model):
    """结算表 - 记录结算处理"""
    __tablename__ = 'settlements'
    
    id = Column(Integer, primary_key=True)
    settlement_number = Column(String(50), unique=True, nullable=False)  # 结算单号
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)  # 结算公司
    settlement_date = Column(DateTime, default=func.now())  # 结算日期
    status = Column(String(20), default='pending')  # 状态：pending, completed, cancelled
    total_items = Column(Integer, default=0)  # 结算产品总数
    description = Column(Text, nullable=True)  # 结算说明
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    company = relationship('Company', backref='settlements')
    created_by = relationship('User', foreign_keys=[created_by_id], backref='created_settlements')
    approved_by = relationship('User', foreign_keys=[approved_by_id], backref='approved_settlements')
    
    def __repr__(self):
        return f'<Settlement {self.settlement_number}>'
    
    @property
    def formatted_settlement_date(self):
        return self.settlement_date.strftime('%Y-%m-%d %H:%M') if self.settlement_date else ''

class SettlementDetail(db.Model):
    """结算明细表"""
    __tablename__ = 'settlement_details'
    
    id = Column(Integer, primary_key=True)
    settlement_id = Column(Integer, ForeignKey('settlements.id'), nullable=False)
    inventory_id = Column(Integer, ForeignKey('inventory.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)  # 冗余字段，便于查询
    quantity_settled = Column(Integer, nullable=False)  # 结算数量
    quantity_before = Column(Integer, nullable=False)  # 结算前库存
    quantity_after = Column(Integer, nullable=False)  # 结算后库存
    unit = Column(String(20), nullable=True)  # 单位
    notes = Column(Text, nullable=True)  # 备注
    
    # 关系
    settlement = relationship('Settlement', backref='details')
    inventory = relationship('Inventory', backref='settlement_details')
    product = relationship('Product', backref='settlement_details')
    
    def __repr__(self):
        return f'<SettlementDetail {self.product.product_name if self.product else "Unknown"}: {self.quantity_settled}>'

class PurchaseOrder(db.Model):
    """订货单表"""
    __tablename__ = 'purchase_orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)  # 订单号
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)  # 供应商/客户公司
    order_type = Column(String(20), default='purchase')  # 订单类型：purchase 采购, sale 销售 [已废弃，不再使用]
    order_date = Column(DateTime, default=func.now())  # 订单日期
    expected_date = Column(DateTime, nullable=True)  # 预期交付日期
    status = Column(String(20), default='draft')  # 状态：draft 草稿, pending 审批中, approved 审批通过, rejected 审批拒绝, confirmed 已确认, shipped 已发货, completed 已完成, cancelled 已取消
    total_amount = Column(db.Numeric(15, 2), default=0)  # 订单总金额
    total_quantity = Column(Integer, default=0)  # 订单总数量
    currency = Column(String(10), default='CNY')  # 币种
    payment_terms = Column(String(100), nullable=True)  # 付款条件
    delivery_address = Column(Text, nullable=True)  # 交付地址
    description = Column(Text, nullable=True)  # 订单说明
    
    # 注意：订单审批使用通用审批系统，不在此表中存储审批状态
    
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    company = relationship('Company', backref='purchase_orders')
    created_by = relationship('User', foreign_keys=[created_by_id], backref='created_orders')
    approved_by = relationship('User', foreign_keys=[approved_by_id], backref='approved_orders')
    
    def __repr__(self):
        return f'<PurchaseOrder {self.order_number}>'
    
    @property
    def formatted_order_date(self):
        return self.order_date.strftime('%Y-%m-%d') if self.order_date else ''
    
    @property
    def formatted_expected_date(self):
        return self.expected_date.strftime('%Y-%m-%d') if self.expected_date else ''

class PurchaseOrderDetail(db.Model):
    """订货单明细表"""
    __tablename__ = 'purchase_order_details'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_name = Column(String(200), nullable=False)  # 冗余字段
    product_model = Column(String(100), nullable=True)  # 冗余字段
    product_desc = Column(Text, nullable=True)  # 产品描述
    brand = Column(String(100), nullable=True)  # 品牌
    quantity = Column(Integer, nullable=False)  # 数量
    unit = Column(String(20), nullable=True)  # 单位
    unit_price = Column(db.Numeric(15, 2), default=0)  # 单价
    discount = Column(db.Numeric(5, 4), default=1.0000)  # 折扣率 (0.8000 = 80%)
    total_price = Column(db.Numeric(15, 2), default=0)  # 总价
    received_quantity = Column(Integer, default=0)  # 已收货数量
    notes = Column(Text, nullable=True)  # 备注
    
    # 关系
    order = relationship('PurchaseOrder', backref='details')
    product = relationship('Product', backref='order_details')
    
    def __repr__(self):
        return f'<PurchaseOrderDetail {self.product_name}: {self.quantity}>'
    
    @property
    def calculated_total(self):
        """计算总价"""
        if self.unit_price and self.quantity and self.discount:
            return float(self.unit_price) * self.quantity * float(self.discount)
        return 0 