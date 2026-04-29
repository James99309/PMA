from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app import db
import logging

logger = logging.getLogger(__name__)

VALID_PLATFORMS = ('ios', 'android')


@api_v1_bp.route('/mobile/push/register', methods=['POST'])
@jwt_required()
def mobile_push_register():
    """注册或更新设备 push token"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    data = request.get_json() or {}
    token = data.get('push_token', '').strip()
    platform = data.get('platform', '').lower().strip()

    if not token:
        return api_response(success=False, code=400, message="push_token 不能为空")
    if platform not in VALID_PLATFORMS:
        return api_response(success=False, code=400, message="platform 必须为 ios 或 android")

    try:
        user.push_token = token
        user.push_platform = platform
        db.session.commit()
        return api_response(success=True, message="push token 已注册")
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile push register error: {e}")
        return api_response(success=False, code=500, message="注册失败，请重试")


@api_v1_bp.route('/mobile/push/unregister', methods=['POST'])
@jwt_required()
def mobile_push_unregister():
    """登出时清除 push token"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    try:
        user.push_token = None
        user.push_platform = None
        db.session.commit()
        return api_response(success=True, message="push token 已清除")
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile push unregister error: {e}")
        return api_response(success=False, code=500, message="操作失败")
