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
    status = db.Column(db.String(20), default='active')  # 产品状态：'active'(生产中), 'discontinued'(已停产), 'upcoming'(待上市)
    image_path = db.Column(db.String(255))  # 产品图片路径
    pdf_path = db.Column(db.String(255))  # 产品PDF文件路径
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 所有者字段（关联到用户表）
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref=db.backref('products', lazy='dynamic'))

    def __repr__(self):
        return f'<Product {self.product_name} ({self.product_mn})>' 