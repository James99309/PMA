"""
权限管理模块
用于定义和检查用户权限
"""
from functools import wraps
from flask import abort, request, g, current_app
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

class Permissions:
    """权限常量定义"""
    # 项目相关权限
    PROJECT_VIEW = 'project_view'
    PROJECT_CREATE = 'project_create'
    PROJECT_EDIT = 'project_edit'
    PROJECT_DELETE = 'project_delete'
    
    # 客户相关权限
    CUSTOMER_VIEW = 'customer_view'
    CUSTOMER_CREATE = 'customer_create'
    CUSTOMER_EDIT = 'customer_edit'
    CUSTOMER_DELETE = 'customer_delete'
    
    # 报价单相关权限
    QUOTATION_VIEW = 'quotation_view'
    QUOTATION_CREATE = 'quotation_create'
    QUOTATION_EDIT = 'quotation_edit'
    QUOTATION_DELETE = 'quotation_delete'
    
    # 用户管理相关权限
    USER_VIEW = 'user_view'
    USER_CREATE = 'user_create'
    USER_EDIT = 'user_edit'
    USER_DELETE = 'user_delete'
    
    # 产品编码相关权限
    PRODUCT_VIEW = 'product_view'
    PRODUCT_CODE_VIEW = 'product_code_view'
    PRODUCT_CODE_CREATE = 'product_code_create'
    PRODUCT_CODE_EDIT = 'product_code_edit'
    PRODUCT_CODE_ADMIN = 'product_code_admin'
    
    # 系统管理相关权限
    ADMIN = 'admin'

def check_permission(permission):
    """
    检查当前用户是否具有指定权限
    参数:
        permission: 权限标识符，格式为 'module_action'，如 'customer_view'
    返回:
        bool: 是否拥有权限
    """
    if not current_user.is_authenticated:
        return False
    # admin超级管理员特权
    if getattr(current_user, 'role', None) == 'admin':
        return True
    # 拆分模块和操作
    parts = permission.split('_')
    if len(parts) < 2:
        return False
    module = parts[0]
    action = parts[1]
    # 只查数据库role_permissions表
    from app.models.role_permissions import RolePermission
    role_permission = RolePermission.query.filter_by(role=current_user.role, module=module).first()
    if role_permission:
        if action == 'view':
            return role_permission.can_view
        elif action == 'create':
            return role_permission.can_create
        elif action == 'edit':
            return role_permission.can_edit
        elif action == 'delete':
            return role_permission.can_delete
    return False

def permission_required(resource_type, action):
    """
    权限检查装饰器
    
    参数:
        resource_type: 资源类型 (例如 'project', 'customer')
        action: 操作类型 (例如 'view', 'create', 'edit', 'delete')
    
    用法:
        @app.route('/projects')
        @permission_required('project', 'view')
        def list_projects():
            # ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 构建权限标识符
            permission_name = f"{resource_type}_{action}"
            permission_attr = getattr(Permissions, permission_name.upper(), None)
            
            if permission_attr is None:
                logger.warning(f"未定义的权限: {permission_name}")
                abort(500)
            
            if not check_permission(permission_attr):
                logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试访问无权限的资源: {resource_type}/{action}")
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    管理员权限检查装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            logger.warning(f"非管理员用户 {getattr(current_user, 'username', '未登录')} 尝试访问管理员资源")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def product_manager_required(f):
    """
    产品经理权限检查装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 增加ceo角色支持
        allowed_roles = ['product_manager', 'admin', 'ceo']
        if not current_user.is_authenticated or current_user.role.lower() not in allowed_roles:
            logger.warning(f"非产品经理/CEO用户 {getattr(current_user, 'username', '未登录')} (角色: {getattr(current_user, 'role', '无')}) 尝试访问产品经理资源")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function 