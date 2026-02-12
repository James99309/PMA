"""产品查询辅助函数

提供统一的产品查询方法，支持新旧product_name字段的兼容查询
同时提供产品编码定义快照生成功能和三级文件引用获取功能
"""
from sqlalchemy import or_
from app.models.product import Product
from app.models.product_code import ProductSubcategory
from datetime import datetime
from flask import current_app


def get_effective_file(product, file_type='image'):
    """
    获取产品的有效文件路径（三级引用：产品自身 > 同名产品 > 子分类）

    Args:
        product: Product对象
        file_type: 'image' 或 'pdf'

    Returns:
        str | None: 有效的文件路径
    """
    # 确定字段名
    if file_type == 'image':
        product_field = product.image_path
        model_field = Product.image_path
    else:
        product_field = product.pdf_path
        model_field = Product.pdf_path

    # 优先级1：产品自身文件
    if product_field:
        return product_field

    # 优先级2：同一子分类下相同product_name的产品
    if product.product_name and product.subcategory_id:
        sibling = Product.query.filter(
            Product.subcategory_id == product.subcategory_id,
            Product.product_name == product.product_name,
            Product.id != product.id,
            model_field.isnot(None),
            model_field != ''
        ).first()
        if sibling:
            sibling_file = sibling.image_path if file_type == 'image' else sibling.pdf_path
            return sibling_file

    # 优先级3：子分类共享文件
    if product.subcategory_obj:
        subcategory_field = product.subcategory_obj.image_path if file_type == 'image' else product.subcategory_obj.pdf_path
        if subcategory_field:
            return subcategory_field

    return None


def get_effective_image(product):
    """获取产品的有效图片路径（三级引用）"""
    return get_effective_file(product, 'image')


def get_effective_pdf(product):
    """获取产品的有效PDF路径（三级引用）"""
    return get_effective_file(product, 'pdf')


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
        from app.models.spec_template import SpecDefinition, SpecCategory

        # 构建快照基础结构
        # 注意: full_code 字段已废弃，保留仅为兼容旧代码
        # 真正的规格MN应使用 product.spec_mn 字段
        snapshot = {
            "version": "1.0",
            "source": source,
            "generated_at": datetime.utcnow().isoformat(),
            "full_code": product.spec_mn or product.product_mn,  # 废弃字段，优先使用spec_mn
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
        specs = ProductSpec.query.filter_by(
            product_id=product.id
        ).all()

        # 批量查询所有 SpecDefinition（含 category 关联），按 field_name 建索引
        spec_names = [s.field_name for s in specs if s.field_name]
        definitions = SpecDefinition.query.filter(
            SpecDefinition.name.in_(spec_names)
        ).all() if spec_names else []
        name_to_def = {d.name: d for d in definitions}

        # 预加载分类的 display_order
        cat_ids = {d.category_id for d in definitions if d.category_id}
        categories = SpecCategory.query.filter(
            SpecCategory.id.in_(cat_ids)
        ).all() if cat_ids else []
        cat_order_map = {c.id: c.display_order for c in categories}

        # 按 SpecCategory.display_order → SpecDefinition.display_order 排序
        def sort_key(spec):
            defn = name_to_def.get(spec.field_name)
            if defn:
                cat_order = cat_order_map.get(defn.category_id, 9999)
                return (0, cat_order, defn.display_order)
            return (1, 9999, 9999)

        specs_sorted = sorted(specs, key=sort_key)

        # 构建 code_parts
        for idx, spec in enumerate(specs_sorted):
            defn = name_to_def.get(spec.field_name)
            # use_in_code: 有 field_code 即参与编码
            use_in_code = bool(spec.field_code and spec.field_code.strip())
            unit = defn.unit if defn else None

            snapshot["code_parts"].append({
                "position": idx,
                "field_name": spec.field_name,
                "field_code": spec.field_code if spec.field_code else "",
                "code": spec.field_code if spec.field_code else "",
                "value": spec.field_value if spec.field_value else "",
                "unit": unit or "",
                "use_in_code": use_in_code,
                "description": ""
            })

        current_app.logger.info(
            f"生成编码定义快照成功: 产品ID={product.id}, "
            f"MN={product.product_mn}, 规格字段数={len(snapshot['code_parts'])}"
        )

        return snapshot

    except Exception as e:
        current_app.logger.error(f"编码快照生成失败: 产品ID={product.id}, 错误={str(e)}")
        return None


def generate_spec_mn(product):
    """
    根据产品规格生成规格MN编码（支持 Product 和 DevProduct）

    读取产品的规格数据，按照编码规则生成规格MN。
    格式：区域编码 + 分类编码 + 子分类编码 + 规格编码序列

    Args:
        product: Product 或 DevProduct 对象，必须已保存到数据库且有ID

    Returns:
        str | None: 生成的规格MN编码，失败返回None
    """
    try:
        from app.models.product_code import ProductCodeField

        # 自动检测模型类型，适配不同的属性名
        # Product 使用 category_obj, subcategory_obj, region_obj
        # DevProduct 使用 category, subcategory, region
        is_dev_product = hasattr(product, 'category') and not hasattr(product, 'category_obj')

        if is_dev_product:
            from app.models.dev_product import DevProductSpec
            SpecModel = DevProductSpec
            spec_id_field = 'dev_product_id'
            category_rel = product.category
            subcategory_rel = product.subcategory
            region_rel = product.region
        else:
            from app.models.product_spec import ProductSpec
            SpecModel = ProductSpec
            spec_id_field = 'product_id'
            category_rel = product.category_obj
            subcategory_rel = product.subcategory_obj
            region_rel = product.region_obj

        # 验证必要的分类信息
        if not category_rel or not subcategory_rel:
            current_app.logger.warning(
                f"无法生成规格MN: 产品ID={product.id}缺少分类信息"
            )
            return None

        # 获取区域编码
        region_code = ""
        if region_rel:
            region_code = region_rel.code or ""
            # 处理"?"情况
            if region_code == "?":
                from app.models.product_code import ProductCodeFieldOption
                option = ProductCodeFieldOption.query.filter_by(
                    field_id=region_rel.id
                ).first()
                region_code = option.code if option else "0"

        # 获取分类和子分类编码
        category_code = category_rel.code_letter or ""
        subcategory_code = subcategory_rel.code_letter or ""

        # 获取产品规格
        filter_kwargs = {spec_id_field: product.id}
        if is_dev_product:
            specs = SpecModel.query.filter_by(**filter_kwargs).all()
        else:
            specs = SpecModel.query.filter_by(**filter_kwargs).order_by(
                SpecModel.display_order, SpecModel.id
            ).all()

        # 收集规格编码数据
        specs_data = []
        for spec in specs:
            # 查询字段定义，获取position
            # 编码定义由分类级和子分类级两部分组成：
            # - 分类级字段：category_id有值，subcategory_id为None
            # - 子分类级字段：subcategory_id有值

            # 查询分类级字段
            cat_field = ProductCodeField.query.filter_by(
                category_id=product.category_id,
                subcategory_id=None,
                name=spec.field_name,
                field_type='spec'
            ).first()

            # 查询子分类级字段
            subcat_field = ProductCodeField.query.filter_by(
                subcategory_id=product.subcategory_id,
                name=spec.field_name,
                field_type='spec'
            ).first()

            # 优先使用子分类级，回退到分类级
            field_def = subcat_field or cat_field

            # 只处理参与编码的规格（use_in_code=True）且有编码值的规格
            current_app.logger.debug(
                f"规格检查: {spec.field_name}, field_code={spec.field_code}, "
                f"field_def={field_def is not None}, use_in_code={field_def.use_in_code if field_def else 'N/A'}"
            )
            if field_def and field_def.use_in_code and spec.field_code and spec.field_code.strip():
                position = field_def.position if field_def else 999
                specs_data.append({
                    'position': position,
                    'code': spec.field_code.strip()
                })
                current_app.logger.debug(f"添加规格编码: position={position}, code={spec.field_code.strip()}")

        # 按position排序
        specs_data.sort(key=lambda x: x.get('position', 999))

        # 提取前10个规格编码
        spec_codes = [s.get('code', '0') for s in specs_data[:10]]

        # 去掉末尾的'0'
        while spec_codes and spec_codes[-1] == '0':
            spec_codes.pop()

        # 生成规格MN：区域 + 分类 + 子分类 + 规格编码
        spec_mn = f"{region_code}{category_code}{subcategory_code}{''.join(spec_codes)}"

        product_type_str = "研发产品" if is_dev_product else "产品"
        current_app.logger.debug(
            f"生成{product_type_str}MN成功: 产品ID={product.id}, spec_mn={spec_mn}"
        )

        return spec_mn if spec_mn else None

    except Exception as e:
        current_app.logger.error(
            f"生成规格MN失败: 产品ID={product.id}, 错误={str(e)}"
        )
        return None


# 为兼容性保留别名
generate_dev_product_mn = generate_spec_mn


def calculate_spec_mn_from_data(product, specs_data):
    """
    根据提供的规格数据计算规格MN编码（不查询数据库中的规格）

    用于预览功能，在保存前计算新的spec_mn。

    Args:
        product: Product对象
        specs_data: 规格数据列表 [{'field_name': str, 'field_value': str, 'field_code': str}, ...]

    Returns:
        str | None: 计算的规格MN编码，失败返回None
    """
    try:
        from app.models.product_code import ProductCodeField

        # 验证必要的分类信息
        if not product.category_obj or not product.subcategory_obj:
            current_app.logger.warning(
                f"无法计算规格MN: 产品ID={product.id}缺少分类信息"
            )
            return None

        # 获取区域编码
        region_code = ""
        if product.region_obj:
            region_code = product.region_obj.code or ""
            if region_code == "?":
                from app.models.product_code import ProductCodeFieldOption
                option = ProductCodeFieldOption.query.filter_by(
                    field_id=product.region_obj.id
                ).first()
                region_code = option.code if option else "0"

        # 获取分类和子分类编码
        category_code = product.category_obj.code_letter or ""
        subcategory_code = product.subcategory_obj.code_letter or ""

        # 收集规格编码数据
        specs_code_data = []
        for spec_data in specs_data:
            field_name = spec_data.get('field_name', '').strip()
            field_code = spec_data.get('field_code')

            if not field_name or not field_code or not field_code.strip():
                continue

            # 查询分类级字段
            cat_field = ProductCodeField.query.filter_by(
                category_id=product.category_id,
                subcategory_id=None,
                name=field_name,
                field_type='spec'
            ).first()

            # 查询子分类级字段
            subcat_field = ProductCodeField.query.filter_by(
                subcategory_id=product.subcategory_id,
                name=field_name,
                field_type='spec'
            ).first()

            # 优先使用子分类级，回退到分类级
            field_def = subcat_field or cat_field

            # 只处理参与编码的规格
            if field_def and field_def.use_in_code:
                position = field_def.position if field_def else 999
                specs_code_data.append({
                    'position': position,
                    'code': field_code.strip()
                })

        # 按position排序
        specs_code_data.sort(key=lambda x: x.get('position', 999))

        # 提取前10个规格编码
        spec_codes = [s.get('code', '0') for s in specs_code_data[:10]]

        # 去掉末尾的'0'
        while spec_codes and spec_codes[-1] == '0':
            spec_codes.pop()

        # 生成规格MN
        spec_mn = f"{region_code}{category_code}{subcategory_code}{''.join(spec_codes)}"

        current_app.logger.debug(
            f"计算规格MN: 产品ID={product.id}, spec_mn={spec_mn}"
        )

        return spec_mn if spec_mn else None

    except Exception as e:
        current_app.logger.error(
            f"计算规格MN失败: 产品ID={product.id}, 错误={str(e)}"
        )
        return None
