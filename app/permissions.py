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

# 角色权限映射
ROLE_PERMISSIONS = {
    'admin': [
        # 管理员拥有所有权限
        Permissions.PROJECT_VIEW, Permissions.PROJECT_CREATE, Permissions.PROJECT_EDIT, Permissions.PROJECT_DELETE,
        Permissions.CUSTOMER_VIEW, Permissions.CUSTOMER_CREATE, Permissions.CUSTOMER_EDIT, Permissions.CUSTOMER_DELETE,
        Permissions.QUOTATION_VIEW, Permissions.QUOTATION_CREATE, Permissions.QUOTATION_EDIT, Permissions.QUOTATION_DELETE,
        Permissions.USER_VIEW, Permissions.USER_CREATE, Permissions.USER_EDIT, Permissions.USER_DELETE,
        Permissions.PRODUCT_CODE_VIEW, Permissions.PRODUCT_CODE_CREATE, Permissions.PRODUCT_CODE_EDIT, Permissions.PRODUCT_CODE_ADMIN,
        Permissions.ADMIN
    , Permissions.PRODUCT_VIEW],
    
    # 添加CEO角色的权限
    'ceo': [
        # CEO权限（添加客户查看权限）
        Permissions.PROJECT_VIEW, Permissions.PROJECT_CREATE, Permissions.PROJECT_EDIT,
        Permissions.CUSTOMER_VIEW, Permissions.CUSTOMER_CREATE, Permissions.CUSTOMER_EDIT,
        Permissions.QUOTATION_VIEW, Permissions.QUOTATION_CREATE, Permissions.QUOTATION_EDIT,
        Permissions.USER_VIEW,
        Permissions.PRODUCT_CODE_VIEW,
        Permissions.PRODUCT_VIEW
    ],
    
    # 已废弃：finace_director角色权限请仅在数据库role_permissions表中维护
    'sales': [
        # 销售人员权限
        Permissions.PROJECT_VIEW, Permissions.PROJECT_CREATE, Permissions.PROJECT_EDIT,
        Permissions.CUSTOMER_VIEW, Permissions.CUSTOMER_CREATE, Permissions.CUSTOMER_EDIT,
        Permissions.QUOTATION_VIEW, Permissions.QUOTATION_CREATE,
        Permissions.PRODUCT_CODE_VIEW
    , Permissions.PRODUCT_VIEW],
    'channel_manager': [
        # 渠道经理权限
        Permissions.PROJECT_VIEW, Permissions.PROJECT_CREATE, Permissions.PROJECT_EDIT,
        Permissions.CUSTOMER_VIEW, Permissions.CUSTOMER_CREATE, Permissions.CUSTOMER_EDIT,
        Permissions.QUOTATION_VIEW, Permissions.QUOTATION_CREATE,
        Permissions.PRODUCT_CODE_VIEW
    ],
    'marketing_director': [
        # 营销总监权限
        Permissions.PROJECT_VIEW, Permissions.PROJECT_CREATE, Permissions.PROJECT_EDIT, Permissions.PROJECT_DELETE,
        Permissions.CUSTOMER_VIEW, Permissions.CUSTOMER_CREATE, Permissions.CUSTOMER_EDIT, 
        Permissions.QUOTATION_VIEW, Permissions.QUOTATION_CREATE, Permissions.QUOTATION_EDIT,
        Permissions.USER_VIEW,
        Permissions.PRODUCT_CODE_VIEW
    ],
    'service': [
        # 服务人员权限
        Permissions.PROJECT_VIEW, 
        Permissions.CUSTOMER_VIEW,
        Permissions.QUOTATION_VIEW,
        Permissions.PRODUCT_CODE_VIEW
    ],
    'service_manager': [
        # 服务经理权限
        Permissions.PROJECT_VIEW, Permissions.PROJECT_CREATE,
        Permissions.CUSTOMER_VIEW, Permissions.CUSTOMER_CREATE,
        Permissions.QUOTATION_VIEW, Permissions.QUOTATION_CREATE,
        Permissions.PRODUCT_CODE_VIEW
    ],
    'product_manager': [
        # 产品经理权限
        Permissions.PROJECT_VIEW,
        Permissions.CUSTOMER_VIEW,
        Permissions.QUOTATION_VIEW, Permissions.QUOTATION_CREATE, Permissions.QUOTATION_EDIT,
        Permissions.PRODUCT_CODE_VIEW, Permissions.PRODUCT_CODE_CREATE, Permissions.PRODUCT_CODE_EDIT
    , Permissions.PRODUCT_VIEW],
    'solution_manager': [
        # 解决方案经理权限
        Permissions.PROJECT_VIEW,
        Permissions.CUSTOMER_VIEW,
        Permissions.QUOTATION_VIEW, Permissions.QUOTATION_CREATE, Permissions.QUOTATION_EDIT,
        Permissions.PRODUCT_CODE_VIEW
    , Permissions.PRODUCT_VIEW],
    'user': [
        # 普通用户权限
        Permissions.PROJECT_VIEW,
        Permissions.CUSTOMER_VIEW,
        Permissions.QUOTATION_VIEW,
        Permissions.PRODUCT_CODE_VIEW
    , Permissions.PRODUCT_VIEW],
    'dealer': [
        # 经销商权限
        Permissions.PROJECT_VIEW, Permissions.PROJECT_CREATE,
        Permissions.CUSTOMER_VIEW, Permissions.CUSTOMER_CREATE,
        Permissions.QUOTATION_VIEW,
        Permissions.PRODUCT_CODE_VIEW
    ]
}

def check_permission(permission):
    """
    检查当前用户是否具有指定权限
    
    参数:
        permission: 权限标识符
    
    返回:
        bool: 是否拥有权限
    """
    # 未登录用户没有任何权限
    if not current_user.is_authenticated:
        return False
    
    # 只查数据库role_permissions表
    from app.models.role_permissions import RolePermission
    user_role = getattr(current_user, 'role', 'user')
    # 遍历所有模块，查找是否有该权限
    perms = RolePermission.query.filter_by(role=user_role).all()
    for perm in perms:
        if permission == f"{perm.module}_{'view' if perm.can_view else ''}{'create' if perm.can_create else ''}{'edit' if perm.can_edit else ''}{'delete' if perm.can_delete else ''}":
            return True
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