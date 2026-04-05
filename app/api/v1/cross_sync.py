# -*- coding: utf-8 -*-
"""
跨系统同步 API

接收来自对等 PMA 实例的推送消息和数据同步请求。
使用 X-API-Key 认证。
"""
import logging
from flask import request, jsonify

from app import db
from app.api.v1 import api_v1_bp
from app.api.v1.configurations import require_api_key_or_jwt

logger = logging.getLogger(__name__)


@api_v1_bp.route('/cross-sync/push', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_push():
    """接收跨系统推送消息"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    required_fields = ['recipient_email', 'content']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400

    from app.services.cross_sync_service import receive_message_from_peer
    result = receive_message_from_peer(data)

    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


@api_v1_bp.route('/cross-sync/refresh-cache', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_refresh_cache():
    """刷新本地物化视图缓存（CN 分类变更时调用）"""
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT refresh_cn_cache()'))
        db.session.commit()
        logger.info('物化视图缓存刷新成功（由对等系统触发）')
        return jsonify({'success': True, 'message': '缓存刷新成功'})
    except Exception as e:
        logger.warning(f'物化视图缓存刷新失败: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/sync-product-specs', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_product_specs():
    """接收跨系统产品规格同步请求

    由 CN NAS 在关联 SG 产品到配置后调用，
    更新 SG 产品的规格值、编码、排序并重建快照。

    Request body:
    {
        "product_id": 25,
        "specs": [
            {"field_name": "工作频率", "field_name_en": "Operating Frequency",
             "field_value": "400-470", "field_code": "4", "unit": "MHz", "display_order": 1},
            ...
        ],
        "config_mn": "SGAN2OFD2TE2"  # 可选：配置的 MN 编码
    }
    """
    data = request.get_json()
    if not data or not data.get('product_id'):
        return jsonify({'success': False, 'message': '缺少 product_id'}), 400

    product_id = data['product_id']
    specs_data = data.get('specs', [])

    try:
        from app.models.product import Product
        from app.models.product_spec import ProductSpec
        from app.utils.product_helpers import generate_product_snapshot

        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            return jsonify({'success': False, 'message': f'产品 {product_id} 不存在'}), 404

        # 删除现有规格
        ProductSpec.query.filter_by(product_id=product_id).delete()

        # 写入新规格
        for spec in specs_data:
            ps = ProductSpec(
                product_id=product_id,
                field_name=spec.get('field_name', ''),
                field_name_en=spec.get('field_name_en', ''),
                field_value=spec.get('field_value', ''),
                field_value_en=spec.get('field_value_en', ''),
                field_code=spec.get('field_code', ''),
                use_in_code=spec.get('use_in_code', False),
                unit=spec.get('unit', ''),
                display_order=spec.get('display_order', 0),
                include_in_description=spec.get('include_in_description', True)
            )
            db.session.add(ps)

        db.session.commit()

        # 重建快照 + 更新描述
        from app.services.spec_service import SpecService
        snap = generate_product_snapshot(product, source='cross_sync')
        if snap:
            product.code_definition_snapshot = snap
        product.specification = SpecService.generate_description(SpecService.TYPE_PRODUCT, product_id)
        db.session.commit()

        logger.info(f'跨系统规格同步成功: 产品 {product_id}, {len(specs_data)} 条规格')
        return jsonify({
            'success': True,
            'message': f'已同步 {len(specs_data)} 条规格并重建快照',
            'product_id': product_id
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'跨系统规格同步失败: 产品 {product_id}, {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/lock-config', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_lock_config():
    """SG 导入产品后通知 CN 锁定对应配置

    Request body:
    {
        "config_id": 31,           # CN 配置 ID
        "product_mn": "SOMWCER8T3J" # SG 产品的 MN 编码
    }
    """
    data = request.get_json()
    config_id = data.get('config_id')
    product_mn = data.get('product_mn')

    if not config_id or not product_mn:
        return jsonify({'success': False, 'message': '缺少 config_id 或 product_mn'}), 400

    try:
        from app.models.spec_template import ProductConfiguration
        from app.views.spec_template import generate_mn_code, generate_code_rule_snapshot

        config = ProductConfiguration.query.get(config_id)
        if not config or config.deleted_at:
            return jsonify({'success': False, 'message': f'配置 {config_id} 不存在'}), 404

        old_mn = config.mn_code
        config.mn_code = product_mn
        config.status = 'production'

        # 重建 code_rule_snapshot（使用当前 MN，不重新生成）
        from app.views.spec_template import get_code_from_dictionary, generate_safe_code_char
        code_items = sorted(
            [item for item in config.template.items if item.use_in_code],
            key=lambda x: x.display_order
        )
        code_items_data = []
        for item in code_items:
            value = None
            for cv in config.config_values:
                if cv.template_item_id == item.id:
                    value = cv.value
                    break
            if not value:
                value = item.general_value
            code_char = get_code_from_dictionary(item.spec_dict_id, value) if item.spec_dict_id else None
            if not code_char:
                code_char = generate_safe_code_char(value, item.options or {})
            code_items_data.append({
                "item_id": item.id,
                "definition_name": item.spec_dict.name if item.spec_dict else None,
                "display_order": item.display_order,
                "code_length": item.code_length,
                "options": item.options or {},
                "value": value,
                "code_char": (code_char or 'X')[:1]
            })
        config.code_rule_snapshot = generate_code_rule_snapshot(config, product_mn, code_items_data)

        db.session.commit()
        logger.info(f'跨系统锁定配置: config_id={config_id}, old_mn={old_mn}, new_mn={product_mn}')
        return jsonify({
            'success': True,
            'message': f'配置 {config_id} 已锁定，MN 更新为 {product_mn}'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'跨系统锁定配置失败: config_id={config_id}, {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/unlock-config', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_unlock_config():
    """SG 删除产品后通知 CN 解锁对应配置

    仅在该配置没有其他关联产品时解锁。

    Request body:
    {
        "product_mn": "SOMWCER8T3J"  # 被删除的 SG 产品 MN
    }
    """
    data = request.get_json()
    product_mn = data.get('product_mn')

    if not product_mn:
        return jsonify({'success': False, 'message': '缺少 product_mn'}), 400

    try:
        from app.models.spec_template import ProductConfiguration
        from app.models.product import Product

        # 找到 MN 匹配的配置
        config = ProductConfiguration.query.filter_by(mn_code=product_mn).first()
        if not config:
            return jsonify({'success': True, 'message': f'未找到 MN={product_mn} 的配置，无需操作'})

        # 检查是否还有 CN 关联产品
        cn_count = Product.query.filter_by(
            source_configuration_id=config.id,
            is_deleted=False
        ).count()

        # 检查是否还有 SG 关联产品（排除刚删除的那个）
        sg_count = db.session.execute(db.text(
            "SELECT COUNT(*) FROM sg_products WHERE product_mn = :mn"
        ), {'mn': product_mn}).scalar() or 0

        if cn_count > 0 or sg_count > 0:
            logger.info(f'配置 {config.id} 仍有关联产品 (CN={cn_count}, SG={sg_count})，保持锁定')
            return jsonify({
                'success': True,
                'message': f'配置仍有 {cn_count + sg_count} 个关联产品，保持锁定'
            })

        # 无关联产品，解锁并重新生成 MN
        old_status = config.status
        config.status = 'development'

        from app.views.spec_template import generate_mn_code
        new_mn = generate_mn_code(config)
        if new_mn:
            config.mn_code = new_mn

        db.session.commit()
        logger.info(f'跨系统解锁配置: config_id={config.id}, {old_status} → development, MN={new_mn}')
        return jsonify({
            'success': True,
            'message': f'配置 {config.id} 已解锁，新 MN={new_mn}'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'跨系统解锁配置失败: product_mn={product_mn}, {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/sync-display-order', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_display_order():
    """接收产品排序数据同步（CN → SG）

    Request body:
    {
        "category_code": "O",
        "subcategory_code": "F",
        "items": [
            {"category_code": "O", "category_order": 3, "subcategory_code": "F",
             "subcategory_order": 1, "model": "PNR2100", "model_order": 1},
            ...
        ]
    }
    """
    data = request.get_json()
    category_code = data.get('category_code')
    subcategory_code = data.get('subcategory_code')
    items = data.get('items', [])

    if not category_code or not subcategory_code:
        return jsonify({'success': False, 'message': '缺少 category_code 或 subcategory_code'}), 400

    try:
        from app.models.product_display_order import ProductDisplayOrder

        # 删除该子分类的现有排序数据
        ProductDisplayOrder.query.filter_by(
            category_code=category_code,
            subcategory_code=subcategory_code
        ).delete()

        # 批量插入新数据
        for item in items:
            row = ProductDisplayOrder(
                category_code=item['category_code'],
                category_order=item['category_order'],
                subcategory_code=item['subcategory_code'],
                subcategory_order=item['subcategory_order'],
                model=item['model'],
                model_order=item['model_order'],
            )
            db.session.add(row)

        db.session.commit()
        logger.info(f'产品排序同步接收成功: {category_code}{subcategory_code}, {len(items)} 条')
        return jsonify({'success': True, 'message': f'已同步 {len(items)} 条排序数据'})

    except Exception as e:
        db.session.rollback()
        logger.error(f'产品排序同步接收失败: {category_code}{subcategory_code}, {e}')
        return jsonify({'success': False, 'message': str(e)}), 500
