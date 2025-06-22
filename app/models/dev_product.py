from datetime import datetime
from sqlalchemy import ForeignKey, Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from app import db

class DevProduct(db.Model):
    __tablename__ = 'dev_products'
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('product_categories.id'))
    subcategory_id = Column(Integer, ForeignKey('product_subcategories.id'))
    region_id = Column(Integer, ForeignKey('product_regions.id'))
    name = Column(String(100))
    model = Column(String(100))
    status = Column(String(50))
    unit = Column(String(20))
    retail_price = Column(Float)
    currency = Column(String(10), default='CNY')  # 货币类型
    description = Column(Text)
    image_path = Column(String(255))
    pdf_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'))
    created_by = Column(Integer, ForeignKey('users.id'))
    mn_code = Column(String(20))
    
    # 关联关系
    category = relationship("ProductCategory", foreign_keys=[category_id])
    subcategory = relationship("ProductSubcategory", foreign_keys=[subcategory_id])
    region = relationship("ProductRegion", foreign_keys=[region_id])
    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by])
    specs = relationship("DevProductSpec", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DevProduct {self.model}>"

class DevProductSpec(db.Model):
    __tablename__ = 'dev_product_specs'
    
    id = Column(Integer, primary_key=True)
    dev_product_id = Column(Integer, ForeignKey('dev_products.id'))
    field_name = Column(String(100))
    field_value = Column(String(255))
    field_code = Column(String(10))  # 规格编码，用于MN号生成
    
    # 关联关系
    product = relationship("DevProduct", back_populates="specs")
    
    def __repr__(self):
        return f"<DevProductSpec {self.field_name}: {self.field_value}>" 