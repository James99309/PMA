# -*- coding: utf-8 -*-
"""
客户订单模型
从批价单转换而来，包含物流交付信息
"""
from app import db
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class SalesOrder(db.Model):
    """客户订单表 - 从批价单转换，管理发货和交付"""
    __tablename__ = 'sales_orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)  # SO202501-001

    # 来源关联
    pricing_order_id = Column(Integer, ForeignKey('pricing_orders.id'), nullable=True)  # 来源批价单
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)  # 关联项目
    customer_id = Column(Integer, ForeignKey('companies.id'), nullable=False)  # 客户公司

    # 交付信息
    delivery_date = Column(DateTime, nullable=True)  # 期望交付日期
    delivery_address = Column(Text, nullable=True)  # 交付地址
    delivery_contact = Column(String(100), nullable=True)  # 收货联系人
    delivery_phone = Column(String(50), nullable=True)  # 收货电话
    delivery_email = Column(String(100), nullable=True)  # 收货邮箱

    # 物流配置
    shipping_method = Column(String(50), nullable=True)  # 运输方式：truck/air/express/self_pickup
    freight_terms = Column(String(20), nullable=True)  # 运费承担：seller/buyer
    incoterms = Column(String(20), nullable=True)  # 贸易术语：DDP/FOB/CIF等

    # 实际物流信息
    carrier = Column(String(100), nullable=True)  # 承运商
    tracking_number = Column(String(100), nullable=True)  # 主运单号
    ship_date = Column(DateTime, nullable=True)  # 发货日期
    arrival_date = Column(DateTime, nullable=True)  # 预计到达日期
    actual_arrival_date = Column(DateTime, nullable=True)  # 实际到达日期

    # 签收信息
    received_by = Column(String(100), nullable=True)  # 签收人
    received_date = Column(DateTime, nullable=True)  # 签收日期
    received_documents = Column(Text, nullable=True)  # 签收凭证 JSON

    # 金额信息
    total_amount = Column(Numeric(15, 2), default=0)  # 订单总金额
    total_quantity = Column(Integer, default=0)  # 订单总数量
    currency = Column(String(10), default='CNY')  # 币种

    # 状态
    status = Column(String(20), default='draft')
    # draft: 草稿
    # confirmed: 已确认
    # preparing: 备货中
    # shipped: 已发货
    # delivered: 已送达
    # completed: 已完成
    # cancelled: 已取消

    notes = Column(Text, nullable=True)  # 备注
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    pricing_order = relationship('PricingOrder', backref='sales_orders')
    project = relationship('Project', backref='sales_orders')
    customer = relationship('Company', backref='customer_sales_orders')
    created_by = relationship('User', backref='created_sales_orders')

    def __repr__(self):
        return f'<SalesOrder {self.order_number}>'

    @property
    def formatted_delivery_date(self):
        return self.delivery_date.strftime('%Y-%m-%d') if self.delivery_date else ''

    @property
    def shipped_quantity(self):
        """已发货数量"""
        return sum(detail.shipped_quantity or 0 for detail in self.details)

    @property
    def received_quantity(self):
        """已签收数量"""
        return sum(detail.received_quantity or 0 for detail in self.details)

    @property
    def delivery_progress(self):
        """交付进度百分比"""
        if self.total_quantity and self.total_quantity > 0:
            return round(self.received_quantity / self.total_quantity * 100, 1)
        return 0


class SalesOrderDetail(db.Model):
    """客户订单明细表"""
    __tablename__ = 'sales_order_details'

    id = Column(Integer, primary_key=True)
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'), nullable=False)
    pricing_detail_id = Column(Integer, ForeignKey('pricing_order_details.id'), nullable=True)  # 来源批价单明细
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)

    # 产品信息（冗余存储）
    product_name = Column(String(200), nullable=False)
    product_model = Column(String(100), nullable=True)
    specification = Column(Text, nullable=True)  # 产品规格

    # 数量和价格
    quantity = Column(Integer, nullable=False)  # 订购数量
    unit = Column(String(20), nullable=True)  # 单位
    unit_price = Column(Numeric(15, 2), default=0)  # 单价
    discount = Column(Numeric(5, 4), default=1.0000)  # 折扣率
    total_price = Column(Numeric(15, 2), default=0)  # 总价

    # 发货和签收状态
    shipped_quantity = Column(Integer, default=0)  # 已发货数量
    received_quantity = Column(Integer, default=0)  # 已签收数量
    status = Column(String(20), default='pending')
    # pending: 待发货
    # partial_shipped: 部分发货
    # shipped: 已发货
    # partial_received: 部分签收
    # received: 已签收

    notes = Column(Text, nullable=True)

    # 关系
    sales_order = relationship('SalesOrder', backref='details')
    pricing_detail = relationship('PricingOrderDetail', backref='sales_order_details')
    product = relationship('Product', backref='sales_order_details')

    def __repr__(self):
        return f'<SalesOrderDetail {self.product_name}: {self.quantity}>'

    @property
    def remaining_to_ship(self):
        """待发货数量"""
        return max(0, self.quantity - (self.shipped_quantity or 0))

    @property
    def remaining_to_receive(self):
        """待签收数量"""
        return max(0, (self.shipped_quantity or 0) - (self.received_quantity or 0))

    @property
    def calculated_total(self):
        """计算总价"""
        if self.unit_price and self.quantity:
            discount = float(self.discount) if self.discount else 1.0
            return float(self.unit_price) * self.quantity * discount
        return 0
