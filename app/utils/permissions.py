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
        # ⚠️ 取证日志:本函数会「删光该用户全部个人权限」再按一张**过时的角色表**重建
        # (只认 admin/sales/product/product_manager/solution/service/business_admin,
        #  现役的 sales_manager/Treasurer/finace_director 等一律变只读;模块清单也是旧命名)。
        # 2026-08-13 已摘除唯一的运行时调用方(移动端登录 app/api/v1/auth.py),正常情况下
        # 不该再被调到。若日志里出现这行,说明有未知调用方在冲掉管理员配好的权限 —— 顺着
        # 调用栈去查。详见 config_management.api_reset_user_permissions 与本文件顶部说明。
        import traceback
        caller = ''.join(traceback.format_stack(limit=6)[:-1]).strip()
        logger.warning(
            f"[权限重建] 正在删除并重建用户 {user.username} (ID: {user.id}, 角色: {user.role}) "
            f"的全部个人权限,调用栈:\n{caller}"
        )

        # 定义模块列表
        modules = ['customer', 'project', 'quotation', 'product', 'product_code', 'user', 'permission', 'inventory', 'settlement', 'order', 'system_diagram']
        
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
            elif user.role == 'product_manager':
                # 产品经理可以创建和编辑产品
                if module == 'product':
                    can_create = True
                    can_edit = True
                    can_delete = True
                # 产品经理可以管理产品编码（研发产品管理）
                if module == 'product_code':
                    can_view = True
                    can_create = True
                    can_edit = True
                    can_delete = True
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
            elif user.role == 'business_admin':
                # 商务助理可以查看和编辑客户、项目和报价
                if module in ['customer', 'project', 'quotation']:
                    can_create = True
                    can_edit = True
                    can_delete = True
                # 商务助理可以查看库存
                if module in ['inventory', 'settlement', 'order']:
                    can_view = True
            
            # 用户和权限模块默认只有管理员可以访问
            if module in ['user', 'permission'] and user.role != 'admin':
                can_view = False
            
            # 库存管理模块权限设置
            if module in ['inventory', 'settlement', 'order']:
                if user.role == 'admin':
                    # 管理员拥有所有库存管理权限
                    can_view = True
                    can_create = True
                    can_edit = True
                    can_delete = True
                elif user.role in ['business_admin', 'ceo']:
                    # 商务助理和CEO可以查看、创建、编辑
                    can_view = True
                    can_create = True
                    can_edit = True
                    can_delete = False
                elif user.role in ['solution', 'service', 'sales']:
                    # 解决方案、服务、销售可以查看
                    can_view = True
                    can_create = False
                    can_edit = False
                    can_delete = False
                else:
                    # 其他角色默认无库存管理权限
                    can_view = False
                    can_create = False
                    can_edit = False
                    can_delete = False
            
            # 系统设计模块：内容创建模块，启用即拥有 create+edit（不给 delete）
            if module == 'system_diagram':
                if user.role == 'admin':
                    can_view = True
                    can_create = True
                    can_edit = True
                    can_delete = True
                elif user.role not in ['user', 'permission']:
                    # 所有业务角色都可以创建和编辑自己的系统设计图
                    can_view = True
                    can_create = True
                    can_edit = True
                    can_delete = False

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


def get_accessible_users_by_permission_only(current_user, context_module=None):
    """
    获取当前用户可访问的用户列表（仅基于权限级别，不包含数据归属）

    用于非业务数据模块（如账户管理、权限管理），这些模块不应受业务数据归属关系影响。

    权限优先级（从高到低）：
    1. admin 管理员特权：可访问所有用户
    2. 权限模块数据权限：system > company > department > personal

    参数:
        current_user: 当前登录用户
        context_module: 上下文模块名称，如 'user_management', 'permission_management' 等

    返回:
        list: 可访问的用户列表
    """
    try:
        if not current_user or not current_user.is_authenticated:
            return []

        # 1. admin 管理员特权：可以查看所有用户（最高优先级）
        # 注意：账户管理模块需要看到所有用户，包括未激活的，否则无法管理
        if current_user.role == 'admin':
            return User.query.all()

        # 2. 权限模块数据权限（第二优先级）
        # 根据上下文模块检查相应的权限
        permission_modules_to_check = []
        if context_module:
            permission_modules_to_check.append(context_module)
        else:
            # 如果没有指定上下文模块，检查常见的用户访问相关权限
            permission_modules_to_check = ['user_management', 'permission_management', 'user']

        highest_permission_level = 'personal'

        for module in permission_modules_to_check:
            if current_user.has_permission(module, 'view'):
                module_permission_level = current_user.get_permission_level(module)

                # 选择最高的权限级别
                if module_permission_level == 'system':
                    highest_permission_level = 'system'
                    break  # 系统级是最高权限，无需继续检查
                elif module_permission_level == 'company' and highest_permission_level in ['personal', 'department']:
                    highest_permission_level = 'company'
                elif module_permission_level == 'department' and highest_permission_level == 'personal':
                    highest_permission_level = 'department'

        # 根据最高权限级别确定可访问范围
        # 注意：不再过滤 _is_active，因为账户管理需要能看到所有用户状态
        if highest_permission_level == 'system':
            # 系统级权限：可以查看所有用户（包括未激活）
            return User.query.all()
        elif highest_permission_level == 'company' and current_user.company_name:
            # 企业级权限：可以查看企业下所有用户
            accessible_users = User.query.filter(
                User.company_name == current_user.company_name
            ).order_by(User.real_name, User.username).all()
            logger.info(f"用户 {current_user.username} 通过模块 {context_module or '默认'} 的 company 级权限可访问 {len(accessible_users)} 个用户")
            return accessible_users
        elif highest_permission_level == 'department' and current_user.department and current_user.company_name:
            # 部门级权限：可以查看部门下所有用户
            accessible_users = User.query.filter(
                User.department == current_user.department,
                User.company_name == current_user.company_name
            ).order_by(User.real_name, User.username).all()
            logger.info(f"用户 {current_user.username} 通过模块 {context_module or '默认'} 的 department 级权限可访问 {len(accessible_users)} 个用户")
            return accessible_users
        else:  # personal
            # 个人级权限：只能查看自己
            logger.info(f"用户 {current_user.username} 通过模块 {context_module or '默认'} 的 personal 级权限只能访问自己")
            return [current_user]

    except Exception as e:
        logger.error(f"获取可访问用户列表失败: {str(e)}")
        return [current_user] if current_user and current_user.is_authenticated else []


def get_accessible_users(current_user, context_module=None):
    """
    获取当前用户可访问的用户列表（用于绩效统计、用户管理等功能）
    统一基于权限模块、部门负责人权限和数据归属关系控制用户访问范围

    权限优先级（从高到低）：
    1. admin 管理员特权：可访问所有用户
    2. 权限模块数据权限：system > company > department > personal
    3. 部门负责人权限：可访问本部门用户
    4. 数据归属设置：基于Affiliation模型的明确授权

    参数:
        current_user: 当前登录用户
        context_module: 上下文模块名称，如 'user_management', 'config_management' 等

    返回:
        list: 可访问的用户列表
    """
    try:
        if not current_user or not current_user.is_authenticated:
            return []
        
        # 1. admin 管理员特权：可以查看所有用户（最高优先级）
        if current_user.role == 'admin':
            return User.query.filter(User._is_active == True).all()
        
        # 收集可访问的用户ID
        accessible_user_ids = set([current_user.id])  # 始终可以查看自己
        
        # 2. 权限模块数据权限（第二优先级）
        # 根据上下文模块检查相应的权限
        permission_modules_to_check = []
        if context_module:
            permission_modules_to_check.append(context_module)
        else:
            # 如果没有指定上下文模块，检查常见的用户访问相关权限
            permission_modules_to_check = ['user_management', 'config_management', 'user']
        
        highest_permission_level = 'personal'
        
        for module in permission_modules_to_check:
            if current_user.has_permission(module, 'view'):
                module_permission_level = current_user.get_permission_level(module)
                
                # 选择最高的权限级别
                if module_permission_level == 'system':
                    highest_permission_level = 'system'
                    break  # 系统级是最高权限，无需继续检查
                elif module_permission_level == 'company' and highest_permission_level in ['personal', 'department']:
                    highest_permission_level = 'company'
                elif module_permission_level == 'department' and highest_permission_level == 'personal':
                    highest_permission_level = 'department'
        
        # 根据最高权限级别确定可访问范围
        if highest_permission_level == 'system':
            # 系统级权限：可以查看所有用户
            return User.query.filter(User._is_active == True).all()
        elif highest_permission_level == 'company' and current_user.company_name:
            # 企业级权限：可以查看企业下所有用户
            company_users = User.query.filter(
                User.company_name == current_user.company_name,
                User._is_active == True
            ).all()
            accessible_user_ids.update([u.id for u in company_users])
        elif highest_permission_level == 'department' and current_user.department and current_user.company_name:
            # 部门级权限：可以查看部门下所有用户
            dept_users = User.query.filter(
                User.department == current_user.department,
                User.company_name == current_user.company_name,
                User._is_active == True
            ).all()
            accessible_user_ids.update([u.id for u in dept_users])
        
        # 3. 检查模块是否支持数据归属
        # 只有业务数据模块才应用部门负责人权限和数据归属
        from app.utils.module_metadata import module_supports_affiliation
        module_supports_aff = module_supports_affiliation(context_module) if context_module else True

        if module_supports_aff:
            # 3a. 部门负责人权限（仅业务数据模块）
            if (hasattr(current_user, 'is_department_manager') and current_user.is_department_manager
                  and current_user.department):
                dept_users = User.query.filter(
                    User.department == current_user.department,
                    User._is_active == True
                ).all()
                accessible_user_ids.update([u.id for u in dept_users])

            # 3b. 数据归属设置（仅业务数据模块）
            from app.models.user import Affiliation
            affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
            for affiliation in affiliations:
                affiliated_user = User.query.filter(
                    User.id == affiliation.owner_id,
                    User._is_active == True
                ).first()
                if affiliated_user:
                    accessible_user_ids.add(affiliated_user.id)

            logger.debug(f"模块 {context_module} 支持数据归属，已应用部门负责人和Affiliation权限")
        else:
            logger.debug(f"模块 {context_module} 不支持数据归属，跳过部门负责人和Affiliation权限")
        
        # 5. 根据收集到的用户ID获取用户对象
        accessible_users = User.query.filter(
            User.id.in_(accessible_user_ids),
            User._is_active == True
        ).order_by(User.real_name, User.username).all()
        
        logger.info(f"用户 {current_user.username} 通过模块 {context_module or '默认'} 可访问 {len(accessible_users)} 个用户的数据，最高权限级别: {highest_permission_level}")
        return accessible_users
        
    except Exception as e:
        logger.error(f"获取可访问用户列表失败: {str(e)}")
        return [current_user] if current_user and current_user.is_authenticated else [] 