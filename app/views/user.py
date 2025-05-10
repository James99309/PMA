from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app.models.user import User, Permission, DataAffiliation, User as UserModel
from app import db
import logging
import json
from datetime import datetime
from app.utils.dictionary_helpers import get_role_display_name
from app.models.dictionary import Dictionary
from app.models.project import Project
from app.models.customer import Company
from app.models.quotation import Quotation
from app.models.role_permissions import RolePermission
from app.utils.access_control import get_viewable_data, can_edit_data

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

    # 统一归属过滤
    query = get_viewable_data(User, current_user)
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
    if request.method == 'POST':
        username = request.form.get('username')
        real_name = request.form.get('real_name')
        company_name = request.form.get('company')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        role = request.form.get('role')
        is_active = 'is_active' in request.form
        is_department_manager = 'is_department_manager' in request.form
        logger.info(f"[用户创建] 操作人: {current_user.username}, 参数: username={username}, email={email}, role={role}, is_active={is_active}")
        if not email or not email.strip():
            logger.warning(f"[用户创建] 邮箱为空，操作人: {current_user.username}")
            flash('邮箱不能为空', 'danger')
            return render_template('user/edit.html', user=None, is_edit=False)
        email = email.strip()
        if User.query.filter_by(username=username).first():
            logger.warning(f"[用户创建] 用户名已存在: {username}")
            flash('用户名已存在', 'danger')
            return render_template('user/edit.html', user=None, is_edit=False)
        if email and User.query.filter_by(email=email).first():
            logger.warning(f"[用户创建] 邮箱已存在: {email}")
            flash('邮箱已存在', 'danger')
            return render_template('user/edit.html', user=None, is_edit=False)
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
        import secrets
        temp_password = secrets.token_urlsafe(12)
        user.set_password(temp_password)
        try:
            db.session.add(user)
            db.session.commit()
            if is_active:
                from app.utils.email import send_user_invitation_email
                user_data = {
                    "id": user.id,
                    "username": username,
                    "real_name": real_name,
                    "company_name": company_name,
                    "email": email,
                    "phone": phone,
                    "department": department,
                    "is_department_manager": is_department_manager,
                    "role": role
                }
                email_sent = send_user_invitation_email(user_data)
                if email_sent:
                    flash('用户创建成功，邀请邮件已发送至用户邮箱', 'success')
                else:
                    flash('用户创建成功，但邀请邮件发送失败，请手动通知用户', 'warning')
            else:
                flash('用户创建成功', 'success')
            return redirect(url_for('user.list_users'))
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"[用户创建] 失败: {str(db_error)}", exc_info=True)
            flash(f'用户创建失败: {str(db_error)}', 'danger')
            return render_template('user/edit.html', user=None, is_edit=False)

@user_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """编辑用户页面和处理"""
    # GET请求 - 显示编辑表单
    if request.method == 'GET':
        user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
        if not user:
            flash('用户不存在或无权限编辑', 'danger')
            return redirect(url_for('user.list_users'))
        user_data = user.to_dict()
        return render_template('user/edit.html', user=user_data, is_edit=True)
    # POST请求 - 处理编辑表单提交
    if request.method == 'POST':
        user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
        if not user:
            flash('用户不存在或无权限编辑', 'danger')
            return redirect(url_for('user.list_users'))
        from app.utils.access_control import can_edit_data
        if not can_edit_data(user, current_user):
            flash('无权限编辑该用户', 'danger')
            return redirect(url_for('user.list_users'))
        real_name = request.form.get('real_name')
        company = request.form.get('company')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        role = request.form.get('role')
        password = request.form.get('password')
        is_active = 'is_active' in request.form
        is_department_manager = 'is_department_manager' in request.form
        logger.info(f"[用户编辑] 操作人: {current_user.username}, 目标用户: {user.username}, 参数: email={email}, role={role}, is_active={is_active}")
        # 邮箱非空校验
        if not email or not email.strip():
            flash('邮箱不能为空', 'danger')
            user_data = user.to_dict()
            return render_template('user/edit.html', user=user_data, is_edit=True)
        email = email.strip()
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
            # 判断是否由未激活变为激活
            if is_active and not getattr(user, '_was_active', True):
                from app.utils.email import send_user_invitation_email
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "real_name": user.real_name,
                    "company_name": user.company_name,
                    "email": user.email,
                    "phone": user.phone,
                    "department": user.department,
                    "is_department_manager": user.is_department_manager,
                    "role": user.role
                }
                email_sent = send_user_invitation_email(user_data)
                if email_sent:
                    flash('邀请邮件已发送至用户邮箱', 'success')
                else:
                    flash('邀请邮件发送失败，请手动通知用户', 'warning')
            else:
                flash('用户信息更新成功', 'success')
            return redirect(url_for('user.list_users'))
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"[用户编辑] 失败: {str(db_error)}", exc_info=True)
            flash(f'更新失败: {str(db_error)}', 'danger')
            user_data = user.to_dict()
            return render_template('user/edit.html', user=user_data, is_edit=True)

@user_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """删除用户"""
    # 归属过滤，确保只能删除有权限的用户
    user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
    if not user:
        flash('用户不存在或无权限删除', 'danger')
        return redirect(url_for('user.list_users'))
    # 禁止删除当前登录用户
    if current_user.id == user_id:
        flash('不能删除当前登录用户', 'danger')
        return redirect(url_for('user.list_users'))
    logger.info(f"[用户删除] 操作人: {current_user.username}, 目标用户ID: {user_id}")
    try:
        # 删除前检查引用关系
        has_references = False
        reference_tables = []
        # 检查企业表
        from app.models.customer import Company
        if Company.query.filter_by(owner_id=user_id).count() > 0:
            has_references = True
            reference_tables.append('企业')
        # 检查联系人表
        from app.models.customer import Contact
        if Contact.query.filter_by(owner_id=user_id).count() > 0:
            has_references = True
            reference_tables.append('联系人')
        # 检查项目表
        from app.models.project import Project
        if Project.query.filter_by(owner_id=user_id).count() > 0:
            has_references = True
            reference_tables.append('项目')
        # 检查沟通记录表
        from app.models.action import Action
        if Action.query.filter_by(owner_id=user_id).count() > 0:
            has_references = True
            reference_tables.append('沟通记录')
        # 只要有业务数据就阻止删除
        if has_references:
            flash(f'用户拥有{", ".join(reference_tables)}数据，建议设置为非活动状态而不是删除。如需强制删除，请先将这些数据转移给其他用户。', 'warning')
            return redirect(url_for('user.edit_user', user_id=user_id))
        # 自动清理归属关系
        from app.models.user import Affiliation, DataAffiliation
        Affiliation.query.filter((Affiliation.owner_id == user_id) | (Affiliation.viewer_id == user_id)).delete(synchronize_session=False)
        DataAffiliation.query.filter((DataAffiliation.owner_id == user_id) | (DataAffiliation.viewer_id == user_id)).delete(synchronize_session=False)
        db.session.delete(user)
        db.session.commit()
        logger.info(f"[用户删除] 成功，目标用户ID: {user_id}")
        flash('用户删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"[用户删除] 失败: {str(e)}", exc_info=True)
        flash('删除用户时发生错误，请稍后重试', 'danger')
    return redirect(url_for('user.list_users'))

@user_bp.route('/permissions/<int:user_id>', methods=['GET', 'POST'])
@login_required
def manage_permissions(user_id):
    """管理用户权限（优先查个人权限，无则查角色模板）"""
    if request.method == 'GET':
        # 归属过滤
        user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
        if not user:
            flash('用户不存在或无权限查看', 'danger')
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
            logger.warning(f"[DEBUG] manage_permissions 被调用，收到请求: user_id={user_id}, form_data={form_data}")
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
            logger.warning(f"[DEBUG] 写入 permissions 表，user_id={user_id}, permissions={permissions}")
            user = User.query.get(user_id)
            if not user:
                flash('用户不存在', 'danger')
                return redirect(url_for('user.list_users'))
            Permission.query.filter_by(user_id=user_id).delete()
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
                logger.warning(f"[DEBUG] permissions 表写入完成，user_id={user_id}")
                flash('用户权限更新成功', 'success')
                return redirect(url_for('user.list_users'))
            except Exception as db_error:
                db.session.rollback()
                logger.error(f'[DEBUG] manage_permissions 保存异常: {str(db_error)}')
                flash(f'权限更新失败: {str(db_error)}', 'danger')
                return redirect(url_for('user.manage_permissions', user_id=user_id))
        except Exception as e:
            logger.error(f'[DEBUG] manage_permissions 处理权限保存请求时出错: {str(e)}', exc_info=True)
            flash('服务器处理请求时出错，请稍后重试', 'danger')
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
    # 归属过滤
    target_user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
    if not target_user:
        flash('用户不存在或无权限查看', 'danger')
        return redirect(url_for('user.list_users'))
    return render_template(
        'user/affiliations.html',
        target_user=target_user
    )

@user_bp.route('/api/check-duplicates', methods=['POST'])
@login_required
def check_duplicates():
    """检查用户重复API"""
    try:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        user_id = data.get('user_id')
        if not field or not value:
            return jsonify({'success': False, 'message': '缺少必要参数', 'data': None}), 400
        query = User.query.filter(getattr(User, field) == value)
        if user_id:
            query = query.filter(User.id != user_id)
        exists = query.first() is not None
        return jsonify({'success': True, 'message': '检查完成', 'data': {'exists': exists}})
    except Exception as e:
        logger.error(f"检查用户重复时出错: {str(e)}")
        return jsonify({'success': False, 'message': f"检查失败: {str(e)}", 'data': None}), 500

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
            logger.warning(f"[DEBUG] manage_role_permissions 被调用，收到请求: {data}")
            role = data.get('role')
            permissions = data.get('permissions', [])
            logger.warning(f"[DEBUG] 写入 role_permissions 表，role={role}, permissions={permissions}")
            if not role or not permissions:
                return jsonify({'success': False, 'message': '角色名称或权限数据不能为空'}), 400
            if role == 'admin':
                return jsonify({'success': False, 'message': '管理员角色权限不允许修改'}), 403
            RolePermission.query.filter_by(role=role).delete()
            for perm in permissions:
                if not isinstance(perm, dict) or 'module' not in perm or not perm['module']:
                    continue
                rp = RolePermission(
                    role=role,
                    module=perm['module'],
                    can_view=bool(perm.get('can_view', False)),
                    can_create=bool(perm.get('can_create', False)),
                    can_edit=bool(perm.get('can_edit', False)),
                    can_delete=bool(perm.get('can_delete', False))
                )
                db.session.add(rp)
            db.session.commit()
            logger.warning(f"[DEBUG] role_permissions 表写入完成，role={role}")
            return jsonify({'success': True, 'message': f"角色权限模板已保存"})
        except Exception as e:
            db.session.rollback()
            logger.error(f"[DEBUG] manage_role_permissions 保存异常: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'message': f"保存权限模板时出错: {str(e)}"}), 500
    # GET请求
    try:
        # 已移除 ROLE_PERMISSIONS 导入，因为它不存在
        # 只取已启用的角色字典项，全部显示
        dict_roles = Dictionary.query.filter_by(type='role', is_active=True).order_by(Dictionary.sort_order).all()
        roles = []
        for role_dict in dict_roles:
            roles.append({'key': role_dict.key, 'value': role_dict.value})
        modules = get_default_modules()
        modules = [dict(module) for module in modules]
        roles = [dict(role) for role in roles]
        
        # 如果URL中指定了role参数，设置默认选中的角色
        selected_role = request.args.get('role', '')
        
        return render_template('user/role_permissions.html', roles=roles, modules=modules, selected_role=selected_role)
    except Exception as e:
        logger.error(f"加载角色权限设置页面时出错: {str(e)}")
        flash('加载角色权限设置页面时出错，请稍后重试', 'danger')
        return redirect(url_for('user.list_users'))

@user_bp.route('/manage-roles', methods=['GET'])
@login_required
def manage_roles():
    """角色字典管理页面（管理dictionaries表中type=role的记录）"""
    if not current_user.has_permission('permission', 'view'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # 获取所有角色字典项，包括禁用的，按排序号排序
        dict_roles = Dictionary.query.filter_by(type='role').order_by(Dictionary.sort_order).all()
        roles = [role.to_dict() for role in dict_roles]  # 使用to_dict方法转换为字典
        
        return render_template('user/role_management.html', roles=roles)
    except Exception as e:
        logger.error(f"加载角色管理页面时出错: {str(e)}")
        flash('加载角色管理页面时出错，请稍后重试', 'danger')
        return redirect(url_for('user.list_users'))

@user_bp.route('/manage-companies', methods=['GET'])
@login_required
def manage_companies():
    """企业字典管理页面（管理dictionaries表中type=company的记录）"""
    if not current_user.has_permission('permission', 'view'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # 获取所有企业字典项，包括禁用的，按排序号排序
        dict_companies = Dictionary.query.filter_by(type='company').order_by(Dictionary.sort_order).all()
        companies = [company.to_dict() for company in dict_companies]  # 使用to_dict方法转换为字典
        
        return render_template('user/company_management.html', companies=companies)
    except Exception as e:
        logger.error(f"加载企业字典管理页面时出错: {str(e)}")
        flash('加载企业字典管理页面时出错，请稍后重试', 'danger')
        return redirect(url_for('user.list_users'))

@user_bp.route('/manage-departments', methods=['GET'])
@login_required
def manage_departments():
    """部门字典管理页面（管理dictionaries表中type=department的记录）"""
    if not current_user.has_permission('permission', 'view'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # 获取所有部门字典项，包括禁用的，按排序号排序
        dict_departments = Dictionary.query.filter_by(type='department').order_by(Dictionary.sort_order).all()
        departments = [department.to_dict() for department in dict_departments]  # 使用to_dict方法转换为字典
        
        return render_template('user/department_management.html', departments=departments)
    except Exception as e:
        logger.error(f"加载部门字典管理页面时出错: {str(e)}")
        flash('加载部门字典管理页面时出错，请稍后重试', 'danger')
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
    user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
    if not user:
        flash('用户不存在或无权限查看', 'danger')
        return redirect(url_for('user.list_users'))
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
    affiliation_users = []
    aff_qs = DataAffiliation.query.filter_by(viewer_id=user.id).all()
    for aff in aff_qs:
        owner = UserModel.query.get(aff.owner_id)
        if owner:
            affiliation_users.append({
                'user_id': owner.id,
                'username': owner.username,
                'real_name': owner.real_name,
                'role': owner.role,
                'company_name': owner.company_name,
                'department': owner.department,
                'is_department_manager': owner.is_department_manager
            })
    affiliations = {
        'department': user.department if hasattr(user, 'department') else '',
        'role': user.role if hasattr(user, 'role') else '',
        'affiliation_users': affiliation_users,
        'affiliation_count': len(affiliation_users)
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
            return jsonify({'success': False, 'message': '未指定要删除的用户', 'data': None}), 400
        deleted, deactivated = [], []
        allowed_users = get_viewable_data(User, current_user).filter(User.id.in_(user_ids)).all()
        allowed_user_ids = {u.id for u in allowed_users}
        logger.info(f"[批量用户删除] 操作人: {current_user.username}, 目标用户ID列表: {user_ids}")
        for uid in user_ids:
            if uid not in allowed_user_ids:
                continue
            user = next((u for u in allowed_users if u.id == uid), None)
            if not user:
                continue
            has_data = False
            if Project.query.filter_by(owner_id=user.id).first():
                has_data = True
            if Company.query.filter_by(owner_id=user.id).first():
                has_data = True
            if Quotation.query.filter_by(owner_id=user.id).first():
                has_data = True
            if not has_data:
                db.session.delete(user)
                deleted.append(user.username)
            else:
                user.is_active = False
                deactivated.append(user.username)
        db.session.commit()
        logger.info(f"[批量用户删除] 成功，已删除: {deleted}, 已禁用: {deactivated}")
        return jsonify({'success': True, 'message': '批量删除完成', 'data': {'deleted': deleted, 'deactivated': deactivated}})
    except Exception as e:
        db.session.rollback()
        logger.error(f"[批量用户删除] 失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

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

@user_bp.route('/api/v1/users', methods=['POST'])
@login_required
def api_create_user():
    """API方式创建新用户，返回标准JSON结构"""
    try:
        data = request.get_json()
        username = data.get('username')
        real_name = data.get('real_name')
        company_name = data.get('company')
        email = data.get('email')
        phone = data.get('phone')
        department = data.get('department')
        role = data.get('role')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        is_active = data.get('is_active', True)
        is_department_manager = data.get('is_department_manager', False)
        logger.info(f"[API用户创建] 操作人: {current_user.username}, 参数: username={username}, email={email}, role={role}")
        if not email or not email.strip():
            logger.warning(f"[API用户创建] 邮箱为空，操作人: {current_user.username}")
            return jsonify({'success': False, 'message': '邮箱不能为空', 'data': None}), 400
        email = email.strip()
        if password != confirm_password:
            logger.warning(f"[API用户创建] 两次密码不一致，操作人: {current_user.username}")
            return jsonify({'success': False, 'message': '两次输入的密码不一致', 'data': None}), 400
        if User.query.filter_by(username=username).first():
            logger.warning(f"[API用户创建] 用户名已存在: {username}")
            return jsonify({'success': False, 'message': '用户名已存在', 'data': None}), 400
        if email and User.query.filter_by(email=email).first():
            logger.warning(f"[API用户创建] 邮箱已存在: {email}")
            return jsonify({'success': False, 'message': '邮箱已存在', 'data': None}), 400
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
        db.session.add(user)
        db.session.commit()
        logger.info(f"[API用户创建] 成功，用户名: {username}")
        return jsonify({'success': True, 'message': '用户创建成功', 'data': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"[API用户创建] 失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'用户创建失败: {str(e)}', 'data': None}), 500

@user_bp.route('/api/v1/users/<int:user_id>', methods=['PUT'])
@login_required
def api_edit_user(user_id):
    """API方式编辑用户，返回标准JSON结构"""
    user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"[API用户编辑] 无权限或用户不存在，操作人: {current_user.username}, 目标用户ID: {user_id}")
        return jsonify({'success': False, 'message': '用户不存在或无权限编辑', 'data': None}), 403
    from app.utils.access_control import can_edit_data
    if not can_edit_data(user, current_user):
        logger.warning(f"[API用户编辑] 无权限编辑，操作人: {current_user.username}, 目标用户: {user.username}")
        return jsonify({'success': False, 'message': '无权限编辑该用户', 'data': None}), 403
    try:
        data = request.get_json()
        real_name = data.get('real_name')
        company_name = data.get('company')
        email = data.get('email')
        phone = data.get('phone')
        department = data.get('department')
        role = data.get('role')
        password = data.get('password')
        is_active = data.get('is_active', True)
        is_department_manager = data.get('is_department_manager', False)
        logger.info(f"[API用户编辑] 操作人: {current_user.username}, 目标用户: {user.username}, 参数: email={email}, role={role}")
        if not email or not email.strip():
            logger.warning(f"[API用户编辑] 邮箱为空，操作人: {current_user.username}")
            return jsonify({'success': False, 'message': '邮箱不能为空', 'data': None}), 400
        email = email.strip()
        user.real_name = real_name
        user.company_name = company_name
        user.email = email
        user.phone = phone
        user.department = department
        user.role = role
        user.is_active = is_active
        user.is_department_manager = is_department_manager
        if password and password.strip():
            user.set_password(password)
        db.session.commit()
        logger.info(f"[API用户编辑] 成功，目标用户: {user.username}")
        return jsonify({'success': True, 'message': '用户信息更新成功', 'data': user.to_dict()})
    except Exception as db_error:
        db.session.rollback()
        logger.error(f"[API用户编辑] 失败: {str(db_error)}", exc_info=True)
        return jsonify({'success': False, 'message': f'更新失败: {str(db_error)}', 'data': None}), 500 