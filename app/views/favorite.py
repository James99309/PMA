# -*- coding: utf-8 -*-
"""个人关注(收藏)API — 星标点亮/熄灭。"""
import logging

from flask import Blueprint, jsonify, request
from flask_babel import gettext as _
from flask_login import current_user, login_required

from app.helpers.favorite_helpers import toggle_favorite

logger = logging.getLogger(__name__)

favorite_bp = Blueprint('favorite', __name__, url_prefix='/api/favorites')


@favorite_bp.route('/toggle', methods=['POST'])
@login_required
def toggle():
    """{object_type, object_id} → {success, favorited}。只作用于当前登录用户。"""
    data = request.get_json(silent=True) or {}
    object_type = (data.get('object_type') or '').strip()
    try:
        object_id = int(data.get('object_id'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': _('参数无效')}), 400

    favorited, err = toggle_favorite(current_user, object_type, object_id)
    if err == 'unsupported':
        return jsonify({'success': False, 'message': _('不支持的关注对象类型')}), 400
    if err == 'forbidden':
        return jsonify({'success': False, 'message': _('您没有权限关注该对象')}), 403
    logger.info(f'关注切换: {current_user.username} {object_type}#{object_id} → {favorited}')
    return jsonify({'success': True, 'favorited': favorited})
