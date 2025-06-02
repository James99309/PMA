"""
装饰器模块，提供权限检查等功能
"""
from functools import wraps
from flask import flash, redirect, url_for, request, current_app, abort
from flask_login import current_user, login_required as flask_login_required
import logging

logger = logging.getLogger(__name__)

# 直接导出Flask-Login的login_required装饰器
login_required = flask_login_required

def permission_required(module, action):
    """
    检查当前用户是否有指定模块的特定操作权限的装饰器
    
    参数:
        module: 模块名称
        action: 操作类型，可以是'view', 'create', 'edit', 'delete'之一
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # 未授权
            
            # 检查权限
            current_app.logger.debug(f"Checking permission: module={module}, action={action}")
            if not current_user.has_permission(module, action):
                current_app.logger.warning(f"Permission denied: user_id={current_user.id}, module={module}, action={action}")
                abort(403)  # 禁止访问
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    检查当前用户是否为管理员的装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)  # 未授权
        
        if current_user.role != 'admin':
            current_app.logger.warning(f"Admin access denied: user_id={current_user.id}, role={current_user.role}")
            abort(403)  # 禁止访问
            
        return f(*args, **kwargs)
    return decorated_function 