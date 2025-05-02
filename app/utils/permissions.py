"""权限工具模块"""
import logging
from app import db
from app.models.user import Permission, User
from functools import wraps
from flask import abort, current_app, g
from flask_login import current_user

logger = logging.getLogger(__name__)

def assign_user_default_permissions(user):
    """
    为新用户分配默认权限
    这将根据用户角色分配不同的默认权限
    
    参数:
        user: User实例，需要分配权限的用户
    
    返回:
        bool: 操作是否成功
    """
    try:
        logger.info(f"为用户 {user.username} (ID: {user.id}) 分配默认权限")
        
        # 定义模块列表
        modules = ['customer', 'project', 'quotation', 'product', 'product_code', 'user', 'permission']
        
        # 删除该用户现有的所有权限（如果有）
        Permission.query.filter_by(user_id=user.id).delete()
        
        # 为每个模块创建权限记录
        for module in modules:
            # 默认普通用户只有查看权限
            can_view = True
            can_create = False
            can_edit = False
            can_delete = False
            
            # 根据角色分配更多权限
            if user.role == 'admin':
                # 管理员拥有所有权限
                can_create = True
                can_edit = True
                can_delete = True
            elif user.role == 'sales':
                # 销售可以创建和编辑客户、项目和报价
                if module in ['customer', 'project', 'quotation']:
                    can_create = True
                    can_edit = True
            elif user.role == 'product':
                # 产品经理可以创建和编辑产品
                if module == 'product':
                    can_create = True
                    can_edit = True
                    can_delete = True
                # 产品经理可以查看产品编码
                if module == 'product_code':
                    can_view = True
            elif user.role == 'solution':
                # 解决方案经理可以查看和编辑项目
                if module in ['project', 'quotation']:
                    can_edit = True
            elif user.role == 'service':
                # 服务经理可以查看和编辑项目及客户
                if module in ['project', 'customer']:
                    can_edit = True
                # 服务经理可以查看报价单
                if module == 'quotation':
                    can_view = True
            
            # 用户和权限模块默认只有管理员可以访问
            if module in ['user', 'permission'] and user.role != 'admin':
                can_view = False
            
            # 创建权限记录
            permission = Permission(
                user_id=user.id,
                module=module,
                can_view=can_view,
                can_create=can_create,
                can_edit=can_edit,
                can_delete=can_delete
            )
            db.session.add(permission)
        
        # 提交变更
        db.session.commit()
        logger.info(f"用户 {user.username} 默认权限分配完成")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"为用户 {user.username} 分配默认权限失败: {str(e)}")
        return False

def update_role_users_permissions(role, permissions_data):
    """
    更新指定角色所有用户的权限
    
    参数:
        role: 角色名称
        permissions_data: 权限数据列表，包含每个模块的权限设置
        
    返回:
        tuple: (是否成功, 更新用户数量)
    """
    try:
        logger.info(f"开始更新角色 '{role}' 的所有用户权限")
        logger.info(f"权限数据: {permissions_data}")
        
        # 如果是管理员角色，不允许修改
        if role == 'admin':
            logger.warning("尝试修改管理员角色权限，已拒绝")
            return False, 0
        
        # 查找所有该角色的用户
        users = User.query.filter_by(role=role).all()
        
        if not users:
            logger.info(f"没有找到角色为 '{role}' 的用户")
            return True, 0
        
        logger.info(f"找到 {len(users)} 个用户需要更新权限")
        
        # 基本验证权限数据
        if not isinstance(permissions_data, list):
            logger.error(f"权限数据格式错误，不是列表: {type(permissions_data)}")
            return False, 0
        
        # 更新每个用户的权限
        updated_count = 0
        updated_user_ids = []
        
        for user in users:
            try:
                logger.info(f"开始更新用户 {user.username} (ID: {user.id}) 的权限")
                
                # 删除现有权限
                deleted_count = Permission.query.filter_by(user_id=user.id).delete()
                logger.info(f"删除了 {deleted_count} 条现有权限记录")
                
                # 添加新权限
                successful_modules = []
                failed_modules = []
                
                for perm_data in permissions_data:
                    try:
                        if not isinstance(perm_data, dict):
                            logger.warning(f"跳过非字典格式的权限数据: {perm_data}")
                            continue
                            
                        module = perm_data.get('module')
                        
                        if not module:
                            logger.warning(f"跳过缺少module字段的权限数据: {perm_data}")
                            continue
                        
                        # 创建新权限记录
                        permission = Permission(
                            user_id=user.id,
                            module=module,
                            can_view=bool(perm_data.get('can_view', False)),
                            can_create=bool(perm_data.get('can_create', False)),
                            can_edit=bool(perm_data.get('can_edit', False)),
                            can_delete=bool(perm_data.get('can_delete', False))
                        )
                        db.session.add(permission)
                        successful_modules.append(module)
                    except Exception as module_error:
                        failed_modules.append(module)
                        logger.error(f"为用户 {user.username} 添加模块 {module} 的权限时出错: {str(module_error)}")
                
                logger.info(f"用户 {user.username} 成功更新的模块: {successful_modules}")
                if failed_modules:
                    logger.warning(f"用户 {user.username} 更新失败的模块: {failed_modules}")
                
                updated_count += 1
                updated_user_ids.append(user.id)
                logger.info(f"已更新用户 {user.username} (ID: {user.id}) 的权限")
            except Exception as user_error:
                logger.error(f"更新用户 {user.username} (ID: {user.id}) 权限时出错: {str(user_error)}")
        
        try:
            # 提交所有更改
            logger.info("提交数据库事务...")
            db.session.commit()
            logger.info("数据库事务提交成功")
            
            # 清除每个更新过权限的用户的缓存
            for user_id in updated_user_ids:
                clear_user_permissions_cache(user_id)
                
            logger.info(f"角色 '{role}' 的用户权限更新完成，共更新了 {updated_count} 个用户")
            return True, updated_count
        except Exception as commit_error:
            db.session.rollback()
            logger.error(f"提交数据库事务失败: {str(commit_error)}")
            return False, 0
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"批量更新角色 '{role}' 用户权限失败: {str(e)}")
        logger.error(f"错误详情: {error_trace}")
        return False, 0

def clear_user_permissions_cache(user_id=None):
    """
    清除用户的权限缓存，使修改后的权限设置立即生效
    
    参数:
        user_id: 指定用户ID，如果为None则清除所有用户的缓存
    
    返回:
        bool: 操作是否成功
    """
    try:
        from flask import session, current_app
        
        # 如果使用了Redis缓存，这里可以添加Redis缓存清理逻辑
        if current_app.config.get('REDIS_URL'):
            try:
                import redis
                from flask import g
                
                redis_client = redis.from_url(current_app.config['REDIS_URL'])
                
                if user_id:
                    # 清除特定用户的权限缓存
                    redis_client.delete(f"user_permissions:{user_id}")
                    logger.info(f"已清除用户ID:{user_id}的Redis权限缓存")
                else:
                    # 清除所有用户的权限缓存
                    keys = redis_client.keys("user_permissions:*")
                    if keys:
                        redis_client.delete(*keys)
                        logger.info(f"已清除所有用户的Redis权限缓存, 共{len(keys)}条")
                
            except Exception as redis_error:
                logger.error(f"清除Redis权限缓存失败: {str(redis_error)}")
        
        # 会话中如果存储了权限信息，也需要清理
        # 注意：这只会影响当前请求会话
        if 'permissions' in session:
            del session['permissions']
            logger.info("已清除会话中的权限缓存")
        
        return True
    except Exception as e:
        logger.error(f"清除权限缓存失败: {str(e)}")
        return False

def permission_required(module, action):
    """
    检查用户是否具有指定模块的指定操作权限的装饰器
    
    参数:
        module (str): 模块名称，如'project', 'customer'等
        action (str): 操作名称，如'create', 'view', 'edit', 'delete'等
    
    用法示例:
        @permission_required('project', 'view')
        def list_projects():
            # 函数内容
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查当前用户是否登录
            if not current_user.is_authenticated:
                abort(401)  # 未授权
                
            # 管理员有所有权限
            if current_user.role == 'admin':
                return f(*args, **kwargs)
                
            # 从当前用户对象获取权限
            if hasattr(current_user, 'has_permission'):
                if current_user.has_permission(module, action):
                    return f(*args, **kwargs)
            
            # 没有权限
            abort(403)  # 禁止访问
            
        return decorated_function
    return decorator 