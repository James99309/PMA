from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, Numeric
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
        return f'<Inventory {self.company.company_name if self.company else "Unknown"} - {self.product.name if self.product else "Unknown"}: {self.quantity}>'

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
        return f'<SettlementDetail {self.product.name if self.product else "Unknown"}: {self.quantity_settled}>'

class PurchaseOrder(db.Model):
    """采购订单表 - 管理从供应商采购的订单"""
    __tablename__ = 'purchase_orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)  # 订单号
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)  # 供应商公司
    order_type = Column(String(20), default='purchase')  # 订单类型 [保留兼容]
    order_date = Column(DateTime, default=func.now())  # 订单日期
    expected_date = Column(DateTime, nullable=True)  # 预期交付日期
    status = Column(String(20), default='draft')  # 状态：draft/pending/approved/rejected/confirmed/producing/tested/shipped/stored/completed/cancelled
    total_amount = Column(db.Numeric(15, 2), default=0)  # 订单总金额
    total_quantity = Column(Integer, default=0)  # 订单总数量
    currency = Column(String(10), default='CNY')  # 币种
    payment_terms = Column(String(100), nullable=True)  # 付款条件
    delivery_address = Column(Text, nullable=True)  # 交付地址
    description = Column(Text, nullable=True)  # 订单说明

    # ========== PO模板扩展字段 ==========
    revision = Column(String(20), nullable=True)  # 版本号 Rev.01
    incoterms = Column(String(20), nullable=True)  # 贸易术语 DDP/FOB/CIF等
    order_category = Column(String(20), nullable=True)  # 订单类别 channel/direct

    # ========== 供应商确认 ==========
    supplier_confirmed = Column(Boolean, default=False)  # 供应商是否确认
    supplier_confirmed_date = Column(DateTime, nullable=True)  # 供应商确认日期
    supplier_confirmed_by = Column(String(100), nullable=True)  # 供应商确认人姓名
    supplier_confirmation_file = Column(String(500), nullable=True)  # 确认回执文件路径
    supplier_confirmation_notes = Column(Text, nullable=True)  # 确认备注
    supplier_signature_url = Column(String(500), nullable=True)  # 供应商签名图片URL

    # ========== 交货信息 ==========
    required_date = Column(DateTime, nullable=True)  # 需求日期（期望交货日期）
    confirmed_date = Column(DateTime, nullable=True)  # 供应商确认的交货日期
    ship_to = Column(Text, nullable=True)  # 交货地点详细地址
    shipping_method = Column(String(50), nullable=True)  # 运输方式：truck/air/express/self_pickup
    freight_terms = Column(String(20), nullable=True)  # 运费承担：supplier/buyer

    # ========== 测试配置 ==========
    verification_test_type = Column(String(20), nullable=True)  # 验证测试方式：site_fat/incoming
    factory_test_status = Column(String(20), default='pending')  # 工厂测试状态：pending/passed/failed
    verification_test_status = Column(String(20), default='pending')  # 验证测试状态：pending/passed/failed/not_required

    # ========== 项目关联（可选）==========
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)  # 关联项目
    sales_order_id = Column(Integer, nullable=True)  # 关联客户订单（延迟外键，避免循环依赖）

    # ========== 生产进度跟踪 ==========
    production_status = Column(String(20), default='not_started')  # 生产状态：not_started/preparing/producing/testing/packaging/ready
    production_progress = Column(Integer, default=0)  # 生产进度百分比 0-100
    production_notes = Column(Text, nullable=True)  # 生产备注
    estimated_completion_date = Column(DateTime, nullable=True)  # 预计完成日期

    # ========== 物流信息 ==========
    carrier = Column(String(100), nullable=True)  # 承运商
    tracking_number = Column(String(100), nullable=True)  # 运单号
    ship_date = Column(DateTime, nullable=True)  # 发货日期
    arrival_date = Column(DateTime, nullable=True)  # 预计到达日期
    actual_arrival_date = Column(DateTime, nullable=True)  # 实际到达日期

    # ========== 验收信息 ==========
    acceptance_status = Column(String(20), default='pending')  # 验收状态：pending/passed/failed/conditional
    acceptance_date = Column(DateTime, nullable=True)  # 验收日期
    acceptance_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 验收人
    acceptance_notes = Column(Text, nullable=True)  # 验收备注
    acceptance_documents = Column(Text, nullable=True)  # 验收文档 JSON

    # ========== 交期计划（供应链创建PO时设定）==========
    milestone_test_complete_date = Column(DateTime, nullable=True)  # 测试完成目标日期
    milestone_ship_date = Column(DateTime, nullable=True)  # 计划发货日期
    # confirmed_date 已存在，作为总交期

    # 交期锁定（供应商确认后锁定）
    delivery_schedule_locked = Column(Boolean, default=False)
    delivery_schedule_locked_at = Column(DateTime, nullable=True)

    # ========== 超期状态 ==========
    is_overdue = Column(Boolean, default=False)
    overdue_days = Column(Integer, default=0)
    overdue_milestone = Column(String(50), nullable=True)  # 哪个节点超期：test_complete/ship/delivery

    # ========== 阶段推进记录 ==========
    current_stage_started_at = Column(DateTime, nullable=True)
    last_stage_change_at = Column(DateTime, nullable=True)
    last_stage_change_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # ========== 测试条件扩展 ==========
    factory_test_report_url = Column(String(500), nullable=True)  # 测试报告URL
    factory_test_signed_at = Column(DateTime, nullable=True)  # 签证确认时间
    fat_completed = Column(Boolean, default=False)  # FAT是否完成
    fat_completed_at = Column(DateTime, nullable=True)  # FAT完成时间
    fat_completed_by = Column(String(100), nullable=True)  # FAT完成确认人

    # ========== 内部审批 ==========
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)  # 审批意见
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    company = relationship('Company', backref='purchase_orders')
    created_by = relationship('User', foreign_keys=[created_by_id], backref='created_orders')
    approved_by = relationship('User', foreign_keys=[approved_by_id], backref='approved_orders')
    acceptance_by = relationship('User', foreign_keys=[acceptance_by_id], backref='accepted_orders')
    last_stage_change_by = relationship('User', foreign_keys=[last_stage_change_by_id])
    project = relationship('Project', backref='purchase_orders')
    
    def __repr__(self):
        return f'<PurchaseOrder {self.order_number}>'
    
    @property
    def formatted_order_date(self):
        return self.order_date.strftime('%Y-%m-%d') if self.order_date else ''
    
    @property
    def formatted_expected_date(self):
        return self.expected_date.strftime('%Y-%m-%d') if self.expected_date else ''
    
    @property
    def inventory_status(self):
        """计算入库状态"""
        # 只有审核通过的订单才有入库状态
        if self.status not in ['approved', 'confirmed', 'shipped', 'completed']:
            return None  # 未审核通过的订单没有入库状态
        
        if not self.details:
            return 'pending'  # 待入库
        
        total_quantity = sum(detail.quantity for detail in self.details)
        total_received = sum(detail.received_quantity for detail in self.details)
        
        if total_received == 0:
            return 'pending'  # 待入库
        elif total_received >= total_quantity:
            return 'fully_received'  # 全部入库
        else:
            return 'partially_received'  # 部分入库

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
    
    @property
    def inventory_status(self):
        """计算单项入库状态"""
        if self.received_quantity == 0:
            return 'pending'  # 待入库
        elif self.received_quantity >= self.quantity:
            return 'fully_received'  # 全部入库
        else:
            return 'partially_received'  # 部分入库
    
    @property
    def remaining_quantity(self):
        """剩余未入库数量"""
        return max(0, self.quantity - self.received_quantity)


class PurchaseOrderStageHistory(db.Model):
    """采购订单阶段推进历史"""
    __tablename__ = 'purchase_order_stage_history'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)

    # 阶段变更信息
    from_stage = Column(String(30), nullable=True)  # 原阶段
    to_stage = Column(String(30), nullable=False)  # 新阶段
    from_progress = Column(Integer, nullable=True)  # 原进度
    to_progress = Column(Integer, nullable=False)  # 新进度

    # 操作人信息（内部用户或外部人员）
    changed_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    changed_by_external_name = Column(String(100), nullable=True)  # 外部人员姓名
    changed_by_external_token = Column(String(64), nullable=True)  # 关联的外部令牌

    # 变更类型和说明
    change_type = Column(String(30), nullable=False)  # manual/auto/condition_triggered/force
    change_reason = Column(Text, nullable=True)  # 变更原因
    change_notes = Column(Text, nullable=True)  # 备注

    created_at = Column(DateTime, default=func.now())

    # 关系
    order = relationship('PurchaseOrder', backref='stage_history')
    changed_by_user = relationship('User')

    def __repr__(self):
        return f'<PurchaseOrderStageHistory {self.from_stage} -> {self.to_stage}>'


class PurchaseOrderDeliveryChange(db.Model):
    """采购订单交期变更记录（仅供应链可操作）"""
    __tablename__ = 'purchase_order_delivery_changes'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)

    # 变更内容
    field_name = Column(String(50), nullable=False)  # 变更的字段名
    old_value = Column(String(100), nullable=True)  # 原值
    new_value = Column(String(100), nullable=False)  # 新值
    change_reason = Column(Text, nullable=True)  # 变更原因

    # 操作人
    changed_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # 关系
    order = relationship('PurchaseOrder', backref='delivery_changes')
    changed_by = relationship('User')

    def __repr__(self):
        return f'<PurchaseOrderDeliveryChange {self.field_name}: {self.old_value} -> {self.new_value}>'