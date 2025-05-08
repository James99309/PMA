"""
权限管理模块
用于定义和检查用户权限
"""
from functools import wraps
from flask import abort, request, g, current_app, flash, redirect, url_for
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

class Permissions:
    """权限常量定义"""
    # 项目相关权限
    PROJECT_VIEW = 'project:view'
    PROJECT_CREATE = 'project:create'
    PROJECT_EDIT = 'project:edit'
    PROJECT_DELETE = 'project:delete'
    
    # 客户相关权限
    CUSTOMER_VIEW = 'customer:view'
    CUSTOMER_CREATE = 'customer:create'
    CUSTOMER_EDIT = 'customer:edit'
    CUSTOMER_DELETE = 'customer:delete'
    
    # 报价单相关权限
    QUOTATION_VIEW = 'quotation:view'
    QUOTATION_CREATE = 'quotation:create'
    QUOTATION_EDIT = 'quotation:edit'
    QUOTATION_DELETE = 'quotation:delete'
    
    # 用户管理相关权限
    USER_VIEW = 'user:view'
    USER_CREATE = 'user:create'
    USER_EDIT = 'user:edit'
    USER_DELETE = 'user:delete'
    
    # 产品编码相关权限
    PRODUCT_CODE_VIEW = 'product_code:view'
    PRODUCT_CODE_CREATE = 'product_code:create'
    PRODUCT_CODE_EDIT = 'product_code:edit'
    PRODUCT_CODE_ADMIN = 'product_code:admin'
    
    # 系统管理相关权限
    PRODUCT_VIEW = 'product:view'
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
    ],
    'finace_director': [
        # 财务总监权限
        Permissions.PROJECT_VIEW,
        Permissions.CUSTOMER_VIEW,
        Permissions.QUOTATION_VIEW,
        Permissions.PRODUCT_VIEW
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
    
    # 获取用户角色（转为小写，避免大小写问题）
    user_role = getattr(current_user, 'role', 'user').lower()
    
    # 匹配角色权限（不区分大小写）
    role_permissions = None
    for role, permissions in ROLE_PERMISSIONS.items():
        if role.lower() == user_role:
            role_permissions = permissions
            break
    
    # 如果找不到角色权限，使用默认空列表
    if role_permissions is None:
        role_permissions = []
    
    # 检查权限
    return permission in role_permissions

def permission_required(module, action):
    """
    权限检查装饰器
    
    参数:
        module: 模块名称 (project, customer, quotation, user等)
        action: 操作名称 (view, create, edit, delete等)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            permission = f"{module}:{action}"
            # 未登录用户重定向到登录页
            if not current_user.is_authenticated:
                flash('请先登录', 'warning')
                return redirect(url_for('auth.login'))
            
            # 检查用户是否有该权限
            if not check_permission(permission):
                # 使用数据库检查用户权限(如果check_permission没有找到)
                if hasattr(current_user, 'has_permission') and callable(current_user.has_permission):
                    if not current_user.has_permission(module, action):
                        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试访问无权限的资源: {module}/{action}")
                        flash('您没有权限访问此页面', 'danger')
                        abort(403)
                else:
                    logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试访问无权限的资源: {module}/{action}")
                    flash('您没有权限访问此页面', 'danger')
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