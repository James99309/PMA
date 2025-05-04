"""
装饰器模块，提供权限检查等功能
"""
from functools import wraps
from flask import flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required as flask_login_required
import logging

logger = logging.getLogger(__name__)

# 直接导出Flask-Login的login_required装饰器
login_required = flask_login_required

def permission_required(module, action):
    """
    权限控制装饰器
    
    参数:
        module: 模块名称，如'customer', 'project'等
        action: 操作类型，'view', 'create', 'edit', 'delete'
    
    用法示例:
        @app.route('/customers')
        @login_required
        @permission_required('customer', 'view')
        def list_customers():
            # 函数内容
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 记录日志
            logger.debug(f"检查权限 - 用户: {current_user.username if current_user.is_authenticated else '未登录'}, 模块: {module}, 操作: {action}")
            
            # 检查用户是否登录
            if not current_user.is_authenticated:
                logger.warning(f"权限检查失败 - 用户未登录")
                return redirect(url_for('auth.login', next=request.url))
            
            # 管理员拥有所有权限
            if current_user.role == 'admin':
                logger.debug(f"管理员用户 {current_user.username} 权限检查通过")
                return f(*args, **kwargs)
            
            # 检查普通用户权限
            if not hasattr(current_user, 'has_permission'):
                logger.error(f"用户对象缺少has_permission方法")
                flash('您没有权限访问该页面', 'danger')
                return redirect(url_for('main.index'))
            
            if not current_user.has_permission(module, action):
                logger.warning(f"权限检查失败 - 用户: {current_user.username}, 模块: {module}, 操作: {action}")
                flash('您没有权限执行此操作', 'danger')
                return redirect(url_for('main.index'))
            
            logger.debug(f"权限检查通过 - 用户: {current_user.username}, 模块: {module}, 操作: {action}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator 
            if current_user.role == 'admin':
                logger.debug(f"管理员用户 {current_user.username} 权限检查通过")
                return f(*args, **kwargs)
            
            # 检查普通用户权限
            if not hasattr(current_user, 'has_permission'):
                logger.error(f"用户对象缺少has_permission方法")
                flash('您没有权限访问该页面', 'danger')
                return redirect(url_for('main.index'))
            
            if not current_user.has_permission(module, action):
                logger.warning(f"权限检查失败 - 用户: {current_user.username}, 模块: {module}, 操作: {action}")
                flash('您没有权限执行此操作', 'danger')
                return redirect(url_for('main.index'))
            
            logger.debug(f"权限检查通过 - 用户: {current_user.username}, 模块: {module}, 操作: {action}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator 