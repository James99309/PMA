"""
产品显示顺序排序工具

将 ProductDisplayOrder 三级排序（分类→子分类→型号）封装为可复用函数。
使用 code_definition_snapshot JSON 字段提取分类代码，无需额外 join
ProductCategory / ProductSubcategory 表。
"""
from sqlalchemy import func, and_
from app import db
from app.models.product import Product
from app.models.product_display_order import ProductDisplayOrder


def apply_product_display_sort(query, tiebreakers=None):
    """
    对 Product query 应用 ProductDisplayOrder 三级排序（分类→子分类→型号）。

    逐级匹配，互不绑定：
      - 分类顺序：按 category_code 取（与型号无关）
      - 子分类顺序：按 (category_code, subcategory_code) 取
      - 型号顺序：按 (category_code, subcategory_code, model) 精确取

    这样新引入的型号（排序表里还没有该型号行）仍能排进自己的分类+子分类，
    只是落在该子分类的末尾（model_order 缺省 9999），而不是整个列表最后。

    :param query:       Product 表的 SQLAlchemy query
    :param tiebreakers: 额外的 order_by 列，默认 [product_name asc, id asc]
    :return:            追加了 outerjoin + order_by 的 query
    """
    snap_cat = func.json_extract_path_text(
        Product.code_definition_snapshot, 'category', 'code_letter'
    )
    snap_sub = func.json_extract_path_text(
        Product.code_definition_snapshot, 'subcategory', 'code_letter'
    )
    eff_model = func.coalesce(Product.model, Product.product_name, '未指定型号')

    # 分类级排序值（category_code → category_order）
    cat_sq = db.session.query(
        ProductDisplayOrder.category_code.label('cc'),
        func.min(ProductDisplayOrder.category_order).label('category_order'),
    ).group_by(ProductDisplayOrder.category_code).subquery()

    # 子分类级排序值（(category_code, subcategory_code) → subcategory_order）
    sub_sq = db.session.query(
        ProductDisplayOrder.category_code.label('cc'),
        ProductDisplayOrder.subcategory_code.label('sc'),
        func.min(ProductDisplayOrder.subcategory_order).label('subcategory_order'),
    ).group_by(
        ProductDisplayOrder.category_code, ProductDisplayOrder.subcategory_code
    ).subquery()

    return query.outerjoin(
        cat_sq, snap_cat == cat_sq.c.cc
    ).outerjoin(
        sub_sq, and_(snap_cat == sub_sq.c.cc, snap_sub == sub_sq.c.sc)
    ).outerjoin(
        ProductDisplayOrder,
        and_(
            snap_cat == ProductDisplayOrder.category_code,
            snap_sub == ProductDisplayOrder.subcategory_code,
            eff_model == ProductDisplayOrder.model,
        )
    ).order_by(
        func.coalesce(cat_sq.c.category_order, 9999).asc(),
        func.coalesce(sub_sq.c.subcategory_order, 9999).asc(),
        func.coalesce(ProductDisplayOrder.model_order, 9999).asc(),
        *(tiebreakers or [Product.product_name.asc(), Product.id.asc()])
    )
