from flask import request, jsonify
from flask_jwt_extended import jwt_required
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response, jwt_required_with_permission
from app.models.user import User, Permission
from app import db
import logging
from app.utils.auth import flexible_auth
from app.models.role_permissions import RolePermission

logger = logging.getLogger(__name__)

# 权限管理相关路由
@api_v1_bp.route('/users/<int:user_id>/permissions', methods=['GET'])
@jwt_required_with_permission('permission', 'view')
def get_user_permissions(user_id):
    """
    获取用户权限（优先查个人权限，无则查角色模板）
    """
    user = User.query.get(user_id)
    if not user:
        return api_response(
            success=False,
            code=404,
            message="用户不存在"
        )
    # 先查个人权限
    permissions = Permission.query.filter_by(user_id=user_id).all()
    if permissions:
        permissions_data = [permission.to_dict() for permission in permissions]
    else:
        # 查角色模板
        from app.models.role_permissions import RolePermission
        perms = RolePermission.query.filter_by(role=user.role).all()
        permissions_data = []
        for perm in perms:
            permissions_data.append({
                'module': perm.module,
                'can_view': perm.can_view,
                'can_create': perm.can_create,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete
            })
    return api_response(
        success=True,
        message="获取成功",
        data={
            "user_id": user_id,
            "username": user.username,
            "permissions": permissions_data
        }
    )

@api_v1_bp.route('/users/<int:user_id>/permissions', methods=['PUT'])
@jwt_required_with_permission('permission', 'edit')
def update_user_permissions(user_id):
    """
    更新用户权限
    """
    user = User.query.get(user_id)
    
    if not user:
        return api_response(
            success=False,
            code=404,
            message="用户不存在"
        )
    
    data = request.get_json()
    
    if not data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
    
    permissions_data = data.get('permissions', [])
    
    if not permissions_data:
        return api_response(
            success=False,
            code=400,
            message="权限数据不能为空"
        )
    
    try:
        # 清除现有权限
        Permission.query.filter_by(user_id=user_id).delete()
        
        # 添加新权限
        for perm_data in permissions_data:
            module = perm_data.get('module')
            can_view = perm_data.get('can_view', False)
            can_create = perm_data.get('can_create', False)
            can_edit = perm_data.get('can_edit', False)
            can_delete = perm_data.get('can_delete', False)
            
            if not module:
                continue
                
            permission = Permission(
                user_id=user_id,
                module=module,
                can_view=can_view,
                can_create=can_create,
                can_edit=can_edit,
                can_delete=can_delete
            )
            db.session.add(permission)
        
        db.session.commit()
        
        return api_response(
            success=True,
            message="权限更新成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新权限失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="更新失败，请稍后重试"
        )

@api_v1_bp.route('/modules', methods=['GET'])
@flexible_auth
def get_modules():
    """
    获取系统模块列表
    """
    # 这里可以从数据库获取，也可以硬编码
    modules = [
        {
            "id": "project",
            "name": "项目管理",
            "description": "管理销售项目和跟进"
        },
        {
            "id": "customer",
            "name": "客户管理",
            "description": "管理客户信息和联系人"
        },
        {
            "id": "quotation",
            "name": "报价管理",
            "description": "管理产品报价"
        },
        {
            "id": "product",
            "name": "产品管理",
            "description": "管理产品信息和价格"
        },
        {
            "id": "product_code",
            "name": "产品编码",
            "description": "管理产品编码系统"
        },
        {
            "id": "user",
            "name": "用户管理",
            "description": "管理系统用户"
        },
        {
            "id": "permission",
            "name": "权限管理",
            "description": "管理用户权限"
        }
    ]
    
    return api_response(
        success=True,
        message="获取成功",
        data=modules
    )

@api_v1_bp.route('/permissions/roles', methods=['GET'])
@flexible_auth
def get_roles_permissions():
    """
    获取所有角色的权限设置
    """
    # 从权限表中获取所有角色的权限
    try:
        from app.permissions import ROLE_PERMISSIONS
        from app.models.user import User, Permission
        import sqlalchemy
        
        # 获取所有可用角色
        all_roles = list(ROLE_PERMISSIONS.keys())
        
        # 准备结果集
        result = []
        
        # 获取所有模块
        modules = ["customer", "project", "quotation", "product", "product_code", "user", "permission"]
        
        # 对于每个角色，获取其权限设置
        for role in all_roles:
            # 查找拥有此角色的用户
            users_with_role = User.query.filter_by(role=role).all()
            
            # 初始化角色权限
            role_permissions = {
                "role": role,
                "permissions": []
            }
            
            # 如果没有此角色的用户，生成默认权限
            if not users_with_role:
                # 为每个模块创建默认权限
                for module in modules:
                    permission = {
                        "module": module,
                        "can_view": role == "admin",
                        "can_create": role == "admin",
                        "can_edit": role == "admin",
                        "can_delete": role == "admin"
                    }
                    role_permissions["permissions"].append(permission)
            else:
                # 获取该角色下的第一个用户的权限
                user = users_with_role[0]
                
                # 收集该用户的所有权限
                for module in modules:
                    permission = Permission.query.filter_by(user_id=user.id, module=module).first()
                    
                    if permission:
                        role_permissions["permissions"].append(permission.to_dict())
                    else:
                        # 如果没有权限记录，则创建默认权限
                        default_permission = {
                            "module": module,
                            "can_view": role == "admin",
                            "can_create": role == "admin",
                            "can_edit": role == "admin",
                            "can_delete": role == "admin"
                        }
                        role_permissions["permissions"].append(default_permission)
            
            result.append(role_permissions)
        
        return api_response(
            success=True,
            message="获取成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取角色权限信息失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="获取角色权限信息失败"
        )

@api_v1_bp.route('/permissions/roles/<role>', methods=['GET'])
@flexible_auth
def get_role_permissions(role):
    """
    获取指定角色的权限设置（只查role_permissions表）
    """
    try:
        # 查询模板权限
        perms = RolePermission.query.filter_by(role=role).all()
        permissions = []
        for perm in perms:
            permissions.append({
                'module': perm.module,
                'can_view': perm.can_view,
                'can_create': perm.can_create,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete
            })
        return api_response(
            success=True,
            message="获取成功",
            data={
                'role': role,
                'permissions': permissions
            }
        )
    except Exception as e:
        logger.error(f"获取角色权限信息失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"获取角色权限信息失败: {str(e)}"
        )

@api_v1_bp.route('/permissions/roles/update', methods=['POST'])
@flexible_auth
def update_role_permissions():
    """
    更新角色的默认权限设置 - 简化版本
    """
    # 记录原始请求
    try:
        logger.info(f"收到角色权限更新请求: {request.data}")
        
        # 确保请求包含有效的JSON数据
        if not request.is_json:
            logger.error("请求不是JSON格式")
            return api_response(
                success=False,
                code=400,
                message="请求必须是JSON格式"
            )
        
        # 尝试获取JSON数据
        try:
            data = request.get_json()
        except Exception as json_err:
            logger.error(f"解析JSON数据失败: {str(json_err)}")
            return api_response(
                success=False,
                code=400,
                message=f"无法解析JSON数据: {str(json_err)}"
            )
        
        # 记录解析后的数据
        logger.info(f"解析后的请求数据: {data}")
        
        # 基本数据验证
        if not data:
            logger.error("请求数据为空")
            return api_response(
                success=False,
                code=400,
                message="请求数据为空"
            )
        
        # 获取角色和权限
        role = data.get('role', '')
        permissions = data.get('permissions', [])
        
        logger.info(f"角色: {role}, 权限数量: {len(permissions)}")
        
        # 更详细的参数验证
        if not role:
            logger.error("未提供角色名称")
            return api_response(
                success=False,
                code=400,
                message="未提供角色名称"
            )
        
        if not permissions or not isinstance(permissions, list):
            logger.error(f"权限数据无效: {permissions}")
            return api_response(
                success=False,
                code=400,
                message="权限数据必须是非空列表"
            )
        
        # 管理员角色不允许修改
        if role == 'admin':
            logger.warning("尝试修改管理员角色权限，已拒绝")
            return api_response(
                success=False,
                code=403,
                message="管理员角色权限不允许修改"
            )
        
        # 导入需要的模块和函数
        try:
            from app.permissions import ROLE_PERMISSIONS
            from app.models.user import User, Permission
            from app import db
        except ImportError as imp_err:
            logger.error(f"导入所需模块失败: {str(imp_err)}")
            return api_response(
                success=False,
                code=500,
                message="服务器配置错误"
            )
        
        # 检查角色是否存在
        if role not in ROLE_PERMISSIONS:
            logger.error(f"角色不存在: {role}")
            return api_response(
                success=False,
                code=404,
                message=f"角色'{role}'不存在"
            )
        
        # 查找具有该角色的所有用户
        try:
            users = User.query.filter_by(role=role).all()
            logger.info(f"找到 {len(users)} 个用户需要更新权限")
        except Exception as db_err:
            logger.error(f"查询用户数据库失败: {str(db_err)}")
            return api_response(
                success=False,
                code=500,
                message="数据库查询错误"
            )
        
        # 如果没有用户，直接返回成功
        if not users:
            logger.info(f"没有找到角色为 '{role}' 的用户，无需更新")
            return api_response(
                success=True,
                message=f"角色'{role}'没有关联用户，无需更新权限"
            )
        
        # 更新每个用户的权限
        updated_count = 0
        error_count = 0
        
        # 使用事务包装所有更新操作
        try:
            for user in users:
                try:
                    # 删除该用户的所有现有权限
                    Permission.query.filter_by(user_id=user.id).delete()
                    
                    # 添加新的权限
                    for perm in permissions:
                        # 确保perm是字典且包含module字段
                        if not isinstance(perm, dict) or 'module' not in perm:
                            continue
                        
                        module = perm.get('module')
                        if not module:
                            continue
                        
                        # 创建新的权限记录
                        permission = Permission(
                            user_id=user.id,
                            module=module,
                            can_view=bool(perm.get('can_view', False)),
                            can_create=bool(perm.get('can_create', False)),
                            can_edit=bool(perm.get('can_edit', False)),
                            can_delete=bool(perm.get('can_delete', False))
                        )
                        db.session.add(permission)
                    
                    updated_count += 1
                    logger.info(f"已更新用户 {user.username} (ID: {user.id}) 的权限")
                except Exception as user_err:
                    error_count += 1
                    logger.error(f"更新用户 {user.username} (ID: {user.id}) 权限时出错: {str(user_err)}")
            
            # 提交所有更改
            db.session.commit()
            logger.info(f"已成功提交 {updated_count} 个用户的权限更新")
            
            # 清除缓存
            try:
                # 简化缓存清除逻辑
                from flask import session
                if 'permissions' in session:
                    del session['permissions']
                logger.info("已清除会话中的权限缓存")
            except Exception as cache_err:
                logger.warning(f"清除权限缓存时出错: {str(cache_err)}")
            
            return api_response(
                success=True,
                message=f"角色权限更新成功，已更新 {updated_count} 个用户的权限"
            )
            
        except Exception as tx_err:
            # 如果发生错误，回滚事务
            db.session.rollback()
            logger.error(f"权限更新事务失败，已回滚: {str(tx_err)}")
            return api_response(
                success=False,
                code=500,
                message="数据库事务错误，请稍后重试"
            )
            
    except Exception as e:
        # 捕获所有异常
        import traceback
        logger.error(f"更新角色权限时发生未预期错误: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return api_response(
            success=False,
            code=500,
            message="服务器处理请求时出错"
        ) 