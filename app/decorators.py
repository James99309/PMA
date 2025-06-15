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

def permission_required_with_approval_context(module, action):
    """
    增强版权限检查装饰器，支持审批上下文
    
    这个装饰器会：
    1. 首先检查常规权限
    2. 如果常规权限检查失败，再检查是否是审批人
    3. 如果是审批人，则允许访问
    
    参数:
        module: 模块名称
        action: 操作类型
    
    用法:
        @app.route('/project/<int:project_id>')
        @permission_required_with_approval_context('project', 'view')
        def view_project(project_id):
            # ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # 未授权
            
            # 首先检查常规权限
            if current_user.has_permission(module, action):
                return f(*args, **kwargs)
            
            # 如果常规权限检查失败，检查是否是审批人
            # 尝试从路由参数中推断对象类型和ID
            object_type = None
            object_id = None
            
            # 根据模块名推断对象类型
            if module == 'project':
                object_type = 'project'
                object_id = kwargs.get('project_id') or kwargs.get('id')
            elif module == 'quotation':
                object_type = 'quotation'
                object_id = kwargs.get('quotation_id') or kwargs.get('id')
            elif module == 'customer':
                object_type = 'customer'
                object_id = kwargs.get('customer_id') or kwargs.get('company_id') or kwargs.get('id')
            elif module == 'order':
                object_type = 'purchase_order'
                object_id = kwargs.get('order_id') or kwargs.get('id')
            
            if object_type and object_id:
                from app.utils.access_control import can_view_in_approval_context
                if can_view_in_approval_context(current_user, object_type, object_id):
                    current_app.logger.info(f"审批权限允许访问: user_id={current_user.id}, username={current_user.username}, object_type={object_type}, object_id={object_id}")
                    return f(*args, **kwargs)
            
            # 如果都没有权限，则拒绝访问
            current_app.logger.warning(f"权限检查失败: user_id={current_user.id}, username={current_user.username}, role={current_user.role}, module={module}, action={action}")
            abort(403)  # 禁止访问
                
        return decorated_function
    return decorator 