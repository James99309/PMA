from functools import wraps
from flask import json
from flask.json.provider import JSONEncoderify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User

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
    return jsonify(response), code

def jwt_required_with_permission(module, action):
    """
    JWT认证 + 权限检查装饰器
    
    参数:
        module (str): 模块名称
        action (str): 操作类型 (view/create/edit/delete)
    
    返回:
        装饰器函数
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # 验证JWT
                verify_jwt_in_request()
                
                # 获取当前用户
                user_id = get_jwt_identity()
                # 不再转换ID类型，保持一致性
                    
                user = User.query.get(user_id)
                
                if not user:
                    return api_response(
                        success=False, 
                        code=401, 
                        message="认证失败，用户不存在"
                    )
                
                # 验证用户是否激活
                if not user.is_active:
                    return api_response(
                        success=False, 
                        code=403, 
                        message="账号未激活，请联系管理员"
                    )
                
                # 检查权限
                if not user.has_permission(module, action):
                    return api_response(
                        success=False, 
                        code=403, 
                        message=f"无权执行此操作: {module}/{action}"
                    )
                
                return fn(*args, **kwargs)
            except Exception as e:
                return api_response(
                    success=False,
                    code=401,
                    message=f"认证失败: {str(e)}"
                )
        return wrapper
    return decorator

def get_pagination_params():
    """
    获取分页参数
    
    返回:
        tuple: (page, limit)
    """
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # 确保参数在合理范围内
    page = max(1, page)
    limit = max(1, min(100, limit))  # 限制最大查询数量为100
    
    return page, limit 