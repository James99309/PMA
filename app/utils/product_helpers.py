"""产品查询辅助函数

提供统一的产品查询方法，支持新旧product_name字段的兼容查询
同时提供产品编码定义快照生成功能
"""
from sqlalchemy import or_
from app.models.product import Product
from app.models.product_code import ProductSubcategory
from datetime import datetime
from flask import current_app


def find_product_by_name_and_model(product_name, model):
    """根据产品名称和型号查找产品（兼容新旧字段）

    Args:
        product_name (str): 产品名称
        model (str): 产品型号

    Returns:
        Product|None: 匹配的产品对象，未找到返回None

    查询逻辑：
    - 优先匹配 subcategory_obj.name (新字段)
    - 回退匹配 product_name (旧字段)
    """
    if not product_name or not model:
        return None

    return Product.query\
        .outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)\
        .filter(
            or_(
                ProductSubcategory.name == product_name,
                Product.product_name == product_name
            ),
            Product.model == model
        ).first()


def find_product_by_name(product_name):
    """根据产品名称查找产品（兼容新旧字段）

    Args:
        product_name (str): 产品名称

    Returns:
        Product|None: 匹配的第一个产品对象，未找到返回None

    注意：如果有多个同名产品，只返回第一个
    """
    if not product_name:
        return None

    return Product.query\
        .outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)\
        .filter(
            or_(
                ProductSubcategory.name == product_name,
                Product.product_name == product_name
            )
        ).first()


def get_products_by_name(product_name):
    """根据产品名称获取所有匹配的产品（兼容新旧字段）

    Args:
        product_name (str): 产品名称

    Returns:
        list[Product]: 匹配的所有产品对象列表

    用途：获取某个产品名称下的所有型号
    """
    if not product_name:
        return []

    return Product.query\
        .outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)\
        .filter(
            or_(
                ProductSubcategory.name == product_name,
                Product.product_name == product_name
            )
        ).all()


def build_product_name_filter(query, product_name_value, search_mode='exact'):
    """为查询添加产品名称筛选条件（兼容新旧字段）

    Args:
        query: SQLAlchemy查询对象
        product_name_value (str): 产品名称值
        search_mode (str): 搜索模式，'exact'精确匹配 或 'like'模糊搜索

    Returns:
        Query: 添加了筛选条件的查询对象

    用途：在复杂查询中添加产品名称筛选
    """
    if not product_name_value:
        return query

    # 确保已经join ProductSubcategory
    query = query.outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)

    if search_mode == 'like':
        search_term = f'%{product_name_value}%'
        return query.filter(
            or_(
                ProductSubcategory.name.ilike(search_term),
                Product.product_name.ilike(search_term)
            )
        )
    else:  # exact
        return query.filter(
            or_(
                ProductSubcategory.name == product_name_value,
                Product.product_name == product_name_value
            )
        )


def generate_product_snapshot(product, source="manual", dev_product=None):
    """
    生成产品编码定义快照（通用函数）

    从研发产品入库逻辑中提取的通用快照生成函数，
    可用于研发入库、手动创建、手动编辑等所有场景。

    Args:
        product: Product对象（标准产品），必须已保存到数据库且有ID
        source: 快照来源，可选值：
                - "dev_product": 研发产品入库
                - "manual_create": 手动创建
                - "manual_update": 手动编辑更新
        dev_product: DevProduct对象（可选，仅研发入库时提供）

    Returns:
        dict | None: 快照数据字典，失败返回None

    快照格式：
        {
            "version": "1.0",
            "source": "manual_create",
            "generated_at": "2025-11-14T12:00:00",
            "full_code": "BC4I2X4NN",
            "category": {...},
            "subcategory": {...},
            "code_parts": [...]
        }
    """
    try:
        from app.models.product_spec import ProductSpec
        from app.models.product_code import ProductCodeField
        from app.routes.product_code import get_field_unit

        # 构建快照基础结构
        snapshot = {
            "version": "1.0",
            "source": source,
            "generated_at": datetime.utcnow().isoformat(),
            "full_code": product.product_mn,
            "category": {
                "id": product.category_id,
                "name": product.category_obj.name if product.category_obj else "",
                "code_letter": product.category_obj.code_letter if product.category_obj else ""
            },
            "subcategory": {
                "id": product.subcategory_id,
                "name": product.subcategory_obj.name if product.subcategory_obj else "",
                "code_letter": product.subcategory_obj.code_letter if product.subcategory_obj else ""
            },
            "code_parts": []
        }

        # 如果提供了研发产品，记录其ID（用于追溯）
        if dev_product:
            snapshot["dev_product_id"] = dev_product.id

        # 从ProductSpec读取规格数据
        # 注意：这里读取的是标准产品的规格表，研发入库时已经复制过来了
        specs = ProductSpec.query.filter_by(
            product_id=product.id
        ).order_by(ProductSpec.id).all()

        # 添加所有规格到快照（包括编码规格和非编码规格）
        # use_in_code 字段用于区分：True=编码规格，False=非编码规格
        position = 1
        for spec in specs:
            # 查询字段定义，获取 use_in_code 值
            field_def = ProductCodeField.query.filter_by(
                subcategory_id=product.subcategory_id,
                name=spec.field_name,
                field_type='spec'
            ).first()

            # 查询规格单位
            unit = get_field_unit(spec.field_name)

            # 判断是否为编码规格
            use_in_code = field_def.use_in_code if field_def else bool(spec.field_code and spec.field_code.strip())

            snapshot["code_parts"].append({
                "position": position,
                "field_name": spec.field_name,
                "field_code": spec.field_code if spec.field_code else "",
                "code": spec.field_code if spec.field_code else "",
                "value": spec.field_value if spec.field_value else "",
                "unit": unit,
                "use_in_code": use_in_code,
                "description": ""
            })
            position += 1

        current_app.logger.info(
            f"生成编码定义快照成功: 产品ID={product.id}, "
            f"MN={product.product_mn}, 规格字段数={len(snapshot['code_parts'])}"
        )

        return snapshot

    except Exception as e:
        current_app.logger.error(f"编码快照生成失败: 产品ID={product.id}, 错误={str(e)}")
        return None
