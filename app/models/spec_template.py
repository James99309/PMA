"""
规格模板系统模型定义

包含9个表的模型：
1. TestMethodDictionary - 测试方法字典
2. TestConditionDictionary - 测试条件字典
3. SpecCategory - 规格分类
4. SpecDefinition - 全局规格字典
5. SpecTemplate - 规格模板
6. SpecTemplateItem - 模板规格项
7. ProductConfiguration - 产品配置版本
8. ProductConfigValue - 配置版本规格值
9. SpecAttachment - 规格附件
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Index, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, CheckConstraint, text
from sqlalchemy.orm import relationship
from app import db


class TestMethodDictionary(db.Model):
    """测试方法字典"""
    __tablename__ = 'test_method_dictionary'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)  # 测试方法名称
    description = Column(Text)  # 说明
    category = Column(String(50))  # 方法类别（RF/ENV/EMC等）
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TestMethod {self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'display_order': self.display_order,
            'is_active': self.is_active
        }


class TestConditionDictionary(db.Model):
    """测试条件字典"""
    __tablename__ = 'test_condition_dictionary'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)  # 测试条件
    description = Column(Text)  # 说明
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TestCondition {self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'display_order': self.display_order,
            'is_active': self.is_active
        }


class SpecCategory(db.Model):
    """规格分类"""
    __tablename__ = 'spec_categories'

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)  # 分类代码
    name = Column(String(100), nullable=False)  # 中文名称
    name_en = Column(String(100))  # 英文名称
    description = Column(Text)  # 分类描述
    display_order = Column(Integer, default=0)  # 显示顺序
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    spec_dicts = relationship("SpecificationDictionary", foreign_keys="SpecificationDictionary.category_id",
                              overlaps="category")

    def __repr__(self):
        return f"<SpecCategory {self.code}: {self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'name_en': self.name_en,
            'description': self.description,
            'display_order': self.display_order,
            'is_active': self.is_active
        }


class SpecDefinition(db.Model):
    """全局规格字典（标准化规格项）"""
    __tablename__ = 'spec_definitions'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('spec_categories.id'))
    name = Column(String(100), nullable=False)  # 标准规格名称（中文）
    name_en = Column(String(100))  # 标准规格名称（英文）
    unit = Column(String(30))  # 单位
    description = Column(Text)  # 规格说明
    value_type = Column(String(20), default='text')  # 值类型：text/number/select/boolean
    allow_attachment = Column(Boolean, default=False)  # 是否允许上传附件
    default_test_condition_id = Column(Integer, ForeignKey('test_condition_dictionary.id'))
    default_test_method_id = Column(Integer, ForeignKey('test_method_dictionary.id'))
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系（category 反向关系已从 SpecCategory 移除）
    category = relationship("SpecCategory")
    default_test_condition = relationship("TestConditionDictionary", foreign_keys=[default_test_condition_id])
    default_test_method = relationship("TestMethodDictionary", foreign_keys=[default_test_method_id])
    # template_items 反向关系已移除（definition FK 已废弃，统一使用 spec_dict）

    def __repr__(self):
        return f"<SpecDefinition {self.name}>"

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'name': self.name,
            'name_en': self.name_en,
            'unit': self.unit,
            'description': self.description,
            'value_type': self.value_type,
            'allow_attachment': self.allow_attachment,
            'display_order': self.display_order,
            'is_active': self.is_active,
            # 测试条件和方法
            'default_test_condition_id': self.default_test_condition_id,
            'default_test_condition': self.default_test_condition.name if self.default_test_condition else None,
            'default_test_method_id': self.default_test_method_id,
            'default_test_method': self.default_test_method.name if self.default_test_method else None
        }


class SpecTemplate(db.Model):
    """规格模板（型号级）"""
    __tablename__ = 'spec_templates'

    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False)  # 产品型号
    name = Column(String(200))  # 模板名称
    name_en = Column(String(200))  # 模板名称（英文）
    description = Column(Text)  # 模板描述
    unit = Column(String(20))  # 产品计量单位（套、个、台、米等）
    version = Column(String(20), default='V1.0')  # 模板版本
    version_first_used_at = Column(DateTime)  # 当前版本首次生成MN编码的时间（用于判断版本是否被绑定）
    deleted_at = Column(DateTime, nullable=True)  # 软删除
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 产品分类（用于MN编码生成）
    category_id = Column(Integer, ForeignKey('product_categories.id'))
    subcategory_id = Column(Integer, ForeignKey('product_subcategories.id'))

    # 关联关系
    creator = relationship("User", foreign_keys=[created_by])
    category = relationship("ProductCategory", foreign_keys=[category_id])
    subcategory = relationship("ProductSubcategory", foreign_keys=[subcategory_id])
    items = relationship("SpecTemplateItem", back_populates="template", cascade="all, delete-orphan",
                          order_by="SpecTemplateItem.display_order")
    configurations = relationship("ProductConfiguration", back_populates="template", cascade="all, delete-orphan",
                                   order_by="ProductConfiguration.display_order")

    __table_args__ = (
        Index('uix_spec_templates_model_active', 'model', unique=True,
              postgresql_where=text('deleted_at IS NULL')),
    )

    def __repr__(self):
        return f"<SpecTemplate {self.model}>"

    def to_dict(self):
        return {
            'id': self.id,
            'model': self.model,
            'name': self.name,
            'name_en': self.name_en,
            'description': self.description,
            'unit': self.unit,
            'version': self.version,
            'version_first_used_at': self.version_first_used_at.isoformat() if self.version_first_used_at else None,
            'version_bound': self.version_first_used_at is not None,  # 当前版本是否已被使用过
            'created_by': self.created_by,
            'creator_name': self.creator.real_name if self.creator else None,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'category_code': self.category.code_letter if self.category else None,
            'subcategory_id': self.subcategory_id,
            'subcategory_name': self.subcategory.name if self.subcategory else None,
            'subcategory_code': self.subcategory.code_letter if self.subcategory else None,
            'item_count': len(self.items) if self.items else 0,
            'config_count': len([c for c in self.configurations if c.deleted_at is None]) if self.configurations else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_items_by_category(self):
        """按分类获取模板规格项"""
        items_by_category = {}
        for item in self.items:
            src = item.spec_dict
            category = src.category if src else None
            if category:
                if category.id not in items_by_category:
                    items_by_category[category.id] = {
                        'category': category.to_dict(),
                        'items': []
                    }
                items_by_category[category.id]['items'].append(item.to_dict())
        return list(items_by_category.values())


class SpecTemplateItem(db.Model):
    """模板规格项定义"""
    __tablename__ = 'spec_template_items'

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('spec_templates.id', ondelete='CASCADE'))
    definition_id = Column(Integer, ForeignKey('spec_definitions.id'))  # 旧FK，保留兼容
    spec_dict_id = Column(Integer, ForeignKey('specification_dictionary.id'))  # 新FK → 统一主表
    general_value = Column(String(255))  # 该型号的通用规格值（General）
    test_condition_id = Column(Integer, ForeignKey('test_condition_dictionary.id'))
    test_condition_text = Column(String(200))  # 自由输入的测试条件
    test_method_id = Column(Integer, ForeignKey('test_method_dictionary.id'))
    test_method_text = Column(String(200))  # 自由输入的测试方法
    display_order = Column(Integer, default=0)
    is_required = Column(Boolean, default=False)  # 是否必填
    options = Column(JSON)  # 该型号的可选值列表
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 编码生成相关字段（模板级）
    use_in_code = Column(Boolean, default=False)  # 是否参与MN编码生成
    code_length = Column(Integer, default=1)  # 编码长度：1位或2位

    # 关联关系
    template = relationship("SpecTemplate", back_populates="items")
    # definition 关系已移除（definition_id FK 指向旧表 spec_definitions，已废弃）
    spec_dict = relationship("SpecificationDictionary", back_populates="template_items",
                             foreign_keys=[spec_dict_id])
    test_condition = relationship("TestConditionDictionary", foreign_keys=[test_condition_id])
    test_method = relationship("TestMethodDictionary", foreign_keys=[test_method_id])
    # 不使用 delete-orphan：删除规格项时保留配置值（用于锁定配置的历史值）
    config_values = relationship("ProductConfigValue", back_populates="template_item")
    attachments = relationship("SpecAttachment", back_populates="template_item", cascade="all, delete-orphan",
                               foreign_keys="SpecAttachment.template_item_id")

    def __repr__(self):
        src = self.spec_dict
        return f"<SpecTemplateItem {src.name if src else 'N/A'}>"

    def get_test_condition_display(self):
        """获取测试条件显示文本"""
        if self.test_condition:
            return self.test_condition.name
        return self.test_condition_text or ''

    def get_test_method_display(self):
        """获取测试方法显示文本"""
        if self.test_method:
            return self.test_method.name
        return self.test_method_text or ''

    def to_dict(self):
        src = self.spec_dict
        return {
            'id': self.id,
            'template_id': self.template_id,
            'definition_id': self.definition_id,
            'spec_dict_id': self.spec_dict_id,
            'definition_name': src.name if src else None,
            'definition_name_en': src.name_en if src else None,
            'unit': src.unit if src else None,
            'category_id': src.category_id if src else None,
            'category_name': src.category.name if src and src.category else None,
            'general_value': self.general_value,
            'test_condition': self.get_test_condition_display(),
            'test_method': self.get_test_method_display(),
            'display_order': self.display_order,
            'is_required': self.is_required,
            'options': self.options,
            # 编码生成相关字段
            'use_in_code': self.use_in_code,
            'code_length': self.code_length
        }


class ProductConfiguration(db.Model):
    """产品配置版本"""
    __tablename__ = 'product_configurations'

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('spec_templates.id', ondelete='CASCADE'))
    dev_product_id = Column(Integer, ForeignKey('dev_products.id', ondelete='SET NULL'))
    config_code = Column(String(50), nullable=False)  # 配置编码
    region = Column(String(50))  # 适用区域
    region_name = Column(String(100))  # 区域名称
    status = Column(String(50), default='development')  # 生产状态
    mn_code = Column(String(50))  # MN编码
    power_spec = Column(String(50))  # 供电规格
    power_cord_type = Column(String(50))  # 电源线类型
    notes = Column(Text)  # 备注
    template_version = Column(String(20))  # 创建时的模版版本快照
    deleted_at = Column(DateTime, nullable=True)  # 软删除
    display_order = Column(Integer, default=0)  # 显示顺序，用于拖动排序
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 编码规则快照（MN编码生成时保存）
    code_rule_version = Column(String(20))  # 规则版本号，如 "V1.0"
    code_rule_snapshot = Column(JSON)  # 编码规则完整快照

    # 关联关系
    template = relationship("SpecTemplate", back_populates="configurations")
    dev_product = relationship("DevProduct", foreign_keys=[dev_product_id])
    creator = relationship("User", foreign_keys=[created_by])
    config_values = relationship("ProductConfigValue", back_populates="configuration", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ProductConfiguration {self.config_code}>"

    @property
    def full_code(self):
        """获取完整配置编码（区域-配置编码）"""
        if self.region:
            return f"{self.region}-{self.config_code}"
        return self.config_code

    @property
    def mn_locked(self):
        """
        判断 MN 编码是否锁定

        当配置处于以下状态时，MN 编码被锁定，不允许修改：
        - production（可生产）
        - discontinued（停产）

        Returns:
            bool: True 表示锁定，False 表示可修改
        """
        return self.status in ('production', 'discontinued')

    def get_spec_value(self, template_item_id):
        """获取指定规格项的值"""
        for cv in self.config_values:
            if cv.template_item_id == template_item_id:
                return cv.value
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'template_model': self.template.model if self.template else None,
            'dev_product_id': self.dev_product_id,
            'config_code': self.config_code,
            'full_code': self.full_code,
            'region': self.region,
            'region_name': self.region_name,
            'status': self.status,
            'mn_code': self.mn_code,
            'mn_locked': self.mn_locked,  # MN 编码是否锁定
            'power_spec': self.power_spec,
            'power_cord_type': self.power_cord_type,
            'notes': self.notes,
            'template_version': self.template_version,
            'version_match': self.template_version == self.template.version if self.template and self.template_version else None,
            'display_order': self.display_order,
            'created_by': self.created_by,
            'creator_name': self.creator.real_name if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # 编码规则快照
            'code_rule_version': self.code_rule_version,
            'code_rule_snapshot': self.code_rule_snapshot,
            # 产品库引用信息（本地 + SG NAS）
            'product_refs': self._get_product_refs()
        }

    def _get_product_refs(self):
        """获取引用此配置的产品列表（本地 + 跨库）"""
        refs = []

        # 本地产品库
        for p in getattr(self, 'productized_products', []):
            if not p.is_deleted:
                refs.append({
                    'id': p.id,
                    'product_mn': p.product_mn,
                    'product_name': p.product_name,
                    'database': 'cn',
                })

        # SG NAS 产品库（通过 postgres_fdw 外部表，按 mn_code 匹配）
        if self.mn_code:
            try:
                from sqlalchemy import text
                result = db.session.execute(
                    text('SELECT id, product_mn, product_name FROM sg_products WHERE product_mn = :mn_code'),
                    {'mn_code': self.mn_code}
                )
                for row in result:
                    refs.append({
                        'id': row.id,
                        'product_mn': row.product_mn,
                        'product_name': row.product_name,
                        'database': 'sg',
                    })
            except Exception:
                db.session.rollback()  # fdw 失败后回滚，避免污染后续查询

        return refs


class ProductConfigValue(db.Model):
    """配置版本规格值"""
    __tablename__ = 'product_config_values'

    id = Column(Integer, primary_key=True)
    configuration_id = Column(Integer, ForeignKey('product_configurations.id', ondelete='CASCADE'))
    # 使用 SET NULL：删除规格项时保留配置值记录（用于锁定配置的历史值）
    template_item_id = Column(Integer, ForeignKey('spec_template_items.id', ondelete='SET NULL'), nullable=True)
    value = Column(String(500))  # 规格值（覆盖通用值，NULL表示使用通用值）
    notes = Column(String(255))  # 备注
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 孤立项信息：当 template_item 被删除后，保留规格信息用于显示
    orphaned_spec_name = Column(String(200))  # 规格名称
    orphaned_spec_name_en = Column(String(200))  # 规格英文名称
    orphaned_spec_unit = Column(String(50))  # 单位
    orphaned_category_id = Column(Integer)  # 分类ID（用于按分类显示）

    # 关联关系
    configuration = relationship("ProductConfiguration", back_populates="config_values")
    template_item = relationship("SpecTemplateItem", back_populates="config_values")
    attachments = relationship("SpecAttachment", back_populates="config_value", cascade="all, delete-orphan",
                               foreign_keys="SpecAttachment.config_value_id")

    def __repr__(self):
        return f"<ProductConfigValue {self.template_item.spec_dict.name if self.template_item and self.template_item.spec_dict else 'N/A'}={self.value}>"

    def to_dict(self):
        return {
            'id': self.id,
            'configuration_id': self.configuration_id,
            'template_item_id': self.template_item_id,
            'definition_name': self.template_item.spec_dict.name if self.template_item and self.template_item.spec_dict else None,
            'value': self.value,
            'notes': self.notes
        }


class SpecAttachment(db.Model):
    """规格附件"""
    __tablename__ = 'spec_attachments'

    id = Column(Integer, primary_key=True)
    template_item_id = Column(Integer, ForeignKey('spec_template_items.id', ondelete='CASCADE'))
    config_value_id = Column(Integer, ForeignKey('product_config_values.id', ondelete='CASCADE'))
    file_name = Column(String(255), nullable=False)  # 文件名
    file_path = Column(String(500), nullable=False)  # 文件路径
    file_type = Column(String(50))  # 文件类型
    file_size = Column(Integer)  # 文件大小（字节）
    description = Column(String(500))  # 附件说明
    display_order = Column(Integer, default=0)
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    template_item = relationship("SpecTemplateItem", back_populates="attachments", foreign_keys=[template_item_id])
    config_value = relationship("ProductConfigValue", back_populates="attachments", foreign_keys=[config_value_id])
    uploader = relationship("User", foreign_keys=[uploaded_by])

    # 约束：必须关联到模板规格项或配置规格值之一
    __table_args__ = (
        CheckConstraint(
            '(template_item_id IS NOT NULL AND config_value_id IS NULL) OR '
            '(template_item_id IS NULL AND config_value_id IS NOT NULL)',
            name='chk_spec_attachments_ref'
        ),
    )

    def __repr__(self):
        return f"<SpecAttachment {self.file_name}>"

    @property
    def file_size_display(self):
        """获取文件大小显示文本"""
        if not self.file_size:
            return ''
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    def to_dict(self):
        return {
            'id': self.id,
            'template_item_id': self.template_item_id,
            'config_value_id': self.config_value_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_size_display': self.file_size_display,
            'description': self.description,
            'display_order': self.display_order,
            'uploader_name': self.uploader.real_name if self.uploader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 预置数据常量（PRODUCT_ID 已删除，其功能由系统元数据字段替代）
SPEC_CATEGORIES = [
    {'code': 'RF_PERFORMANCE', 'name': '射频性能', 'name_en': 'RF Performance', 'display_order': 1},
    {'code': 'ELECTRICAL', 'name': '电气规格', 'name_en': 'Electrical Specifications', 'display_order': 2},
    {'code': 'OPTICAL_PERFORMANCE', 'name': '光学性能', 'name_en': 'Optical Performance', 'display_order': 3},
    {'code': 'FEATURE_CONFIG', 'name': '功能配置', 'name_en': 'Feature Configuration', 'display_order': 4},
    {'code': 'ENV_RELIABILITY', 'name': '环境与可靠性', 'name_en': 'Environment & Reliability', 'display_order': 5},
    {'code': 'REGULATORY', 'name': '法规与认证', 'name_en': 'Regulatory & Certification', 'display_order': 6},
    {'code': 'MECHANICAL', 'name': '外观与机械', 'name_en': 'Appearance & Mechanical', 'display_order': 7},
    {'code': 'PACKAGING', 'name': '包装与配件', 'name_en': 'Packaging & Accessories', 'display_order': 8},
    {'code': 'SPARE_PARTS', 'name': '维修替换件', 'name_en': 'Spare Parts', 'display_order': 9},
]

CONFIG_STATUS = [
    ('development', '研发中'),
    ('prototype', '研发样机'),
    ('pilot', '小批量'),
    ('production', '可生产'),
    ('discontinued', '停产'),
]

REGIONS = [
    ('CN', '中国大陆'),
    ('TW', '中国台湾'),
    ('SG', '新加坡'),
    ('MY', '马来西亚'),
    ('TH', '泰国'),
    ('VN', '越南'),
    ('OTHER', '其他'),
]

# 常用测试方法预置数据
TEST_METHODS = [
    {'name': 'ETSI EN 300 113', 'description': 'RF测试标准', 'category': 'RF'},
    {'name': 'IEC 60068-2-1/2', 'description': '环境测试 - 低温/高温', 'category': 'ENV'},
    {'name': 'IEC 60529', 'description': '防护等级测试', 'category': 'ENV'},
    {'name': 'Telcordia SR-332', 'description': '可靠性预测标准', 'category': 'RELIABILITY'},
    {'name': 'EN 55032', 'description': 'EMC辐射测试', 'category': 'EMC'},
    {'name': 'EN 55035', 'description': 'EMC抗扰度测试', 'category': 'EMC'},
    {'name': 'IEC 62368-1', 'description': '安全测试标准', 'category': 'SAFETY'},
    {'name': 'RoHS 2.0', 'description': '有害物质限制', 'category': 'REGULATORY'},
]

# 常用测试条件预置数据
TEST_CONDITIONS = [
    {'name': 'Ta=25°C', 'description': '常温条件'},
    {'name': 'Ta=-20°C~+55°C', 'description': '工作温度范围'},
    {'name': 'Ta=-40°C~+85°C', 'description': '存储温度范围'},
    {'name': '非凝露', 'description': '湿度条件'},
    {'name': 'RH 5%~95%', 'description': '相对湿度范围'},
    {'name': 'Vin=AC220V±10%', 'description': 'AC220V供电'},
    {'name': 'Vin=AC110V±10%', 'description': 'AC110V供电'},
    {'name': 'Vin=DC48V±10%', 'description': 'DC48V供电'},
]

# ============================================
# MN编码生成相关常量
# ============================================

# 安全字符集（排除易混淆字符：0/O, 1/I/l, 5/S, 2/Z, Q）
# 参考：Crockford Base32、国际编码最佳实践
SAFE_CHARS = "346789ABCDEFGHJKLMNPRTUVWXY"

# 数字到安全字符的映射（0-9 → 安全字符）
DIGIT_TO_SAFE = {
    0: "3", 1: "4", 2: "6", 3: "7", 4: "8",
    5: "9", 6: "A", 7: "B", 8: "C", 9: "D"
}

# 编码位置结构说明
# 位置1: 区域编码（全局，来自 ProductCodeField.code_letter）
# 位置2: 分类编码（全局，来自 ProductCategory.code_letter）
# 位置3: 子分类编码（全局，来自 ProductSubcategory.code_letter）
# 位置4-13: 规格编码（子分类级，来自 SpecDefinition.code_options）
# 末位: 校验位（Mod-27算法）

# 编码快照版本（用于历史数据追溯）
CODE_RULE_VERSION = "V1.0"


def calculate_check_digit(code):
    """
    计算校验位（Mod-27算法，带位置权重）

    算法：
    1. 每个字符乘以其位置序号（1-based）
    2. 求和后对27取模
    3. 映射到安全字符

    Args:
        code: 编码字符串（不含校验位）

    Returns:
        str: 单个校验位字符
    """
    total = 0
    for i, char in enumerate(code):
        if char in SAFE_CHARS:
            total += (i + 1) * SAFE_CHARS.index(char)
    return SAFE_CHARS[total % len(SAFE_CHARS)]


def validate_code_with_check_digit(code):
    """
    验证带校验位的编码是否有效

    Args:
        code: 完整编码（含校验位）

    Returns:
        bool: 校验是否通过
    """
    if not code or len(code) < 2:
        return False
    main_code = code[:-1]
    check_digit = code[-1]
    return calculate_check_digit(main_code) == check_digit


def generate_safe_code_char(value, code_options):
    """
    根据规格值生成安全编码字符

    Args:
        value: 规格值
        code_options: 编码选项映射 {"规格值": "编码字符"}

    Returns:
        str: 编码字符，未找到映射时返回 "X"
    """
    if not code_options or not value:
        return "X"

    if value in code_options:
        raw_code = code_options[value]
        # 如果映射值已经是安全字符，直接返回
        if raw_code in SAFE_CHARS:
            return raw_code
        # 否则尝试转换
        try:
            idx = int(raw_code) % len(SAFE_CHARS)
            return SAFE_CHARS[idx]
        except (ValueError, TypeError):
            return raw_code[0] if raw_code else "X"

    return "X"  # 未知值用 X 填充
