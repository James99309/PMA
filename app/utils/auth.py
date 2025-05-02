from functools import wraps
from flask import json
from flask.json.provider import JSONEncoderify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_login import current_user

def api_response(success=True, code=200, message="操作成功", data=None):
    """
    统一的API响应格式
    
    参数:
        success (bool): 操作是否成功
        code (int): HTTP状态码
        message (str): 响应消息
        data (dict/list): 响应数据
    
    返回:
        JSON响应
    """
    response = {
        "success": success,
        "code": code,
        "message": message,
        "data": data if data is not None else {}
    }
    return jsonify(response)

def flexible_auth(fn):
    """允许JWT认证或基于会话的认证的装饰器"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # 尝试JWT认证
            verify_jwt_in_request(optional=True)
            if get_jwt_identity():
                # JWT认证成功
                return fn(*args, **kwargs)
        except Exception as e:
            # JWT认证失败，记录但继续尝试其他认证方式
            pass
        
        # 如果JWT认证失败，检查当前用户是否已登录
        if current_user and current_user.is_authenticated:
            # 会话认证成功
            return fn(*args, **kwargs)
        
        # 如果都未认证，返回401错误
        return api_response(
            success=False,
            code=401,
            message="未认证"
        ), 401
        
    return wrapper 