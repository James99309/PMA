from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class ProductCategory(db.Model):
    """产品分类模型"""
    __tablename__ = 'product_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # 分类名称
    code_letter = Column(String(1), nullable=False, unique=True)  # 分类标识符
    description = Column(Text)  # 描述
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联字段
    subcategories = db.relationship('ProductSubcategory', backref='parent_category', lazy='dynamic')
    product_codes = db.relationship('ProductCode', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<ProductCategory {self.name} ({self.code_letter})>'

class ProductSubcategory(db.Model):
    """产品名称模型"""
    __tablename__ = 'product_subcategories'
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('product_categories.id'), nullable=False)
    name = Column(String(100), nullable=False)  # 产品名称
    code_letter = Column(String(1), nullable=False)  # 产品名称标识符
    description = Column(Text)  # 描述
    display_order = Column(Integer, default=0)  # 在所属分类中的排序位置（从1开始）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联字段
    fields = db.relationship('ProductCodeField', backref='subcategory', lazy='dynamic', cascade="all, delete-orphan")
    product_codes = db.relationship('ProductCode', backref='subcategory', lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('category_id', 'code_letter', name='uq_subcategory_code_letter'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code_letter': self.code_letter,
            'display_order': self.display_order
        }
    
    def __repr__(self):
        return f'<ProductSubcategory {self.name} ({self.code_letter})>'

class ProductRegion(db.Model):
    __tablename__ = 'product_regions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code_letter = Column(String(1), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code_letter': self.code_letter
        }
    
    def __repr__(self):
        return f'<ProductRegion {self.name} ({self.code_letter})>'

class ProductCodeField(db.Model):
    """产品编码字段模型"""
    __tablename__ = 'product_code_fields'
    
    id = Column(Integer, primary_key=True)
    subcategory_id = Column(Integer, ForeignKey('product_subcategories.id'), nullable=False)
    name = Column(String(100), nullable=False)  # 字段名称
    code = Column(String(10), nullable=True)  # 字段编码，用于标识
    description = Column(Text, nullable=True)  # 字段说明
    field_type = Column(String(20), nullable=False)  # 字段类型：'origin_location', 'spec', 'supplement'
    position = Column(Integer, nullable=False)  # 字段顺序位置
    max_length = Column(Integer, default=1)  # 字段编码最大长度
    is_required = Column(Boolean, default=True)  # 是否必填
    use_in_code = Column(Boolean, default=True)  # 是否用于产品编码
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联字段
    options = db.relationship('ProductCodeFieldOption', backref='field', lazy='dynamic')
    
    def __repr__(self):
        return f'<ProductCodeField {self.name} ({self.field_type})>'

class ProductCodeFieldOption(db.Model):
    """产品编码字段选项模型"""
    __tablename__ = 'product_code_field_options'
    
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('product_code_fields.id'), nullable=False)
    value = Column(String(100), nullable=False)  # 选项值
    code = Column(String(10), nullable=False)  # 选项编码
    description = Column(Text)  # 描述
    is_active = Column(Boolean, default=True)  # 是否活跃
    position = Column(Integer, default=0)  # 排序位置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<ProductCodeFieldOption {self.value} ({self.code})>'

class ProductCode(db.Model):
    """产品编码模型"""
    __tablename__ = 'product_codes'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('product_categories.id'), nullable=False)
    subcategory_id = Column(Integer, ForeignKey('product_subcategories.id'), nullable=False)
    full_code = Column(String(50), unique=True, nullable=False)  # 完整编码
    status = Column(String(20), default='draft')  # 状态：'draft', 'active', 'deprecated'
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    product = relationship('Product', backref=db.backref('product_code', uselist=False))
    creator = relationship('User', backref='created_product_codes')
    
    # 编码组成部分的存储
    field_values = relationship('ProductCodeFieldValue', backref='product_code', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ProductCode {self.full_code}>'

class ProductCodeFieldValue(db.Model):
    """产品编码字段值模型"""
    __tablename__ = 'product_code_field_values'
    
    id = Column(Integer, primary_key=True)
    product_code_id = Column(Integer, ForeignKey('product_codes.id'), nullable=False)
    field_id = Column(Integer, ForeignKey('product_code_fields.id'), nullable=False)
    option_id = Column(Integer, ForeignKey('product_code_field_options.id'))
    custom_value = Column(String(100))  # 自定义值（当没有对应选项时）
    
    # 关联
    field = relationship('ProductCodeField')
    option = relationship('ProductCodeFieldOption')
    
    def __repr__(self):
        return f'<ProductCodeFieldValue {self.field.name}: {self.option.value if self.option else self.custom_value}>' 