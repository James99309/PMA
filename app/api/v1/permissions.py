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
@flexible_auth
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
                'can_delete': perm.can_delete,
                'can_change_owner': getattr(perm, 'can_change_owner', False),
                'can_export_email': getattr(perm, 'can_export_email', False)
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
@flexible_auth
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
        # === 性能优化：批量删除 ===
        Permission.query.filter_by(user_id=user_id).delete(synchronize_session=False)

        # === 性能优化：构建批量插入数据 ===
        permission_records = []
        for perm_data in permissions_data:
            module = perm_data.get('module')
            if not module:
                continue

            can_view = perm_data.get('can_view', False)
            can_create = perm_data.get('can_create', False)
            can_edit = perm_data.get('can_edit', False)
            can_delete = perm_data.get('can_delete', False)
            can_change_owner = perm_data.get('can_change_owner', False)
            can_export_email = perm_data.get('can_export_email', False)
            permission_level = perm_data.get('permission_level', 'personal')

            # 数据一致性验证：如果permission_level为'none'，强制所有权限为False
            if permission_level == 'none':
                can_view = False
                can_create = False
                can_edit = False
                can_delete = False
                can_change_owner = False
                can_export_email = False
                logger.info(f"✅ 数据一致性保护：模块 {module} level='none'，已强制清空所有权限")

            permission_records.append({
                'user_id': user_id,
                'module': module,
                'can_view': can_view,
                'can_create': can_create,
                'can_edit': can_edit,
                'can_delete': can_delete,
                'can_change_owner': can_change_owner,
                'can_export_email': can_export_email,
                'permission_level': permission_level,
                'permission_level_description': perm_data.get('permission_level_description'),
                'pricing_discount_limit': perm_data.get('pricing_discount_limit'),
                'settlement_discount_limit': perm_data.get('settlement_discount_limit'),
                'content_filters': perm_data.get('content_filters')
            })

        # === 性能优化：批量插入 ===
        if permission_records:
            db.session.bulk_insert_mappings(Permission, permission_records)

        db.session.commit()

        logger.info(f"成功更新用户 {user_id} 的个人权限，共 {len(permission_records)} 个模块")

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
    获取系统模块列表（从配置文件读取）
    """
    from app.utils.module_metadata import MODULE_METADATA

    # 从配置文件生成模块列表
    modules = [
        {
            "id": module_id,
            "name": meta['name'],
            "description": meta.get('description', f"管理{meta['name']}")
        }
        for module_id, meta in MODULE_METADATA.items()
    ]

    # 按模块名称排序
    modules.sort(key=lambda x: x['name'])

    return api_response(
        success=True,
        message="获取成功",
        data=modules
    )

@api_v1_bp.route('/permissions/module-metadata', methods=['GET'])
@flexible_auth
def get_module_metadata():
    """
    获取模块完整元数据（包括图标、特殊权限能力、权限级别定义）
    """
    from app.utils.module_metadata import MODULE_METADATA, PERMISSION_LEVELS

    return api_response(
        success=True,
        message="获取成功",
        data={
            'modules': MODULE_METADATA,
            'levels': PERMISSION_LEVELS
        }
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
                'can_delete': perm.can_delete,
                'can_change_owner': getattr(perm, 'can_change_owner', False),
                'can_export_email': getattr(perm, 'can_export_email', False),
                'permission_level': perm.permission_level,
                'permission_level_description': perm.permission_level_description,
                'pricing_discount_limit': perm.pricing_discount_limit,
                'settlement_discount_limit': perm.settlement_discount_limit,
                'content_filters': perm.content_filters
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
        
        # 获取角色和权限 (清理role参数,防止制表符等空白字符)
        role = data.get('role', '').strip()
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
            from app.models.user import User, Permission
            from app.models.role_permissions import RolePermission
            from app.models.dictionary import Dictionary
            from app import db
        except ImportError as imp_err:
            logger.error(f"导入所需模块失败: {str(imp_err)}")
            return api_response(
                success=False,
                code=500,
                message="服务器配置错误"
            )
        
        # 检查角色是否存在于字典中
        role_dict = Dictionary.query.filter_by(type='role', key=role).first()
        if not role_dict:
            logger.error(f"角色不存在: {role}")
            return api_response(
                success=False,
                code=404,
                message=f"角色'{role}'不存在"
            )
        
        # 更新角色权限模板（role_permissions表）
        try:
            # 删除该角色的所有现有权限模板
            RolePermission.query.filter_by(role=role).delete()
            
            # 添加新的权限模板
            for perm in permissions:
                # 确保perm是字典且包含module字段
                if not isinstance(perm, dict) or 'module' not in perm:
                    continue
                
                module = perm.get('module')
                if not module:
                    continue
                
                # 获取权限状态
                can_view = bool(perm.get('can_view', False))
                can_create = bool(perm.get('can_create', False))
                can_edit = bool(perm.get('can_edit', False))
                can_delete = bool(perm.get('can_delete', False))
                permission_level = perm.get('permission_level', 'personal')

                # 🆕 数据一致性验证：如果permission_level为'none'，强制所有权限为False
                if permission_level == 'none':
                    can_view = False
                    can_create = False
                    can_edit = False
                    can_delete = False
                    logger.info(f"✅ 数据一致性保护：模块 {module} level='none'，已强制清空所有权限")
                    # level='none'时跳过其他智能修正逻辑
                elif permission_level == 'personal' and can_create is False:
                    # 🆕 智能修正逻辑1：仅个人级别需要创建权限保底
                    can_create = True
                    logger.info(f"✅ 智能修正：模块 {module} 个人级别创建权限已自动设置为True（保底规则）")

                # 🆕 智能修正逻辑2：个人级别自动开启所有权限（保底规则）
                if permission_level == 'personal':
                    # 个人级别的含义：只能查看自己的数据，但对自己的数据拥有完整管理权
                    # 因此确保所有权限都开启
                    corrected = []
                    if not can_view:
                        can_view = True
                        corrected.append('查看')
                    if not can_create:
                        can_create = True
                        corrected.append('创建')
                    if not can_edit:
                        can_edit = True
                        corrected.append('编辑')
                    if not can_delete:
                        can_delete = True
                        corrected.append('删除')

                    if corrected:
                        logger.info(f"✅ 智能修正：模块 {module} 个人级别权限已自动补全 [{', '.join(corrected)}]")

                # 检查是否有任何权限
                has_any_permission = can_view or can_create or can_edit or can_delete

                # 如果没有任何权限，权限级别强制设置为personal（但不覆盖none级别）
                if not has_any_permission and permission_level != 'none':
                    permission_level = 'personal'
                    logger.info(f"⚠️ 模块 {module} 没有任何权限，权限级别重置为 personal")

                # 创建新的角色权限记录
                role_permission = RolePermission(
                    role=role,
                    module=module,
                    can_view=can_view,
                    can_create=can_create,
                    can_edit=can_edit,
                    can_delete=can_delete,
                    can_change_owner=perm.get('can_change_owner', False),
                    can_export_email=perm.get('can_export_email', False),
                    permission_level=permission_level,
                    permission_level_description=perm.get('permission_level_description'),
                    pricing_discount_limit=perm.get('pricing_discount_limit'),
                    settlement_discount_limit=perm.get('settlement_discount_limit'),
                    content_filters=perm.get('content_filters')
                )
                db.session.add(role_permission)
            
            # 提交所有更改
            db.session.commit()
            logger.info(f"已成功更新角色 {role} 的权限模板")
            
            return api_response(
                success=True,
                message=f"角色'{role}'权限模板更新成功"
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


# =============================================
# 子功能权限 API
# =============================================

@api_v1_bp.route('/permissions/modules', methods=['GET'])
@flexible_auth
def get_permission_modules():
    """
    获取权限模块列表（从数据库读取）

    返回所有有效的权限模块，包括子功能列表
    """
    from flask import session
    from app.models.permission_module import PermissionModule, PermissionModuleFeature

    lang = session.get('language', 'zh')

    try:
        modules = PermissionModule.query.filter_by(is_active=True)\
            .order_by(PermissionModule.group_name, PermissionModule.sort_order).all()

        result = []
        for m in modules:
            # 获取模块的子功能
            features = PermissionModuleFeature.query.filter_by(
                module_id=m.module_id,
                is_active=True
            ).order_by(PermissionModuleFeature.sort_order).all()

            result.append({
                'id': m.module_id,
                'module_id': m.module_id,
                'name': m.name_en if lang == 'en' and m.name_en else m.name,
                'icon': m.icon,
                'description': m.description_en if lang == 'en' and m.description_en else m.description,
                'group': m.group_name_en if lang == 'en' and m.group_name_en else m.group_name,
                'group_name': m.group_name,
                'sort_order': m.sort_order,
                'supports_discount': m.supports_discount,
                'supports_owner_change': m.supports_owner_change,
                'supports_affiliation': m.supports_affiliation,
                'supports_content_filter': m.supports_content_filter,
                'supports_export_email': getattr(m, 'supports_export_email', False),
                'features': [f.to_dict(lang) for f in features]
            })

        return api_response(
            success=True,
            message="获取成功",
            data=result
        )
    except Exception as e:
        logger.error(f"获取权限模块列表失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"获取失败: {str(e)}"
        )


@api_v1_bp.route('/permissions/modules/<module_id>/features', methods=['GET'])
@flexible_auth
def get_module_features(module_id):
    """
    获取指定模块的子功能列表
    """
    from flask import session
    from app.models.permission_module import PermissionModuleFeature

    lang = session.get('language', 'zh')

    try:
        features = PermissionModuleFeature.query.filter_by(
            module_id=module_id,
            is_active=True
        ).order_by(PermissionModuleFeature.sort_order).all()

        return api_response(
            success=True,
            message="获取成功",
            data=[f.to_dict(lang) for f in features]
        )
    except Exception as e:
        logger.error(f"获取模块子功能失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"获取失败: {str(e)}"
        )


@api_v1_bp.route('/permissions/roles/<role>/features', methods=['GET'])
@flexible_auth
def get_role_feature_permissions(role):
    """
    获取角色的子功能权限配置
    """
    from app.models.permission_module import RoleFeaturePermission

    try:
        perms = RoleFeaturePermission.query.filter_by(role=role).all()

        result = {}
        for perm in perms:
            if perm.module_id not in result:
                result[perm.module_id] = {}
            result[perm.module_id][perm.feature_id] = perm.is_enabled

        return api_response(
            success=True,
            message="获取成功",
            data={
                'role': role,
                'feature_permissions': result
            }
        )
    except Exception as e:
        logger.error(f"获取角色子功能权限失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"获取失败: {str(e)}"
        )


@api_v1_bp.route('/permissions/roles/<role>/features', methods=['PUT'])
@flexible_auth
def update_role_feature_permissions(role):
    """
    更新角色的子功能权限配置

    请求体:
    {
        "feature_permissions": {
            "module_id": {
                "feature_id": true/false,
                ...
            },
            ...
        }
    }
    """
    import time
    from app.models.permission_module import RoleFeaturePermission

    try:
        data = request.get_json()
        if not data:
            return api_response(
                success=False,
                code=400,
                message="请求数据为空"
            )

        feature_permissions = data.get('feature_permissions', {})

        # 管理员角色限制
        if role == 'admin':
            return api_response(
                success=False,
                code=403,
                message="管理员角色子功能权限不允许修改"
            )

        now = time.time()

        # 更新或创建子功能权限
        for module_id, features in feature_permissions.items():
            for feature_id, is_enabled in features.items():
                # 查找现有记录
                perm = RoleFeaturePermission.query.filter_by(
                    role=role,
                    module_id=module_id,
                    feature_id=feature_id
                ).first()

                if perm:
                    # 更新现有记录
                    perm.is_enabled = is_enabled
                    perm.updated_at = now
                else:
                    # 创建新记录
                    perm = RoleFeaturePermission(
                        role=role,
                        module_id=module_id,
                        feature_id=feature_id,
                        is_enabled=is_enabled,
                        created_at=now,
                        updated_at=now
                    )
                    db.session.add(perm)

        db.session.commit()
        logger.info(f"已更新角色 {role} 的子功能权限")

        return api_response(
            success=True,
            message="子功能权限更新成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新角色子功能权限失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"更新失败: {str(e)}"
        )