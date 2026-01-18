"""
=============================================================================
配置树API模块 (SP8D跨系统调用)
=============================================================================

用于OVS系统调用SP8D配置树数据的API端点。
支持API Key认证和JWT认证。

版本：1.0
最后更新：2025-01-15
"""

from flask import request, jsonify
from functools import wraps
import os
import logging

logger = logging.getLogger(__name__)

# 导入api_v1_bp蓝图
from app.api.v1 import api_v1_bp


def require_api_key_or_jwt(f):
    """支持API Key或JWT两种认证方式的装饰器

    用于跨系统API调用：
    - API Key认证：通过 X-API-Key header（推荐用于系统间通信）
    - JWT认证：通过标准JWT token（用于用户直接访问）

    Returns:
        401: 认证失败
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 方式1: API Key认证（跨系统调用 - 推荐）
        api_key = request.headers.get('X-API-Key')
        valid_api_key = os.environ.get('CROSS_SYSTEM_API_KEY')

        if api_key and valid_api_key and api_key == valid_api_key:
            return f(*args, **kwargs)

        # 方式2: JWT认证（用户直接访问）
        try:
            from flask_jwt_extended import jwt_required
            jwt_required()(lambda: None)()
            return f(*args, **kwargs)
        except Exception as e:
            logger.debug(f"JWT认证失败: {e}")
            pass

        return jsonify({
            'success': False,
            'message': '认证失败 - 请提供有效的API Key或JWT token'
        }), 401

    return decorated_function


@api_v1_bp.route('/configurations-tree', methods=['GET'])
@require_api_key_or_jwt
def get_configurations_tree():
    """获取可引入配置的树状数据（用于OVS跨系统调用）

    返回按分类/子分类组织的配置产品树。
    只返回 pilot（小批价）或 production（可生产）状态的配置。

    **认证方式**：
    - API Key: 通过 X-API-Key header
    - JWT: 通过标准Authorization header

    **查询参数**：
    无

    **返回数据结构**：
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "cat_1",
          "type": "category",
          "name": "基站",
          "category_id": 1,
          "children": [
            {
              "id": "sub_3",
              "type": "subcategory",
              "name": "宏基站",
              "subcategory_id": 3,
              "children": [
                {
                  "id": 123,
                  "type": "configuration",
                  "template_id": 10,
                  "template_model": "BS2800",
                  "mn_code": "EBS4X33N",
                  "config_code": "4X33",
                  "status": "production",
                  "status_display": "可生产",
                  "region": "N",
                  "region_id": 5,
                  "region_name": "北美",
                  "category_id": 1,
                  "category_name": "基站",
                  "subcategory_id": 3,
                  "subcategory_name": "宏基站",
                  "product_name": "宏基站",
                  "already_imported": false
                }
              ]
            }
          ]
        }
      ]
    }
    ```

    Returns:
        JSON: 树状配置数据或错误信息
    """
    try:
        from flask_babel import gettext as _
        from app.models.spec_template import ProductConfiguration, SpecTemplate
        from app.models.product import Product

        # 查询 pilot/production 状态的配置
        configs = ProductConfiguration.query.filter(
            ProductConfiguration.status.in_(['pilot', 'production']),
            ProductConfiguration.is_active == True,
            ProductConfiguration.mn_code.isnot(None)
        ).join(SpecTemplate).all()

        # 按分类/子分类组织成树
        category_map = {}

        for config in configs:
            template = config.template
            if not template or not template.category_id:
                continue

            cat_id = template.category_id
            sub_id = template.subcategory_id

            # 检查是否已引入（通过source_configuration_id查询Product表）
            already_imported = Product.query.filter_by(
                source_configuration_id=config.id
            ).first() is not None

            # 获取状态显示文本
            status_display = _('可生产') if config.status == 'production' else _('小批价')

            # 查找区域ID和区域名称
            region_id = None
            region_name_display = config.region_name
            region_name_en_display = None
            if config.region:
                from app.models.product_code import ProductCodeField, ProductCodeFieldOption
                region_field = ProductCodeField.query.filter(
                    ProductCodeField.field_type == 'origin_location',
                    ProductCodeField.code == config.region
                ).first()
                if region_field:
                    region_id = region_field.id
                    # 当 region_name 为空时，从 ProductCodeField 获取名称
                    if not region_name_display:
                        region_name_display = region_field.name
                        region_name_en_display = region_field.name_en
                else:
                    region_option = ProductCodeFieldOption.query.join(ProductCodeField).filter(
                        ProductCodeField.field_type == 'origin_location',
                        ProductCodeFieldOption.code == config.region
                    ).first()
                    if region_option:
                        region_id = region_option.field_id

            # 获取产品名称
            product_name = template.subcategory.name if template.subcategory else ''
            # 英文名称优先使用规格模板的name_en，其次使用子分类的name_en
            product_name_en = template.name_en if template.name_en else (
                template.subcategory.name_en if template.subcategory else ''
            )

            # 构建配置节点数据
            config_node = {
                'id': config.id,
                'type': 'configuration',
                'template_id': template.id,
                'template_model': template.model,
                'mn_code': config.mn_code,
                'config_code': config.config_code,
                'status': config.status,
                'status_display': status_display,
                'region': config.region,
                'region_id': region_id,
                'region_name': region_name_display or config.region,
                'region_name_en': region_name_en_display,
                'category_id': template.category_id,
                'category_name': template.category.name if template.category else None,
                'category_name_en': template.category.name_en if template.category else None,
                'subcategory_id': template.subcategory_id,
                'subcategory_name': template.subcategory.name if template.subcategory else None,
                'subcategory_name_en': template.subcategory.name_en if template.subcategory else None,
                'product_name': product_name,
                'product_name_en': product_name_en,
                'already_imported': already_imported
            }

            # 添加到分类树
            if cat_id not in category_map:
                category = template.category
                category_map[cat_id] = {
                    'id': f'cat_{cat_id}',
                    'type': 'category',
                    'name': category.name if category else f'Category {cat_id}',
                    'category_id': cat_id,
                    'children': {}
                }

            # 添加到子分类
            if sub_id:
                if sub_id not in category_map[cat_id]['children']:
                    subcategory = template.subcategory
                    category_map[cat_id]['children'][sub_id] = {
                        'id': f'sub_{sub_id}',
                        'type': 'subcategory',
                        'name': subcategory.name if subcategory else f'Subcategory {sub_id}',
                        'subcategory_id': sub_id,
                        'children': []
                    }
                category_map[cat_id]['children'][sub_id]['children'].append(config_node)
            else:
                if '_no_sub' not in category_map[cat_id]['children']:
                    category_map[cat_id]['children']['_no_sub'] = {
                        'id': f'sub_none_{cat_id}',
                        'type': 'subcategory',
                        'name': _('未分类'),
                        'subcategory_id': None,
                        'children': []
                    }
                category_map[cat_id]['children']['_no_sub']['children'].append(config_node)

        # 转换为列表结构
        tree = []
        for cat_id in sorted(category_map.keys()):
            cat_node = category_map[cat_id].copy()
            cat_node['children'] = list(cat_node['children'].values())
            tree.append(cat_node)

        return jsonify({'success': True, 'data': tree})

    except Exception as e:
        logger.error(f"获取配置树失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取配置树失败: {str(e)}'
        }), 500


@api_v1_bp.route('/configurations/<int:config_id>/specs', methods=['GET'])
@require_api_key_or_jwt
def get_configuration_specs_api(config_id):
    """获取配置版本的规格数据（跨系统调用）

    用于OVS从SP8D导入产品时获取规格数据。

    **认证方式**：
    - API Key: 通过 X-API-Key header
    - JWT: 通过标准Authorization header

    **返回数据结构**：
    ```json
    {
        "success": true,
        "data": {
            "configuration": {
                "id": 123,
                "config_code": "4X33",
                "region": "N",
                "region_name": "北美",
                "template_model": "BS2800",
                "mn_code": "EBS4X33N"
            },
            "specs": [
                {
                    "template_item_id": 1,
                    "name": "频段",
                    "name_en": "Frequency Band",
                    "value": "700MHz",
                    "unit": "",
                    "category": "基本参数",
                    "use_in_code": true,
                    "code_char": "7"
                }
            ]
        }
    }
    ```

    Args:
        config_id: 配置版本ID

    Returns:
        JSON: 规格数据或错误信息
    """
    try:
        from app.models.spec_template import ProductConfiguration, SpecTemplate, SpecTemplateItem
        from app.models.spec_template import generate_safe_code_char

        config = ProductConfiguration.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'message': f'配置版本 {config_id} 不存在'
            }), 404

        template = config.template
        if not template:
            return jsonify({
                'success': False,
                'message': '配置模板不存在'
            }), 404

        specs = []

        # 遍历模板规格项
        for item in template.items:
            if not item.definition:
                continue

            # 获取配置值（优先）或通用值
            value = config.get_spec_value(item.id)
            if not value:
                continue  # 只返回有值的规格

            # 获取编码字符（如果是编码规格）
            code_char = None
            if item.use_in_code and item.options:
                code_char = generate_safe_code_char(value, item.options)
                # 处理编码长度
                if item.code_length == 2:
                    code_char = code_char.ljust(2, 'X')[:2]
                else:
                    code_char = code_char[:1]

            specs.append({
                'template_item_id': item.id,
                'name': item.definition.name,
                'name_en': item.definition.name_en,
                'value': value,
                'unit': item.definition.unit or '',
                'category': item.definition.category.name if item.definition.category else '',
                'use_in_code': item.use_in_code,
                'code_char': code_char
            })

        # 按编码规格优先排序
        specs.sort(key=lambda x: (not x['use_in_code'], x['category']))

        logger.info(f"获取配置 {config_id} 的规格数据，共 {len(specs)} 条")

        return jsonify({
            'success': True,
            'data': {
                'configuration': {
                    'id': config.id,
                    'config_code': config.config_code,
                    'region': config.region,
                    'region_name': config.region_name or config.region,
                    'template_model': template.model,
                    'mn_code': config.mn_code
                },
                'specs': specs
            }
        })

    except Exception as e:
        logger.error(f"获取配置规格失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取配置规格失败: {str(e)}'
        }), 500
