from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_login import current_user
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User, Affiliation
from app.decorators import permission_required
from app.utils.auth import flexible_auth
from app import db
import logging

logger = logging.getLogger(__name__)


def get_current_user_flexible():
    """获取当前用户，支持 JWT 和 Session 认证"""
    # 先尝试 JWT
    try:
        verify_jwt_in_request(optional=True)
        jwt_id = get_jwt_identity()
        if jwt_id:
            user_id = int(jwt_id) if isinstance(jwt_id, str) else jwt_id
            return User.query.get(user_id)
    except Exception:
        pass

    # 回退到 Session
    if current_user and current_user.is_authenticated:
        return current_user

    return None


@api_v1_bp.route('/affiliations', methods=['GET'])
@flexible_auth
def get_affiliations():
    """获取当前用户可查看的用户列表"""
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 查询当前用户的归属关系
    affiliations = Affiliation.query.filter_by(viewer_id=auth_user.id).all()
    viewable_users = []
    
    for affiliation in affiliations:
        owner = User.query.get(affiliation.owner_id)
        if owner:
            viewable_users.append({
                'affiliation_id': affiliation.id,
                'user_id': owner.id,
                'username': owner.username,
                'real_name': owner.real_name,
                'role': owner.role,
                'company_name': owner.company_name
            })
    
    return api_response(
        success=True,
        message="获取成功",
        data=viewable_users
    )

@api_v1_bp.route('/affiliations/<int:user_id>', methods=['GET'])
@flexible_auth
def get_user_affiliations(user_id):
    """获取可以查看该用户数据的用户列表（谁可以看该用户的数据）"""
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 检查目标用户是否存在
    target_user = User.query.get(user_id)
    if not target_user:
        logger.error(f"目标用户不存在 ID: {user_id}")
        return api_response(
            success=False,
            code=404,
            message="目标用户不存在"
        )

    # 检查权限：只有管理员或用户本人可以查看
    if auth_user.role != 'admin' and auth_user.id != user_id:
        if not auth_user.has_permission('user_management', 'view'):
            logger.warning(f"用户 {auth_user.username} 尝试访问用户 {target_user.username} 的数据归属但无权限")
            return api_response(
                success=False,
                code=403,
                message="无权限访问此数据"
            )

    try:
        # 查询以该用户为 owner 的归属关系（谁可以看该用户的数据）
        affiliations = Affiliation.query.filter_by(owner_id=user_id).all()

        # 格式化数据：返回 viewer 信息
        result = []
        for affiliation in affiliations:
            viewer = User.query.get(affiliation.viewer_id)
            if viewer:
                result.append({
                    'user_id': viewer.id,
                    'username': viewer.username,
                    'real_name': viewer.real_name,
                    'role': viewer.role,
                    'company_name': viewer.company_name
                })
        
        return api_response(
            success=True,
            message="获取成功",
            data=result
        )
    except Exception as e:
        logger.error(f"获取数据归属关系失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"获取数据归属关系失败: {str(e)}"
        )

@api_v1_bp.route('/affiliations/batch', methods=['POST'])
@flexible_auth
def create_affiliations_batch():
    """批量创建归属关系（设置当前用户可查看的用户列表）"""
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    data = request.get_json()
    
    if not data or 'owner_ids' not in data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
    
    owner_ids = data.get('owner_ids', [])

    try:
        # 删除现有的所有归属关系
        Affiliation.query.filter_by(viewer_id=auth_user.id).delete()

        # 创建新的归属关系
        for owner_id in owner_ids:
            # 确保不会将自己添加为可查看对象
            if int(owner_id) != auth_user.id:
                affiliation = Affiliation(
                    owner_id=owner_id,
                    viewer_id=auth_user.id
                )
                db.session.add(affiliation)
        
        db.session.commit()
        
        return api_response(
            success=True,
            message="归属关系设置成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"设置归属关系失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="设置失败，请稍后重试"
        )

@api_v1_bp.route('/affiliations/<int:user_id>/batch', methods=['POST'])
@flexible_auth
def set_user_affiliations(user_id):
    """批量设置可以查看该用户数据的用户列表（设置谁可以看该用户的数据）"""
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 检查权限：只有管理员或有user edit权限的用户才能设置数据归属关系
    if auth_user.role != 'admin' and not auth_user.has_permission('user_management', 'edit'):
        logger.warning(f"用户 {auth_user.username} 尝试设置用户ID {user_id} 的数据归属但无权限")
        return api_response(
            success=False,
            code=403,
            message="无权限执行此操作"
        )

    # 获取请求数据（支持 viewer_ids 或 owner_ids 参数名，兼容旧代码）
    try:
        data = request.get_json()
        viewer_ids = data.get('viewer_ids') or data.get('owner_ids', [])
        if not data or (viewer_ids is None):
            logger.warning(f"无效的请求数据: {data}")
            return api_response(
                success=False,
                code=400,
                message="无效的请求数据，缺少viewer_ids字段"
            )
        # 确保viewer_ids是列表类型
        if not isinstance(viewer_ids, list):
            logger.warning(f"viewer_ids不是列表类型: {type(viewer_ids)}")
            return api_response(
                success=False,
                code=400,
                message="viewer_ids必须是数组类型"
            )
        # 允许viewer_ids为空，表示清空归属关系
        if len(viewer_ids) == 0:
            Affiliation.query.filter_by(owner_id=user_id).delete()
            db.session.commit()
            logger.info(f"用户 {user_id} 的归属关系已全部清空")
            return api_response(success=True, message="归属关系已全部清空")
    except Exception as e:
        logger.error(f"解析请求数据失败: {str(e)}")
        return api_response(
            success=False,
            code=400,
            message=f"无法解析请求数据: {str(e)}"
        )

    # 获取目标用户
    target_user = User.query.get(user_id)
    if not target_user:
        logger.error(f"目标用户不存在 ID: {user_id}")
        return api_response(
            success=False,
            code=404,
            message="用户不存在"
        )

    try:
        # 删除现有的所有归属关系（以该用户为 owner 的记录）
        old_count = Affiliation.query.filter_by(owner_id=user_id).count()
        Affiliation.query.filter_by(owner_id=user_id).delete()
        logger.info(f"已删除用户 {target_user.username} 的 {old_count} 条现有数据归属关系")

        # 创建新的归属关系（该用户为 owner，选中的用户为 viewer）
        added_count = 0
        for viewer_id in viewer_ids:
            try:
                # 确保 viewer ID 是整数
                viewer_id = int(viewer_id)

                # 确保 viewer 存在且有效
                viewer = User.query.get(viewer_id)
                if viewer and viewer.id != user_id:  # 不能将自己设为自己的 viewer
                    # 添加到 Affiliation 表：owner_id=目标用户，viewer_id=选中的用户
                    affiliation = Affiliation(owner_id=user_id, viewer_id=viewer_id)
                    db.session.add(affiliation)
                    added_count += 1
                else:
                    if viewer_id == user_id:
                        logger.warning(f"跳过用户 {user_id} 自己作为自己的 viewer")
                    else:
                        logger.warning(f"跳过不存在的 viewer ID: {viewer_id}")
            except ValueError:
                logger.warning(f"跳过无效的 viewer ID: {viewer_id}")
                continue

        db.session.commit()
        logger.info(f"为用户 {target_user.username} 添加了 {added_count} 条新的数据归属关系")

        return api_response(
            success=True,
            message="数据归属关系设置成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"设置数据归属关系失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"设置失败: {str(e)}"
        )

@api_v1_bp.route('/users/available', methods=['GET'])
@flexible_auth
def get_all_available_users():
    """获取所有可以添加的用户列表"""
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 获取所有活跃用户，排除当前用户
    users = User.query.filter(
        User._is_active == True,
        User.id != auth_user.id
    ).all()
    
    # 转换为列表
    users_data = [{
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'role': user.role,
        'company_name': user.company_name
    } for user in users]
    
    return api_response(
        success=True,
        message="获取成功",
        data=users_data
    )

@api_v1_bp.route('/users/<int:user_id>/available', methods=['GET'])
@flexible_auth
def get_available_users_for_owner(user_id):
    """获取可以添加为特定用户的数据所有者的用户列表，返回所有活跃用户（含自己）"""
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    logger.info(f"当前用户: {auth_user.username}, 角色: {auth_user.role}, 正在查询用户ID: {user_id} 的可用用户")

    if auth_user.role != 'admin' and not auth_user.has_permission('user_management', 'view'):
        logger.warning(f"用户 {auth_user.username} 无权限访问此数据")
        return api_response(
            success=False,
            code=403,
            message="无权限访问此数据"
        )
    
    # 获取所有用户，不限制is_active状态，确保能看到数据
    users = User.query.all()
    
    # 添加日志
    logger.info(f"找到 {len(users)} 个用户")
    
    result = []
    for user in users:
        # 添加用户状态信息，便于调试
        result.append({
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name or user.username,
            'role': user.role,
            'company_name': user.company_name,
            'department': user.department,
            'is_department_manager': user.is_department_manager,
            'is_active': user.is_active
        })
    
    logger.info(f"返回 {len(result)} 个用户记录")
    
    return api_response(
        success=True,
        message="获取成功",
        data=result
    ) 