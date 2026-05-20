from app import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))  # 产品类型
    category = db.Column(db.String(50))  # 产品类别(如"基站")
    product_mn = db.Column(db.String(50), unique=True)  # 产品型号编码(MN)
    serial_code = db.Column(db.String(10), unique=True, nullable=True)  # 序列号编码(5字符)，用于产品序列号生成
    product_name = db.Column(db.String(100))  # 产品名称
    model = db.Column(db.String(100))  # 具体型号
    specification = db.Column(db.Text)  # 规格说明
    brand = db.Column(db.String(50))  # 品牌
    unit = db.Column(db.String(20))  # 单位（中文）
    unit_en = db.Column(db.String(20))  # 单位（英文）
    retail_price = db.Column(db.Numeric(10, 2))  # 市场单价
    currency = db.Column(db.String(10), default='CNY')  # 货币类型
    status = db.Column(db.String(20), default='active')  # 产品状态：'active'(生产中), 'discontinued'(已停产), 'upcoming'(待上市)
    image_path = db.Column(db.String(255))  # 产品图片路径
    pdf_path = db.Column(db.String(255))  # 产品PDF文件路径
    icon_svg = db.Column(db.Text, comment='产品SVG图标数据')

    # 厂商产品标记字段
    is_vendor_product = db.Column(db.Boolean, default=False)  # 是否为厂商产品（用于植入合计统计）

    # SN 管理开关:False 则发货时跳过 SN 输入(如耦合器、功分器等小附件)
    has_serial_number = db.Column(db.Boolean, default=True, nullable=False, server_default='true')

    # MN编码锁定标记字段
    is_mn_locked = db.Column(db.Boolean, default=False)  # MN编码是否锁定（锁定后不可修改MN和分类）

    # 产品编码定义快照字段
    code_definition_snapshot = db.Column(db.JSON)  # 编码生成时的完整定义快照（避免编码表变化导致历史数据丢失）

    # 规格自动生成的MN编码
    spec_mn = db.Column(db.String(50))  # 根据规格自动计算的MN编码

    # 产品分类体系字段（与研发库一致）
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('product_subcategories.id'))
    region_id = db.Column(db.Integer, db.ForeignKey('product_code_fields.id'))

    # 产品来源字段
    source_type = db.Column(db.String(20))  # 'manual'(手动创建) 或 'from_dev'(研发产品化)
    source_dev_product_id = db.Column(db.Integer, db.ForeignKey('dev_products.id'))  # 来源研发产品ID
    source_configuration_id = db.Column(db.Integer, db.ForeignKey('product_configurations.id'))  # 来源配置版本ID（本地）
    productized_at = db.Column(db.DateTime)  # 产品化时间

    # 积分系数
    points_coefficient_override = db.Column(db.Numeric(3, 1), nullable=True, comment='手动积分系数(Admin设置,NULL=按引用频次自动)')
    points_coefficient_override_at = db.Column(db.DateTime, nullable=True, comment='手动系数设置时间')

    # 引用频次系数（批量预计算）
    citation_coefficient = db.Column(db.Numeric(4, 2), nullable=True, comment='引用频率积分系数')
    citation_count = db.Column(db.Integer, nullable=True, comment='过去12个月引用次数')

    # 软删除
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 所有者字段（关联到用户表）
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref=db.backref('products', lazy='dynamic'))

    # 分类体系关联关系（使用_obj后缀避免与旧字段名冲突）
    category_obj = db.relationship('ProductCategory', foreign_keys=[category_id], backref='products')
    subcategory_obj = db.relationship('ProductSubcategory', foreign_keys=[subcategory_id], backref='products')
    region_obj = db.relationship('ProductCodeField', foreign_keys=[region_id], backref='products')
    source_dev_product = db.relationship('DevProduct', foreign_keys=[source_dev_product_id], backref='productized_products')
    source_configuration = db.relationship('ProductConfiguration', foreign_keys=[source_configuration_id], backref='productized_products')

    @property
    def name(self):
        """获取产品名称（优先使用新字段，回退到旧字段）

        新字段: subcategory_obj.name (通过外键关联)
        旧字段: product_name (直接存储的字符串)

        Returns:
            str: 产品名称
        """
        if self.subcategory_obj:
            return self.subcategory_obj.name
        return self.product_name or ''

    @property
    def name_en(self):
        """获取产品的英文名称

        优先返回关联 ProductSubcategory 的英文名称

        Returns:
            str: 产品英文名称，或 None 如果没有关联的子分类或英文名称
        """
        if self.subcategory_obj and self.subcategory_obj.name_en:
            return self.subcategory_obj.name_en
        return None

    @property
    def category_name(self):
        """获取产品分类名称（优先使用新字段，回退到旧字段）

        新字段: category_obj.name (通过外键关联)
        旧字段: category (直接存储的字符串)

        Returns:
            str: 产品分类名称
        """
        if self.category_obj:
            return self.category_obj.name
        return self.category or ''

    @property
    def category_name_en(self):
        """获取分类的英文名称"""
        if self.category_obj and self.category_obj.name_en:
            return self.category_obj.name_en
        return None

    @property
    def subcategory_name_en(self):
        """获取子分类的英文名称"""
        if self.subcategory_obj and self.subcategory_obj.name_en:
            return self.subcategory_obj.name_en
        return None

    @property
    def display_mn(self):
        """返回显示用的MN编号

        显示逻辑：
        - 如果没有规格MN：返回产品MN
        - 如果没有产品MN或两者相同：返回规格MN
        - 如果两者不同：返回 "产品MN [规格MN]" 格式

        Returns:
            str: 显示用的MN编号
        """
        if not self.spec_mn:
            return self.product_mn or ''
        if not self.product_mn or self.product_mn == self.spec_mn:
            return self.spec_mn
        return f"{self.product_mn} [{self.spec_mn}]"

    def __repr__(self):
        return f'<Product {self.name} ({self.product_mn})>'

    def get_specs_from_configuration(self):
        """从关联的配置版本获取规格数据

        Returns:
            dict: 按分类组织的规格数据
            {
                category_id: {
                    'category': SpecCategory对象,
                    'items': [{
                        'name': 规格名称,
                        'name_en': 英文名称,
                        'unit': 单位,
                        'value': 规格值（配置值或通用值）,
                        'test_condition': 测试条件,
                        'test_method': 测试方法
                    }, ...]
                }
            }
        """
        if not self.source_configuration:
            return {}

        config = self.source_configuration
        template = config.template
        if not template:
            return {}

        result = {}
        for item in template.items:
            if not item.spec_dict:
                continue

            cat_id = item.spec_dict.category_id
            if cat_id not in result:
                result[cat_id] = {
                    'category': item.spec_dict.category,
                    'items': []
                }

            # 获取配置值，如果没有则使用通用值
            value = config.get_spec_value(item.id)

            # 获取测试条件
            test_condition = None
            if item.test_condition:
                test_condition = item.test_condition.name
            elif item.test_condition_text:
                test_condition = item.test_condition_text

            # 获取测试方法
            test_method = None
            if item.test_method:
                test_method = item.test_method.name
            elif item.test_method_text:
                test_method = item.test_method_text

            result[cat_id]['items'].append({
                'name': item.spec_dict.name,
                'name_en': item.spec_dict.name_en,
                'unit': item.spec_dict.unit,
                'value': value,
                'test_condition': test_condition,
                'test_method': test_method,
                'is_required': item.is_required
            })

        return result

    @property
    def has_configuration_specs(self):
        """检查是否使用新的配置版本规格系统"""
        return self.source_configuration_id is not None

    @property
    def points_coefficient(self):
        """积分系数：手动覆盖 > 预计算引用系数 > 回退默认值"""
        if self.points_coefficient_override is not None:
            return float(self.points_coefficient_override)
        if self.citation_coefficient is not None:
            return float(self.citation_coefficient)
        return 3.0

    @property
    def points(self):
        """积分 = 系数 × retail_price"""
        if not self.retail_price:
            return 0
        return round(self.points_coefficient * float(self.retail_price))

    @property
    def points_tier(self):
        """积分等级: 'gold' / 'silver' / 'bronze'"""
        from app.helpers.product_points import get_points_tier
        return get_points_tier(self.points)