from flask import request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity
)
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User, Permission
from app import db
from app.utils.email import send_admin_notification
import time
import logging
import os
from sqlalchemy import func
from flask_login import current_user
import sys

# 设置日志
logger = logging.getLogger(__name__)

# 认证相关路由
@api_v1_bp.route('/auth/login', methods=['POST'])
def login():
    """
    用户登录API
    """
    data = request.get_json()
    
    if not data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
        
    username = data.get('username')
    password = data.get('password')
    remember_me = data.get('remember_me', False)
    
    if not username or not password:
        return api_response(
            success=False,
            code=400,
            message="用户名和密码不能为空"
        )
    
    # 使用不区分大小写的查询
    user = User.query.filter(
        (func.lower(User.username) == func.lower(username)) | 
        (func.lower(User.email) == func.lower(username))
    ).first()
    
    if not user or not user.check_password(password):
        return api_response(
            success=False,
            code=401,
            message="用户名或密码错误"
        )
    
    # 检查是否为首次登录并处理账户激活
    first_login = False
    if not user.is_active:
        # 检查是否为首次登录（通过检查last_login是否为None或0）
        is_first_login = user.last_login is None or user.last_login == 0
        
        if is_first_login:
            # 首次登录，自动激活账户
            user.is_active = True
            first_login = True
            logger.info(f'自动激活首次登录用户: {user.username} (ID: {user.id})')
        else:
            # 非首次登录且未激活，拒绝登录
            return api_response(
                success=False,
                code=403,
                message="账号未激活，请联系管理员"
            )
    
    # 检查用户是否有权限设置，如果没有则分配默认权限
    is_first_login = user.last_login is None or user.last_login == 0
    has_permissions = Permission.query.filter_by(user_id=user.id).first() is not None
    
    if first_login or is_first_login or not has_permissions:
        # 导入权限工具
        from app.utils.permissions import assign_user_default_permissions
        assign_result = assign_user_default_permissions(user)
        logger.info(f"已为用户 {user.username} 分配默认权限: {'成功' if assign_result else '失败'}")
    
    # 更新最后登录时间
    user.last_login = time.time()
    db.session.commit()
    
    # 不再发送测试邮件
    test_email_result = True  # 为了保持兼容性，假设邮件测试成功
    
    # 创建访问令牌和刷新令牌，确保用户ID为字符串
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id)) if remember_me else None
    
    # 获取用户权限
    permissions = user.get_permissions()
    
    return api_response(
        success=True,
        message="登录成功" + ("，账户已自动激活" if first_login else ""),
        data={
            "token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 24 * 3600,  # 24小时
            "user": user.to_dict(),
            "permissions": permissions,
            "email_test": "成功" if test_email_result else "失败",
            "first_login": first_login
        }
    )

@api_v1_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    刷新访问令牌
    """
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=str(current_user_id))
    
    return api_response(
        success=True,
        message="Token刷新成功",
        data={
            "token": access_token,
            "expires_in": 24 * 3600  # 24小时
        }
    )

@api_v1_bp.route('/auth/register', methods=['POST'])
def register():
    """
    用户注册申请
    """
    data = request.get_json()
    
    if not data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
    
    # 获取注册信息
    username = data.get('username')
    real_name = data.get('real_name')
    company_name = data.get('company_name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    
    # 验证必填字段
    if not all([username, real_name, company_name, email, phone, password, confirm_password]):
        return api_response(
            success=False,
            code=400,
            message="请填写所有必填字段"
        )
    
    # 验证两次密码是否一致
    if password != confirm_password:
        return api_response(
            success=False,
            code=400,
            message="两次输入的密码不一致"
        )
    
    # 验证用户名是否已存在（不区分大小写）
    if User.query.filter(func.lower(User.username) == func.lower(username)).first():
        return api_response(
            success=False,
            code=400,
            message="用户名已被使用"
        )
    
    # 验证邮箱是否已存在（不区分大小写）
    if User.query.filter(func.lower(User.email) == func.lower(email)).first():
        return api_response(
            success=False,
            code=400,
            message="邮箱已被使用"
        )
    
    # 创建新用户对象，但暂不添加到数据库
    user = User(
        username=username,
        real_name=real_name,
        company_name=company_name,
        email=email,
        phone=phone,
        is_active=False,  # 默认未激活，等待管理员审核
        role='user'  # 默认角色
    )
    user.set_password(password)
    
    try:
        # 直接将用户添加到数据库，不再发送通知邮件
        logger.info(f"添加新用户: {username}, {email}")
        db.session.add(user)
        db.session.commit()
        
        return api_response(
            success=True,
            message="注册申请已提交，请等待管理员审核",
            data={
                "username": username,
                "email": email
            }
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"用户注册过程中发生错误: {str(e)}", exc_info=True)
        return api_response(
            success=False,
            code=500,
            message="注册过程中发生错误，请稍后重试"
        )

@api_v1_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """
    忘记密码请求
    """
    data = request.get_json()
    
    if not data:
        logger.error("请求数据无效: request.get_json() 返回 None")
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
    
    username_or_email = data.get('username_or_email')
    logger.info(f"收到忘记密码请求，用户名/邮箱: {username_or_email}")
    
    if not username_or_email:
        logger.error("用户名或邮箱为空")
        return api_response(
            success=False,
            code=400,
            message="用户名或邮箱不能为空"
        )
    
    # 查找用户
    logger.info(f"开始查找用户: {username_or_email}")
    try:
        user = User.query.filter(
            (func.lower(User.username) == func.lower(username_or_email)) | 
            (func.lower(User.email) == func.lower(username_or_email))
        ).first()
        
        if not user:
            logger.warning(f"找不到用户: {username_or_email}")
            # 出于安全考虑，不告诉用户是否存在该账户
            return api_response(
                success=True,
                message="如果账户存在，密码重置邮件已发送到您的邮箱，请查收"
            )
        
        logger.info(f"用户存在，ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
        
        # 生成密码重置令牌
        token = user.generate_reset_token()
        logger.info(f"生成密码重置令牌成功: {token[:10]}...")
        
        # 构建密码重置URL，使用实际请求的URL schema和host
        # 注意：从request.url_root获取可以确保使用当前实际请求的完整URL（包括正确的端口）
        reset_url = f"{request.url_root.rstrip('/')}/auth/reset-password/{token}"
        logger.info(f"生成密码重置链接: {reset_url}")
        
        # 导入密码重置邮件发送函数
        from app.utils.email import send_password_reset_email
        
        # 发送密码重置邮件
        try:
            email_sent = send_password_reset_email(user, token, reset_url)
            
            if email_sent:
                logger.info(f"密码重置邮件已发送给用户: {user.username} ({user.email})")
            else:
                logger.error(f"密码重置邮件发送失败: {user.username} ({user.email})")
                # 即使邮件发送失败，我们也不告知用户，以防信息泄露
        except Exception as e:
            logger.error(f"发送密码重置邮件时出现异常: {str(e)}", exc_info=True)
        
        # 不再发送通知给管理员
        
        return api_response(
            success=True,
            message="如果账户存在，密码重置邮件已发送到您的邮箱，请查收"
        )
    except Exception as e:
        logger.error(f"处理密码重置请求时出现异常: {str(e)}", exc_info=True)
        return api_response(
            success=False,
            code=500,
            message="处理请求失败，请稍后重试"
        )

@api_v1_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    用户登出
    
    注意：由于JWT是无状态的，服务器端无法真正"登出"JWT
    客户端应该删除本地存储的令牌
    """
    # 这里可以实现JWT黑名单，但需要使用Redis等缓存服务
    # 简单起见，返回成功即可，客户端负责删除令牌
    
    return api_response(
        success=True,
        message="已成功登出"
    )

@api_v1_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """
    重置密码API
    
    要求请求包含:
    - token: 重置令牌
    - new_password: 新密码
    """
    data = request.get_json()
    
    if not data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
    
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return api_response(
            success=False,
            code=400,
            message="缺少必要参数"
        )
    
    # 验证令牌
    user = User.verify_reset_token(token)
    
    if not user:
        logger.warning(f"无效的重置令牌: {token[:10]}...")
        return api_response(
            success=False,
            code=400,
            message="重置链接无效或已过期，请重新请求密码重置"
        )
    
    # 设置新密码
    user.set_password(new_password)
    
    # 如果用户未激活，则激活用户
    if not user.is_active:
        user.is_active = True
        logger.info(f"通过密码重置激活用户账户: {user.username}")
    
    # 保存更改
    try:
        db.session.commit()
        logger.info(f"用户 {user.username} 密码重置成功")
        
        # 不再发送通知邮件给管理员
        
        return api_response(
            success=True,
            message="密码重置成功，请使用新密码登录"
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"密码重置失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message="密码重置失败，请稍后重试"
        )

@api_v1_bp.route('/auth/token', methods=['POST'])
def get_token_from_session():
    """
    根据当前用户会话生成JWT令牌
    用于前端AJAX请求需要JWT认证的API
    """
    # 验证是否已登录
    if not current_user.is_authenticated:
        return api_response(
            success=False,
            code=401,
            message="用户未登录，无法生成令牌"
        )
    
    try:
        # 创建访问令牌
        access_token = create_access_token(identity=str(current_user.id))
        
        return api_response(
            success=True,
            message="令牌生成成功",
            data={
                "access_token": access_token,
                "expires_in": 24 * 3600  # 24小时
            }
        )
    except Exception as e:
        logger.error(f"生成令牌失败: {str(e)}", exc_info=True)
        return api_response(
            success=False,
            code=500,
            message=f"生成令牌失败: {str(e)}"
        ) 