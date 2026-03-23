# -*- coding: utf-8 -*-
"""
发货记录模型
管理客户订单的发货和物流信息
"""
from app import db
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Shipment(db.Model):
    """发货记录表 - 管理发货批次和物流信息"""
    __tablename__ = 'shipments'

    id = Column(Integer, primary_key=True)
    shipment_number = Column(String(50), unique=True, nullable=False)  # SHP202501-001

    # 关联订单
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'), nullable=True)  # 目标客户订单（发给代理商时填写）
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=True)  # 来源采购单

    # 物流信息
    carrier = Column(String(100), nullable=True)  # 承运商
    tracking_number = Column(String(100), nullable=True)  # 主运单号
    shipping_method = Column(String(50), nullable=True)  # 运输方式：truck/air/express/self_pickup
    ship_date = Column(DateTime, nullable=True)  # 发货日期
    expected_arrival = Column(DateTime, nullable=True)  # 预计到达日期
    actual_arrival = Column(DateTime, nullable=True)  # 实际到达日期

    # 运费信息
    freight_cost = Column(Numeric(15, 2), nullable=True)  # 运费
    freight_payer = Column(String(20), nullable=True)  # 运费承担方：seller/buyer
    currency = Column(String(10), default='CNY')  # 币种

    # 发货地址
    ship_from = Column(Text, nullable=True)  # 发货地址
    ship_from_contact = Column(String(100), nullable=True)  # 发货联系人
    ship_from_phone = Column(String(50), nullable=True)  # 发货联系电话

    # 收货地址
    ship_to = Column(Text, nullable=True)  # 收货地址
    contact_name = Column(String(100), nullable=True)  # 收货联系人
    contact_phone = Column(String(50), nullable=True)  # 收货电话
    contact_email = Column(String(100), nullable=True)  # 收货邮箱

    # 包装信息
    total_packages = Column(Integer, default=1)  # 包裹数量
    total_weight = Column(Numeric(10, 2), nullable=True)  # 总重量(kg)
    total_volume = Column(Numeric(10, 4), nullable=True)  # 总体积(m³)
    package_description = Column(Text, nullable=True)  # 包装说明

    # 附件和签收
    documents = Column(Text, nullable=True)  # 附件列表 JSON [{"name": "xxx.pdf", "url": "..."}]
    delivery_proof = Column(Text, nullable=True)  # 签收凭证 JSON

    # 签收信息
    received_by = Column(String(100), nullable=True)  # 签收人
    received_date = Column(DateTime, nullable=True)  # 签收日期
    received_notes = Column(Text, nullable=True)  # 签收备注

    # 状态
    status = Column(String(20), default='pending')
    # pending: 待发货
    # shipped: 已发货
    # in_transit: 运输中
    # delivered: 已送达
    # received: 已签收
    # exception: 异常

    notes = Column(Text, nullable=True)  # 备注
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    sales_order = relationship('SalesOrder', backref='shipments')
    purchase_order = relationship('PurchaseOrder', backref='shipments')
    created_by = relationship('User', backref='created_shipments')

    def __repr__(self):
        return f'<Shipment {self.shipment_number}>'

    @property
    def formatted_ship_date(self):
        return self.ship_date.strftime('%Y-%m-%d') if self.ship_date else ''

    @property
    def formatted_expected_arrival(self):
        return self.expected_arrival.strftime('%Y-%m-%d') if self.expected_arrival else ''

    @property
    def status_label(self):
        """状态标签"""
        labels = {
            'pending': '待发货',
            'shipped': '已发货',
            'in_transit': '运输中',
            'delivered': '已送达',
            'received': '已签收',
            'exception': '异常'
        }
        return labels.get(self.status, self.status)

    @property
    def total_quantity(self):
        """发货总数量"""
        return sum(detail.quantity or 0 for detail in self.details)


class ShipmentDetail(db.Model):
    """发货明细表 - 记录每次发货的产品明细"""
    __tablename__ = 'shipment_details'

    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey('shipments.id'), nullable=False)
    sales_order_detail_id = Column(Integer, ForeignKey('sales_order_details.id'), nullable=True)  # 关联客户订单明细
    purchase_order_detail_id = Column(Integer, ForeignKey('purchase_order_details.id'), nullable=True)  # 关联采购订单明细
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)

    # 产品信息（冗余存储）
    product_name = Column(String(200), nullable=False)
    product_model = Column(String(100), nullable=True)
    specification = Column(Text, nullable=True)  # 产品规格

    # 数量信息
    quantity = Column(Integer, nullable=False)  # 发货数量
    unit = Column(String(20), nullable=True)  # 单位

    # 序列号列表
    serial_numbers = Column(Text, nullable=True)  # JSON [序列号列表]

    # 签收信息
    received_quantity = Column(Integer, default=0)  # 已签收数量
    status = Column(String(20), default='pending')
    # pending: 待发货
    # shipped: 已发货
    # partial_received: 部分签收
    # received: 已签收

    notes = Column(Text, nullable=True)

    # 关系
    shipment = relationship('Shipment', backref='details')
    sales_order_detail = relationship('SalesOrderDetail', backref='shipment_details')
    purchase_order_detail = relationship('PurchaseOrderDetail', backref='shipment_details')
    product = relationship('Product', backref='shipment_details')

    def __repr__(self):
        return f'<ShipmentDetail {self.product_name}: {self.quantity}>'

    @property
    def remaining_to_receive(self):
        """待签收数量"""
        return max(0, self.quantity - (self.received_quantity or 0))
