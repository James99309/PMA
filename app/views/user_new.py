from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.user import User, Permission, Affiliation
from app.forms.user import UserForm, ChangePasswordForm
from app import db
from app.utils.access_control import get_viewable_data
import logging
import json
import os
from datetime import datetime
from app.models.dictionary import Dictionary
from app.models.project import Project
from app.models.customer import Company
from app.models.quotation import Quotation
from app.models.role_permissions import RolePermission
from app.api.v1.utils import api_response
from app.utils.dictionary_helpers import get_role_display_name

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
    """用户列表页面（带分页、搜索、角色、状态过滤）"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')

    query = User.query
    if search:
        query = query.filter(
            (User.username.like(f'%{search}%')) |
            (User.real_name.like(f'%{search}%')) |
            (User.email.like(f'%{search}%')) |
            (User.company_name.like(f'%{search}%'))
        )
    if role:
        query = query.filter(User.role == role)
    if status:
        is_active = True if status == 'active' else False
        query = query.filter(User.is_active == is_active)

    pagination = query.order_by(User.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    users_data = [user.to_dict() for user in pagination.items]

    # 批量获取企业名称和角色字典映射
    company_dict = {d.key: d.value for d in Dictionary.query.filter_by(type='company').all()}
    role_dict = {d.key: d.value for d in Dictionary.query.filter_by(type='role').all()}

    return render_template(
        'user/list.html',
        users=users_data,
        total=pagination.total,
        pagination=pagination,
        company_dict=company_dict,
        role_dict=role_dict
    )

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
        company = request.form.get('company')
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
        
        # 检查用户名/邮箱唯一性
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('user/edit.html', user=None, is_edit=False)
        if email and User.query.filter_by(email=email).first():
            flash('邮箱已存在', 'danger')
            return render_template('user/edit.html', user=None, is_edit=False)
                
        # 创建用户
        user = User(
            username=username,
            real_name=real_name,
            company_name=company,
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
            # 发送邀请邮件
            from app.utils.email import send_user_invitation_email
            user_data = {
                "username": username,
                "real_name": real_name,
                "company_name": company,
                "email": email,
                "phone": phone,
                "department": department,
                "is_department_manager": is_department_manager,
                "role": role,
                "password": password,
                "is_active": is_active
            }
            email_sent = send_user_invitation_email(user_data)
            if email_sent:
                flash('用户创建成功，邀请邮件已发送至用户邮箱', 'success')
            else:
                flash('用户创建成功，但邀请邮件发送失败，请手动通知用户', 'warning')
            return redirect(url_for('user.list_users'))
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"创建用户时出错: {str(db_error)}")
            flash(f'用户创建失败: {str(db_error)}', 'danger')
            return render_template('user/edit.html', user=None, is_edit=False)

@user_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """编辑用户页面和处理"""
    # GET请求 - 显示编辑表单
    if request.method == 'GET':
        user = User.query.get(user_id)
        if user:
            user_data = user.to_dict()
            return render_template('user/edit.html', user=user_data, is_edit=True)
        else:
            flash('用户不存在', 'danger')
        return redirect(url_for('user.list_users'))
    
    # POST请求 - 处理编辑表单提交
    if request.method == 'POST':
        real_name = request.form.get('real_name')
        company = request.form.get('company')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        role = request.form.get('role')
        password = request.form.get('password')
        is_active = 'is_active' in request.form
        is_department_manager = 'is_department_manager' in request.form
        
        user = User.query.get(user_id)
        if not user:
            flash('用户不存在', 'danger')
            return redirect(url_for('user.list_users'))
                
        old_department = user.department
        old_company = user.company_name
        old_manager = user.is_department_manager
        user.real_name = real_name
        user.company_name = company
        user.email = email
        user.phone = phone
        user.department = department
        user.role = role
        user.is_active = is_active
        user.is_department_manager = is_department_manager
                    
        if password and password.strip():
            user.set_password(password)
        try:
            db.session.commit()
            from app.models.user import sync_department_manager_affiliations, remove_department_manager_affiliations, sync_affiliations_for_new_member, transfer_member_affiliations_on_department_change
            # 负责人变为True
            if not old_manager and is_department_manager:
                sync_department_manager_affiliations(user)
            # 负责人变为False
            elif old_manager and not is_department_manager:
                remove_department_manager_affiliations(user)
            # 部门或公司变更，且仍为负责人
            elif is_department_manager and (old_department != department or old_company != company):
                remove_department_manager_affiliations(user)
                sync_department_manager_affiliations(user)
            # 普通成员变更部门/公司，自动为新部门负责人添加归属，并同步转移归属
            if (old_department != department or old_company != company) and not is_department_manager:
                transfer_member_affiliations_on_department_change(user, old_department, old_company)
            flash('用户信息更新成功', 'success')
            return redirect(url_for('user.list_users'))
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"更新用户信息时出错: {str(db_error)}")
            flash(f'更新失败: {str(db_error)}', 'danger')
            user_data = user.to_dict()
            return render_template('user/edit.html', user=user_data, is_edit=True)

@user_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """删除用户"""
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash('用户删除成功', 'success')
        else:
            flash('用户不存在', 'danger')
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户时出错: {str(e)}")
        flash('删除用户时发生错误，请稍后重试', 'danger')
    return redirect(url_for('user.list_users'))

@user_bp.route('/permissions/<int:user_id>', methods=['GET', 'POST'])
@login_required
def manage_permissions(user_id):
    """管理用户权限（优先查个人权限，无则查角色模板）"""
    if request.method == 'GET':
        user = User.query.get(user_id)
        if not user:
            flash('用户不存在', 'danger')
            return redirect(url_for('user.list_users'))
        user_data = user.to_dict()
        modules = get_default_modules()
        # 优先查个人权限
        permissions_dict = {}
        personal_perms = list(user.permissions)
        if personal_perms:
            for permission in personal_perms:
                permissions_dict[permission.module] = {
                    'module': permission.module,
                    'can_view': permission.can_view,
                    'can_create': permission.can_create,
                    'can_edit': permission.can_edit,
                    'can_delete': permission.can_delete
                }
        else:
            # 查角色模板
            from app.models.role_permissions import RolePermission
            perms = RolePermission.query.filter_by(role=user.role).all()
            for perm in perms:
                permissions_dict[perm.module] = {
                    'module': perm.module,
                    'can_view': perm.can_view,
                    'can_create': perm.can_create,
                    'can_edit': perm.can_edit,
                    'can_delete': perm.can_delete
                }
        return render_template(
            'user/permissions.html',
            user=user_data,
            modules=modules,
            permissions=permissions_dict
        )
    # POST请求 - 保存权限设置
    if request.method == 'POST':
        try:
            form_data = request.form
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
            user = User.query.get(user_id)
            if not user:
                flash('用户不存在', 'danger')
                return redirect(url_for('user.list_users'))
            # 先删除该用户所有旧权限，避免主键冲突
            Permission.query.filter_by(user_id=user_id).delete()
            # 批量插入新权限
            for perm in permissions:
                module = perm.get('module')
                permission = Permission(
                    user_id=user_id,
                    module=module,
                    can_view=bool(perm.get('can_view', False)),
                    can_create=bool(perm.get('can_create', False)),
                    can_edit=bool(perm.get('can_edit', False)),
                    can_delete=bool(perm.get('can_delete', False))
                )
                db.session.add(permission)
            try:
                db.session.commit()
                flash('用户权限更新成功', 'success')
                return redirect(url_for('user.list_users'))
            except Exception as db_error:
                db.session.rollback()
                logger.error(f'权限更新失败: {str(db_error)}')
                flash(f'权限更新失败: {str(db_error)}', 'danger')
                return redirect(url_for('user.manage_permissions', user_id=user_id))
        except Exception as e:
            logger.error(f'处理权限保存请求时出错: {str(e)}', exc_info=True)
            flash('服务器处理请求时出错，请稍后重试', 'danger')
            return redirect(url_for('user.manage_permissions', user_id=user_id))

@user_bp.route('/affiliations')
@login_required
def manage_affiliations():
    """重定向到用户列表"""
    flash('请通过用户管理界面设置用户的数据归属关系', 'info')
    return redirect(url_for('user.list_users'))

@user_bp.route('/user/affiliations/<int:user_id>', methods=['GET'])
@login_required
def manage_user_affiliations(user_id):
    """管理用户数据归属关系 - 直接从数据库获取数据，不经过API"""
    
    # 权限检查
    current_user_id = session.get('user_id')
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        flash('当前用户不存在，请重新登录', 'danger')
        return redirect(url_for('auth.login'))
    
    # 只有管理员、自己或有user.edit权限的用户可管理归属
    has_permission = (current_user.role == 'admin' or 
                      current_user.id == user_id or 
                      current_user.has_permission('user', 'edit'))
    
    if not has_permission:
        flash('您无权限管理此用户的数据归属关系', 'danger')
        return redirect(url_for('user.list_users'))
    
    # 获取目标用户
    target_user = User.query.get(user_id)
    if not target_user:
        flash('目标用户不存在', 'danger')
        return redirect(url_for('user.list_users'))
    
    # 直接从数据库获取用户已有的归属关系
    existing_affiliations = Affiliation.query.filter_by(viewer_id=user_id).all()
    selected_user_ids = [aff.owner_id for aff in existing_affiliations]
    
    # 获取所有活跃用户，包括自己
    all_users = User.query.filter(User.is_active == True).all()
    
    # 构建模板需要的数据结构
    selected_users = []
    for user in all_users:
        if user.id in selected_user_ids:
            selected_users.append({
                'user_id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'role': user.role,
                'company_name': user.company_name,
                'department': user.department,
                'is_department_manager': user.is_department_manager
            })
    
    # 设置JWT令牌用于前端保存操作
    jwt_token = session.get('jwt_token', '')
    
    # 获取角色字典
    role_dict = current_app.config.get('ROLE_DICT', {})
    
    return render_template(
        'user/affiliations.html',
        target_user=target_user,
        selected_users=selected_users,
        jwt_token=jwt_token,
        role_dict=role_dict
    )

@user_bp.route('/api/check-duplicates', methods=['POST'])
@login_required
def check_duplicates():
    """检查用户重复API"""
    try:
        # 从请求中获取要检查的字段和值
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        user_id = data.get('user_id')  # 编辑时的用户ID
        
        if not field or not value:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
            
        # 构建查询
        query = User.query.filter(getattr(User, field) == value)
        
        # 如果是编辑模式，排除当前用户ID
        if user_id:
            query = query.filter(User.id != user_id)
            
        # 检查是否存在
        exists = query.first() is not None
        
        return jsonify({
            'success': True,
            'exists': exists
        })
        
    except Exception as e:
        logger.error(f"检查用户重复时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"检查失败: {str(e)}"
        }), 500

@user_bp.route('/api/import', methods=['POST'])
@login_required
def import_users():
    """批量导入用户"""
    if not current_user.has_permission('user', 'create'):
        flash('您没有批量导入用户的权限', 'danger')
        return redirect(url_for('user.list_users'))
        
    try:
        # 检查是否有文件上传
        if 'csv_file' not in request.files:
            flash('没有选择文件', 'danger')
            return redirect(url_for('user.list_users'))
            
        file = request.files['csv_file']
        
        # 检查文件名是否为空
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(url_for('user.list_users'))
            
        # 检查文件类型
        if not file.filename.endswith('.csv'):
            flash('只支持CSV文件格式', 'danger')
            return redirect(url_for('user.list_users'))
            
        # 尝试使用API导入
        api_url = f"{request.host_url.rstrip('/')}{API_BASE_URL}/users/import"
        
        # 使用JWT令牌认证
        headers = get_auth_headers()
        
        # 准备multipart/form-data请求
        files = {'csv_file': (file.filename, file.stream, 'text/csv')}
        
        response = requests.post(api_url, files=files, headers=headers)
        
        # 添加JSON解析的异常处理
        try:
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                imported_count = data.get('data', {}).get('imported_count', 0)
                errors = data.get('data', {}).get('errors', [])
                
                if errors:
                    flash(f'已成功导入 {imported_count} 名用户，但有 {len(errors)} 条记录导入失败', 'warning')
                else:
                    flash(f'成功导入 {imported_count} 名用户', 'success')
                    
                return redirect(url_for('user.list_users'))
        except json.JSONDecodeError as e:
            logger.error(f"导入用户API响应JSON解析错误: {str(e)}")
            # 如果JSON解析失败，继续直接处理CSV文件
        
        # 如果API导入失败，尝试直接导入CSV文件
        logger.warning("通过API导入失败，尝试直接导入CSV文件")
        
        # 读取CSV文件内容
        file.stream.seek(0)  # 重置文件指针
        import csv
        
        # 使用UTF-8编码读取，以防止中文乱码
        csv_data = file.read().decode('utf-8-sig')
        csv_reader = csv.DictReader(csv_data.splitlines())
        
        # 跟踪导入统计
        imported_count = 0
        errors = []
        
        # 处理每一行
        for row in csv_reader:
            try:
                # 必要字段检查
                required_fields = ['username', 'real_name', 'email', 'password', 'role']
                for field in required_fields:
                    if field not in row or not row[field]:
                        raise ValueError(f"行 {csv_reader.line_num}: 缺少必要字段 '{field}'")
                
                # 检查用户名是否已存在
                if User.query.filter_by(username=row['username']).first():
                    raise ValueError(f"行 {csv_reader.line_num}: 用户名 '{row['username']}' 已存在")
                
                # 检查电子邮件是否已存在
                if 'email' in row and row['email'] and User.query.filter_by(email=row['email']).first():
                    raise ValueError(f"行 {csv_reader.line_num}: 电子邮件 '{row['email']}' 已存在")
                
                # 规范化字段
                is_active = row.get('is_active', '').lower() in ['true', 'yes', '1', 'y', 't']
                is_department_manager = row.get('is_department_manager', '').lower() in ['true', 'yes', '1', 'y', 't']
                
                # 创建新用户
                new_user = User(
                    username=row['username'],
                    real_name=row['real_name'],
                    email=row['email'],
                    phone=row.get('phone', ''),
                    company_name=row.get('company', ''),
                    department=row.get('department', ''),
                    is_department_manager=is_department_manager,
                    role=row['role'],
                    is_active=is_active
                )
                
                # 设置密码
                new_user.set_password(row['password'])
                
                # 保存用户
                db.session.add(new_user)
                imported_count += 1
                
            except Exception as user_error:
                errors.append(f"行 {csv_reader.line_num}: {str(user_error)}")
                continue
        
        # 提交事务
        if imported_count > 0:
            try:
                db.session.commit()
                if errors:
                    flash(f'已成功导入 {imported_count} 名用户，但有 {len(errors)} 条记录导入失败', 'warning')
                else:
                    flash(f'成功导入 {imported_count} 名用户', 'success')
            except Exception as commit_error:
                db.session.rollback()
                logger.error(f"提交导入用户事务时出错: {str(commit_error)}")
                flash('导入过程中发生错误，所有更改已回滚', 'danger')
                return redirect(url_for('user.list_users'))
        else:
            flash('没有用户被导入，请检查CSV文件格式', 'warning')
        
        return redirect(url_for('user.list_users'))
        
    except Exception as e:
        logger.error(f"导入用户时出错: {str(e)}")
        flash(f'导入过程中发生错误: {str(e)}', 'danger')
        return redirect(url_for('user.list_users'))

@user_bp.route('/manage-permissions', methods=['GET', 'POST'])
@login_required
def manage_role_permissions():
    """角色权限设置页面（只操作role_permissions表）"""
    if not current_user.has_permission('permission', 'view'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                logger.error("保存角色权限时请求数据为空")
                return jsonify({'success': False, 'message': '请求数据为空'}), 400
            role = data.get('role')
            normalized_role = role
            permissions = data.get('permissions', [])
            logger.info(f"保存角色权限模板：角色={normalized_role}，权限数量={len(permissions)}")
            if not normalized_role or not permissions:
                return jsonify({'success': False, 'message': '角色名称或权限数据不能为空'}), 400
            if normalized_role == 'admin':
                return jsonify({'success': False, 'message': '管理员角色权限不允许修改'}), 403
            # 先删除该角色所有旧模板
            RolePermission.query.filter_by(role=normalized_role).delete()
            # 批量插入新模板
            for perm in permissions:
                if not isinstance(perm, dict) or 'module' not in perm or not perm['module']:
                    continue
                rp = RolePermission(
                    role=normalized_role,
                    module=perm['module'],
                    can_view=bool(perm.get('can_view', False)),
                    can_create=bool(perm.get('can_create', False)),
                    can_edit=bool(perm.get('can_edit', False)),
                    can_delete=bool(perm.get('can_delete', False))
                )
                db.session.add(rp)
            db.session.commit()
            return jsonify({'success': True, 'message': f"角色权限模板已保存"})
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存角色权限模板时出错: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'message': f"保存权限模板时出错: {str(e)}"}), 500
    # GET请求
    try:
        # 以下代码只取已启用的角色字典项，全部显示
        dict_roles = Dictionary.query.filter_by(type='role', is_active=True).order_by(Dictionary.sort_order).all()
        roles = []
        for role_dict in dict_roles:
            roles.append({'key': role_dict.key, 'value': role_dict.value})
        modules = get_default_modules()
        modules = [dict(module) for module in modules]
        roles = [dict(role) for role in roles]
        return render_template('user/role_permissions.html', roles=roles, modules=modules)
    except Exception as e:
        logger.error(f"加载角色权限设置页面时出错: {str(e)}")
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

@user_bp.route('/detail/<int:user_id>')
@login_required
def user_detail(user_id):
    """用户详情页，展示基本信息、权限、归属关系，分选项卡"""
    user = User.query.get_or_404(user_id)
    # 查询权限，优先查个人权限，无则查角色模板
    personal_perms = list(user.permissions) if hasattr(user, 'permissions') else []
    permissions = []
    if personal_perms:
        for perm in personal_perms:
            permissions.append({
                'module': perm.module,
                'can_view': perm.can_view,
                'can_create': perm.can_create,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete
            })
    else:
        from app.models.role_permissions import RolePermission
        perms = RolePermission.query.filter_by(role=user.role).all()
        for perm in perms:
            permissions.append({
                'module': perm.module,
                'can_view': perm.can_view,
                'can_create': perm.can_create,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete
            })
    # 查询归属关系（如部门、角色等）
    affiliations = {
        'department': user.department if hasattr(user, 'department') else '',
        'role': user.role if hasattr(user, 'role') else '',
        # 可扩展更多归属关系
    }
    role_display_name = get_role_display_name(user.role)
    # 用户详情页
    role_dict = {d.key: d.value for d in Dictionary.query.filter_by(type='role').all()}
    modules = get_default_modules()
    return render_template(
        'user/detail.html',
        user=user,
        permissions=permissions,
        affiliations=affiliations,
        role_display_name=role_display_name,
        role_dict=role_dict,
        modules=modules
    )

@user_bp.route('/batch-delete', methods=['POST'])
@login_required
def batch_delete_users():
    """批量删除用户：无数据可物理删除，有数据则改为未激活"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        if not user_ids or not isinstance(user_ids, list):
            return jsonify({'success': False, 'message': '未指定要删除的用户'}), 400
        deleted, deactivated = [], []
        for uid in user_ids:
            user = User.query.get(uid)
            if not user:
                continue
            # 检查是否有关联数据
            has_data = False
            if Project.query.filter_by(owner_id=user.id).first():
                has_data = True
            if Company.query.filter_by(owner_id=user.id).first():
                has_data = True
            if Quotation.query.filter_by(owner_id=user.id).first():
                has_data = True
            # 可扩展更多业务表...
            if not has_data:
                db.session.delete(user)
                deleted.append(user.username)
            else:
                user.is_active = False
                deactivated.append(user.username)
                db.session.commit()
        return jsonify({'success': True, 'deleted': deleted, 'deactivated': deactivated})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500 

def to_dict(self):
    """将用户信息转为字典，用于API响应"""
    return {
        'id': self.id,
        'username': self.username,
        'real_name': self.real_name,
        'company_name': self.company_name,
        'email': self.email,
        'phone': self.phone,
        'department': self.department,
        'is_department_manager': self.is_department_manager,
        'is_active': self.is_active,
        'is_profile_complete': self.is_profile_complete,
        'role': self.role,
        'created_at': self.created_at,
        'updated_at': self.updated_at if hasattr(self, 'updated_at') else None,
        'last_login': self.last_login
    } 

# 直接从数据库获取用户数据，不经过API
@user_bp.route('/api/get_all_users', methods=['GET'])
@login_required
def get_all_users_api():
    """获取所有活跃用户，用于前端显示"""
    try:
        # 获取所有活跃用户
        users = User.query.filter(User.is_active == True).all()
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'role': user.role,
                'company_name': user.company_name,
                'department': user.department,
                'is_department_manager': user.is_department_manager
            })
                
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': result
        })
    except Exception as e:
        logging.error(f"获取所有用户失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取所有用户失败: {str(e)}",
            'data': []
        }), 500
                
# 直接从数据库获取已选用户，不经过API
@user_bp.route('/api/get_selected_users/<int:user_id>', methods=['GET'])
@login_required
def get_selected_users_api(user_id):
    """获取用户已有的归属关系，用于前端显示"""
    try:
        # 权限检查
        if current_user.role != 'admin' and current_user.id != user_id and not current_user.has_permission('user', 'view'):
            return jsonify({
                'success': False,
                'message': '无权限访问此数据',
                'data': []
            }), 403
        
        # 获取已有归属关系
        affiliations = Affiliation.query.filter_by(viewer_id=user_id).all()
        result = []
        
        for affiliation in affiliations:
            owner = User.query.get(affiliation.owner_id)
            if owner:
                result.append({
                    'user_id': owner.id,
                    'username': owner.username,
                    'real_name': owner.real_name,
                    'role': owner.role,
                    'company_name': owner.company_name,
                    'department': owner.department,
                    'is_department_manager': owner.is_department_manager
                })
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': result
        })
    except Exception as e:
        logging.error(f"获取已选用户失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取已选用户失败: {str(e)}",
            'data': []
        }), 500

# 直接保存用户归属关系，不经过API
@user_bp.route('/api/save_affiliations/<int:user_id>', methods=['POST'])
@login_required
def save_affiliations_api(user_id):
    """保存用户归属关系，直接操作数据库"""
    try:
        # 权限检查
        if current_user.role != 'admin' and current_user.id != user_id and not current_user.has_permission('user', 'edit'):
            return jsonify({
                'success': False,
                'message': '无权限操作此数据'
            }), 403
        
        # 检查用户是否存在
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 获取提交的所有者ID列表
        data = request.get_json()
        owner_ids = data.get('owner_ids', [])
        
        # 检查数据格式
        if not isinstance(owner_ids, list):
            return jsonify({
                'success': False,
                'message': '无效的数据格式，owner_ids必须是数组'
            }), 400
        
        try:
            # 删除现有的所有归属关系
            Affiliation.query.filter_by(viewer_id=user_id).delete()
            
            # 创建新的归属关系
            added_count = 0
            for owner_id in owner_ids:
                try:
                    # 确保所有者ID是整数
                    owner_id = int(owner_id)
                    
                    # 确保所有者ID存在且有效
                    owner = User.query.get(owner_id)
                    if owner and owner.id != user_id:  # 不能将自己设为自己的数据所有者
                        # 添加到Affiliation表
                        affiliation = Affiliation(viewer_id=user_id, owner_id=owner_id)
                        db.session.add(affiliation)
                        added_count += 1
                except (ValueError, TypeError):
                    # 跳过无效的ID
                    continue
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'数据归属关系设置成功，已添加{added_count}条记录'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'设置失败: {str(e)}'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'发生错误: {str(e)}'
        }), 500 