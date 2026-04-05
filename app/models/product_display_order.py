from app import db
from datetime import datetime


class ProductDisplayOrder(db.Model):
    """产品展示排序表 - 使用自然键，可跨 CN/SG 数据库移植

    存储三层排序：分类 → 子分类 → 型号
    CN 端管理排序，通过 cross-sync 同步到 SG
    """
    __tablename__ = 'product_display_order'

    id = db.Column(db.Integer, primary_key=True)
    category_code = db.Column(db.String(1), nullable=False)
    category_order = db.Column(db.Integer, nullable=False, default=0)
    subcategory_code = db.Column(db.String(1), nullable=False)
    subcategory_order = db.Column(db.Integer, nullable=False, default=0)
    model = db.Column(db.String(100), nullable=False)
    model_order = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('category_code', 'subcategory_code', 'model',
                            name='uq_display_order_cat_sub_model'),
        db.Index('ix_display_order_cat_sub', 'category_code', 'subcategory_code'),
    )

    def to_dict(self):
        return {
            'category_code': self.category_code,
            'category_order': self.category_order,
            'subcategory_code': self.subcategory_code,
            'subcategory_order': self.subcategory_order,
            'model': self.model,
            'model_order': self.model_order,
        }
