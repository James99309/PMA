class ProductCategory(db.Model):
    """产品分类模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code_letter = db.Column(db.String(1), nullable=False, unique=True)
    
    # 关系
    subcategories = db.relationship('ProductSubcategory', backref='category', lazy='dynamic')
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<ProductCategory {self.name}>'


class ProductSubcategory(db.Model):
    """产品子类模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code_letter = db.Column(db.String(1), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=False)
    
    # 关系
    fields = db.relationship('ProductCodeField', backref='subcategory', lazy='dynamic')
    products = db.relationship('Product', backref='subcategory', lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('category_id', 'code_letter', name='_category_code_letter_uc'),
    )
    
    def __repr__(self):
        return f'<ProductSubcategory {self.name}>'


class ProductCodeField(db.Model):
    """产品编码字段模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='text')  # text, number, select, origin_location
    max_length = db.Column(db.Integer, default=1)
    required = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('product_subcategory.id'), nullable=False)
    use_in_code = db.Column(db.Boolean, default=False)  # 是否用于产品编码
    
    # 关系
    options = db.relationship('FieldOption', backref='field', lazy='dynamic', cascade='all, delete-orphan')
    field_values = db.relationship('CodeFieldValue', backref='field', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ProductCodeField {self.name}>'


class FieldOption(db.Model):
    """字段选项模型"""
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('product_code_field.id'), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    
    # 关系
    field_values = db.relationship('CodeFieldValue', backref='option', lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('field_id', 'code', name='_field_code_uc'),
    )
    
    def __repr__(self):
        return f'<FieldOption {self.value}>'


class CodeFieldValue(db.Model):
    """产品编码字段值模型"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('product_code_field.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('field_option.id'), nullable=True)
    text_value = db.Column(db.String(100), nullable=True)
    
    __table_args__ = (
        db.UniqueConstraint('product_id', 'field_id', name='_product_field_uc'),
    )
    
    def __repr__(self):
        return f'<CodeFieldValue {self.id}>'


# 更新产品模型
class Product(db.Model):
    # ... existing code ...
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=True)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('product_subcategory.id'), nullable=True)
    product_code = db.Column(db.String(50), unique=True, nullable=True)
    
    # 关系
    field_values = db.relationship('CodeFieldValue', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    # ... existing code ... 