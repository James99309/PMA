"""
产品关联模型 - 用于配置产品之间的关联关系

功能说明:
- 支持子分类级别和产品级别的关联配置
- 定义主产品与附加产品的依赖关系
- 用于报价单配置时自动提示配套产品

使用场景:
- 直放站 → 馈电模块（可选配件）
- 大功率基站 → 冷却风扇（必需配件）
- 基站 → 天线（必需配件，数量=4）

作者: Claude AI
创建日期: 2025-11-02
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app import db


class ProductRelation(db.Model):
    """产品关联配置模型"""
    __tablename__ = 'product_relations'

    # 关联类型常量
    REQUIRED_ACCESSORY = 'required_accessory'  # 必需配件
    OPTIONAL_ACCESSORY = 'optional_accessory'  # 可选配件
    RECOMMENDED = 'recommended'                # 推荐产品
    ALTERNATIVE = 'alternative'                # 替代产品

    # 主产品类型常量
    MAIN_TYPE_SUBCATEGORY = 'subcategory'  # 子分类级关联
    MAIN_TYPE_PRODUCT = 'product'          # 产品级关联

    id = Column(Integer, primary_key=True)
    main_product_type = Column(String(20), nullable=False)    # 'subcategory' 或 'product'
    main_product_id = Column(Integer, nullable=False)         # 子分类ID或产品ID
    related_product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    relation_type = Column(String(50), nullable=False)        # 关联类型
    display_name = Column(String(100), nullable=True)         # 显示名称（可选）
    default_quantity = Column(Integer, nullable=False, default=1)  # 默认数量
    is_required = Column(Boolean, nullable=False, default=False)   # 是否必选
    display_order = Column(Integer, nullable=False, default=0)     # 显示顺序
    is_active = Column(Boolean, nullable=False, default=True)      # 是否启用
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 互斥组相关字段
    mutual_exclusion_group = Column(String(100), nullable=True)  # 互斥组标识
    group_display_name = Column(String(200), nullable=True)      # 组显示名称
    is_group_required = Column(Boolean, nullable=True, default=False)  # 组是否必选
    group_selection_mode = Column(String(20), nullable=True, default='single')  # 选择模式
    is_default = Column(Boolean, nullable=True, default=False)   # 是否为默认选项

    # 关联关系
    related_product = relationship('Product', foreign_keys=[related_product_id], backref='relation_as_accessory')

    def __repr__(self):
        return f'<ProductRelation {self.main_product_type}:{self.main_product_id} -> Product:{self.related_product_id}>'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'main_product_type': self.main_product_type,
            'main_product_id': self.main_product_id,
            'related_product_id': self.related_product_id,
            'related_product': {
                'id': self.related_product.id,
                'name': self.related_product.name,
                'product_name': self.related_product.name,  # 完整产品名称
                'mn': self.related_product.product_mn,
                'product_mn': self.related_product.product_mn,  # 产品料号
                'model': self.related_product.model,  # 型号
                'product_model': self.related_product.model,  # 产品型号
                'brand': self.related_product.brand,  # 品牌
                'unit': self.related_product.unit,  # 单位
                'specification': self.related_product.specification,  # 规格描述
                'product_desc': self.related_product.specification,  # 产品描述
                'retail_price': self.related_product.retail_price,  # 零售价格
                'market_price': self.related_product.retail_price,  # 市场价格
                'category': self.related_product.category_name
            } if self.related_product else None,
            'relation_type': self.relation_type,
            'display_name': self.display_name or (self.related_product.name if self.related_product else ''),
            'default_quantity': self.default_quantity,
            'is_required': self.is_required,
            'display_order': self.display_order,
            'is_active': self.is_active
        }

    @classmethod
    def get_relations_for_product(cls, product_id):
        """
        获取产品的所有关联配置（包含子分类级和产品级）

        Args:
            product_id: 产品ID

        Returns:
            list: 关联配置列表，按display_order排序
        """
        from app.models.product import Product

        product = Product.query.get(product_id)
        if not product:
            return []

        relations = []

        # 1. 查询子分类级关联（通用配件）
        if product.subcategory_id:
            subcategory_relations = cls.query.filter_by(
                main_product_type=cls.MAIN_TYPE_SUBCATEGORY,
                main_product_id=product.subcategory_id,
                is_active=True
            ).all()
            relations.extend(subcategory_relations)

        # 2. 查询产品级关联（专属配件）
        product_relations = cls.query.filter_by(
            main_product_type=cls.MAIN_TYPE_PRODUCT,
            main_product_id=product_id,
            is_active=True
        ).all()
        relations.extend(product_relations)

        # 3. 按display_order排序
        relations.sort(key=lambda x: x.display_order)

        return relations

    @classmethod
    def get_products_using_accessory(cls, accessory_product_id):
        """
        反向查询：查询哪些产品/子分类使用了该配件

        Args:
            accessory_product_id: 配件产品ID

        Returns:
            dict: {
                'subcategories': [子分类关联列表],
                'products': [产品关联列表],
                'total_product_count': 总覆盖产品数
            }
        """
        from app.models.product import Product
        from app.models.product_code import ProductSubcategory

        relations = cls.query.filter_by(
            related_product_id=accessory_product_id,
            is_active=True
        ).all()

        result = {
            'subcategories': [],
            'products': [],
            'all_products': []
        }

        for relation in relations:
            if relation.main_product_type == cls.MAIN_TYPE_SUBCATEGORY:
                # 子分类级关联
                subcategory = ProductSubcategory.query.get(relation.main_product_id)
                if subcategory:
                    products = Product.query.filter_by(subcategory_id=subcategory.id).all()
                    result['subcategories'].append({
                        'relation': relation,
                        'subcategory': subcategory,
                        'product_count': len(products)
                    })
                    result['all_products'].extend(products)

            elif relation.main_product_type == cls.MAIN_TYPE_PRODUCT:
                # 产品级关联
                product = Product.query.get(relation.main_product_id)
                if product:
                    result['products'].append({
                        'relation': relation,
                        'product': product
                    })
                    result['all_products'].append(product)

        result['total_product_count'] = len(result['all_products'])

        return result

    @classmethod
    def get_relation_type_label(cls, relation_type):
        """获取关联类型的中文标签"""
        labels = {
            cls.REQUIRED_ACCESSORY: '必选',
            cls.OPTIONAL_ACCESSORY: '可选配件',
            cls.RECOMMENDED: '推荐',
            cls.ALTERNATIVE: '替代产品'
        }
        return labels.get(relation_type, relation_type)

    @classmethod
    def get_relation_type_badge_class(cls, relation_type):
        """获取关联类型的徽章样式类"""
        classes = {
            cls.REQUIRED_ACCESSORY: 'bg-danger',
            cls.OPTIONAL_ACCESSORY: 'bg-info',
            cls.RECOMMENDED: 'bg-success',
            cls.ALTERNATIVE: 'bg-warning'
        }
        return classes.get(relation_type, 'bg-secondary')

    @classmethod
    def get_mutual_exclusion_groups(cls, main_product_type, main_product_id):
        """
        获取指定主产品的所有互斥组配置

        Args:
            main_product_type: 主产品类型
            main_product_id: 主产品ID

        Returns:
            dict: {group_id: [relations]}
        """
        relations = cls.query.filter_by(
            main_product_type=main_product_type,
            main_product_id=main_product_id,
            is_active=True
        ).filter(
            cls.mutual_exclusion_group.isnot(None)
        ).all()

        # 按互斥组分组
        groups = {}
        for relation in relations:
            group_id = relation.mutual_exclusion_group
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(relation)

        return groups

    def is_in_mutual_exclusion_group(self):
        """判断是否属于互斥组"""
        return self.mutual_exclusion_group is not None and self.mutual_exclusion_group != ''
