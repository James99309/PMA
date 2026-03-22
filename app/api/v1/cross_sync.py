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
