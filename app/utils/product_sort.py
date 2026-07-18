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
    对 Product query 应用 ProductDisplayOrder 四级排序（分类→子分类→名称→型号）。

    逐级匹配，互不绑定：
      - 分类顺序：按 category_code 取（与型号无关）
      - 子分类顺序：按 (category_code, subcategory_code) 取
      - 名称组顺序：同名（product_name）的型号聚成一组，组位置 = 该名称下型号的
        最小 model_order（从现有型号顺序推导，不额外维护名称顺序）
      - 型号顺序：组内按 (category_code, subcategory_code, model) 精确取

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

    # 名称组排序值：把型号顺序(model_order)映射到它所属的名称，取该名称下最小 model_order。
    # ProductDisplayOrder 只有 model，没有名称，故 join Product 拿 product_name。
    _p = db.aliased(Product)
    _p_cat = func.json_extract_path_text(_p.code_definition_snapshot, 'category', 'code_letter')
    _p_sub = func.json_extract_path_text(_p.code_definition_snapshot, 'subcategory', 'code_letter')
    _p_model = func.coalesce(_p.model, _p.product_name, '未指定型号')
    name_sq = db.session.query(
        ProductDisplayOrder.category_code.label('cc'),
        ProductDisplayOrder.subcategory_code.label('sc'),
        _p.product_name.label('pname'),
        func.min(ProductDisplayOrder.model_order).label('name_order'),
    ).join(
        _p,
        and_(
            _p_cat == ProductDisplayOrder.category_code,
            _p_sub == ProductDisplayOrder.subcategory_code,
            _p_model == ProductDisplayOrder.model,
        )
    ).group_by(
        ProductDisplayOrder.category_code, ProductDisplayOrder.subcategory_code, _p.product_name
    ).subquery()

    return query.outerjoin(
        cat_sq, snap_cat == cat_sq.c.cc
    ).outerjoin(
        sub_sq, and_(snap_cat == sub_sq.c.cc, snap_sub == sub_sq.c.sc)
    ).outerjoin(
        name_sq,
        and_(snap_cat == name_sq.c.cc, snap_sub == name_sq.c.sc,
             Product.product_name == name_sq.c.pname)
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
        func.coalesce(name_sq.c.name_order, 9999).asc(),   # 名称组（同名聚合，组按最小型号序）
        Product.product_name.asc(),                        # 同名内确定次序 / 同序名称间稳定
        func.coalesce(ProductDisplayOrder.model_order, 9999).asc(),  # 组内型号顺序
        *(tiebreakers or [Product.product_name.asc(), Product.id.asc()])
    )
