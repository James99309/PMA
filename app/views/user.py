from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app.models.user import User, Permission
from app import db
import logging
import requests
import json
from datetime import datetime
from app.utils.role_mappings import normalize_role_key

logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__)

# API基础URL
API_BASE_URL = "/api/v1"

def get_auth_headers():
    """获取认证头部信息"""
    # 从session中获取JWT令牌
    token = session.get('jwt_token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}

@user_bp.route('/list')
@login_required
def list_users():
    """用户列表页面"""
    # 获取API基础URL
    api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users"
    
    # 尝试从API获取用户列表
    try:
        # 使用JWT令牌认证
        headers = get_auth_headers()
        response = requests.get(api_url, headers=headers)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            users_data = data.get('data', {}).get('users', [])
            total = data.get('data', {}).get('total', 0)
            
            return render_template(
                'user/list.html',
                users=users_data,
                total=total
            )
        else:
            # API请求失败，尝试直接从数据库获取
            users = User.query.all()
            users_data = [user.to_dict() for user in users]
            
            return render_template(
                'user/list.html',
                users=users_data,
                total=len(users_data)
            )
            
    except Exception as e:
        logger.error(f"获取用户列表时出错: {str(e)}")
        flash('获取用户列表时发生错误，尝试直接从数据库获取', 'warning')
        
        # 直接从数据库获取
        try:
            users = User.query.all()
            users_data = [user.to_dict() for user in users]
            
            return render_template(
                'user/list.html',
                users=users_data,
                total=len(users_data)
            )
        except Exception as db_error:
            logger.error(f"从数据库获取用户列表时出错: {str(db_error)}")
            flash('获取用户列表失败，请稍后重试', 'danger')
            return render_template('user/list.html', users=[], total=0)

@user_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """创建新用户页面和处理"""
    if request.method == 'GET':
        return render_template('user/edit.html', user=None, is_edit=False)
    
    # POST请求处理
    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username')
        real_name = request.form.get('real_name')
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        role = request.form.get('role')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        is_active = 'is_active' in request.form
        is_department_manager = 'is_department_manager' in request.form
        
        # 验证密码
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return render_template('user/edit.html', user=None, is_edit=False)
        
        # 准备用户数据
        user_data = {
            "username": username,
            "real_name": real_name,
            "company_name": company_name,
            "email": email,
            "phone": phone,
            "department": department,
            "is_department_manager": is_department_manager,
            "role": role,
            "password": password,
            "is_active": is_active
        }
        
        # 尝试通过API创建用户
        try:
            # 准备API请求数据
            api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users"
            
            # 使用JWT令牌认证
            headers = get_auth_headers()
            response = requests.post(api_url, json=user_data, headers=headers)
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                # 发送邀请邮件给新用户
                from app.utils.email import send_user_invitation_email
                email_sent = send_user_invitation_email(user_data)
                
                if email_sent:
                    flash('用户创建成功，邀请邮件已发送至用户邮箱', 'success')
                else:
                    flash('用户创建成功，但邀请邮件发送失败，请手动通知用户', 'warning')
                
                return redirect(url_for('user.list_users'))
            else:
                # API创建失败，尝试直接创建
                error_msg = data.get('message', '未知错误')
                logger.warning(f"通过API创建用户失败: {error_msg}，尝试直接创建")
                
                # 直接创建用户
                user = User(
                    username=username,
                    real_name=real_name,
                    company_name=company_name,
                    email=email,
                    phone=phone,
                    department=department,
                    is_department_manager=is_department_manager,
                    role=role,
                    is_active=is_active
                )
                user.set_password(password)
                
                try:
                    db.session.add(user)
                    db.session.commit()
                    
                    # 发送邀请邮件给新用户
                    from app.utils.email import send_user_invitation_email
                    email_sent = send_user_invitation_email(user_data)
                    
                    if email_sent:
                        flash('用户创建成功，邀请邮件已发送至用户邮箱（直接创建）', 'success')
                    else:
                        flash('用户创建成功，但邀请邮件发送失败，请手动通知用户（直接创建）', 'warning')
                    
                    return redirect(url_for('user.list_users'))
                except Exception as db_error:
                    db.session.rollback()
                    logger.error(f"直接创建用户时出错: {str(db_error)}")
                    flash(f'用户创建失败: {str(db_error)}', 'danger')
                    return render_template('user/edit.html', user=user_data, is_edit=False)
                
        except Exception as e:
            logger.error(f"创建用户时出错: {str(e)}")
            flash('创建用户时发生错误，请稍后重试', 'danger')
            return render_template('user/edit.html', user=user_data, is_edit=False)

@user_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """编辑用户页面和处理"""
    # GET请求 - 显示编辑表单
    if request.method == 'GET':
        try:
            # 首先尝试API获取
            api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users/{user_id}"
            headers = get_auth_headers()
            
            try:
                response = requests.get(api_url, headers=headers)
                data = response.json()
                
                if response.status_code == 200 and data.get('success'):
                    user_data = data.get('data', {})
                    return render_template('user/edit.html', user=user_data, is_edit=True)
            except Exception as api_error:
                logger.warning(f"通过API获取用户信息失败: {str(api_error)}，尝试直接获取")
            
            # 如果API失败，直接从数据库获取
            user = User.query.get(user_id)
            if user:
                user_data = user.to_dict()
                return render_template('user/edit.html', user=user_data, is_edit=True)
            else:
                flash('用户不存在', 'danger')
                return redirect(url_for('user.list_users'))
                
        except Exception as e:
            logger.error(f"获取用户信息时出错: {str(e)}")
            flash('获取用户信息时发生错误，请稍后重试', 'danger')
            return redirect(url_for('user.list_users'))
    
    # POST请求 - 处理编辑表单提交
    if request.method == 'POST':
        # 获取表单数据
        real_name = request.form.get('real_name')
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        role = request.form.get('role')
        password = request.form.get('password')
        is_active = 'is_active' in request.form
        is_department_manager = 'is_department_manager' in request.form
        
        try:
            # 尝试通过API更新
            api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users/{user_id}"
            user_data = {
                "real_name": real_name,
                "company_name": company_name,
                "email": email,
                "phone": phone,
                "department": department,
                "is_department_manager": is_department_manager,
                "role": role,
                "is_active": is_active
            }
            
            headers = get_auth_headers()
            response = requests.put(api_url, json=user_data, headers=headers)
            
            # 如果提供了密码，处理密码更新
            if password and password.strip():
                try:
                    password_api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users/{user_id}/reset-password"
                    password_response = requests.post(
                        password_api_url, 
                        json={"password": password},
                        headers=headers
                    )
                except Exception as pwd_error:
                    logger.error(f"通过API重置密码时出错: {str(pwd_error)}")
                    # 如果API不可用，尝试直接更新密码
                    try:
                        user = User.query.get(user_id)
                        if user:
                            user.set_password(password)
                            db.session.commit()
                    except Exception as db_pwd_error:
                        logger.error(f"直接更新密码时出错: {str(db_pwd_error)}")
            
            data = response.json() if response.status_code == 200 else {"success": False}
            
            if response.status_code == 200 and data.get('success'):
                flash('用户信息更新成功', 'success')
                return redirect(url_for('user.list_users'))
            else:
                # API更新失败，尝试直接更新
                logger.warning("通过API更新用户失败，尝试直接更新")
                
                user = User.query.get(user_id)
                if user:
                    user.real_name = real_name
                    user.company_name = company_name
                    user.email = email
                    user.phone = phone
                    user.department = department
                    user.role = role
                    user.is_active = is_active
                    user.is_department_manager = is_department_manager
                    
                    try:
                        db.session.commit()
                        flash('用户信息更新成功（直接更新）', 'success')
                        return redirect(url_for('user.list_users'))
                    except Exception as db_error:
                        db.session.rollback()
                        logger.error(f"直接更新用户信息时出错: {str(db_error)}")
                        flash(f'更新失败: {str(db_error)}', 'danger')
                else:
                    flash('用户不存在', 'danger')
                
                return render_template('user/edit.html', user=user_data, is_edit=True)
                
        except Exception as e:
            logger.error(f"更新用户信息时出错: {str(e)}")
            flash('更新用户信息时发生错误，请稍后重试', 'danger')
            return render_template('user/edit.html', user=user_data, is_edit=True)

@user_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """删除用户"""
    try:
        # 尝试通过API删除
        api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users/{user_id}"
        headers = get_auth_headers()
        
        response = requests.delete(api_url, headers=headers)
        data = response.json() if response.status_code == 200 else {"success": False}
        
        if response.status_code == 200 and data.get('success'):
            flash('用户删除成功', 'success')
        else:
            # API删除失败，尝试直接删除
            logger.warning("通过API删除用户失败，尝试直接删除")
            
            user = User.query.get(user_id)
            if user:
                try:
                    db.session.delete(user)
                    db.session.commit()
                    flash('用户删除成功（直接删除）', 'success')
                except Exception as db_error:
                    db.session.rollback()
                    logger.error(f"直接删除用户时出错: {str(db_error)}")
                    flash(f'删除失败: {str(db_error)}', 'danger')
            else:
                flash('用户不存在', 'danger')
    except Exception as e:
        logger.error(f"删除用户时出错: {str(e)}")
        flash('删除用户时发生错误，请稍后重试', 'danger')
    
    return redirect(url_for('user.list_users'))

@user_bp.route('/permissions/<int:user_id>', methods=['GET', 'POST'])
@login_required
def manage_permissions(user_id):
    """管理用户权限"""
    # GET请求 - 显示权限管理页面
    if request.method == 'GET':
        try:
            headers = get_auth_headers()
            
            # 获取用户信息
            user_data = {}
            try:
                user_api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users/{user_id}"
                user_response = requests.get(user_api_url, headers=headers)
                if user_response.status_code == 200:
                    user_data = user_response.json().get('data', {})
                else:
                    # 直接从数据库获取
                    user = User.query.get(user_id)
                    if user:
                        user_data = user.to_dict()
            except Exception as user_error:
                logger.warning(f"获取用户信息时出错: {str(user_error)}")
                user = User.query.get(user_id)
                if user:
                    user_data = user.to_dict()
            
            # 获取模块列表
            modules = []
            try:
                modules_api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/modules"
                modules_response = requests.get(modules_api_url, headers=headers)
                if modules_response.status_code == 200:
                    modules = modules_response.json().get('data', [])
                else:
                    # 如果API失败，使用预定义模块列表
                    modules = [
                        {"id": "project", "name": "项目管理", "description": "管理销售项目和跟进"},
                        {"id": "customer", "name": "客户管理", "description": "管理客户信息和联系人"},
                        {"id": "quotation", "name": "报价管理", "description": "管理产品报价"},
                        {"id": "product", "name": "产品管理", "description": "管理产品信息和价格"},
                        {"id": "user", "name": "用户管理", "description": "管理系统用户"},
                        {"id": "permission", "name": "权限管理", "description": "管理用户权限"}
                    ]
            except Exception as modules_error:
                logger.warning(f"获取模块列表时出错: {str(modules_error)}")
                # 使用预定义模块列表
                modules = [
                    {"id": "project", "name": "项目管理", "description": "管理销售项目和跟进"},
                    {"id": "customer", "name": "客户管理", "description": "管理客户信息和联系人"},
                    {"id": "quotation", "name": "报价管理", "description": "管理产品报价"},
                    {"id": "product", "name": "产品管理", "description": "管理产品信息和价格"},
                    {"id": "user", "name": "用户管理", "description": "管理系统用户"},
                    {"id": "permission", "name": "权限管理", "description": "管理用户权限"}
                ]
            
            # 获取用户当前权限
            permissions_dict = {}
            try:
                permissions_api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users/{user_id}/permissions"
                permissions_response = requests.get(permissions_api_url, headers=headers)
                if permissions_response.status_code == 200:
                    permissions_data = permissions_response.json().get('data', {}).get('permissions', [])
                    for perm in permissions_data:
                        module = perm.get('module')
                        permissions_dict[module] = perm
                else:
                    # 直接从数据库获取
                    user = User.query.get(user_id)
                    if user:
                        for permission in user.permissions:
                            permissions_dict[permission.module] = {
                                'module': permission.module,
                                'can_view': permission.can_view,
                                'can_create': permission.can_create,
                                'can_edit': permission.can_edit,
                                'can_delete': permission.can_delete
                            }
            except Exception as permissions_error:
                logger.warning(f"获取用户权限时出错: {str(permissions_error)}")
                # 直接从数据库获取
                user = User.query.get(user_id)
                if user:
                    for permission in user.permissions:
                        permissions_dict[permission.module] = {
                            'module': permission.module,
                            'can_view': permission.can_view,
                            'can_create': permission.can_create,
                            'can_edit': permission.can_edit,
                            'can_delete': permission.can_delete
                        }
            
            return render_template(
                'user/permissions.html',
                user=user_data,
                modules=modules,
                permissions=permissions_dict
            )
                
        except Exception as e:
            logger.error(f"获取用户权限信息时出错: {str(e)}")
            flash('获取用户权限信息时发生错误，请稍后重试', 'danger')
            return redirect(url_for('user.list_users'))
    
    # POST请求 - 保存权限设置
    if request.method == 'POST':
        # 获取表单数据
        form_data = request.form
        
        # 处理模块权限
        permissions = []
        modules = form_data.getlist('module')
        
        for module in modules:
            permission = {
                "module": module,
                "can_view": f"view_{module}" in form_data,
                "can_create": f"create_{module}" in form_data,
                "can_edit": f"edit_{module}" in form_data,
                "can_delete": f"delete_{module}" in form_data
            }
            permissions.append(permission)
        
        try:
            # 尝试通过API更新权限
            permissions_api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users/{user_id}/permissions"
            permissions_data = {"permissions": permissions}
            
            headers = get_auth_headers()
            response = requests.put(permissions_api_url, json=permissions_data, headers=headers)
            data = response.json() if response.status_code == 200 else {"success": False}
            
            if response.status_code == 200 and data.get('success'):
                flash('用户权限更新成功', 'success')
                return redirect(url_for('user.list_users'))
            else:
                # API更新失败，尝试直接更新
                logger.warning("通过API更新权限失败，尝试直接更新")
                
                user = User.query.get(user_id)
                if user:
                    # 清除现有权限
                    Permission.query.filter_by(user_id=user_id).delete()
                    
                    # 添加新权限
                    for perm in permissions:
                        module = perm.get('module')
                        permission = Permission(
                            user_id=user_id,
                            module=module,
                            can_view=perm.get('can_view', False),
                            can_create=perm.get('can_create', False),
                            can_edit=perm.get('can_edit', False),
                            can_delete=perm.get('can_delete', False)
                        )
                        db.session.add(permission)
                    
                    try:
                        db.session.commit()
                        flash('用户权限更新成功（直接更新）', 'success')
                        return redirect(url_for('user.list_users'))
                    except Exception as db_error:
                        db.session.rollback()
                        logger.error(f"直接更新权限时出错: {str(db_error)}")
                        flash(f'权限更新失败: {str(db_error)}', 'danger')
                else:
                    flash('用户不存在', 'danger')
                
                return redirect(url_for('user.manage_permissions', user_id=user_id))
                
        except Exception as e:
            logger.error(f"更新用户权限时出错: {str(e)}")
            flash('更新用户权限时发生错误，请稍后重试', 'danger')
            return redirect(url_for('user.manage_permissions', user_id=user_id))

@user_bp.route('/affiliations')
@login_required
def manage_affiliations():
    """重定向到用户列表"""
    flash('请通过用户管理界面设置用户的数据归属关系', 'info')
    return redirect(url_for('user.list_users'))

@user_bp.route('/affiliations/<int:user_id>')
@login_required
def manage_user_affiliations(user_id):
    """管理用户数据归属权限"""
    # 只有管理员或对应用户可以管理
    if current_user.role != 'admin' and current_user.id != user_id:
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('user.list_users'))
    
    # 获取目标用户
    target_user = User.query.get_or_404(user_id)
    
    return render_template(
        'user/affiliations.html',
        target_user=target_user
    )

@user_bp.route('/api/check-duplicates', methods=['POST'])
@login_required
def check_duplicates():
    """检查用户名重复性"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
        
        data = request.json
        
        # 确保data是一个dict
        if not isinstance(data, dict):
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        usernames = data.get('usernames', [])
        
        # 确保usernames是一个列表
        if not isinstance(usernames, list):
            return jsonify({'success': False, 'message': 'usernames必须是列表'}), 400
        
        if not usernames:
            return jsonify({'success': False, 'message': '没有提供用户名'}), 400
        
        # 检查列表中的每个元素是否为字符串
        for i, name in enumerate(usernames):
            if not isinstance(name, str):
                # 尝试转换为字符串
                try:
                    usernames[i] = str(name)
                except:
                    # 如果转换失败，则移除该元素
                    usernames[i] = ""
        
        # 过滤掉空字符串
        usernames = [name for name in usernames if name]
        
        if not usernames:
            return jsonify({'success': False, 'message': '没有有效的用户名'}), 400
        
        # 获取所有现有用户名
        existing_users = User.query.with_entities(User.id, User.username, User.email).all()
        existing_usernames = {user.username.lower(): {'id': user.id, 'username': user.username, 'email': user.email} for user in existing_users}
        
        conflicts = []
        for import_username in usernames:
            # 查找匹配的用户名（不区分大小写）
            if import_username.lower() in existing_usernames:
                existing_user = existing_usernames[import_username.lower()]
                
                # 查找导入数据中对应的电子邮件
                import_email = None
                for user_data in data.get('users', []):
                    if isinstance(user_data, dict) and user_data.get('username') == import_username:
                        import_email = user_data.get('email')
                        break
                
                conflicts.append({
                    'import_username': import_username,
                    'import_email': import_email,
                    'existing_username': existing_user['username'],
                    'existing_id': existing_user['id']
                })
        
        return jsonify({
            'success': True,
            'conflicts': conflicts
        })
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"检查用户名重复出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@user_bp.route('/api/import', methods=['POST'])
@login_required
def import_users():
    """导入用户数据"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
        data = request.json
        
        # 确保data是一个dict
        if not isinstance(data, dict):
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
            
        users = data.get('users', [])
        conflict_actions = data.get('conflict_actions', {})
        
        # 确保users是列表
        if not isinstance(users, list):
            return jsonify({'success': False, 'message': 'users必须是列表'}), 400
        
        # 确保conflict_actions是字典
        if not isinstance(conflict_actions, dict):
            return jsonify({'success': False, 'message': 'conflict_actions必须是字典'}), 400
        
        # 获取所有现有用户名（不区分大小写）
        existing_users = User.query.all()
        existing_usernames = {user.username.lower(): user for user in existing_users}
        
        # 导入统计
        stats = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # 记录导入日志
        import_log = []
        
        # 导入用户数据
        for user_data in users:
            try:
                username = user_data.get('username')
                if not username:
                    logger.warning(f"跳过无用户名的记录: {user_data}")
                    stats['skipped'] += 1
                    import_log.append(f"跳过无用户名的记录")
                    continue
                
                # 检查用户名是否存在
                existing_user = None
                for existing_username, user in existing_usernames.items():
                    if username.lower() == existing_username:
                        existing_user = user
                        break
                
                # 如果用户名存在，检查冲突处理方式
                if existing_user:
                    action = conflict_actions.get(username, 'skip')
                    
                    if action == 'skip':
                        logger.info(f"跳过已存在的用户: {username}")
                        stats['skipped'] += 1
                        import_log.append(f"跳过已存在的用户: {username}")
                        continue
                        
                    elif action == 'override':
                        logger.info(f"覆盖已存在的用户: {username}")
                        
                        # 更新用户信息
                        existing_user.real_name = user_data.get('real_name', existing_user.real_name)
                        existing_user.company_name = user_data.get('company_name', existing_user.company_name)
                        existing_user.email = user_data.get('email', existing_user.email)
                        existing_user.phone = user_data.get('phone', existing_user.phone)
                        existing_user.role = user_data.get('role', existing_user.role)
                        existing_user.is_active = user_data.get('is_active', existing_user.is_active)
                        
                        # 处理创建时间
                        if user_data.get('created_at'):
                            try:
                                # 尝试转换ISO格式的日期字符串为时间戳
                                created_at = datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00')).timestamp()
                                existing_user.created_at = created_at
                            except Exception as e:
                                logger.warning(f"无法解析创建时间: {user_data['created_at']}, 错误: {str(e)}")
                        
                        db.session.commit()
                        stats['updated'] += 1
                        import_log.append(f"更新用户: {username}")
                
                # 如果用户名不存在，创建新用户
                else:
                    # 生成随机密码
                    import random
                    import string
                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                    
                    # 创建新用户
                    new_user = User(
                        username=username,
                        real_name=user_data.get('real_name', ''),
                        company_name=user_data.get('company_name', ''),
                        email=user_data.get('email', ''),
                        phone=user_data.get('phone', ''),
                        role=user_data.get('role', 'user'),
                        is_active=user_data.get('is_active', False)
                    )
                    
                    # 设置密码
                    new_user.set_password(password)
                    
                    # 处理创建时间
                    if user_data.get('created_at'):
                        try:
                            # 尝试转换ISO格式的日期字符串为时间戳
                            created_at = datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00')).timestamp()
                            new_user.created_at = created_at
                        except Exception as e:
                            logger.warning(f"无法解析创建时间: {user_data['created_at']}, 错误: {str(e)}")
                    
                    db.session.add(new_user)
                    db.session.commit()
                    
                    # 发送邀请邮件
                    from app.utils.email import send_user_invitation_email
                    user_data_with_password = user_data.copy()
                    user_data_with_password['password'] = password
                    email_sent = send_user_invitation_email(user_data_with_password)
                    
                    if email_sent:
                        logger.info(f"用户创建成功，邀请邮件已发送: {username}")
                        import_log.append(f"创建用户并发送邀请邮件: {username}")
                    else:
                        logger.warning(f"用户创建成功，但邀请邮件发送失败: {username}")
                        import_log.append(f"创建用户但邀请邮件发送失败: {username}")
                    
                    stats['imported'] += 1
                
            except Exception as e:
                logger.error(f"处理用户数据时出错: {str(e)}")
                stats['errors'] += 1
                import_log.append(f"处理用户数据时出错: {user_data.get('username', '未知')} - {str(e)}")
        
        logger.info(f"用户导入完成: 导入={stats['imported']}, 更新={stats['updated']}, 跳过={stats['skipped']}, 错误={stats['errors']}")
        
        # 记录导入日志到数据库或文件系统
        # TODO: 实现导入日志记录功能
        
        return jsonify({
            'success': True,
            'message': '用户导入完成',
            'imported': stats['imported'],
            'updated': stats['updated'],
            'skipped': stats['skipped'],
            'errors': stats['errors'],
            'log': import_log
        })
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"导入用户时出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500 

@user_bp.route('/manage-permissions', methods=['GET', 'POST'])
@login_required
def manage_role_permissions():
    """角色权限设置页面"""
    # 检查用户是否有访问权限
    if not current_user.has_permission('permission', 'view'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 处理POST请求 - 直接保存权限设置而不通过API
    if request.method == 'POST':
        try:
            import json
            
            # 解析请求JSON数据
            data = request.get_json()
            if not data:
                logger.error("保存角色权限时请求数据为空")
                return jsonify({
                    'success': False,
                    'message': '请求数据为空'
                }), 400
            
            role = data.get('role')
            # 规范化角色键名
            normalized_role = normalize_role_key(role)
            
            permissions = data.get('permissions', [])
            
            logger.info(f"直接保存角色权限：角色={normalized_role}，权限数量={len(permissions)}")
            
            if not normalized_role or not permissions:
                return jsonify({
                    'success': False,
                    'message': '角色名称或权限数据不能为空'
                }), 400
            
            # admin角色不允许修改
            if normalized_role == 'admin':
                return jsonify({
                    'success': False,
                    'message': '管理员角色权限不允许修改'
                }), 403
            
            # 查找所有具有该角色的用户
            from app.permissions import ROLE_PERMISSIONS
            if normalized_role not in ROLE_PERMISSIONS:
                return jsonify({
                    'success': False,
                    'message': f"角色'{normalized_role}'不存在"
                }), 404
            
            users = User.query.filter_by(role=normalized_role).all()
            
            if not users:
                return jsonify({
                    'success': True,
                    'message': f"角色'{normalized_role}'没有关联用户，无需更新权限"
                })
            
            # 更新用户权限
            updated_count = 0
            
            try:
                for user in users:
                    # 删除现有权限
                    Permission.query.filter_by(user_id=user.id).delete()
                    
                    # 添加新权限
                    for perm in permissions:
                        if not isinstance(perm, dict) or 'module' not in perm:
                            continue
                        
                        module = perm.get('module')
                        if not module:
                            continue
                        
                        # 创建新权限记录
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
                
                # 提交事务
                db.session.commit()
                
                # 清除会话缓存
                if 'permissions' in session:
                    del session['permissions']
                
                return jsonify({
                    'success': True,
                    'message': f"角色权限更新成功，已更新{updated_count}个用户的权限"
                })
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"保存角色权限时出错: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f"保存权限时出错: {str(e)}"
                }), 500
                
        except Exception as e:
            logger.error(f"处理角色权限保存请求时出错: {str(e)}")
            return jsonify({
                'success': False,
                'message': '服务器处理请求时出错'
            }), 500
    
    # GET请求处理逻辑保持不变
    try:
        import requests
        import json
        import traceback
        
        # 获取API URL路径 - 使用绝对URL而不是相对路径
        api_url_base = request.host_url.rstrip('/') + url_for('api_v1.index').rstrip('/')
        logger.info(f"API基础URL: {api_url_base}")
        
        # 创建请求头，包含用户令牌
        jwt_token = session.get("jwt_token", "")
        if not jwt_token:
            logger.error("JWT令牌不存在，无法访问API")
            flash('会话已过期，请重新登录', 'danger')
            return redirect(url_for('auth.login'))
            
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        logger.info(f"准备请求API，请求头: {headers}")
        
        # 1. 获取所有角色信息
        try:
            from app.permissions import ROLE_PERMISSIONS
            from app.utils.role_mappings import normalize_role_key, get_role_display_name
            from app.models.dictionary import Dictionary
            
            # 从字典表中获取角色列表
            dict_roles = Dictionary.query.filter_by(type='role', is_active=True).order_by(Dictionary.sort_order).all()
            
            # 从ROLE_PERMISSIONS中获取有效的权限角色列表，以便过滤
            valid_perm_roles = set(ROLE_PERMISSIONS.keys())
            
            # 将角色转换为前端需要的格式（只包含ROLE_PERMISSIONS中存在的角色）
            roles = []
            for role_dict in dict_roles:
                # 规范化角色键名
                norm_key = normalize_role_key(role_dict.key)
                
                # 只添加在权限系统中存在的角色
                if norm_key in valid_perm_roles:
                    roles.append({
                        'key': norm_key,  # 使用规范化后的键作为API调用的标识符
                        'name': role_dict.value  # 使用字典中的值作为显示名称
                    })
            
            logger.info(f"成功获取角色列表: {len(roles)}个角色")
        except Exception as roles_error:
            logger.error(f"获取角色列表时出错: {str(roles_error)}")
            logger.error(traceback.format_exc())
            flash('获取角色列表时出错，请稍后重试', 'danger')
            return redirect(url_for('user.list_users'))
        
        # 2. 获取模块列表 - 直接从API获取
        try:
            # 构建模块API URL
            modules_api_url = f"{api_url_base}/modules"
            logger.info(f"开始请求模块列表API: {modules_api_url}")
            
            # 发送API请求
            try:
                modules_response = requests.get(modules_api_url, headers=headers, timeout=10)
                logger.info(f"模块API响应状态码: {modules_response.status_code}")
                
                if modules_response.status_code == 200:
                    modules_data = modules_response.json()
                    if modules_data.get('success'):
                        modules = modules_data.get('data', [])
                        logger.info(f"成功获取模块列表: {len(modules)}个模块")
                    else:
                        logger.warning(f"API返回错误: {modules_data.get('message')}")
                        # 使用预定义模块列表
                        modules = get_default_modules()
                else:
                    logger.warning(f"API请求失败，状态码: {modules_response.status_code}, 响应内容: {modules_response.text}")
                    # 使用预定义模块列表
                    modules = get_default_modules()
            except requests.RequestException as req_err:
                logger.error(f"请求模块API时出错: {str(req_err)}")
                # 使用预定义模块列表
                modules = get_default_modules()
        except Exception as modules_error:
            logger.error(f"获取模块列表过程中出错: {str(modules_error)}")
            logger.error(traceback.format_exc())
            # 使用预定义模块列表
            modules = get_default_modules()
        
        # 确保数据格式正确 - 避免可能的JSON序列化问题
        modules = [dict(module) for module in modules]
        roles = [dict(role) for role in roles]
        
        # 渲染模板
        return render_template(
            'user/role_permissions.html',
            roles=roles,
            modules=modules
        )
    
    except Exception as e:
        logger.error(f"加载角色权限设置页面时出错: {str(e)}")
        logger.error(traceback.format_exc())
        flash('加载角色权限设置页面时出错，请稍后重试', 'danger')
        return redirect(url_for('user.list_users'))

def get_default_modules():
    """获取默认模块列表"""
    return [
        {"id": "project", "name": "项目管理", "description": "管理销售项目和跟进"},
        {"id": "customer", "name": "客户管理", "description": "管理客户信息和联系人"},
        {"id": "quotation", "name": "报价管理", "description": "管理产品报价"},
        {"id": "product", "name": "产品管理", "description": "管理产品信息和价格"},
        {"id": "product_code", "name": "产品编码", "description": "管理产品编码系统"},
        {"id": "user", "name": "用户管理", "description": "管理系统用户"},
        {"id": "permission", "name": "权限管理", "description": "管理用户权限"}
    ] 