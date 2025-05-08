from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from app.models.customer import Company, Contact, COMPANY_TYPES
from app.models.user import User
from app import db
from app.permissions import permission_required
from app.utils.access_control import get_viewable_data, can_edit_data
from app.models.project import Project
from app.models.action import Action
from sqlalchemy import or_, func, desc, text
from datetime import datetime
import difflib
import json

customer = Blueprint('customer', __name__)

@customer.route('/')
@permission_required('customer', 'view')
def list_companies():
    search = request.args.get('search', '')
    
    # 获取排序参数
    sort_field = request.args.get('sort', 'updated_at')
    sort_order = request.args.get('order', 'desc')
    
    # 验证排序字段是否有效
    valid_sort_fields = ['company_code', 'company_name', 'company_type', 'industry', 
                         'country', 'region', 'status', 'owner_id', 
                         'updated_at', 'created_at']
    
    if sort_field not in valid_sort_fields:
        sort_field = 'company_name'
    
    # 使用通用数据访问控制函数获取查询
    query = get_viewable_data(Company, current_user)
    
    # 添加搜索条件
    if search:
        query = query.filter(Company.company_name.ilike(f'%{search}%'))
    
    # 添加排序
    if hasattr(Company, sort_field):
        order_attr = getattr(Company, sort_field)
        if sort_order == 'desc':
            query = query.order_by(order_attr.desc())
        else:
            query = query.order_by(order_attr.asc())
        
    companies = query.all()
    
    # 预加载所有企业的所有者信息
    owner_ids = [company.owner_id for company in companies if company.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for company in companies:
            if company.owner_id and company.owner_id in owners:
                company.owner = owners[company.owner_id]
    
    # 国家代码到名称的映射
    country_code_to_name = {
        "CN": "中国", "US": "美国", "JP": "日本", "DE": "德国", "FR": "法国", "GB": "英国", "CA": "加拿大", "AU": "澳大利亚", "NZ": "新西兰", "IN": "印度", "RU": "俄罗斯", "BR": "巴西", "ZA": "南非", "SG": "新加坡", "MY": "马来西亚", "TH": "泰国", "ID": "印度尼西亚", "PH": "菲律宾", "VN": "越南", "KR": "韩国", "AE": "阿联酋", "SA": "沙特阿拉伯", "IT": "意大利", "ES": "西班牙", "NL": "荷兰", "CH": "瑞士", "SE": "瑞典", "NO": "挪威", "FI": "芬兰", "DK": "丹麦", "BE": "比利时"
    }
    return render_template('customer/list.html', 
                          companies=companies, 
                          search_term=search, 
                          sort_field=sort_field, 
                          sort_order=sort_order,
                          country_code_to_name=country_code_to_name)

@customer.route('/search', methods=['GET'])
@permission_required('customer', 'view')
def search_companies():
    search = request.args.get('search', '')
    if not search:
        return redirect(url_for('customer.list_companies'))
    
    # 使用数据访问控制
    query = get_viewable_data(Company, current_user)
    
    # 添加搜索条件
    query = query.filter(Company.company_name.ilike(f'%{search}%'))
    companies = query.all()
    
    return render_template('customer/list.html', companies=companies, search_term=search)

@customer.route('/search_contacts', methods=['GET'])
@permission_required('customer', 'view')
def search_contacts():
    search = request.args.get('search', '')
    
    if not search:
        return redirect(url_for('customer.list_companies'))
    
    # 使用数据访问控制
    query = get_viewable_data(Contact, current_user)
    
    if search:
        # 搜索联系人
        contacts = query.filter(Contact.name.ilike(f'%{search}%')).all()
    else:
        contacts = query.limit(50).all()  # 限制结果数量
    
    # 获取联系人所属的公司信息
    company_ids = set(contact.company_id for contact in contacts if contact.company_id)
    companies = {company.id: company for company in Company.query.filter(Company.id.in_(company_ids)).all()}
    
    # 为每个联系人添加company属性
    for contact in contacts:
        if contact.company_id and contact.company_id in companies:
            contact.company = companies[contact.company_id]
    
    # 返回搜索结果专用模板，不使用contacts.html
    return render_template('customer/search_results.html', contacts=contacts, search_term=search)

@customer.route('/view/<int:company_id>')
@permission_required('customer', 'view')
def view_company(company_id):
    company = Company.query.get_or_404(company_id)
    
    # 检查查看权限
    allowed_user_ids = current_user.get_viewable_user_ids()
    if current_user.role != 'admin' and company.owner_id not in allowed_user_ids:
        flash('您没有权限查看此企业信息', 'danger')
        return redirect(url_for('customer.list_companies'))
    
    # 获取企业的联系人列表
    contacts = Contact.query.filter_by(company_id=company_id).all()
    
    # 预加载所有联系人的所有者信息
    owner_ids = [contact.owner_id for contact in contacts if contact.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for contact in contacts:
            if contact.owner_id and contact.owner_id in owners:
                contact.owner = owners[contact.owner_id]
    
    # 如果需要，确保公司的动作记录已正确加载并按日期排序
    if hasattr(company, 'actions') and company.actions:
        company.actions.sort(key=lambda x: x.date, reverse=True)
    
    # 查询与该企业相关的所有项目
    projects = Project.query.filter(
        or_(
            Project.end_user == company.company_name,
            Project.design_issues.like(f'%{company.company_name}%'),
            Project.contractor == company.company_name,
            Project.system_integrator == company.company_name,
            Project.dealer == company.company_name
        )
    ).all()
    
    # 获取公司的行动记录
    page = request.args.get('page', 1, type=int)
    query = Action.query.filter_by(company_id=company_id)
    pagination = query.order_by(Action.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    actions = pagination.items
    
    # 提前加载行动记录所有者信息，避免N+1查询
    user_ids = [action.owner_id for action in actions if action.owner_id]
    users = User.query.filter(User.id.in_(set(user_ids))).all()
    user_map = {user.id: user for user in users}
    
    for action in actions:
        if action.owner_id and action.owner_id in user_map:
            action.owner = user_map[action.owner_id]
    
    # 国家代码到名称的映射
    country_code_to_name = {
        "CN": "中国", "US": "美国", "JP": "日本", "DE": "德国", "FR": "法国", "GB": "英国", "CA": "加拿大", "AU": "澳大利亚", "NZ": "新西兰", "IN": "印度", "RU": "俄罗斯", "BR": "巴西", "ZA": "南非", "SG": "新加坡", "MY": "马来西亚", "TH": "泰国", "ID": "印度尼西亚", "PH": "菲律宾", "VN": "越南", "KR": "韩国", "AE": "阿联酋", "SA": "沙特阿拉伯", "IT": "意大利", "ES": "西班牙", "NL": "荷兰", "CH": "瑞士", "SE": "瑞典", "NO": "挪威", "FI": "芬兰", "DK": "丹麦", "BE": "比利时"
    }
    return render_template('customer/view.html', 
                          company=company, 
                          contacts=contacts, 
                          actions=actions, 
                          pagination=pagination,
                          projects=projects,
                          country_code_to_name=country_code_to_name)

@customer.route('/add', methods=['GET', 'POST'])
@permission_required('customer', 'create')
def add_company():
    if request.method == 'POST':
        try:
            company = Company(
                company_name=request.form['company_name'],
                country=request.form.get('country'),
                region=request.form.get('region'),
                address=request.form.get('address'),
                industry=request.form.get('industry'),
                company_type=request.form.get('company_type'),
                status=request.form.get('status', '活跃'),
                notes=request.form.get('notes'),
                owner_id=current_user.id  # 设置当前用户为所有者
            )
            db.session.add(company)
            db.session.commit()
            flash('企业添加成功！', 'success')
            return redirect(url_for('customer.view_company', company_id=company.id))
        except Exception as e:
            db.session.rollback()
            import traceback
            # 增强日志输出，包含表单内容和traceback
            flash('保存失败：' + str(e) + '<br>表单内容：' + str(dict(request.form)) + '<br>' + traceback.format_exc(), 'danger')
    
    return render_template('customer/add.html')

@customer.route('/edit/<int:company_id>', methods=['GET', 'POST'])
@permission_required('customer', 'edit')
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)
    
    # 检查编辑权限
    if not can_edit_data(company, current_user):
        flash('您没有权限编辑此企业信息', 'danger')
        return redirect(url_for('customer.view_company', company_id=company_id))
    
    if request.method == 'POST':
        try:
            company.company_name = request.form['company_name']
            company.country = request.form.get('country')
            company.region = request.form.get('region')
            company.address = request.form.get('address')
            company.industry = request.form.get('industry')
            company.company_type = request.form.get('company_type')
            company.status = request.form.get('status')
            company.notes = request.form.get('notes')
            
            db.session.commit()
            flash('企业信息更新成功！', 'success')
            return redirect(url_for('customer.view_company', company_id=company.id))
        except Exception as e:
            db.session.rollback()
            flash('保存失败：' + str(e), 'danger')
    
    return render_template('customer/edit.html', company=company)

@customer.route('/delete/<int:company_id>', methods=['POST'])
@permission_required('customer', 'delete')
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    
    # 检查删除权限
    if not can_edit_data(company, current_user):
        flash('您没有权限删除此企业', 'danger')
        return redirect(url_for('customer.list_companies'))
    
    try:
        # 找到与此公司相关的所有行动记录
        related_actions = Action.query.filter_by(company_id=company.id).all()
        
        # 删除所有相关的行动记录
        for action in related_actions:
            db.session.delete(action)
            
        # 然后删除公司 (这将级联删除联系人，因为在模型中设置了cascade='all, delete-orphan')
        db.session.delete(company)
        db.session.commit()
        flash('企业删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash('删除失败：' + str(e), 'danger')
    
    return redirect(url_for('customer.list_companies'))

@customer.route('/<int:company_id>/contacts')
@permission_required('customer', 'view')
def list_contacts(company_id):
    company = Company.query.get_or_404(company_id)
    
    # 预加载所有联系人的所有者信息
    owner_ids = [contact.owner_id for contact in company.contacts if contact.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for contact in company.contacts:
            if contact.owner_id and contact.owner_id in owners:
                contact.owner = owners[contact.owner_id]
    
    return render_template('customer/contacts.html', company=company)

@customer.route('/<int:company_id>/contacts/add', methods=['GET', 'POST'])
@permission_required('customer', 'create')
def add_contact(company_id):
    company = Company.query.get_or_404(company_id)
    
    # 检查创建权限
    if not can_edit_data(company, current_user):
        flash('您没有权限为此企业添加联系人', 'danger')
        return redirect(url_for('customer.list_contacts', company_id=company_id))
    
    if request.method == 'POST':
        contact = Contact(
            company_id=company_id,
            name=request.form['name'],
            department=request.form['department'],
            position=request.form['position'],
            phone=request.form['phone'],
            email=request.form['email'],
            notes=request.form['notes'],
            owner_id=current_user.id  # 设置联系人所有者为当前用户
        )
        db.session.add(contact)
        db.session.commit()
        
        if request.form.get('is_primary'):
            contact.set_as_primary()
            
        flash('联系人添加成功！', 'success')
        return redirect(url_for('customer.view_company', company_id=company_id))
    return render_template('customer/add_contact.html', company=company)

@customer.route('/<int:company_id>/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@permission_required('customer', 'edit')
def edit_contact(company_id, contact_id):
    contact = Contact.query.get_or_404(contact_id)
    company = Company.query.get_or_404(company_id)
    
    # 检查编辑权限
    if not can_edit_data(company, current_user):
        flash('您没有权限编辑此企业的联系人', 'danger')
        return redirect(url_for('customer.list_contacts', company_id=company_id))
    
    if request.method == 'POST':
        contact.name = request.form['name']
        contact.department = request.form['department']
        contact.position = request.form['position']
        contact.phone = request.form['phone']
        contact.email = request.form['email']
        contact.notes = request.form['notes']
        
        # 处理主要联系人状态
        if request.form.get('is_primary'):
            contact.set_as_primary()
        elif contact.is_primary:  # 如果之前是主要联系人，现在取消了
            contact.is_primary = False
            
        db.session.commit()
        flash('联系人信息更新成功！', 'success')
        return redirect(url_for('customer.list_contacts', company_id=contact.company_id))
    return render_template('customer/edit_contact.html', contact=contact)

@customer.route('/<int:company_id>/contacts/<int:contact_id>/delete', methods=['POST'])
@permission_required('customer', 'delete')
def delete_contact(company_id, contact_id):
    contact = Contact.query.get_or_404(contact_id)
    company = Company.query.get_or_404(company_id)

    # 权限校验
    if not can_edit_data(company, current_user):
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '您没有权限删除此联系人'}), 403
        flash('您没有权限删除此联系人', 'danger')
        return redirect(url_for('customer.view_company', company_id=company_id))

    try:
        # 删除相关行动记录
        related_actions = Action.query.filter_by(contact_id=contact.id).all()
        for action in related_actions:
            db.session.delete(action)
        db.session.delete(contact)
        db.session.commit()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        flash('联系人已删除', 'success')
        return redirect(url_for('customer.view_company', company_id=company_id))
    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '删除失败：' + str(e)}), 500
        flash('删除联系人失败', 'danger')
        return redirect(url_for('customer.view_company', company_id=company_id))

@customer.route('/api/contacts/<int:contact_id>/add_action', methods=['POST'])
@permission_required('customer', 'create')
def add_action_api(contact_id):
    """通过API添加行动记录"""
    try:
        contact = Contact.query.get_or_404(contact_id)
        company = contact.company
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
        data = request.json
        # 验证必填字段
        if not data.get('communication'):
            return jsonify({'success': False, 'message': '沟通情况不能为空'}), 400
        if not data.get('date'):
            return jsonify({'success': False, 'message': '日期不能为空'}), 400
        # 获取项目ID，如果未选择则设为None
        project_id = data.get('project_id') or None
        try:
            # 解析日期，支持ISO格式
            action_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00')).date()
        except ValueError:
            # 尝试标准格式
            action_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        action = Action(
            date=action_date,
            contact_id=contact.id,
            company_id=company.id,
            project_id=project_id,
            communication=data['communication'],
            owner_id=current_user.id
        )
        db.session.add(action)
        db.session.commit()
        # 返回成功信息和新创建的行动记录信息
        return jsonify({
            'success': True, 
            'message': '行动记录添加成功',
            'data': {
                'id': action.id,
                'date': action.date.isoformat(),
                'contact_name': contact.name,
                'contact_id': contact.id,
                'company_name': company.company_name,
                'company_id': company.id,
                'project_id': action.project_id,
                'communication': action.communication,
                'owner_id': action.owner_id
            }
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback_str = traceback.format_exc()
        print(f"添加行动记录出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/company/search')
@permission_required('customer', 'view')
def search_company_api():
    keyword = request.args.get('keyword', '').strip()
    if not keyword or len(keyword) < 1:
        return jsonify({'results': []})
    
    # 优化搜索查询，提高中文单字符匹配效率
    # 使用or_条件组合多个搜索条件，支持任意位置匹配
    from sqlalchemy import or_
    
    # 判断是否为单个中文字符（完整中文字符范围判断）
    is_single_chinese = len(keyword) == 1 and '\u4e00' <= keyword <= '\u9fff'
    
    # 构建搜索条件
    if is_single_chinese:
        # 中文单字符使用包含匹配
        search_condition = Company.company_name.contains(keyword)
    else:
        # 其他情况使用前缀匹配，效率更高
        search_condition = Company.company_name.ilike(f"%{keyword}%")
    
    # 执行查询
    all_matches = Company.query.filter(search_condition).limit(15).all()
    
    # 获取用户有权限查看的公司
    user_authorized_companies = get_viewable_data(Company, current_user).all()
    authorized_ids = {c.id for c in user_authorized_companies}
    
    # 预加载所有公司拥有者信息，避免N+1查询问题
    owner_ids = [c.owner_id for c in all_matches if c.owner_id is not None]
    owners = {}
    if owner_ids:
        for user in User.query.filter(User.id.in_(owner_ids)).all():
            owners[user.id] = user
    
    results = []
    for c in all_matches:
        # 准备地区显示文本
        location = []
        if c.country:
            location.append(c.country)
        if c.region:
            location.append(c.region)
        location_text = " ".join(location)
        
        # 判断用户是否有权限查看/编辑该公司
        has_permission = c.id in authorized_ids
        
        # 获取拥有者信息
        owner_name = "未指定"
        if c.owner_id and c.owner_id in owners:
            owner = owners[c.owner_id]
            owner_name = owner.real_name or owner.username
        
        # 构建紧凑格式的显示文本：企业名称 | 国家 城市 | 拥有者真实姓名
        display_text = c.company_name
        if location_text:
            display_text += f" | {location_text}"
        display_text += f" | {owner_name}"
        
        result = {
            'id': c.id,
            'name': c.company_name,
            'display': display_text,
            'has_permission': has_permission,
            'region': c.region,
            'owner_name': owner_name
        }
        
        # 只有当用户有权限时才返回详细信息
        if has_permission:
            result.update({
                'country': c.country,
                'region': c.region,
                'address': c.address,
                'industry': c.industry,
                'company_type': c.company_type,
                'status': c.status or 'active',
                'notes': c.notes,
                'owner_id': c.owner_id
            })
        
        results.append(result)
    
    return jsonify({'results': results})

@customer.route('/api/contacts/search_by_name')
@permission_required('customer', 'view')
def search_contact_api():
    keyword = request.args.get('keyword', '').strip()
    if not keyword or len(keyword) < 1:
        return jsonify({'results': []})
    
    # 判断是否为单个中文字符（完整中文字符范围判断）
    is_single_chinese = len(keyword) == 1 and '\u4e00' <= keyword <= '\u9fff'
    
    # 构建搜索条件
    if is_single_chinese:
        # 中文单字符使用包含匹配
        search_condition = Contact.name.contains(keyword)
    else:
        # 其他情况使用模糊匹配
        search_condition = Contact.name.ilike(f"%{keyword}%")
    
    # 执行查询
    all_matches = Contact.query.filter(search_condition).limit(15).all()
    
    # 获取用户有权限查看的公司ID
    user_authorized_companies = get_viewable_data(Company, current_user).all()
    authorized_company_ids = {c.id for c in user_authorized_companies}
    
    results = []
    for contact in all_matches:
        # 预加载公司信息，避免N+1查询
        company = Company.query.get(contact.company_id)
        if not company:
            continue
            
        # 判断用户是否有权限查看该联系人所属的公司
        can_view_enterprise = contact.company_id in authorized_company_ids
        
        # 获取地区信息用于显示
        location = []
        if company.region:
            location.append(company.region)
        location_text = ", ".join(location)
        
        result = {
            'id': contact.id,
            'name': contact.name,
            'company_id': company.id,
            'company_name': company.company_name,
            'display': f"{contact.name} ({company.company_name})",
            'position': contact.position or '',
            'department': contact.department or '',
            'can_view_enterprise': can_view_enterprise
        }
        
        results.append(result)
    
    return jsonify({'results': results})

@customer.route('/api/check-duplicates', methods=['POST'])
@permission_required('customer', 'create')
def check_duplicates():
    """检查企业名称重复"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        # 打印请求内容，帮助调试
        print(f"收到check-duplicates请求: {request.data}")
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            print(f"请求不是JSON格式: {request.data}")
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
        
        data = request.json
        
        # 确保data是一个dict
        if not isinstance(data, dict):
            print(f"请求数据不是字典: {data}")
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        company_names = data.get('company_names', [])
        
        # 确保company_names是一个列表
        if not isinstance(company_names, list):
            print(f"company_names不是列表: {company_names}")
            return jsonify({'success': False, 'message': 'company_names必须是列表'}), 400
        
        if not company_names:
            return jsonify({'success': False, 'message': '没有提供企业名称'}), 400
        
        # 检查列表中的每个元素是否为字符串
        for i, name in enumerate(company_names):
            if not isinstance(name, str):
                print(f"company_names中的元素[{i}]不是字符串: {name}")
                # 尝试转换为字符串
                try:
                    company_names[i] = str(name)
                except:
                    # 如果转换失败，则移除该元素
                    print(f"无法将元素[{i}]转换为字符串，已移除")
                    company_names[i] = ""
        
        # 过滤掉空字符串
        company_names = [name for name in company_names if name]
        
        if not company_names:
            return jsonify({'success': False, 'message': '没有有效的企业名称'}), 400
        
        print(f"过滤后的企业名称列表: {company_names}")
        
        # 获取所有现有企业名称
        existing_companies = Company.query.with_entities(Company.id, Company.company_name).all()
        existing_names = {company.company_name: company.id for company in existing_companies}
        
        conflicts = []
        for import_name in company_names:
            # 如果名称完全匹配
            if import_name in existing_names:
                conflicts.append({
                    'import_name': import_name,
                    'existing_name': import_name,
                    'existing_id': existing_names[import_name],
                    'similarity': 1.0
                })
                continue
            
            # 模糊匹配
            for existing_name, existing_id in existing_names.items():
                # 对于中文名称，使用较高的相似度阈值以减少错误匹配
                similarity = difflib.SequenceMatcher(None, import_name, existing_name).ratio()
                
                # 提高阈值，只有较高相似度或完全包含才判定为冲突
                if len(import_name) >= 3 and len(existing_name) >= 3:
                    # 提取相似部分，判断是否有连续的中文字符
                    blocks = difflib.SequenceMatcher(None, import_name, existing_name).get_matching_blocks()
                    
                    # 判断是否有从左到右的前缀匹配（优先考虑公司名称开头部分）
                    left_to_right_match = False
                    for block in blocks:
                        # 检查是否为左侧开始的匹配（import_name的起始位置或existing_name的起始位置）
                        if (block.a == 0 or block.b == 0) and block.size >= 3:
                            left_to_right_match = True
                            break
                    
                    # 找到连续的中文字符匹配
                    continuous_match = False
                    longest_match_size = 0
                    for block in blocks:
                        if block.size > longest_match_size:
                            longest_match_size = block.size
                        
                        # 对于4个以上的中文字符匹配，需要进一步判断
                        if block.size >= 4:
                            # 提取匹配部分的文本
                            import_substr = import_name[block.a:block.a+block.size]
                            existing_substr = existing_name[block.b:block.b+block.size]
                            
                            # 检查提取的子串是否含有常见的公司名称后缀（如"有限公司"、"股份"等）
                            common_suffixes = ["有限公司", "股份", "科技", "集团", "公司"]
                            contains_common_suffix = any(suffix in import_substr for suffix in common_suffixes) or \
                                                    any(suffix in existing_substr for suffix in common_suffixes)
                            
                            # 如果不包含常见后缀，则更可能是实质性匹配
                            if not contains_common_suffix:
                                continuous_match = True
                                break
                        
                        # 对于3个字符的匹配，只有在从左到右或相似度很高的情况下才考虑
                        elif block.size == 3 and (left_to_right_match or similarity > 0.75):
                            continuous_match = True
                            break
                    
                    # 检查是否一方完全包含另一方（处理简称情况），但忽略常见后缀
                    def normalize_company_name(name):
                        # 去除常见的公司后缀
                        suffixes = ["有限公司", "有限责任公司", "股份有限公司", "股份公司", "公司"]
                        normalized = name
                        for suffix in suffixes:
                            normalized = normalized.replace(suffix, "")
                        return normalized.strip()
                    
                    norm_import = normalize_company_name(import_name)
                    norm_existing = normalize_company_name(existing_name)
                    
                    name_contains = (norm_import in norm_existing or norm_existing in norm_import) and \
                                    min(len(norm_import), len(norm_existing)) >= 2  # 确保有意义的匹配
                    
                    # 或者整体相似度较高(提高到超过0.8)
                    high_similarity = similarity > 0.8
                    
                    # 前缀匹配给予更高权重
                    prefix_match = import_name.startswith(existing_name[:3]) or existing_name.startswith(import_name[:3])
                    
                    # 综合判断是否构成冲突
                    is_conflict = (continuous_match and (left_to_right_match or longest_match_size >= 4)) or \
                                  (name_contains and similarity > 0.6) or \
                                  high_similarity or \
                                  (prefix_match and similarity > 0.65)
                    
                    if is_conflict:
                        print(f"发现潜在冲突: '{import_name}' vs '{existing_name}', " 
                              f"相似度={similarity:.2f}, 连续匹配长度={longest_match_size}, "
                              f"从左到右匹配={left_to_right_match}, 名称包含={name_contains}")
                        
                        conflicts.append({
                            'import_name': import_name,
                            'existing_name': existing_name,
                            'existing_id': existing_id,
                            'similarity': similarity
                        })
        
        # 对于每个导入名称，只保留相似度最高的匹配项
        filtered_conflicts = {}
        for conflict in conflicts:
            import_name = conflict['import_name']
            if import_name not in filtered_conflicts or conflict['similarity'] > filtered_conflicts[import_name]['similarity']:
                filtered_conflicts[import_name] = conflict
        
        # 添加推荐操作字段
        for import_name, conflict in filtered_conflicts.items():
            # 根据相似度添加推荐操作：≥0.8推荐跳过，<0.8推荐添加为新用户
            if conflict['similarity'] >= 0.8:
                conflict['recommended_action'] = 'ignore'  # 建议跳过
            else:
                conflict['recommended_action'] = 'keep'    # 建议添加为新用户
        
        result = {
            'success': True,
            'conflicts': list(filtered_conflicts.values())
        }
        
        print(f"检查重复完成，返回结果: {len(filtered_conflicts)}条冲突")
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"检查重复出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/check-contact-duplicates', methods=['POST'])
@permission_required('customer', 'create')
def check_contact_duplicates():
    """检查联系人导入冲突"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
        data = request.json
        contacts = data.get('contacts', [])
        company_names = data.get('company_names', [])
        
        # 检查格式
        if not isinstance(contacts, list):
            return jsonify({'success': False, 'message': 'contacts必须是列表'}), 400
            
        if not isinstance(company_names, list):
            return jsonify({'success': False, 'message': 'company_names必须是列表'}), 400
        
        # 1. 检查公司是否存在
        company_not_found = []
        company_map = {}  # 公司名称到ID的映射
        
        # 查询所有公司
        all_companies = Company.query.filter_by(is_deleted=False).all()
        all_company_names = {company.company_name: company.id for company in all_companies}
        
        # 检查每个公司名称是否存在
        for company_name in company_names:
            if not company_name:
                continue
                
            if company_name not in all_company_names:
                # 记录未找到的公司
                not_found_contacts = [c for c in contacts if c.get('company_name') == company_name]
                for contact in not_found_contacts:
                    company_not_found.append({
                        'company_name': company_name,
                        'name': contact.get('name', '')
                    })
            else:
                # 记录公司ID映射，方便后续使用
                company_map[company_name] = all_company_names[company_name]
        
        # 2. 检查联系人冲突
        conflicts = []
        
        # 按公司分组
        for company_name, company_id in company_map.items():
            # 查询该公司的所有联系人
            existing_contacts = Contact.query.filter_by(company_id=company_id).all()
            existing_contacts_names = {contact.name.lower(): contact for contact in existing_contacts}
            
            # 检查导入联系人是否与已有联系人冲突
            for contact in contacts:
                if contact.get('company_name') != company_name or not contact.get('name'):
                    continue
                    
                contact_name = contact.get('name').lower()
                if contact_name in existing_contacts_names:
                    # 生成联系人冲突的唯一标识
                    contact_key = f"{company_id}_{contact_name}"
                    
                    # 记录冲突信息
                    conflict = {
                        'contact_key': contact_key,
                        'import_contact': contact,
                        'existing_contact': {
                            'id': existing_contacts_names[contact_name].id,
                            'name': existing_contacts_names[contact_name].name,
                            'company_id': company_id,
                            'company_name': company_name
                        }
                    }
                    conflicts.append(conflict)
        
        return jsonify({
            'success': True,
            'company_not_found': company_not_found,
            'conflicts': conflicts
        })
        
    except Exception as e:
        print(f"检查联系人冲突出错: {str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str)
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/import-contacts', methods=['POST'])
@permission_required('customer', 'create')
def import_contacts():
    """导入联系人数据"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        print(f"收到联系人导入请求: {request.data}")
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            print(f"请求不是JSON格式: {request.data}")
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
        data = request.json
        
        # 确保data是一个dict
        if not isinstance(data, dict):
            print(f"请求数据不是字典: {data}")
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
            
        contacts = data.get('contacts', [])
        conflict_actions = data.get('conflict_actions', {})
        owner_id = data.get('owner_id')
        
        # 确保contacts是列表
        if not isinstance(contacts, list):
            print(f"contacts不是列表: {contacts}")
            return jsonify({'success': False, 'message': 'contacts必须是列表'}), 400
        
        # 确保conflict_actions是字典
        if not isinstance(conflict_actions, dict):
            print(f"conflict_actions不是字典: {conflict_actions}")
            return jsonify({'success': False, 'message': 'conflict_actions必须是字典'}), 400
        
        # 验证归属账户是否存在
        owner = User.query.get(owner_id)
        if not owner:
            return jsonify({'success': False, 'message': '指定的归属账户不存在'}), 400
        
        # 取得所有公司信息，用于匹配
        companies = {company.company_name: company.id for company in Company.query.filter_by(is_deleted=False).all()}
        
        # 取得所有联系人信息，用于检查冲突
        all_contacts = {}
        for company_id in set(companies.values()):
            all_contacts[company_id] = {
                contact.name.lower(): contact
                for contact in Contact.query.filter_by(company_id=company_id).all()
            }
        
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        error_details = []
        
        for contact_data in contacts:
            company_name = contact_data.get('company_name', '')
            contact_name = contact_data.get('name', '')
            
            if not company_name or not contact_name:
                error_count += 1
                error_details.append({
                    'record': contact_data,
                    'reason': '公司名称或联系人姓名为空'
                })
                continue
            
            # 查找公司ID
            if company_name not in companies:
                error_count += 1
                error_details.append({
                    'record': contact_data,
                    'reason': f'公司"{company_name}"不存在于系统中'
                })
                continue
                
            company_id = companies[company_name]
            
            try:
                # 检查是否存在冲突
                contact_key = f"{company_id}_{contact_name.lower()}"
                if company_id in all_contacts and contact_name.lower() in all_contacts[company_id]:
                    # 有冲突的情况
                    action = conflict_actions.get(contact_key, 'keep')
                    
                    if action == 'keep':
                        # 跳过此联系人
                        skipped_count += 1
                        continue
                    
                    # 覆盖现有联系人
                    existing_contact = all_contacts[company_id][contact_name.lower()]
                    existing_contact.department = contact_data.get('department', '')
                    existing_contact.position = contact_data.get('position', '')
                    existing_contact.phone = contact_data.get('phone', '')
                    existing_contact.email = contact_data.get('email', '')
                    existing_contact.owner_id = owner_id  # 更新所有者
                    
                    # 处理创建时间
                    if 'created_at' in contact_data and contact_data['created_at']:
                        try:
                            created_at = datetime.fromisoformat(contact_data['created_at'].replace('Z', '+00:00'))
                            existing_contact.created_at = created_at
                        except (ValueError, TypeError):
                            pass
                            
                    # 更新时间设置为当前时间（导入时间）
                    existing_contact.updated_at = datetime.utcnow()
                    
                    db.session.commit()
                    updated_count += 1
                else:
                    # 新建联系人
                    new_contact = Contact(
                        company_id=company_id,
                        name=contact_name,
                        department=contact_data.get('department', ''),
                        position=contact_data.get('position', ''),
                        phone=contact_data.get('phone', ''),
                        email=contact_data.get('email', ''),
                        is_primary=False,  # 默认不是主要联系人
                        owner_id=owner_id
                    )
                    
                    # 处理创建时间
                    if 'created_at' in contact_data and contact_data['created_at']:
                        try:
                            created_at = datetime.fromisoformat(contact_data['created_at'].replace('Z', '+00:00'))
                            new_contact.created_at = created_at
                        except (ValueError, TypeError):
                            pass
                            
                    # 更新时间设置为当前时间（导入时间）
                    new_contact.updated_at = datetime.utcnow()
                    
                    db.session.add(new_contact)
                    db.session.commit()
                    imported_count += 1
                    
            except Exception as e:
                db.session.rollback()
                error_count += 1
                error_details.append({
                    'record': contact_data,
                    'reason': str(e)
                })
                print(f"导入联系人 {contact_name} 出错: {str(e)}")
                
        # 记录导入日志
        import_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': current_user.id,
            'user_name': current_user.username,
            'owner_id': owner_id,
            'owner_name': owner.username,
            'total': len(contacts),
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'error': error_count,
            'notFoundCount': len([c for c in contacts if c.get('company_name', '') not in companies]),
            'error_details': error_details
        }
        
        return jsonify({
            'success': True,
            'message': f'导入完成，新增: {imported_count}，更新: {updated_count}，跳过: {skipped_count}，错误: {error_count}',
            'data': {
                'imported': imported_count,
                'updated': updated_count,
                'skipped': skipped_count,
                'error': error_count,
                'notFoundCount': import_log['notFoundCount'],
                'total': len(contacts),
                'log': import_log,
                'error_details': error_details
            }
        })
        
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"导入联系人数据出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/import', methods=['POST'])
@permission_required('customer', 'create')
def import_customers():
    """导入客户数据"""
    try:
        if not current_user.role == 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以使用此功能'}), 403
        
        print(f"收到导入请求: {request.data}")
        
        # 检查请求是否包含JSON数据
        if not request.is_json:
            print(f"请求不是JSON格式: {request.data}")
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
        data = request.json
        
        # 确保data是一个dict
        if not isinstance(data, dict):
            print(f"请求数据不是字典: {data}")
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
            
        customers = data.get('customers', [])
        conflict_actions = data.get('conflict_actions', {})
        owner_id = data.get('owner_id')
        
        # 确保customers是列表
        if not isinstance(customers, list):
            print(f"customers不是列表: {customers}")
            return jsonify({'success': False, 'message': 'customers必须是列表'}), 400
        
        # 确保conflict_actions是字典
        if not isinstance(conflict_actions, dict):
            print(f"conflict_actions不是字典: {conflict_actions}")
            return jsonify({'success': False, 'message': 'conflict_actions必须是字典'}), 400
            
        # 对导入数据进行去重，确保每个公司名称只出现一次
        import_name_set = set()
        unique_customers = []
        
        for customer in customers:
            if isinstance(customer, dict) and customer.get('company_name'):
                company_name = customer['company_name'].strip()
                if company_name and company_name not in import_name_set:
                    import_name_set.add(company_name)
                    unique_customers.append(customer)
                else:
                    print(f"忽略重复的企业名称: {company_name}")
        
        print(f"去重后的导入数据: {len(unique_customers)}/{len(customers)} 条记录")
        
        # 使用去重后的数据
        customers = unique_customers
        
        # 清理和验证客户数据
        valid_customers = []
        invalid_customers = []  # 存储无效的客户数据及原因
        for i, customer in enumerate(customers):
            if not isinstance(customer, dict):
                print(f"客户数据[{i}]不是字典: {customer}")
                invalid_customers.append({
                    'record': {'index': i, 'data': str(customer)[:100]},  # 截取前100个字符避免过长
                    'reason': '数据格式错误，不是有效的对象'
                })
                continue
                
            # 确保必要字段存在且类型正确
            if 'company_name' not in customer or not customer['company_name']:
                print(f"客户数据[{i}]缺少company_name字段")
                invalid_customers.append({
                    'record': customer,
                    'reason': '缺少企业名称字段或企业名称为空'
                })
                continue
                
            # 确保所有字符串字段的值都是字符串，并且不是'none'
            for field in ['company_name', 'country', 'region', 'address', 'company_type', 'status']:
                if field in customer and customer[field] is not None:
                    if not isinstance(customer[field], str):
                        try:
                            customer[field] = str(customer[field])
                        except:
                            customer[field] = ""
                            invalid_customers.append({
                                'record': {'company_name': customer.get('company_name', '未知'), 'field': field},
                                'reason': f'字段 {field} 无法转换为字符串'
                            })
                    
                    # 如果值是'none'或'None'，则设置为空字符串
                    if customer[field].lower() == 'none':
                        customer[field] = ""
            
            # 处理创建时间
            if 'created_at' in customer and customer['created_at']:
                if isinstance(customer['created_at'], str):
                    try:
                        print(f"尝试解析创建时间: {customer['created_at']}")
                        # 处理ISO 8601格式的日期字符串，去掉Z后添加时区信息
                        if customer['created_at'].endswith('Z'):
                            customer['created_at'] = customer['created_at'].replace('Z', '+00:00')
                        
                        # 尝试从ISO格式解析
                        try:
                            customer['created_at'] = datetime.fromisoformat(customer['created_at'])
                            print(f"成功从ISO格式解析: {customer['created_at']}")
                        except ValueError:
                            # 如果fromisoformat失败，尝试strptime
                            formats = [
                                '%Y-%m-%dT%H:%M:%S.%f%z',  # ISO 8601 with microseconds and timezone
                                '%Y-%m-%d %H:%M:%S',       # Standard datetime
                                '%Y-%m-%d',                # Just date
                                '%d/%m/%Y',                # DD/MM/YYYY
                                '%m/%d/%Y',                # MM/DD/YYYY
                            ]
                            
                            parsed = False
                            for fmt in formats:
                                try:
                                    customer['created_at'] = datetime.strptime(customer['created_at'], fmt)
                                    print(f"使用格式 {fmt} 成功解析: {customer['created_at']}")
                                    parsed = True
                                    break
                                except ValueError:
                                    continue
                            
                            if not parsed:
                                print(f"无法解析创建时间: {customer['created_at']}，使用当前时间")
                                customer['created_at'] = datetime.utcnow()
                                invalid_customers.append({
                                    'record': {'company_name': customer.get('company_name', '未知')},
                                    'reason': '创建时间格式不正确'
                                })
                    except Exception as e:
                        print(f"创建时间解析异常: {e}")
                        customer['created_at'] = datetime.utcnow()
                        invalid_customers.append({
                            'record': {'company_name': customer.get('company_name', '未知')},
                            'reason': f'创建时间格式错误: {str(e)}'
                        })
                elif not isinstance(customer['created_at'], datetime):
                    print(f"创建时间不是字符串也不是datetime对象: {type(customer['created_at'])}")
                    customer['created_at'] = datetime.utcnow()
                    invalid_customers.append({
                        'record': {'company_name': customer.get('company_name', '未知')},
                        'reason': '创建时间格式不正确'
                    })
            else:
                print("未提供创建时间，使用当前时间")
                customer['created_at'] = datetime.utcnow()
                
            valid_customers.append(customer)
        
        if not valid_customers:
            return jsonify({
                'success': False, 
                'message': '没有有效的客户数据', 
                'data': {'error_details': invalid_customers}
            }), 400
            
        print(f"有效客户数据: {len(valid_customers)}条")
        
        if not owner_id:
            return jsonify({
                'success': False, 
                'message': '没有提供归属账户', 
                'data': {'error_details': invalid_customers}
            }), 400
        
        # 验证归属账户是否存在
        owner = User.query.get(owner_id)
        if not owner:
            return jsonify({
                'success': False, 
                'message': '指定的归属账户不存在', 
                'data': {'error_details': invalid_customers}
            }), 400
        
        # 获取现有企业列表(用于检查重复)
        existing_companies = {c.company_name: c for c in Company.query.all()}
        
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        error_details = []  # 添加错误详情列表
        
        # 合并前面验证阶段的错误信息
        error_details.extend(invalid_customers)
        
        for customer_data in valid_customers:
            company_name = customer_data.get('company_name')
            if not company_name:
                error_count += 1
                error_details.append({
                    'record': customer_data,
                    'reason': '企业名称为空'
                })
                continue
            
            try:
                # 检查是否存在冲突处理决策
                action = conflict_actions.get(company_name, 'keep')
                
                # 如果存在同名企业
                if company_name in existing_companies:
                    if action == 'ignore':
                        # 忽略该条数据
                        skipped_count += 1
                        print(f"忽略已存在的企业: {company_name}")
                        continue
                    elif action == 'override':
                        # 更新现有企业
                        company = existing_companies[company_name]
                        
                        # 确保更新值不是'none'或'None'，使用None而不是空字符串
                        if 'country' in customer_data:
                            if customer_data['country'] and customer_data['country'].lower() != 'none':
                                company.country = customer_data['country']
                            elif customer_data['country'] == '' or customer_data['country'].lower() == 'none':
                                company.country = None
                        
                        # 导入表中的城市映射到省份
                        if 'region' in customer_data:
                            if customer_data['region'] and customer_data['region'].lower() != 'none':
                                company.region = customer_data['region']
                            elif customer_data['region'] == '' or customer_data['region'].lower() == 'none':
                                company.region = None
                        
                        if 'address' in customer_data:
                            if customer_data['address'] and customer_data['address'].lower() != 'none':
                                company.address = customer_data['address']
                            elif customer_data['address'] == '' or customer_data['address'].lower() == 'none':
                                company.address = None
                        
                        if 'company_type' in customer_data:
                            if customer_data['company_type'] and customer_data['company_type'].lower() != 'none':
                                company.company_type = customer_data['company_type']
                            elif customer_data['company_type'] == '' or customer_data['company_type'].lower() == 'none':
                                company.company_type = None
                        
                        # 处理备注字段
                        if 'notes' in customer_data:
                            if not customer_data['notes'] or customer_data['notes'].lower() == 'none':
                                company.notes = None
                            else:
                                company.notes = customer_data['notes']
                        
                        # 保留原始创建时间（如果Excel中有指定且有效，则使用；否则保留数据库中现有的）
                        if 'created_at' in customer_data and customer_data['created_at'] and isinstance(customer_data['created_at'], datetime):
                            print(f"覆盖记录 - 设置创建时间: {customer_data['created_at']}")
                            company.created_at = customer_data['created_at']
                        
                        # 更新时间设置为当前时间（导入时间）
                        company.updated_at = datetime.utcnow()
                        print(f"覆盖记录 - 设置更新时间: {company.updated_at}")
                        
                        company.owner_id = owner_id  # 更新所有者
                        db.session.commit()
                        updated_count += 1
                        
                        # 标记此企业已处理，防止重复导入
                        existing_companies.pop(company_name, None)
                        continue
                    else:  # action == 'keep'
                        # 克隆为新记录，但使用不同名称
                        company_name = f"{company_name}_导入_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                        print(f"发现同名企业，重命名为: {company_name}")
                
                # 创建新企业(action == 'keep'或不存在冲突)
                company = Company(
                    company_name=company_name,
                    country=customer_data.get('country', '') if customer_data.get('country') and customer_data.get('country').lower() != 'none' else None,
                    region=customer_data.get('region', '') if customer_data.get('region') and customer_data.get('region').lower() != 'none' else None,  # 导入表中的城市映射到省份
                    address=customer_data.get('address', '') if customer_data.get('address') and customer_data.get('address').lower() != 'none' else None,
                    company_type=customer_data.get('company_type', '') if customer_data.get('company_type') and customer_data.get('company_type').lower() != 'none' else None,
                    status=customer_data.get('status', '活跃') if customer_data.get('status') and customer_data.get('status').lower() != 'none' else '活跃',
                    owner_id=owner_id  # 设置所有者
                )
                
                # 处理备注字段 - 如果是"none"或"None"则设为空字符串
                notes = customer_data.get('notes', '')
                if not notes or notes.lower() == 'none':
                    notes = None
                company.notes = notes
                
                # 设置创建时间和更新时间
                # 保留原始创建时间
                if 'created_at' in customer_data and customer_data['created_at']:
                    print(f"设置创建时间: {customer_data['created_at']}")
                    company.created_at = customer_data['created_at']
                
                # 更新时间设置为当前时间（导入时间）
                company.updated_at = datetime.utcnow()
                print(f"设置更新时间: {company.updated_at}")
                
                db.session.add(company)
                db.session.commit()
                imported_count += 1
                
            except Exception as e:
                db.session.rollback()
                error_count += 1
                error_message = str(e)
                print(f"导入企业 {company_name} 时出错: {error_message}")
                error_details.append({
                    'record': {'company_name': company_name},
                    'reason': error_message
                })
        
        # 记录导入日志
        import_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': current_user.id,
            'user_name': current_user.username,
            'owner_id': owner_id,
            'owner_name': owner.username,
            'total': len(valid_customers),
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'error': error_count,
            'error_details': error_details  # 添加错误详情
        }
        
        # 这里可以实现导入日志的保存逻辑
        # 例如保存到数据库或日志文件
        
        return jsonify({
            'success': True,
            'message': f'导入完成，新增: {imported_count}，更新: {updated_count}，跳过: {skipped_count}，错误: {error_count}',
            'data': {
                'imported': imported_count,
                'updated': updated_count,
                'skipped': skipped_count,
                'error': error_count,
                'log': import_log,
                'error_details': error_details  # 添加错误详情
            }
        })
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"导入客户数据出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/batch-delete', methods=['POST'])
@permission_required('customer', 'delete')
def batch_delete_companies():
    """批量删除企业API"""
    try:
        # 只要有customer.delete权限即可批量删除，但只能删除自己有权限的企业
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
        data = request.json
        company_ids = data.get('company_ids', [])
        
        if not company_ids or not isinstance(company_ids, list):
            return jsonify({'success': False, 'message': '缺少要删除的企业ID列表'}), 400
        
        # 转换为整数列表
        try:
            company_ids = [int(id) for id in company_ids]
        except ValueError:
            return jsonify({'success': False, 'message': '企业ID必须是整数'}), 400
        
        # 获取要删除的企业记录
        companies = Company.query.filter(Company.id.in_(company_ids)).all()
        
        # 检查操作人是否有权限删除这些企业，未授权的企业自动跳过
        unauthorized_companies = []
        deletable_companies = []
        for company in companies:
            if can_edit_data(company, current_user):
                deletable_companies.append(company)
            else:
                unauthorized_companies.append(company.company_name)
        if not deletable_companies:
            return jsonify({
                'success': False,
                'message': '您没有权限删除所选企业'
            }), 403
        
        deleted_count = 0
        errors = []
        
        # 开始事务
        try:
            for company in deletable_companies:
                # 找到与企业相关的所有行动记录
                related_actions = Action.query.filter_by(company_id=company.id).all()
                
                # 删除所有相关的行动记录
                for action in related_actions:
                    db.session.delete(action)
                
                # 删除企业（会级联删除联系人）
                db.session.delete(company)
                deleted_count += 1
            
            # 提交事务
            db.session.commit()
            msg = f'成功删除{deleted_count}个企业'
            if unauthorized_companies:
                msg += f'，无权删除: {", ".join(unauthorized_companies)}'
            return jsonify({
                'success': True,
                'deleted_count': deleted_count,
                'message': msg
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'删除过程中出错: {str(e)}'
            }), 500
        
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"批量删除企业出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/api/actions/<int:action_id>/delete', methods=['POST'])
@permission_required('customer', 'delete')
def delete_action_api(action_id):
    """通过API删除行动记录"""
    try:
        action = Action.query.get_or_404(action_id)
        
        # 检查权限：只有行动记录的创建者和管理员可以删除
        if action.owner_id != current_user.id and current_user.role != 'admin':
            return jsonify({
                'success': False, 
                'message': '您没有权限删除此行动记录'
            }), 403
        
        # 记录相关信息用于返回
        contact_id = action.contact_id
        company_id = action.company_id
        
        # 删除行动记录
        db.session.delete(action)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '行动记录已成功删除',
            'data': {
                'contact_id': contact_id,
                'company_id': company_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback_str = traceback.format_exc()
        print(f"删除行动记录出错: {str(e)}\n{traceback_str}")
        return jsonify({'success': False, 'message': f'服务器处理请求时出错: {str(e)}'}), 500

@customer.route('/contacts/<int:contact_id>/view')
@permission_required('customer', 'view')
def view_contact(contact_id):
    """查看联系人详情页面"""
    contact = Contact.query.get_or_404(contact_id)
    company = contact.company

    # 检查查看权限
    allowed_user_ids = current_user.get_viewable_user_ids()
    if current_user.role != 'admin' and contact.owner_id not in allowed_user_ids:
        flash('您没有权限查看此联系人信息', 'danger')
        return redirect(url_for('customer.view_company', company_id=company.id))

    # 获取该联系人的所有行动记录，按时间倒序排列
    actions = Action.query.filter_by(contact_id=contact.id).order_by(Action.created_at.desc()).all()

    # 预加载所有行动记录的所有者信息
    owner_ids = [action.owner_id for action in actions if action.owner_id]
    if owner_ids:
        owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
        for action in actions:
            if action.owner_id and action.owner_id in owners:
                action.owner = owners[action.owner_id]

    return render_template('customer/contact_view.html', contact=contact, company=company, actions=actions)

@customer.route('/<int:company_id>/add_action', methods=['GET', 'POST'])
@permission_required('customer', 'create')
def add_action_for_company(company_id):
    company = Company.query.get_or_404(company_id)
    allowed_user_ids = current_user.get_viewable_user_ids()
    if current_user.role != 'admin' and company.owner_id not in allowed_user_ids:
        flash('您没有权限为该企业添加行动记录', 'danger')
        return redirect(url_for('customer.view_company', company_id=company_id))
    contacts = Contact.query.filter_by(company_id=company_id).all()
    projects = Project.query.filter(
        or_(
            Project.end_user == company.company_name,
            Project.design_issues.like(f'%{company.company_name}%'),
            Project.contractor == company.company_name,
            Project.system_integrator == company.company_name,
            Project.dealer == company.company_name
        )
    ).all()
    selected_contact = None
    contact_actions = []
    contact_id = request.args.get('contact_id') if request.method == 'GET' else request.form.get('contact_id')
    if request.method == 'POST':
        project_id = request.form.get('project_id') or None
        communication = request.form.get('communication')
        date = request.form.get('date')
        if not contact_id or not communication or not date:
            flash('请填写所有必填项', 'danger')
        else:
            action = Action(
                date=datetime.strptime(date, '%Y-%m-%d'),
                contact_id=contact_id,
                company_id=company_id,
                project_id=project_id,
                communication=communication,
                owner_id=current_user.id
            )
            db.session.add(action)
            db.session.commit()
            flash('行动记录添加成功！', 'success')
            return redirect(url_for('customer.view_company', company_id=company_id))
    if contact_id:
        selected_contact = Contact.query.get(contact_id)
        contact_actions = Action.query.filter_by(contact_id=contact_id).order_by(Action.created_at.desc()).all()
    return render_template('customer/add_action_for_company.html', company=company, contacts=contacts, projects=projects, selected_contact=selected_contact, contact_actions=contact_actions) 