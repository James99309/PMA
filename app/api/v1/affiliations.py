from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User, Affiliation, DataAffiliation
from app.decorators import permission_required
from app import db
import logging

logger = logging.getLogger(__name__)

@api_v1_bp.route('/affiliations', methods=['GET'])
@jwt_required()
def get_affiliations():
    """获取当前用户可查看的用户列表"""
    try:
        current_user_id = get_jwt_identity()  # 获取字符串形式的用户ID
        # 确保是字符串类型
        if not isinstance(current_user_id, str):
            current_user_id = str(current_user_id)
            
        # 查询用户时使用整数ID
        current_user = User.query.get(int(current_user_id))
        if not current_user:
            return api_response(
                success=False,
                code=404,
                message="用户不存在"
            )
    except ValueError as ve:
        # 用户ID转换错误
        logger.error(f"用户ID转换错误: {str(ve)}")
        return api_response(
            success=False,
            code=422,
            message=f"无效的用户ID格式: {str(ve)}"
        )
    except Exception as e:
        # 如果获取失败，返回错误响应
        logger.error(f"JWT验证失败: {str(e)}")
        return api_response(
            success=False,
            code=422,
            message=f"JWT验证失败: {str(e)}"
        )
    
    # 查询当前用户的归属关系
    affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
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
@jwt_required()
def get_user_affiliations(user_id):
    """获取用户可以查看的数据所有者列表"""
    try:
        current_user_id = get_jwt_identity()  # 获取字符串形式的用户ID
        # 确保是字符串类型
        if not isinstance(current_user_id, str):
            current_user_id = str(current_user_id)
            
        # 查询用户时使用整数ID
        current_user = User.query.get(int(current_user_id))
        if not current_user:
            logger.error(f"用户不存在 ID: {current_user_id}")
            return api_response(
                success=False,
                code=404,
                message="用户不存在"
            )
    except ValueError as ve:
        # 用户ID转换错误
        logger.error(f"用户ID转换错误: {str(ve)}")
        return api_response(
            success=False,
            code=422,
            message=f"无效的用户ID格式: {str(ve)}"
        )
    except Exception as e:
        # 如果获取失败，返回错误响应
        logger.error(f"JWT验证失败: {str(e)}")
        return api_response(
            success=False,
            code=422,
            message=f"JWT验证失败: {str(e)}"
        )
    
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
    if current_user.role != 'admin' and current_user.id != user_id:
        if not current_user.has_permission('user', 'view'):
            logger.warning(f"用户 {current_user.username} 尝试访问用户 {target_user.username} 的数据归属但无权限")
            return api_response(
                success=False,
                code=403,
                message="无权限访问此数据"
            )
    
    try:
        # 获取用户可查看的数据所有者
        affiliations = DataAffiliation.query.filter_by(viewer_id=user_id).all()
        
        # 格式化数据
        result = []
        for affiliation in affiliations:
            owner = User.query.get(affiliation.owner_id)
            if owner:
                result.append({
                    'user_id': owner.id,
                    'username': owner.username,
                    'real_name': owner.real_name,
                    'role': owner.role,
                    'company_name': owner.company_name
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
@jwt_required()
def create_affiliations_batch():
    """批量创建归属关系（设置当前用户可查看的用户列表）"""
    try:
        current_user_id = get_jwt_identity()  # 获取字符串形式的用户ID
        # 确保是字符串类型
        if not isinstance(current_user_id, str):
            current_user_id = str(current_user_id)
            
        # 查询用户时使用整数ID
        current_user = User.query.get(int(current_user_id))
        if not current_user:
            return api_response(
                success=False,
                code=404,
                message="用户不存在"
            )
    except ValueError as ve:
        # 用户ID转换错误
        logger.error(f"用户ID转换错误: {str(ve)}")
        return api_response(
            success=False,
            code=422,
            message=f"无效的用户ID格式: {str(ve)}"
        )
    except Exception as e:
        # 如果获取失败，返回错误响应
        logger.error(f"JWT验证失败: {str(e)}")
        return api_response(
            success=False,
            code=422,
            message=f"JWT验证失败: {str(e)}"
        )
    
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
        Affiliation.query.filter_by(viewer_id=current_user.id).delete()
        
        # 创建新的归属关系
        for owner_id in owner_ids:
            # 确保不会将自己添加为可查看对象
            if int(owner_id) != current_user.id:
                affiliation = Affiliation(
                    owner_id=owner_id,
                    viewer_id=current_user.id
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
@jwt_required()
def set_user_affiliations(user_id):
    """批量设置用户数据归属关系"""
    try:
        current_user_id = get_jwt_identity()  # 获取字符串形式的用户ID
        # 确保是字符串类型
        if not isinstance(current_user_id, str):
            current_user_id = str(current_user_id)
            
        # 查询用户时使用整数ID
        current_user = User.query.get(int(current_user_id))
        if not current_user:
            logger.error(f"当前用户不存在 ID: {current_user_id}")
            return api_response(
                success=False,
                code=404,
                message="用户不存在"
            )
            
        # 检查权限：只有管理员或有user edit权限的用户才能设置数据归属关系
        if current_user.role != 'admin' and not current_user.has_permission('user', 'edit'):
            logger.warning(f"用户 {current_user.username} 尝试设置用户ID {user_id} 的数据归属但无权限")
            return api_response(
                success=False,
                code=403,
                message="无权限执行此操作"
            )
    except ValueError as ve:
        # 用户ID转换错误
        logger.error(f"用户ID转换错误: {str(ve)}")
        return api_response(
            success=False,
            code=422,
            message=f"无效的用户ID格式: {str(ve)}"
        )
    except Exception as e:
        # 如果获取失败，返回错误响应
        logger.error(f"JWT验证失败: {str(e)}")
        return api_response(
            success=False,
            code=422,
            message=f"JWT验证失败: {str(e)}"
        )
    
    # 获取请求数据
    try:
        data = request.get_json()
        if not data or 'owner_ids' not in data:
            logger.warning(f"无效的请求数据: {data}")
            return api_response(
                success=False,
                code=400,
                message="无效的请求数据，缺少owner_ids字段"
            )
        owner_ids = data.get('owner_ids', [])
        # 确保owner_ids是列表类型
        if not isinstance(owner_ids, list):
            logger.warning(f"owner_ids不是列表类型: {type(owner_ids)}")
            return api_response(
                success=False,
                code=400,
                message="owner_ids必须是数组类型"
            )
        # 允许owner_ids为空，表示清空归属关系
        if len(owner_ids) == 0:
            DataAffiliation.query.filter_by(viewer_id=user_id).delete()
            Affiliation.query.filter_by(viewer_id=user_id).delete()
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
        # 删除现有的所有归属关系 - 同时处理两个表
        old_count = DataAffiliation.query.filter_by(viewer_id=user_id).count()
        DataAffiliation.query.filter_by(viewer_id=user_id).delete()
        Affiliation.query.filter_by(viewer_id=user_id).delete()
        logger.info(f"已删除用户 {target_user.username} 的 {old_count} 条现有数据归属关系")
        
        # 创建新的归属关系 - 同时添加到两个表
        added_count = 0
        for owner_id in owner_ids:
            try:
                # 确保所有者ID是整数
                owner_id = int(owner_id)
                
                # 确保所有者ID存在且有效
                owner = User.query.get(owner_id)
                if owner and owner.id != user_id:  # 不能将自己设为自己的数据所有者
                    # 添加到DataAffiliation表
                    data_affiliation = DataAffiliation(viewer_id=user_id, owner_id=owner_id)
                    db.session.add(data_affiliation)
                    
                    # 添加到Affiliation表
                    affiliation = Affiliation(viewer_id=user_id, owner_id=owner_id)
                    db.session.add(affiliation)
                    added_count += 1
                else:
                    if owner_id == user_id:
                        logger.warning(f"跳过用户 {user_id} 自己作为自己的数据所有者")
                    else:
                        logger.warning(f"跳过不存在的所有者ID: {owner_id}")
            except ValueError:
                logger.warning(f"跳过无效的所有者ID: {owner_id}")
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
@jwt_required()
def get_all_available_users():
    """获取所有可以添加的用户列表"""
    try:
        current_user_id = get_jwt_identity()  # 获取字符串形式的用户ID
        # 确保是字符串类型
        if not isinstance(current_user_id, str):
            current_user_id = str(current_user_id)
            
        # 查询用户时使用整数ID
        current_user = User.query.get(int(current_user_id))
        if not current_user:
            return api_response(
                success=False,
                code=404,
                message="用户不存在"
            )
    except ValueError as ve:
        # 用户ID转换错误
        logger.error(f"用户ID转换错误: {str(ve)}")
        return api_response(
            success=False,
            code=422,
            message=f"无效的用户ID格式: {str(ve)}"
        )
    except Exception as e:
        # 如果获取失败，返回错误响应
        logger.error(f"JWT验证失败: {str(e)}")
        return api_response(
            success=False,
            code=422,
            message=f"JWT验证失败: {str(e)}"
        )
    
    # 获取所有活跃用户，排除当前用户
    users = User.query.filter(
        User.is_active == True,
        User.id != current_user.id
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
@jwt_required()
def get_available_users_for_owner(user_id):
    """获取可以添加为特定用户的数据所有者的用户列表，返回所有活跃用户（含自己）"""
    try:
        current_user_id = get_jwt_identity()  # 获取字符串形式的用户ID
        logger.info(f"当前用户ID: {current_user_id}, 类型: {type(current_user_id)}")
        
        if not isinstance(current_user_id, str):
            current_user_id = str(current_user_id)
        
        # 查询用户时使用整数ID    
        current_user = User.query.get(int(current_user_id))
        if not current_user:
            logger.error(f"当前用户不存在 ID: {current_user_id}")
            return api_response(
                success=False,
                code=404,
                message="用户不存在"
            )
        
        logger.info(f"当前用户: {current_user.username}, 角色: {current_user.role}, 正在查询用户ID: {user_id} 的可用用户")
        
        if current_user.role != 'admin' and not current_user.has_permission('user', 'view'):
            logger.warning(f"用户 {current_user.username} 无权限访问此数据")
            return api_response(
                success=False,
                code=403,
                message="无权限访问此数据"
            )
    except ValueError as ve:
        logger.error(f"用户ID转换错误: {str(ve)}")
        return api_response(
            success=False,
            code=422,
            message=f"无效的用户ID格式: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"JWT验证失败: {str(e)}")
        return api_response(
            success=False,
            code=422,
            message=f"JWT验证失败: {str(e)}"
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