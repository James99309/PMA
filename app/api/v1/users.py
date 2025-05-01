from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response, jwt_required_with_permission, get_pagination_params
from app.models.user import User
from app.models.customer import Company
from app import db
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)

# 用户管理相关路由
@api_v1_bp.route('/users', methods=['GET'])
@jwt_required_with_permission('user', 'view')
def get_users():
    """
    获取用户列表，支持分页和搜索
    """
    page, limit = get_pagination_params()
    
    # 获取过滤参数
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    
    query = User.query
    
    # 添加搜索条件
    if search:
        query = query.filter(
            (User.username.like(f'%{search}%')) |
            (User.real_name.like(f'%{search}%')) |
            (User.email.like(f'%{search}%')) |
            (User.company_name.like(f'%{search}%'))
        )
    
    # 添加角色过滤
    if role:
        query = query.filter(User.role == role)
    
    # 添加状态过滤
    if status:
        is_active = True if status == 'active' else False
        query = query.filter(User.is_active == is_active)
    
    # 分页
    total = query.count()
    users_page = query.paginate(page=page, per_page=limit, error_out=False)
    users = users_page.items
    
    # 准备响应数据
    users_data = [user.to_dict() for user in users]
    
    return api_response(
        success=True,
        message="获取成功",
        data={
            "total": total,
            "page": page,
            "limit": limit,
            "users": users_data
        }
    )

@api_v1_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required_with_permission('user', 'view')
def get_user(user_id):
    """
    获取单个用户详情
    """
    user = User.query.get(user_id)
    
    if not user:
        return api_response(
            success=False,
            code=404,
            message="用户不存在"
        )
    
    return api_response(
        success=True,
        message="获取成功",
        data=user.to_dict()
    )

@api_v1_bp.route('/users', methods=['POST'])
@jwt_required_with_permission('user', 'create')
def create_user():
    """
    创建新用户
    """
    data = request.get_json()
    
    if not data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
    
    # 获取用户数据
    username = data.get('username')
    real_name = data.get('real_name')
    email = data.get('email')
    phone = data.get('phone')
    company_name = data.get('company_name')
    department = data.get('department')
    is_department_manager = data.get('is_department_manager', False)
    role = data.get('role', 'user')
    password = data.get('password')
    is_active = data.get('is_active', True)
    
    # 验证必填字段
    if not all([username, real_name, company_name, role, password]):
        return api_response(
            success=False,
            code=400,
            message="请填写所有必填字段"
        )
    
    # 验证用户名是否已存在（不区分大小写）
    if User.query.filter(func.lower(User.username) == func.lower(username)).first():
        return api_response(
            success=False,
            code=400,
            message="用户名已被使用"
        )
    
    # 验证邮箱是否已存在（不区分大小写）
    if email and User.query.filter(func.lower(User.email) == func.lower(email)).first():
        return api_response(
            success=False,
            code=400,
            message="邮箱已被使用"
        )
    
    # 创建新用户
    user = User(
        username=username,
        real_name=real_name,
        email=email,
        phone=phone,
        company_name=company_name,
        department=department,
        is_department_manager=is_department_manager,
        role=role,
        is_active=is_active
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # 准备用户数据以发送邀请邮件
        user_data = {
            "username": username,
            "real_name": real_name,
            "company_name": company_name,
            "email": email,
            "phone": phone,
            "role": role,
            "password": password
        }
        
        # 发送邀请邮件给新用户
        email_sent = False
        try:
            from app.utils.email import send_user_invitation_email
            email_sent = send_user_invitation_email(user_data)
            logger.info(f"用户邀请邮件发送{'成功' if email_sent else '失败'}: {username} <{email}>")
        except Exception as email_error:
            logger.error(f"发送用户邀请邮件时出错: {str(email_error)}")
        
        return api_response(
            success=True,
            message="用户创建成功" + ("并已发送邀请邮件" if email_sent else "，但邀请邮件发送失败"),
            data={
                "id": user.id,
                "username": user.username,
                "email_sent": email_sent
            }
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建用户失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="创建失败，请稍后重试"
        )

@api_v1_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required_with_permission('user', 'edit')
def update_user(user_id):
    """
    更新用户信息
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
    
    # 获取更新的字段
    real_name = data.get('real_name')
    email = data.get('email')
    phone = data.get('phone')
    company_name = data.get('company_name')
    department = data.get('department')
    is_department_manager = data.get('is_department_manager', user.is_department_manager)
    role = data.get('role')
    is_active = data.get('is_active', user.is_active)
    
    # 验证邮箱是否已被其他用户使用
    if email and email != user.email:
        if User.query.filter(func.lower(User.email) == func.lower(email), User.id != user_id).first():
            return api_response(
                success=False,
                code=400,
                message="邮箱已被其他用户使用"
            )
    
    # 更新用户信息
    if real_name:
        user.real_name = real_name
    if email:
        user.email = email
    if phone is not None:
        user.phone = phone
    if company_name:
        user.company_name = company_name
    if department is not None:
        user.department = department
    
    user.is_department_manager = is_department_manager
    if role:
        user.role = role
    
    user.is_active = is_active
    
    try:
        db.session.commit()
        
        return api_response(
            success=True,
            message="用户信息更新成功",
            data={
                "id": user.id,
                "username": user.username
            }
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新用户信息失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="更新失败，请稍后重试"
        )

@api_v1_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required_with_permission('user', 'delete')
def delete_user(user_id):
    """
    删除用户
    """
    user = User.query.get(user_id)
    
    if not user:
        return api_response(
            success=False,
            code=404,
            message="用户不存在"
        )
    
    # 禁止删除当前登录用户
    current_user_id = get_jwt_identity()
    if user_id == current_user_id:
        return api_response(
            success=False,
            code=400,
            message="不能删除当前登录用户"
        )
    
    try:
        db.session.delete(user)
        db.session.commit()
        
        return api_response(
            success=True,
            message="用户删除成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="删除失败，请稍后重试"
        )

@api_v1_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required_with_permission('user', 'edit')
def reset_user_password(user_id):
    """
    重置用户密码
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
    
    new_password = data.get('new_password')
    
    if not new_password:
        return api_response(
            success=False,
            code=400,
            message="新密码不能为空"
        )
    
    try:
        user.set_password(new_password)
        db.session.commit()
        
        return api_response(
            success=True,
            message="密码重置成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"重置密码失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="重置失败，请稍后重试"
        )

@api_v1_bp.route('/companies', methods=['GET'])
@jwt_required()
def get_companies():
    """
    获取企业列表，用于用户创建/编辑时选择
    """
    company_type = request.args.get('type')
    
    query = Company.query
    
    # 如果指定了类型，则过滤
    if company_type:
        query = query.filter_by(type=company_type)
    
    companies = query.all()
    
    # 准备响应数据
    companies_data = [
        {"id": company.id, "name": company.name} 
        for company in companies
    ]
    
    return api_response(
        success=True,
        message="获取成功",
        data=companies_data
    )

@api_v1_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """
    获取当前用户个人信息
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return api_response(
            success=False,
            code=404,
            message="用户不存在"
        )
    
    return api_response(
        success=True,
        message="获取成功",
        data=user.to_dict()
    )

@api_v1_bp.route('/user/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """
    更新当前用户个人信息
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
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
    
    # 获取更新字段
    real_name = data.get('real_name')
    email = data.get('email')
    phone = data.get('phone')
    
    # 验证邮箱唯一性
    if email and email != user.email:
        if User.query.filter(User.id != current_user_id, User.email == email).first():
            return api_response(
                success=False,
                code=400,
                message="邮箱已被使用"
            )
    
    # 更新字段
    if real_name:
        user.real_name = real_name
    if email:
        user.email = email
    if phone:
        user.phone = phone
    
    try:
        db.session.commit()
        
        return api_response(
            success=True,
            message="个人信息更新成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新个人信息失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="更新失败，请稍后重试"
        )

@api_v1_bp.route('/user/change-password', methods=['POST'])
@jwt_required()
def change_user_password():
    """
    修改当前用户密码
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
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
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        return api_response(
            success=False,
            code=400,
            message="所有密码字段不能为空"
        )
    
    # 验证当前密码
    if not user.check_password(current_password):
        return api_response(
            success=False,
            code=400,
            message="当前密码错误"
        )
    
    # 验证两次新密码是否一致
    if new_password != confirm_password:
        return api_response(
            success=False,
            code=400,
            message="两次输入的新密码不一致"
        )
    
    try:
        user.set_password(new_password)
        db.session.commit()
        
        return api_response(
            success=True,
            message="密码修改成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"修改密码失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="修改失败，请稍后重试"
        ) 