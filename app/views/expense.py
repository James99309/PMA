from flask import Blueprint, render_template, render_template_string, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import gettext as _
from app.extensions import csrf
from app.utils.chinese_mapping_manager import mapping_manager
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
from app.utils.dictionary_helpers import get_currency_type_options
from types import SimpleNamespace
import os
from werkzeug.utils import secure_filename
from app.utils.file_url_helper import normalize_file_url
from app.helpers.approval_helpers import (
    get_approval_permission_service, 
    get_field_edit_service,
    check_universal_approval_permission
)

logger = logging.getLogger(__name__)

def is_cloud_environment():
    """检测是否在云端环境运行"""
    render_service = os.getenv('RENDER_SERVICE_NAME')
    supabase_url = os.getenv('SUPABASE_URL')
    
    # 支持强制启用云端上传进行本地测试
    force_cloud_upload = os.getenv('FORCE_CLOUD_UPLOAD', '').lower() in ['true', '1', 'yes']
    
    is_cloud = bool(render_service or supabase_url or force_cloud_upload)
    
    # 添加调试日志
    current_app.logger.info(f"环境检测: RENDER_SERVICE_NAME={render_service}, SUPABASE_URL={supabase_url[:20] + '...' if supabase_url else None}, FORCE_CLOUD_UPLOAD={force_cloud_upload}, is_cloud={is_cloud}")
    
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
            customer_name=customers.get(expense.customer_id, _('未指定')),
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
        'auto_submit': True,  # 启用下拉框自动筛选
        'dynamic_reset_button': True,  # 启用动态重置按钮
        'search_field_id': 'search',  # 搜索框ID，用于重置按钮检测
        'search_field': {
            'name': 'search',
            'label': _('搜索'),
            'placeholder': _('报销单号、标题或客户名称'),
            'value': search,
            'col_width': 4
        },
        'filter_fields': [
            {
                'name': 'customer_id',
                'label': _(mapping_manager.get_field_display_name('expense', 'customer_id')),
                'all_option_text': _('全部客户'),
                'current_value': customer_id,
                'col_width': 2,
                'options': [{'value': str(c.id), 'label': c.company_name, 'translate': False} for c in customers]
            },
            {
                'name': 'owner_id',
                'label': _(mapping_manager.get_field_display_name('expense', 'owner_id')),
                'all_option_text': _('全部申请人'),
                'current_value': owner_id,
                'col_width': 2,
                'options': [{'value': str(u.id), 'label': u.real_name or u.username, 'translate': False} for u in users]
            },
            # 移除报销科目筛选，因为现在在明细表中，可以考虑后续通过明细表联查实现
            {
                'name': 'status',
                'label': _(mapping_manager.get_field_display_name('expense', 'status')),
                'all_option_text': _('全部状态'),
                'current_value': status,
                'col_width': 2,
                'options': status_options
            }
        ],
        'search_button_text': _('搜索'),
        'reset_button_text': _('重置')
    }
    
    # 使用通用列表组件配置
    list_config = {
        'module_name': 'expense',
        'title': _('报销管理'),
        'ajax_mode': True,
        
        # 统计卡片配置
        'stats': {
            'cards': [
                {
                    'id': 'total',
                    'title': _('全部报销'),
                    'icon': 'fas fa-receipt',
                    'value': total_count,
                    'amount': total_amount / 10000,
                    'unit': _('单'),
                    'amount_unit': _('万元'),
                    'color': 'primary',
                    'clickable': True,
                    'click_params': {}
                },
                {
                    'id': 'pending',
                    'title': _('待审批'),
                    'icon': 'fas fa-clock',
                    'value': pending_count,
                    'amount': pending_amount / 10000,
                    'unit': _('单'),
                    'amount_unit': _('万元'),
                    'color': 'warning',
                    'clickable': True,
                    'click_params': {'status': 'pending'}
                },
                {
                    'id': 'approved',
                    'title': _('已通过'),
                    'icon': 'fas fa-check-circle',
                    'value': approved_count,
                    'amount': approved_amount / 10000,
                    'unit': _('单'),
                    'amount_unit': _('万元'),
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
            'title': _('报销列表'),
            'icon': 'fas fa-table',
            'table_name': 'expense',        # 指定数据库表名用于动态映射
            'columns': [
                {
                    'key': 'expense_number',
                    'field': 'expense_number',
                    'label': _(mapping_manager.get_field_display_name('expense', 'expense_number')),
                    'type': 'link',
                    'url_template': '/expense/{id}',
                    'render': 'render_expense_number',
                    'width': '140px',
                    'sort_type': 'string'
                },
                {
                    'key': 'owner',
                    'field': 'owner_id',
                    'label': _(mapping_manager.get_field_display_name('expense', 'owner_id')),
                    'type': 'text',
                    'align': 'start',
                    'width': '100px',
                    'sort_type': 'string'
                },
                {
                    'key': 'status',
                    'field': 'status',
                    'label': _(mapping_manager.get_field_display_name('expense', 'status')),
                    'type': 'badge',
                    'render': 'render_expense_status_badge',
                    'align': 'start',
                    'width': '100px',
                    'sort_type': 'string'
                },
                {
                    'key': 'total_amount',
                    'field': 'total_amount',
                    'label': _(mapping_manager.get_field_display_name('expense', 'total_amount')),
                    'type': 'number',
                    'format': 'currency',
                    'align': 'end',
                    'width': '100px',
                    'sort_type': 'currency'
                },
                {
                    'key': 'customer_name',
                    'field': 'customer_id',
                    'label': _(mapping_manager.get_field_display_name('expense', 'customer_id')),
                    'type': 'text',
                    'width': '150px',
                    'sort_type': 'string'
                },
                {
                    'key': 'contact_name',
                    'field': 'contact_id',
                    'label': _(mapping_manager.get_field_display_name('expense', 'contact_id')),
                    'type': 'text',
                    'width': '120px',
                    'sort_type': 'string'
                },
                {
                    'key': 'project_name',
                    'field': 'project_id',
                    'label': _(mapping_manager.get_field_display_name('expense', 'project_id')),
                    'type': 'text',
                    'width': '150px',
                    'sort_type': 'string'
                },
                {
                    'key': 'created_at',
                    'field': 'created_at',
                    'label': _(mapping_manager.get_field_display_name('expense', 'created_at')),
                    'type': 'date',
                    'format': '%Y-%m-%d',
                    'width': '120px',
                    'sort_type': 'date'
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
        
        # 排序参数
        sort_field = request.args.get('sort_field', '')
        sort_direction = request.args.get('sort_direction', 'asc')
        
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
            Expense.contact_id,
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
            # 获取总数
            total_count = search_query.count()
            # 应用排序
            query_for_sort = search_query
        else:
            # 无搜索条件时直接查询
            total_count = base_query.count()
            query_for_sort = base_query
        
        # 使用通用排序服务
        from app.utils.sorting_service import SortingService, create_basic_field_mappings
        
        # 创建排序配置
        sorting_config = {
            'field_mappings': create_basic_field_mappings(Expense, [
                'expense_number', 'title', 'total_amount', 'status', 'created_at', 'updated_at'
            ]),
            'relation_mappings': {},
            'default_sort': {'field': 'created_at', 'direction': 'desc'}
        }
        
        # 创建排序服务并应用排序
        sorting_service = SortingService(Expense, sorting_config)
        query_for_sort = sorting_service.apply_sort(query_for_sort, sort_field, sort_direction)
            
        # 分页查询
        expenses = query_for_sort.offset(offset).limit(limit).all()
        
        # 4. 批量获取关联数据（避免N+1查询）
        if expenses:
            customer_ids = list(set(e.customer_id for e in expenses if e.customer_id))
            contact_ids = list(set(e.contact_id for e in expenses if e.contact_id))
            project_ids = list(set(e.project_id for e in expenses if e.project_id))
            owner_ids = list(set(e.owner_id for e in expenses if e.owner_id))
            expense_ids = [e.id for e in expenses]
            
            # 批量查询关联数据
            customers = {c.id: c.company_name for c in 
                        Company.query.filter(Company.id.in_(customer_ids)).all()} if customer_ids else {}
            
            contacts = {c.id: c.name for c in 
                       Contact.query.filter(Contact.id.in_(contact_ids)).all()} if contact_ids else {}
            
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
            contacts = {}
            projects = {}
            owners = {}
            detail_counts = {}
        
        # 5. 格式化数据并渲染HTML
        formatted_results = []
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
                customer_name=customers.get(expense.customer_id, _('未指定')),
                contact_name=contacts.get(expense.contact_id, '未指定'),
                project_name=projects.get(expense.project_id, '-'),
                owner=owner_display,
                owner_obj=user_obj,
                detail_count=detail_counts.get(expense.id, 0)
            )
            formatted_results.append(formatted_row)
        
        # 检测移动端并使用智能移动卡片
        from app.utils.mobile_helpers import is_mobile_request
        
        if formatted_results:
            if is_mobile_request():
                # 智能移动卡片配置
                smart_mobile_card = {
                    'module': 'expense',
                    'title_field': {'field': 'expense_number', 'renderer': 'render_expense_number'},
                    'link_url': '/expense/{id}',
                    'badges': [
                        {'field': 'status', 'renderer': 'expense_status'}
                    ],
                    'details': [
                        {'field': 'title', 'label': mapping_manager.get_field_display_name('expense', 'title')},
                        {'field': 'customer_name', 'label': mapping_manager.get_field_display_name('expense', 'customer_id')},
                        {'field': 'owner', 'label': mapping_manager.get_field_display_name('expense', 'owner_id')},
                        {'field': 'total_amount', 'label': mapping_manager.get_field_display_name('expense', 'total_amount'), 'format': 'currency'},
                        {'field': 'detail_count', 'label': mapping_manager.get_field_display_name('expense', 'detail_count'), 'suffix': '项'},
                        {'field': 'created_at', 'label': mapping_manager.get_field_display_name('expense', 'created_at'), 'format': 'date'}
                    ]
                }
                
                # 使用智能移动卡片模板渲染
                html = render_template_string('''
                {% from 'macros/ui_helpers.html' import render_smart_mobile_cards %}
                {{ render_smart_mobile_cards(items, card_config) }}
                ''', items=formatted_results, card_config=smart_mobile_card)
            else:
                # 桌面端使用传统表格行渲染
                html_rows = []
                for formatted_row in formatted_results:
                    html_row = render_template('expense/expense_rows.html', expense=formatted_row)
                    html_rows.append(html_row)
                html = '\n'.join(html_rows)
        else:
            if is_mobile_request():
                html = '<div class="text-center py-4">暂无符合条件的数据</div>'
            else:
                html = '<tr><td colspan="8" class="text-center py-4">暂无符合条件的数据</td></tr>'
        
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
            'html': html,
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
            no_customer_mode = request.form.get('no_customer_mode') == '1'
            customer_id = request.form.get('customer_id', type=int) if not no_customer_mode else None
            contact_id = request.form.get('contact_id', type=int) if not no_customer_mode else None
            project_id = request.form.get('project_id', type=int) if not no_customer_mode else None
            expense_currency = request.form.get('currency', 'CNY').strip()  # 报销单主货币
            logger.info(f"用户选择的报销单主货币: {expense_currency}, 不关联客户模式: {no_customer_mode}")
            
            # 数据验证
            if no_customer_mode:
                # 不关联客户模式：验证报销说明必填
                if not description:
                    flash(_('不关联客户模式下，报销说明为必填项'), 'error')
                    return redirect(url_for('expense.create_expense'))
            else:
                # 常规模式：验证客户和联系人
                if not all([customer_id, contact_id]):
                    flash(_('请填写所有必填字段（客户和联系人）'), 'error')
                    return redirect(url_for('expense.create_expense'))
            
            # 获取报销明细数据 - 支持两种数据格式
            detail_data = {}
            
            # 方式1：尝试从 expense_details 隐藏字段获取JSON数据
            expense_details_json = request.form.get('expense_details')
            if expense_details_json:
                try:
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
                flash(_('请至少添加一条报销明细'), 'error')
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
                            flash(_('第{index}个明细项目的{field}字段为必填项').format(index=index+1, field=field), 'error')
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
                        flash(_('第{index}个明细项目的发票金额必须大于0').format(index=index+1), 'error')
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
                    flash(_('第{index}个明细项目数据格式错误: {error}').format(index=index+1, error=str(e)), 'error')
                    return redirect(url_for('expense.create_expense'))
            
            # 如果没有填写报销主题，则自动生成
            if not title:
                # 获取当前用户账户
                current_user_account = current_user.username if current_user else ''
                
                # 生成时间戳 YYDDHHS（年年月月日日时时秒秒）
                now = datetime.now()
                time_str = now.strftime('%y%m%d%H%S')
                
                if no_customer_mode:
                    # 不关联客户模式：不关联（报销说明前6个字）-账号-序号
                    description_prefix = description[:6] if description else '报销'
                    title = f"不关联（{description_prefix}）-{current_user_account}-{time_str}"
                else:
                    # 常规模式：客户名称-用户账户-YYDDHHS
                    customer = Company.query.get(customer_id)
                    customer_name = customer.company_name if customer else '未知客户'
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
                                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif', 'pdf'}
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
                                        
                                        # 使用规范化的文件命名系统
                                        # upload_expense_invoice方法现在会自动生成规范化的文件名
                                        # 格式：{项目代码}-{客户简称}-{报销单号}-{明细序号}-{文件序号}.{扩展名}
                                        
                                        # 上传到Supabase（传递明细索引和文件索引避免冲突）
                                        upload_result = supabase_client.upload_expense_invoice(detail_obj.id, file_obj, file_obj.filename, 'invoice', index, file_index)
                                        
                                        if upload_result:
                                            # 处理新的返回格式
                                            if isinstance(upload_result, dict):
                                                image_url = upload_result['url']
                                                original_filename = upload_result['filename']  # 使用规范化文件名
                                            else:
                                                image_url = upload_result
                                                original_filename = file_obj.filename
                                        else:
                                            raise Exception("Supabase上传失败")
                                            
                                        current_app.logger.info(f"发票文件上传到Supabase成功: {image_url}")
                                        
                                    except Exception as supabase_error:
                                        current_app.logger.error(f"云端Supabase上传失败: {str(supabase_error)}")
                                        # 添加详细错误信息
                                        import traceback
                                        current_app.logger.error(f"Supabase上传详细错误: {traceback.format_exc()}")
                                        current_app.logger.error(f"文件信息: filename={file_obj.filename}, size={file_size}, ext={file_ext}")
                                        # 云端上传失败，跳过这个文件
                                        continue
                                else:
                                    # 本地环境，使用智能存储系统（自动生成规范化文件名）
                                    try:
                                        from app.utils.supabase_client import get_supabase_client
                                        supabase_client = get_supabase_client()
                                        
                                        # 上传到智能存储系统（传递明细索引和文件索引避免冲突）
                                        upload_result = supabase_client.upload_expense_invoice(detail_obj.id, file_obj, file_obj.filename, 'invoice', index, file_index)
                                        
                                        if upload_result:
                                            # 处理新的返回格式
                                            if isinstance(upload_result, dict):
                                                image_url = upload_result['url']
                                                original_filename = upload_result['filename']  # 使用规范化文件名
                                            else:
                                                image_url = upload_result
                                                original_filename = file_obj.filename
                                        else:
                                            raise Exception("智能存储上传失败")
                                            
                                    except Exception as storage_error:
                                        current_app.logger.error(f"智能存储上传失败: {str(storage_error)}")
                                        continue
                                
                                # 注意：original_filename已经在上面的if-else分支中设置了
                                
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
                        if invoice.get('pending'):
                            # 处理待确认的发票（临时上传的文件）
                            if invoice.get('temp_id') and invoice.get('url'):
                                # 这是临时上传的文件，需要移动到正式位置
                                logger.info(f"明细 {index}: 处理临时文件 - {invoice.get('filename')}")
                                
                                # 🔥 将临时文件转移到正式存储
                                final_url = _move_temp_file_to_permanent(
                                    detail_obj.id, 
                                    invoice.get('temp_id'),
                                    invoice.get('filename'),
                                    invoice.get('url')
                                )
                                
                                if final_url:
                                    processed_images.append({
                                        'filename': invoice.get('filename', ''),
                                        'url': final_url,
                                        'size': invoice.get('size', 0)
                                    })
                                    logger.info(f"明细 {index}: 临时文件已转移到正式存储: {final_url}")
                                else:
                                    # 转移失败，保留临时URL（降级方案）
                                    processed_images.append({
                                        'filename': invoice.get('filename', ''),
                                        'url': invoice.get('url', ''),
                                        'size': invoice.get('size', 0)
                                    })
                                    logger.warning(f"明细 {index}: 临时文件转移失败，保留临时URL")
                            elif invoice.get('file'):
                                # 这是前端待上传的文件对象，跳过（应该通过文件上传处理）
                                logger.info(f"明细 {index}: 跳过前端文件对象")
                                pass
                        elif not invoice.get('pending') and (invoice.get('url') or invoice.get('path')):
                            # 处理已确认的发票（已保存的文件）
                            processed_images.append(invoice)
                
                # 更新明细的发票数据
                if processed_images:
                    detail_obj.invoice_images = json.dumps(processed_images)
                    logger.info(f"明细 {index}: 最终保存 {len(processed_images)} 张图片到数据库")
                else:
                    detail_obj.invoice_images = None
                    logger.info(f"明细 {index}: 清空图片数据（无图片）")
            
            # 确保用户选择的货币不被覆盖
            if expense_obj.currency != expense_currency:
                logger.warning(f"创建时检测到货币被意外修改: {expense_obj.currency} -> {expense_currency}，正在恢复")
                expense_obj.currency = expense_currency
            
            db.session.commit()
            logger.info(f"报销单创建完成，最终货币: {expense_obj.currency}")
            
            # 检查是否是AJAX请求
            if request.headers.get('Content-Type', '').startswith('multipart/form-data'):
                # 收集文件上传信息用于调试
                upload_info = {
                    'is_cloud': is_cloud_environment(),
                    'uploaded_files': [],
                    'environment_vars': {
                        'SUPABASE_URL': os.getenv('SUPABASE_URL', 'Not Set')[:20] + '...' if os.getenv('SUPABASE_URL') else 'Not Set',
                        'FORCE_CLOUD_UPLOAD': os.getenv('FORCE_CLOUD_UPLOAD', 'Not Set'),
                        'RENDER_SERVICE_NAME': os.getenv('RENDER_SERVICE_NAME', 'Not Set')
                    }
                }
                
                # 收集上传的文件信息
                for detail in detail_items:
                    if 'invoice_images' in detail and detail['invoice_images']:
                        try:
                            images = json.loads(detail['invoice_images']) if isinstance(detail['invoice_images'], str) else detail['invoice_images']
                            if images:
                                upload_info['uploaded_files'].extend([img.get('url', 'No URL') for img in images])
                        except:
                            pass
                
                # AJAX请求，返回JSON响应
                return jsonify({
                    'success': True,
                    'message': f'报销单创建成功，共添加 {len(detail_items)} 条明细，总金额 ¥{total_amount:.2f}',
                    'redirect_url': url_for('expense.expense_detail', id=expense_obj.id),
                    'expense_id': expense_obj.id,
                    'expense_number': expense_obj.expense_number,
                    'file_upload_info': upload_info
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
    # 获取用户最近一次报销的货币作为默认值
    last_expense_currency = 'CNY'  # 默认人民币
    try:
        last_expense = Expense.query.filter_by(owner_id=current_user.id)\
                                   .order_by(Expense.created_at.desc())\
                                   .first()
        if last_expense and last_expense.currency:
            last_expense_currency = last_expense.currency
            logger.info(f"用户 {current_user.username} 最近报销货币: {last_expense_currency}")
    except Exception as e:
        logger.warning(f"获取最近报销货币失败: {e}")
    
    return render_template('expense/create_expense.html',
                         currency_options=get_currency_type_options(),
                         expense_categories=EXPENSE_CATEGORIES,
                         default_currency=last_expense_currency)

@expense.route('/<int:id>')
@login_required
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
        flash(_('您没有权限查看此报销单'), 'error')
        return redirect(url_for('expense.expense_list'))
    
    # 智能返回逻辑：根据用户权限和访问来源确定返回链接
    return_url = url_for('expense.expense_list')  # 默认返回报销单管理
    return_text = '返回列表'
    
    # 检查是否从审批中心访问（通过URL参数）
    from_approval = request.args.get('from_approval', 'false').lower() == 'true'
    
    if from_approval:
        # 从审批中心访问，应该返回审批中心
        return_url = url_for('approval.center')
        return_text = '返回审批中心'
    else:
        # 不是从审批中心访问，检查用户是否有报销单管理权限
        if expense_obj.owner_id != current_user.id:
            # 用户不是创建人，检查是否有查看权限
            try:
                if not current_user.has_permission('expense', 'view'):
                    # 没有报销单管理权限，返回审批中心
                    return_url = url_for('approval.center')
                    return_text = '返回审批中心'
            except Exception:
                # 权限检查失败时，安全起见返回审批中心
                return_url = url_for('approval.center')
                return_text = '返回审批中心'
    
    # 获取审核阶段可编辑字段信息（使用通用服务）
    approval_edit_info = None
    try:
        approval_edit_info = check_universal_approval_permission('expense', id, current_user.id, 'edit')
    except Exception as e:
        current_app.logger.warning(f"获取审核阶段可编辑字段信息失败: {str(e)}")
    
    return render_template('expense/expense_detail.html', 
                         expense=expense_obj,
                         return_url=return_url,
                         return_text=return_text,
                         approval_edit_info=approval_edit_info)

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
    
    # 检查是否为审核阶段编辑模式
    approval_edit_mode = request.args.get('approval_edit') == '1'
    approval_edit_info = None
    
    if approval_edit_mode:
        # 审核阶段编辑模式的权限检查（使用通用服务）
        approval_edit_info = check_universal_approval_permission('expense', id, current_user.id, 'edit')
        
        if not approval_edit_info['can_edit']:
            flash(_('您无权在当前审核阶段编辑此报销单'), 'error')
            return redirect(url_for('expense.expense_detail', id=id))
    else:
        # 常规编辑模式的权限检查
        if not can_edit_data(expense_obj, current_user):
            flash(_('您没有权限编辑此报销单'), 'error')
            return redirect(url_for('expense.expense_detail', id=id))
        
        # 检查报销单是否可编辑：只有草稿状态和被拒绝/召回状态可以编辑
        if expense_obj.status not in ['draft', 'rejected', 'recalled']:
            flash(_('当前状态的报销单不能编辑'), 'error')
            return redirect(url_for('expense.expense_detail', id=id))
        
        # 检查锁定状态：如果报销单被锁定（通常在审批过程中），不能编辑
        if expense_obj.is_locked:
            flash(_('报销单已被锁定，无法编辑'), 'error')
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
            
            # 根据编辑模式决定更新哪些字段
            if approval_edit_mode:
                # 审核编辑模式：只更新允许编辑的字段
                logger.info(f"审核编辑模式：可编辑字段 {approval_edit_info['editable_fields']}")
                editable_fields = approval_edit_info['editable_fields']
                
                # 基本信息字段的有条件更新
                if 'title' in editable_fields:
                    title = request.form.get('title', '').strip()
                    if not title:
                        return jsonify({'success': False, 'message': '报销主题不能为空'}), 400
                    expense_obj.title = title
                
                if 'description' in editable_fields:
                    expense_obj.description = request.form.get('description', '').strip()
                    
                if 'customer_id' in editable_fields:
                    customer_id = request.form.get('customer_id', type=int)
                    if not customer_id:
                        return jsonify({'success': False, 'message': '请选择关联客户'}), 400
                    expense_obj.customer_id = customer_id
                    
                if 'contact_id' in editable_fields:
                    contact_id = request.form.get('contact_id', type=int)
                    if not contact_id:
                        return jsonify({'success': False, 'message': '请选择联系人'}), 400
                    expense_obj.contact_id = contact_id
                    
                if 'project_id' in editable_fields:
                    expense_obj.project_id = request.form.get('project_id', type=int) or None
                    
                if 'currency' in editable_fields:
                    user_selected_currency = request.form.get('currency', 'CNY')
                    expense_obj.currency = user_selected_currency
                    logger.info(f"审核编辑：更新货币为 {user_selected_currency}")
            else:
                # 常规编辑模式：更新所有字段
                title = request.form.get('title', '').strip()
                if not title:
                    return jsonify({'success': False, 'message': '报销主题不能为空'}), 400
                
                # 检查不关联客户模式
                no_customer_mode = request.form.get('no_customer_mode') == '1'
                logger.info(f"编辑模式检测到不关联客户模式: {no_customer_mode}")
                
                if not no_customer_mode:
                    # 常规模式：验证客户和联系人
                    customer_id = request.form.get('customer_id', type=int)
                    if not customer_id:
                        return jsonify({'success': False, 'message': '请选择关联客户'}), 400
                        
                    contact_id = request.form.get('contact_id', type=int)
                    if not contact_id:
                        return jsonify({'success': False, 'message': '请选择联系人'}), 400
                        
                    expense_obj.customer_id = customer_id
                    expense_obj.contact_id = contact_id
                    expense_obj.project_id = request.form.get('project_id', type=int) or None
                else:
                    # 不关联客户模式：设置为空值
                    expense_obj.customer_id = None
                    expense_obj.contact_id = None
                    expense_obj.project_id = None
                
                expense_obj.title = title
                expense_obj.description = request.form.get('description', '').strip()
                
                # 保存用户明确选择的货币，确保不被后续逻辑覆盖
                user_selected_currency = request.form.get('currency', 'CNY')
                expense_obj.currency = user_selected_currency
                logger.info(f"常规编辑：用户选择的报销单货币 {user_selected_currency}")
            
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
            
            if approval_edit_mode and 'exchange_rate' in approval_edit_info['editable_fields']:
                # 审核编辑模式：只更新汇率字段，不删除重建明细
                logger.info("审核编辑模式：只更新汇率字段")
                existing_details = ExpenseDetail.query.filter_by(expense_id=expense_obj.id).order_by(ExpenseDetail.id).all()
                total_amount = 0.0
                
                for index, detail_obj in enumerate(existing_details):
                    if index in detail_data:
                        detail = detail_data[index]
                        # 只更新汇率相关字段
                        if 'exchange_rate' in detail:
                            exchange_rate = float(detail.get('exchange_rate', 1.0))
                            detail_obj.exchange_rate = exchange_rate
                            
                            # 重新计算转换后的金额
                            invoice_amount = detail_obj.invoice_amount or 0
                            current_amount = invoice_amount * exchange_rate
                            detail_obj.current_amount = current_amount
                            detail_obj.amount = current_amount  # 向后兼容
                            
                            logger.info(f"更新明细 {detail_obj.id} 汇率: {exchange_rate}, 转换金额: {current_amount}")
                    
                    total_amount += detail_obj.current_amount or detail_obj.amount or 0
                
                # 更新报销单总金额
                expense_obj.total_amount = total_amount
                
            else:
                # 新的简单编辑模式：智能增量更新，无需删除重建
                logger.info("简单编辑模式：智能增量更新明细")
                
                # 获取现有明细，按ID排序以保持顺序
                existing_details = ExpenseDetail.query.filter_by(expense_id=expense_obj.id).order_by(ExpenseDetail.id).all()
                existing_detail_ids = [d.id for d in existing_details]
                logger.info(f"现有明细数量: {len(existing_details)}, IDs: {existing_detail_ids}")
                
                total_amount = 0.0
                processed_detail_ids = set()
                
                for index in sorted(detail_data.keys()):
                    detail = detail_data[index]
                    logger.info(f"处理明细 {index}: {detail.get('description', 'N/A')}")
                    
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
                    
                    # 智能处理明细：更新现有或创建新的
                    detail_obj = None
                    if index < len(existing_details):
                        # 更新现有明细
                        detail_obj = existing_details[index]
                        logger.info(f"更新现有明细 ID={detail_obj.id}")
                        
                        detail_obj.expense_date = expense_date
                        detail_obj.expense_category = detail['expense_category']
                        detail_obj.description = detail['description'].strip()
                        detail_obj.document_count = document_count
                        detail_obj.currency = detail['currency']
                        detail_obj.invoice_amount = invoice_amount
                        detail_obj.current_amount = current_amount
                        detail_obj.amount = current_amount  # 向后兼容
                        detail_obj.exchange_rate = exchange_rate
                        
                        processed_detail_ids.add(detail_obj.id)
                        
                    else:
                        # 创建新明细
                        logger.info(f"创建新明细 {index}")
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
                            invoice_images=None  # 稍后处理图片
                        )
                        db.session.add(detail_obj)
                        db.session.flush()  # 获取ID
                        processed_detail_ids.add(detail_obj.id)
                    
                    # 处理该明细的图片数据（智能保留现有+添加新的）
                    processed_images = []
                    
                    # 1. 处理通过表单传递的现有图片（前端传递的现有图片）
                    existing_images_count = 0
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
                            
                            # 保留现有图片记录（即使URL为空）
                            if existing_filename or existing_url or existing_size:
                                processed_images.append({
                                    'filename': existing_filename,
                                    'url': existing_url,
                                    'size': existing_size
                                })
                                existing_images_count += 1
                                logger.info(f"明细 {index}: 保留现有图片 - {existing_filename}")
                    
                    # 2. 处理新上传的文件（简化逻辑）
                    if index in file_data and 'files' in file_data[index]:
                        for file_index, file_obj in file_data[index]['files'].items():
                            if file_obj and file_obj.filename:
                                # 使用现有的文件上传逻辑（简化版本）
                                try:
                                    # 验证文件类型
                                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif', 'pdf'}
                                    file_ext = file_obj.filename.rsplit('.', 1)[1].lower() if '.' in file_obj.filename else ''
                                    if file_ext not in allowed_extensions:
                                        logger.warning(f"明细 {index}: 不支持的文件类型 - {file_obj.filename}")
                                        continue
                                    
                                    # 检查文件大小
                                    file_obj.seek(0, 2)
                                    file_size = file_obj.tell()
                                    file_obj.seek(0)
                                    
                                    max_size = 5 * 1024 * 1024  # 5MB
                                    if file_size > max_size:
                                        logger.warning(f"明细 {index}: 文件过大 - {file_obj.filename}")
                                        continue
                                    
                                    # 云端上传逻辑
                                    cloud_env = is_cloud_environment()
                                    if cloud_env:
                                        try:
                                            from app.utils.supabase_client import get_supabase_client
                                            supabase_client = get_supabase_client()
                                            
                                            # 使用规范化的文件命名系统（传递文件索引避免冲突）
                                            upload_result = supabase_client.upload_expense_invoice(detail_obj.id, file_obj, file_obj.filename, 'invoice', index, file_index)
                                            
                                            if upload_result:
                                                # 处理新的返回格式
                                                if isinstance(upload_result, dict):
                                                    image_url = upload_result['url']
                                                    original_filename = upload_result['filename']  # 使用规范化文件名
                                                else:
                                                    image_url = upload_result
                                                    original_filename = file_obj.filename
                                            else:
                                                raise Exception("Supabase上传失败")
                                                
                                            logger.info(f"明细 {index}: Supabase上传成功 - {image_url}")
                                            
                                        except Exception as supabase_error:
                                            logger.error(f"明细 {index}: Supabase上传失败 - {supabase_error}")
                                            continue
                                    else:
                                        # 本地上传逻辑
                                        import uuid
                                        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'invoices', str(detail_obj.id))
                                        os.makedirs(upload_dir, exist_ok=True)
                                        
                                        filename = f"invoice_{uuid.uuid4().hex[:8]}.{file_ext}"
                                        file_path = os.path.join(upload_dir, filename)
                                        file_obj.save(file_path)
                                        
                                        relative_path = os.path.join('uploads', 'invoices', str(detail_obj.id), filename).replace('\\', '/')
                                        image_url = f"/static/{relative_path}"
                                        original_filename = file_obj.filename  # 本地上传使用原始文件名
                                    
                                    # 添加到图片列表
                                    processed_images.append({
                                        'filename': original_filename,
                                        'url': image_url,
                                        'size': file_size,
                                        'uploaded_at': datetime.now().isoformat()
                                    })
                                    logger.info(f"明细 {index}: 新增图片 - {file_obj.filename}")
                                    
                                except Exception as file_error:
                                    logger.error(f"明细 {index}: 文件处理异常 - {file_error}")
                                    continue
                    
                    # 3. 保存图片数据到数据库
                    if processed_images:
                        detail_obj.invoice_images = json.dumps(processed_images)
                        logger.info(f"明细 {index}: 最终保存 {len(processed_images)} 张图片到数据库")
                    else:
                        detail_obj.invoice_images = None
                        logger.info(f"明细 {index}: 无图片数据")
                    
                    # 累计总金额
                    total_amount += current_amount
                
                # 删除未处理的旧明细（如果有的话）
                for old_detail in existing_details:
                    if old_detail.id not in processed_detail_ids:
                        logger.info(f"删除未使用的明细 ID={old_detail.id}")
                        db.session.delete(old_detail)
                
                # 更新报销单总金额
                expense_obj.total_amount = total_amount
            
            # 确保用户选择的货币不被覆盖（仅在常规编辑模式下）
            if not approval_edit_mode:
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
                    images_data = json.loads(detail.invoice_images) if isinstance(detail.invoice_images, str) else detail.invoice_images
                    if isinstance(images_data, list):
                        for img in images_data:
                            if isinstance(img, dict):
                                # 修复URL数据：处理错误的"[object Object]"字符串
                                raw_url = img.get('url', '')
                                fixed_url = ''
                                
                                if isinstance(raw_url, str):
                                    if raw_url == '[object Object]':
                                        # 错误的对象字符串，尝试从其他字段重构URL或清空
                                        logger.warning(f"检测到错误的URL数据，将被清空: {raw_url}")
                                        fixed_url = ''
                                    else:
                                        fixed_url = raw_url
                                elif isinstance(raw_url, dict):
                                    # 如果URL是字典，提取实际的URL字符串
                                    fixed_url = raw_url.get('url', '') if 'url' in raw_url else str(raw_url)
                                else:
                                    fixed_url = str(raw_url) if raw_url else ''
                                
                                detail_dict['invoice_images'].append({
                                    'url': fixed_url,
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
                         expense_details_data=expense_details_data,
                         approval_edit_mode=approval_edit_mode,
                         approval_edit_info=approval_edit_info,
                         currency_options=get_currency_type_options(),
                         expense_categories=EXPENSE_CATEGORIES)

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
    
    # 只允许删除草稿、已拒绝、已召回状态的报销单
    if expense_obj.status not in ['draft', 'rejected', 'recalled']:
        return jsonify({'success': False, 'message': '只能删除草稿、已拒绝或已召回状态的报销单'})
    
    try:
        # 🔥 删除关联的云端图片文件（在软删除之前）
        deleted_files_count = 0
        try:
            for detail in expense_obj.details:
                if detail.invoice_images_list:
                    for image_info in detail.invoice_images_list:
                        try:
                            # 检测运行环境并删除云端文件
                            if is_cloud_environment() and image_info.get('url', '').startswith('http'):
                                from app.utils.supabase_client import get_supabase_client
                                supabase_client = get_supabase_client()
                                if supabase_client.delete_expense_invoice(image_info.get('filename', '')):
                                    deleted_files_count += 1
                                    logger.info(f"云端发票文件删除成功: {image_info.get('filename')}")
                            else:
                                # 本地文件删除逻辑
                                import os
                                file_path = os.path.join(current_app.static_folder, image_info.get('url', '').lstrip('/static/'))
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    deleted_files_count += 1
                                    logger.info(f"本地发票文件删除成功: {file_path}")
                        except Exception as e:
                            logger.warning(f"删除发票文件失败 {image_info.get('filename', 'unknown')}: {str(e)}")
        except Exception as e:
            logger.warning(f"删除关联图片文件时出错，但继续执行软删除: {str(e)}")
        
        # 软删除报销单
        expense_obj.is_deleted = True
        db.session.commit()
        
        success_message = f'报销单删除成功'
        if deleted_files_count > 0:
            success_message += f'，同时删除了 {deleted_files_count} 个关联的图片文件'
        
        return jsonify({
            'success': True, 
            'message': success_message,
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
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif', 'pdf'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'message': '不支持的文件格式，支持：PNG、JPG、JPEG、GIF、WEBP、HEIC、PDF'})
        
        # 生成临时文件名
        import uuid
        temp_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        
        # 检测Safari tempImage重命名并修正扩展名
        filename = original_filename
        if original_filename.startswith('tempImage') and original_filename.endswith('.heic'):
            # Safari的tempImage文件，为了兼容性强制使用JPG扩展名
            name, ext = os.path.splitext(original_filename)
            filename = f"{name}.jpg"
            logger.warning(f"检测到Safari tempImage文件，修正扩展名：{original_filename} -> {filename}")
        
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
                logger.info(f"🌐 获取Supabase客户端成功，使用存储类型: {'云端' if not supabase_client.use_local_storage else '本地'}")
                
                # 先保存文件大小
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                # 使用临时路径但应用标准的图片处理逻辑
                storage_path = f"temp_expense_invoices/{temp_id}/{filename}"
                
                # 读取文件内容
                file_content = file.read()
                file.seek(0)  # 重置文件指针
                
                # 使用标准的图片处理逻辑（压缩等，但保持原始格式）
                try:
                    processed_content = supabase_client._process_invoice_image(file_content, filename)
                    logger.info(f"图片已处理但保持原始格式: {filename}")
                except Exception as e:
                    logger.warning(f"图片处理失败，使用原始文件: {str(e)}")
                    processed_content = file_content
                
                # 根据文件扩展名确定content-type
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                content_type_map = {
                    'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                    'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp',
                    'heic': 'image/heic', 'heif': 'image/heif', 'pdf': 'application/pdf'
                }
                content_type = content_type_map.get(file_ext, 'application/octet-stream')
                
                # 上传处理后的文件
                bucket_name = supabase_client.get_bucket_name('invoice')
                # 使用新版SDK的正确API格式
                result = supabase_client.supabase.storage.from_(bucket_name).upload(
                    storage_path,
                    processed_content
                )
                
                if result.path:
                    # 获取公开URL
                    public_url_response = supabase_client.supabase.storage.from_(bucket_name).get_public_url(storage_path)
                    # 处理Supabase的URL响应格式
                    if hasattr(public_url_response, 'data'):
                        image_url = public_url_response.data
                    elif hasattr(public_url_response, 'publicUrl'):
                        image_url = public_url_response.publicUrl
                    elif hasattr(public_url_response, 'url'):
                        image_url = public_url_response.url
                    elif isinstance(public_url_response, str):
                        image_url = public_url_response
                    else:
                        # 🚨 避免[object Object]，手动构建公开URL
                        base_url = supabase_client.supabase_url
                        image_url = f"{base_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
                        logger.warning(f"临时上传URL响应格式未知，手动构建公开URL: {image_url}")
                        logger.debug(f"响应对象类型: {type(public_url_response)}, 内容: {public_url_response}")
                    
                    logger.info(f"🌐 生成的公开URL: {image_url}")
                    
                    return jsonify({
                        'success': True,
                        'message': '发票上传成功',
                        'data': {
                            'url': image_url,
                            'filename': filename,  # 返回处理后的文件名
                            'size': len(processed_content),  # 使用处理后的文件大小
                            'temp_id': temp_id,
                            'is_temp': True
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
                    'filename': filename,
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
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif', 'pdf'}
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
        # 使用智能存储系统（自动选择本地/云端）
        try:
            from app.utils.supabase_client import get_supabase_client
            supabase_client = get_supabase_client()
            
            current_app.logger.info(f"使用智能存储系统上传发票: {'本地存储' if supabase_client.use_local_storage else '云端存储'}")
            
            # 计算下一个文件序号（避免命名冲突）
            next_file_sequence = current_count + 1
            
            # 上传到智能存储系统（自动生成规范化文件名，传递文件序号）
            upload_result = supabase_client.upload_expense_invoice(detail_id, file, file.filename, 'invoice', None, next_file_sequence)
            
            if upload_result:
                # 处理新的返回格式（支持向下兼容）
                if isinstance(upload_result, dict):
                    # 新格式：详细文件信息
                    image_url = upload_result['url']
                    display_filename = upload_result['filename']  # 使用规范化文件名
                    current_app.logger.info(f"规范化文件名: {display_filename}")
                else:
                    # 旧格式：仅URL字符串（向下兼容）
                    image_url = upload_result
                    display_filename = file.filename
                
                # 添加到明细记录
                detail.add_invoice_image(display_filename, image_url, file_size)
                db.session.commit()
                
                current_app.logger.info(f"发票图片上传成功: {image_url}")
                
                return jsonify({
                    'success': True,
                    'message': _('发票上传成功'),
                    'image_url': image_url,
                    'filename': display_filename,
                    'size': file_size,
                    'invoice_count': detail.invoice_count
                })
            else:
                raise Exception("智能存储系统上传失败")
                
        except Exception as upload_error:
            current_app.logger.error(f"智能存储系统上传失败: {str(upload_error)}")
            return jsonify({
                'success': False,
                'message': _('文件上传失败，请重试')
            }), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发票图片上传异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': _('发票上传失败，请重试')
        }), 500


@expense.route('/api/preview_invoice_filename/<int:detail_id>', methods=['POST'])
@csrf.exempt
@login_required
@permission_required('expense', 'edit')
def preview_invoice_filename(detail_id):
    """预览规范化发票文件名（上传前预览）"""
    try:
        data = request.get_json()
        original_filename = data.get('filename', '')
        mime_type = data.get('mimeType', '')
        
        if not original_filename:
            return jsonify({
                'success': False,
                'message': _('文件名不能为空')
            }), 400
        
        # 检测Safari错误转换并确定正确的扩展名
        correct_extension = 'jpg'  # 默认扩展名
        
        if original_filename and '.' in original_filename:
            user_extension = original_filename.rsplit('.', 1)[1].lower()
            
            # 检测Safari错误转换：用户选择非HEIC文件但MIME类型为image/heic
            if user_extension != 'heic' and mime_type and mime_type.lower() == 'image/heic':
                current_app.logger.warning(f"检测到Safari错误转换：用户文件 {original_filename}（{user_extension}）被标记为 {mime_type}")
                current_app.logger.warning(f"强制使用用户文件的原始扩展名：{user_extension}")
                correct_extension = user_extension
            elif mime_type:
                # 正常情况：基于MIME类型确定扩展名
                mime_to_extension = {
                    'image/png': 'png',
                    'image/jpeg': 'jpg',
                    'image/jpg': 'jpg', 
                    'image/gif': 'gif',
                    'image/bmp': 'bmp',
                    'image/webp': 'webp',
                    'image/heic': 'heic',
                    'image/heif': 'heif',
                    'application/pdf': 'pdf'
                }
                correct_extension = mime_to_extension.get(mime_type.lower(), user_extension or 'jpg')
            else:
                # 没有MIME类型：使用用户文件扩展名
                correct_extension = user_extension or 'jpg'
        elif mime_type:
            # 没有原始文件名但有MIME类型
            mime_to_extension = {
                'image/png': 'png',
                'image/jpeg': 'jpg',
                'image/jpg': 'jpg', 
                'image/gif': 'gif',
                'image/bmp': 'bmp',
                'image/webp': 'webp',
                'image/heic': 'heic',
                'image/heif': 'heif',
                'application/pdf': 'pdf'
            }
            correct_extension = mime_to_extension.get(mime_type.lower(), 'jpg')
        
        # 构造用于生成规范化名称的文件名
        preview_filename = f"temp_file.{correct_extension}"
        current_app.logger.info(f"预览文件名生成：原始={original_filename}, MIME={mime_type}, 最终扩展名={correct_extension}")
        
        # 验证明细存在
        detail = ExpenseDetail.query.get_or_404(detail_id)
        
        # 检查权限
        if not can_edit_data(detail.expense, current_user):
            return jsonify({
                'success': False,
                'message': _('您没有权限预览此报销单的发票')
            }), 403
        
        # 使用智能存储系统生成预览文件名
        from app.utils.supabase_client import get_supabase_client
        supabase_client = get_supabase_client()
        
        # 生成规范化文件名（仅预览，不实际保存）
        result = supabase_client._generate_standardized_invoice_name(detail_id, preview_filename)
        
        if result:
            return jsonify({
                'success': True,
                'preview_filename': result['filename'],
                'system_id': result['system_id'],
                'expense_number': result['expense_number'],
                'detail_sequence': f"{result['detail_sequence']:02d}",
                'file_sequence': f"{result['file_sequence']:02d}"
            })
        else:
            return jsonify({
                'success': False,
                'preview_filename': original_filename,
                'message': _('无法生成规范化文件名，将使用原始文件名')
            })
            
    except Exception as e:
        current_app.logger.error(f"预览发票文件名失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': _('预览发票文件名失败')
        }), 500

def _move_temp_file_to_permanent(detail_id, temp_id, filename, temp_url):
    """
    将临时上传的文件转移到正式存储位置
    
    Args:
        detail_id: 明细ID
        temp_id: 临时文件ID
        filename: 文件名
        temp_url: 临时文件URL
        
    Returns:
        正式存储的URL，失败返回None
    """
    try:
        from app.utils.supabase_client import SupabaseStorageClient
        supabase_client = SupabaseStorageClient()
        
        logger.info(f"🔄 开始转移临时文件到正式存储: detail_id={detail_id}, temp_id={temp_id}, filename={filename}")
        
        if supabase_client.use_local_storage:
            # 本地存储：从temp目录移动到正式目录
            return _move_temp_file_local(detail_id, temp_id, filename, temp_url, supabase_client)
        else:
            # 云端存储：从临时路径复制到正式路径
            return _move_temp_file_cloud(detail_id, temp_id, filename, temp_url, supabase_client)
            
    except Exception as e:
        logger.error(f"转移临时文件失败: {e}")
        return None

def _move_temp_file_local(detail_id, temp_id, filename, temp_url, supabase_client):
    """本地存储的临时文件转移"""
    try:
        # 构建临时文件路径
        temp_dir = os.path.join(current_app.static_folder, 'uploads', 'temp', 'invoices')
        temp_file_path = os.path.join(temp_dir, filename)
        
        if not os.path.exists(temp_file_path):
            logger.warning(f"临时文件不存在: {temp_file_path}")
            return None
        
        # 构建正式文件路径
        local_dir_name = supabase_client.get_bucket_name('invoice')
        final_dir = os.path.join(supabase_client.local_storage_root, local_dir_name, f"expense_{detail_id}")
        os.makedirs(final_dir, exist_ok=True)
        
        final_file_path = os.path.join(final_dir, filename)
        
        # 移动文件
        import shutil
        shutil.move(temp_file_path, final_file_path)
        
        # 生成URL
        relative_path = os.path.relpath(final_file_path, current_app.static_folder).replace('\\', '/')
        final_url = url_for('static', filename=relative_path)
        
        logger.info(f"✅ 本地文件转移成功: {temp_file_path} -> {final_file_path}")
        return final_url
        
    except Exception as e:
        logger.error(f"本地文件转移失败: {e}")
        return None

def _move_temp_file_cloud(detail_id, temp_id, filename, temp_url, supabase_client):
    """云端存储的临时文件转移"""
    try:
        bucket_name = supabase_client.get_bucket_name('invoice')
        
        # 构建临时和正式的存储路径
        temp_path = f"temp_expense_invoices/{temp_id}/{filename}"
        
        # 生成正式的标准化路径
        standardized_info = supabase_client._generate_standardized_invoice_name(detail_id, filename)
        if standardized_info:
            final_path = standardized_info['storage_path']
            standardized_filename = standardized_info['filename']
        else:
            final_path = f"expense_invoices/{detail_id}/{filename}"
            standardized_filename = filename
        
        logger.info(f"🔄 云端文件转移: {temp_path} -> {final_path}")
        
        # 从临时位置复制到正式位置
        copy_response = supabase_client.supabase.storage.from_(bucket_name).copy(temp_path, final_path)
        
        if copy_response and not hasattr(copy_response, 'error'):
            # 删除临时文件
            try:
                supabase_client.supabase.storage.from_(bucket_name).remove([temp_path])
                logger.info(f"🗑️ 临时文件已删除: {temp_path}")
            except Exception as e:
                logger.warning(f"删除临时文件失败（但转移已成功）: {e}")
            
            # 生成正式的公开URL
            public_url_response = supabase_client.supabase.storage.from_(bucket_name).get_public_url(final_path)
            
            # 处理URL响应格式
            if hasattr(public_url_response, 'data'):
                final_url = public_url_response.data
            elif hasattr(public_url_response, 'publicUrl'):
                final_url = public_url_response.publicUrl
            elif hasattr(public_url_response, 'url'):
                final_url = public_url_response.url
            elif isinstance(public_url_response, str):
                final_url = public_url_response
            else:
                # 🚨 避免[object Object]，手动构建公开URL
                base_url = supabase_client.supabase_url
                final_url = f"{base_url}/storage/v1/object/public/{bucket_name}/{final_path}"
                logger.warning(f"URL响应格式未知，手动构建公开URL: {final_url}")
                logger.debug(f"响应对象类型: {type(public_url_response)}, 内容: {public_url_response}")
            
            logger.info(f"✅ 云端文件转移成功: {final_url}")
            return final_url
        else:
            logger.error(f"云端文件复制失败: {copy_response}")
            return None
            
    except Exception as e:
        logger.error(f"云端文件转移失败: {e}")
        return None

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


# ==================== 审批流程相关API端点 ====================

@expense.route('/api/approval/<int:expense_id>/templates')
@login_required
def get_approval_templates(expense_id):
    """获取报销单可用的审批模板"""
    try:
        from app.helpers.approval_helpers import get_approval_templates
        
        # 获取报销单对象 - 使用直接查询，然后进行权限检查
        expense_obj = Expense.query.get_or_404(expense_id)
        
        # 检查访问权限
        if not can_edit_data(expense_obj, current_user):
            return jsonify({
                'success': False,
                'message': '您没有权限访问此报销单的审批模板'
            }), 403
        
        # 获取报销单类型的审批模板
        templates = get_approval_templates(object_type='expense', active_only=True)
        
        template_list = []
        if hasattr(templates, 'items'):  # 如果是分页对象
            template_list = [{
                'id': t.id,
                'name': t.name,
                'object_type': t.object_type,
                'required_fields': t.required_fields or []
            } for t in templates.items]
        else:  # 如果是列表
            template_list = [{
                'id': t.id,
                'name': t.name,
                'object_type': t.object_type,
                'required_fields': t.required_fields or []
            } for t in templates]
        
        return jsonify({
            'success': True,
            'templates': template_list
        })
        
    except Exception as e:
        current_app.logger.error(f"获取报销单审批模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取审批模板失败: {str(e)}'
        }), 500


@expense.route('/api/approval/<int:expense_id>/submit', methods=['POST'])
@login_required
@permission_required('expense', 'edit')
def submit_approval(expense_id):
    """提交报销单审批"""
    try:
        from app.helpers.approval_helpers import start_approval_process
        
        # 获取报销单对象
        expense_obj = get_viewable_data(Expense, current_user).filter_by(id=expense_id).first()
        if not expense_obj:
            return jsonify({
                'success': False,
                'message': '报销单不存在或无权限访问'
            }), 404
        
        # 检查是否是报销单创建人
        if not can_edit_data(expense_obj, current_user):
            return jsonify({
                'success': False,
                'message': '只有报销单创建人可以提交审批'
            }), 403
        
        # 检查报销单状态 - 允许草稿和被拒绝的报销单提交审批
        if expense_obj.status not in ['draft', 'rejected']:
            return jsonify({
                'success': False,
                'message': f'报销单当前状态为 {expense_obj.status}，无法提交审批。只有草稿和被拒绝的报销单可以提交审批'
            }), 400
        
        # 获取请求数据
        data = request.get_json() or {}
        template_id = data.get('template_id')
        
        # 如果未指定模板，使用默认模板
        if not template_id:
            from app.models.approval import ApprovalProcessTemplate
            default_template = ApprovalProcessTemplate.query.filter_by(
                object_type='expense',
                is_active=True
            ).first()
            
            if not default_template:
                return jsonify({
                    'success': False,
                    'message': '未找到可用的报销单审批模板'
                }), 400
            
            template_id = default_template.id
        
        # 启动审批流程
        approval_instance = start_approval_process(
            object_type='expense',
            object_id=expense_id,
            template_id=template_id,
            user_id=current_user.id
        )
        
        if not approval_instance:
            return jsonify({
                'success': False,
                'message': '启动审批流程失败'
            }), 500
        
        # 更新报销单状态
        expense_obj.status = 'pending'
        db.session.commit()
        
        current_app.logger.info(f"报销单 {expense_obj.expense_number} 审批流程已启动，实例ID: {approval_instance.id}")
        
        return jsonify({
            'success': True,
            'message': '审批流程已启动',
            'instance_id': approval_instance.id,
            'expense_status': expense_obj.status
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"提交报销单审批失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'提交审批失败: {str(e)}'
        }), 500


@expense.route('/api/approval/<int:expense_id>/recall', methods=['POST'])
@login_required  
@permission_required('expense', 'edit')
def recall_approval(expense_id):
    """召回报销单审批"""
    try:
        from app.helpers.approval_helpers import recall_approval_process
        
        # 获取报销单对象
        expense_obj = get_viewable_data(Expense, current_user).filter_by(id=expense_id).first()
        if not expense_obj:
            return jsonify({
                'success': False,
                'message': '报销单不存在或无权限访问'
            }), 404
        
        # 检查是否是报销单创建人
        if not can_edit_data(expense_obj, current_user):
            return jsonify({
                'success': False,
                'message': '只有报销单创建人可以召回审批'
            }), 403
        
        # 召回审批流程
        success, message = recall_approval_process(
            object_type='expense',
            object_id=expense_id,
            user_id=current_user.id
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': message
            }), 500
        
        # 召回成功，刷新对象状态以获取最新信息
        db.session.refresh(expense_obj)
        
        current_app.logger.info(f"报销单 {expense_obj.expense_number} 审批流程已召回")
        
        return jsonify({
            'success': True,
            'message': message,
            'expense_status': expense_obj.status
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"召回报销单审批失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'召回审批失败: {str(e)}'
        }), 500


@expense.route('/api/approval/<int:expense_id>/resubmit', methods=['POST'])
@login_required
@permission_required('expense', 'edit')
def resubmit_approval(expense_id):
    """重新提交报销单审批"""
    try:
        from app.helpers.approval_helpers import start_approval_process
        
        # 获取报销单对象
        expense_obj = get_viewable_data(Expense, current_user).filter_by(id=expense_id).first()
        if not expense_obj:
            return jsonify({
                'success': False,
                'message': '报销单不存在或无权限访问'
            }), 404
        
        # 检查是否是报销单创建人
        if not can_edit_data(expense_obj, current_user):
            return jsonify({
                'success': False,
                'message': '只有报销单创建人可以重新提交审批'
            }), 403
        
        # 检查报销单状态
        if expense_obj.status not in ['rejected', 'recalled']:
            return jsonify({
                'success': False,
                'message': f'报销单当前状态为 {expense_obj.status}，无法重新提交审批'
            }), 400
        
        # 获取请求数据
        data = request.get_json() or {}
        template_id = data.get('template_id')
        
        # 如果未指定模板，使用默认模板
        if not template_id:  
            from app.models.approval import ApprovalProcessTemplate
            default_template = ApprovalProcessTemplate.query.filter_by(
                object_type='expense',
                is_active=True
            ).first()
            
            if not default_template:
                return jsonify({
                    'success': False,
                    'message': '未找到可用的报销单审批模板'
                }), 400
            
            template_id = default_template.id
        
        # 重新启动审批流程
        approval_instance = start_approval_process(
            object_type='expense',
            object_id=expense_id,
            template_id=template_id,
            user_id=current_user.id
        )
        
        if not approval_instance:
            return jsonify({
                'success': False,
                'message': '重新启动审批流程失败'
            }), 500
        
        # 更新报销单状态
        expense_obj.status = 'pending'
        db.session.commit()
        
        current_app.logger.info(f"报销单 {expense_obj.expense_number} 审批流程已重新提交，实例ID: {approval_instance.id}")
        
        return jsonify({
            'success': True,
            'message': '审批流程已重新提交',
            'instance_id': approval_instance.id,
            'expense_status': expense_obj.status
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"重新提交报销单审批失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'重新提交审批失败: {str(e)}'
        }), 500


@expense.route('/api/approval/<int:expense_id>/flow')
@login_required
def get_expense_approval_flow(expense_id):
    """获取报销单审批流程信息 - 标准化API"""
    try:
        # 获取报销单 - 使用直接查询，然后进行权限检查
        expense_obj = Expense.query.get_or_404(expense_id)
        
        # 检查访问权限
        if not can_edit_data(expense_obj, current_user):
            return jsonify({
                'success': False,
                'message': '您没有权限查看此报销单的审批流程'
            }), 403
        
        # 导入审批相关函数
        from app.helpers.approval_helpers import get_object_approval_instance, can_recall_approval, can_resubmit_approval
        from app.models.approval import ApprovalInstance, ApprovalRecord, ApprovalStep
        
        # 获取审批实例
        approval_instance = get_object_approval_instance('expense', expense_id)
        
        if not approval_instance:
            # 返回控制信息，即使没有审批流程
            control_info = {
                'status': expense_obj.status,
                'can_submit': expense_obj.status == 'draft' and expense_obj.owner_id == current_user.id,
                'can_recall': False,
                'can_resubmit': False
            }
            return jsonify({
                'success': False, 
                'message': '未找到审批流程', 
                'approval_flow': None,
                'control_info': control_info
            })
        
        # 获取审批步骤（从模板获取）
        steps = approval_instance.get_steps()
        if not steps:
            return jsonify({'success': False, 'message': '审批流程配置错误'})
        
        # 获取已有的审批记录
        records = ApprovalRecord.query.filter_by(
            instance_id=approval_instance.id
        ).order_by(ApprovalRecord.timestamp.asc()).all()
        
        # 构建审批阶段数据
        stages_data = []
        # 🔥 修复：获取当前步骤的step_order（current_step存储的是step_id）
        current_step_order = None
        if approval_instance.current_step:
            current_step_obj = ApprovalStep.query.filter_by(id=approval_instance.current_step).first()
            current_step_order = current_step_obj.step_order if current_step_obj else None
        
        for i, step in enumerate(steps):
            # 确定审批人
            from app.helpers.approval_helpers import get_step_actual_approver
            actual_approver = get_step_actual_approver(step, approval_instance)
            
            # 获取这个步骤的审批记录
            # 优先通过step_id匹配，如果没有匹配到则通过审批者匹配
            step_records = []
            
            if step.get('step_id'):
                # 尝试通过step_id匹配
                step_records = [r for r in records if r.step_id == step['step_id']]
            
            # 注释掉错误的兜底逻辑，避免将其他审批流程的记录错误应用到当前步骤
            # 这个逻辑会导致审批人在其他流程中的记录影响当前步骤的状态判断
            # if not step_records and actual_approver:
            #     approver_records = [r for r in records if r.approver_id == actual_approver.id]
            #     if approver_records:
            #         # 按时间排序，通常第一条记录对应该步骤
            #         approver_records.sort(key=lambda x: x.timestamp)
            #         step_records = [approver_records[0]]
            
            stage_data = {
                'id': step['step_id'],
                'stage_name': step['step_name'],  # 修复字段名匹配问题
                'stage_order': step['step_order'],
                'approver_name': actual_approver.real_name if actual_approver else '待确定',
                'approver_id': actual_approver.id if actual_approver else None,
                'status': 'pending',
                'completed_time': None,
                'comment': None,
                'action': None,
                'arrived_at': None,  # 前端期望的字段名
                'can_approve': False
            }
            
            if step_records:
                # 使用最新的记录
                latest_record = step_records[-1]
                stage_data.update({
                    'status': 'approved' if latest_record.action == 'approve' else 'rejected',  # 前端期望的状态值
                    'processed_at': latest_record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # 修复字段名
                    'comment': latest_record.comment,
                    'action': latest_record.action,
                    'approver_name': latest_record.approver.real_name,  # 修复关联字段名
                    'approver_id': latest_record.approver_id
                })
            elif step['step_order'] == current_step_order:
                # 当前步骤 - 使用标准权限检查
                from app.helpers.approval_helpers import can_user_approve
                can_approve = can_user_approve(approval_instance.id, current_user.id)
                
                stage_data.update({
                    'status': 'current',
                    'arrived_at': approval_instance.started_at.strftime('%Y-%m-%d %H:%M:%S'),  # 修复字段名
                    'can_approve': can_approve
                })
                
                # 调试信息：记录can_approve计算过程
                from flask import current_app
                current_app.logger.info("[DEBUG] Step %s can_approve calculation:", step['step_order'])
                current_app.logger.info("  actual_approver: %s", actual_approver)
                current_app.logger.info("  actual_approver.id: %s", actual_approver.id if actual_approver else None)
                current_app.logger.info("  current_user: %s", current_user)  
                current_app.logger.info("  current_user.id: %s", current_user.id)
                current_app.logger.info("  can_approve: %s", can_approve)
            
            stages_data.append(stage_data)
        
        # 确定整体状态
        actual_status = approval_instance.status.value if hasattr(approval_instance.status, 'value') else approval_instance.status
        
        # 检查是否有召回记录
        last_record = records[-1] if records else None
        if last_record and last_record.action == 'recall':
            actual_status = 'recalled'
        
        return jsonify({
            'success': True,
            'approval_flow': {
                'instance_id': approval_instance.id,  # 添加实例ID
                'stages': stages_data,
                'current_stage': current_step_order,  # 使用实例的当前步骤序号
                'can_approve': any(stage.get('can_approve', False) for stage in stages_data),
                'status': actual_status,
                'can_recall': can_recall_approval('expense', expense_id, current_user.id),
                'can_resubmit': can_resubmit_approval('expense', expense_id, current_user.id),
                'is_creator': approval_instance.created_by == current_user.id,
                'creator_id': approval_instance.created_by
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取报销单审批流程失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取审批流程失败: {str(e)}'
        }), 500


@expense.route('/api/approval/<int:expense_id>/editable-fields', methods=['GET'])
@login_required
@permission_required('expense', 'view')
def get_approval_editable_fields(expense_id):
    """获取当前审核阶段可编辑的字段"""
    try:
        from app.helpers.approval_helpers import get_current_approval_step_editable_fields
        
        # 检查报销单是否存在
        expense_obj = Expense.query.get(expense_id)
        if not expense_obj:
            return jsonify({
                'success': False,
                'message': '报销单不存在'
            }), 404
        
        # 获取可编辑字段信息
        edit_info = get_current_approval_step_editable_fields('expense', expense_id, current_user.id)
        
        return jsonify({
            'success': True,
            'data': edit_info
        })
        
    except Exception as e:
        current_app.logger.error(f"获取审核阶段可编辑字段失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取可编辑字段失败: {str(e)}'
        }), 500


@expense.route('/api/approval/<int:expense_id>/update-fields', methods=['POST'])
@login_required
@permission_required('expense', 'edit')
def update_approval_fields(expense_id):
    """在审核阶段更新特定字段（使用通用服务）"""
    try:
        # 检查报销单是否存在
        expense_obj = Expense.query.get(expense_id)
        if not expense_obj:
            return jsonify({
                'success': False,
                'message': '报销单不存在'
            }), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data or 'field_updates' not in data:
            return jsonify({
                'success': False,
                'message': '缺少字段更新数据'
            }), 400
        
        field_updates = data['field_updates']
        if not isinstance(field_updates, dict):
            return jsonify({
                'success': False,
                'message': '字段更新数据格式不正确'
            }), 400
        
        # 使用通用字段编辑服务更新字段
        field_service = get_field_edit_service('expense')
        success, message = field_service.update_fields(expense_id, field_updates, current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
    except Exception as e:
        current_app.logger.error(f"更新审核阶段字段失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新字段失败: {str(e)}'
        }), 500


@expense.route('/api/<int:expense_id>/status')
@login_required
def get_expense_status(expense_id):
    """获取报销单的最新状态信息 - 用于审批后动态更新页面"""
    try:
        # 获取报销单
        expense_obj = Expense.query.get_or_404(expense_id)
        
        # 检查访问权限
        if not can_edit_data(expense_obj, current_user):
            return jsonify({
                'success': False,
                'message': '您没有权限查看此报销单'
            }), 403
        
        # 返回最新状态信息
        return jsonify({
            'success': True,
            'status': expense_obj.status,
            'is_locked': expense_obj.is_locked,
            'updated_at': expense_obj.updated_at.strftime('%Y-%m-%d %H:%M:%S') if expense_obj.updated_at else None,
            'message': '状态获取成功'
        })
        
    except Exception as e:
        current_app.logger.error(f"获取报销单状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500


@expense.route('/download-invoice/<int:detail_id>/<int:invoice_index>')
@login_required
@permission_required('expense', 'view')
def download_invoice(detail_id, invoice_index):
    """下载发票文件 - 支持预览和下载模式"""
    from flask import send_file, abort, request
    import os
    import json
    import urllib.parse
    from app.utils.access_control import can_edit_data
    
    try:
        # 获取报销明细
        expense_detail = ExpenseDetail.query.get_or_404(detail_id)
        
        # 检查权限 - 是否能查看对应的报销单
        if not can_edit_data(expense_detail.expense, current_user):
            flash(_('您没有权限下载此发票'), 'danger')
            abort(403)
        
        # 解析发票图片数据
        invoice_images = []
        if expense_detail.invoice_images:
            try:
                if isinstance(expense_detail.invoice_images, str):
                    invoice_images = json.loads(expense_detail.invoice_images)
                else:
                    invoice_images = expense_detail.invoice_images
            except (json.JSONDecodeError, TypeError):
                current_app.logger.error(f"发票图片数据解析失败: {expense_detail.invoice_images}")
                flash(_('发票数据格式错误'), 'danger')
                abort(400)
        
        # 检查索引是否有效
        if not invoice_images or invoice_index < 0 or invoice_index >= len(invoice_images):
            flash(_('发票不存在'), 'danger')
            abort(404)
        
        invoice_info = invoice_images[invoice_index]
        filename = invoice_info.get('filename', f'invoice_{detail_id}_{invoice_index}')
        file_url = invoice_info.get('url', '')
        
        # 检查是否强制下载模式 - 只有明确请求下载时才强制下载，否则允许预览
        force_download = (request.args.get('download') == '1' or 
                         request.args.get('as_attachment') == 'true')
        
        # 检查是否是预览模式
        is_preview_mode = (request.args.get('view') == 'inline' or 
                          request.args.get('embedded') == 'true' or
                          not force_download)  # 默认为预览模式
        
        # 检查是否是外部云端URL（非本地服务器）
        is_external_url = (file_url.startswith('http') and 
                         not file_url.startswith('http://localhost:') and 
                         not file_url.startswith('http://127.0.0.1:'))
        
        if is_external_url:
            # 对于外部云端文件，使用代理下载确保强制下载
            try:
                import requests
                from io import BytesIO
                
                current_app.logger.info(f"开始代理下载云端文件: {file_url}")
                
                # 从云端下载文件内容
                response = requests.get(file_url, timeout=30)
                response.raise_for_status()
                
                # 获取文件内容
                file_content = BytesIO(response.content)
                file_content.seek(0)
                
                # 确定MIME类型
                file_ext = os.path.splitext(filename)[1].lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg', 
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.pdf': 'application/pdf',
                    '.heic': 'image/heic',
                    '.heif': 'image/heif'
                }
                mimetype = mime_types.get(file_ext, 'application/octet-stream')
                
                current_app.logger.info(f"云端文件代理下载成功，文件大小: {len(response.content)} bytes")
                
                # 根据查询参数决定是否强制下载或预览
                current_app.logger.info(f"云端文件响应模式: {'强制下载' if force_download else '预览模式'}")
                return send_file(
                    file_content,
                    as_attachment=force_download,
                    download_name=filename if force_download else None,
                    mimetype=mimetype
                )
                
            except requests.RequestException as e:
                current_app.logger.error(f"云端文件下载失败: {str(e)}")
                flash(_('云端文件下载失败，请稍后再试'), 'danger')
                abort(500)
            except Exception as e:
                current_app.logger.error(f"代理下载处理失败: {str(e)}")
                flash(_('文件下载处理失败'), 'danger')
                abort(500)
        
        # 处理本地文件
        # 将URL路径转换为本地文件路径
        if file_url.startswith('http://localhost:') or file_url.startswith('http://127.0.0.1:'):
            # 提取URL中的路径部分
            from urllib.parse import urlparse
            parsed_url = urlparse(file_url)
            url_path = parsed_url.path
        else:
            url_path = file_url
        
        if url_path.startswith('/static/uploads/'):
            local_path = url_path.replace('/static/', '')
        elif url_path.startswith('/uploads/'):
            local_path = url_path[1:]  # 去掉开头的 /
        else:
            # 假设是相对路径
            local_path = url_path
        
        file_path = os.path.join(current_app.static_folder, local_path)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            current_app.logger.error(f"发票文件不存在: {file_path}")
            flash(_('发票文件不存在'), 'danger')
            abort(404)
        
        # 确定MIME类型
        file_ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.heic': 'image/heic',
            '.heif': 'image/heif'
        }
        mimetype = mime_types.get(file_ext, 'application/octet-stream')
        
        # 根据查询参数决定是否强制下载或预览
        current_app.logger.info(f"本地文件响应模式: {'强制下载' if force_download else '预览模式'}")
        return send_file(
            file_path,
            as_attachment=force_download,
            download_name=filename if force_download else None,
            mimetype=mimetype
        )
        
    except Exception as e:
        current_app.logger.error(f"下载发票文件失败: {str(e)}")
        flash(_('下载发票文件失败'), 'danger')
        abort(500)