"""
产品规格模型 - 存储产品库产品的规格值

与研发产品规格（DevProductSpec）使用相同的结构，但关联到products表
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app import db


class ProductSpec(db.Model):
    """产品规格值模型"""
    __tablename__ = 'product_specs'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    field_name = Column(String(100), nullable=False)  # 规格名称
    field_value = Column(String(255), nullable=False)  # 规格值
    field_code = Column(String(10), nullable=True)  # 规格编码（用于MN号生成）
    display_order = Column(Integer, default=0)  # 显示顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    product = relationship("Product", backref=db.backref('specs', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<ProductSpec {self.field_name}: {self.field_value}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'field_name': self.field_name,
            'field_value': self.field_value,
            'field_code': self.field_code,
            'display_order': self.display_order
        }
