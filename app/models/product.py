from app import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))  # 产品类型
    category = db.Column(db.String(50))  # 产品类别(如"基站")
    product_mn = db.Column(db.String(50), unique=True)  # 产品型号编码(MN)
    product_name = db.Column(db.String(100))  # 产品名称
    model = db.Column(db.String(100))  # 具体型号
    specification = db.Column(db.Text)  # 规格说明
    brand = db.Column(db.String(50))  # 品牌
    unit = db.Column(db.String(20))  # 单位(Set)
    retail_price = db.Column(db.Numeric(10, 2))  # 市场单价
    currency = db.Column(db.String(10), default='CNY')  # 货币类型
    status = db.Column(db.String(20), default='active')  # 产品状态：'active'(生产中), 'discontinued'(已停产), 'upcoming'(待上市)
    image_path = db.Column(db.String(255))  # 产品图片路径
    pdf_path = db.Column(db.String(255))  # 产品PDF文件路径
    
    # 厂商产品标记字段
    is_vendor_product = db.Column(db.Boolean, default=False)  # 是否为厂商产品（用于植入合计统计）

    # MN编码锁定标记字段
    is_mn_locked = db.Column(db.Boolean, default=False)  # MN编码是否锁定（锁定后不可修改MN和分类）

    # 产品编码定义快照字段
    code_definition_snapshot = db.Column(db.JSON)  # 编码生成时的完整定义快照（避免编码表变化导致历史数据丢失）

    # 产品分类体系字段（与研发库一致）
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('product_subcategories.id'))
    region_id = db.Column(db.Integer, db.ForeignKey('product_code_fields.id'))

    # 产品来源字段
    source_type = db.Column(db.String(20))  # 'manual'(手动创建) 或 'from_dev'(研发产品化)
    source_dev_product_id = db.Column(db.Integer, db.ForeignKey('dev_products.id'))  # 来源研发产品ID
    productized_at = db.Column(db.DateTime)  # 产品化时间

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

    def __repr__(self):
        return f'<Product {self.name} ({self.product_mn})>' 