from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class ProductCategory(db.Model):
    """产品分类模型"""
    __tablename__ = 'product_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # 分类名称（中文）
    name_en = Column(String(100))  # 分类名称（英文）
    code_letter = Column(String(1), nullable=False, unique=True)  # 分类标识符
    description = Column(Text)  # 描述
    display_order = Column(Integer, default=0, nullable=False)  # 显示顺序
    manager_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='产品经理ID')
    icon_key = Column(String(30), comment='系统图图标标识')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联字段
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_categories')
    subcategories = db.relationship('ProductSubcategory', backref='parent_category', lazy='dynamic')
    product_codes = db.relationship('ProductCode', backref='category', lazy='dynamic')

    @classmethod
    def get_ordered_list(cls):
        """获取按显示顺序排列的分类列表"""
        return cls.query.order_by(cls.display_order, cls.id).all()

    def __repr__(self):
        return f'<ProductCategory {self.name} ({self.code_letter})>'

class ProductSubcategory(db.Model):
    """产品子分类（产品系列）模型"""
    __tablename__ = 'product_subcategories'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('product_categories.id'), nullable=False)
    name = Column(String(100), nullable=False)  # 子分类名称（中文）
    name_en = Column(String(100))  # 子分类名称（英文）
    code_letter = Column(String(1), nullable=False)  # 子分类标识符
    description = Column(Text)  # 描述
    display_order = Column(Integer, default=0)  # 在所属分类中的排序位置（从1开始）
    icon_key = Column(String(30), comment='系统图图标标识')
    image_path = Column(String(500))  # 子分类共享图片
    pdf_path = Column(String(500))    # 子分类共享PDF
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

class ProductCodeField(db.Model):
    """产品编码字段模型

    支持两种级别的字段定义：
    - 分类级字段：category_id 有值，subcategory_id 为空，所有子分类继承
    - 子分类级字段：subcategory_id 有值，category_id 为空，仅该子分类使用
    """
    __tablename__ = 'product_code_fields'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('product_categories.id'), nullable=True)  # 分类级字段
    subcategory_id = Column(Integer, ForeignKey('product_subcategories.id'), nullable=True)  # 子分类级字段
    name = Column(String(100), nullable=False)  # 字段名称
    name_en = Column(String(100))  # 字段名称（英文）
    code = Column(String(10), nullable=True)  # 字段编码，用于标识
    description = Column(Text, nullable=True)  # 字段说明
    field_type = Column(String(20), nullable=False)  # 字段类型：'origin_location', 'spec', 'supplement'
    position = Column(Integer, nullable=False)  # 字段顺序位置
    max_length = Column(Integer, default=1)  # 字段编码最大长度
    is_required = Column(Boolean, default=True)  # 是否必填
    use_in_code = Column(Boolean, default=True)  # 是否用于产品编码
    allow_quotation_config = Column(Boolean, default=False)  # 是否允许在报价单中动态配置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联字段
    category = db.relationship('ProductCategory', backref=db.backref('code_fields', lazy='dynamic'))
    options = db.relationship('ProductCodeFieldOption', backref='field', lazy='dynamic', cascade="all, delete-orphan")

    @property
    def is_category_level(self):
        """是否为分类级字段"""
        return self.category_id is not None and self.subcategory_id is None

    @property
    def options_sorted(self):
        """返回按position排序的选项列表"""
        return self.options.order_by(ProductCodeFieldOption.position).all()

    @classmethod
    def get_category_fields(cls, category_id):
        """获取分类级别的编码字段"""
        return cls.query.filter_by(
            category_id=category_id,
            subcategory_id=None
        ).order_by(cls.position).all()

    @classmethod
    def get_subcategory_fields(cls, subcategory_id):
        """获取子分类级别的编码字段"""
        return cls.query.filter_by(
            subcategory_id=subcategory_id
        ).order_by(cls.position).all()

    @classmethod
    def get_all_fields_for_subcategory(cls, subcategory_id):
        """获取子分类的所有字段（包括继承的分类级字段）"""
        from app.models.product_code import ProductSubcategory
        subcategory = ProductSubcategory.query.get(subcategory_id)
        if not subcategory:
            return {'inherited': [], 'own': []}

        inherited = cls.get_category_fields(subcategory.category_id)
        own = cls.get_subcategory_fields(subcategory_id)

        return {'inherited': inherited, 'own': own}

    def is_configurable_for_subcategory(self, subcategory_id):
        """检查该字段在特定子分类下是否允许报价配置

        通过检查是否存在 allow_quotation_config=True 的子分类级选项来判断
        """
        option = ProductCodeFieldOption.query.filter_by(
            field_id=self.id,
            subcategory_id=subcategory_id,
            allow_quotation_config=True,
            is_active=True
        ).first()
        return option is not None

    def get_options_for_subcategory(self, subcategory_id):
        """获取该字段在特定子分类下的可用选项（用于报价配置）

        返回 subcategory_id 匹配且 allow_quotation_config=True 的选项
        """
        return ProductCodeFieldOption.query.filter_by(
            field_id=self.id,
            subcategory_id=subcategory_id,
            allow_quotation_config=True,
            is_active=True
        ).order_by(ProductCodeFieldOption.position).all()

    def __repr__(self):
        level = 'category' if self.is_category_level else 'subcategory'
        return f'<ProductCodeField {self.name} ({self.field_type}, {level})>'

class ProductCodeFieldOption(db.Model):
    """产品编码字段选项模型

    支持两级选项定义：
    - 分类级选项：subcategory_id 为空，用于产品编码生成
    - 子分类级选项：subcategory_id 有值，用于报价可配置功能

    新架构：引用模式
    - spec_option_id: 引用 SpecificationOption 中的指标
    - value/code: 保留用于兼容，迁移完成后可通过 spec_option 获取

    当 spec_option_id 有值时，value 和 code 应从关联的 spec_option 获取
    """
    __tablename__ = 'product_code_field_options'

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('product_code_fields.id'), nullable=False)
    subcategory_id = Column(Integer, ForeignKey('product_subcategories.id'), nullable=True)  # 子分类ID（空=分类级）
    spec_option_id = Column(Integer, ForeignKey('specification_options.id'), nullable=True)  # 引用规格指标
    value = Column(String(100), nullable=True)  # 选项值（兼容字段，迁移后可空）
    code = Column(String(10), nullable=True)  # 选项编码（兼容字段，迁移后可空）
    description = Column(Text)  # 描述
    is_active = Column(Boolean, default=True)  # 是否活跃（本地启用/禁用）
    position = Column(Integer, default=0)  # 排序位置（本地排序）
    price_adjustment = Column(Integer, default=0)  # 价格增量（单位：分），正数加价，负数减价
    allow_quotation_config = Column(Boolean, default=False)  # 是否允许报价配置（子分类级选项使用）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    spec_option = db.relationship('SpecificationOption')
    subcategory = db.relationship('ProductSubcategory', backref=db.backref('field_options', lazy='dynamic'))

    @property
    def effective_value(self):
        """获取有效的指标值（优先使用引用的规格指标）"""
        if self.spec_option:
            return self.spec_option.value
        return self.value

    @property
    def effective_code(self):
        """获取有效的编码（优先使用引用的规格指标）"""
        if self.spec_option:
            return self.spec_option.code
        return self.code

    def __repr__(self):
        return f'<ProductCodeFieldOption {self.effective_value} ({self.effective_code})>'

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
    """规格字典 - 统一主表（合并原 spec_definitions 字段）

    合并前: specification_dictionary(编码层) + spec_definitions(定义层) 靠 name 桥接
    合并后: specification_dictionary 为唯一主表，包含定义层字段
    """
    __tablename__ = 'specification_dictionary'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)  # 规格名称，如"频率范围"
    name_en = Column(String(100), nullable=True)  # 英文名称（原 spec_definitions.name_en）
    unit = Column(String(20), nullable=True)  # 单位，如"MHz", "dBm"
    category_id = Column(Integer, ForeignKey('spec_categories.id'), nullable=True)  # 规格分类
    description = Column(Text, nullable=True)  # 规格说明
    value_type = Column(String(20), default='text')  # 值类型：text/number/select/boolean
    allow_attachment = Column(Boolean, default=False)  # 是否允许上传附件
    default_test_condition_id = Column(Integer, ForeignKey('test_condition_dictionary.id'), nullable=True)
    default_test_method_id = Column(Integer, ForeignKey('test_method_dictionary.id'), nullable=True)
    is_active = Column(Boolean, default=True)  # 是否活跃（可停用不常用的规格）
    display_order = Column(Integer, nullable=False, default=0, index=True)  # 显示排序（用于拖拽排序）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    category = db.relationship('SpecCategory', foreign_keys=[category_id])
    default_test_condition = db.relationship('TestConditionDictionary', foreign_keys=[default_test_condition_id])
    default_test_method = db.relationship('TestMethodDictionary', foreign_keys=[default_test_method_id])
    options = db.relationship('SpecificationOption', backref='spec', lazy='dynamic', cascade="all, delete-orphan")
    template_items = db.relationship('SpecTemplateItem', back_populates='spec_dict',
                                     foreign_keys='SpecTemplateItem.spec_dict_id')

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'unit': self.unit,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'description': self.description,
            'value_type': self.value_type,
            'allow_attachment': self.allow_attachment,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'default_test_condition_id': self.default_test_condition_id,
            'default_test_condition': self.default_test_condition.name if self.default_test_condition else None,
            'default_test_method_id': self.default_test_method_id,
            'default_test_method': self.default_test_method.name if self.default_test_method else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SpecificationDictionary {self.name}>'


class SpecificationOption(db.Model):
    """规格指标 - 存储规格字典下的具体指标值和编码

    每个规格（如"频率范围"）可以有多个指标选项（如"400-450"、"134-174"），
    每个指标有唯一的编码，由智能编码规则自动生成。

    分类和子分类的规格字段只引用这些指标，不独立存储。
    """
    __tablename__ = 'specification_options'

    id = Column(Integer, primary_key=True)
    spec_id = Column(Integer, ForeignKey('specification_dictionary.id'), nullable=False)  # 所属规格
    value = Column(String(100), nullable=False)  # 指标值，如"400-450"
    code = Column(String(10), nullable=False)  # 指标编码，如"4"（智能生成）
    description = Column(Text)  # 描述
    is_active = Column(Boolean, default=True)  # 是否活跃
    position = Column(Integer, default=0)  # 排序位置
    created_at = Column(DateTime, default=datetime.utcnow)

    # 唯一约束：同一规格下指标值唯一
    __table_args__ = (
        db.UniqueConstraint('spec_id', 'value', name='uq_spec_option_value'),
    )

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'spec_id': self.spec_id,
            'value': self.value,
            'code': self.code,
            'description': self.description,
            'is_active': self.is_active,
            'position': self.position,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<SpecificationOption {self.value} ({self.code})>'