# -*- coding: utf-8 -*-
"""
产品序列号模型
管理产品序列号的全生命周期追踪（从入库到出库）
"""
from app import db
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class ProductSerialNumber(db.Model):
    """产品序列号表 - 追踪产品从入库到出库的全生命周期"""
    __tablename__ = 'product_serial_numbers'

    id = Column(Integer, primary_key=True)
    serial_number = Column(String(100), unique=True, nullable=False)  # 序列号（唯一）
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)  # 关联产品

    # ========== 采购来源 ==========
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=True)  # 采购订单
    purchase_detail_id = Column(Integer, ForeignKey('purchase_order_details.id'), nullable=True)  # 订单明细
    batch_number = Column(String(100), nullable=True)  # 批次号
    supplier_id = Column(Integer, ForeignKey('companies.id'), nullable=True)  # 供应商

    # ========== 入库信息 ==========
    warehouse_in_date = Column(DateTime, nullable=True)  # 入库日期
    warehouse_location = Column(String(100), nullable=True)  # 仓库位置
    inventory_id = Column(Integer, ForeignKey('inventory.id'), nullable=True)  # 库存记录
    received_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 入库操作人

    # ========== 出库信息 ==========
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'), nullable=True)  # 关联客户订单
    shipment_id = Column(Integer, ForeignKey('shipments.id'), nullable=True)  # 关联发货单
    ship_out_date = Column(DateTime, nullable=True)  # 出库日期
    destination = Column(String(200), nullable=True)  # 目的地
    shipped_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 出库操作人

    # ========== 客户信息 ==========
    customer_id = Column(Integer, ForeignKey('companies.id'), nullable=True)  # 最终客户
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)  # 关联项目

    # ========== 状态 ==========
    status = Column(String(20), default='registered')
    # registered: 已登记（序列号录入但未入库）
    # in_stock: 库存中
    # reserved: 已预留（关联到订单但未发货）
    # shipped: 已发货
    # delivered: 已交付（客户签收）
    # returned: 已退回
    # defective: 故障/损坏

    # ========== 测试信息 ==========
    test_passed = Column(Boolean, nullable=True)  # 测试是否通过
    test_date = Column(DateTime, nullable=True)  # 测试日期
    test_id = Column(Integer, ForeignKey('product_tests.id'), nullable=True)  # 关联测试记录

    # ========== 质保信息 ==========
    warranty_start_date = Column(DateTime, nullable=True)  # 质保开始日期
    warranty_end_date = Column(DateTime, nullable=True)  # 质保结束日期
    warranty_notes = Column(Text, nullable=True)  # 质保备注

    # ========== 其他信息 ==========
    manufacture_date = Column(DateTime, nullable=True)  # 生产日期
    hardware_version = Column(String(50), nullable=True)  # 硬件版本
    firmware_version = Column(String(50), nullable=True)  # 固件版本
    mac_address = Column(String(50), nullable=True)  # MAC地址（如适用）

    notes = Column(Text, nullable=True)  # 备注
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    product = relationship('Product', backref='serial_numbers')
    purchase_order = relationship('PurchaseOrder', backref='serial_numbers')
    purchase_detail = relationship('PurchaseOrderDetail', backref='serial_numbers')
    supplier = relationship('Company', foreign_keys=[supplier_id], backref='supplied_serial_numbers')
    inventory = relationship('Inventory', backref='serial_numbers')
    sales_order = relationship('SalesOrder', backref='serial_numbers')
    shipment = relationship('Shipment', backref='serial_numbers')
    customer = relationship('Company', foreign_keys=[customer_id], backref='owned_serial_numbers')
    project = relationship('Project', backref='serial_numbers')
    test = relationship('ProductTest', backref='serial_numbers')
    received_by = relationship('User', foreign_keys=[received_by_id], backref='received_serial_numbers')
    shipped_by = relationship('User', foreign_keys=[shipped_by_id], backref='shipped_serial_numbers')
    created_by = relationship('User', foreign_keys=[created_by_id], backref='created_serial_numbers')

    def __repr__(self):
        return f'<ProductSerialNumber {self.serial_number}>'

    @property
    def status_label(self):
        """状态标签"""
        labels = {
            'registered': '已登记',
            'in_stock': '库存中',
            'reserved': '已预留',
            'shipped': '已发货',
            'delivered': '已交付',
            'returned': '已退回',
            'defective': '故障'
        }
        return labels.get(self.status, self.status)

    @property
    def formatted_warehouse_in_date(self):
        return self.warehouse_in_date.strftime('%Y-%m-%d') if self.warehouse_in_date else ''

    @property
    def formatted_ship_out_date(self):
        return self.ship_out_date.strftime('%Y-%m-%d') if self.ship_out_date else ''

    @property
    def is_in_warranty(self):
        """是否在保修期内"""
        if not self.warranty_end_date:
            return None
        from datetime import datetime
        return datetime.now() <= self.warranty_end_date


class SerialNumberHistory(db.Model):
    """序列号历史记录表 - 记录序列号状态变更历史"""
    __tablename__ = 'serial_number_histories'

    id = Column(Integer, primary_key=True)
    serial_number_id = Column(Integer, ForeignKey('product_serial_numbers.id'), nullable=False)

    # 变更信息
    action = Column(String(50), nullable=False)  # 操作类型：register/stock_in/reserve/ship/deliver/return/defect
    status_before = Column(String(20), nullable=True)  # 变更前状态
    status_after = Column(String(20), nullable=False)  # 变更后状态

    # 关联单据
    reference_type = Column(String(50), nullable=True)  # 关联单据类型：purchase_order/sales_order/shipment等
    reference_id = Column(Integer, nullable=True)  # 关联单据ID

    # 操作详情
    description = Column(Text, nullable=True)  # 变更说明
    location = Column(String(100), nullable=True)  # 当前位置

    # 操作人和时间
    operated_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    operated_at = Column(DateTime, default=func.now())

    # 关系
    serial_number = relationship('ProductSerialNumber', backref='histories')
    operated_by = relationship('User', backref='serial_number_operations')

    def __repr__(self):
        return f'<SerialNumberHistory {self.action}: {self.status_before} -> {self.status_after}>'

    @property
    def action_label(self):
        """操作类型标签"""
        labels = {
            'register': '登记',
            'stock_in': '入库',
            'reserve': '预留',
            'ship': '发货',
            'deliver': '交付',
            'return': '退回',
            'defect': '故障标记',
            'update': '信息更新'
        }
        return labels.get(self.action, self.action)
