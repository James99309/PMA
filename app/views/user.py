from flask import Blueprint, render_template, render_template_string, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app.models.user import User, Permission, User as UserModel, Affiliation
from app import db
import logging
import json
from datetime import datetime
from app.utils.dictionary_helpers import (
    get_role_display_name,
    get_project_type_options,
    get_project_stage_options,
    get_report_source_options,
    get_industry_options,
    get_company_type_options,
    get_status_options,
    get_business_type_options,
    get_currency_type_options,
    PRODUCT_TYPE_OPTIONS,
    PRODUCT_STATUS_OPTIONS
)
from app.models.dictionary import Dictionary
from app.models.project import Project
from app.models.customer import Company
from app.models.quotation import Quotation
from app.models.role_permissions import RolePermission
from app.utils.access_control import get_viewable_data, can_edit_data
from app.utils.sharing import get_shareable_users_tree
from app.permissions import permission_required
from app.extensions import csrf

logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__)

# API基础URL
API_BASE_URL = "/api/v1"

# ==================== 权限字典辅助函数 ====================
def build_permission_dict(perm_obj):
    """将权限对象转换为标准字典格式

    Args:
        perm_obj: RolePermission 或 Permission 对象

    Returns:
        dict: 包含所有权限字段的标准字典
    """
    return {
        'can_view': getattr(perm_obj, 'can_view', False),
        'can_create': getattr(perm_obj, 'can_create', False),
        'can_edit': getattr(perm_obj, 'can_edit', False),
        'can_delete': getattr(perm_obj, 'can_delete', False),
        'can_change_owner': getattr(perm_obj, 'can_change_owner', False),
        'permission_level': getattr(perm_obj, 'permission_level', 'personal'),
        'permission_level_description': getattr(perm_obj, 'permission_level_description', None),
        'pricing_discount_limit': getattr(perm_obj, 'pricing_discount_limit', None),
        'settlement_discount_limit': getattr(perm_obj, 'settlement_discount_limit', None),
        'content_filters': getattr(perm_obj, 'content_filters', None)
    }

def get_default_permission_dict():
    """返回默认权限字典（所有权限为False/None）

    Returns:
        dict: 默认权限字典
    """
    return {
        'can_view': False,
        'can_create': False,
        'can_edit': False,
        'can_delete': False,
        'can_change_owner': False,
        'permission_level': 'personal',
        'pricing_discount_limit': None,
        'settlement_discount_limit': None,
        'content_filters': None
    }

# ==================== 权限字典辅助函数结束 ====================
# 注意：merge_permission_dicts 函数已删除，现在使用 permission_level 作为判断基准
# - 如果 permission_level 有值 → 使用个人权限
# - 如果 permission_level 为 None → 使用角色权限

def get_auth_headers():
    """获取认证头部信息"""
    # 从session中获取JWT令牌
    token = session.get('jwt_token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}

@user_bp.route('/list')
@login_required
@permission_required('user_management', 'view')
def list_users():
    """用户列表页面（使用标准组件）"""
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', 'active')  # 默认显示已激活用户
    company = request.args.get('company', '')

    # 统一归属过滤
    base_query = get_viewable_data(User, current_user)
    query = base_query

    # 使用性能优化工具
    from app.utils.performance_optimizer import ListPerformanceOptimizer

    if search:
        # 使用优化的搜索查询
        search_fields = ['username', 'real_name', 'email', 'company_name']
        query = ListPerformanceOptimizer.optimize_search_query(
            query, User, search, search_fields
        )
    if role:
        query = query.filter(User.role == role)
    # 状态筛选：active=已激活, inactive=未激活, all=全部
    if status and status != 'all':
        is_active = True if status == 'active' else False
        query = query.filter(User._is_active == is_active)
    if company:
        query = query.filter(User.company_name == company)
    
    # 定义统计字段配置
    stat_fields = [
        {'name': 'total_count', 'condition': None},
        {'name': 'active_count', 'condition': (User._is_active == True)},
        {'name': 'inactive_count', 'condition': (User._is_active == False)},
        {'name': 'admin_count', 'condition': (User.role == 'admin')},
        {'name': 'user_count', 'condition': (User.role == 'user')}
    ]
    
    # 获取优化的统计数据
    stats = ListPerformanceOptimizer.optimize_stats_query(base_query, stat_fields)
    total_count = stats['total_count']
    active_count = stats['active_count'] 
    inactive_count = stats['inactive_count']
    admin_count = stats['admin_count']
    user_count = stats['user_count']

    # 优化列表查询 - 保持无限滚动，但限制最大记录数
    try:
        users = query.order_by(User.updated_at.desc()).limit(1000).all()  # 限制最多1000条记录防止过载
    except Exception as e:
        logger.error(f"用户列表查询失败: {str(e)}")
        db.session.rollback()
        users = []

    # 用户数据已通过 datetimeformat 过滤器处理，无需额外转换

    # 批量获取字典映射
    company_dict = {d.key: d.value for d in Dictionary.query.filter_by(type='company').all()}
    role_dict = {d.key: d.value for d in Dictionary.query.filter_by(type='role').all()}
    
    # 获取实际存在的筛选选项
    actual_roles = db.session.query(User.role).filter(
        User.id.in_([u.id for u in base_query.all()])
    ).distinct().all()
    
    actual_companies = db.session.query(User.company_name).filter(
        User.id.in_([u.id for u in base_query.all()]),
        User.company_name.isnot(None)
    ).distinct().all()

    filter_config = {
        'action_url': url_for('user.list_users'),
        'form_id': 'userFilterForm',
        'reset_url': url_for('user.list_users'),
        
        # 自动筛选配置
        'realtime_search': False,
        'auto_submit': True,
        'dynamic_reset_button': True,
        'adaptive_width': True,
        'adaptive_button_layout': True,
        'search_delay': 300,
        'search_field_id': 'search',  # 添加搜索字段ID
        
        'search_field': {
            'name': 'search',
            'label': '搜索',
            'placeholder': '用户名、姓名、邮箱或企业',
            'value': search,
            'col_width': 4
        },
        
        'filter_fields': [
            {
                'name': 'status',
                'label': _('账号状态'),
                'all_option_text': _('全部状态'),
                'current_value': status,
                'col_width': 2,
                'options': [
                    {'value': 'active', 'label': _('已激活'), 'translate': False},
                    {'value': 'inactive', 'label': _('未激活'), 'translate': False}
                ]
            },
            {
                'name': 'role',
                'label': _('用户角色'),
                'all_option_text': _('全部角色'),
                'current_value': role,
                'col_width': 2,
                'options': [
                    {'value': role_tuple[0], 'label': role_dict.get(role_tuple[0], role_tuple[0]), 'translate': False}
                    for role_tuple in actual_roles if role_tuple[0]
                ]
            },
            {
                'name': 'company',
                'label': _('企业'),
                'all_option_text': _('全部企业'),
                'current_value': company,
                'col_width': 3,
                'options': [
                    {'value': company_tuple[0], 'label': company_dict.get(company_tuple[0], company_tuple[0]), 'translate': False}
                    for company_tuple in actual_companies if company_tuple[0]
                ]
            }
        ],

        'search_button_text': _('搜索'),
        'reset_button_text': _('重置')
    }

    # 直接使用用户对象，让模板自动访问属性
    user_items = users

    # 钉钉绑定标记 - 仅 CN 启用时查询
    dingtalk_bound_ids = set()
    try:
        from app.services.dingtalk import is_dingtalk_enabled
        if is_dingtalk_enabled() and users:
            from app.models.dingtalk import DingtalkUserMapping
            uid_list = [u.id for u in users]
            dingtalk_bound_ids = {
                m.pma_user_id for m in DingtalkUserMapping.query.filter(
                    DingtalkUserMapping.pma_user_id.in_(uid_list),
                    DingtalkUserMapping.is_active == True  # noqa: E712
                ).all()
            }
    except Exception as e:
        logger.warning(f"查询钉钉绑定状态失败: {e}")

    # 构建列表配置
    list_config = {
        'module_name': 'user',
        'title': '账户管理',
        'ajax_mode': True,  # 使用AJAX模式
        
        # 统计卡片配置
        'stats': {
            'cards': [
                {
                    'id': 'total',
                    'title': _('全部用户'),
                    'icon': 'fas fa-users',
                    'value': total_count,
                    'unit': _('个'),
                    'color': 'primary'
                },
                {
                    'id': 'active',
                    'title': _('已激活'),
                    'icon': 'fas fa-user-check',
                    'value': active_count,
                    'unit': _('个'),
                    'color': 'success'
                },
                {
                    'id': 'inactive',
                    'title': _('未激活'),
                    'icon': 'fas fa-user-times',
                    'value': inactive_count,
                    'unit': _('个'),
                    'color': 'warning'
                },
                {
                    'id': 'admin',
                    'title': _('管理员'),
                    'icon': 'fas fa-user-shield',
                    'value': admin_count,
                    'unit': _('个'),
                    'color': 'info'
                }
            ]
        },
        
        # 筛选配置（复用现有筛选组件）
        'filter': filter_config,
        
        # 表格配置
        'table': {
            'ajax_target': 'userTableBody',
            'title': '用户列表',
            'icon': 'fas fa-table',
            'show_header': True,
            'enhanced_striping': True,  # 启用斑马线
            'fixed_height_scroll': False,  # 暂时禁用内部滚动
            'table_name': 'user',        # 指定数据库表名用于动态映射
            'infinite_scroll': {  # 无限滚动配置
                'enabled': True,
                'page_size': 30,  # 增加初始加载数量，确保产生滚动条
                'scroll_threshold': 300,  # 增加触发阈值，更容易触发
                'container_selector': '.table-responsive',
                'scroll_mode': 'window'
            },
            'min_height': 'calc(100vh - 300px)',  # 设置表格最小高度，确保产生滚动条
            'columns': [
                {
                    'key': 'id',
                    'field': 'id',
                    'label': 'ID',
                    'type': 'text',
                    'width': '60px',
                    'sort_type': 'number'
                },
                {
                    'key': 'real_name',
                    'field': 'real_name',
                    'label': _('真实姓名'),
                    'type': 'link',
                    'url_template': '/user/detail/{id}',
                    'width': '120px',
                    'sort_type': 'string'
                },
                {
                    'key': 'username',
                    'field': 'username',
                    'label': _('用户名'),
                    'type': 'text',
                    'width': '120px',
                    'sort_type': 'string'
                },
                {
                    'key': 'is_active',
                    'field': '_is_active',
                    'label': _('状态'),
                    'type': 'badge',
                    'render': 'render_user_status_badge',
                    'width': '120px',
                    'sort_type': 'string'
                },
                {
                    'key': 'email',
                    'field': 'email',
                    'label': _('邮箱地址'),
                    'type': 'text',
                    'width': '200px',
                    'sort_type': 'string'
                },
                {
                    'key': 'company_name',
                    'field': 'company_name',
                    'label': _('企业名称'),
                    'type': 'text',
                    'width': '180px',
                    'sort_type': 'string'
                },
                {
                    'key': 'department',
                    'field': 'department',
                    'label': _('部门'),
                    'type': 'text',
                    'width': '140px',
                    'sort_type': 'string'
                },
                {
                    'key': 'role',
                    'field': 'role',
                    'label': _('角色'),
                    'type': 'badge',
                    'render': 'render_user_role_badge',
                    'width': '120px',
                    'align': 'start',
                    'role_dict': role_dict,
                    'sort_type': 'string'
                },
                {
                    'key': 'updated_at',
                    'field': 'updated_at',
                    'label': _('更新时间'),
                    'type': 'date',
                    'format': 'datetimeformat',
                    'width': '160px',
                    'sort_type': 'date'
                },
                {
                    'key': 'created_at',
                    'field': 'created_at',
                    'label': _('创建时间'),
                    'type': 'date',
                    'format': 'datetimeformat',
                    'width': '160px',
                    'sort_type': 'date'
                }
            ]
        }
    }

    return render_template(
        'user/tw_list.html',
        list_config=list_config,
        items=user_items,
        total_count=total_count,
        role_dict=role_dict,
        dingtalk_bound_ids=dingtalk_bound_ids
    )

@user_bp.route('/api/users/active', methods=['GET'])
@login_required
def get_active_users():
    """获取所有活跃用户列表（简单版本，用于下拉选择器）"""
    try:
        users = User.query.filter(User._is_active.is_(True)).order_by(User.real_name).all()

        return jsonify({
            'success': True,
            'data': [{
                'id': u.id,
                'username': u.username,
                'real_name': u.real_name,
                'role': u.role,
                'role_display': get_role_display_name(u.role) if u.role else '',
                'company_name': u.company_name
            } for u in users]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@user_bp.route('/api/list_ajax', methods=['GET'])
@login_required
@permission_required('user_management', 'view')
def list_users_ajax():
    """用户列表AJAX筛选API"""
    try:
        # 获取所有筛选参数
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        role = request.args.get('role', '')
        company = request.args.get('company', '')
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # 排序参数
        sort_field = request.args.get('sort_field', '')
        sort_direction = request.args.get('sort_direction', 'asc')
        
        # 构建查询
        query = get_viewable_data(User, current_user)
        
        # 应用搜索
        if search:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search}%'),
                    User.real_name.ilike(f'%{search}%'),
                    User.company_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        # 应用角色筛选
        if role:
            query = query.filter(User.role == role)
        
        # 应用公司筛选
        if company:
            query = query.filter(User.company_name == company)
        
        # 应用状态筛选
        if status == 'active':
            query = query.filter(User._is_active == True)
        elif status == 'inactive':
            query = query.filter(User._is_active == False)
        
        # 动态排序
        if sort_field and sort_direction:
            # 映射前端字段名到数据库字段
            field_mapping = {
                'username': User.username,
                'real_name': User.real_name,
                'email': User.email,
                'company_name': User.company_name,
                'role': User.role,
                'is_active': User._is_active,
                'created_at': User.created_at,
                'updated_at': User.updated_at
            }
            
            if sort_field in field_mapping:
                sort_column = field_mapping[sort_field]
                if sort_direction.lower() == 'desc':
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            else:
                # 默认排序
                query = query.order_by(User.updated_at.desc())
        else:
            # 默认排序
            query = query.order_by(User.updated_at.desc())
        
        # 执行查询
        total_count = query.count()
        users = query.offset(offset).limit(limit).all()
        
        # 计算是否还有更多数据
        has_more = (offset + limit) < total_count
        
        # 计算统计数据
        total_query = get_viewable_data(User, current_user)
        total_users = total_query.count()
        active_users = total_query.filter(User._is_active == True).count()
        inactive_users = total_query.filter(User._is_active == False).count()
        
        # 检测移动端并使用智能移动卡片
        from app.utils.mobile_helpers import is_mobile_request
        from types import SimpleNamespace
        
        if users:
            # 格式化用户数据为标准结构
            formatted_results = []
            for user in users:
                # 安全访问用户属性
                real_name = getattr(user, 'real_name', None) or '未设置'
                email = getattr(user, 'email', None) or '未设置'
                department = getattr(user, 'department', None) or '未设置'
                
                # 处理角色显示
                role_key = getattr(user, 'role', None)
                if role_key:
                    role_dict = Dictionary.query.filter_by(type='role', key=role_key, is_active=True).first()
                    role_display = role_dict.value if role_dict else role_key
                else:
                    role_display = '未设置'
                
                # 企业名称
                company_name = getattr(user, 'company_name', None) or getattr(user, 'company', None) or '未设置'
                
                # 用户状态
                is_active = getattr(user, '_is_active', True)
                status_display = '激活' if is_active else '禁用'
                
                # 处理时间
                created_at = getattr(user, 'created_at', None)
                updated_at = getattr(user, 'updated_at', None)
                
                formatted_user = SimpleNamespace(
                    id=user.id,
                    username=user.username,
                    real_name=real_name,
                    email=email,
                    company_name=company_name,
                    department=department,
                    role_display=role_display,
                    role_key=role_key,
                    status_display=status_display,
                    is_active=is_active,
                    created_at=created_at,
                    updated_at=updated_at
                )
                formatted_results.append(formatted_user)
            
            if is_mobile_request():
                # 智能移动卡片配置 - 用户管理
                smart_mobile_card = {
                    'module': 'user',
                    'title_field': {'field': 'username'},
                    'link_url': '/user/detail/{id}',
                    'badges': [
                        {'field': 'status_display', 'renderer': 'user_status'},
                        {'field': 'role_display', 'renderer': 'user_role'}
                    ],
                    'details': [
                        {'field': 'real_name', 'label': '真实姓名'},
                        {'field': 'email', 'label': '邮箱'},
                        {'field': 'company_name', 'label': '所属公司'},
                        {'field': 'department', 'label': '部门'},
                        {'field': 'created_at', 'label': '创建时间', 'format': 'date'},
                        {'field': 'updated_at', 'label': '更新时间', 'format': 'date'}
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
                for user in formatted_results:
                    # 重新生成徽章HTML（用于桌面端）
                    if user.role_key:
                        role_badge = f'<span class="badge badge-pill badge-transparent user-role-{user.role_key}">{user.role_display}</span>'
                    else:
                        role_badge = '<span class="badge badge-pill badge-transparent badge-muted">未设置</span>'
                    
                    if user.is_active:
                        status_badge = '<span class="badge badge-pill badge-transparent user-status-active">激活</span>'
                    else:
                        status_badge = '<span class="badge badge-pill badge-transparent user-status-inactive">禁用</span>'
                    
                    # 处理时间显示
                    if user.created_at:
                        if isinstance(user.created_at, (int, float)):
                            created_time = datetime.fromtimestamp(user.created_at).strftime('%Y-%m-%d %H:%M')
                        else:
                            created_time = user.created_at.strftime('%Y-%m-%d %H:%M')
                    else:
                        created_time = '未知'
                        
                    if user.updated_at:
                        if isinstance(user.updated_at, (int, float)):
                            updated_time = datetime.fromtimestamp(user.updated_at).strftime('%Y-%m-%d %H:%M')
                        else:
                            updated_time = user.updated_at.strftime('%Y-%m-%d %H:%M')
                    else:
                        updated_time = '未知'
                    
                    html_row = f'''
                    <tr>
                        <td>{user.id}</td>
                        <td><a href="/user/detail/{user.id}">{user.username}</a></td>
                        <td>{user.real_name}</td>
                        <td>{status_badge}</td>
                        <td>{user.email}</td>
                        <td>{user.company_name}</td>
                        <td style="text-align: left !important;">{user.department}</td>
                        <td>{role_badge}</td>
                        <td>{updated_time}</td>
                        <td>{created_time}</td>
                    </tr>
                    '''
                    html_rows.append(html_row)
                html = '\n'.join(html_rows)
        else:
            if is_mobile_request():
                html = '<div class="text-center py-4">暂无符合条件的数据</div>'
            else:
                html = '<tr><td colspan="10" class="text-center text-muted py-4">暂无符合条件的数据</td></tr>'
        
        return jsonify({
            'success': True,
            'html': html,
            'total_count': total_count,
            'loaded_count': len(users),
            'has_more': has_more,
            'statistics': {
                'total': total_users,
                'active': active_users,
                'inactive': inactive_users
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'html': f'<tr><td colspan="9" class="text-center text-danger">错误: {str(e)}</td></tr>'
        }), 500

@user_bp.route('/api/list_ajax_full', methods=['GET'])
@login_required
@permission_required('user_management', 'view')
def list_users_ajax_full():
    """用户列表AJAX筛选API"""
    try:
        # 获取所有筛选参数
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        role = request.args.get('role', '')
        company = request.args.get('company', '')
        
        # 分页参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # 构建查询
        query = get_viewable_data(User, current_user)
        
        # 应用搜索
        if search:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search}%'),
                    User.real_name.ilike(f'%{search}%'),
                    User.company_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        # 应用角色筛选
        if role:
            query = query.filter(User.role == role)
        
        # 应用公司筛选
        if company:
            query = query.filter(User.company_name == company)
        
        # 应用状态筛选
        if status == 'active':
            query = query.filter(User._is_active == True)
        elif status == 'inactive':
            query = query.filter(User._is_active == False)
        
        # 排序
        query = query.order_by(User.updated_at.desc())
        
        # 执行查询
        total_count = query.count()
        users = query.offset(offset).limit(limit).all()
        
        # 计算是否还有更多数据
        has_more = (offset + limit) < total_count
        
        # 计算统计数据
        total_query = get_viewable_data(User, current_user)
        total_users = total_query.count()
        active_users = total_query.filter(User._is_active == True).count()
        inactive_users = total_query.filter(User._is_active == False).count()
        
        # 渲染HTML片段
        html_rows = []
        for user in users:
            # 处理时间显示 - 如果是时间戳，转换为datetime再格式化
            if user.created_at:
                if isinstance(user.created_at, (int, float)):
                    created_time = datetime.fromtimestamp(user.created_at).strftime('%Y-%m-%d %H:%M')
                else:
                    created_time = user.created_at.strftime('%Y-%m-%d %H:%M')
            else:
                created_time = '未知'
                
            if user.updated_at:
                if isinstance(user.updated_at, (int, float)):
                    updated_time = datetime.fromtimestamp(user.updated_at).strftime('%Y-%m-%d %H:%M')
                else:
                    updated_time = user.updated_at.strftime('%Y-%m-%d %H:%M')
            else:
                updated_time = '未知'
                
            status_badge = '激活' if user._is_active else '禁用'
            status_class = 'success' if user._is_active else 'secondary'
            
            html_row = f'''
            <tr>
                <td>{user.id}</td>
                <td><a href="/user/detail/{user.id}">{user.username}</a></td>
                <td>{user.real_name or '未设置'}</td>
                <td>{user.company or '未设置'}</td>
                <td>{user.email or '未设置'}</td>
                <td>{user.role or '未设置'}</td>
                <td><span class="badge bg-{status_class}">{status_badge}</span></td>
                <td>{created_time}</td>
                <td>{updated_time}</td>
            </tr>
            '''
            html_rows.append(html_row)
        
        return jsonify({
            'success': True,
            'html': '\n'.join(html_rows),
            'total_count': total_count,
            'loaded_count': len(users),
            'has_more': has_more,
            'statistics': {
                'total': total_users,
                'active': active_users,
                'inactive': inactive_users
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"用户列表AJAX错误: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'html': f'<tr><td colspan="9" class="text-center text-danger">加载失败: {str(e)}</td></tr>'
        }), 500

@user_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('user_management', 'create')
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
        settlement_currency = request.form.get('settlement_currency') or None  # 空字符串转为None
        is_department_manager = 'is_department_manager' in request.form

        # 对角色字段进行去空格处理，防止空格问题
        if role:
            role = role.strip()
        
        logger.info(f"[用户创建] 操作人: {current_user.username}, 参数: username={username}, email={email}, role={role}")
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
        # 试用期(账户级):勾选后读起止日期
        def _form_date(name):
            v = (request.form.get(name) or '').strip()
            if not v:
                return None
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                return None
        prob_on = 'is_probation' in request.form
        prob_start = _form_date('probation_start') if prob_on else None
        prob_end = _form_date('probation_end') if prob_on else None

        user = User(
            username=username,
            real_name=real_name,
            company_name=company_name,
            email=email,
            phone=phone,
            department=department,
            is_department_manager=is_department_manager,
            probation_start=prob_start,
            probation_end=prob_end,
            role=role,
            settlement_currency=settlement_currency,
            is_active=False  # 新建用户默认未激活
        )
        import secrets
        temp_password = secrets.token_urlsafe(12)
        user.set_password(temp_password)
        try:
            db.session.add(user)
            db.session.commit()
            
            # 记录创建历史
            try:
                from app.utils.change_tracker import ChangeTracker
                ChangeTracker.log_create(user)
            except Exception as track_err:
                logger.warning(f"记录用户创建历史失败: {str(track_err)}")
            
            flash('用户创建成功', 'success')
            return redirect(url_for('user.at_user_detail', user_id=user.id))
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"[用户创建] 失败: {str(db_error)}", exc_info=True)
            flash(f'用户创建失败: {str(db_error)}', 'danger')
            return render_template('user/edit.html', user=None, is_edit=False)

@user_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('user_management', 'edit')
def edit_user(user_id):
    """编辑用户页面和处理"""
    # GET请求 - 显示编辑表单
    if request.method == 'GET':
        user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
        if not user:
            flash('用户不存在或无权限编辑', 'danger')
            return redirect(url_for('user.at_list'))
        user_data = user.to_dict()
        return render_template('user/edit.html', user=user_data, is_edit=True)
    # POST请求 - 处理编辑表单提交
    if request.method == 'POST':
        user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
        if not user:
            flash('用户不存在或无权限编辑', 'danger')
            return redirect(url_for('user.at_list'))
        from app.utils.access_control import can_edit_data
        if not can_edit_data(user, current_user):
            flash('无权限编辑该用户', 'danger')
            return redirect(url_for('user.at_list'))
        real_name = request.form.get('real_name')
        company = request.form.get('company')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        role = request.form.get('role')
        settlement_currency = request.form.get('settlement_currency') or None  # 空字符串转为None
        password = request.form.get('password')
        is_active = 'is_active' in request.form
        is_department_manager = 'is_department_manager' in request.form
        # 跨系统镜像 (Federation Lite Phase 1) - 仅 admin 可改
        cross_team_visible = 'cross_team_visible' in request.form
        cross_team_label = (request.form.get('cross_team_label') or '').strip() or None

        # 对角色字段进行去空格处理，防止空格问题
        if role:
            role = role.strip()
        
        logger.info(f"[用户编辑] 操作人: {current_user.username}, 目标用户: {user.username}, 参数: email={email}, role={role}, is_active={is_active}")
        # 邮箱非空校验
        if not email or not email.strip():
            flash('邮箱不能为空', 'danger')
            user_data = user.to_dict()
            return render_template('user/edit.html', user=user_data, is_edit=True)
        email = email.strip()
        
        # 捕获修改前的值
        from app.utils.change_tracker import ChangeTracker
        old_values = ChangeTracker.capture_old_values(user)
        
        old_department = user.department
        old_company = user.company_name
        old_manager = user.is_department_manager
        old_role = user.role  # 记录旧角色
        old_is_active = user.is_active  # 记录旧激活状态，用于触发项目活跃度重算
        # 跨系统镜像状态变化追踪
        old_cross_visible = bool(getattr(user, 'cross_team_visible', False))
        old_pw_hash = user.password_hash

        user.real_name = real_name
        user.company_name = company
        user.email = email
        user.phone = phone
        user.department = department
        user.role = role
        user.settlement_currency = settlement_currency
        user.is_active = is_active
        user.is_department_manager = is_department_manager
        # 试用期(账户级):勾选则存起止日期,取消则清空
        def _form_date2(name):
            v = (request.form.get(name) or '').strip()
            if not v:
                return None
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                return None
        if 'is_probation' in request.form:
            user.probation_start = _form_date2('probation_start')
            user.probation_end = _form_date2('probation_end')
        else:
            user.probation_start = None
            user.probation_end = None
        # 跨系统镜像字段（admin only；mirror 用户本地不允许编辑这两项）
        if not bool(getattr(user, 'is_mirror', False)) and current_user.role == 'admin':
            user.cross_team_visible = cross_team_visible
            user.cross_team_label = cross_team_label
        if password and password.strip():
            user.set_password(password)

        # 检查角色是否发生变化，如果变化则重置个人权限
        if old_role != role:
            logger.info(f"[用户编辑] 用户 {user.username} 角色从 {old_role} 变更为 {role}，重置个人权限")
            # 删除现有的个人权限设置，让系统使用新角色的权限
            Permission.query.filter_by(user_id=user.id).delete()
        
        try:
            db.session.commit()

            # 用户激活状态变化时，刷新其名下项目的活跃度（离职/复职逻辑）
            if old_is_active != is_active:
                from app.utils.activity_tracker import recompute_projects_for_user
                try:
                    n = recompute_projects_for_user(user.id)
                    current_app.logger.info(
                        f"User {user.id} active state changed; recomputed {n} projects"
                    )
                except Exception as e:
                    current_app.logger.exception(
                        f"recompute_projects_for_user failed for user {user.id}: {e}"
                    )

            # 跨系统镜像同步 (Federation Lite Phase 1)
            # 仅本地原生用户（非 mirror）参与对外镜像
            if not bool(getattr(user, 'is_mirror', False)):
                try:
                    from app.services import cross_team_mirror as ctm
                    new_cross = bool(getattr(user, 'cross_team_visible', False))
                    pw_changed = (user.password_hash != old_pw_hash)
                    if not old_cross_visible and new_cross:
                        # 第一次开 → 推送 mirror_user
                        ok, info = ctm.push_mirror(user)
                        if not ok and info.get('code') == 'CONFLICT':
                            # 对端已有同名/同邮箱账号 → 转 promote_to_mirror
                            existing_id = info.get('existing_id')
                            if existing_id:
                                pok, pinfo = ctm.push_promote(user, existing_id)
                                if not pok:
                                    current_app.logger.warning(
                                        f'[cross-team] push_promote failed (existing#{existing_id}): {pinfo}')
                            else:
                                current_app.logger.warning(
                                    f'[cross-team] CONFLICT 无 existing_id, 无法 promote: {info}')
                        elif not ok:
                            current_app.logger.warning(f'[cross-team] push_mirror failed: {info}')
                    elif old_cross_visible and not new_cross:
                        # 取消 → disable mirror
                        ctm.push_disable(user)
                    elif new_cross:
                        # 仍 visible：推送最新 (real_name/email/label/active)，幂等 upsert
                        # mirror_user 已带 is_active 和 password_hash，无需再单独 push_password
                        ctm.push_mirror(user)
                    db.session.commit()  # 持久化 mirrored_at
                except Exception as ce:
                    current_app.logger.exception(f'[cross-team] mirror sync failed: {ce}')

            # 记录变更历史
            try:
                new_values = ChangeTracker.get_new_values(user, old_values.keys())
                ChangeTracker.log_update(user, old_values, new_values)
            except Exception as track_err:
                logger.warning(f"记录用户变更历史失败: {str(track_err)}")
            
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
            return redirect(url_for('user.at_user_detail', user_id=user_id))
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"[用户编辑] 失败: {str(db_error)}", exc_info=True)
            flash(f'更新失败: {str(db_error)}', 'danger')
            user_data = user.to_dict()
            return render_template('user/edit.html', user=user_data, is_edit=True)

@user_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
@permission_required('user_management', 'delete')
def delete_user(user_id):
    """删除用户"""
    # 归属过滤，确保只能删除有权限的用户
    user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
    if not user:
        flash('用户不存在或无权限删除', 'danger')
        return redirect(url_for('user.at_list'))
    # 禁止删除当前登录用户
    if current_user.id == user_id:
        flash('不能删除当前登录用户', 'danger')
        return redirect(url_for('user.at_list'))
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
        Affiliation.query.filter((Affiliation.owner_id == user_id) | (Affiliation.viewer_id == user_id)).delete(synchronize_session=False)
        
        # 记录删除历史
        try:
            from app.utils.change_tracker import ChangeTracker
            ChangeTracker.log_delete(user)
        except Exception as track_err:
            logger.warning(f"记录用户删除历史失败: {str(track_err)}")
        
        db.session.delete(user)
        db.session.commit()
        logger.info(f"[用户删除] 成功，目标用户ID: {user_id}")
        flash('用户删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"[用户删除] 失败: {str(e)}", exc_info=True)
        flash('删除用户时发生错误，请稍后重试', 'danger')
    return redirect(url_for('user.at_list'))

@user_bp.route('/permissions/<int:user_id>', methods=['GET', 'POST'])
@login_required
def manage_permissions(user_id):
    """管理用户权限（优先查个人权限，无则查角色模板）"""
    if request.method == 'GET':
        user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
        if not user:
            flash('用户不存在或无权限查看', 'danger')
            return redirect(url_for('user.at_list'))
        user_data = user.to_dict()
        modules = get_default_modules()
        
        # 获取用户的角色权限
        from app.models.role_permissions import RolePermission
        role_perms = RolePermission.query.filter_by(role=user.role).all()

        # 使用辅助函数构建角色权限字典
        role_permissions = {}
        for perm in role_perms:
            role_permissions[perm.module] = build_permission_dict(perm)

        # 转换角色权限为数组格式（用于前端"恢复角色设置"功能）
        role_permissions_list = []
        for module in modules:
            module_id = module['id']
            perm = role_permissions.get(module_id, get_default_permission_dict())
            perm_copy = perm.copy()
            perm_copy['module'] = module_id
            role_permissions_list.append(perm_copy)

        # 获取用户的个人权限，使用辅助函数构建字典
        personal_perms = list(user.permissions)
        personal_permissions = {}
        for permission in personal_perms:
            personal_permissions[permission.module] = build_permission_dict(permission)

        # 权限加载逻辑：与 user_detail 保持一致
        # - 如果个人权限的 permission_level 有值 → 使用个人权限（完全覆盖角色权限）
        # - 如果 permission_level 为 None 或记录不存在 → 使用角色权限
        permissions = []
        for module in modules:
            module_id = module['id']
            role_perm = role_permissions.get(module_id, get_default_permission_dict())
            personal_perm = personal_permissions.get(module_id)

            if personal_perm and personal_perm.get('permission_level') is not None:
                final_perm = personal_perm.copy()
            else:
                final_perm = role_perm.copy()

            final_perm['module'] = module_id
            permissions.append(final_perm)
        
        # 准备内容筛选配置（配置驱动，支持国际化）
        filter_configs = {
            'project': {
                'project_type': {
                    'label': '项目类型',
                    'options': get_project_type_options()
                },
                'current_stage': {
                    'label': '项目阶段',
                    'options': get_project_stage_options()
                },
                'report_source': {
                    'label': '报备来源',
                    'options': get_report_source_options()
                },
                'industry': {
                    'label': '行业分类',
                    'options': get_industry_options()
                }
            },
            'customer': {
                'company_type': {
                    'label': '企业类型',
                    'options': get_company_type_options()
                },
                'status': {
                    'label': '客户状态',
                    'options': get_status_options()
                },
                'industry': {
                    'label': '行业分类',
                    'options': get_industry_options()  # 复用行业选项
                }
            },
            'product': {
                'type': {
                    'label': '产品类型',
                    'options': PRODUCT_TYPE_OPTIONS
                },
                'status': {
                    'label': '产品状态',
                    'options': PRODUCT_STATUS_OPTIONS
                }
            },
            'quotation': {
                'project_type': {
                    'label': '项目类型',
                    'options': get_project_type_options()
                }
            },
            'pricing_order': {
                'business_type': {
                    'label': '业务类型',
                    'options': get_business_type_options()
                }
            },
            'settlement_order': {
                'business_type': {
                    'label': '业务类型',
                    'options': get_business_type_options()
                }
            }
        }

        ROLE_DICT = {d.key: d.value for d in Dictionary.query.filter_by(type='role').all()}
        return render_template('user/permissions.html',
                             user=user_data,
                             modules=modules,
                             permissions=permissions,
                             role_dict=ROLE_DICT,
                             role_permissions=role_permissions_list,
                             personal_permissions=personal_permissions,
                             filter_configs=filter_configs)
    # POST请求 - 保存权限设置
    if request.method == 'POST':
        try:
            form_data = request.form
            logger.warning(f"[DEBUG] manage_permissions 被调用，收到请求: user_id={user_id}, form_data={form_data}")
            
            user = User.query.get(user_id)
            if not user:
                flash('用户不存在', 'danger')
                return redirect(url_for('user.at_list'))
            
            # 获取用户的角色权限
            from app.models.role_permissions import RolePermission
            role_perms = RolePermission.query.filter_by(role=user.role).all()
            role_permissions_dict = {}
            for rp in role_perms:
                role_permissions_dict[rp.module] = {
                    'can_view': rp.can_view,
                    'can_create': rp.can_create,
                    'can_edit': rp.can_edit,
                    'can_delete': rp.can_delete,
                    'can_change_owner': getattr(rp, 'can_change_owner', False)
                }
            
            permissions = []
            modules = form_data.getlist('module')
            for module in modules:
                # 从前端获取用户想要设置的完整权限状态
                wants_view = f"view_{module}" in form_data
                wants_create = f"create_{module}" in form_data
                wants_edit = f"edit_{module}" in form_data
                wants_delete = f"delete_{module}" in form_data
                wants_change_owner = f"change_owner_{module}" in form_data

                # 获取权限级别设置
                permission_level = form_data.get(f"permission_level_{module}", 'personal')

                # 获取折扣限制
                pricing_limit_str = form_data.get(f"pricing_discount_limit_{module}", '').strip()
                settlement_limit_str = form_data.get(f"settlement_discount_limit_{module}", '').strip()

                pricing_limit = float(pricing_limit_str) if pricing_limit_str else None
                settlement_limit = float(settlement_limit_str) if settlement_limit_str else None

                # 获取内容筛选
                content_filters_str = form_data.get(f"content_filters_{module}", '')
                content_filters = content_filters_str if content_filters_str else None

                # 构建完整的个人权限记录（不做差异过滤，保存完整状态）
                permission = {
                    "module": module,
                    "can_view": wants_view,
                    "can_create": wants_create,
                    "can_edit": wants_edit,
                    "can_delete": wants_delete,
                    "can_change_owner": wants_change_owner,
                    "permission_level": permission_level,
                    "pricing_discount_limit": pricing_limit,
                    "settlement_discount_limit": settlement_limit,
                    "content_filters": content_filters
                }
                permissions.append(permission)
            
            logger.warning(f"[DEBUG] 写入 permissions 表，user_id={user_id}, permissions={permissions}")
            
            # 删除现有个人权限
            Permission.query.filter_by(user_id=user_id).delete()

            # 保存完整的个人权限状态（不过滤，保存所有模块的完整配置）
            for perm in permissions:
                module = perm.get('module')
                permission = Permission(
                    user_id=user_id,
                    module=module,
                    can_view=bool(perm.get('can_view', False)),
                    can_create=bool(perm.get('can_create', False)),
                    can_edit=bool(perm.get('can_edit', False)),
                    can_delete=bool(perm.get('can_delete', False)),
                    can_change_owner=bool(perm.get('can_change_owner', False)),
                    permission_level=perm.get('permission_level', 'personal'),
                    pricing_discount_limit=perm.get('pricing_discount_limit'),
                    settlement_discount_limit=perm.get('settlement_discount_limit'),
                    content_filters=perm.get('content_filters')
                )
                db.session.add(permission)
                
            try:
                db.session.commit()
                logger.warning(f"[DEBUG] permissions 表写入完成，user_id={user_id}")
                flash('用户权限更新成功', 'success')
                return redirect(url_for('user.user_detail', user_id=user_id))
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
    return redirect(url_for('user.at_list'))

@user_bp.route('/affiliations/<int:user_id>')
@login_required
def manage_user_affiliations(user_id):
    """管理用户数据归属权限"""
    if current_user.role != 'admin' and current_user.id != user_id:
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('user.at_list'))
    target_user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
    if not target_user:
        flash('用户不存在或无权限查看', 'danger')
        return redirect(url_for('user.at_list'))
    ROLE_DICT = {d.key: d.value for d in Dictionary.query.filter_by(type='role').all()}

    return render_template('user/affiliations.html',
                           target_user=target_user,
                           role_dict=ROLE_DICT)

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
    if not current_user.has_permission('user_management', 'create'):
        flash('您没有批量导入用户的权限', 'danger')
        return redirect(url_for('user.at_list'))
        
    try:
        # 检查是否有文件上传
        if 'csv_file' not in request.files:
            flash('没有选择文件', 'danger')
            return redirect(url_for('user.at_list'))
            
        file = request.files['csv_file']
        
        # 检查文件名是否为空
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(url_for('user.at_list'))
            
        # 检查文件类型
        if not file.filename.endswith('.csv'):
            flash('只支持CSV文件格式', 'danger')
            return redirect(url_for('user.at_list'))
            
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
                    
                return redirect(url_for('user.at_list'))
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
                return redirect(url_for('user.at_list'))
        else:
            flash('没有用户被导入，请检查CSV文件格式', 'warning')
        
        return redirect(url_for('user.at_list'))
        
    except Exception as e:
        logger.error(f"导入用户时出错: {str(e)}")
        flash(f'导入过程中发生错误: {str(e)}', 'danger')
        return redirect(url_for('user.at_list'))

@user_bp.route('/manage-permissions', methods=['GET', 'POST'])
@login_required
def manage_role_permissions():
    """角色权限设置页面（只操作role_permissions表）"""
    if not current_user.has_permission('permission_management', 'view'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        try:
            data = request.get_json()
            logger.warning(f"[DEBUG] manage_role_permissions 被调用，收到请求: {data}")
            role = data.get('role')
            # 清理角色名称中的空白字符
            if role:
                role = role.strip()
            permissions = data.get('permissions', [])
            logger.warning(f"[DEBUG] 写入 role_permissions 表，role={role}, permissions={permissions}")
            if not role or not permissions:
                return jsonify({'success': False, 'message': '角色名称或权限数据不能为空'}), 400
            if role == 'admin':
                return jsonify({'success': False, 'message': '管理员角色权限不允许修改'}), 403
            
            # 先删除现有权限记录
            deleted_count = RolePermission.query.filter_by(role=role).delete()
            logger.warning(f"[DEBUG] 删除了 {deleted_count} 条 {role} 角色的权限记录")
            
            # 刷新会话以确保删除操作生效
            db.session.flush()
            
            for perm in permissions:
                if not isinstance(perm, dict) or 'module' not in perm or not perm['module']:
                    continue
                # 获取权限状态
                can_view = bool(perm.get('can_view', False))
                can_create = bool(perm.get('can_create', False))
                can_edit = bool(perm.get('can_edit', False))
                can_delete = bool(perm.get('can_delete', False))
                can_change_owner = bool(perm.get('can_change_owner', False))
                
                # 检查是否有任何权限
                has_any_permission = can_view or can_create or can_edit or can_delete or can_change_owner
                
                # 如果没有任何权限，权限级别强制设置为personal
                permission_level = perm.get('permission_level', 'personal')
                if not has_any_permission:
                    permission_level = 'personal'
                
                rp = RolePermission(
                    role=role,
                    module=perm['module'],
                    can_view=can_view,
                    can_create=can_create,
                    can_edit=can_edit,
                    can_delete=can_delete,
                    can_change_owner=can_change_owner,
                    permission_level=permission_level,
                    permission_level_description=perm.get('permission_level_description'),
                    pricing_discount_limit=perm.get('pricing_discount_limit'),
                    settlement_discount_limit=perm.get('settlement_discount_limit'),
                    content_filters=perm.get('content_filters')
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
            # 清理key和value中的空白字符
            roles.append({'key': role_dict.key.strip(), 'value': role_dict.value.strip()})
        modules = get_default_modules()
        modules = [dict(module) for module in modules]
        roles = [dict(role) for role in roles]
        
        # 如果URL中指定了role参数，设置默认选中的角色
        selected_role = request.args.get('role', '')

        # 准备内容筛选配置（配置驱动，支持国际化）
        filter_configs = {
            'project': {
                'project_type': {
                    'label': '项目类型',
                    'options': get_project_type_options()
                },
                'current_stage': {
                    'label': '项目阶段',
                    'options': get_project_stage_options()
                },
                'report_source': {
                    'label': '报备来源',
                    'options': get_report_source_options()
                },
                'industry': {
                    'label': '行业分类',
                    'options': get_industry_options()
                }
            },
            'customer': {
                'company_type': {
                    'label': '企业类型',
                    'options': get_company_type_options()
                },
                'status': {
                    'label': '客户状态',
                    'options': get_status_options()
                },
                'industry': {
                    'label': '行业分类',
                    'options': get_industry_options()  # 复用行业选项
                }
            },
            'product': {
                'type': {
                    'label': '产品类型',
                    'options': PRODUCT_TYPE_OPTIONS
                },
                'status': {
                    'label': '产品状态',
                    'options': PRODUCT_STATUS_OPTIONS
                }
            },
            'quotation': {
                'project_type': {
                    'label': '项目类型',
                    'options': get_project_type_options()
                }
            },
            'pricing_order': {
                'business_type': {
                    'label': '业务类型',
                    'options': get_business_type_options()
                }
            },
            'settlement_order': {
                'business_type': {
                    'label': '业务类型',
                    'options': get_business_type_options()
                }
            }
        }

        return render_template('user/role_permissions.html',
                             roles=roles,
                             modules=modules,
                             selected_role=selected_role,
                             filter_configs=filter_configs)
    except Exception as e:
        logger.error(f"加载角色权限设置页面时出错: {str(e)}")
        flash('加载角色权限设置页面时出错，请稍后重试', 'danger')
        return redirect(url_for('user.at_list'))

@user_bp.route('/manage-roles', methods=['GET'])
@login_required
def manage_roles():
    """角色字典管理页面（管理dictionaries表中type=role的记录）"""
    if not current_user.has_permission('dictionary_management', 'view'):
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
        return redirect(url_for('user.at_list'))

@user_bp.route('/manage-companies', methods=['GET'])
@login_required
def manage_companies():
    """企业字典管理页面（管理dictionaries表中type=company的记录）"""
    if not current_user.has_permission('dictionary_management', 'view'):
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
        return redirect(url_for('user.at_list'))

@user_bp.route('/manage-departments', methods=['GET'])
@login_required
def manage_departments():
    """部门管理页面（管理 Department 表）"""
    if not current_user.has_permission('dictionary_management', 'view'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))

    try:
        from app.models.expense import Department

        # 获取所有部门，按公司和名称排序
        departments = Department.query.order_by(Department.company_name, Department.name).all()

        # 获取所有公司列表（从用户表）
        companies = db.session.query(User.company_name).filter(
            User.company_name.isnot(None),
            User.company_name != ''
        ).distinct().order_by(User.company_name).all()
        company_list = [c[0] for c in companies]

        # 获取所有可选的用户（用于设置负责人）
        users = User.query.filter(
            User._is_active == True
        ).order_by(User.company_name, User.real_name).all()

        # HRBP 候选(人事经理角色;下拉过滤用)
        hr_users = [u for u in users if u.role == 'hr_manager']

        return render_template('user/tw_department_management.html',
                               departments=departments,
                               companies=company_list,
                               users=users,
                               hr_users=hr_users)
    except Exception as e:
        logger.error(f"加载部门管理页面时出错: {str(e)}")
        flash('加载部门管理页面时出错，请稍后重试', 'danger')
        return redirect(url_for('user.at_list'))


@user_bp.route('/api/departments', methods=['GET'])
@login_required
def api_get_departments():
    """获取部门列表 API"""
    from app.models.expense import Department

    company_name = request.args.get('company_name')
    query = Department.query

    if company_name:
        query = query.filter_by(company_name=company_name)

    departments = query.order_by(Department.name).all()

    return jsonify({
        'success': True,
        'data': [{
            'id': d.id,
            'name': d.name,
            'code': d.code,
            'company_name': d.company_name,
            'manager_id': d.manager_id,
            'manager_name': d.manager.real_name if d.manager else None,
            'hrbp_user_id': d.hrbp_user_id,
            'hrbp_name': (d.hrbp.real_name or d.hrbp.username) if d.hrbp else None,
            'is_active': d.is_active
        } for d in departments]
    })


@user_bp.route('/api/departments', methods=['POST'])
@login_required
def api_create_department():
    """创建部门 API"""
    if not current_user.has_permission('dictionary_management', 'edit'):
        return jsonify({'success': False, 'message': '无权限'}), 403

    from app.models.expense import Department

    data = request.get_json()
    name = data.get('name', '').strip()
    company_name = data.get('company_name', '').strip()
    manager_id = data.get('manager_id')

    if not name or not company_name:
        return jsonify({'success': False, 'message': '部门名称和公司不能为空'})

    # 检查是否已存在
    existing = Department.query.filter_by(name=name, company_name=company_name).first()
    if existing:
        return jsonify({'success': False, 'message': '该公司已存在同名部门'})

    # 生成代码
    code = f"{name[:10]}_{company_name[:4]}"

    hrbp_user_id = data.get('hrbp_user_id')
    dept = Department(
        name=name,
        code=code,
        company_name=company_name,
        manager_id=int(manager_id) if manager_id else None,
        hrbp_user_id=int(hrbp_user_id) if hrbp_user_id else None,
        is_active=True
    )
    db.session.add(dept)
    db.session.commit()

    return jsonify({'success': True, 'message': '部门创建成功', 'id': dept.id})


@user_bp.route('/api/departments/<int:dept_id>', methods=['PUT'])
@login_required
def api_update_department(dept_id):
    """更新部门 API"""
    if not current_user.has_permission('dictionary_management', 'edit'):
        return jsonify({'success': False, 'message': '无权限'}), 403

    from app.models.expense import Department

    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({'success': False, 'message': '部门不存在'})

    data = request.get_json()

    if 'name' in data:
        dept.name = data['name'].strip()
    if 'manager_id' in data:
        dept.manager_id = int(data['manager_id']) if data['manager_id'] else None
    if 'hrbp_user_id' in data:
        dept.hrbp_user_id = int(data['hrbp_user_id']) if data['hrbp_user_id'] else None
    if 'is_active' in data:
        dept.is_active = data['is_active']

    db.session.commit()

    return jsonify({'success': True, 'message': '部门更新成功'})


@user_bp.route('/api/departments/<int:dept_id>', methods=['DELETE'])
@login_required
def api_delete_department(dept_id):
    """删除部门 API"""
    if not current_user.has_permission('dictionary_management', 'edit'):
        return jsonify({'success': False, 'message': '无权限'}), 403

    from app.models.expense import Department

    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({'success': False, 'message': '部门不存在'})

    # 检查是否有用户归属此部门
    users_in_dept = User.query.filter_by(department=dept.name, company_name=dept.company_name).count()
    if users_in_dept > 0:
        return jsonify({'success': False, 'message': f'该部门下有 {users_in_dept} 个用户，无法删除'})

    db.session.delete(dept)
    db.session.commit()

    return jsonify({'success': True, 'message': '部门删除成功'})

def get_default_modules():
    """获取默认模块列表（数据库驱动，与配置管理保持一致）"""
    from app.views.config_management import get_ordered_modules
    return get_ordered_modules()

@user_bp.route('/detail/<int:user_id>')
@login_required
def user_detail(user_id):
    """用户详情页，展示基本信息、权限、归属关系，分选项卡"""
    user = get_viewable_data(User, current_user).filter(User.id == user_id).first()
    if not user:
        flash('用户不存在或无权限查看', 'danger')
        return redirect(url_for('user.at_list'))
    
    # 检查用户是否为厂商用户
    is_vendor = user.is_vendor_user()
    
    # 获取所有模块
    modules = get_default_modules()
    
    # 获取用户的角色权限
    from app.models.role_permissions import RolePermission
    role_perms = RolePermission.query.filter_by(role=user.role).all()

    # 使用辅助函数构建角色权限字典
    role_permissions = {}
    for perm in role_perms:
        role_permissions[perm.module] = build_permission_dict(perm)

    # 转换角色权限为数组格式（用于前端），确保包含所有模块
    role_permissions_list = []
    for module in modules:
        module_id = module['id']
        perm = role_permissions.get(module_id, get_default_permission_dict())
        perm_copy = perm.copy()
        perm_copy['module'] = module_id
        role_permissions_list.append(perm_copy)

    # 获取用户的个人权限，使用辅助函数构建字典
    personal_perms = list(user.permissions) if hasattr(user, 'permissions') else []
    personal_permissions = {}
    for permission in personal_perms:
        personal_permissions[permission.module] = build_permission_dict(permission)

    # 权限加载逻辑：使用 permission_level 作为判断基准
    # - 如果 permission_level 有值 → 使用个人权限（完全覆盖角色权限）
    # - 如果 permission_level 为 None 或记录不存在 → 使用角色权限
    permissions = []
    for module in modules:
        module_id = module['id']
        # 获取角色权限和个人权限
        role_perm = role_permissions.get(module_id, get_default_permission_dict())
        personal_perm = personal_permissions.get(module_id)  # 不存在时返回 None

        # 判断基准：permission_level 是否为 None
        if personal_perm and personal_perm.get('permission_level') is not None:
            # permission_level 有值 → 使用个人权限（完全覆盖）
            final_perm = personal_perm.copy()
            final_perm['is_using_role_default'] = False
        else:
            # permission_level 为 None 或记录不存在 → 使用角色权限
            final_perm = role_perm.copy()
            final_perm['is_using_role_default'] = True

        final_perm['module'] = module_id
        permissions.append(final_perm)
    affiliation_users = []
    aff_qs = Affiliation.query.filter_by(viewer_id=user.id).all()
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

    # 准备归属关系模态框数据（复用共享组件）
    users_tree = get_shareable_users_tree(current_user, 'user')

    # 计算部门默认可见用户（部门经理可见本部门成员）
    dept_default_users = []
    if user.is_department_manager and user.department and user.company_name:
        dept_members = User.query.filter(
            User.department == user.department,
            User.company_name == user.company_name,
            User.id != user.id,
            User._is_active == True
        ).all()
        for member in dept_members:
            dept_default_users.append({
                'id': member.id,
                'user_id': member.id,
                'username': member.username,
                'real_name': member.real_name,
                'name': member.real_name or member.username,
                'initials': ((member.real_name or member.username) or '?')[:2],
                'department': member.department,
                'company_name': member.company_name,
                'role': member.role,
                'is_department_manager': member.is_department_manager
            })

    # 获取已归属用户（排除部门默认用户，用于模态框）
    dept_default_ids = [u['id'] for u in dept_default_users]
    affiliated_users_for_modal = []
    for aff in aff_qs:
        if aff.owner_id not in dept_default_ids:
            owner = UserModel.query.get(aff.owner_id)
            if owner:
                affiliated_users_for_modal.append({
                    'id': owner.id,
                    'name': owner.real_name or owner.username,
                    'initials': ((owner.real_name or owner.username) or '?')[:2]
                })

    # 准备内容筛选配置（配置驱动，支持国际化）
    filter_configs = {
        'project': {
            'project_type': {
                'label': '项目类型',
                'options': get_project_type_options()
            },
            'current_stage': {
                'label': '项目阶段',
                'options': get_project_stage_options()
            },
            'report_source': {
                'label': '报备来源',
                'options': get_report_source_options()
            },
            'industry': {
                'label': '行业分类',
                'options': get_industry_options()
            }
        },
        'customer': {
            'company_type': {
                'label': '企业类型',
                'options': get_company_type_options()
            },
            'status': {
                'label': '客户状态',
                'options': get_status_options()
            },
            'industry': {
                'label': '行业分类',
                'options': get_industry_options()  # 复用行业选项
            }
        },
        'product': {
            'type': {
                'label': '产品类型',
                'options': PRODUCT_TYPE_OPTIONS
            },
            'status': {
                'label': '产品状态',
                'options': PRODUCT_STATUS_OPTIONS
            }
        },
        'quotation': {
            'project_type': {
                'label': '项目类型',
                'options': get_project_type_options()
            }
        },
        'pricing_order': {
            'business_type': {
                'label': '业务类型',
                'options': get_business_type_options()
            }
        },
        'settlement_order': {
            'business_type': {
                'label': '业务类型',
                'options': get_business_type_options()
            }
        }
    }

    role_dict = {d.key: d.value for d in Dictionary.query.filter_by(type='role').all()}

    # 绩效权限：所有人都能看自己或有权访问用户的绩效
    # 已经通过 get_viewable_data 验证了用户访问权限，所以可以查看绩效
    can_view_performance = True

    # 绩效编辑权限：管理员或有配置管理权限
    can_edit_performance = (
        current_user.role == 'admin' or
        current_user.has_permission('config_management', 'edit')
    )

    # 计算用户管理编辑权限
    can_edit_user = current_user.has_permission('user_management', 'edit')

    # 计算薪资管理权限
    # 薪资查看权限：管理员或有user_management的view权限
    # 注：用户已通过 get_viewable_data 验证访问权限，能进入此页面说明已有权限
    can_view_salary = (
        current_user.role == 'admin' or
        current_user.has_permission('user_management', 'view')
    )
    # 薪资编辑权限：管理员或有user_management的edit权限
    can_edit_salary = (
        current_user.role == 'admin' or
        current_user.has_permission('user_management', 'edit')
    )

    # 默认使用TW模板（Tailwind版本）
    template = 'user/tw_detail.html'

    # 当前年份（用于绩效看板）
    current_year = datetime.now().year

    # 获取用户的AI分析启用状态
    ai_enabled = False
    try:
        from app.models.salary_config import EmployeeSalaryConfig
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id).first()
        ai_enabled = employee_config.ai_analysis_enabled if employee_config else False
    except Exception as e:
        logger.warning(f"获取用户AI启用状态失败: {e}")
        ai_enabled = False

    # 计算上一个/下一个用户ID（用于导航）
    all_user_ids = get_viewable_data(User, current_user).filter(
        User._is_active == True
    ).order_by(User.real_name.asc(), User.username.asc()).with_entities(User.id).all()
    user_ids = [u.id for u in all_user_ids]
    current_index = user_ids.index(user_id) if user_id in user_ids else -1
    prev_user_id = user_ids[current_index - 1] if current_index > 0 else None
    next_user_id = user_ids[current_index + 1] if current_index < len(user_ids) - 1 else None

    return render_template(
        template,
        user=user,
        permissions=permissions,
        role_permissions=role_permissions_list,  # 传递数组格式给前端
        personal_permissions=personal_permissions,
        filter_configs=filter_configs,
        affiliations=affiliations,
        role_dict=role_dict,
        modules=modules,
        is_vendor=is_vendor,
        can_view_performance=can_view_performance,
        can_edit_performance=can_edit_performance,
        can_edit_user=can_edit_user,
        can_view_salary=can_view_salary,
        can_edit_salary=can_edit_salary,
        current_year=current_year,
        # 归属关系模态框数据
        users_tree=users_tree,
        dept_default_users=dept_default_users,
        affiliated_users_for_modal=affiliated_users_for_modal,
        # 上一个/下一个用户导航
        prev_user_id=prev_user_id,
        next_user_id=next_user_id,
        # AI功能状态
        ai_enabled=ai_enabled
    )

@user_bp.route('/batch-delete', methods=['POST'])
@login_required
def batch_delete_users():
    """批量删除用户：无数据可物理删除，有数据则改为未激活"""
    try:
        # 兼容表单和JSON两种请求
        if request.is_json:
            data = request.get_json()
            user_ids = data.get('user_ids', [])
        else:
            # 表单方式，user_ids为多个同名字段
            user_ids = request.form.getlist('user_ids')
            
        if not user_ids or not isinstance(user_ids, list):
            return jsonify({'success': False, 'message': '未指定要删除的用户', 'data': None}), 400
            
        # 转换为整数
        try:
            user_ids = [int(uid) for uid in user_ids]
        except Exception:
            return jsonify({'success': False, 'message': '用户ID格式错误', 'data': None}), 400
            
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
        
        # 判断请求类型，返回JSON或重定向
        if request.is_json:
            return jsonify({'success': True, 'message': '批量删除完成', 'data': {'deleted': deleted, 'deactivated': deactivated}})
        else:
            flash(f'批量删除完成，已删除: {deleted}，已禁用: {deactivated}', 'success')
            return redirect(url_for('user.at_list'))
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"[批量用户删除] 失败: {str(e)}", exc_info=True)
        
        if request.is_json:
            return jsonify({'success': False, 'message': str(e), 'data': None}), 500
        else:
            flash(f'批量删除失败: {str(e)}', 'danger')
            return redirect(url_for('user.at_list'))

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
        
        # 对角色字段进行去空格处理，防止空格问题
        if role:
            role = role.strip()
        
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
        
        # 对角色字段进行去空格处理，防止空格问题
        if role:
            role = role.strip()
        
        logger.info(f"[API用户编辑] 操作人: {current_user.username}, 目标用户: {user.username}, 参数: email={email}, role={role}")
        if not email or not email.strip():
            logger.warning(f"[API用户编辑] 邮箱为空，操作人: {current_user.username}")
            return jsonify({'success': False, 'message': '邮箱不能为空', 'data': None}), 400
        email = email.strip()
        old_department = user.department
        old_company = user.company_name
        old_manager = user.is_department_manager
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

        # 处理管理部门关系
        managed_department_ids = data.get('managed_department_ids', [])
        if managed_department_ids is not None:
            from app.models.expense import Department
            # 获取当前用户管理的所有部门
            current_managed = Department.query.filter_by(manager_id=user.id).all()
            current_managed_ids = [d.id for d in current_managed]

            # 移除不再管理的部门
            for dept in current_managed:
                if dept.id not in managed_department_ids:
                    dept.manager_id = None

            # 添加新管理的部门
            for dept_id in managed_department_ids:
                if dept_id not in current_managed_ids:
                    dept = Department.query.get(dept_id)
                    if dept:
                        dept.manager_id = user.id

            logger.info(f"[API用户编辑] 管理部门更新，用户: {user.username}, 部门IDs: {managed_department_ids}")

        # 移除嵌套的try，整合成单一try-except结构
        db.session.commit()
        from app.models.user import sync_department_manager_affiliations, remove_department_manager_affiliations, sync_affiliations_for_new_member, transfer_member_affiliations_on_department_change
        # 负责人变为True
        if not old_manager and is_department_manager:
            sync_department_manager_affiliations(user)
        # 负责人变为False
        elif old_manager and not is_department_manager:
            remove_department_manager_affiliations(user)
        # 部门或公司变更，且仍为负责人
        elif is_department_manager and (old_department != department or old_company != company_name):
            remove_department_manager_affiliations(user)
            sync_department_manager_affiliations(user)
        # 普通成员变更部门/公司，自动为新部门负责人添加归属，并同步转移归属
        if (old_department != department or old_company != company_name) and not is_department_manager:
            transfer_member_affiliations_on_department_change(user, old_department, old_company)
        
        logger.info(f"[API用户编辑] 成功，目标用户: {user.username}")
        return jsonify({'success': True, 'message': '用户信息更新成功', 'data': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"[API用户编辑] 失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}', 'data': None}), 500

@user_bp.route('/send-invitation/<int:user_id>', methods=['POST'])
@login_required
def send_invitation(user_id):
    """发送用户邀请邮件，仅限未激活用户"""
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('user.at_list'))
    if user.is_active:
        flash('该用户已激活，无需发送邀请邮件', 'info')
        return redirect(url_for('user.user_detail', user_id=user_id))
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
    return redirect(url_for('user.user_detail', user_id=user_id))

# 直接从数据库获取已选用户，不经过API
@user_bp.route('/api/get_selected_users/<int:user_id>', methods=['GET'])
@login_required
def get_selected_users_api(user_id):
    """获取用户已有的归属关系，用于前端显示"""
    try:
        # 权限检查
        if current_user.role != 'admin' and current_user.id != user_id and not current_user.has_permission('user_management', 'view'):
            return jsonify({
                'success': False,
                'message': '无权限访问此数据',
                'data': []
            }), 403
        from app.helpers.hrbp_helpers import hrbp_denies
        if hrbp_denies(current_user, user_id):
            return jsonify({'success': False, 'message': '只能查看你负责部门的成员归属', 'data': []}), 403

        # 获取已有归属关系
        affiliations = Affiliation.query.filter_by(viewer_id=user_id).all()
        result = []
        
        for affiliation in affiliations:
            owner = UserModel.query.get(affiliation.owner_id)
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

@user_bp.route('/api/save_affiliations/<int:user_id>', methods=['POST'])
@login_required
def save_affiliations_api(user_id):
    """保存用户归属关系，直接操作数据库"""
    try:
        # 权限检查
        if current_user.role != 'admin' and current_user.id != user_id and not current_user.has_permission('user_management', 'edit'):
            return jsonify({
                'success': False,
                'message': '无权限操作此数据'
            }), 403
        # HRBP 范围隔离:人事经理只能配置负责部门成员的归属
        from app.helpers.hrbp_helpers import hrbp_denies
        if hrbp_denies(current_user, user_id):
            return jsonify({'success': False, 'message': '只能配置你负责部门的成员归属'}), 403

        # 检查用户是否存在
        target_user = UserModel.query.get(user_id)
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
                    owner = UserModel.query.get(owner_id)
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

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """用户个人设置页面，包括账户详情、权限和数据归属"""
    user = User.query.get(current_user.id)
    if not user:
        flash(_('找不到用户信息'), 'danger')
        return redirect(url_for('main.index'))
        
    # 处理表单提交
    if request.method == 'POST':
        real_name = request.form.get('real_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        settlement_currency = request.form.get('settlement_currency') or None

        # 邮箱非空校验
        if not email or not email.strip():
            flash(_('邮箱不能为空'), 'danger')
            return render_template('user/profile.html', user=user)

        # 检查邮箱是否已被其他用户使用
        email = email.strip()
        existing_user = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_user:
            flash(_('此邮箱已被其他账户使用'), 'danger')
            return render_template('user/profile.html', user=user)

        # 更新用户信息
        user.real_name = real_name
        user.email = email
        user.phone = phone
        user.settlement_currency = settlement_currency
        
        try:
            db.session.commit()
            flash(_('个人信息更新成功'), 'success')
            return redirect(url_for('user.profile'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"个人信息更新失败: {str(e)}", exc_info=True)
            flash(_('更新失败') + f': {str(e)}', 'danger')
            
    # 获取用户权限信息（包含权限级别等完整信息）
    # 首先获取角色权限作为基础
    from app.models.role_permissions import RolePermission
    role_perms = RolePermission.query.filter_by(role=user.role).all()
    role_permissions = {}
    for perm in role_perms:
        role_permissions[perm.module] = {
            'can_view': perm.can_view,
            'can_create': perm.can_create,
            'can_edit': perm.can_edit,
            'can_delete': perm.can_delete,
            'permission_level': perm.permission_level or 'personal',
            'permission_level_description': perm.permission_level_description,
            'pricing_discount_limit': perm.pricing_discount_limit,
            'settlement_discount_limit': perm.settlement_discount_limit
        }
    
    # 然后获取个人权限
    personal_perms = list(user.permissions) if hasattr(user, 'permissions') else []
    personal_permissions = {}
    for perm in personal_perms:
        personal_permissions[perm.module] = {
            'can_view': perm.can_view,
            'can_create': perm.can_create,
            'can_edit': perm.can_edit,
            'can_delete': perm.can_delete,
            'permission_level': perm.permission_level or 'personal',
            'permission_level_description': perm.permission_level_description,
            'pricing_discount_limit': perm.pricing_discount_limit,
            'settlement_discount_limit': perm.settlement_discount_limit
        }
    
    # 获取所有模块
    modules = get_default_modules()
    permissions = []
    
    # 为每个模块生成最终权限
    for module in modules:
        module_id = module['id']
        role_perm = role_permissions.get(module_id)
        personal_perm = personal_permissions.get(module_id)
        
        if role_perm:
            # 如果角色权限中有此模块，使用角色权限作为基础，个人权限可以增强
            final_perm = {
                'module': module_id,
                'can_view': role_perm['can_view'] or (personal_perm['can_view'] if personal_perm else False),
                'can_create': role_perm['can_create'] or (personal_perm['can_create'] if personal_perm else False),
                'can_edit': role_perm['can_edit'] or (personal_perm['can_edit'] if personal_perm else False),
                'can_delete': role_perm['can_delete'] or (personal_perm['can_delete'] if personal_perm else False),
                # 权限级别：个人权限设置 > 角色权限设置
                'permission_level': (personal_perm['permission_level'] if personal_perm and personal_perm['permission_level'] else role_perm['permission_level']),
                'permission_level_description': (personal_perm['permission_level_description'] if personal_perm else role_perm['permission_level_description']),
                'pricing_discount_limit': (personal_perm['pricing_discount_limit'] if personal_perm and personal_perm['pricing_discount_limit'] is not None else role_perm['pricing_discount_limit']),
                'settlement_discount_limit': (personal_perm['settlement_discount_limit'] if personal_perm and personal_perm['settlement_discount_limit'] is not None else role_perm['settlement_discount_limit'])
            }
        elif personal_perm:
            # 如果角色权限中没有此模块，但个人权限中有，使用个人权限
            final_perm = {
                'module': module_id,
                'can_view': personal_perm['can_view'],
                'can_create': personal_perm['can_create'],
                'can_edit': personal_perm['can_edit'],
                'can_delete': personal_perm['can_delete'],
                'permission_level': personal_perm['permission_level'],
                'permission_level_description': personal_perm['permission_level_description'],
                'pricing_discount_limit': personal_perm['pricing_discount_limit'],
                'settlement_discount_limit': personal_perm['settlement_discount_limit']
            }
        else:
            # 如果角色权限和个人权限中都没有此模块，默认为关闭状态
            final_perm = {
                'module': module_id,
                'can_view': False,
                'can_create': False,
                'can_edit': False,
                'can_delete': False,
                'permission_level': 'personal',
                'permission_level_description': None,
                'pricing_discount_limit': None,
                'settlement_discount_limit': None
            }
        
        permissions.append(final_perm)
            
    # 获取用户归属关系信息
    affiliation_users = []
    aff_qs = Affiliation.query.filter_by(viewer_id=user.id).all()
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
    
    ROLE_DICT = {d.key: d.value for d in Dictionary.query.filter_by(type='role').all()}
    MODULES = get_default_modules()
    
    affiliations = {
        'department': user.department or '未设置',
        'affiliation_users': affiliation_users,
        'affiliation_count': len(affiliation_users)
    }
    
    return render_template('user/tw_profile.html', user=user, permissions=permissions,
                          affiliations=affiliations, role_dict=ROLE_DICT, modules=MODULES,
                          currency_options=get_currency_type_options()) 

# ==================== Claude AI 代理（cliproxy 集成）====================

def _assert_admin():
    """非管理员直接返回 403 响应，调用方 return 该返回值即可。返回 None 表示通过。"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '仅管理员可操作'}), 403
    return None


def _assert_ai_access(user_id, need_edit=False):
    """Claude AI 代理管理放行:个人配置 pc_ai 功能开关驱动(admin 恒通过,否则需
    person_config 权限 + pc_ai + 目标在数据范围内)。返回 403 响应或 None。"""
    from app.views.performance_config import can_access_person_tab
    if not can_access_person_tab(user_id, 'pc_ai', need_edit=need_edit):
        return jsonify({'success': False, 'message': '无权限'}), 403
    return None

@user_bp.route('/api/<int:user_id>/claude-ai', methods=['GET'])
@login_required
def api_claude_ai_get(user_id):
    """获取某用户的 Claude AI 代理状态 + 用量摘要 + 设备锁定状态"""
    err = _assert_ai_access(user_id)
    if err: return err
    from app.services.ai_proxy_service import get_user_usage_summary, default_quota, get_device_lock_status
    user = User.query.get_or_404(user_id)
    usage = get_user_usage_summary(user_id)
    locked_device_id = get_device_lock_status(user.claude_ai_token) if user.claude_ai_token else None
    return jsonify({
        'enabled': bool(user.claude_ai_enabled),
        'has_token': bool(user.claude_ai_token),
        'token_preview': (user.claude_ai_token[:14] + '…') if user.claude_ai_token else None,
        'token': user.claude_ai_token if user.id == current_user.id else None,  # 仅本人可见明文
        'quota': int(user.claude_ai_quota_tokens or 0),
        'effective_quota': int(user.claude_ai_quota_tokens or default_quota()),
        'default_quota': default_quota(),
        'enabled_at': user.claude_ai_enabled_at.strftime('%Y-%m-%d %H:%M') if user.claude_ai_enabled_at else None,
        'is_active': user.is_active,
        'has_email': bool(user.email),
        'usage': usage,
        'locked_device_id': locked_device_id,
    })


@user_bp.route('/api/<int:user_id>/claude-ai/enable', methods=['POST'])
@csrf.exempt
@login_required
def api_claude_ai_enable(user_id):
    """启用某用户的 Claude AI 代理（生成 token + 发邮件 + 推送 Mac mini）"""
    err = _assert_ai_access(user_id, need_edit=True)
    if err: return err
    from app.services.ai_proxy_service import enable_user
    user = User.query.get_or_404(user_id)
    payload = request.get_json(silent=True) or {}
    quota = payload.get('quota')

    try:
        result = enable_user(user, quota_tokens=quota, send_email=True)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        logger.exception('启用 Claude AI 代理失败')
        return jsonify({'success': False, 'message': str(e)}), 500

    return jsonify({
        'success': True,
        'is_new_token': result['is_new_token'],
        'email_sent': result['email_sent'],
        'sync_ok': result['push_ok'],
        'sync_msg': result['push_msg'],
    })


@user_bp.route('/api/<int:user_id>/claude-ai/disable', methods=['POST'])
@csrf.exempt
@login_required
def api_claude_ai_disable(user_id):
    """禁用 Claude AI 代理"""
    err = _assert_ai_access(user_id, need_edit=True)
    if err: return err
    from app.services.ai_proxy_service import disable_user
    user = User.query.get_or_404(user_id)
    push_ok, push_msg = disable_user(user)
    return jsonify({'success': True, 'sync_ok': push_ok, 'sync_msg': push_msg})


@user_bp.route('/api/<int:user_id>/claude-ai/reset-token', methods=['POST'])
@csrf.exempt
@login_required
def api_claude_ai_reset_token(user_id):
    """重置 token"""
    err = _assert_ai_access(user_id, need_edit=True)
    if err: return err
    from app.services.ai_proxy_service import reset_user_token
    user = User.query.get_or_404(user_id)
    try:
        new_token, email_sent, push_ok = reset_user_token(user, send_email=True)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    return jsonify({
        'success': True,
        'token': new_token if user.id == current_user.id else None,  # 仅本人能看明文
        'token_preview': new_token[:14] + '…',
        'email_sent': email_sent,
        'sync_ok': push_ok,
    })


@user_bp.route('/api/<int:user_id>/claude-ai/quota', methods=['POST'])
@csrf.exempt
@login_required
def api_claude_ai_quota(user_id):
    """设置某用户的月度配额"""
    err = _assert_ai_access(user_id, need_edit=True)
    if err: return err
    from app.services.ai_proxy_service import update_user_quota
    user = User.query.get_or_404(user_id)
    payload = request.get_json(silent=True) or {}
    quota = payload.get('quota', 0)
    try:
        quota = max(0, int(quota))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': '配额必须是非负整数'}), 400
    push_ok, _ = update_user_quota(user, quota)
    return jsonify({'success': True, 'quota': quota, 'sync_ok': push_ok})


@user_bp.route('/api/<int:user_id>/claude-ai/refresh-usage', methods=['POST'])
@csrf.exempt
@login_required
def api_claude_ai_refresh_usage(user_id):
    """从 Mac mini 拉取该用户最新用量（手动刷新）"""
    err = _assert_ai_access(user_id)
    if err: return err
    from app.services.ai_proxy_service import _pull_user_daily_usage, get_user_usage_summary
    user = User.query.get_or_404(user_id)
    if not user.claude_ai_token:
        return jsonify({'success': False, 'message': '用户未开通代理'}), 400
    try:
        _pull_user_daily_usage(user, user.claude_ai_token, days=14)
        usage = get_user_usage_summary(user_id)
        return jsonify({'success': True, 'usage': usage})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/<int:user_id>/claude-ai/unlock-device', methods=['POST'])
@csrf.exempt
@login_required
def api_claude_ai_unlock_device(user_id):
    """解除该用户 token 的设备锁定"""
    err = _assert_ai_access(user_id, need_edit=True)
    if err: return err
    from app.services.ai_proxy_service import clear_device_lock
    user = User.query.get_or_404(user_id)
    if not user.claude_ai_token:
        return jsonify({'success': False, 'message': '用户未开通代理'}), 400
    ok, msg = clear_device_lock(user.claude_ai_token)
    if not ok:
        return jsonify({'success': False, 'message': f'解锁失败: {msg}'}), 500
    return jsonify({'success': True})


@user_bp.route('/api/<int:user_id>/claude-ai/requests', methods=['GET'])
@login_required
def api_claude_ai_requests(user_id):
    """获取该用户的 Claude AI 提问记录（从 Mac mini admin_server 拉取）"""
    err = _assert_ai_access(user_id)
    if err: return err
    import requests as http_requests
    from app.services.ai_proxy_service import _admin_url
    user = User.query.get_or_404(user_id)
    if not user.claude_ai_token:
        return jsonify({'success': True, 'entries': [], 'dates': []})
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        resp = http_requests.get(
            _admin_url().rstrip('/') + '/api/requests',
            params={'ip': user.claude_ai_token, 'date': date},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({'success': True, 'entries': data.get('entries', []), 'dates': data.get('dates', [])})
        return jsonify({'success': False, 'entries': [], 'dates': [], 'message': f'http {resp.status_code}'})
    except Exception as e:
        return jsonify({'success': False, 'entries': [], 'dates': [], 'message': str(e)})


@user_bp.route('/api/claude-ai/download-dxt')
def api_claude_ai_download_dxt():
    """下载 .dxt 扩展文件。支持两种认证方式：
    1. 已登录会话（直接访问）
    2. ?t=<claude_ai_token>（邮件链接，无需登录）
    """
    from app.utils.email import generate_dxt_bytes
    from flask import Response
    import os

    t = request.args.get('t', '').strip()
    if t:
        user = User.query.filter_by(claude_ai_token=t).first()
        if not user:
            return jsonify({'error': 'Invalid token'}), 403
    elif current_user.is_authenticated:
        user = current_user
    else:
        from flask import redirect, url_for
        return redirect(url_for('auth.login', next=request.url))

    if not user.claude_ai_token:
        return jsonify({'error': '未开通 Claude AI'}), 403

    db_type = os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE', 'sp8d')
    is_cn = (db_type == 'sp8d')
    if is_cn:
        mcp_host, dxt_name, display = 'pma-mcp.jamesgpone.win', 'pma', 'PMA'
    else:
        mcp_host, dxt_name, display = 'sg-pma-mcp.jamesgpone.win', 'pma-sg', 'PMA (SG)'
    dxt_bytes = generate_dxt_bytes(user.claude_ai_token, display_name=display, host=mcp_host, dxt_name=dxt_name)
    safe_name = (user.username or 'user').lower()
    return Response(
        dxt_bytes,
        mimetype='application/zip',
        headers={'Content-Disposition': f'attachment; filename="pma-{safe_name}.dxt"'}
    )


@user_bp.route('/api/<int:user_id>/claude-ai/send-dxt', methods=['POST'])
@login_required
@csrf.exempt
def api_claude_ai_send_dxt(user_id):
    """发送 Claude Desktop 扩展文件（.dxt）给用户"""
    err = _assert_ai_access(user_id, need_edit=True)
    if err: return err
    user = User.query.get_or_404(user_id)
    if not user.claude_ai_token:
        return jsonify({'success': False, 'message': '该用户尚未开通 Claude AI，请先开通'}), 400
    if not user.email:
        return jsonify({'success': False, 'message': '用户未绑定邮箱'}), 400
    try:
        from app.utils.email import send_dxt_install_email
        sent = send_dxt_install_email(user)
        if sent:
            return jsonify({'success': True, 'message': f'扩展安装邮件已发送至 {user.email}'})
        return jsonify({'success': False, 'message': '邮件发送失败，请检查邮件配置'})
    except Exception as e:
        logger.exception(f'send_dxt error user={user_id}: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


# ═══════════════════════════════════════════════════════════
# AT 个人配置(账户详情 · 个人级配置中心)
# 划界:配置管理=角色默认/系统规则;此处=个人覆盖(目标/预算/权限)与归属
# tab 由 person_config 模块功能开关控制(白名单);数据范围用标准四级
# ═══════════════════════════════════════════════════════════

def _person_tab_allowed(feature_id):
    """个人配置某 tab 访问:纯功能开关驱动(白名单)—— admin,或 person_config view + 对应 feature。
    数据范围决定能配哪些人(页内人员列表按 scope 过滤)。"""
    u = current_user
    if u.role == 'admin':
        return True
    return u.has_permission('person_config', 'view') and u.has_feature('person_config', feature_id)


# 个人配置 tab 顺序(功能开关 → 路由 endpoint);落地路由按此取首个可访问 tab
_PERSON_TAB_ORDER = [
    ('pc_permission', 'user.at_person_permissions'),
    ('pc_affiliation', 'user.at_person_affiliation'),
    ('pc_budget', 'user.at_person_budget'),
    ('pc_performance', 'user.at_person_performance'),
    ('pc_salary', 'user.at_person_salary'),
    ('pc_ai', 'user.at_person_ai'),
]


@user_bp.route('/at-config')
@login_required
def at_person_home():
    """个人配置落地:重定向到当前用户第一个有权访问的 tab(避免落到无权 tab → 403)。
    透传 ?user= 锁定参数。"""
    from flask import redirect, url_for, request, abort
    if current_user.role != 'admin' and not current_user.has_permission('person_config', 'view'):
        abort(403)
    qs = {}
    if request.args.get('user'):
        qs['user'] = request.args.get('user')
    for feat, endpoint in _PERSON_TAB_ORDER:
        if current_user.role == 'admin' or current_user.has_feature('person_config', feat):
            return redirect(url_for(endpoint, **qs))
    abort(403)


@user_bp.route('/at-config/performance')
@login_required
def at_person_performance():
    """AT 个人配置 · 绩效目标(个人覆盖,优先于角色默认)。
    复用 performance_config 的 users/targets/batch(只提交变更项=未动的保持继承)。
    绩效结算审批人(无配置权限)可经 ?user=&settle_q= 进入,仅用于展开审批 chip。"""
    _has_cfg = _person_tab_allowed('pc_performance')
    if not _has_cfg:
        # 放行:?user 指定下属在数据范围内(标准四级)或为其绩效结算审批人
        _ok = False
        try:
            _tu = request.args.get('user', type=int)
            if _tu:
                _tgt = User.query.get(_tu)
                if _tgt and current_user.can_view_person(_tgt, 'person_config'):
                    _ok = True
                if not _ok:
                    from app.helpers.perf_settlement_helpers import is_settlement_approver_of
                    _ok = is_settlement_approver_of(current_user.id, _tu)
        except Exception:
            _ok = False
        if not _ok:
            from flask import abort
            abort(403)

    from app.services.role_kpi_schemes import get_role_scheme
    is_admin = current_user.role == 'admin'
    q = User.query.filter(User._is_active.is_(True))
    if not is_admin:
        q = q.filter(User.company_name == (current_user.company_name or ''))
    users = q.order_by(User.company_name, User.department, User.real_name).all()
    # HRBP 隔离:hr_manager 选人列表只列自己负责部门的成员
    from app.helpers.hrbp_helpers import is_hrbp, hrbp_scope_user_ids
    if is_hrbp(current_user):
        _scope = hrbp_scope_user_ids(current_user)
        users = [u for u in users if u.id in _scope]
    else:
        # 个人配置数据范围隔离:personal→仅自己 / department→本部门 / company→本公司 / system→全部
        users = [u for u in users if current_user.can_view_person(u, 'person_config')]
    users_data = [{
        'id': u.id,
        'name': u.real_name or u.username,
        'role': u.role or '',
        'role_display': get_role_display_name(u.role) if u.role else '',
        'department': u.department or '未分组',
        'company': u.company_name or '',
        'has_scheme': bool(get_role_scheme(u.role)),
    } for u in users]
    # 审批模式:确保被审批的下属在人员列表里(审批人权限范围可能不含 → 否则前端选不中)
    if not _has_cfg:
        _tu = request.args.get('user', type=int)
        if _tu and not any(u['id'] == _tu for u in users_data):
            _tgt = User.query.get(_tu)
            if _tgt:
                users_data.append({
                    'id': _tgt.id, 'name': _tgt.real_name or _tgt.username,
                    'role': _tgt.role or '', 'role_display': get_role_display_name(_tgt.role) if _tgt.role else '',
                    'department': _tgt.department or '未分组', 'company': _tgt.company_name or '',
                    'has_scheme': bool(get_role_scheme(_tgt.role)),
                })
    my_company = current_user.company_name or ''
    companies = sorted({u['company'] for u in users_data if u['company']},
                       key=lambda c: (c != my_company, c))

    # 手工录入指标清单(月度人工填报:研发达成/批次质量/上市支持/SE 培训等)
    from app.models.performance_config import PerformanceMetricsDefinition
    _MANUAL = ['se_response_rate', 'se_content_output', 'se_satisfaction']
    manual_metrics = [{'code': m.metric_code, 'name': m.metric_name,
                       'unit': m.default_unit or '', 'is_rate': m.data_type == 'percentage'}
                      for m in PerformanceMetricsDefinition.query.filter(
                          PerformanceMetricsDefinition.metric_code.in_(_MANUAL)).all()]

    return render_template('user/at_person_performance.html',
                           users_data=users_data,
                           companies=companies,
                           user_company=my_company,
                           is_admin=is_admin,
                           manual_metrics=manual_metrics,
                           current_year=datetime.now().year,
                           approver_mode=(not _has_cfg),  # 审批人进入:仅审批,隐藏切换/其他 tab
                           can_edit=current_user.has_permission('config_management', 'edit'))


@user_bp.route('/at-config/permissions')
@login_required
def at_person_permissions():
    """AT 个人配置 · 权限覆盖。
    语义:有个人 Permission 行的模块=整模块覆盖(含显式拒绝),无行=继承角色默认;
    保存走 overrides 端点(只写覆盖集,不补显式拒绝行),行级「↺ 继承」删单模块行。"""
    if not _person_tab_allowed('pc_permission'):
        from flask import abort
        abort(403)

    is_admin = current_user.role == 'admin'
    q = User.query.filter(User._is_active.is_(True))
    if not is_admin:
        q = q.filter(User.company_name == (current_user.company_name or ''))
    users = q.order_by(User.company_name, User.department, User.real_name).all()
    # 数据范围隔离:HRBP→负责部门;其余→person_config 级别(与绩效/薪资/费用/归属一致)
    from app.helpers.hrbp_helpers import is_hrbp, hrbp_scope_user_ids
    if is_hrbp(current_user):
        _scope = hrbp_scope_user_ids(current_user)
        users = [u for u in users if u.id in _scope]
    else:
        users = [u for u in users if current_user.can_view_person(u, 'person_config')]
    users_data = [{
        'id': u.id,
        'name': u.real_name or u.username,
        'role': u.role or '',
        'role_display': get_role_display_name(u.role) if u.role else '',
        'department': u.department or '未分组',
        'company': u.company_name or '',
    } for u in users]
    my_company = current_user.company_name or ''
    companies = sorted({u['company'] for u in users_data if u['company']},
                       key=lambda c: (c != my_company, c))

    return render_template('user/at_person_permissions.html',
                           users_data=users_data,
                           companies=companies,
                           user_company=my_company,
                           is_admin=is_admin,
                           can_edit=current_user.has_permission('config_management', 'edit'))


@user_bp.route('/at-config/budget')
@login_required
def at_person_budget():
    """AT 个人配置 · 费用预算(挂部门预算之下:个人 ≤ 部门待分配,部门明细强制保留)。
    企业隔离:非 admin 只列/只配本公司用户。"""
    if not _person_tab_allowed('pc_budget'):
        from flask import abort
        abort(403)

    from app.models.expense import EXPENSE_CATEGORIES
    from app.utils.dictionary_helpers import get_default_currency, get_currency_symbol

    is_admin = current_user.role == 'admin'
    q = User.query.filter(User._is_active.is_(True))
    if not is_admin:
        q = q.filter(User.company_name == (current_user.company_name or ''))
    users = q.order_by(User.company_name, User.department, User.real_name).all()
    # 数据范围隔离:HRBP→负责部门;其余→person_config 级别(personal 仅自己)
    from app.helpers.hrbp_helpers import is_hrbp, hrbp_scope_user_ids
    if is_hrbp(current_user):
        _scope = hrbp_scope_user_ids(current_user)
        users = [u for u in users if u.id in _scope]
    else:
        users = [u for u in users if current_user.can_view_person(u, 'person_config')]
    users_data = [{
        'id': u.id,
        'name': u.real_name or u.username,
        'role_display': get_role_display_name(u.role) if u.role else '',
        'department': u.department or '未分组',
        'company': u.company_name or '',
    } for u in users]
    # 公司清单:先选公司再选人;admin=全部公司,非 admin=本公司;
    # 访问者所属公司(厂商)排最前 = admin 进入时的默认上下文
    my_company = current_user.company_name or ''
    companies = sorted({u['company'] for u in users_data if u['company']},
                       key=lambda c: (c != my_company, c))

    currency_code = get_default_currency()
    return render_template('user/at_person_budget.html',
                           users_data=users_data,
                           companies=companies,
                           user_company=current_user.company_name or '',
                           is_admin=is_admin,
                           expense_categories=[{'code': c, 'name': n} for c, n in EXPENSE_CATEGORIES],
                           currency_code=currency_code,
                           currency_symbol=get_currency_symbol(currency_code),
                           current_year=datetime.now().year,
                           can_edit=current_user.has_permission('config_management', 'edit'))


@user_bp.route('/at-list')
@login_required
@permission_required('user_management', 'view')
def at_list():
    """AT 风格账户列表(替代 tw_list);tabs=激活状态,筛选=角色/公司/部门"""
    from sqlalchemy import or_

    page = max(int(request.args.get('page', 1)), 1)
    per_page = 50
    tab = request.args.get('tab', 'active')
    search = request.args.get('search', '').strip()
    role_values = [v for v in request.args.getlist('role') if v.strip()]
    company_values = [v for v in request.args.getlist('company') if v.strip()]
    dept_values = [v for v in request.args.getlist('dept') if v.strip()]

    base = get_viewable_data(User, current_user)

    # 筛选选项(基于可见范围)
    role_options = [{'value': r, 'label': get_role_display_name(r) or r}
                    for (r,) in base.with_entities(User.role).distinct().all() if r]
    role_options.sort(key=lambda x: x['label'])
    company_options = sorted({c for (c,) in base.with_entities(User.company_name).distinct().all() if c})
    dept_options = sorted({d for (d,) in base.with_entities(User.department).distinct().all() if d})

    if role_values:
        base = base.filter(User.role.in_(role_values))
    if company_values:
        base = base.filter(User.company_name.in_(company_values))
    if dept_values:
        base = base.filter(User.department.in_(dept_values))
    if search:
        like = f'%{search}%'
        base = base.filter(or_(User.username.ilike(like), User.real_name.ilike(like),
                               User.email.ilike(like), User.company_name.ilike(like),
                               User.department.ilike(like)))

    tab_counts = {
        'all': base.count(),
        'active': base.filter(User._is_active.is_(True)).count(),
        'inactive': base.filter(User._is_active.is_(False)).count(),
    }
    q = base
    if tab == 'active':
        q = q.filter(User._is_active.is_(True))
    elif tab == 'inactive':
        q = q.filter(User._is_active.is_(False))

    pagination = q.order_by(User.updated_at.desc().nullslast()).paginate(
        page=page, per_page=per_page, error_out=False)

    users_view = [{
        'id': u.id,
        'name': u.real_name or u.username,
        'username': u.username,
        'role_display': get_role_display_name(u.role) if u.role else '—',
        'department': u.department or '—',
        'company': u.company_name or '—',
        'email': u.email or '',
        'phone': u.phone or '',
        'is_active': bool(u._is_active),
        'is_dept_manager': bool(u.is_department_manager),
        'in_probation': u.in_probation,
        'probation_end': u.probation_end.isoformat() if u.probation_end else None,
        # updated_at 在 User 模型里是 float 时间戳,统一在此格式化
        'updated': (datetime.fromtimestamp(u.updated_at).strftime('%Y-%m-%d')
                    if isinstance(u.updated_at, (int, float)) and u.updated_at
                    else (u.updated_at.strftime('%Y-%m-%d') if u.updated_at else '—')),
    } for u in pagination.items]

    list_qs = {}
    if search:
        list_qs['search'] = search
    if role_values:
        list_qs['role'] = role_values
    if company_values:
        list_qs['company'] = company_values
    if dept_values:
        list_qs['dept'] = dept_values

    # 新建账户模态框的字典选项(角色 key→显示名;公司/部门用值)
    can_create = current_user.has_permission('user_management', 'create')
    form_options = None
    if can_create:
        dicts = Dictionary.query.filter_by(is_active=True).all()
        from app.models.expense import Department as _Dept
        _depts = _Dept.query.filter_by(is_active=True).order_by(_Dept.company_name, _Dept.name).all()
        form_options = {
            'roles': sorted([{'value': d.key, 'label': d.value} for d in dicts if d.type == 'role'],
                            key=lambda x: x['label']),
            'companies': [{'value': d.value, 'label': d.value} for d in dicts if d.type == 'company'],
            # 部门来自部门字典(Department 表),带公司用于联动过滤
            'departments': [{'value': d.name, 'label': d.name, 'company': d.company_name or ''} for d in _depts],
        }

    return render_template('user/at_list.html',
                           users=users_view,
                           pagination=pagination,
                           tab_counts=tab_counts,
                           current_tab=tab,
                           search=search,
                           role_options=role_options,
                           company_options=[{'value': c, 'label': c} for c in company_options],
                           dept_options=[{'value': d, 'label': d} for d in dept_options],
                           role_values=role_values,
                           company_values=company_values,
                           dept_values=dept_values,
                           list_qs=list_qs,
                           can_create=can_create,
                           form_options=form_options)


@user_bp.route('/at-detail/<int:user_id>')
@login_required
@permission_required('user_management', 'view')
def at_user_detail(user_id):
    """AT 风格账户详情:档案信息 + 账户操作;个人级配置跳「个人配置」四页签(?user= 预选)。"""
    u = get_viewable_data(User, current_user).filter(User.id == user_id).first()
    if not u:
        flash('用户不存在或无权限查看', 'danger')
        return redirect(url_for('user.at_list'))

    def _ts(v, fmt='%Y-%m-%d %H:%M'):
        if not v:
            return '—'
        try:
            return datetime.fromtimestamp(v).strftime(fmt) if isinstance(v, (int, float)) else v.strftime(fmt)
        except Exception:
            return '—'

    info = {
        'id': u.id,
        'name': u.real_name or u.username,
        'username': u.username,
        'role': u.role or '',
        'role_display': get_role_display_name(u.role) if u.role else '—',
        'department': u.department or '—',
        'company': u.company_name or '—',
        'email': u.email or '',
        'phone': u.phone or '',
        'wechat': u.wechat_nickname or '',
        'is_active': bool(u._is_active),
        'is_dept_manager': bool(u.is_department_manager),
        'in_probation': u.in_probation,
        'probation_start': u.probation_start.isoformat() if u.probation_start else None,
        'probation_end': u.probation_end.isoformat() if u.probation_end else None,
        'created': _ts(u.created_at),
        'last_login': _ts(u.last_login),
    }
    can_edit = current_user.has_permission('user_management', 'edit')
    # 编辑模态:原始字段值(与 edit_user POST 字段对齐)+ 字典选项
    edit_data, form_options = None, None
    if can_edit:
        edit_data = {
            'username': u.username,
            'real_name': u.real_name or '',
            'role': u.role or '',
            'department': u.department or '',
            'company': u.company_name or '',
            'email': u.email or '',
            'phone': u.phone or '',
            'settlement_currency': u.settlement_currency or '',
            'is_active': bool(u._is_active),
            'is_department_manager': bool(u.is_department_manager),
            'probation_start': u.probation_start.isoformat() if u.probation_start else None,
            'probation_end': u.probation_end.isoformat() if u.probation_end else None,
            'cross_team_visible': bool(getattr(u, 'cross_team_visible', False)),
            'cross_team_label': getattr(u, 'cross_team_label', '') or '',
        }
        dicts = Dictionary.query.filter_by(is_active=True).all()
        from app.models.expense import Department as _Dept
        _depts = _Dept.query.filter_by(is_active=True).order_by(_Dept.company_name, _Dept.name).all()
        form_options = {
            'roles': sorted([{'value': d.key, 'label': d.value} for d in dicts if d.type == 'role'],
                            key=lambda x: x['label']),
            'companies': [{'value': d.value, 'label': d.value} for d in dicts if d.type == 'company'],
            # 部门来自部门字典(Department 表),带公司用于联动过滤
            'departments': [{'value': d.name, 'label': d.name, 'company': d.company_name or ''} for d in _depts],
        }
    # 个人配置入口:逐 tab 按功能开关(白名单)gate;有 person_config 查看权 + 任一 feature 才显示该区块
    _pc_view = current_user.has_permission('person_config', 'view')
    pc_tabs = {
        'pc_permission': current_user.has_feature('person_config', 'pc_permission'),
        'pc_affiliation': current_user.has_feature('person_config', 'pc_affiliation'),
        'pc_budget': current_user.has_feature('person_config', 'pc_budget'),
        'pc_performance': current_user.has_feature('person_config', 'pc_performance'),
        'pc_salary': current_user.has_feature('person_config', 'pc_salary'),
        'pc_ai': current_user.has_feature('person_config', 'pc_ai'),
    }
    return render_template('user/at_detail.html',
                           u=info,
                           edit_data=edit_data,
                           form_options=form_options,
                           can_edit=can_edit,
                           can_delete=current_user.has_permission('user_management', 'delete'),
                           pc_tabs=pc_tabs,
                           can_person_config=(_pc_view and any(pc_tabs.values())))


# ── AT 个人配置 · 薪资(岗位结构套用 + 个人覆盖/专属项目;仅 admin/ceo/hr_manager) ──

def _salary_guard():
    from app.models.salary_structure import SALARY_ADMIN_ROLES
    if current_user.role not in SALARY_ADMIN_ROLES:
        from flask import abort
        abort(403)


@user_bp.route('/at-config/salary')
@login_required
def at_person_salary():
    """AT 个人配置 · 薪资:显示该人岗位的薪资结构(继承),金额可个人覆盖,可加专属项目。"""
    if not _person_tab_allowed('pc_salary'):
        from flask import abort
        abort(403)
    from app.utils.dictionary_helpers import get_default_currency, get_currency_symbol
    is_admin = current_user.role == 'admin'
    q = User.query.filter(User._is_active.is_(True))
    if not is_admin:
        q = q.filter(User.company_name == (current_user.company_name or ''))
    users = q.order_by(User.company_name, User.department, User.real_name).all()
    # HRBP 隔离:hr_manager 选人列表只列自己负责部门的成员
    from app.helpers.hrbp_helpers import is_hrbp, hrbp_scope_user_ids
    if is_hrbp(current_user):
        _scope = hrbp_scope_user_ids(current_user)
        users = [u for u in users if u.id in _scope]
    else:
        # 个人配置数据范围隔离:personal→仅自己 / department→本部门 / company→本公司 / system→全部
        users = [u for u in users if current_user.can_view_person(u, 'person_config')]
    users_data = [{
        'id': u.id,
        'name': u.real_name or u.username,
        'role': u.role or '',
        'role_display': get_role_display_name(u.role) if u.role else '',
        'department': u.department or '未分组',
        'company': u.company_name or '',
    } for u in users]
    my_company = current_user.company_name or ''
    companies = sorted({u['company'] for u in users_data if u['company']},
                       key=lambda c: (c != my_company, c))
    return render_template('user/at_person_salary.html',
                           users_data=users_data,
                           companies=companies,
                           user_company=my_company,
                           is_admin=is_admin,
                           currency_symbol=get_currency_symbol(get_default_currency()),
                           current_year=datetime.now().year,
                           can_edit=True)


@user_bp.route('/api/person-salary/<int:user_id>/<int:year>')
@login_required
def api_get_person_salary(user_id, year):
    """个人薪资:套用全局结构(主子层级)+ 月度实发 + 试用期标记。
    主项有子项→每月金额=子项汇总(前端算);叶子项 HR 按月回填实发(monthly)。"""
    from app.views.performance_config import can_access_person_tab
    if not can_access_person_tab(user_id, 'pc_salary'):
        return jsonify({'success': False, 'message': '无权限'}), 403
    try:
        from app.models.salary_structure import SalaryStructureItem, UserSalaryItem, UserSalaryProfile

        def _monthly(row):
            m = (row.monthly_amounts or {}) if row else {}
            # JSON key 可能是字符串,统一成 {1..12: float}
            return {int(k): float(v) for k, v in m.items() if v not in (None, '')}

        u = User.query.get(user_id)
        if not u:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        struct = SalaryStructureItem.query.filter_by(is_active=True)\
            .order_by(SalaryStructureItem.sort_order, SalaryStructureItem.id).all()
        urows = UserSalaryItem.query.filter_by(user_id=user_id, year=year).all()
        amap = {x.item_code: x for x in urows if not x.is_personal}    # 结构项金额
        personal = [x for x in urows if x.is_personal]
        child_codes = {r.parent_code for r in struct if r.parent_code}
        items = []
        for r in struct:
            a = amap.get(r.item_code)
            # 发放方式:个人覆盖(a.pay_cycle)优先,默认引用配置结构(r.pay_cycle)
            cyc = (a.pay_cycle if (a and a.pay_cycle) else None) or (r.pay_cycle or 'monthly')
            items.append({
                'item_code': r.item_code, 'item_name': r.item_name,
                'parent_code': r.parent_code, 'pay_cycle': cyc,
                'default_cycle': r.pay_cycle or 'monthly',
                'is_locked': bool(r.is_locked), 'is_personal': False,
                'has_children': r.item_code in child_codes,
                'amount': float(a.amount) if (a and a.amount is not None) else None,
                'monthly': _monthly(a),
            })
        for x in sorted(personal, key=lambda p: (p.sort_order or 0, p.id)):
            items.append({
                'item_code': x.item_code, 'item_name': x.item_name or '',
                'parent_code': None, 'pay_cycle': x.pay_cycle or 'monthly',
                'is_locked': False, 'is_personal': True, 'has_children': False,
                'amount': float(x.amount) if x.amount is not None else None,
                'monthly': _monthly(x),
            })
        # 薪资审批已锁定的月份(提交/通过 → 该月不可编辑)
        from app.helpers.salary_run_helpers import locked_months as _locked_months_fn
        lk = _locked_months_fn(u.company_name, year) if u.company_name else []
        # 试用期为账户级属性(账户创建/编辑设定);薪资页只读引用并高亮对应月份
        return jsonify({'success': True, 'data': {
            'items': items,
            'structure_configured': bool(struct),
            'role': u.role or '', 'role_display': get_role_display_name(u.role) if u.role else '',
            'in_probation': u.in_probation,
            'probation_start': u.probation_start.isoformat() if u.probation_start else None,
            'probation_end': u.probation_end.isoformat() if u.probation_end else None,
            'locked_months': lk,
        }})
    except Exception as e:
        logger.exception(f'person-salary get error: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/person-salary/<int:user_id>/<int:year>', methods=['POST'])
@login_required
def api_save_person_salary(user_id, year):
    """保存个人薪资:结构项月度实发 + 个人专属项目整组替换 + 试用期开关/日期"""
    from app.views.performance_config import can_access_person_tab
    if not can_access_person_tab(user_id, 'pc_salary', need_edit=True):
        return jsonify({'success': False, 'message': '无权限'}), 403
    try:
        from app.models.salary_structure import SalaryStructureItem, UserSalaryItem, UserSalaryProfile
        data = request.get_json() or {}
        struct_rows = SalaryStructureItem.query.filter_by(is_active=True).all()
        struct_codes = {r.item_code for r in struct_rows}
        struct_cycle = {r.item_code: (r.pay_cycle or 'monthly') for r in struct_rows}

        # 薪资审批已锁定的月份(提交/通过):该月各项实发不可改,保存时保留原值
        from app.helpers.salary_run_helpers import locked_months as _locked_months_fn
        _tu = User.query.get(user_id)
        _locked = set(_locked_months_fn(_tu.company_name, year)) if (_tu and _tu.company_name) else set()

        def _keep_locked(months, row):
            if not _locked:
                return months
            existing = (row.monthly_amounts if row else None) or {}
            for lm in _locked:
                k = str(lm)
                if k in existing:
                    months[k] = existing[k]
                else:
                    months.pop(k, None)
            return months

        def _num(v):
            return None if v in (None, '') else float(v)

        def _cyc(v):
            return v if v in ('monthly', 'quarterly', 'yearly') else None

        def _months(raw):
            """清理月度载荷 → {"1":float,...};空值剔除;无有效月返回 {}"""
            out = {}
            for k, v in (raw or {}).items():
                if v in (None, ''):
                    continue
                try:
                    mk = int(k)
                except (TypeError, ValueError):
                    continue
                if 1 <= mk <= 12:
                    out[str(mk)] = float(v)
            return out

        # 1) 结构项:标准金额 amount + 月度覆盖实发 monthly(两者皆空则删行)
        for it in data.get('amounts', []):
            code = it.get('item_code')
            if code not in struct_codes:
                continue
            amt = _num(it.get('amount'))
            months = _months(it.get('monthly'))
            # 发放方式:与配置默认相同存 null(继承,配置改了跟随),不同则存覆盖
            sub_cyc = _cyc(it.get('pay_cycle'))
            cyc_override = sub_cyc if (sub_cyc and sub_cyc != struct_cycle.get(code)) else None
            row = UserSalaryItem.query.filter_by(user_id=user_id, year=year,
                                                 item_code=code, is_personal=False).first()
            months = _keep_locked(months, row)   # 锁定月保留原值
            if amt is None and not months and cyc_override is None:
                if row:
                    db.session.delete(row)
                continue
            if not row:
                row = UserSalaryItem(user_id=user_id, year=year, item_code=code,
                                     is_personal=False, created_by=current_user.id)
                db.session.add(row)
            row.amount = amt
            row.monthly_amounts = months
            row.pay_cycle = cyc_override
            row.updated_by = current_user.id

        # 2) 个人专属项目:整组替换(载荷外的删除)
        if 'personal' in data:
            keep = set()
            for i, it in enumerate(data.get('personal') or []):
                name = (it.get('item_name') or '').strip()
                if not name:
                    continue
                code = (it.get('item_code') or '').strip()
                if not code:
                    import uuid
                    code = 'pers_' + uuid.uuid4().hex[:8]
                keep.add(code)
                row = UserSalaryItem.query.filter_by(user_id=user_id, year=year, item_code=code).first()
                if not row:
                    row = UserSalaryItem(user_id=user_id, year=year, item_code=code,
                                         is_personal=True, created_by=current_user.id)
                    db.session.add(row)
                row.is_personal = True
                row.item_name = name
                row.pay_cycle = it.get('pay_cycle') if it.get('pay_cycle') in ('monthly', 'quarterly', 'yearly') else 'monthly'
                row.amount = _num(it.get('amount'))
                row.monthly_amounts = _months(it.get('monthly'))
                row.sort_order = i
                row.updated_by = current_user.id
            for row in UserSalaryItem.query.filter_by(user_id=user_id, year=year, is_personal=True).all():
                if row.item_code not in keep:
                    db.session.delete(row)

        # 试用期已挪到账户设置(账户创建/编辑),薪资页不再写入

        db.session.commit()
        return jsonify({'success': True, 'message': '个人薪资已保存'})
    except Exception as e:
        db.session.rollback()
        logger.exception(f'person-salary save error: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/at-config/ai')
@login_required
def at_person_ai():
    """AT 个人配置 · Claude AI 代理:开通/配额/用量/设备锁定。
    由 person_config 功能开关 pc_ai 控制(默认仅 admin 勾选)。"""
    if not _person_tab_allowed('pc_ai'):
        from flask import abort
        abort(403)

    is_admin = current_user.role == 'admin'
    q = User.query.filter(User._is_active.is_(True))
    if not is_admin:
        q = q.filter(User.company_name == (current_user.company_name or ''))
    users = q.order_by(User.company_name, User.department, User.real_name).all()
    # 数据范围隔离:HRBP→负责部门;其余→person_config 级别(与其它人事页一致)
    from app.helpers.hrbp_helpers import is_hrbp, hrbp_scope_user_ids
    if is_hrbp(current_user):
        _scope = hrbp_scope_user_ids(current_user)
        users = [u for u in users if u.id in _scope]
    else:
        users = [u for u in users if current_user.can_view_person(u, 'person_config')]
    users_data = [{
        'id': u.id,
        'name': u.real_name or u.username,
        'role_display': get_role_display_name(u.role) if u.role else '',
        'department': u.department or '未分组',
        'company': u.company_name or '',
        'ai_enabled': bool(u.claude_ai_enabled),
    } for u in users]
    my_company = current_user.company_name or ''
    companies = sorted({u['company'] for u in users_data if u['company']},
                       key=lambda c: (c != my_company, c))

    return render_template('user/at_person_ai.html',
                           users_data=users_data,
                           companies=companies,
                           user_company=my_company,
                           is_admin=True,
                           can_edit=True)


@user_bp.route('/at-api/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@permission_required('user_management', 'edit')
def at_api_toggle_user_active(user_id):
    """启用/停用账户(AT 详情页操作)"""
    try:
        u = get_viewable_data(User, current_user).filter(User.id == user_id).first()
        if not u:
            return jsonify({'success': False, 'message': '用户不存在或无权限'}), 404
        if u.id == current_user.id:
            return jsonify({'success': False, 'message': '不能停用自己的账户'}), 400
        if u.role == 'admin' and current_user.role != 'admin':
            return jsonify({'success': False, 'message': '无权操作管理员账户'}), 403
        was_active = bool(u._is_active)
        u._is_active = not was_active
        db.session.commit()

        msg = '账户已激活' if u._is_active else '账户已停用'
        # 首次激活的新账户(从未登录过)→ 发邀请邮件(激活链接,用户自设密码);
        # 老账户重新激活不发(已有密码)。邮件失败不回滚激活,只提示。
        if u._is_active and not was_active and not u.last_login:
            try:
                from app.utils.email import send_user_invitation_email
                sent = send_user_invitation_email({
                    'id': u.id, 'username': u.username, 'real_name': u.real_name,
                    'company_name': u.company_name, 'email': u.email, 'phone': u.phone,
                    'department': u.department, 'is_department_manager': u.is_department_manager,
                    'role': u.role,
                })
                msg += (',邀请邮件已发送至 ' + (u.email or '')) if sent \
                    else ',但邀请邮件发送失败,请手动通知用户设置密码'
            except Exception as mail_err:
                logger.warning(f"激活邀请邮件发送失败: {mail_err}")
                msg += ',但邀请邮件发送失败,请手动通知用户设置密码'
        return jsonify({'success': True, 'is_active': bool(u._is_active), 'message': msg})
    except Exception as e:
        db.session.rollback()
        logger.error(f"切换账户状态失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500


@user_bp.route('/at-config/affiliation')
@login_required
def at_person_affiliation():
    """AT 个人配置 · 归属关系(该用户作为 viewer 可查看哪些 owner 的数据)。
    复用 /user/api/get_selected_users 与 /user/api/save_affiliations(整包替换)。
    企业隔离:非 admin 只列/只配本公司用户。"""
    if not _person_tab_allowed('pc_affiliation'):
        from flask import abort
        abort(403)

    is_admin = current_user.role == 'admin'
    q = User.query.filter(User._is_active.is_(True))
    if not is_admin:
        q = q.filter(User.company_name == (current_user.company_name or ''))
    users = q.order_by(User.company_name, User.department, User.real_name).all()
    # 数据范围隔离:HRBP→负责部门;其余→person_config 级别(与绩效/薪资/费用/权限一致)
    from app.helpers.hrbp_helpers import is_hrbp, hrbp_scope_user_ids
    if is_hrbp(current_user):
        _scope = hrbp_scope_user_ids(current_user)
        users = [u for u in users if u.id in _scope]
    else:
        users = [u for u in users if current_user.can_view_person(u, 'person_config')]
    users_data = [{
        'id': u.id,
        'name': u.real_name or u.username,
        'role_display': get_role_display_name(u.role) if u.role else '',
        'department': u.department or '未分组',
        'company': u.company_name or '',
        'is_dept_manager': bool(u.is_department_manager),
    } for u in users]
    # 访问者所属公司(厂商)排最前 = admin 进入时的默认上下文
    my_company = current_user.company_name or ''
    companies = sorted({u['company'] for u in users_data if u['company']},
                       key=lambda c: (c != my_company, c))

    return render_template('user/at_person_affiliation.html',
                           users_data=users_data,
                           companies=companies,
                           user_company=current_user.company_name or '',
                           is_admin=is_admin,
                           can_edit=(is_admin or current_user.has_permission('user_management', 'edit')))


