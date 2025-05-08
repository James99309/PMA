from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User, Permission
from app import db
from flask_login import login_user, logout_user, login_required, current_user
import qrcode
import io
import base64
import uuid
import time
import logging
import requests
import json
from sqlalchemy import func
from flask_jwt_extended import create_access_token
from urllib.parse import urlparse
from app.forms import ForgotPasswordForm, ResetPasswordForm
from app.utils.email import send_password_reset_email

logger = logging.getLogger(__name__)
auth = Blueprint('auth', __name__)

# API基础URL
API_BASE_URL = "/api/v1"

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """登录处理函数"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    # 如果是POST请求，处理登录表单
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # 使用与API相同的不区分大小写的查询逻辑
        user = User.query.filter(
            (func.lower(User.username) == func.lower(username_or_email)) | 
            (func.lower(User.email) == func.lower(username_or_email))
        ).first()
        
        # 验证用户名和密码
        if user and user.check_password(password):
            # 用户验证成功，无需再检查is_active
            login_user(user, remember=remember)
            
            # 生成JWT令牌
            jwt_token = create_access_token(identity=str(user.id))
            # 将角色和用户ID信息存放在session中，方便前端使用
            session['jwt_token'] = jwt_token
            session['role'] = user.role  # 确保使用数据库中的最新角色值
            session['user_id'] = user.id
            session['username'] = user.username
            
            # 记录登录日志
            logger.info(f"用户 {user.username} (ID: {user.id}, 角色: {user.role}) 成功登录")
            
            # 重定向到登录前的页面或默认页面
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            # 记录失败的登录尝试
            if user:
                logger.warning(f"用户 {username_or_email} 登录失败：密码错误")
            else:
                logger.warning(f"用户 {username_or_email} 登录失败：用户名或邮箱不存在")
            flash('用户名/邮箱或密码错误', 'danger')
    
    return render_template('auth/login.html')

@auth.route('/complete_profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    user = current_user
    if user.is_profile_complete:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        real_name = request.form.get('real_name')
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        
        if not all([real_name, company_name, email]):
            flash('请填写所有必填字段！', 'danger')
            return render_template('auth/complete_profile.html')
            
        # 检查邮箱是否已被使用
        if User.query.filter(User.id != user.id, User.email == email).first():
            flash('该邮箱已被使用！', 'danger')
            return render_template('auth/complete_profile.html')
            
        user.real_name = real_name
        user.company_name = company_name
        user.email = email
        user.is_profile_complete = True
        
        try:
            db.session.commit()
            flash('个人信息已完善！', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            logger.error('Error saving profile: %s', str(e))
            db.session.rollback()
            flash('保存失败，请稍后重试！', 'danger')
            
    return render_template('auth/complete_profile.html')

@auth.route('/logout')
@login_required
def logout():
    """用户登出"""
    # 记录登出信息
    if current_user.is_authenticated:
        logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 登出系统")
    
    # 清除会话数据
    session.clear()
    
    # 登出用户
    logout_user()
    
    flash('您已成功登出！', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册页面和处理
    
    GET: 显示注册页面
    POST: 处理注册请求
    """
    if request.method == 'POST':
        username = request.form.get('username')
        real_name = request.form.get('real_name')
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 使用API注册
        try:
            response = requests.post(
                f"{request.host_url.rstrip('/')}{API_BASE_URL}/auth/register",
                json={
                    "username": username,
                    "real_name": real_name,
                    "company_name": company_name,
                    "email": email,
                    "phone": phone,
                    "password": password,
                    "confirm_password": confirm_password
                }
            )
            
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                flash('注册申请已提交，请等待管理员审核！', 'success')
                return redirect(url_for('auth.login'))
            else:
                # API注册失败
                error_message = data.get('message', '注册失败，请检查输入信息！')
                flash(error_message, 'danger')
                
        except Exception as e:
            logger.error(f'Error during API register: {str(e)}')
            flash('服务器错误，请稍后重试', 'danger')
        
    return render_template('auth/register.html')

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    忘记密码页面和处理
    
    GET: 显示忘记密码页面
    POST: 处理忘记密码请求
    """
    logger.info(f"访问忘记密码页面，Method: {request.method}")
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        username_or_email = form.username_or_email.data
        logger.info(f"提交忘记密码表单，输入: {username_or_email}")
        # 直接在视图中处理忘记密码逻辑
        user = User.query.filter(
            (func.lower(User.username) == func.lower(username_or_email)) |
            (func.lower(User.email) == func.lower(username_or_email))
        ).first()
        if not user:
            logger.warning(f"找不到用户: {username_or_email}")
            flash('如果账户存在，密码重置邮件已发送到您的邮箱，请查收。', 'success')
            return redirect(url_for('auth.login'))
        logger.info(f"用户存在，ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
        # 生成密码重置令牌
        token = user.generate_reset_token()
        logger.info(f"生成密码重置令牌成功: {token[:10]}...")
        reset_url = f"{request.url_root.rstrip('/')}/auth/reset-password/{token}"
        logger.info(f"生成密码重置链接: {reset_url}")
        try:
            email_sent = send_password_reset_email(user, token, reset_url)
            if email_sent:
                logger.info(f"密码重置邮件已发送给用户: {user.username} ({user.email})")
            else:
                logger.error(f"密码重置邮件发送失败: {user.username} ({user.email})")
        except Exception as e:
            logger.error(f"发送密码重置邮件时出现异常: {str(e)}", exc_info=True)
        flash('如果账户存在，密码重置邮件已发送到您的邮箱，请查收。', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    密码重置页面
    
    GET: 显示密码重置页面
    POST: 处理密码重置请求
    """
    logger.info(f"访问密码重置页面，Token: {token[:10]}...")
    # 先验证令牌是否有效，不显示用户名等信息以保护隐私
    user = User.verify_reset_token(token)
    if not user:
        logger.warning(f"无效的密码重置令牌: {token[:10]}...")
        flash('密码重置链接无效或已过期，请重新申请', 'danger')
        return redirect(url_for('auth.forgot_password'))
    logger.info(f"密码重置令牌有效，用户: {user.username}")
    form = ResetPasswordForm()
    if form.validate_on_submit():
        password = form.password.data
        # 直接在视图中重置密码
        user.set_password(password)
        if not user.is_active:
            user.is_active = True
        try:
            db.session.commit()
            logger.info(f"用户 {user.username} 成功重置密码")
            flash('密码已成功重置，请使用新密码登录', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error during password reset: {str(e)}')
            flash('服务器错误，请稍后重试', 'danger')
    return render_template('auth/reset_password.html', form=form, token=token)

@auth.route('/generate_wechat_qrcode')
def generate_wechat_qrcode():
    # 生成唯一的状态码
    state = str(uuid.uuid4())
    session['wechat_state'] = state
    
    # 生成包含状态码的二维码URL
    # 这里需要替换成实际的微信OAuth2.0授权URL
    qr_url = f"https://open.weixin.qq.com/connect/qrconnect?appid=YOUR_APP_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=snsapi_login&state={state}#wechat_redirect"
    
    # 生成二维码图片
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 将图片转换为base64字符串
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    return jsonify({
        'qrcode': f'data:image/png;base64,{img_str}',
        'state': state
    })

@auth.route('/check_wechat_bind')
def check_wechat_bind():
    state = request.args.get('state')
    # 这里需要实现检查微信绑定状态的逻辑
    # 临时返回未绑定状态
    return jsonify({'bound': False})

@auth.route('/wechat_callback')
def wechat_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    # 验证state是否匹配
    if state != session.get('wechat_state'):
        flash('无效的请求', 'error')
        return redirect(url_for('auth.login'))
    
    # 这里需要实现微信登录的逻辑
    # 1. 使用code获取access_token
    # 2. 使用access_token获取用户信息
    # 3. 更新或创建用户记录
    # 4. 设置登录状态
    
    return redirect(url_for('main.index')) 
    return redirect(url_for('main.index')) 