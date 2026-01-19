# -*- coding: utf-8 -*-
"""
统一的产品规格服务

支持产品库和研发产品库的规格保存、预览、冲突检测
"""

import logging
from datetime import datetime
from flask import current_app
from app import db

logger = logging.getLogger(__name__)


class SpecService:
    """
    统一的规格服务类

    支持:
    - 产品库 (Product/ProductSpec)
    - 研发产品库 (DevProduct/DevProductSpec)
    """

    # 产品类型常量
    TYPE_PRODUCT = 'product'
    TYPE_DEV_PRODUCT = 'dev_product'

    @classmethod
    def get_models(cls, product_type):
        """
        根据产品类型获取对应的模型类

        Args:
            product_type: 'product' 或 'dev_product'

        Returns:
            tuple: (ProductModel, SpecModel, product_id_field, unit_field)
        """
        if product_type == cls.TYPE_PRODUCT:
            from app.models.product import Product
            from app.models.product_spec import ProductSpec
            return Product, ProductSpec, 'product_id', 'unit'
        else:
            from app.models.dev_product import DevProduct, DevProductSpec
            return DevProduct, DevProductSpec, 'dev_product_id', 'field_unit'

    @classmethod
    def save_specs(cls, product_type, product_id, specs_data, deleted_ids=None):
        """
        统一的规格保存方法

        Args:
            product_type: 'product' 或 'dev_product'
            product_id: 产品ID
            specs_data: 规格数据列表
            deleted_ids: 要删除的规格ID列表

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'description': str,
                'specs': list,
                'spec_mn': str,
                'product_mn': str
            }
        """
        ProductModel, SpecModel, id_field, unit_field = cls.get_models(product_type)

        try:
            product = ProductModel.query.get(product_id)
            if not product:
                return {'success': False, 'message': '产品不存在'}

            deleted_ids = deleted_ids or []

            # 1. 删除标记的规格
            if deleted_ids:
                for spec_id in deleted_ids:
                    filter_kwargs = {'id': int(spec_id), id_field: product_id}
                    spec = SpecModel.query.filter_by(**filter_kwargs).first()
                    if spec:
                        db.session.delete(spec)
                        logger.debug(f"删除规格: {spec.field_name}")

            # 2. 更新或添加规格
            display_order = 0
            for spec_data in specs_data:
                spec_id = spec_data.get('id')
                field_name = spec_data.get('field_name', '').strip()
                field_name_en = spec_data.get('field_name_en', '').strip() if spec_data.get('field_name_en') else ''
                field_value = spec_data.get('field_value', '').strip()
                field_code = spec_data.get('field_code') or None
                include_in_description = spec_data.get('include_in_description', True)

                if not field_name or not field_value:
                    continue

                if spec_id:
                    # 更新现有规格
                    filter_kwargs = {'id': int(spec_id), id_field: product_id}
                    spec = SpecModel.query.filter_by(**filter_kwargs).first()
                    if spec:
                        spec.field_value = field_value
                        spec.include_in_description = include_in_description
                        if hasattr(spec, 'field_code'):
                            spec.field_code = field_code
                        if hasattr(spec, 'display_order'):
                            spec.display_order = display_order
                        # 保存英文名称（如果提供且模型支持）
                        if hasattr(spec, 'field_name_en') and field_name_en:
                            spec.field_name_en = field_name_en
                        logger.debug(f"更新规格: {field_name} = {field_value}")
                else:
                    # 添加新规格
                    new_spec_kwargs = {
                        id_field: product_id,
                        'field_name': field_name,
                        'field_value': field_value,
                        'include_in_description': include_in_description
                    }
                    if hasattr(SpecModel, 'field_code'):
                        new_spec_kwargs['field_code'] = field_code
                    if hasattr(SpecModel, 'display_order'):
                        new_spec_kwargs['display_order'] = display_order
                    # 保存英文名称（如果提供且模型支持）
                    if hasattr(SpecModel, 'field_name_en') and field_name_en:
                        new_spec_kwargs['field_name_en'] = field_name_en

                    new_spec = SpecModel(**new_spec_kwargs)
                    db.session.add(new_spec)
                    logger.debug(f"添加规格: {field_name} = {field_value}")

                display_order += 1

            db.session.flush()

            # 3. 生成产品描述（只包含 include_in_description=True 的规格）
            # 按 display_order 排序，确保描述顺序与用户定义的顺序一致
            filter_kwargs = {id_field: product_id}
            if hasattr(SpecModel, 'display_order'):
                all_specs = SpecModel.query.filter_by(**filter_kwargs).order_by(SpecModel.display_order).all()
            else:
                all_specs = SpecModel.query.filter_by(**filter_kwargs).order_by(SpecModel.id).all()

            # 检查是否为OVS系统，决定描述使用的语言
            is_ovs = current_app.config.get('IS_OVS', False)

            description_parts = []
            for spec in all_specs:
                if spec.include_in_description and spec.field_value:
                    unit = getattr(spec, unit_field, '') or ''
                    unit_str = f" {unit}" if unit else ""
                    # OVS使用英文名称，SP8D使用中文名称
                    if is_ovs and hasattr(spec, 'field_name_en') and spec.field_name_en:
                        field_display_name = spec.field_name_en
                    else:
                        field_display_name = spec.field_name
                    description_parts.append(f"{field_display_name}: {spec.field_value}{unit_str}")
            new_description = ", ".join(description_parts) if description_parts else ""

            # 4. 更新产品描述
            if product_type == cls.TYPE_PRODUCT:
                product.specification = new_description
            else:
                product.description = new_description
            product.updated_at = datetime.utcnow()

            # 5. 更新MN编码（如果适用）
            # 引入产品（有source_configuration_id）跳过编码更新，保持从配置引入的编码
            spec_mn = None
            product_mn = None
            is_imported_product = product_type == cls.TYPE_PRODUCT and getattr(product, 'source_configuration_id', None)

            if product_type == cls.TYPE_PRODUCT:
                if is_imported_product:
                    # 引入产品：保持现有编码不变
                    spec_mn = product.spec_mn
                    product_mn = product.product_mn
                    logger.debug(f"引入产品 {product_id} 跳过编码更新，保持 spec_mn={spec_mn}, product_mn={product_mn}")
                else:
                    # 普通产品：重新计算编码
                    from app.utils.product_helpers import generate_spec_mn
                    spec_mn = generate_spec_mn(product)
                    if spec_mn:
                        product.spec_mn = spec_mn
                        if not getattr(product, 'is_mn_locked', False) or not product.product_mn:
                            product.product_mn = spec_mn
                        product_mn = product.product_mn
            else:
                # 研发产品的MN编码逻辑
                from app.utils.product_helpers import generate_dev_product_mn
                try:
                    spec_mn = generate_dev_product_mn(product)
                    if spec_mn:
                        product.mn_code = spec_mn
                    product_mn = product.mn_code
                except Exception as e:
                    logger.warning(f"生成研发产品MN失败: {e}")

            db.session.commit()
            logger.info(f"{'产品' if product_type == cls.TYPE_PRODUCT else '研发产品'} {product_id} 规格保存成功")

            # 6. 返回更新后的规格列表
            specs_list = []
            for spec in all_specs:
                spec_dict = {
                    'id': spec.id,
                    'field_name': spec.field_name,
                    'field_name_en': getattr(spec, 'field_name_en', '') or '',
                    'field_value': spec.field_value,
                    'include_in_description': spec.include_in_description
                }
                if hasattr(spec, 'field_code'):
                    spec_dict['field_code'] = spec.field_code or ''
                unit_value = getattr(spec, unit_field, '') or ''
                spec_dict['unit' if product_type == cls.TYPE_PRODUCT else 'field_unit'] = unit_value
                specs_list.append(spec_dict)

            return {
                'success': True,
                'message': '规格保存成功',
                'description': new_description,
                'specification': new_description,  # 兼容产品库
                'specs': specs_list,
                'spec_mn': spec_mn,
                'product_mn': product_mn
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"保存规格失败: {str(e)}")
            return {'success': False, 'message': f'保存失败: {str(e)}'}

    @classmethod
    def preview_specs_mn(cls, product_type, product_id, specs_data):
        """
        预览规格保存后的MN变化和冲突检测

        Args:
            product_type: 'product' 或 'dev_product'
            product_id: 产品ID
            specs_data: 规格数据列表

        Returns:
            dict: {
                'success': bool,
                'current_product_mn': str,
                'current_spec_mn': str,
                'new_spec_mn': str,
                'is_mn_locked': bool,
                'missing_codes': list,
                'conflict_product': dict or None,
                'current_specs': list
            }
        """
        ProductModel, SpecModel, id_field, unit_field = cls.get_models(product_type)

        try:
            product = ProductModel.query.get(product_id)
            if not product:
                return {'success': False, 'message': '产品不存在'}

            from app.models.product_code import ProductCodeField

            # 获取子分类ID
            subcategory_id = product.subcategory_id
            category_id = getattr(product, 'category_id', None)

            # 检查哪些规格缺少编码
            missing_codes = []
            for spec_data in specs_data:
                field_name = spec_data.get('field_name', '').strip()
                field_code = spec_data.get('field_code')

                # 查找该规格是否参与编码
                field_def = None
                if subcategory_id:
                    field_def = ProductCodeField.query.filter_by(
                        subcategory_id=subcategory_id,
                        name=field_name,
                        field_type='spec'
                    ).first()

                if not field_def and category_id:
                    field_def = ProductCodeField.query.filter_by(
                        category_id=category_id,
                        subcategory_id=None,
                        name=field_name,
                        field_type='spec'
                    ).first()

                # 如果该规格参与编码但没有编码值
                if field_def and field_def.use_in_code and (not field_code or not str(field_code).strip()):
                    missing_codes.append(field_name)

            # 计算新的spec_mn
            new_spec_mn = None
            conflict_product = None

            if not missing_codes:
                from app.utils.product_helpers import calculate_spec_mn_from_data
                new_spec_mn = calculate_spec_mn_from_data(product, specs_data)

                # 冲突检测（同时检查研发库和产品库）
                if new_spec_mn:
                    conflict_product = cls._check_mn_conflict(
                        new_spec_mn,
                        product_type,
                        product_id,
                        specs_data,
                        SpecModel,
                        id_field
                    )

            # 获取当前修改的规格
            filter_kwargs = {id_field: product_id}
            current_specs_db = {s.field_name: s.field_value for s in SpecModel.query.filter_by(**filter_kwargs).all()}
            changed_spec_list = []
            for s in specs_data:
                if s.get('field_code'):
                    field_name = s.get('field_name')
                    new_value = s.get('field_value')
                    old_value = current_specs_db.get(field_name)
                    if old_value != new_value:
                        changed_spec_list.append({'name': field_name, 'value': new_value})

            # 获取当前MN
            if product_type == cls.TYPE_PRODUCT:
                current_product_mn = product.product_mn or ''
                current_spec_mn = product.spec_mn or ''
                is_mn_locked = getattr(product, 'is_mn_locked', False)
            else:
                current_product_mn = product.mn_code or ''
                current_spec_mn = product.mn_code or ''
                is_mn_locked = False  # 研发产品暂无锁定机制

            return {
                'success': True,
                'current_product_mn': current_product_mn,
                'current_spec_mn': current_spec_mn,
                'new_spec_mn': new_spec_mn or '',
                'is_mn_locked': is_mn_locked,
                'missing_codes': missing_codes,
                'conflict_product': conflict_product,
                'current_specs': changed_spec_list
            }

        except Exception as e:
            logger.error(f"预览规格MN失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    @classmethod
    def _check_mn_conflict(cls, new_mn, product_type, product_id, specs_data, SpecModel, id_field):
        """
        检查MN冲突（同时检查研发库和产品库）

        Returns:
            dict or None: 冲突产品信息
        """
        from app.models.product import Product
        from app.models.dev_product import DevProduct
        from app.models.product_spec import ProductSpec
        from app.models.dev_product import DevProductSpec

        conflict = None
        conflict_source = None

        # 检查产品库
        product_query = Product.query.filter(
            db.or_(
                Product.spec_mn == new_mn,
                Product.product_mn == new_mn
            )
        )
        if product_type == cls.TYPE_PRODUCT:
            product_query = product_query.filter(Product.id != product_id)
        conflict = product_query.first()
        if conflict:
            conflict_source = 'product'

        # 如果产品库没有冲突，检查研发库
        if not conflict:
            dev_query = DevProduct.query.filter(DevProduct.mn_code == new_mn)
            if product_type == cls.TYPE_DEV_PRODUCT:
                dev_query = dev_query.filter(DevProduct.id != product_id)
            conflict = dev_query.first()
            if conflict:
                conflict_source = 'dev_product'

        if not conflict:
            return None

        # 获取修改的字段名
        changed_field_names = set()
        for s in specs_data:
            if s.get('field_code'):
                changed_field_names.add(s.get('field_name'))

        # 获取冲突产品的规格
        if conflict_source == 'product':
            conflict_specs = ProductSpec.query.filter_by(product_id=conflict.id).all()
            conflict_spec_list = [
                {'name': s.field_name, 'value': s.field_value}
                for s in conflict_specs
                if s.field_code and s.field_name in changed_field_names
            ]
            return {
                'id': conflict.id,
                'product_name': conflict.product_name or conflict.name or '-',
                'model': conflict.model or '-',
                'product_mn': conflict.product_mn or '-',
                'spec_mn': conflict.spec_mn or '-',
                'specs': conflict_spec_list,
                'source': '产品库'
            }
        else:
            conflict_specs = DevProductSpec.query.filter_by(dev_product_id=conflict.id).all()
            conflict_spec_list = [
                {'name': s.field_name, 'value': s.field_value}
                for s in conflict_specs
                if s.field_code and s.field_name in changed_field_names
            ]
            return {
                'id': conflict.id,
                'product_name': conflict.name or '-',
                'model': conflict.model or '-',
                'product_mn': conflict.mn_code or '-',
                'spec_mn': conflict.mn_code or '-',
                'specs': conflict_spec_list,
                'source': '研发产品库'
            }

    @classmethod
    def get_specs_with_coded_fields(cls, product_type, product_id, subcategory_id):
        """
        获取产品规格，包含缺失的编码规格字段

        Args:
            product_type: 'product' 或 'dev_product'
            product_id: 产品ID
            subcategory_id: 子分类ID

        Returns:
            list: 规格列表，每个规格包含:
                - id: 规格ID (None 表示缺失)
                - field_name: 规格名称
                - field_value: 规格值 (空字符串表示缺失)
                - field_code: 编码
                - unit: 单位
                - include_in_description: 是否包含在描述中
                - is_missing: 是否为缺失的编码规格
                - is_coded: 是否为编码规格
                - field_id: 字段ID
                - is_inherited: 是否继承自父分类
                - options: 可选值列表 (仅缺失的编码规格)
        """
        from app.models.product_code import ProductCodeField, ProductCodeFieldOption, ProductSubcategory
        from app.routes.product_code import get_field_unit

        ProductModel, SpecModel, id_field, unit_field = cls.get_models(product_type)

        # 获取已有规格
        filter_kwargs = {id_field: product_id}
        specs_db = SpecModel.query.filter_by(**filter_kwargs).order_by(
            SpecModel.display_order if hasattr(SpecModel, 'display_order') else SpecModel.id
        ).all()

        specs = []
        existing_spec_names = set()
        existing_field_ids = set()  # 用 field_id 来判断，更准确

        # 预先获取该子分类下所有字段，用于查找field_id和use_in_code
        # field_info 结构: {name: {'id': field_id, 'use_in_code': bool}}
        field_info = {}
        if subcategory_id:
            subcategory = ProductSubcategory.query.get(subcategory_id)
            if subcategory:
                # 获取分类级字段
                category_fields = ProductCodeField.query.filter(
                    ProductCodeField.category_id == subcategory.category_id,
                    ProductCodeField.subcategory_id.is_(None),
                    ProductCodeField.field_type == 'spec'
                ).all()
                for f in category_fields:
                    field_info[f.name] = {'id': f.id, 'use_in_code': f.use_in_code}

                # 获取子分类级字段
                subcategory_fields = ProductCodeField.query.filter(
                    ProductCodeField.subcategory_id == subcategory_id,
                    ProductCodeField.field_type == 'spec'
                ).all()
                for f in subcategory_fields:
                    field_info[f.name] = {'id': f.id, 'use_in_code': f.use_in_code}

        for spec in specs_db:
            # 判断是否为编码规格：基于 ProductCodeField.use_in_code，而非 field_code 是否有值
            spec_field_info = field_info.get(spec.field_name, {})
            is_coded = spec_field_info.get('use_in_code', False)
            field_id = spec_field_info.get('id')

            spec_dict = {
                'id': spec.id,
                'field_name': spec.field_name,
                'field_name_en': getattr(spec, 'field_name_en', '') or '',
                'field_value': spec.field_value,
                'field_code': getattr(spec, 'field_code', '') or '',
                'unit': get_field_unit(spec.field_name) or '',
                'include_in_description': getattr(spec, 'include_in_description', True),
                'is_missing': False,
                'is_coded': is_coded,  # 基于 use_in_code 判断，而非 field_code
                'field_id': field_id,  # 查找对应的字段ID
                'is_inherited': False,
                'options': []
            }
            specs.append(spec_dict)
            existing_spec_names.add(spec.field_name)
            if field_id:
                existing_field_ids.add(field_id)

        # 获取该子分类的所有编码规格字段（包含继承的）
        if subcategory_id:
            subcategory = ProductSubcategory.query.get(subcategory_id)
            if subcategory:
                # 获取继承的分类级编码规格
                inherited_fields = ProductCodeField.query.filter(
                    ProductCodeField.category_id == subcategory.category_id,
                    ProductCodeField.subcategory_id.is_(None),
                    ProductCodeField.field_type == 'spec',
                    ProductCodeField.use_in_code == True
                ).order_by(ProductCodeField.position).all()

                # 获取子分类自己的编码规格
                own_fields = ProductCodeField.query.filter(
                    ProductCodeField.subcategory_id == subcategory_id,
                    ProductCodeField.field_type == 'spec',
                    ProductCodeField.use_in_code == True
                ).order_by(ProductCodeField.position).all()

                # 合并编码规格字段，用字典去重（按 field_id）
                all_coded_fields_map = {}
                inherited_field_ids = {f.id for f in inherited_fields}
                for f in inherited_fields:
                    all_coded_fields_map[f.id] = f
                for f in own_fields:
                    all_coded_fields_map[f.id] = f  # 子分类级覆盖分类级同名字段
                all_coded_fields = list(all_coded_fields_map.values())

                # 为缺失的编码规格创建空条目（用 field_id 判断，更准确）
                for field in all_coded_fields:
                    if field.id not in existing_field_ids:
                        # 获取该字段的选项
                        if field.id in inherited_field_ids:
                            options = ProductCodeFieldOption.query.filter_by(
                                field_id=field.id,
                                subcategory_id=subcategory_id
                            ).order_by(ProductCodeFieldOption.position).all()
                        else:
                            options = ProductCodeFieldOption.query.filter_by(
                                field_id=field.id
                            ).order_by(ProductCodeFieldOption.position).all()

                        specs.append({
                            'id': None,
                            'field_name': field.name,
                            'field_name_en': field.name_en or '',
                            'field_value': '',
                            'field_code': '',
                            'unit': get_field_unit(field.name) or '',
                            'include_in_description': True,
                            'is_missing': True,
                            'is_coded': True,
                            'field_id': field.id,
                            'is_inherited': field.id in inherited_field_ids,
                            'options': [{'value': o.effective_value, 'code': o.effective_code or ''} for o in options]
                        })

        return specs

    @classmethod
    def group_specs_by_category(cls, specs):
        """
        将规格列表按分类分组

        Args:
            specs: 规格列表，每个规格需要有 field_name 字段

        Returns:
            list: 分类列表，每个分类包含:
                - id: 分类ID (0 表示未分类)
                - name: 分类名称
                - name_en: 分类英文名称
                - specs: 该分类下的规格列表
        """
        from app.models.spec_template import SpecDefinition, SpecCategory

        # 获取所有分类（按 display_order 排序）
        all_categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()
        category_map = {cat.id: cat for cat in all_categories}

        # 通过 field_name 匹配 SpecDefinition 获取分类信息和英文名称
        spec_names = [s.get('field_name') or s.get('name', '') for s in specs if s.get('field_name') or s.get('name')]
        definitions = SpecDefinition.query.filter(SpecDefinition.name.in_(spec_names)).all()
        name_to_category = {d.name: d.category_id for d in definitions}
        name_to_name_en = {d.name: d.name_en for d in definitions}

        # 按分类分组
        specs_by_category = {}
        uncategorized_specs = []

        for spec in specs:
            field_name = spec.get('field_name') or spec.get('name', '')
            # 只包含有值的规格
            field_value = spec.get('field_value') or spec.get('value', '')
            if not field_value:
                continue

            # 添加英文名称到规格：优先使用已存储的值，回退到 SpecDefinition 查询
            spec_with_en = dict(spec)
            if not spec_with_en.get('field_name_en'):
                spec_with_en['field_name_en'] = name_to_name_en.get(field_name, '')

            cat_id = name_to_category.get(field_name)
            if cat_id and cat_id in category_map:
                if cat_id not in specs_by_category:
                    specs_by_category[cat_id] = []
                specs_by_category[cat_id].append(spec_with_en)
            else:
                uncategorized_specs.append(spec_with_en)

        # 构建按 display_order 排序的分类列表
        spec_categories = []
        for cat in all_categories:
            if cat.id in specs_by_category:
                spec_categories.append({
                    'id': cat.id,
                    'name': cat.name,
                    'name_en': cat.name_en,
                    'specs': specs_by_category[cat.id]
                })

        # 未分类的规格放在最后
        if uncategorized_specs:
            spec_categories.append({
                'id': 0,
                'name': '其他规格',
                'name_en': 'Other Specs',
                'specs': uncategorized_specs
            })

        return spec_categories
