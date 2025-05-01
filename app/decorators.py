"""
装饰器模块，提供权限检查等功能
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required as flask_login_required
import logging

logger = logging.getLogger(__name__)

# 直接导出Flask-Login的login_required装饰器
login_required = flask_login_required

def permission_required(module, action):
    """
    权限检查装饰器
    
    参数:
        module (str): 模块名称
        action (str): 操作类型 (view/create/edit/delete)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 管理员拥有所有权限
            if current_user.role == 'admin':
                return f(*args, **kwargs)
                
            # 产品经理和解决方案经理可以查看所有报价单
            if module == 'quotation' and action == 'view' and current_user.role in ['product_manager', 'solution_manager']:
                return f(*args, **kwargs)
                
            # 检查用户权限
            if not current_user.has_permission(module, action):
                logger.warning(f"用户 {current_user.username} 尝试访问 {module}/{action} 但没有权限")
                flash('您没有权限执行此操作', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator 