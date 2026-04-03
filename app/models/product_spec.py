"""
产品规格模型 - 存储产品库产品的规格值

与研发产品规格（DevProductSpec）使用相同的结构，但关联到products表
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app import db


class ProductSpec(db.Model):
    """产品规格值模型"""
    __tablename__ = 'product_specs'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    field_name = Column(String(100), nullable=False)  # 规格名称（中文）
    field_name_en = Column(String(100), nullable=True)  # 规格名称（英文）
    field_value = Column(String(255), nullable=False)  # 规格值
    field_value_en = Column(String(255), nullable=True)  # 规格值（英文）
    field_code = Column(String(10), nullable=True)  # 规格编码（用于MN号生成）
    use_in_code = Column(Boolean, default=False)  # 是否参与MN编码（来源：SpecTemplateItem.use_in_code）
    unit = Column(String(20), nullable=True)  # 规格单位（如 dB、MHz、kg）
    include_in_description = Column(Boolean, default=False)  # 是否纳入产品描述
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
            'field_name_en': self.field_name_en or '',
            'field_value': self.field_value,
            'field_value_en': self.field_value_en or '',
            'field_code': self.field_code,
            'use_in_code': bool(self.use_in_code),
            'unit': self.unit or '',
            'include_in_description': self.include_in_description if self.include_in_description is not None else False,
            'display_order': self.display_order
        }
