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
