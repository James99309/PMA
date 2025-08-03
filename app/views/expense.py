from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import gettext as _
from app.models.expense import Expense, ExpenseDetail, EXPENSE_CATEGORIES, EXPENSE_STATUS
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.action import Action
from app.models.user import User
from app import db
from app.permissions import permission_required
from sqlalchemy import or_, func, desc, extract, case
from sqlalchemy.orm import joinedload
from datetime import datetime, date
import logging
import json
from app.utils.access_control import get_viewable_data, can_edit_data
from types import SimpleNamespace
import os
from werkzeug.utils import secure_filename
from app.utils.file_url_helper import normalize_file_url

logger = logging.getLogger(__name__)

def is_cloud_environment():
    """检测是否在云端环境运行"""
    render_service = os.getenv('RENDER_SERVICE_NAME')
    supabase_url = os.getenv('SUPABASE_URL')
    is_cloud = bool(render_service or supabase_url)
    
    # 添加调试日志
    current_app.logger.info(f"环境检测: RENDER_SERVICE_NAME={render_service}, SUPABASE_URL={supabase_url[:20] + '...' if supabase_url else None}, is_cloud={is_cloud}")
    
    return is_cloud

expense = Blueprint('expense', __name__)

@expense.route('/')
@login_required
@permission_required('expense', 'view')
def expense_list():
    """报销单列表 - 优化版本"""
    # 获取筛选参数
    search = request.args.get('search', '').strip()
    customer_id = request.args.get('customer_id', '')
    owner_id = request.args.get('owner_id', '')
    expense_category = request.args.get('expense_category', '')
    status = request.args.get('status', '')
    
    # 1. 使用权限控制函数获取可查看的报销单数据
    from app.utils.access_control import get_viewable_data
    
    # 获取基本的报销单信息，应用权限过滤
    base_query = get_viewable_data(Expense, current_user).with_entities(
        Expense.id,
        Expense.expense_number,
        Expense.title,
        Expense.total_amount,
        Expense.currency,
        Expense.status,
        Expense.created_at,
        Expense.customer_id,
        Expense.project_id,
        Expense.owner_id
    )
    
    # 2. 在JOIN之前先应用非搜索筛选条件（减少数据量）
    if customer_id:
        base_query = base_query.filter(Expense.customer_id == customer_id)
    if owner_id:
        base_query = base_query.filter(Expense.owner_id == owner_id)
    if status:
        base_query = base_query.filter(Expense.status == status)
    
    # 3. 只在需要搜索时才JOIN相关表
    if search:
        # 有搜索条件时才JOIN
        search_query = base_query.join(Company, Expense.customer_id == Company.id)\
                                .outerjoin(Project, Expense.project_id == Project.id)\
                                .filter(
                                    or_(
                                        Expense.expense_number.ilike(f'%{search}%'),
                                        Expense.title.ilike(f'%{search}%'),
                                        Company.company_name.ilike(f'%{search}%')
                                    )
                                )
        expenses = search_query.order_by(desc(Expense.created_at)).all()
    else:
        # 无搜索条件时直接查询，避免不必要的JOIN
        expenses = base_query.order_by(desc(Expense.created_at)).all()
    
    # 4. 批量获取关联数据（避免N+1查询）
    if expenses:
        # 收集所有需要的ID
        customer_ids = list(set(e.customer_id for e in expenses if e.customer_id))
        project_ids = list(set(e.project_id for e in expenses if e.project_id))
        owner_ids = list(set(e.owner_id for e in expenses if e.owner_id))
        expense_ids = [e.id for e in expenses]
        
        # 批量查询关联数据
        customers = {c.id: c.company_name for c in 
                    Company.query.filter(Company.id.in_(customer_ids)).all()} if customer_ids else {}
        
        projects = {p.id: p.project_name for p in 
                   Project.query.filter(Project.id.in_(project_ids)).all()} if project_ids else {}
        
        owners = {u.id: u for u in 
                 User.query.filter(User.id.in_(owner_ids)).all()} if owner_ids else {}
        
        # 批量查询detail_count（使用子查询优化）
        detail_counts = dict(
            db.session.query(
                ExpenseDetail.expense_id,
                func.count(ExpenseDetail.id)
            ).filter(ExpenseDetail.expense_id.in_(expense_ids))
            .group_by(ExpenseDetail.expense_id).all()
        )
    else:
        customers = {}
        projects = {}
        owners = {}
        detail_counts = {}
    
    # 5. 格式化数据
    formatted_expenses = []
    for expense in expenses:
        # 获取User对象
        user_obj = owners.get(expense.owner_id)
        owner_display = ""
        if user_obj:
            if hasattr(user_obj, 'real_name') and user_obj.real_name:
                owner_display = user_obj.real_name
            elif hasattr(user_obj, 'username'):
                owner_display = user_obj.username
            else:
                owner_display = str(user_obj)
        
        formatted_row = SimpleNamespace(
            id=expense.id,
            expense_number=expense.expense_number,
            title=expense.title,
            total_amount=expense.total_amount,
            currency=expense.currency,
            status=expense.status,
            created_at=expense.created_at,
            customer_name=customers.get(expense.customer_id, '未指定'),
            project_name=projects.get(expense.project_id, '-'),
            owner=owner_display,
            owner_obj=user_obj,
            detail_count=detail_counts.get(expense.id, 0)
        )
        formatted_expenses.append(formatted_row)
    
    # 6. 优化统计查询：使用权限过滤的查询获取所有统计数据
    stats_query = get_viewable_data(Expense, current_user)
    
    # 如果有搜索条件，应用相同的搜索过滤到统计查询
    if search:
        stats_query = stats_query.join(Company, Expense.customer_id == Company.id)\
                                .outerjoin(Project, Expense.project_id == Project.id)\
                                .filter(
                                    or_(
                                        Expense.expense_number.ilike(f'%{search}%'),
                                        Expense.title.ilike(f'%{search}%'),
                                        Company.company_name.ilike(f'%{search}%')
                                    )
                                )
    
    # 应用其他筛选条件到统计查询
    if customer_id:
        stats_query = stats_query.filter(Expense.customer_id == customer_id)
    if owner_id:
        stats_query = stats_query.filter(Expense.owner_id == owner_id)
    if status:
        stats_query = stats_query.filter(Expense.status == status)
    
    # 使用单个查询获取所有统计数据（避免多次查询）
    stats_result = stats_query.with_entities(
        func.count(Expense.id).label('total_count'),
        func.coalesce(func.sum(Expense.total_amount), 0).label('total_amount'),
        func.sum(case(
            (Expense.status == 'pending', 1),
            else_=0
        )).label('pending_count'),
        func.sum(case(
            (Expense.status == 'pending', Expense.total_amount),
            else_=0
        )).label('pending_amount'),
        func.sum(case(
            (Expense.status == 'approved', 1),
            else_=0
        )).label('approved_count'),
        func.sum(case(
            (Expense.status == 'approved', Expense.total_amount),
            else_=0
        )).label('approved_amount')
    ).first()
    
    total_count = stats_result.total_count or 0
    total_amount = stats_result.total_amount or 0
    pending_count = stats_result.pending_count or 0
    pending_amount = stats_result.pending_amount or 0
    approved_count = stats_result.approved_count or 0
    approved_amount = stats_result.approved_amount or 0
    
    # 获取筛选选项数据 - 基于当前列表实际数据生成筛选选项
    # 1. 获取实际存在的申请人ID（基于权限过滤的报销单数据）
    unique_owner_ids_query = get_viewable_data(Expense, current_user)\
        .filter(Expense.owner_id.isnot(None))\
        .with_entities(Expense.owner_id.distinct())
    
    unique_owner_ids = {row[0] for row in unique_owner_ids_query.all()}
    
    # 只查询需要的用户，避免加载所有用户
    users = User.query.filter(
        User.id.in_(unique_owner_ids),
        User.is_active == True
    ).order_by(User.real_name, User.username).all() if unique_owner_ids else []
    
    # 2. 获取实际存在的客户ID（基于权限过滤的报销单数据）
    unique_customer_ids_query = get_viewable_data(Expense, current_user)\
        .filter(Expense.customer_id.isnot(None))\
        .with_entities(Expense.customer_id.distinct())
    
    unique_customer_ids = {row[0] for row in unique_customer_ids_query.all()}
    
    # 只查询需要的客户，确保不包含已删除的客户
    customers = Company.query.filter(
        Company.id.in_(unique_customer_ids),
        Company.is_deleted == False
    ).order_by(Company.company_name).all() if unique_customer_ids else []
    
    # 3. 获取实际存在的审批状态（基于权限过滤的报销单数据）
    unique_status_query = get_viewable_data(Expense, current_user)\
        .filter(Expense.status.isnot(None))\
        .filter(Expense.status != '')\
        .with_entities(Expense.status.distinct())
    
    unique_statuses = {row[0] for row in unique_status_query.all()}
    
    # 基于实际存在的状态构建状态选项
    status_options = []
    for status_key, status_label in EXPENSE_STATUS:
        if status_key in unique_statuses:
            status_options.append({
                'value': status_key,
                'label': status_label,
                'translate': True
            })
    
    # 按状态重要性排序（草稿、待审批、已通过、已拒绝）
    status_order = {'draft': 1, 'pending': 2, 'approved': 3, 'rejected': 4}
    status_options.sort(key=lambda x: status_order.get(x['value'], 999))
    
    # 构建筛选配置
    filter_config = {
        'action_url': url_for('expense.expense_list'),
        'form_id': 'expenseFilterForm',
        'reset_url': url_for('expense.expense_list'),
        'search_field': {
            'name': 'search',
            'label': '搜索',
            'placeholder': '报销单号、标题或客户名称',
            'value': search,
            'col_width': 4
        },
        'filter_fields': [
            {
                'name': 'customer_id',
                'label': '客户',
                'all_option_text': '全部客户',
                'current_value': customer_id,
                'col_width': 2,
                'options': [{'value': str(c.id), 'label': c.company_name, 'translate': False} for c in customers]
            },
            {
                'name': 'owner_id',
                'label': '申请人',
                'all_option_text': '全部申请人',
                'current_value': owner_id,
                'col_width': 2,
                'options': [{'value': str(u.id), 'label': u.real_name or u.username, 'translate': False} for u in users]
            },
            # 移除报销科目筛选，因为现在在明细表中，可以考虑后续通过明细表联查实现
            {
                'name': 'status',
                'label': '审批状态',
                'all_option_text': '全部状态',
                'current_value': status,
                'col_width': 2,
                'options': status_options
            }
        ],
        'search_button_text': '搜索',
        'reset_button_text': '重置'
    }
    
    # 使用通用列表组件配置
    list_config = {
        'module_name': 'expense',
        'title': '报销管理',
        'ajax_mode': True,
        
        # 统计卡片配置
        'stats': {
            'cards': [
                {
                    'id': 'total',
                    'title': '全部报销',
                    'icon': 'fas fa-receipt',
                    'value': total_count,
                    'amount': total_amount / 10000,
                    'unit': '单',
                    'amount_unit': '万元',
                    'color': 'primary',
                    'clickable': True,
                    'click_params': {}
                },
                {
                    'id': 'pending',
                    'title': '待审批',
                    'icon': 'fas fa-clock',
                    'value': pending_count,
                    'amount': pending_amount / 10000,
                    'unit': '单',
                    'amount_unit': '万元',
                    'color': 'warning',
                    'clickable': True,
                    'click_params': {'status': 'pending'}
                },
                {
                    'id': 'approved',
                    'title': '已通过',
                    'icon': 'fas fa-check-circle',
                    'value': approved_count,
                    'amount': approved_amount / 10000,
                    'unit': '单',
                    'amount_unit': '万元',
                    'color': 'success',
                    'clickable': True,
                    'click_params': {'status': 'approved'}
                }
            ]
        },
        
        # 筛选配置
        'filter': filter_config,
        
        # 表格配置
        'table': {
            'ajax_target': 'expenseTableBody',
            'title': '报销列表',
            'icon': 'fas fa-table',
            'columns': [
                {
                    'key': 'expense_number',
                    'label': '报销单号',
                    'type': 'link',
                    'url_template': '/expense/{id}',
                    'render': 'render_expense_number',
                    'width': '140px'
                },
                {
                    'key': 'title',
                    'label': '报销标题',
                    'type': 'text',
                    'width': '200px'
                },
                {
                    'key': 'customer_name',
                    'label': '客户',
                    'type': 'text',
                    'width': '150px'
                },
                {
                    'key': 'project_name',
                    'label': '项目',
                    'type': 'text',
                    'width': '150px'
                },
                {
                    'key': 'detail_count',
                    'label': '明细数量',
                    'type': 'text',
                    'width': '80px'
                },
                {
                    'key': 'total_amount',
                    'label': '总金额',
                    'type': 'number',
                    'format': 'currency',
                    'align': 'end',
                    'width': '100px'
                },
                {
                    'key': 'status',
                    'label': '状态',
                    'type': 'badge',
                    'render': 'render_expense_status_badge',
                    'align': 'start',
                    'width': '100px'
                },
                {
                    'key': 'owner',
                    'label': '申请人',
                    'type': 'text',
                    'align': 'start',
                    'width': '100px'
                },
                {
                    'key': 'created_at',
                    'label': '创建时间',
                    'type': 'date',
                    'format': '%Y-%m-%d',
                    'width': '120px'
                }
            ]
        }
    }
    
    return render_template('expense/expense_list.html', 
                         list_config=list_config,
                         expenses=formatted_expenses)

@expense.route('/ajax/test')
def test_ajax():
    """测试AJAX端点"""
    return jsonify({'status': 'ok', 'message': 'AJAX端点工作正常'})

@expense.route('/ajax')
@login_required
@permission_required('expense', 'view')
def expense_list_ajax():
    """报销列表AJAX端点 - 优化版本"""
    try:
        logger.info(f"AJAX请求开始，参数: {dict(request.args)}")
        
        # 获取筛选参数
        search = request.args.get('search', '').strip()
        customer_id = request.args.get('customer_id', '')
        owner_id = request.args.get('owner_id', '')
        status = request.args.get('status', '')
        
        # 分页参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # 1. 使用权限控制函数获取可查看的报销单数据
        from app.utils.access_control import get_viewable_data
        
        # 获取基本的报销单信息，应用权限过滤
        base_query = get_viewable_data(Expense, current_user).with_entities(
            Expense.id,
            Expense.expense_number,
            Expense.title,
            Expense.total_amount,
            Expense.currency,
            Expense.status,
            Expense.created_at,
            Expense.customer_id,
            Expense.project_id,
            Expense.owner_id
        )
        
        # 2. 在JOIN之前先应用非搜索筛选条件
        if customer_id:
            base_query = base_query.filter(Expense.customer_id == customer_id)
        if owner_id:
            base_query = base_query.filter(Expense.owner_id == owner_id)
        if status:
            base_query = base_query.filter(Expense.status == status)
        
        # 3. 只在需要搜索时才JOIN相关表
        if search:
            search_query = base_query.join(Company, Expense.customer_id == Company.id)\
                                    .outerjoin(Project, Expense.project_id == Project.id)\
                                    .filter(
                                        or_(
                                            Expense.expense_number.ilike(f'%{search}%'),
                                            Expense.title.ilike(f'%{search}%'),
                                            Company.company_name.ilike(f'%{search}%')
                                        )
                                    )
            # 获取总数和分页数据
            total_count = search_query.count()
            expenses = search_query.order_by(desc(Expense.created_at))\
                                   .offset(offset)\
                                   .limit(limit)\
                                   .all()
        else:
            # 无搜索条件时直接查询
            total_count = base_query.count()
            expenses = base_query.order_by(desc(Expense.created_at))\
                                 .offset(offset)\
                                 .limit(limit)\
                                 .all()
        
        # 4. 批量获取关联数据（避免N+1查询）
        if expenses:
            customer_ids = list(set(e.customer_id for e in expenses if e.customer_id))
            project_ids = list(set(e.project_id for e in expenses if e.project_id))
            owner_ids = list(set(e.owner_id for e in expenses if e.owner_id))
            expense_ids = [e.id for e in expenses]
            
            # 批量查询关联数据
            customers = {c.id: c.company_name for c in 
                        Company.query.filter(Company.id.in_(customer_ids)).all()} if customer_ids else {}
            
            projects = {p.id: p.project_name for p in 
                       Project.query.filter(Project.id.in_(project_ids)).all()} if project_ids else {}
            
            owners = {u.id: u for u in 
                     User.query.filter(User.id.in_(owner_ids)).all()} if owner_ids else {}
            
            # 批量查询detail_count
            detail_counts = dict(
                db.session.query(
                    ExpenseDetail.expense_id,
                    func.count(ExpenseDetail.id)
                ).filter(ExpenseDetail.expense_id.in_(expense_ids))
                .group_by(ExpenseDetail.expense_id).all()
            )
        else:
            customers = {}
            projects = {}
            owners = {}
            detail_counts = {}
        
        # 5. 格式化数据并渲染HTML
        html_rows = []
        for expense in expenses:
            user_obj = owners.get(expense.owner_id)
            owner_display = ""
            if user_obj:
                if hasattr(user_obj, 'real_name') and user_obj.real_name:
                    owner_display = user_obj.real_name
                elif hasattr(user_obj, 'username'):
                    owner_display = user_obj.username
                else:
                    owner_display = str(user_obj)
            
            formatted_row = SimpleNamespace(
                id=expense.id,
                expense_number=expense.expense_number,
                title=expense.title,
                total_amount=expense.total_amount,
                currency=expense.currency,
                status=expense.status,
                created_at=expense.created_at,
                customer_name=customers.get(expense.customer_id, '未指定'),
                project_name=projects.get(expense.project_id, '-'),
                owner=owner_display,
                owner_obj=user_obj,
                detail_count=detail_counts.get(expense.id, 0)
            )
            
            html_row = render_template('expense/expense_rows.html', expense=formatted_row)
            html_rows.append(html_row)
        
        # 6. 优化统计查询：使用权限过滤的查询获取所有统计数据
        stats_query = get_viewable_data(Expense, current_user)
        
        # 应用相同的筛选条件到统计查询
        if search:
            stats_query = stats_query.join(Company, Expense.customer_id == Company.id)\
                                    .outerjoin(Project, Expense.project_id == Project.id)\
                                    .filter(
                                        or_(
                                            Expense.expense_number.ilike(f'%{search}%'),
                                            Expense.title.ilike(f'%{search}%'),
                                            Company.company_name.ilike(f'%{search}%')
                                        )
                                    )
        if customer_id:
            stats_query = stats_query.filter(Expense.customer_id == customer_id)
        if owner_id:
            stats_query = stats_query.filter(Expense.owner_id == owner_id)
        if status:
            stats_query = stats_query.filter(Expense.status == status)
        
        # 使用单个查询获取所有统计数据
        stats_result = stats_query.with_entities(
            func.count(Expense.id).label('total_stats_count'),
            func.coalesce(func.sum(Expense.total_amount), 0).label('total_stats_amount'),
            func.sum(case(
                (Expense.status == 'pending', 1),
                else_=0
            )).label('pending_stats_count'),
            func.sum(case(
                (Expense.status == 'pending', Expense.total_amount),
                else_=0
            )).label('pending_stats_amount'),
            func.sum(case(
                (Expense.status == 'approved', 1),
                else_=0
            )).label('approved_stats_count'),
            func.sum(case(
                (Expense.status == 'approved', Expense.total_amount),
                else_=0
            )).label('approved_stats_amount')
        ).first()
        
        statistics = {
            'total_count': stats_result.total_stats_count or 0,
            'total_amount': (stats_result.total_stats_amount or 0) / 10000,
            'pending_count': stats_result.pending_stats_count or 0,
            'pending_amount': (stats_result.pending_stats_amount or 0) / 10000,
            'approved_count': stats_result.approved_stats_count or 0,
            'approved_amount': (stats_result.approved_stats_amount or 0) / 10000
        }
        
        return jsonify({
            'success': True,
            'html': '\n'.join(html_rows),
            'total_count': total_count,
            'loaded_count': len(expenses),
            'statistics': statistics
        })
    
    except Exception as e:
        import traceback
        logger.error(f"报销列表AJAX请求失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'html': '<tr><td colspan="9" class="text-center text-danger">数据加载失败</td></tr>'
        }), 500

@expense.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('expense', 'create')
def create_expense():
    """创建报销单"""
    if request.method == 'POST':
        try:
            # 获取主表表单数据
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            customer_id = request.form.get('customer_id', type=int)
            contact_id = request.form.get('contact_id', type=int)
            project_id = request.form.get('project_id', type=int) or None
            expense_currency = request.form.get('currency', 'CNY').strip()  # 报销单主货币
            logger.info(f"用户选择的报销单主货币: {expense_currency}")
            
            # 数据验证
            if not all([customer_id, contact_id]):
                flash('请填写所有必填字段（客户和联系人）', 'error')
                return redirect(url_for('expense.create_expense'))
            
            # 获取报销明细数据 - 支持两种数据格式
            detail_data = {}
            
            # 方式1：尝试从 expense_details 隐藏字段获取JSON数据
            expense_details_json = request.form.get('expense_details')
            if expense_details_json:
                try:
                    import json
                    detail_list = json.loads(expense_details_json)
                    for index, detail in enumerate(detail_list):
                        detail_data[index] = detail
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # 方式2：从 details[index][field] 格式的表单字段获取
            if not detail_data:
                for key, value in request.form.items():
                    if key.startswith('details[') and '][' in key:
                        # 解析 details[index][field] 格式
                        try:
                            index_end = key.find('][')
                            index = int(key[8:index_end])  # 提取索引
                            field = key[index_end+2:-1]    # 提取字段名
                            
                            if index not in detail_data:
                                detail_data[index] = {}
                            detail_data[index][field] = value
                        except (ValueError, IndexError):
                            continue
            
            # 方式3：处理AJAX FormData提交的文件数据
            file_data = {}
            for key in request.files.keys():
                if key.startswith('details[') and '][invoice_files][' in key:
                    # 解析 details[index][invoice_files][fileIndex] 格式
                    try:
                        # 例如: details[0][invoice_files][0]
                        parts = key.split('][')
                        index = int(parts[0][8:])  # 提取明细索引
                        file_index = int(parts[2][:-1])  # 提取文件索引
                        
                        if index not in file_data:
                            file_data[index] = {}
                        if 'files' not in file_data[index]:
                            file_data[index]['files'] = {}
                        
                        file_data[index]['files'][file_index] = request.files[key]
                    except (ValueError, IndexError):
                        continue
            
            # 处理文件元数据
            for key, value in request.form.items():
                if key.startswith('details[') and '][invoice_meta][' in key:
                    try:
                        # 例如: details[0][invoice_meta][0][filename]
                        parts = key.split('][')
                        index = int(parts[0][8:])
                        file_index = int(parts[2])
                        meta_field = parts[3][:-1]  # filename 或 size
                        
                        if index not in file_data:
                            file_data[index] = {}
                        if 'meta' not in file_data[index]:
                            file_data[index]['meta'] = {}
                        if file_index not in file_data[index]['meta']:
                            file_data[index]['meta'][file_index] = {}
                        
                        file_data[index]['meta'][file_index][meta_field] = value
                    except (ValueError, IndexError):
                        continue
            
            # 验证明细数据
            if not detail_data:
                flash('请至少添加一条报销明细', 'error')
                return redirect(url_for('expense.create_expense'))
            
            # 验证明细数据完整性
            detail_items = []
            total_amount = 0.0
            
            for index in sorted(detail_data.keys()):
                detail = detail_data[index]
                try:
                    # 检查必填字段 - 更新为新的字段名
                    required_fields = ['expense_category', 'expense_date', 'description', 'invoice_amount', 'currency']
                    for field in required_fields:
                        if not detail.get(field) or not str(detail[field]).strip():
                            flash(f'第{index+1}个明细项目的{field}字段为必填项', 'error')
                            return redirect(url_for('expense.create_expense'))
                    
                    # 转换数据类型
                    expense_date = datetime.strptime(detail['expense_date'], '%Y-%m-%d').date()
                    invoice_amount = float(detail['invoice_amount'])
                    current_amount = float(detail.get('current_amount', invoice_amount))  # 如果没有转换金额，使用发票金额
                    
                    # 确保amount字段也有值（向后兼容）
                    amount = float(detail.get('amount', current_amount))  # 优先使用amount，否则使用current_amount
                    
                    # 处理汇率字段
                    exchange_rate = float(detail.get('exchange_rate', 1.0))  # 获取前端传递的汇率
                    
                    # 如果没有汇率信息，尝试根据金额计算
                    if exchange_rate == 1.0 and invoice_amount > 0 and current_amount != invoice_amount:
                        exchange_rate = current_amount / invoice_amount
                        logger.info(f"明细{index}计算汇率: {current_amount} / {invoice_amount} = {exchange_rate}")
                    
                    # 调试日志
                    logger.info(f"明细{index}数据处理: invoice_amount={invoice_amount}, current_amount={current_amount}, amount={amount}, exchange_rate={exchange_rate}")
                    logger.info(f"原始表单数据: {dict(detail)}")
                    
                    detail_currency = detail['currency']  # 明细的发票货币
                    document_count = int(detail.get('document_count', 1)) if detail.get('document_count') else 1
                    
                    if invoice_amount <= 0:
                        flash(f'第{index+1}个明细项目的发票金额必须大于0', 'error')
                        return redirect(url_for('expense.create_expense'))
                    
                    # 确保amount字段不为null或0
                    if amount is None or amount <= 0:
                        logger.warning(f"明细{index}的amount字段异常: {amount}, 使用invoice_amount: {invoice_amount}")
                        amount = invoice_amount
                    
                    # 处理发票图片数据
                    invoice_images = detail.get('invoice_images', [])
                    if isinstance(invoice_images, str):
                        # 如果是字符串，尝试解析为JSON
                        try:
                            import json
                            invoice_images = json.loads(invoice_images)
                        except (json.JSONDecodeError, ValueError):
                            invoice_images = []
                    
                    detail_items.append({
                        'expense_date': expense_date,
                        'expense_category': detail['expense_category'],
                        'description': detail['description'].strip(),
                        'document_count': document_count,
                        'currency': detail_currency,  # 使用明细的发票货币
                        'invoice_amount': invoice_amount,
                        'current_amount': current_amount,
                        'amount': amount,  # 确保包含amount字段
                        'exchange_rate': exchange_rate,  # 添加汇率字段
                        'invoice_images': invoice_images
                    })
                    
                    total_amount += current_amount  # 使用转换后的金额计算总额
                    
                except (ValueError, KeyError) as e:
                    flash(f'第{index+1}个明细项目数据格式错误: {str(e)}', 'error')
                    return redirect(url_for('expense.create_expense'))
            
            # 如果没有填写报销主题，则自动生成
            if not title:
                # 获取客户信息
                customer = Company.query.get(customer_id)
                customer_name = customer.company_name if customer else '未知客户'
                
                # 获取当前用户账户
                current_user_account = current_user.username if current_user else ''
                
                # 生成时间戳 YYDDHHS（年年月月日日时时秒秒）
                now = datetime.now()
                time_str = now.strftime('%y%m%d%H%S')
                
                # 生成报销主题：客户名称-用户账户-YYDDHHS
                title = f"{customer_name}-{current_user_account}-{time_str}"
            
            # 创建报销单（主表）
            expense_obj = Expense(
                title=title,
                description=description,
                customer_id=customer_id,
                contact_id=contact_id,
                project_id=project_id,
                currency=expense_currency,  # 使用报销单主货币
                owner_id=current_user.id,
                total_amount=total_amount  # 根据明细计算总金额
            )
            
            db.session.add(expense_obj)
            db.session.flush()  # 获取主表ID
            
            # 创建报销明细
            for index, detail_data in enumerate(detail_items):
                # 先创建明细对象（不包含发票数据）
                detail_obj = ExpenseDetail(
                    expense_id=expense_obj.id,
                    expense_date=detail_data['expense_date'],
                    expense_category=detail_data['expense_category'],
                    description=detail_data['description'],
                    document_count=detail_data['document_count'],
                    currency=detail_data['currency'],
                    invoice_amount=detail_data['invoice_amount'],
                    current_amount=detail_data['current_amount'],
                    amount=detail_data['amount'],  # 使用处理后的amount字段
                    exchange_rate=detail_data['exchange_rate'],  # 添加汇率字段
                    invoice_images=None  # 先不设置发票数据
                )
                db.session.add(detail_obj)
                db.session.flush()  # 获取明细ID
                
                # 处理发票图片数据
                processed_images = []
                
                # 处理新上传的文件（AJAX FormData方式）
                if index in file_data and 'files' in file_data[index]:
                    for file_index, file_obj in file_data[index]['files'].items():
                        if file_obj and file_obj.filename:
                            try:
                                # 验证文件类型
                                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                                file_ext = file_obj.filename.rsplit('.', 1)[1].lower() if '.' in file_obj.filename else ''
                                if file_ext not in allowed_extensions:
                                    current_app.logger.warning(f"不支持的文件类型: {file_obj.filename}")
                                    continue
                                
                                # 检查文件大小 (最大5MB)
                                file_obj.seek(0, 2)
                                file_size = file_obj.tell()
                                file_obj.seek(0)
                                
                                max_size = 5 * 1024 * 1024  # 5MB
                                if file_size > max_size:
                                    current_app.logger.warning(f"文件过大: {file_obj.filename} ({file_size} bytes)")
                                    continue
                                
                                # 检测运行环境 - 优先判断是否在云端部署
                                current_app.logger.info(f"开始处理文件上传: {file_obj.filename}, 大小: {file_size} bytes")
                                cloud_env = is_cloud_environment()
                                current_app.logger.info(f"环境检测结果: 云端环境={cloud_env}")
                                if cloud_env:
                                    # 云端环境，使用Supabase存储
                                    try:
                                        from app.utils.supabase_client import get_supabase_client
                                        supabase_client = get_supabase_client()
                                        
                                        # 生成文件名
                                        import uuid
                                        filename = f"expense_invoice_{detail_obj.id}_{uuid.uuid4().hex[:8]}.{file_ext}"
                                        
                                        # 上传到Supabase
                                        image_url = supabase_client.upload_expense_invoice(detail_obj.id, file_obj, filename)
                                        
                                        if not image_url:
                                            raise Exception("Supabase上传失败")
                                            
                                        current_app.logger.info(f"发票文件上传到Supabase成功: {image_url}")
                                        
                                    except Exception as supabase_error:
                                        current_app.logger.error(f"云端Supabase上传失败: {str(supabase_error)}")
                                        # 云端上传失败，跳过这个文件
                                        continue
                                else:
                                    # 本地环境，使用本地文件系统
                                    import os
                                    import uuid
                                    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'invoices', str(detail_obj.id))
                                    os.makedirs(upload_dir, exist_ok=True)
                                    
                                    # 生成文件名
                                    filename = f"invoice_{uuid.uuid4().hex[:8]}.{file_ext}"
                                    file_path = os.path.join(upload_dir, filename)
                                    
                                    # 保存文件
                                    file_obj.save(file_path)
                                    
                                    # 生成URL
                                    relative_path = os.path.join('uploads', 'invoices', str(detail_obj.id), filename).replace('\\', '/')
                                    raw_url = f"/static/{relative_path}"
                                    image_url = normalize_file_url(raw_url, 'invoice_image')
                                
                                # 获取原始文件名（如果有元数据）
                                original_filename = file_obj.filename
                                if index in file_data and 'meta' in file_data[index] and file_index in file_data[index]['meta']:
                                    original_filename = file_data[index]['meta'][file_index].get('filename', file_obj.filename)
                                
                                # 添加到处理后的图片列表
                                processed_images.append({
                                    'filename': original_filename,
                                    'url': image_url,
                                    'size': file_size
                                })
                                
                                current_app.logger.info(f"发票文件上传成功: {image_url}")
                                
                            except Exception as e:
                                current_app.logger.error(f"上传发票文件失败: {str(e)}")
                                continue
                
                # 处理已有的发票数据（JSON格式）
                if detail_data.get('invoice_images'):
                    for invoice in detail_data['invoice_images']:
                        if not invoice.get('pending') and (invoice.get('url') or invoice.get('path')):
                            processed_images.append(invoice)
                
                # 更新明细的发票数据
                if processed_images:
                    import json
                    detail_obj.invoice_images = json.dumps(processed_images)
            
            # 确保用户选择的货币不被覆盖
            if expense_obj.currency != expense_currency:
                logger.warning(f"创建时检测到货币被意外修改: {expense_obj.currency} -> {expense_currency}，正在恢复")
                expense_obj.currency = expense_currency
            
            db.session.commit()
            logger.info(f"报销单创建完成，最终货币: {expense_obj.currency}")
            
            # 检查是否是AJAX请求
            if request.headers.get('Content-Type', '').startswith('multipart/form-data'):
                # AJAX请求，返回JSON响应
                return jsonify({
                    'success': True,
                    'message': f'报销单创建成功，共添加 {len(detail_items)} 条明细，总金额 ¥{total_amount:.2f}',
                    'redirect_url': url_for('expense.expense_detail', id=expense_obj.id),
                    'expense_id': expense_obj.id,
                    'expense_number': expense_obj.expense_number
                })
            else:
                # 传统表单提交
                flash(f'报销单创建成功，共添加 {len(detail_items)} 条明细，总金额 ¥{total_amount:.2f}', 'success')
                return redirect(url_for('expense.expense_detail', id=expense_obj.id))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"创建报销单失败: {e}")
            logger.error(f"详细错误信息: {error_details}")
            logger.error(f"表单数据: {dict(request.form)}")
            
            # 详细错误日志
            logger.error(f"创建报销单详细调试信息:")
            logger.error(f"- 标题: {title}")
            logger.error(f"- 客户ID: {customer_id}")
            logger.error(f"- 项目ID: {project_id}")
            logger.error(f"- 用户ID: {current_user.id}")
            logger.error(f"- 明细数量: {len(detail_items) if 'detail_items' in locals() else 'undefined'}")
            logger.error(f"- 总金额: {total_amount if 'total_amount' in locals() else 'undefined'}")
            
            if 'detail_items' in locals():
                for idx, item in enumerate(detail_items):
                    logger.error(f"- 明细{idx+1}: {item}")
            
            # 检查是否是AJAX请求
            if request.headers.get('Content-Type', '').startswith('multipart/form-data'):
                # AJAX请求，返回JSON错误响应
                return jsonify({
                    'success': False,
                    'message': f'创建报销单失败: {str(e)}'
                }), 500
            else:
                # 传统表单提交
                flash(f'创建报销单失败: {str(e)}', 'error')
    
    # GET请求，显示创建表单
    return render_template('expense/create_expense.html')

@expense.route('/<int:id>')
@login_required
@permission_required('expense', 'view')
def expense_detail(id):
    """报销单详情"""
    expense_obj = Expense.query.options(
        db.joinedload(Expense.customer),
        db.joinedload(Expense.project),
        db.joinedload(Expense.owner),
        db.joinedload(Expense.approver),
        db.joinedload(Expense.details)
        # 移除action和department关联加载，因为已从模型中删除
    ).get_or_404(id)
    
    # 检查访问权限
    if not can_edit_data(expense_obj, current_user):
        flash('您没有权限查看此报销单', 'error')
        return redirect(url_for('expense.expense_list'))
    
    return render_template('expense/expense_detail.html', expense=expense_obj)

@expense.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('expense', 'edit')
def edit_expense(id):
    """编辑报销单"""
    expense_obj = Expense.query.options(
        db.joinedload(Expense.customer),
        db.joinedload(Expense.project),
        db.joinedload(Expense.owner)
        # 移除action和department关联加载，因为已从模型中删除
    ).get_or_404(id)
    
    # 检查编辑权限
    if not can_edit_data(expense_obj, current_user):
        flash('您没有权限编辑此报销单', 'error')
        return redirect(url_for('expense.expense_detail', id=id))
    
    # 已审批的报销单不能编辑
    if expense_obj.status not in ['draft', 'pending']:
        flash('已审批的报销单不能编辑', 'error')
        return redirect(url_for('expense.expense_detail', id=id))
    
    if request.method == 'POST':
        try:
            # 调试：记录接收到的基本表单数据
            logger.info(f"编辑报销单 {id} - 接收到的基本数据:")
            logger.info(f"title: {request.form.get('title')}")
            logger.info(f"customer_id: {request.form.get('customer_id')}")
            logger.info(f"contact_id: {request.form.get('contact_id')}")
            logger.info(f"project_id: {request.form.get('project_id')}")
            logger.info(f"currency: {request.form.get('currency')}")
            
            # 更新报销单主表信息
            title = request.form.get('title', '').strip()
            if not title:
                return jsonify({'success': False, 'message': '报销主题不能为空'}), 400
                
            customer_id = request.form.get('customer_id', type=int)
            if not customer_id:
                return jsonify({'success': False, 'message': '请选择关联客户'}), 400
                
            contact_id = request.form.get('contact_id', type=int)
            if not contact_id:
                return jsonify({'success': False, 'message': '请选择联系人'}), 400
            
            expense_obj.title = title
            expense_obj.description = request.form.get('description', '').strip()
            expense_obj.customer_id = customer_id
            expense_obj.contact_id = contact_id
            expense_obj.project_id = request.form.get('project_id', type=int) or None
            
            # 保存用户明确选择的货币，确保不被后续逻辑覆盖
            user_selected_currency = request.form.get('currency', 'CNY')
            expense_obj.currency = user_selected_currency
            logger.info(f"用户选择的报销单货币: {user_selected_currency}")
            
            # 处理明细数据（复用创建报销单的逻辑）
            detail_data = {}
            
            # 解析明细数据
            for key, value in request.form.items():
                if key.startswith('details[') and '][' in key:
                    try:
                        index_end = key.find('][')
                        index = int(key[8:index_end])
                        field = key[index_end+2:-1]
                        
                        if index not in detail_data:
                            detail_data[index] = {}
                        detail_data[index][field] = value
                    except (ValueError, IndexError):
                        continue
            
            # 处理AJAX FormData提交的文件数据（与创建报销单保持一致）
            file_data = {}
            for key in request.files.keys():
                if key.startswith('details[') and '][invoice_files][' in key:
                    # 解析 details[index][invoice_files][fileIndex] 格式
                    try:
                        # 例如: details[0][invoice_files][0]
                        parts = key.split('][')
                        index = int(parts[0][8:])  # 提取明细索引
                        file_index = int(parts[2][:-1])  # 提取文件索引
                        
                        if index not in file_data:
                            file_data[index] = {}
                        if 'files' not in file_data[index]:
                            file_data[index]['files'] = {}
                        
                        file_data[index]['files'][file_index] = request.files[key]
                    except (ValueError, IndexError):
                        continue
            
            # 处理文件元数据
            for key, value in request.form.items():
                if key.startswith('details[') and '][invoice_meta][' in key:
                    try:
                        # 例如: details[0][invoice_meta][0][filename]
                        parts = key.split('][')
                        index = int(parts[0][8:])
                        file_index = int(parts[2])
                        meta_field = parts[3][:-1]  # filename 或 size
                        
                        if index not in file_data:
                            file_data[index] = {}
                        if 'meta' not in file_data[index]:
                            file_data[index]['meta'] = {}
                        if file_index not in file_data[index]['meta']:
                            file_data[index]['meta'][file_index] = {}
                        
                        file_data[index]['meta'][file_index][meta_field] = value
                    except (ValueError, IndexError):
                        continue
            
            # 调试：记录解析的明细数据
            logger.info(f"解析到 {len(detail_data)} 条明细数据")
            logger.info(f"解析到 {len(file_data)} 组文件数据")
            for idx, data in detail_data.items():
                logger.info(f"明细 {idx}: {data}")
            for idx, files in file_data.items():
                logger.info(f"文件 {idx}: files={len(files.get('files', {}))}, meta={len(files.get('meta', {}))}")
            
            # 验证至少有一条明细
            if not detail_data:
                return jsonify({'success': False, 'message': '请至少保留一条报销明细'}), 400
            
            # 删除所有现有明细
            existing_details = ExpenseDetail.query.filter_by(expense_id=expense_obj.id).all()
            for detail in existing_details:
                db.session.delete(detail)
            db.session.flush()  # 确保删除操作被执行
            
            # 重新创建明细
            total_amount = 0.0
            for index in sorted(detail_data.keys()):
                detail = detail_data[index]
                
                # 验证必填字段
                required_fields = ['expense_category', 'expense_date', 'description', 'invoice_amount', 'currency']
                for field in required_fields:
                    if not detail.get(field) or not str(detail[field]).strip():
                        return jsonify({'success': False, 'message': f'第{index+1}条明细的{field}字段为必填项'}), 400
                
                # 转换数据类型
                expense_date = datetime.strptime(detail['expense_date'], '%Y-%m-%d').date()
                invoice_amount = float(detail['invoice_amount'])
                current_amount = float(detail.get('current_amount', invoice_amount))
                exchange_rate = float(detail.get('exchange_rate', 1.0))
                document_count = int(detail.get('document_count', 1))
                
                if invoice_amount <= 0:
                    return jsonify({'success': False, 'message': f'第{index+1}条明细的发票金额必须大于0'}), 400
                
                # 先创建明细对象（不包含发票数据）
                detail_obj = ExpenseDetail(
                    expense_id=expense_obj.id,
                    expense_date=expense_date,
                    expense_category=detail['expense_category'],
                    description=detail['description'].strip(),
                    document_count=document_count,
                    currency=detail['currency'],
                    invoice_amount=invoice_amount,
                    current_amount=current_amount,
                    amount=current_amount,  # 向后兼容
                    exchange_rate=exchange_rate,
                    invoice_images=None  # 先不设置发票数据
                )
                db.session.add(detail_obj)
                db.session.flush()  # 获取明细ID
                
                # 处理发票图片数据（使用与创建报销单相同的逻辑）
                processed_images = []
                
                # 处理新上传的文件（AJAX FormData方式）
                if index in file_data and 'files' in file_data[index]:
                    for file_index, file_obj in file_data[index]['files'].items():
                        if file_obj and file_obj.filename:
                            try:
                                # 验证文件类型
                                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                                file_ext = file_obj.filename.rsplit('.', 1)[1].lower() if '.' in file_obj.filename else ''
                                if file_ext not in allowed_extensions:
                                    current_app.logger.warning(f"不支持的文件类型: {file_obj.filename}")
                                    continue
                                
                                # 检查文件大小 (最大5MB)
                                file_obj.seek(0, 2)
                                file_size = file_obj.tell()
                                file_obj.seek(0)
                                
                                max_size = 5 * 1024 * 1024  # 5MB
                                if file_size > max_size:
                                    current_app.logger.warning(f"文件过大: {file_obj.filename} ({file_size} bytes)")
                                    continue
                                
                                # 检测运行环境 - 优先判断是否在云端部署
                                current_app.logger.info(f"开始处理文件上传: {file_obj.filename}, 大小: {file_size} bytes")
                                cloud_env = is_cloud_environment()
                                current_app.logger.info(f"环境检测结果: 云端环境={cloud_env}")
                                if cloud_env:
                                    # 云端环境，使用Supabase存储
                                    try:
                                        from app.utils.supabase_client import get_supabase_client
                                        supabase_client = get_supabase_client()
                                        
                                        # 生成文件名
                                        import uuid
                                        filename = f"expense_invoice_{detail_obj.id}_{uuid.uuid4().hex[:8]}.{file_ext}"
                                        
                                        # 上传到Supabase
                                        image_url = supabase_client.upload_expense_invoice(detail_obj.id, file_obj, filename)
                                        
                                        if not image_url:
                                            raise Exception("Supabase上传失败")
                                            
                                        current_app.logger.info(f"发票文件上传到Supabase成功: {image_url}")
                                        
                                    except Exception as supabase_error:
                                        current_app.logger.error(f"云端Supabase上传失败: {str(supabase_error)}")
                                        # 云端上传失败，跳过这个文件
                                        continue
                                else:
                                    # 本地环境，使用本地文件系统
                                    import os
                                    import uuid
                                    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'invoices', str(detail_obj.id))
                                    os.makedirs(upload_dir, exist_ok=True)
                                    
                                    # 生成文件名
                                    filename = f"invoice_{uuid.uuid4().hex[:8]}.{file_ext}"
                                    file_path = os.path.join(upload_dir, filename)
                                    
                                    # 保存文件
                                    file_obj.save(file_path)
                                    
                                    # 生成URL
                                    relative_path = os.path.join('uploads', 'invoices', str(detail_obj.id), filename).replace('\\', '/')
                                    raw_url = f"/static/{relative_path}"
                                    image_url = normalize_file_url(raw_url, 'invoice_image')
                                
                                # 获取原始文件名（如果有元数据）
                                original_filename = file_obj.filename
                                if index in file_data and 'meta' in file_data[index] and file_index in file_data[index]['meta']:
                                    original_filename = file_data[index]['meta'][file_index].get('filename', file_obj.filename)
                                
                                # 添加到处理后的图片列表
                                processed_images.append({
                                    'filename': original_filename,
                                    'url': image_url,
                                    'size': file_size,
                                    'uploaded_at': datetime.now().isoformat()
                                })
                                
                                current_app.logger.info(f"发票图片保存成功: {image_url}")
                                
                            except Exception as file_error:
                                current_app.logger.error(f"发票图片处理失败: {file_error}")
                                continue
                
                # 处理临时上传的文件（通过表单数据传递）
                for key, value in request.form.items():
                    if key.startswith(f'details[{index}][temp_invoices][') and key.endswith('][url]'):
                        # 解析临时文件信息
                        file_index = key.split('][')[2]
                        temp_url = value
                        temp_filename = request.form.get(f'details[{index}][temp_invoices][{file_index}][filename]', '')
                        temp_size_str = request.form.get(f'details[{index}][temp_invoices][{file_index}][size]', '0')
                        
                        try:
                            temp_size = int(temp_size_str) if temp_size_str else 0
                        except (ValueError, TypeError):
                            temp_size = 0
                        
                        if temp_url:
                            processed_images.append({
                                'filename': temp_filename,
                                'url': temp_url,
                                'size': temp_size,
                                'uploaded_at': datetime.now().isoformat()
                            })
                
                # 处理已存在的文件（通过表单数据传递）
                for key, value in request.form.items():
                    if key.startswith(f'details[{index}][existing_invoices][') and key.endswith('][url]'):
                        # 解析已存在文件信息
                        file_index = key.split('][')[2]
                        existing_url = value
                        existing_filename = request.form.get(f'details[{index}][existing_invoices][{file_index}][filename]', '')
                        existing_size_str = request.form.get(f'details[{index}][existing_invoices][{file_index}][size]', '0')
                        
                        try:
                            existing_size = int(existing_size_str) if existing_size_str else 0
                        except (ValueError, TypeError):
                            existing_size = 0
                        
                        if existing_url:
                            processed_images.append({
                                'filename': existing_filename,
                                'url': existing_url,
                                'size': existing_size
                            })
                
                # 处理已有的发票数据（JSON格式，向后兼容）
                if detail.get('invoice_images'):
                    for invoice in detail['invoice_images']:
                        if not invoice.get('pending') and (invoice.get('url') or invoice.get('path')):
                            processed_images.append(invoice)
                
                # 更新明细的发票数据
                if processed_images:
                    import json
                    detail_obj.invoice_images = json.dumps(processed_images)
                total_amount += current_amount
            
            # 更新报销单总金额
            expense_obj.total_amount = total_amount
            
            # 确保用户选择的货币不被覆盖
            if expense_obj.currency != user_selected_currency:
                logger.warning(f"检测到货币被意外修改: {expense_obj.currency} -> {user_selected_currency}，正在恢复")
                expense_obj.currency = user_selected_currency
            
            db.session.commit()
            logger.info(f"报销单保存完成，最终货币: {expense_obj.currency}")
            
            # 返回JSON响应
            return jsonify({
                'success': True,
                'message': '报销单更新成功',
                'redirect_url': url_for('expense.expense_detail', id=expense_obj.id)
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新报销单失败: {e}")
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"详细错误: {error_details}")
            
            # 记录表单数据以便调试
            logger.error(f"表单数据: {dict(request.form)}")
            logger.error(f"文件数据键: {list(request.files.keys())}")
            
            return jsonify({
                'success': False, 
                'message': f'更新报销单失败: {str(e)}',
                'debug_info': str(e) if current_app.debug else None
            }), 500
    
    # GET请求，显示编辑表单
    customers = Company.query.filter(Company.is_deleted == False).order_by(Company.company_name).all()
    projects = Project.query.order_by(Project.project_name).all()
    # 移除departments查询，因为已从模型中删除
    
    # 将报销明细对象转换为字典格式，用于前端组件
    expense_details_data = []
    if expense_obj.details:
        for detail in expense_obj.details:
            detail_dict = {
                'id': detail.id,
                'expense_category': detail.expense_category,
                'expense_date': detail.expense_date.strftime('%Y-%m-%d') if detail.expense_date else '',
                'description': detail.description or '',
                'document_count': detail.document_count or 1,
                'currency': detail.currency or 'CNY',
                'invoice_amount': detail.invoice_amount or 0,
                'current_amount': detail.current_amount or detail.amount or 0,
                'amount': detail.current_amount or detail.amount or 0,  # 向后兼容
                'exchange_rate': detail.exchange_rate or 1.0,
                'invoice_images': []
            }
            
            # 处理发票图片数据
            if detail.invoice_images:
                try:
                    import json
                    images_data = json.loads(detail.invoice_images) if isinstance(detail.invoice_images, str) else detail.invoice_images
                    if isinstance(images_data, list):
                        for img in images_data:
                            if isinstance(img, dict):
                                detail_dict['invoice_images'].append({
                                    'url': img.get('url', ''),
                                    'filename': img.get('filename', ''),
                                    'size': img.get('size', 0),
                                    'pending': False  # 现有图片不是pending状态
                                })
                except (json.JSONDecodeError, TypeError):
                    # 如果解析失败，设为空列表
                    detail_dict['invoice_images'] = []
            
            expense_details_data.append(detail_dict)
    
    return render_template('expense/edit_expense.html',
                         expense=expense_obj,
                         customers=customers,
                         projects=projects,
                         expense_details_data=expense_details_data)

@expense.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('expense', 'delete')
def delete_expense(id):
    """删除报销单"""
    expense_obj = Expense.query.options(
        db.joinedload(Expense.owner)
    ).get_or_404(id)
    
    # 检查删除权限
    if not can_edit_data(expense_obj, current_user):
        return jsonify({'success': False, 'message': '您没有权限删除此报销单'})
    
    # 已审批的报销单不能删除
    if expense_obj.status not in ['draft', 'pending']:
        return jsonify({'success': False, 'message': '已审批的报销单不能删除'})
    
    try:
        # 软删除
        expense_obj.is_deleted = True
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '报销单删除成功',
            'redirect_url': url_for('expense.expense_list')
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除报销单失败: {e}")
        return jsonify({'success': False, 'message': '删除报销单失败，请重试'})

@expense.route('/api/expense/monthly_stats')
@login_required
@permission_required('expense', 'view')
def monthly_expense_stats():
    """当月费用统计"""
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # 查询当月已通过的报销（基于明细表）
    monthly_query = db.session.query(
        func.sum(ExpenseDetail.amount).label('total_amount'),
        func.count(ExpenseDetail.id).label('total_count'),
        ExpenseDetail.expense_category
    ).join(Expense, ExpenseDetail.expense_id == Expense.id)\
     .filter(
        Expense.is_deleted == False,
        Expense.status == 'approved',
        extract('year', Expense.approved_at) == current_year,
        extract('month', Expense.approved_at) == current_month
    ).group_by(ExpenseDetail.expense_category).all()
    
    # 按用户统计（基于主表总金额）
    user_stats = db.session.query(
        func.sum(Expense.total_amount).label('total_amount'),
        func.count(Expense.id).label('total_count'),
        User.username,
        User.real_name
    ).join(User, Expense.owner_id == User.id)\
     .filter(
        Expense.is_deleted == False,
        Expense.status == 'approved',
        extract('year', Expense.approved_at) == current_year,
        extract('month', Expense.approved_at) == current_month
    ).group_by(User.id, User.username, User.real_name).all()
    
    # 格式化统计数据
    category_stats = {}
    # 移除department_stats，因为已从模型中删除部门功能
    
    for row in monthly_query:
        category = dict(EXPENSE_CATEGORIES).get(row.expense_category, row.expense_category)
        if category not in category_stats:
            category_stats[category] = {'amount': 0, 'count': 0}
        category_stats[category]['amount'] += row.total_amount or 0
        category_stats[category]['count'] += row.total_count or 0
    
    user_stats_formatted = []
    for row in user_stats:
        user_stats_formatted.append({
            'username': row.username,
            'real_name': row.real_name,
            'amount': row.total_amount or 0,
            'count': row.total_count or 0
        })
    
    return jsonify({
        'success': True,
        'month': f'{current_year}年{current_month}月',
        'category_stats': category_stats,
        # 移除department_stats，因为已从模型中删除部门功能
        'user_stats': user_stats_formatted
    })


@expense.route('/api/upload_invoice_temp', methods=['POST'])
@login_required
@permission_required('expense', 'edit')
def upload_invoice_temp():
    """临时上传发票图片（用于编辑页面新增明细）"""
    try:
        # 检查是否有上传的文件
        if 'invoice_image' not in request.files:
            return jsonify({'success': False, 'message': '未选择文件'})
        
        file = request.files['invoice_image']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'})
        
        # 验证文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'message': '不支持的文件格式'})
        
        # 生成临时文件名
        import uuid
        temp_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        original_filename = filename
        
        # 添加时间戳避免重复
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}_{temp_id[:8]}{ext}"
        
        # 检查是否在云端环境
        if is_cloud_environment():
            try:
                # 云端环境，尝试使用Supabase上传
                from app.utils.supabase_client import get_supabase_client
                supabase_client = get_supabase_client()
                
                # 先保存文件大小
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                # 使用现有的发票上传方法，但保存到临时路径
                storage_path = f"temp_expense_invoices/{temp_id}/{filename}"
                
                # 直接使用Supabase存储API
                file_content = file.read()
                result = supabase_client.supabase.storage.from_(supabase_client.bucket_name).upload(
                    path=storage_path,
                    file=file_content,
                    file_options={"content-type": "image/jpeg", "upsert": True}
                )
                
                if result.path:
                    # 获取公开URL
                    image_url = supabase_client.supabase.storage.from_(supabase_client.bucket_name).get_public_url(storage_path)
                    
                    return jsonify({
                        'success': True,
                        'message': '发票上传成功',
                        'data': {
                            'url': image_url,
                            'filename': original_filename,
                            'size': file_size,
                            'temp_id': temp_id
                        }
                    })
                else:
                    raise Exception("Supabase上传失败")
                
            except Exception as e:
                logger.error(f"云端Supabase上传失败: {e}")
                # 回退到本地存储
                pass
        
        # 本地环境或云端失败时，使用本地存储
        try:
            temp_upload_dir = os.path.join(current_app.static_folder, 'uploads', 'temp', 'invoices')
            os.makedirs(temp_upload_dir, exist_ok=True)
            
            file_path = os.path.join(temp_upload_dir, filename)
            file.save(file_path)
            
            # 返回相对路径
            relative_path = os.path.join('uploads', 'temp', 'invoices', filename).replace('\\', '/')
            image_url = url_for('static', filename=relative_path)
            
            return jsonify({
                'success': True,
                'message': '发票上传成功',
                'data': {
                    'url': image_url,
                    'filename': original_filename,
                    'size': os.path.getsize(file_path),
                    'temp_id': temp_id
                }
            })
            
        except Exception as e:
            logger.error(f"本地存储失败: {e}")
            return jsonify({'success': False, 'message': f'本地存储失败: {str(e)}'})
            
    except Exception as e:
        logger.error(f"临时上传发票失败: {e}")
        return jsonify({'success': False, 'message': '上传失败，请重试'})

@expense.route('/api/upload_invoice/<int:detail_id>', methods=['POST'])
@login_required
@permission_required('expense', 'edit')
def upload_invoice_image(detail_id):
    """为报销明细上传发票图片"""
    try:
        # 查找报销明细
        detail = ExpenseDetail.query.get_or_404(detail_id)
        
        # 检查权限 - 只有创建者或管理员可以上传
        if not can_edit_data(detail.expense.owner_id):
            return jsonify({
                'success': False,
                'message': _('您没有权限上传此报销单的发票')
            }), 403
        
        # 检查是否已锁定
        if detail.expense.is_locked and current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': _('报销单已锁定，无法上传发票')
            }), 400
        
        # 检查文件
        if 'invoice_image' not in request.files:
            return jsonify({
                'success': False,
                'message': _('请选择要上传的发票图片')
            }), 400
            
        file = request.files['invoice_image']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': _('请选择要上传的发票图片')
            }), 400
        
        # 验证文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'message': _('只支持图片格式：PNG、JPG、JPEG、GIF、WEBP')
            }), 400
        
        # 检查文件大小 (最大5MB)
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 回到文件开头
        
        max_size = 5 * 1024 * 1024  # 5MB
        if file_size > max_size:
            return jsonify({
                'success': False,
                'message': _('文件大小不能超过5MB')
            }), 400
        
        # 检查发票数量限制
        current_count = detail.invoice_count
        if current_count >= 10:  # 最多10张发票
            return jsonify({
                'success': False,
                'message': _('每个报销明细最多只能上传10张发票')
            }), 400
        
        # 检测运行环境 - 优先判断是否在云端部署
        if is_cloud_environment():
            # 云端环境，使用Supabase存储
            try:
                from app.utils.supabase_client import get_supabase_client
                supabase_client = get_supabase_client()
                
                # 生成文件名
                import uuid
                filename = f"expense_invoice_{detail_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
                
                # 上传到Supabase
                image_url = supabase_client.upload_expense_invoice(detail_id, file, filename)
                
                if image_url:
                    # 添加到明细记录
                    detail.add_invoice_image(filename, image_url, file_size)
                    db.session.commit()
                    
                    current_app.logger.info(f"发票图片上传到Supabase成功: {image_url}")
                    
                    return jsonify({
                        'success': True,
                        'message': _('发票上传成功'),
                        'image_url': image_url,
                        'filename': filename,
                        'size': file_size,
                        'invoice_count': detail.invoice_count
                    })
                else:
                    raise Exception("Supabase上传失败")
                    
            except Exception as supabase_error:
                current_app.logger.error(f"云端Supabase上传失败: {str(supabase_error)}")
                return jsonify({
                    'success': False,
                    'message': _('云端存储失败，请检查网络连接后重试')
                }), 500
        else:
            # 本地环境，直接使用本地存储
            import os
            import uuid
            
            current_app.logger.info("检测到本地环境，使用本地文件存储")
            
            # 创建上传目录
            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'invoices', str(detail_id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成文件名
            filename = f"invoice_{uuid.uuid4().hex[:8]}.{file_ext}"
            file_path = os.path.join(upload_dir, filename)
            
            # 保存文件
            file.save(file_path)
            
            # 生成URL
            relative_path = os.path.join('uploads', 'invoices', str(detail_id), filename).replace('\\', '/')
            image_url = f"/static/{relative_path}"
            
            # 添加到明细记录
            detail.add_invoice_image(filename, image_url, file_size)
            db.session.commit()
            
            current_app.logger.info(f"发票图片本地存储成功: {image_url}")
            
            return jsonify({
                'success': True,
                'message': _('发票上传成功'),
                'image_url': image_url,
                'filename': filename,
                'size': file_size,
                'invoice_count': detail.invoice_count
            })
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发票图片上传异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': _('发票上传失败，请重试')
        }), 500


@expense.route('/api/delete_invoice/<int:detail_id>/<int:image_index>', methods=['DELETE'])
@login_required
@permission_required('expense', 'edit')
def delete_invoice_image(detail_id, image_index):
    """删除报销明细的发票图片"""
    try:
        # 查找报销明细
        detail = ExpenseDetail.query.get_or_404(detail_id)
        
        # 检查权限
        if not can_edit_data(detail.expense.owner_id):
            return jsonify({
                'success': False,
                'message': _('您没有权限删除此报销单的发票')
            }), 403
        
        # 检查是否已锁定
        if detail.expense.is_locked and current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': _('报销单已锁定，无法删除发票')
            }), 400
        
        # 获取图片信息
        images = detail.invoice_images_list
        if not images or image_index < 0 or image_index >= len(images):
            return jsonify({
                'success': False,
                'message': _('发票图片不存在')
            }), 404
        
        image_info = images[image_index]
        
        # 删除云端或本地文件
        try:
            # 检测运行环境
            if is_cloud_environment() and image_info['url'].startswith('http'):
                # 云端环境，删除Supabase文件
                from app.utils.supabase_client import get_supabase_client
                supabase_client = get_supabase_client()
                supabase_client.delete_expense_invoice(image_info['filename'])
                current_app.logger.info(f"云端发票文件删除成功: {image_info['filename']}")
            else:
                # 本地环境或本地文件，删除本地文件
                import os
                file_path = os.path.join(current_app.static_folder, image_info['url'].lstrip('/static/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
                    current_app.logger.info(f"本地发票文件删除成功: {file_path}")
                else:
                    current_app.logger.warning(f"本地发票文件不存在: {file_path}")
        except Exception as e:
            current_app.logger.warning(f"删除发票文件失败: {str(e)}")
        
        # 从数据库记录中移除
        detail.remove_invoice_image(image_index)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': _('发票删除成功'),
            'invoice_count': detail.invoice_count
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除发票图片异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': _('发票删除失败，请重试')
        }), 500