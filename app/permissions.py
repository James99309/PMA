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
    QUOTATION_APPROVAL_CREATE = 'quotation_approval_create'  # 报价审核权限
    
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
    
    # 库存管理相关权限
    INVENTORY_VIEW = 'inventory_view'
    INVENTORY_CREATE = 'inventory_create'
    INVENTORY_EDIT = 'inventory_edit'
    INVENTORY_DELETE = 'inventory_delete'
    
    # 结算单相关权限
    SETTLEMENT_VIEW = 'settlement_view'
    SETTLEMENT_CREATE = 'settlement_create'
    SETTLEMENT_EDIT = 'settlement_edit'
    SETTLEMENT_DELETE = 'settlement_delete'
    
    # 订单相关权限
    ORDER_VIEW = 'order_view'
    ORDER_CREATE = 'order_create'
    ORDER_EDIT = 'order_edit'
    ORDER_DELETE = 'order_delete'

def is_admin_or_ceo(user=None):
    """
    检查用户是否是管理员或总经理，拥有最高权限
    
    参数:
        user: 用户对象，如果为None则使用current_user
    返回:
        bool: 是否拥有管理员级别权限
    """
    if user is None:
        user = current_user
    
    if not user or not user.is_authenticated:
        return False
    
    user_role = getattr(user, 'role', '').strip().lower()
    return user_role in ['admin', 'ceo']

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
    # admin和CEO超级管理员特权
    if is_admin_or_ceo():
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

def permission_required(module, action):
    """
    权限检查装饰器
    
    参数:
        module: 模块名称 (例如 'project', 'customer', 'product_code')
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
            if not current_user.is_authenticated:
                abort(401)  # 未授权
            
            # 检查权限
            current_app.logger.debug(f"Checking permission: module={module}, action={action}")
            if not current_user.has_permission(module, action):
                current_app.logger.warning(f"Permission denied: user_id={current_user.id}, username={current_user.username}, role={current_user.role}, module={module}, action={action}")
                abort(403)  # 禁止访问
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    管理员权限检查装饰器（包括CEO）
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_or_ceo():
            user_role = getattr(current_user, 'role', '未知') if current_user.is_authenticated else '未登录'
            logger.warning(f"非管理员/CEO用户 {getattr(current_user, 'username', '未登录')} (角色: {user_role}) 尝试访问管理员资源")
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

def approval_view_permission_required(object_type_param, object_id_param):
    """
    审批上下文权限检查装饰器
    
    这个装饰器会检查用户是否有权限查看业务对象，包括：
    1. 如果用户是当前审批人，则允许查看（即使平时没有查看权限）
    2. 如果用户不是审批人，则检查常规权限
    
    参数:
        object_type_param: 业务对象类型参数名（在路由参数或函数参数中的名称）
        object_id_param: 业务对象ID参数名（在路由参数或函数参数中的名称）
    
    用法:
        @app.route('/project/<int:project_id>/detail')
        @approval_view_permission_required('project', 'project_id')
        def view_project_detail(project_id):
            # ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # 未授权
            
            # 获取业务对象类型和ID
            if isinstance(object_type_param, str):
                object_type = object_type_param
            else:
                # 如果是函数，则调用获取对象类型
                object_type = object_type_param(*args, **kwargs)
            
            # 从路由参数或函数参数中获取对象ID
            object_id = kwargs.get(object_id_param)
            if object_id is None:
                # 如果在kwargs中找不到，尝试从args中获取
                # 这需要根据具体的路由定义来确定参数位置
                current_app.logger.error(f"无法获取对象ID参数: {object_id_param}")
                abort(400)  # 错误请求
            
            # 检查审批上下文权限
            from app.utils.access_control import has_approval_view_permission
            if not has_approval_view_permission(current_user, object_type, object_id):
                current_app.logger.warning(f"审批权限检查失败: user_id={current_user.id}, username={current_user.username}, role={current_user.role}, object_type={object_type}, object_id={object_id}")
                abort(403)  # 禁止访问
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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