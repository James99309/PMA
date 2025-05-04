from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app.models.user import User, Permission
from app import db
import logging
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
    return render_template(
        'user/list.html',
        users=users_data,
        total=pagination.total,
        pagination=pagination
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
            # 发送邀请邮件
            from app.utils.email import send_user_invitation_email
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
        company_name = request.form.get('company_name')
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
        try:
            db.session.commit()
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
    """管理用户权限"""
    # GET请求 - 显示权限管理页面
    if request.method == 'GET':
        user = User.query.get(user_id)
        if not user:
            flash('用户不存在', 'danger')
            return redirect(url_for('user.list_users'))
        user_data = user.to_dict()
        # 预定义模块列表
        modules = get_default_modules()
        # 权限字典
        permissions_dict = {}
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
    # POST请求 - 保存权限设置
    if request.method == 'POST':
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
        Permission.query.filter_by(user_id=user_id).delete()
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
            flash('用户权限更新成功', 'success')
            return redirect(url_for('user.list_users'))
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"权限更新失败: {str(db_error)}")
            flash(f'权限更新失败: {str(db_error)}', 'danger')
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
                    company_name=row.get('company_name', ''),
                    department=row.get('department', ''),
                    is_department_manager=is_department_manager,
                    role=normalize_role_key(row['role']),
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
    
    # GET请求处理逻辑
    try:
        from app.permissions import ROLE_PERMISSIONS
        from app.utils.role_mappings import normalize_role_key, get_role_display_name
        from app.models.dictionary import Dictionary
        dict_roles = Dictionary.query.filter_by(type='role', is_active=True).order_by(Dictionary.sort_order).all()
        valid_perm_roles = set(ROLE_PERMISSIONS.keys())
        roles = []
        for role_dict in dict_roles:
            norm_key = normalize_role_key(role_dict.key)
            if norm_key in valid_perm_roles:
                roles.append({
                'key': norm_key,
                'name': role_dict.value
                })
        modules = get_default_modules()
        modules = [dict(module) for module in modules]
        roles = [dict(role) for role in roles]
        return render_template(
            'user/role_permissions.html',
            roles=roles,
            modules=modules
        )
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
    # 查询权限
    permissions = user.permissions if hasattr(user, 'permissions') else []
    # 查询归属关系（如部门、角色等）
    affiliations = {
        'department': user.department if hasattr(user, 'department') else '',
        'role': user.role if hasattr(user, 'role') else '',
        # 可扩展更多归属关系
    }
    return render_template('user/detail.html', user=user, permissions=permissions, affiliations=affiliations) 