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
    display_order = Column(Integer, default=0, nullable=False)  # 显示顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联字段
    subcategories = db.relationship('ProductSubcategory', backref='parent_category', lazy='dynamic')
    product_codes = db.relationship('ProductCode', backref='category', lazy='dynamic')

    @classmethod
    def get_ordered_list(cls):
        """获取按显示顺序排列的分类列表"""
        return cls.query.order_by(cls.display_order, cls.id).all()

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
    """
    ⚠️ DEPRECATED - 此表已废弃

    此表为历史遗留，现已被 ProductCodeField (field_type='origin_location') 替代。

    废弃原因：
    - 系统已统一使用 product_code_fields 表管理销售区域
    - 保留此类仅用于兼容历史数据和数据库表定义

    新功能请使用：
        ProductCodeField.query.filter_by(field_type='origin_location')

    管理页面：/origin-fields（区域信息管理）

    废弃日期：2025-11-20
    """
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
    options = db.relationship('ProductCodeFieldOption', backref='field', lazy='dynamic', cascade="all, delete-orphan")
    
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

    def generate_snapshot(self):
        """生成产品编码的完整定义快照

        返回包含编码定义的完整信息字典，用于永久保存到产品表中。
        避免编码表变化导致历史产品编码含义丢失。

        Returns:
            dict: 编码定义快照，包含元数据、分类信息、字段明细
        """
        from app.models.product_code import ProductCategory, ProductSubcategory, ProductCodeField

        # 查询分类信息
        category = ProductCategory.query.get(self.category_id)
        subcategory = ProductSubcategory.query.get(self.subcategory_id)

        # 构建快照基本结构
        snapshot = {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "product_code_id": self.id,
            "full_code": self.full_code,
            "category": {
                "id": category.id if category else None,
                "name": category.name if category else "",
                "code_letter": category.code_letter if category else "",
                "description": category.description if category else ""
            },
            "subcategory": {
                "id": subcategory.id if subcategory else None,
                "name": subcategory.name if subcategory else "",
                "code_letter": subcategory.code_letter if subcategory else "",
                "description": subcategory.description if subcategory else ""
            },
            "code_parts": []
        }

        # 查询产品的地区信息（如果存在）
        if hasattr(self.product, 'region_id') and self.product.region_id:
            region = ProductCodeField.query.get(self.product.region_id)
            if region and region.field_type == 'origin_location':
                snapshot["region"] = {
                    "id": region.id,
                    "name": region.name,
                    "code": region.code,
                    "description": region.description if region.description else ""
                }

        # 获取所有字段值，按position排序
        field_value_list = db.session.query(ProductCodeFieldValue)\
            .join(ProductCodeField)\
            .filter(ProductCodeFieldValue.product_code_id == self.id)\
            .order_by(ProductCodeField.position)\
            .all()

        # 构建每个编码位的详细信息
        for field_value in field_value_list:
            field = field_value.field
            option = field_value.option

            # 导入单位查询函数
            from app.routes.product_code import get_field_unit
            unit = get_field_unit(field.name)

            part = {
                "position": field.position,
                "field_id": field.id,
                "field_name": field.name,
                "field_type": field.field_type,
                "field_code": field.code if field.code else "",
                "unit": unit,
            }

            # 添加选项信息或自定义值
            if option:
                part["option_id"] = option.id
                part["code"] = option.code
                part["value"] = option.value
                part["description"] = option.description if option.description else ""
            else:
                part["option_id"] = None
                part["code"] = field_value.custom_value if field_value.custom_value else ""
                part["value"] = field_value.custom_value if field_value.custom_value else ""
                part["description"] = ""

            snapshot["code_parts"].append(part)

        return snapshot

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

class SpecificationDictionary(db.Model):
    """规格字典 - 存储标准化的规格名称"""
    __tablename__ = 'specification_dictionary'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)  # 规格名称，如"频率范围"
    unit = Column(String(20), nullable=True)  # 单位，如"MHz", "dBm"
    is_active = Column(Boolean, default=True)  # 是否活跃（可停用不常用的规格）
    display_order = Column(Integer, nullable=False, default=0, index=True)  # 显示排序（用于拖拽排序）
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SpecificationDictionary {self.name}>'