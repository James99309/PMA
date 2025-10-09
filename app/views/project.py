from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort, session, after_this_request
from flask_babel import gettext as _
from datetime import datetime, date, timedelta
from flask_login import login_required, current_user
from app import db, csrf
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.approval import ApprovalStatus
from app.decorators import permission_required, permission_required_with_approval_context
from app.utils.access_control import get_viewable_data, can_edit_data, get_accessible_data, can_change_project_owner, can_view_project
import logging
import re
from fuzzywuzzy import fuzz
from app.utils.text_similarity import calculate_chinese_similarity, is_similar_project_name
import uuid  # 使用内置的uuid模块替代bson.objectid
import pandas as pd
import json
from app.models.user import User
from app.models.quotation import Quotation
from app.models.pricing_order import PricingOrder
from app.models.relation import ProjectMember
from app.permissions import check_permission, Permissions
from werkzeug.utils import secure_filename
import os
from flask_wtf.csrf import CSRFProtect
from app.models.action import Action, ActionReply
from app.models.projectpm_stage_history import ProjectStageHistory  # 导入阶段历史记录模型
from app.utils.dictionary_helpers import project_type_label, project_stage_label, REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS, COMPANY_TYPE_LABELS, INDUSTRY_OPTIONS, get_industry_options, get_project_type_options, get_report_source_options, get_product_situation_options, get_project_stage_options, get_default_currency, get_currency_symbol, get_amount_unit_config
from app.services.exchange_rate_service import exchange_rate_service
from app.utils.chinese_mapping_manager import mapping_manager
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from app.utils.notification_helpers import trigger_event_notification
from app.services.event_dispatcher import notify_project_created, notify_project_status_updated
from app.helpers.project_helpers import is_project_editable
from app.utils.activity_tracker import check_company_activity, update_active_status
from app.models.settings import SystemSettings
from zoneinfo import ZoneInfo
from app.utils.role_mappings import get_role_display_name
from app.utils.solution_manager_notifications import notify_solution_managers_project_created, notify_solution_managers_project_stage_changed
from flask import after_this_request
from app.utils.change_tracker import ChangeTracker
from app.helpers.approval_helpers import get_object_approval_instance, get_available_templates
from app.utils.access_control import can_start_approval

# 添加 ProjectRatingRecord 导入
try:
    from app.models.project_rating_record import ProjectRatingRecord
except ImportError:
    ProjectRatingRecord = None

csrf = CSRFProtect()

logger = logging.getLogger(__name__)

project = Blueprint('project', __name__)

@project.route('/api/companies/<company_type>')
@login_required
def api_companies_for_project(company_type):
    """API端点 - 为项目获取企业列表（移除权限等级过滤，仅过滤删除状态和企业角色）"""
    try:
        # 直接查询所有未删除的企业，不使用权限等级过滤
        query = Company.query.filter(Company.is_deleted == False)
        
        # 根据类型筛选企业
        type_mapping = {
            'user': ['user', 'end_user', 'customer'],
            'designer': ['designer', 'design_institute', 'consultant'],
            'contractor': ['contractor', 'general_contractor'],
            'integrator': ['integrator', 'system_integrator'],
            'dealer': ['dealer', 'distributor']
        }
        
        if company_type in type_mapping:
            company_types = type_mapping[company_type]
            query = query.filter(Company.company_type.in_(company_types))
        
        companies = query.all()  # 先获取所有企业，后面分组后再排序
        
        # 格式化返回数据，区分当前用户和其他用户的公司
        current_user_companies = []
        other_companies = []
        
        for company in companies:
            company_data = {
                'id': company.id,
                'name': company.company_name,
                'type': company.company_type,
                'owner_name': company.owner.real_name if company.owner else '未指定',
                'owner_id': company.owner_id,
                'is_readable': True,  # 移除权限检查，所有企业都可读
                'is_own': company.owner_id == current_user.id
            }
            
            # 分组：当前用户的公司优先
            if company.owner_id == current_user.id:
                current_user_companies.append(company_data)
            else:
                other_companies.append(company_data)
        
        # 对每个分组内部按企业名称排序
        current_user_companies.sort(key=lambda x: x['name'] or '')
        other_companies.sort(key=lambda x: x['name'] or '')
        
        # 组合结果：当前用户的公司在前，其他公司在后
        result = current_user_companies + other_companies
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取项目企业列表失败: {str(e)}")
        return jsonify([])

def get_company_list_by_type(company_type):
    """根据企业类型获取企业列表"""
    # 使用数据访问控制
    query = get_viewable_data(Company, current_user)
    return query.filter_by(company_type=company_type).order_by(Company.company_name).all()

@project.route('/')
@permission_required('project', 'view')
def list_projects():
    import time
    start_time = time.time()
    logger.info(f"⏱️ [性能] 开始加载项目列表")

    search = request.args.get('search', '')
    sort = request.args.get('sort', 'updated_at')
    order = request.args.get('order', 'desc')
    # my_projects和account_id参数处理已移除
    # 检查是否需要保持面板打开
    keep_panel = request.args.get('keep_panel', 'false') == 'true'

    t1 = time.time()
    logger.info(f"⏱️ [性能] 参数解析: {(t1-start_time)*1000:.0f}ms")

    # 使用数据访问控制，预加载owner关系
    query = get_viewable_data(Project, current_user).options(joinedload(Project.owner))
    
    # 只看自己和账户过滤逻辑已移除
    
    # 添加搜索条件
    if search:
        query = query.filter(Project.project_name.ilike(f'%{search}%'))
    
    # 处理筛选参数
    filters = {}
    for key, value in request.args.items():
        if key.startswith('filter_') and value:
            field = key[7:]  # 移除'filter_'前缀
            filters[field] = value
    
    
    # 移除默认的有效业务过滤逻辑
    # 现在页面默认显示所有项目，包括签约、失败、搁置状态的项目
    # 用户需要主动点击"有效项目"筛选卡才会应用过滤条件
    
    # 注释掉默认过滤逻辑，恢复显示所有项目
    # enable_default_valid_filter = (
    #     'stage_not' not in filters and 
    #     'current_stage' not in filters and
    #     not any(key in request.args for key in ['filter_stage_not', 'filter_current_stage', 'business_update_filter'])
    # )
    # 
    # if enable_default_valid_filter:
    #     # 应用默认的有效业务过滤：排除搁置、失败和签约阶段，且有授权编号
    #     filters['stage_not'] = 'lost,paused,signed'
    #     filters['has_authorization'] = '1'
    
    # 应用筛选条件
    for field, value in filters.items():
        # 处理特殊筛选条件
        if field == 'is_active':
            # 筛选活跃状态
            is_active_value = value.lower() in ['true', '1', 'yes', 'active']
            query = query.filter(Project.is_active == is_active_value)
        elif field == 'has_authorization':
            # 筛选有授权编号的项目
            if value == '1':
                query = query.filter(Project.authorization_code.isnot(None), 
                                     func.length(Project.authorization_code) > 0)
            elif value == '0':
                query = query.filter(or_(Project.authorization_code.is_(None),
                                         func.length(Project.authorization_code) == 0))
        elif field == 'stage_not':
            # 排除特定阶段的项目
            excluded_stages = value.split(',')
            
            # 基础排除：排除当前阶段在排除列表中的项目
            for stage in excluded_stages:
                stage = stage.strip()
                if stage:
                    query = query.filter(Project.current_stage != stage)
            
            # 增强逻辑：如果排除列表包含 'lost' 或 'paused'，还要排除历史上曾经进入这些状态的项目
            critical_stages = []
            for stage in excluded_stages:
                stage = stage.strip()
                if stage in ['lost', 'paused']:
                    critical_stages.append(stage)
            
            if critical_stages:
                # 查询曾经进入失败或搁置状态的项目ID
                from app.models.projectpm_stage_history import ProjectStageHistory
                
                # 查找历史上进入过关键状态的项目
                historical_excluded_ids = db.session.query(ProjectStageHistory.project_id).filter(
                    ProjectStageHistory.to_stage.in_(critical_stages)
                ).distinct().all()
                
                if historical_excluded_ids:
                    # 排除这些项目
                    excluded_project_ids = [p.project_id for p in historical_excluded_ids]
                    query = query.filter(~Project.id.in_(excluded_project_ids))
        elif field == 'updated_this_month' or field.endswith('_update_filter'):
            # 筛选本月有阶段变更的项目（支持 updated_this_month 和 business_update_filter）
            if value == '1':
                today = datetime.now().date()
                start_date = today.replace(day=1)  # 本月1号
                
                # 查询本月内有阶段变化的项目
                from app.models.projectpm_stage_history import ProjectStageHistory
                project_ids_with_changes = db.session.query(ProjectStageHistory.project_id).filter(
                    ProjectStageHistory.change_date >= start_date
                ).distinct().all()
                
                project_ids = [p.project_id for p in project_ids_with_changes]
                if project_ids:
                    query = query.filter(Project.id.in_(project_ids))
                else:
                    # 如果没有找到任何项目，返回空结果
                    query = query.filter(Project.id == -1)  # 不会匹配任何项目
        elif field == 'current_stage':
            # 处理阶段过滤，直接使用英文key进行匹配
            query = query.filter(Project.current_stage == value)
        elif hasattr(Project, field):
            # 处理不同类型的字段
            if field in ['report_time', 'delivery_forecast', 'created_at', 'updated_at']:
                # 日期字段
                try:
                    date_value = datetime.strptime(value, '%Y-%m-%d').date()
                    query = query.filter(getattr(Project, field) == date_value)
                except (ValueError, TypeError):
                    # 日期格式错误，忽略此筛选
                    pass
            elif field == 'quotation_customer':
                # 数字字段，使用模糊匹配
                query = query.filter(getattr(Project, field).cast(db.String).ilike(f'%{value}%'))
            else:
                # 文本字段，使用模糊匹配
                query = query.filter(getattr(Project, field).ilike(f'%{value}%'))
    
    # 添加排序条件
    try:
        # 特殊处理：当按项目名称排序时，实际按奖励星星数量排序
        if sort == 'project_name':
            # 按星星数量排序，空值排在最后
            if order == 'desc':
                # 降序：星星多的在前，空值在最后
                sort_column = Project.rating.desc().nullslast()
            else:
                # 升序：星星少的在前，空值在最后  
                sort_column = Project.rating.asc().nullslast()
        else:
            # 其他字段按原逻辑排序
            sort_column = getattr(Project, sort, Project.id)
            if order == 'desc':
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()
        
        # 关键优化：首次加载只获取前30个项目，其余通过滚动加载
        initial_page_size = 30
        projects = query.order_by(sort_column).limit(initial_page_size).all()
    except Exception as e:
        logger.warning(f"排序出错：{str(e)}，使用默认排序")
        # 错误情况下也使用分页
        initial_page_size = 30
        projects = query.order_by(Project.id.desc()).limit(initial_page_size).all()

    t2 = time.time()
    logger.info(f"⏱️ [性能] 项目列表查询(前30条): {(t2-t1)*1000:.0f}ms")

    # 将筛选参数传递到模板
    filter_params = {key: value for key, value in request.args.items() if key.startswith('filter_')}

    # 检查是否是AJAX请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.args.get('format') == 'json':
        # 返回JSON格式的项目列表HTML片段
        html = render_template('project/list_partial.html', projects=projects, search_term=search, Quotation=Quotation, filter_params=filter_params)
        return jsonify({'success': True, 'html': html})

    # 构建通用组件配置
    # 获取当前语言环境和目标货币
    from app.utils.i18n import get_current_language
    current_lang = get_current_language()
    target_currency = 'USD' if current_lang == 'en' else 'CNY'

    # 计算统计数据（使用高效的聚合查询，性能可接受）
    try:
        # 构建统计查询（应用与主查询相同的筛选条件，但不包含 current_stage 筛选）
        stats_query = get_viewable_data(Project, current_user)

        # 应用筛选条件（排除 current_stage 以显示各阶段统计）
        stats_query = _apply_filters_to_query(stats_query, search, None, None,
                                             None, None, None, None, None)

        # 使用优化的聚合统计函数（仅2次数据库查询）
        raw_statistics = get_full_project_stats(stats_query, target_currency)

        # 提取统计数据
        total_count = raw_statistics.get('total_count', 0)
        active_count = raw_statistics.get('active_count', 0)
        inactive_count = raw_statistics.get('inactive_count', 0)
        total_value = raw_statistics.get('total_value', 0)
        stage_stats = raw_statistics.get('stage_stats', {})
    except Exception as e:
        logger.error(f"计算统计数据失败: {str(e)}")
        total_count = 0
        active_count = 0
        inactive_count = 0
        total_value = 0
        stage_stats = {}

    t3 = time.time()
    logger.info(f"⏱️ [性能] 统计数据计算: {(t3-t2)*1000:.0f}ms")

    # 获取系统货币符号
    default_currency = get_default_currency()
    currency_symbol = get_currency_symbol(default_currency)

    # 统计卡片配置（使用实际统计数据）
    amount_unit = '万美元' if current_lang == 'en' else '万元'

    stats_config = {
        'cards': [
            {
                'id': 'total',
                'title': _('全部项目'),
                'icon': 'fas fa-project-diagram',
                'value': total_count,
                'amount': round(total_value / 10000, 2),
                'unit': _('个'),
                'amount_unit': amount_unit,
                'currency_symbol': currency_symbol,
                'color': 'primary',
                'data_key': 'total'
            },
            {
                'id': 'active',
                'title': _('活跃项目'),
                'icon': 'fas fa-chart-line',
                'value': active_count,
                'unit': _('个'),
                'color': 'success',
                'data_key': 'active'
            },
            _create_stage_card('discover', '发现', 'fas fa-search', stage_stats, currency_symbol, 'info'),
            _create_stage_card('embed', '植入', 'fas fa-seedling', stage_stats, currency_symbol, 'success'),
            _create_stage_card('pre_tender', '招标前', 'fas fa-clipboard-list', stage_stats, currency_symbol, 'warning'),
            _create_stage_card('tendering', '招标中', 'fas fa-gavel', stage_stats, currency_symbol, 'warning'),
            _create_stage_card('awarded', '中标', 'fas fa-trophy', stage_stats, currency_symbol, 'success'),
            _create_stage_card('quoted', '批价', 'fas fa-dollar-sign', stage_stats, currency_symbol, 'warning'),
            _create_stage_card('signed', '签约', 'fas fa-handshake', stage_stats, currency_symbol, 'primary'),
            _create_stage_card('lost', '失败', 'fas fa-times-circle', stage_stats, currency_symbol, 'danger'),
            _create_stage_card('paused', '搁置', 'fas fa-pause-circle', stage_stats, currency_symbol, 'secondary')
        ]
    }


    # 筛选搜索配置
    filter_config = {
        'action_url': url_for('project.list_projects'),
        'form_id': 'projectFilterForm',
        'reset_url': url_for('project.list_projects'),
        'search_field': {
            'name': 'search',
            'label': _('搜索'),
            'placeholder': _('项目名称或客户名称'),
            'value': search,
            'col_width': 4
        },
        'filter_fields': [
            {
                'name': 'owner_id',
                'label': _(mapping_manager.get_field_display_name('project', 'owner_id')),
                'all_option_text': _('全部负责人'),
                'current_value': request.args.get('owner_id', ''),
                'col_width': 2,
                'options': (lambda: (
                    t4 := time.time(),
                    owner_opts := _get_project_owner_options(current_user),
                    t5 := time.time(),
                    logger.info(f"⏱️ [性能] 项目拥有者选项查询: {(t5-t4)*1000:.0f}ms"),
                    owner_opts
                )[-1])()
            },
            {
                'name': 'vendor_sales_manager_id',
                'label': _(mapping_manager.get_field_display_name('project', 'vendor_sales_manager_id')),
                'all_option_text': _('全部厂商销售'),
                'current_value': request.args.get('vendor_sales_manager_id', ''),
                'col_width': 2,
                'options': (lambda: (
                    t6 := time.time(),
                    vendor_opts := _get_vendor_manager_options(current_user),
                    t7 := time.time(),
                    logger.info(f"⏱️ [性能] 厂商负责人选项查询: {(t7-t6)*1000:.0f}ms"),
                    vendor_opts
                )[-1])()
            },
            {
                'name': 'is_active',
                'label': _(mapping_manager.get_field_display_name('common', 'is_active')),
                'all_option_text': _('全部状态'),
                'current_value': request.args.get('is_active', ''),
                'col_width': 2,
                'options': [
                    {'value': 'true', 'label': '活跃', 'translate': True},
                    {'value': 'false', 'label': '非活跃', 'translate': True}
                ]
            },
            {
                'name': 'industry',
                'label': _(mapping_manager.get_field_display_name('project', 'industry')),
                'all_option_text': _('全部行业'),
                'current_value': request.args.get('industry', ''),
                'col_width': 2,
                'options': [
                    {'value': k, 'label': v, 'translate': False}
                    for k, v in get_industry_options()
                ]
            },
            {
                'name': 'report_source',
                'label': _(mapping_manager.get_field_display_name('project', 'report_source')),
                'all_option_text': _('全部来源'),
                'current_value': request.args.get('report_source', ''),
                'col_width': 2,
                'options': [
                    {'value': k, 'label': v, 'translate': False}
                    for k, v in get_report_source_options()
                ]
            },
            {
                'name': 'current_stage',
                'label': _('项目阶段'),
                'all_option_text': _('全部阶段'),
                'current_value': request.args.get('current_stage', ''),
                'col_width': 3,
                'options': [
                    {'value': 'discover', 'label': '发现', 'translate': True},
                    {'value': 'embed', 'label': '植入', 'translate': True},
                    {'value': 'pre_tender', 'label': '招标前', 'translate': True},
                    {'value': 'tendering', 'label': '招标中', 'translate': True},
                    {'value': 'awarded', 'label': '中标', 'translate': True},
                    {'value': 'quoted', 'label': '批价', 'translate': True},
                    {'value': 'signed', 'label': '签约', 'translate': True},
                    {'value': 'lost', 'label': '失败', 'translate': True},
                    {'value': 'paused', 'label': '搁置', 'translate': True}
                ]
            },
            {
                'name': 'project_type',
                'label': '项目类型',
                'all_option_text': '全部类型',
                'current_value': request.args.get('project_type', ''),
                'col_width': 2,
                'options': [
                    {'value': k, 'label': v, 'translate': False}
                    for k, v in get_project_type_options()
                ]
            }
        ],
        'search_button_text': _('搜索'),
        'reset_button_text': _('重置'),
        # 添加关键配置，与报价单模块保持一致
        'auto_submit': True,           # 启用自动提交，确保初始数据加载
        'ajax_mode': True,            # 启用AJAX模式
        'dynamic_reset_button': True,  # 启用动态重置按钮
        'adaptive_width': True,        # 启用自适应宽度
        'adaptive_button_layout': True # 启用自适应按钮布局
    }
    
    # 表格配置 - 支持动态字段映射
    table_config = {
        'ajax_target': 'projectTableBody',
        'title': _('项目列表'),
        'icon': 'fas fa-table',
        'show_header': True,
        'enhanced_striping': True,  # 启用增强斑马线
        'fixed_height_scroll': True,  # 启用列表内滚动
        'table_name': 'project',  # 新增：指定数据库表名用于动态映射
        'columns': [
            {
                'key': 'owner', 
                'field': 'owner_id',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'owner_id')),
                'type': 'custom',
                'render': 'render_owner',
                'width': '120px'
            },
            {
                'key': 'vendor_sales_manager', 
                'field': 'vendor_sales_manager_id',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'vendor_sales_manager_id')),
                'type': 'custom',
                'render': 'render_owner',
                'width': '120px'
            },
            {
                'key': 'authorization_code', 
                'field': 'authorization_code',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'authorization_code')),
                'type': 'custom',
                'render': 'render_project_authorization',
                'width': '120px'
            },
            {
                'key': 'project_name', 
                'field': 'project_name',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'project_name')),
                'type': 'link',
                'url_template': '/project/view/{id}',
                'width': '200px'
            },
            {
                'key': 'is_active', 
                'field': 'is_active',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('common', 'is_active')),
                'type': 'custom',
                'render': 'render_status_badge',
                'width': '80px'
            },
            {
                'key': 'current_stage', 
                'field': 'current_stage',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'current_stage')),
                'type': 'custom',
                'render': 'render_project_stage',
                'width': '120px'
            },
            {
                'key': 'project_type', 
                'field': 'project_type',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'project_type')),
                'type': 'custom',
                'render': 'render_project_type',
                'width': '100px',
                'align': 'start'
            },
            {
                'key': 'quotation_customer', 
                'field': 'quotation_customer',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'quotation_customer')), 
                'type': 'number',
                'format': 'currency',
                'sort_type': 'currency',  # 新增：排序类型
                'width': '120px', 
                'align': 'end'
            },
            {
                'key': 'industry', 
                'field': 'industry',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'industry')), 
                'type': 'custom',
                'render': 'render_industry_badge',
                'width': '100px'
            },
            {
                'key': 'report_source', 
                'field': 'report_source',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'report_source')), 
                'type': 'custom',
                'render': 'render_report_source_badge',
                'width': '100px'
            },
            {
                'key': 'delivery_forecast', 
                'field': 'delivery_forecast',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('project', 'delivery_forecast')), 
                'type': 'date',
                'format': '%Y-%m-%d',
                'sort_type': 'date',  # 新增：排序类型
                'width': '150px'
            },
            {
                'key': 'updated_at', 
                'field': 'updated_at',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('common', 'updated_at')), 
                'type': 'date',
                'format': '%Y-%m-%d %H:%M',
                'sort_type': 'date',  # 新增：排序类型
                'width': '150px'
            },
            {
                'key': 'created_at', 
                'field': 'created_at',  # 新增：指定对应的数据库字段名
                'label': _(mapping_manager.get_field_display_name('common', 'created_at')), 
                'type': 'date',
                'format': '%Y-%m-%d %H:%M',
                'sort_type': 'date',  # 新增：排序类型
                'width': '150px'
            }
        ]
    }
    
    # 通用列表配置
    list_config = {
        'module_name': 'project',
        'title': None,  # 页面级标题由模板控制，此处不显示
        'ajax_mode': True,  # 启用AJAX模式
        'ajax_endpoint': url_for('project.project_list_ajax'),  # AJAX端点
        
        # 无限滚动配置 - 恢复正常无限滚动功能
        'infinite_scroll': {
            'enabled': True,
            'page_size': 30,
            'scroll_threshold': 100,
            'container_selector': '.table-responsive'
        },
        
        'stats': stats_config,
        'filter': filter_config,
        'table': table_config,
    }

    # 传递keep_panel参数到模板
    t8 = time.time()
    logger.info(f"⏱️ [性能] 配置构建完成: {(t8-t3)*1000:.0f}ms")

    result = render_template(
        'project/list.html',
        projects=projects,
        search_term=search,
        Quotation=Quotation,
        filter_params=filter_params,
        keep_panel=keep_panel,
        INDUSTRY_OPTIONS=get_industry_options(),
        PROJECT_TYPE_OPTIONS=get_project_type_options(),
        REPORT_SOURCE_OPTIONS=get_report_source_options(),
        list_config=list_config
    )

    t9 = time.time()
    logger.info(f"⏱️ [性能] 模板渲染: {(t9-t8)*1000:.0f}ms")
    logger.info(f"⏱️ [性能] ===== 总耗时: {(t9-start_time)*1000:.0f}ms =====")

    return result

@project.route('/api/projects/filter', methods=['GET'])
@login_required
@permission_required('project', 'view')
def project_list_ajax():
    """项目列表AJAX筛选API"""
    try:
        current_app.logger.info("项目AJAX端点被调用")
        
        # 获取搜索和筛选参数
        search = request.args.get('search', '').strip()
        owner_id = request.args.get('owner_id', '')
        vendor_sales_manager_id = request.args.get('vendor_sales_manager_id', '')
        is_active = request.args.get('is_active', '')
        industry = request.args.get('industry', '')
        report_source = request.args.get('report_source', '')
        current_stage = request.args.get('current_stage', '')
        project_type = request.args.get('project_type', '')
        
        # 分页参数 - 默认30条支持无限滚动
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 30, type=int)
        
        # 排序参数
        sort_field = request.args.get('sort_field', '')
        sort_direction = request.args.get('sort_direction', 'asc')
        
        # 限制每次加载数量范围
        if limit > 100:
            limit = 100  # 最大100条防止性能问题
        
        current_app.logger.info(f"筛选参数: search={search}, owner_id={owner_id}, current_stage={current_stage}")
        
        # 基础查询
        try:
            query = get_viewable_data(Project, current_user)
            # 预加载关联数据
            query = query.options(
                joinedload(Project.owner),
                joinedload(Project.vendor_sales_manager)
            )
            current_app.logger.info("基础查询创建成功")
        except Exception as e:
            current_app.logger.error(f"基础查询创建失败: {e}")
            raise
        
        # 应用搜索条件
        if search:
            try:
                query = query.filter(
                    or_(
                        Project.project_name.ilike(f'%{search}%'),
                        Project.authorization_code.ilike(f'%{search}%')
                    )
                )
                current_app.logger.info(f"应用搜索条件: {search}")
            except Exception as e:
                current_app.logger.error(f"应用搜索条件失败: {e}")
        
        # 应用筛选条件
        if owner_id:
            try:
                query = query.filter(Project.owner_id == owner_id)
                current_app.logger.info(f"应用拥有人筛选: {owner_id}")
            except Exception as e:
                current_app.logger.error(f"应用拥有人筛选失败: {e}")
        
        if vendor_sales_manager_id:
            try:
                query = query.filter(Project.vendor_sales_manager_id == vendor_sales_manager_id)
                current_app.logger.info(f"应用厂商负责人筛选: {vendor_sales_manager_id}")
            except Exception as e:
                current_app.logger.error(f"应用厂商负责人筛选失败: {e}")
        
        if is_active:
            try:
                is_active_value = is_active.lower() == 'true'
                query = query.filter(Project.is_active == is_active_value)
                current_app.logger.info(f"应用活跃状态筛选: {is_active}")
            except Exception as e:
                current_app.logger.error(f"应用活跃状态筛选失败: {e}")
        
        if industry:
            try:
                query = query.filter(Project.industry == industry)
                current_app.logger.info(f"应用行业筛选: {industry}")
            except Exception as e:
                current_app.logger.error(f"应用行业筛选失败: {e}")
        
        if report_source:
            try:
                query = query.filter(Project.report_source == report_source)
                current_app.logger.info(f"应用来源筛选: {report_source}")
            except Exception as e:
                current_app.logger.error(f"应用来源筛选失败: {e}")
        
        if current_stage:
            try:
                query = query.filter(Project.current_stage == current_stage)
                current_app.logger.info(f"应用项目阶段筛选: {current_stage}")
            except Exception as e:
                current_app.logger.error(f"应用项目阶段筛选失败: {e}")
        
        if project_type:
            try:
                query = query.filter(Project.project_type == project_type)
                current_app.logger.info(f"应用项目类型筛选: {project_type}")
            except Exception as e:
                current_app.logger.error(f"应用项目类型筛选失败: {e}")
        
        # 计算总数
        total_count = query.count()
        
        # 使用通用排序服务
        from app.utils.sorting_service import SortingService, create_user_relation_config, create_basic_field_mappings
        from app.models.user import User
        
        # 创建排序配置
        sorting_config = {
            'field_mappings': create_basic_field_mappings(Project, [
                'project_name', 'current_stage', 'quotation_customer', 'delivery_forecast', 
                'report_source', 'created_at', 'updated_at'
            ]),
            'relation_mappings': {
                'owner_id': create_user_relation_config(Project.owner_id),
                'vendor_sales_manager_id': create_user_relation_config(Project.vendor_sales_manager_id)
            },
            'default_sort': {'field': 'updated_at', 'direction': 'desc'}
        }
        
        # 创建排序服务并应用排序
        sorting_service = SortingService(Project, sorting_config)
        query = sorting_service.apply_sort(query, sort_field, sort_direction)
        
        # 获取项目数据（应用分页）
        try:
            projects = query.offset(offset).limit(limit).all()
            current_app.logger.info(f"查询到 {len(projects)} 条项目 (总数: {total_count})")
        except Exception as e:
            current_app.logger.error(f"查询项目失败: {e}")
            raise
        
        # 响应式渲染 - 根据设备类型返回不同格式
        try:
            from app.utils.mobile_helpers import is_mobile_request
            from flask import render_template, render_template_string
            
            if is_mobile_request():
                # 移动端：使用智能移动端卡片配置
                use_smart_card = request.args.get('use_smart_card', 'true').lower() == 'true'
                
                if use_smart_card:
                    # 项目智能卡片配置
                    smart_card_config = {
                        'module': 'project',
                        'title_field': {'field': 'project_name'},
                        'link_url': '/project/view/{id}',
                        'badges': [
                            {'field': 'current_stage', 'renderer': 'project_stage'},
                            {'field': 'is_active', 'renderer': 'status_badge'},
                            {'field': 'project_type', 'renderer': 'project_type'}
                        ],
                        'details': [
                            {'field': 'authorization_code', 'label': '授权编号', 'renderer': 'render_project_authorization'},
                            {'field': 'owner', 'label': '拥有者', 'renderer': 'owner'},
                            {'field': 'vendor_sales_manager', 'label': '厂商负责人', 'renderer': 'owner'},
                            {'field': 'industry', 'label': '行业', 'renderer': 'industry_badge'},
                            {'field': 'report_source', 'label': '来源', 'renderer': 'report_source_badge'},
                            {'field': 'quotation_customer', 'label': '报价金额', 'format': 'currency'},
                            {'field': 'delivery_forecast', 'label': _('预测出货时间'), 'format': 'date'},
                            {'field': 'updated_at', 'label': '更新时间', 'format': 'datetime'}
                        ]
                    }
                    html = render_template_string('''
                        {% from 'macros/ui_helpers.html' import render_smart_mobile_cards %}
                        {{ render_smart_mobile_cards(projects, card_config) }}
                    ''', projects=projects, card_config=smart_card_config)
                    current_app.logger.info("智能移动端卡片渲染成功")
                else:
                    # 兼容传统移动端模板（如果存在）
                    try:
                        html = render_template('project/project_cards.html', items=projects)
                        current_app.logger.info("传统移动端模板渲染成功")
                    except Exception:
                        # 传统模板不存在，回退到智能卡片
                        html = render_template_string('''
                            {% from 'macros/ui_helpers.html' import render_smart_mobile_cards %}
                            {{ render_smart_mobile_cards(projects, card_config) }}
                        ''', projects=projects, card_config=smart_card_config)
                        current_app.logger.info("回退到智能移动端卡片渲染")
            else:
                # 桌面端：使用表格渲染
                table_columns = [
                    {'key': 'owner', 'label': _(mapping_manager.get_field_display_name('project', 'owner_id')), 'type': 'custom', 'render': 'render_owner', 'width': '120px'},
                    {'key': 'vendor_sales_manager', 'label': _(mapping_manager.get_field_display_name('project', 'vendor_sales_manager_id')), 'type': 'custom', 'render': 'render_owner', 'width': '120px'},
                    {'key': 'authorization_code', 'label': _(mapping_manager.get_field_display_name('project', 'authorization_code')), 'type': 'custom', 'render': 'render_project_authorization', 'width': '120px'},
                    {'key': 'project_name', 'label': _(mapping_manager.get_field_display_name('project', 'project_name')), 'type': 'link', 'url_template': '/project/view/{id}', 'width': '200px'},
                    {'key': 'is_active', 'label': _(mapping_manager.get_field_display_name('common', 'is_active')), 'type': 'custom', 'render': 'render_status_badge', 'width': '80px'},
                    {'key': 'current_stage', 'label': _(mapping_manager.get_field_display_name('project', 'current_stage')), 'type': 'custom', 'render': 'render_project_stage', 'width': '120px'},
                    {'key': 'project_type', 'label': _(mapping_manager.get_field_display_name('project', 'project_type')), 'type': 'custom', 'render': 'render_project_type', 'width': '100px', 'align': 'start'},
                    {'key': 'quotation_customer', 'label': _(mapping_manager.get_field_display_name('project', 'quotation_customer')), 'type': 'number', 'format': 'currency', 'width': '120px', 'align': 'end'},
                    {'key': 'industry', 'label': _(mapping_manager.get_field_display_name('project', 'industry')), 'type': 'custom', 'render': 'render_industry_badge', 'width': '100px'},
                    {'key': 'report_source', 'label': _(mapping_manager.get_field_display_name('project', 'report_source')), 'type': 'custom', 'render': 'render_report_source_badge', 'width': '100px'},
                    {'key': 'delivery_forecast', 'label': _(mapping_manager.get_field_display_name('project', 'delivery_forecast')), 'type': 'date', 'format': '%Y-%m-%d', 'width': '150px'},
                    {'key': 'updated_at', 'label': _(mapping_manager.get_field_display_name('common', 'updated_at')), 'type': 'date', 'format': '%Y-%m-%d %H:%M', 'width': '150px'},
                    {'key': 'created_at', 'label': _(mapping_manager.get_field_display_name('common', 'created_at')), 'type': 'date', 'format': '%Y-%m-%d %H:%M', 'width': '150px'}
                ]
                html = render_template('project/project_rows_standard.html', projects=projects, table_columns=table_columns)
                current_app.logger.info("桌面端表格渲染成功")
        except Exception as e:
            current_app.logger.error(f"标准组件模板渲染失败: {e}")
            html = f'<tr><td colspan="12" class="text-center text-muted">渲染失败: {str(e)}</td></tr>'

        # 获取货币配置信息（必须在统计计算之前）
        from app.utils.i18n import get_current_language, get_default_currency, get_currency_symbol
        current_lang = get_current_language()
        default_currency = get_default_currency()
        currency_symbol = get_currency_symbol(default_currency)

        # 计算统计数据 - 使用高效的聚合查询算法
        try:
            # 构建筛选查询（不包含current_stage筛选，以显示各阶段统计）
            stats_query = get_viewable_data(Project, current_user)

            # 应用筛选条件
            stats_query = _apply_filters_to_query(stats_query, search, owner_id, vendor_sales_manager_id,
                                                is_active, industry, report_source, project_type, None)

            # 使用优化的聚合统计函数
            raw_statistics = get_full_project_stats(stats_query, default_currency)

            # 格式化统计数据
            statistics = _format_stats_for_ajax(raw_statistics)
            
        except Exception as e:
            current_app.logger.error(f"计算统计数据失败: {e}")
            statistics = {
                'total': 0,
                'total_amount': 0,
                'discover': 0,
                'embed': 0,
                'pre_tender': 0,
                'tendering': 0,
                'awarded': 0,
                'quoted': 0,
                'signed': 0,
                'lost': 0,
                'paused': 0
            }

        # 返回JSON响应（包含货币配置）
        return jsonify({
            'success': True,
            'html': html,
            'has_more': (offset + limit) < total_count,
            'total_count': total_count,
            'loaded_count': offset + len(projects),
            'statistics': statistics,
            'currency_symbol': currency_symbol,  # 添加货币符号配置
            'currency': default_currency,  # 添加货币类型配置
            'language': current_lang  # 添加语言配置
        })
        
    except Exception as e:
        current_app.logger.error(f"项目列表AJAX请求失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'html': f'<tr><td colspan="11" class="text-center text-danger">加载失败: {str(e)}</td></tr>'
        }), 500

@project.route('/view/<int:project_id>')
@permission_required_with_approval_context('project', 'view')
def view_project(project_id):
    # 导入权限检查函数，确保在所有代码路径中都可用
    from app.permissions import is_admin_or_ceo
    
    # 使用统一的权限检查逻辑
    from app.utils.access_control import get_viewable_data
    viewable_projects = get_viewable_data(Project, current_user).options(
        joinedload(Project.creator),              # 预加载创建人
        joinedload(Project.owner),                # 预加载当前负责人
        joinedload(Project.vendor_sales_manager)  # 预加载厂商销售负责人
    )
    project = viewable_projects.filter_by(id=project_id).first()

    if not project:
        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试查看无权限的项目: {project_id}")
        flash('您没有权限查看此项目', 'danger')
        return redirect(url_for('project.list_projects'))
    
    # 查询相关单位对应的企业ID并检查访问权限
    from app.utils.access_control import can_view_company
    related_companies = {}
    
    # 查询直接用户
    if project.end_user:
        end_user_company = Company.query.filter_by(company_name=project.end_user, is_deleted=False).first()
        if end_user_company:
            can_view = can_view_company(current_user, end_user_company)
            logger.debug(f"权限检查 - 用户 {current_user.username} (ID: {current_user.id}) 访问企业 '{end_user_company.company_name}' (ID: {end_user_company.id}, 拥有者: {end_user_company.owner_id}): {can_view}")
            if can_view:
                related_companies['end_user'] = end_user_company.id
            else:
                related_companies['end_user'] = None
        else:
            related_companies['end_user'] = None
    
    # 查询设计院及顾问
    if project.design_issues:
        design_company = Company.query.filter_by(company_name=project.design_issues, is_deleted=False).first()
        if design_company and can_view_company(current_user, design_company):
            related_companies['design_issues'] = design_company.id
        else:
            related_companies['design_issues'] = None
    
    # 查询经销商
    if project.dealer:
        dealer_company = Company.query.filter_by(company_name=project.dealer, is_deleted=False).first()
        if dealer_company and can_view_company(current_user, dealer_company):
            related_companies['dealer'] = dealer_company.id
        else:
            related_companies['dealer'] = None
    
    # 查询总承包单位
    if project.contractor:
        contractor_company = Company.query.filter_by(company_name=project.contractor, is_deleted=False).first()
        if contractor_company and can_view_company(current_user, contractor_company):
            related_companies['contractor'] = contractor_company.id
        else:
            related_companies['contractor'] = None
    
    # 查询系统集成商
    if project.system_integrator:
        integrator_company = Company.query.filter_by(company_name=project.system_integrator, is_deleted=False).first()
        if integrator_company and can_view_company(current_user, integrator_company):
            related_companies['system_integrator'] = integrator_company.id
        else:
            related_companies['system_integrator'] = None
    
    # 解析阶段变更历史，生成stageHistory结构
    # 优先使用project_stage_history表中的数据，如果没有则从stage_description解析
    from app.models.projectpm_stage_history import ProjectStageHistory
    
    stage_history = []
    history_records = ProjectStageHistory.query.filter_by(project_id=project_id).order_by(ProjectStageHistory.change_date).all()
    
    if history_records:
        # 使用project_stage_history表中的数据，去除重复记录
        # 按阶段变更去重，保留最新的记录
        unique_records = []
        seen_changes = set()
        for record in history_records:
            change_key = f"{record.from_stage}->{record.to_stage}"
            if change_key not in seen_changes:
                unique_records.append(record)
                seen_changes.add(change_key)
            else:
                # 如果是重复的变更，保留时间更晚的记录
                for i, existing in enumerate(unique_records):
                    if f"{existing.from_stage}->{existing.to_stage}" == change_key:
                        if record.change_date > existing.change_date:
                            unique_records[i] = record
                        break
        
        current_stage_start = None
        for i, record in enumerate(unique_records):
            if i == 0:
                # 第一条记录，需要添加初始阶段（如果有from_stage）
                if record.from_stage:
                    stage_history.append({
                        'stage': record.from_stage,
                        'startDate': str(project.report_time) if project.report_time else '',
                        'endDate': str(record.change_date)
                    })
                # 添加变更后的阶段
                stage_history.append({
                    'stage': record.to_stage,
                    'startDate': str(record.change_date),
                    'endDate': None
                })
                current_stage_start = str(record.change_date)
            else:
                # 后续记录，更新上一个阶段的endDate，添加新阶段
                if stage_history:
                    stage_history[-1]['endDate'] = str(record.change_date)
                stage_history.append({
                    'stage': record.to_stage,
                    'startDate': str(record.change_date),
                    'endDate': None
                })
                current_stage_start = str(record.change_date)
        
        # 确保当前阶段是最后一个阶段
        if stage_history and stage_history[-1]['stage'] != project.current_stage:
            # 如果最后一个历史记录的阶段与当前阶段不一致，添加当前阶段
            stage_history.append({
                'stage': project.current_stage,
                'startDate': current_stage_start or str(project.report_time) if project.report_time else '',
                'endDate': None
            })
    else:
        # 没有project_stage_history记录，尝试从stage_description解析
        if project.stage_description:
            # 匹配形如：[阶段变更] 阶段A → 阶段B (更新者: xxx, 时间: yyyy-mm-dd HH:MM:SS)
            pattern = re.compile(r'\[阶段变更\][^\n]*?([\u4e00-\u9fa5A-Za-z0-9_]+) ?(?:→|-) ?([\u4e00-\u9fa5A-Za-z0-9_]+).*?时间: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
            matches = list(pattern.finditer(project.stage_description))
            # 按时间顺序生成阶段历史
            for i, match in enumerate(matches):
                from_stage, to_stage, change_time = match.group(1), match.group(2), match.group(3)
                # 上一个阶段的endDate为本次变更时间
                if i == 0:
                    # 项目创建时的阶段
                    stage_history.append({
                        'stage': from_stage,
                        'startDate': str(project.report_time) if project.report_time else '',
                        'endDate': change_time
                    })
                else:
                    # 上一个to_stage的endDate为本次变更时间
                    stage_history[-1]['endDate'] = change_time
                # 新阶段的startDate为本次变更时间
                stage_history.append({
                    'stage': to_stage,
                    'startDate': change_time,
                    'endDate': None
                })
            # 如果没有任何变更记录，只有当前阶段
            if not matches:
                stage_history.append({
                    'stage': project.current_stage,
                    'startDate': str(project.report_time) if project.report_time else '',
                    'endDate': None
                })
        else:
            # 没有历史，只有当前阶段
            stage_history.append({
                'stage': project.current_stage,
                'startDate': str(project.report_time) if project.report_time else '',
                'endDate': None
            })

    # 查询项目相关的行动记录，按时间倒序排列
    from app.utils.access_control import get_viewable_data
    
    # 如果是项目拥有者，可以看到所有相关的行动记录
    if current_user.id == project.owner_id or current_user.role == 'admin':
        project_actions = Action.query.filter_by(project_id=project_id).order_by(Action.date.desc(), Action.created_at.desc()).all()
    else:
        # 其他用户只能看到有权限查看的行动记录
        project_actions = get_viewable_data(Action, current_user, special_filters=[Action.project_id == project_id]).order_by(Action.date.desc(), Action.created_at.desc()).all()

    # 传递原始阶段key给前端用于条件判断，避免语言切换时的问题
    current_stage_key = project.current_stage

    # 确保阶段历史中的阶段名称也转换为中文
    for stage_item in stage_history:
        stage_name = stage_item['stage']
        if stage_name in PROJECT_STAGE_LABELS:
            stage_item['stage'] = PROJECT_STAGE_LABELS[stage_name]['zh']
        # 如果已经是中文名，保持不变

    # 查询可选新拥有人
    all_users = []
    if can_change_project_owner(current_user, project):
        if is_admin_or_ceo():
            all_users = User.query.all()
        elif getattr(current_user, 'is_department_manager', False) or current_user.role == 'sales_director':
            all_users = User.query.filter(
                or_(User.role == 'admin', User._is_active == True),
                User.department == current_user.department
            ).all()
        else:
            # 包含有数据归属的账户，即使不在同公司/部门
            # 1. 当前用户自己
            # 2. 当前项目拥有者
            base_user_ids = {current_user.id, project.owner_id}
            
            # 3. 通过归属关系，用户可以将数据转移给的账户
            from app.models.user import Affiliation
            
            # 用户可以查看的数据的拥有者（双向关系）
            # - 用户作为viewer，可以查看的数据的owner
            viewer_affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
            viewer_accessible_owner_ids = {a.owner_id for a in viewer_affiliations}
            
            # - 用户作为owner，将数据归属给的viewer（可以将数据转移给这些用户）
            owner_affiliations = Affiliation.query.filter_by(owner_id=current_user.id).all()
            owner_accessible_viewer_ids = {a.viewer_id for a in owner_affiliations}
            
            # 合并所有可访问的用户ID
            all_accessible_user_ids = base_user_ids.union(viewer_accessible_owner_ids).union(owner_accessible_viewer_ids)
            
            # 查询这些用户，确保只包含活跃用户
            all_users = User.query.filter(
                User.id.in_(all_accessible_user_ids),
                or_(User.role == 'admin', User._is_active == True)
            ).all()
            
        if not all_users:
            all_users = User.query.filter(User.id.in_([current_user.id, project.owner_id])).all()
    has_change_owner_permission = can_change_project_owner(current_user, project)

    # 生成用户树状数据
    from app.utils.user_helpers import generate_user_tree_data_from_users
    user_tree_data = None
    if has_change_owner_permission:
        # 使用已筛选的用户列表生成树状数据，而不是使用默认的权限过滤
        user_tree_data = generate_user_tree_data_from_users(all_users)

    # 获取系统设置
    settings = {
        "project_activity_threshold": SystemSettings.get('project_activity_threshold', 30)
    }


    # 判断当前用户是否可以编辑项目阶段
    can_edit_stage = False
    if current_user.has_permission('project', 'edit'):
        # 检查项目是否被锁定
        from app.helpers.project_helpers import is_project_editable
        is_editable, lock_reason = is_project_editable(project_id, current_user.id)
        
        # 检查用户权限
        if is_admin_or_ceo():
            can_edit_stage = True
        elif project.owner_id == current_user.id:
            can_edit_stage = True and (is_editable or is_admin_or_ceo())
        elif project.vendor_sales_manager_id == current_user.id:
            # 厂商负责人享有与拥有人同等的编辑权限
            can_edit_stage = True and (is_editable or is_admin_or_ceo())
        else:
            # 对于非拥有者和非厂商负责人，需要检查是否在可查看用户列表中，但渠道经理等角色不能编辑其他人的项目
            allowed_user_ids = current_user.get_viewable_user_ids() if hasattr(current_user, 'get_viewable_user_ids') else [current_user.id]
            if project.owner_id in allowed_user_ids:
                # 即使可以查看，也不能编辑其他人的项目（除非是管理员）
                can_edit_stage = False

    # 预先计算关系数据，避免模板中的错误
    has_quotations = project.quotations.count() > 0
    has_pricing_orders = False
    pricing_orders_list = []
    try:
        from app.models.pricing_order import PricingOrder
        pricing_orders_list = PricingOrder.query.filter_by(project_id=project.id).order_by(PricingOrder.created_at.desc()).all()
        has_pricing_orders = len(pricing_orders_list) > 0
    except Exception:
        has_pricing_orders = False
        pricing_orders_list = []

    # 添加语言支持
    from app.utils.i18n import get_current_language
    current_language = get_current_language()
    
    # 检查共享权限和获取可共享用户
    from app.utils.sharing import SharingService, get_shareable_users_tree
    can_edit_sharing = SharingService.can_edit_sharing_settings(current_user, project, 'project')
    
    # 检查是否能查看共享设置（即使不能编辑）
    can_view_sharing = False
    if current_user.has_permission('project', 'view'):
        permission_level = current_user.get_permission_level('project')
        if permission_level in ['system', 'company', 'department']:
            can_view_sharing = True
    
    if can_edit_sharing:
        shareable_users_tree = get_shareable_users_tree(current_user, 'project')
        logger.info(f"用户 {current_user.username} 的共享用户树结构已生成")
    else:
        shareable_users_tree = []
    
    # 检查用户是否可以添加客户关联（基于查看权限）
    # 只要能查看项目，就可以添加客户关联
    can_edit_project_data = True  # 如果能执行到这里，说明已经通过了查看权限检查
    
    return render_template("project/detail.html", 
                         project=project, 
                         Quotation=Quotation, 
                         related_companies=related_companies, 
                         stageHistory=stage_history, 
                         project_actions=project_actions, 
                         current_stage_key=current_stage_key, 
                         all_users=all_users, 
                         has_change_owner_permission=has_change_owner_permission, 
                         user_tree_data=user_tree_data, 
                         settings=settings, 
                         can_edit_stage=can_edit_stage,
                         # 预计算的关系数据
                         has_quotations=has_quotations,
                         has_pricing_orders=has_pricing_orders,
                         pricing_orders_list=pricing_orders_list,
                         # 添加审批相关函数
                         get_object_approval_instance=get_object_approval_instance,
                         get_available_templates=get_available_templates,
                         can_start_approval=can_start_approval,
                         # 添加语言支持
                         current_language=current_language,
                         # 共享权限和用户
                         can_edit_sharing=can_edit_sharing,
                         can_view_sharing=can_view_sharing,
                         shareable_users_tree=shareable_users_tree,
                         # 数据权限
                         can_edit_project_data=can_edit_project_data,
                         # 中文映射管理器
                         mapping_manager=mapping_manager)

@project.route('/add', methods=['GET', 'POST'])
@permission_required('project', 'create')
def add_project():
    if request.method == 'POST':
        try:
            # 验证必填字段
            if not request.form.get('project_name'):
                flash('项目名称不能为空', 'danger')
                return render_template('project/add.html', **get_project_form_data())
            # 报备日期不再强制要求，将在授权批准后自动设置
            # if not request.form.get('report_time'):
            #     flash('报备日期不能为空', 'danger')
            #     return render_template('project/add.html', **get_project_form_data())
            # 当前阶段不在创建页面显示，默认设为'discover'阶段
            # if not request.form.get('current_stage'):
            #     flash('当前阶段不能为空', 'danger')
            #     return render_template('project/add.html', **get_project_form_data())
            if not request.form.get('industry'):
                flash('项目行业不能为空', 'danger')
                return render_template('project/add.html', **get_project_form_data())
            
            # 解析日期 - 只有在授权批准后才设置报备日期，创建时不设置
            report_time = None  # 初始创建时不设置报备日期
            # if request.form.get('report_time'):
            #     report_time = datetime.strptime(request.form['report_time'], '%Y-%m-%d').date()
                
            delivery_forecast = None
            if request.form.get('delivery_forecast'):
                delivery_forecast = datetime.strptime(request.form['delivery_forecast'], '%Y-%m-%d').date()
            
            # 获取项目类型
            from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS
            project_type = request.form.get('project_type', '').strip()
            if not project_type:
                project_type = None
            elif project_type not in PROJECT_TYPE_LABELS:
                # 反查中文 label 对应的 key
                reverse_lookup = {v['zh']: k for k, v in PROJECT_TYPE_LABELS.items()}
                project_type = reverse_lookup.get(project_type, None)
            # 如果 project_type 是合法英文 key，则保留原样
            
            # 不再自动生成授权编号，授权编号必须通过申请流程获得
            authorization_code = None
            
            # 报价字段设置为无效，不处理
            quotation_customer = None
            
            # 自动设置销售负责人
            vendor_sales_manager_id = request.form.get('vendor_sales_manager_id')
            
            # 如果厂商销售负责人字段为空，默认将拥有人账户作为内容
            if not vendor_sales_manager_id and current_user.is_vendor_user():
                vendor_sales_manager_id = current_user.id
            
            project = Project(
                project_name=request.form['project_name'],
                report_time=report_time,
                report_source=request.form.get('report_source'),
                product_situation=request.form.get('product_situation'),
                design_issues=request.form.get('design_issues'),
                delivery_forecast=delivery_forecast,
                current_stage='discover',  # 默认从发现阶段开始
                dealer=request.form.get('dealer'),
                end_user=request.form.get('end_user'),
                contractor=request.form.get('contractor'),
                system_integrator=request.form.get('system_integrator'),
                stage_description=request.form.get('stage_description'),
                authorization_code=authorization_code,
                project_type=project_type,
                quotation_customer=quotation_customer,
                industry=request.form.get('industry'),  # 添加行业字段
                created_by=current_user.id,  # 设置创建人（不可变）
                owner_id=current_user.id,  # 设置当前负责人（可修改）
                vendor_sales_manager_id=vendor_sales_manager_id  # 设置厂商销售负责人
            )
            
            db.session.add(project)
            db.session.commit()
            
            # 记录创建历史
            try:
                ChangeTracker.log_create(project)
            except Exception as track_err:
                logger.warning(f"记录项目创建历史失败: {str(track_err)}")
            
            # 新增：每次保存后自动刷新活跃度
            update_active_status(project)
            
            # 项目保存后触发评分重新计算
            try:
                from app.models.project_scoring import ProjectScoringEngine
                ProjectScoringEngine.calculate_project_score(project.id, commit=True)
                current_app.logger.info(f"项目 {project.project_name} 更新后评分已重新计算")
            except Exception as score_err:
                current_app.logger.warning(f"项目更新后评分重新计算失败: {str(score_err)}")
            
            # 异步触发项目创建通知，避免阻塞保存操作
            try:
                import threading
                from app.services.event_dispatcher import notify_project_created
                from app.utils.solution_manager_notifications import notify_solution_managers_project_created
                
                def send_notifications_async():
                    """异步发送通知"""
                    with current_app.app_context():
                        try:
                            # 触发项目创建通知
                            notify_project_created(project, current_user)
                            # 通知解决方案经理
                            notify_solution_managers_project_created(project)
                            current_app.logger.debug('异步项目创建通知已发送')
                        except Exception as notify_err:
                            current_app.logger.warning(f"异步触发项目创建通知失败: {str(notify_err)}")
                
                # 启动异步通知线程
                threading.Thread(target=send_notifications_async, daemon=True).start()
                current_app.logger.debug('异步项目创建通知线程已启动')
                
            except Exception as notify_err:
                logger.warning(f"启动异步项目创建通知失败: {str(notify_err)}")
            
            # 更新相关客户的活跃状态
            # 查找与项目相关的所有企业名称
            related_companies = []
            if project.end_user:
                related_companies.append(project.end_user)
            if project.design_issues:
                related_companies.append(project.design_issues)
            if project.contractor:
                related_companies.append(project.contractor)
            if project.system_integrator:
                related_companies.append(project.system_integrator)
            if project.dealer:
                related_companies.append(project.dealer)
                
            # 查找匹配的企业ID并更新活跃状态
            for company_name in set(related_companies):
                company = Company.query.filter_by(company_name=company_name, is_deleted=False).first()
                if company:
                    check_company_activity(company_id=company.id)
            
            flash('项目添加成功！', 'success')
            return redirect(url_for('project.view_project', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存项目失败: {str(e)}", exc_info=True)
            flash(f'保存失败：{str(e)}', 'danger')
            return render_template('project/add.html', **get_project_form_data())
    
    return render_template(
        'project/add.html',
        **get_project_form_data()
    )

# 辅助函数，获取公司数据
def get_company_data():
    company_query = get_viewable_data(Company, current_user)
    return {
        key: company_query.filter_by(company_type=key).all()
        for key in COMPANY_TYPE_LABELS.keys()
    }

# 新的项目表单数据逻辑函数
def get_project_form_data():
    """获取项目表单需要的数据（创建和编辑通用）"""
    return {
        'PRODUCT_SITUATION_OPTIONS': get_product_situation_options(),
        'REPORT_SOURCE_OPTIONS': get_report_source_options(),
        'PROJECT_TYPE_OPTIONS': get_project_type_options(),
        'PROJECT_STAGE_OPTIONS': get_project_stage_options(),
        'INDUSTRY_OPTIONS': get_industry_options(),
        **get_company_data()
    }

# 新的编辑项目后台逻辑函数
def get_edit_project_data():
    """获取编辑项目需要的数据"""
    return get_project_form_data()

@project.route('/edit/<int:project_id>', methods=['GET', 'POST'])
@permission_required('project', 'edit')
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查编辑权限
    if not can_edit_data(project, current_user):
        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试编辑无权限的项目: {project_id} (所有者: {project.owner_id})")
        flash('您没有权限编辑此项目', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 检查项目是否被锁定
    from app.helpers.project_helpers import is_project_editable
    is_editable, lock_reason = is_project_editable(project_id, current_user.id)
    if not is_editable and current_user.role != 'admin':
        flash(f'项目已被锁定，无法编辑: {lock_reason}', 'warning')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    if request.method == 'POST':
        # 在修改前捕获旧值用于变更跟踪
        from app.utils.change_tracker import ChangeTracker
        old_values = ChangeTracker.capture_old_values(project)
        
        # 记录修改前的客户关联信息，用于判断是否有新增关联
        old_customer_relations = {
            'end_user': project.end_user,
            'design_issues': project.design_issues,
            'contractor': project.contractor,
            'system_integrator': project.system_integrator,
            'dealer': project.dealer
        }
        
        try:
            # 必填项校验
            if not request.form.get('project_name'):
                flash('项目名称不能为空', 'danger')
                return render_template('project/edit.html', project=project, **get_edit_project_data())
            # 报备日期不在编辑页面显示，不需要验证
            # 当前阶段不在编辑页面显示，不需要验证
            # if not request.form.get('current_stage'):
            #     flash('当前阶段不能为空', 'danger')
            #     return render_template('project/edit.html', project=project, **get_edit_project_data())
            if not request.form.get('industry'):
                flash('项目行业不能为空', 'danger')
                return render_template('project/edit.html', project=project, **get_edit_project_data())
            # 报备日期不在编辑页面显示，不需要解析，保持原有值不变
            # 解析出货预测日期
            if request.form.get('delivery_forecast'):
                project.delivery_forecast = datetime.strptime(request.form['delivery_forecast'], '%Y-%m-%d').date()
            else:
                project.delivery_forecast = None
            # 更新项目信息
            project.project_name = request.form['project_name']
            project.report_source = request.form.get('report_source')
            project.product_situation = request.form.get('product_situation')
            project.industry = request.form.get('industry')  # 添加行业字段更新
            
            # 当前阶段不在编辑页面显示，不需要更新，保持原值
            old_stage = project.current_stage
            new_stage = project.current_stage  # 保持不变
            # 客户关联字段已从编辑表单中移除，在项目详情页单独管理
            project.stage_description = request.form.get('stage_description')
            
            # 更新销售负责人字段
            vendor_sales_manager_id = request.form.get('vendor_sales_manager_id')
            
            # 如果厂商销售负责人字段为空，默认将拥有人账户作为内容
            if not vendor_sales_manager_id and project.owner and project.owner.is_vendor_user():
                vendor_sales_manager_id = project.owner_id
            
            if vendor_sales_manager_id:
                project.vendor_sales_manager_id = int(vendor_sales_manager_id) if vendor_sales_manager_id != '' else None
            
            # 更新项目类型 - 只接受英文键
            new_project_type = request.form.get('project_type', 'normal')
            
            # 验证项目类型有效性
            if new_project_type not in ['normal', 'channel_follow', 'sales_focus', 'sales_key', 'business_opportunity']:
                new_project_type = 'normal'
            if new_project_type != project.project_type:
                project.project_type = new_project_type
            
            # 更新项目共享设置
            from app.utils.sharing import SharingService
            SharingService.update_sharing_from_request(project, current_user, 'project')
            
            db.session.commit()
            
            # 记录变更历史
            try:
                new_values = ChangeTracker.get_new_values(project, old_values.keys())
                ChangeTracker.log_update(project, old_values, new_values)
            except Exception as track_err:
                logger.warning(f"记录项目变更历史失败: {str(track_err)}")
            
            # 新增：每次保存后自动刷新活跃度（必须在commit之后调用）
            try:
                logger.info(f"项目编辑保存后更新活跃状态: 项目 ID {project.id}, 名称: {project.project_name}")
                logger.info(f"更新前活跃状态: {project.is_active}, 更新时间: {project.updated_at}")
                update_active_status(project, commit=True)
                # 重新查询项目以获取最新状态
                db.session.refresh(project)
                logger.info(f"更新后活跃状态: {project.is_active}")
            except Exception as activity_err:
                logger.error(f"更新项目活跃状态失败: {str(activity_err)}")
            
            # 项目保存后触发评分重新计算
            try:
                from app.models.project_scoring import ProjectScoringEngine
                ProjectScoringEngine.calculate_project_score(project.id, commit=True)
                current_app.logger.info(f"项目 {project.project_name} 更新后评分已重新计算")
            except Exception as score_err:
                current_app.logger.warning(f"项目更新后评分重新计算失败: {str(score_err)}")
            
            # 如果项目阶段发生变更，触发通知
            if old_stage != new_stage:
                try:
                    # 项目活跃度已在上面统一更新，这里只记录日志
                    current_app.logger.debug(f"项目阶段变更后项目 {project.id} 活跃度已更新")
                    
                    import threading
                    from app.services.event_dispatcher import notify_project_status_updated
                    from app.utils.solution_manager_notifications import notify_solution_managers_project_stage_changed
                    
                    def send_stage_notifications_async():
                        """异步发送阶段变更通知"""
                        with current_app.app_context():
                            try:
                                # 触发项目阶段变更通知
                                notify_project_status_updated(project, current_user, old_stage)
                                # 通知解决方案经理
                                notify_solution_managers_project_stage_changed(project, old_stage, new_stage)
                                current_app.logger.debug('异步项目阶段变更通知已发送')
                            except Exception as notify_err:
                                current_app.logger.warning(f"异步触发项目阶段变更通知失败: {str(notify_err)}")
                    
                    # 启动异步通知线程
                    threading.Thread(target=send_stage_notifications_async, daemon=True).start()
                    current_app.logger.debug('异步项目阶段变更通知线程已启动')
                    
                except Exception as notify_err:
                    current_app.logger.warning(f"启动异步项目阶段变更通知失败: {str(notify_err)}")
            
            # 只更新新增关联的客户活跃状态
            # 获取当前的客户关联信息
            current_customer_relations = {
                'end_user': project.end_user,
                'design_issues': project.design_issues,
                'contractor': project.contractor,
                'system_integrator': project.system_integrator,
                'dealer': project.dealer
            }
            
            # 找出新增的客户关联（之前为空或不同，现在有值）
            new_related_companies = []
            for field, current_value in current_customer_relations.items():
                old_value = old_customer_relations.get(field)
                # 如果当前有值且与之前不同（新增或修改了关联）
                if current_value and current_value != old_value:
                    new_related_companies.append(current_value)
                    current_app.logger.debug(f"检测到客户关联变更: {field} 从 '{old_value}' 变为 '{current_value}'")
            
            # 只更新新增关联的客户活跃状态
            for company_name in set(new_related_companies):
                company = Company.query.filter_by(company_name=company_name, is_deleted=False).first()
                if company:
                    check_company_activity(company_id=company.id)
                    current_app.logger.debug(f"更新新关联客户 '{company_name}' 的活跃度")
            
            flash('项目信息已更新！', 'success')
            return redirect(url_for('project.view_project', project_id=project.id))
        except Exception as e:
            import sqlalchemy
            db.session.rollback()
            # 详细日志
            logger.error(f"编辑项目保存异常，表单内容: {dict(request.form)}，异常类型: {type(e).__name__}, 信息: {str(e)}")
            if isinstance(e, sqlalchemy.exc.InvalidRequestError) and 'closed' in str(e).lower():
                flash('保存失败：数据库会话已关闭，请刷新页面后重试。如多次出现请联系管理员。', 'danger')
            else:
                flash(f'保存失败：{type(e).__name__}: {str(e)}', 'danger')
    
    # GET请求：返回编辑页面
    return render_template(
        'project/edit.html',
        project=project,
        **get_edit_project_data()
    )

@project.route('/delete/<int:project_id>', methods=['POST'])
@permission_required('project', 'delete')
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查删除权限
    if not can_edit_data(project, current_user):
        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试删除无权限的项目: {project_id} (所有者: {project.owner_id})")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': '您没有权限删除此项目'
            }), 403
            
        flash('您没有权限删除此项目', 'danger')
        return redirect(url_for('project.list_projects'))
    
    try:
        # === 关联数据清理开始 ===
        
        # 1. 先删除项目关联的所有报价单
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project_id).all()
        quotation_ids = [q.id for q in quotations]  # 保存报价单ID用于后续删除审批
        
        if quotations:
            for quotation in quotations:
                db.session.delete(quotation)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotations)} 个报价单")
        
        # 2. 删除项目关联的所有阶段历史记录
        from app.models.projectpm_stage_history import ProjectStageHistory
        stage_histories = ProjectStageHistory.query.filter_by(project_id=project_id).all()
        if stage_histories:
            for history in stage_histories:
                db.session.delete(history)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(stage_histories)} 个阶段历史记录")
        
        # 3. 删除项目跟进记录和回复 (新增)
        from app.models.action import Action, ActionReply
        project_actions = Action.query.filter_by(project_id=project_id).all()
        if project_actions:
            action_reply_count = 0
            for action in project_actions:
                # 统计回复数量
                replies = ActionReply.query.filter_by(action_id=action.id).all()
                action_reply_count += len(replies)
                # ActionReply已通过cascade='all, delete-orphan'自动删除
                db.session.delete(action)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(project_actions)} 个跟进记录和 {action_reply_count} 个回复")
        
        # 4. 删除项目审批实例和记录 (新增)
        from app.models.approval import ApprovalInstance, ApprovalRecord
        project_approvals = ApprovalInstance.query.filter_by(
            object_type='project', 
            object_id=project_id
        ).all()
        if project_approvals:
            approval_record_count = 0
            for approval in project_approvals:
                # 统计审批记录数量
                records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                approval_record_count += len(records)
                # ApprovalRecord已通过cascade="all, delete-orphan"自动删除
                db.session.delete(approval)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(project_approvals)} 个项目审批实例和 {approval_record_count} 个审批记录")
        
        # 5. 删除关联报价单的审批实例 (新增)
        if quotation_ids:
            quotation_approvals = ApprovalInstance.query.filter(
                ApprovalInstance.object_type == 'quotation',
                ApprovalInstance.object_id.in_(quotation_ids)
            ).all()
            if quotation_approvals:
                quotation_approval_record_count = 0
                for approval in quotation_approvals:
                    # 统计审批记录数量
                    records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                    quotation_approval_record_count += len(records)
                    db.session.delete(approval)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotation_approvals)} 个报价单审批实例和 {quotation_approval_record_count} 个审批记录")
        
        # 6. 删除项目关联的评分记录
        try:
            from app.models.project_scoring import ProjectScoringRecord, ProjectTotalScore
            
            # 删除评分记录
            scoring_records = ProjectScoringRecord.query.filter_by(project_id=project_id).all()
            if scoring_records:
                for record in scoring_records:
                    db.session.delete(record)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(scoring_records)} 个项目评分记录")
            
            # 删除总评分记录
            total_scores = ProjectTotalScore.query.filter_by(project_id=project_id).all()
            if total_scores:
                for score in total_scores:
                    db.session.delete(score)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(total_scores)} 个项目总分记录")
                    
        except ImportError:
            # 如果新评分系统模块不存在，跳过
            logger.info("项目评分系统模块不存在，跳过评分记录清理")
        
        # 7. 删除旧的评分记录
        try:
            if ProjectRatingRecord:
                old_rating_records = ProjectRatingRecord.query.filter_by(project_id=project_id).all()
                if old_rating_records:
                    for record in old_rating_records:
                        db.session.delete(record)
                    logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(old_rating_records)} 个旧版评分记录")
        except Exception:
            # 如果评分系统模块处理失败，跳过
            logger.info("旧版评分系统模块处理失败，跳过")

        # 8. 删除项目-客户关联记录
        from app.models.project_customer_association import ProjectCustomerAssociation
        associations = ProjectCustomerAssociation.query.filter_by(project_id=project_id).all()
        if associations:
            for association in associations:
                db.session.delete(association)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(associations)} 个客户关联")

        # === 关联数据清理结束 ===

        # 9. 最后删除项目
        # 记录删除历史（在实际删除前记录）
        try:
            ChangeTracker.log_delete(project)
        except Exception as track_err:
            logger.warning(f"记录项目删除历史失败: {str(track_err)}")
        
        db.session.delete(project)
        db.session.commit()
        
        logger.info(f"项目 {project_id} ({project.project_name}) 及其所有关联数据删除成功")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': '项目删除成功！'
            })
        flash('项目删除成功！', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除项目 {project_id} 失败: {str(e)}")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'删除失败：{str(e)}'
            }), 500
            
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('project.list_projects'))

@project.route('/apply_authorization/<int:project_id>', methods=['POST'])
@login_required
def apply_authorization(project_id):
    """申请项目授权编号"""
    project = Project.query.get_or_404(project_id)
    
    # 检查权限 - 项目拥有者、厂商负责人或管理员可以申请
    if (current_user.id != project.owner_id and 
        current_user.id != project.vendor_sales_manager_id and 
        current_user.role != 'admin'):
        flash('您没有权限申请此项目的授权编号', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 检查项目当前状态
    if project.authorization_code:
        flash('此项目已有授权编号，无需重复申请', 'warning')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    if project.authorization_status == 'pending':
        flash('此项目已经提交申请，正在审批中', 'warning')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 检查项目类型是否填写
    if not project.project_type or project.project_type.strip() == '':
        flash('项目类型未填写，无法提交授权编号申请。请先完善项目信息。', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 更新项目状态为申请中
    apply_note = request.form.get('apply_note', '')
    project.authorization_status = 'pending'
    project.feedback = f"申请备注: {apply_note}" if apply_note else None
    
    try:
        db.session.commit()
        # 记录日志
        logger.info(f"用户 {current_user.username} 申请了项目 {project.project_name} 的授权编号")
        flash('授权编号申请已提交，等待审批', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"申请授权编号失败: {str(e)}")
        flash('申请提交失败，请稍后重试', 'danger')
    
    return redirect(url_for('project.view_project', project_id=project_id))

@project.route('/check_similar_projects', methods=['POST'])
def check_similar_projects():
    """检查是否有类似的项目名称"""
    data = request.get_json()
    project_name = data.get('project_name', '')
    exclude_id = data.get('exclude_id', None)
    
    if not project_name:
        return jsonify({'similar_projects': []})
    
    # 使用SQLAlchemy查询而非MongoDB
    query = Project.query.filter(Project.authorization_status != 'rejected')
    
    if exclude_id:
        try:
            exclude_id = int(exclude_id)
            query = query.filter(Project.id != exclude_id)
        except Exception:
            pass
    
    projects = query.all()
    similar_projects = []
    
    for project in projects:
        # 使用优化后的中文相似度比较函数
        is_similar, similarity = is_similar_project_name(
            project_name, 
            project.project_name, 
            threshold=50,  # 使用较低的阈值捕获更多潜在相似项目
            debug=True
        )
        
        if is_similar:
            similar_projects.append({
                'name': project.project_name,
                'authorization_code': project.authorization_code,
                'owner_name': project.owner.username if project.owner else "未知",
                'status': project.authorization_status,
                'similarity': similarity
            })
    
    # 按相似度降序排序
    similar_projects.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify({'similar_projects': similar_projects})

@project.route('/projects/approve_authorization/<int:project_id>', methods=['POST'])
@login_required
def approve_authorization(project_id):
    """批准项目授权编号申请"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 获取最新的用户信息（确保角色是最新的）
        from app.models.user import User
        current_db_user = User.query.get(current_user.id)
        
        # 检查用户权限
        can_approve = False
        
        # 统一处理角色字符串，去除空格
        user_role = current_db_user.role.strip() if current_db_user.role else ''

        # 管理员可以批准所有项目授权申请
        if user_role == 'admin':
            can_approve = True
        # 财务总监、解决方案经理、产品经理可以批准所有项目授权申请
        elif user_role in ['finance_director', 'finace_director', 'solution_manager', 'solution', 'product_manager', 'product']:
            can_approve = True
        # 渠道经理可以批准渠道跟进项目
        elif user_role == 'channel_manager' and project.project_type == 'channel_follow':
            can_approve = True
        # 销售总监可以批准销售重点项目
        elif user_role == 'sales_director' and project.project_type == 'sales_focus':
            can_approve = True
        # 销售经理不能批准客户服务项目
        elif user_role == 'sales' and project.project_type != 'business_opportunity':
            can_approve = True
        # 服务经理可以批准客户服务项目
        elif user_role in ['service', 'service_manager'] and project.project_type == 'business_opportunity':
            can_approve = True

        if not can_approve:
            logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_db_user.role}) 尝试批准无权限的项目: {project_id} (类型: {project.project_type})")
            flash('您没有权限批准此类项目的授权申请', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))

        # 如果项目状态不是待授权，则不能批准
        if project.authorization_code:
            flash('此项目已有授权编号，无需审批', 'warning')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        if project.authorization_status != 'pending':
            flash('此项目未提交授权申请或已被处理', 'warning')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 获取审批备注
        approval_note = request.form.get('approval_note', '')
        
        # 生成授权编号 - 先将英文类型映射为中文
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        project_type_for_code = project_type_label(project.project_type, lang_code)
        authorization_code = Project.generate_authorization_code(project_type_for_code)
        
        if not authorization_code:
            flash('无法为此类型的项目生成授权编号', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 更新项目
        project.authorization_code = authorization_code
        project.authorization_status = None  # 清除pending状态
        project.feedback = approval_note if approval_note else None
        
        # 授权批准后自动设置报备日期为当前日期
        from datetime import date
        project.report_time = date.today()
        
        # 同步更新所有关联报价单的project_stage和project_type
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project.id).all()
        for q in quotations:
            q.project_stage = project.current_stage
            q.project_type = project.project_type
        
        try:
            db.session.commit()
            # 记录日志
            logger.info(f"用户 {current_user.username} 批准了项目 {project.project_name} 的授权编号申请，编号为 {authorization_code}")
            flash(f'授权申请已批准，授权编号为: {authorization_code}', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"批准授权编号失败: {str(e)}")
            flash('批准申请失败，请稍后重试', 'danger')
        
        return redirect(url_for('project.view_project', project_id=project_id))
    except Exception as e:
        flash(f'批准授权失败：{str(e)}', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

@project.route('/reject_authorization/<int:project_id>', methods=['POST'])
@login_required
def reject_authorization(project_id):
    """拒绝项目授权申请"""
    try:
        project = Project.query.get_or_404(project_id)
        feedback = request.form.get('feedback', '')
        
        # 获取最新的用户信息（确保角色是最新的）
        from app.models.user import User
        current_db_user = User.query.get(current_user.id)
        
        # 检查用户权限
        can_reject = False
        
        # 统一处理角色字符串，去除空格
        user_role = current_db_user.role.strip() if current_db_user.role else ''

        # 管理员可以拒绝所有项目授权申请
        if user_role == 'admin':
            can_reject = True
        # 财务总监、解决方案经理、产品经理可以拒绝所有项目授权申请
        elif user_role in ['finance_director', 'finace_director', 'solution_manager', 'solution', 'product_manager', 'product']:
            can_reject = True
        # 渠道经理可以拒绝渠道跟进项目
        elif user_role == 'channel_manager' and project.project_type == 'channel_follow':
            can_reject = True
        # 销售总监可以拒绝销售重点项目
        elif user_role == 'sales_director' and project.project_type == 'sales_focus':
            can_reject = True
        # 销售经理不能拒绝客户服务项目
        elif user_role == 'sales' and project.project_type != 'business_opportunity':
            can_reject = True
        # 服务经理可以拒绝客户服务项目
        elif user_role in ['service', 'service_manager'] and project.project_type == 'business_opportunity':
            can_reject = True

        if not can_reject:
            logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_db_user.role}) 尝试拒绝无权限的项目: {project_id} (类型: {project.project_type})")
            flash('您没有权限拒绝此类项目的授权申请', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))

        # 如果项目状态不是待授权，则不能拒绝
        if project.authorization_status != 'pending':
            flash('此项目未提交授权申请或已被处理', 'warning')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 更新项目状态
        project.authorization_status = 'rejected'
        project.feedback = feedback
        
        try:
            db.session.commit()
            # 记录日志
            logger.info(f"用户 {current_user.username} 驳回了项目 {project.project_name} 的授权编号申请")
            flash('授权申请已驳回', 'warning')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"驳回授权编号失败: {str(e)}")
            flash('操作失败，请稍后重试', 'danger')
        
        return redirect(url_for('project.view_project', project_id=project_id))
    except Exception as e:
        flash(f'驳回授权失败：{str(e)}', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

@project.route('/revoke_authorization/<int:project_id>', methods=['POST'])
@login_required
def revoke_authorization(project_id):
    """撤回项目授权申请"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 检查权限 - 只有项目拥有者或管理员可以撤回
        if current_user.id != project.owner_id and current_user.role != 'admin':
            flash('您没有权限撤回此项目的授权申请', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 检查项目当前状态，只有pending状态的可以撤回
        if project.authorization_status != 'pending':
            flash('此项目未在审批中，无法撤回申请', 'warning')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 获取撤回原因
        revoke_reason = request.form.get('revoke_reason', '')
        
        # 更新项目状态，清除pending状态
        project.authorization_status = None
        project.feedback = f"申请已撤回。原因: {revoke_reason}" if revoke_reason else "申请已撤回"
        
        try:
            db.session.commit()
            # 记录日志
            logger.info(f"用户 {current_user.username} 撤回了项目 {project.project_name} 的授权编号申请")
            flash('授权申请已成功撤回', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"撤回授权申请失败: {str(e)}")
            flash('撤回申请失败，请稍后重试', 'danger')
        
        return redirect(url_for('project.view_project', project_id=project_id))
    except Exception as e:
        flash(f'撤回授权申请失败：{str(e)}', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

@project.route('/api/batch-delete', methods=['POST'])
@permission_required('project', 'delete')
@csrf.exempt
def batch_delete_projects():
    """批量删除项目"""
    try:
        data = request.get_json()
        if not data or 'project_ids' not in data or not data['project_ids']:
            return jsonify({
                'success': False,
                'message': '请选择要删除的项目'
            })
        
        project_ids = data['project_ids']
        result = {
            'success': True,
            'deleted': 0,
            'failed': 0,
            'failure_reasons': []
        }
        
        # 导入 Quotation 模型
        from app.models.quotation import Quotation
        
        for project_id in project_ids:
            try:
                project = Project.query.get(project_id)
                if not project:
                    result['failed'] += 1
                    result['failure_reasons'].append(f'ID为{project_id}的项目不存在')
                    continue
                
                # 检查权限
                if not can_edit_data(project, current_user):
                    result['failed'] += 1
                    result['failure_reasons'].append(f'您没有权限删除 "{project.project_name}" 项目')
                    continue
                
                # 先删除关联的报价单
                quotations = Quotation.query.filter_by(project_id=project_id).all()
                if quotations:
                    for quotation in quotations:
                        db.session.delete(quotation)
                    
                    logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotations)} 个报价单")
                
                # 删除关联的阶段历史记录
                from app.models.projectpm_stage_history import ProjectStageHistory
                stage_histories = ProjectStageHistory.query.filter_by(project_id=project_id).all()
                if stage_histories:
                    for history in stage_histories:
                        db.session.delete(history)
                
                # 删除项目关联的评分记录
                try:
                    from app.models.project_scoring import ProjectScoringRecord, ProjectTotalScore
                    
                    # 删除评分记录
                    scoring_records = ProjectScoringRecord.query.filter_by(project_id=project_id).all()
                    if scoring_records:
                        for record in scoring_records:
                            db.session.delete(record)
                    
                    # 删除总评分记录
                    total_scores = ProjectTotalScore.query.filter_by(project_id=project_id).all()
                    if total_scores:
                        for score in total_scores:
                            db.session.delete(score)
                            
                except ImportError:
                    # 如果新评分系统模块不存在，跳过
                    pass
                
                # 删除旧的评分记录
                try:
                    if ProjectRatingRecord:
                        old_rating_records = ProjectRatingRecord.query.filter_by(project_id=project_id).all()
                        if old_rating_records:
                            for record in old_rating_records:
                                db.session.delete(record)
                except Exception:
                    # 如果评分系统模块处理失败，跳过
                    pass

                # 删除项目-客户关联记录
                from app.models.project_customer_association import ProjectCustomerAssociation
                associations = ProjectCustomerAssociation.query.filter_by(project_id=project_id).all()
                if associations:
                    for association in associations:
                        db.session.delete(association)

                # 最后删除项目
                # 记录删除历史（在实际删除前记录）
                try:
                    ChangeTracker.log_delete(project)
                except Exception as track_err:
                    logger.warning(f"记录项目删除历史失败: {str(track_err)}")
                
                db.session.delete(project)
                result['deleted'] += 1
                
                # 记录日志
                logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 删除了项目 {project.project_name} (ID: {project_id})")
                
            except Exception as e:
                db.session.rollback()
                result['failed'] += 1
                result['failure_reasons'].append(f'删除 ID为{project_id} 的项目时出错: {str(e)}')
                logger.error(f"删除项目 {project_id} 失败: {str(e)}")
        
        db.session.commit()
        
        if result['deleted'] > 0:
            result['message'] = f'成功删除 {result["deleted"]} 个项目' + (f'，{result["failed"]} 个项目删除失败' if result['failed'] > 0 else '')
        else:
            result['success'] = False
            result['message'] = '所有项目删除失败'
        
        return jsonify(result)
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量删除项目失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        })

def update_project_stage_business_logic(project_id, new_stage, current_user_id):
    """
    业务逻辑函数：更新项目阶段并处理批价单创建
    供测试脚本和其他业务逻辑调用
    """
    try:
        from app.models.user import User
        user = User.query.get(current_user_id)
        if not user:
            return {'error': '用户不存在'}
        
        # 查询项目
        project = Project.query.get(project_id)
        if not project:
            return {'error': '项目不存在'}
        
        old_stage = project.current_stage
        
        # 检查从批价到签约的流程 - 严格控制，只有批价单审批通过才能推进
        if new_stage == 'signed' and old_stage == 'quoted':
            from app.models.quotation import Quotation
            from app.models.pricing_order import PricingOrder
            
            # 获取项目的最新报价单
            latest_quotation = Quotation.query.filter_by(project_id=project_id).order_by(
                Quotation.created_at.desc()
            ).first()
            
            if not latest_quotation:
                return {'error': '项目未找到相关报价单，无法推进到签约阶段。请先创建报价单。'}
            
            # 检查报价单是否有审核标记
            has_approval = (
                # 传统审核流程：有审核状态且不是pending/rejected，且有已审核阶段
                (latest_quotation.approval_status and 
                 latest_quotation.approval_status != 'pending' and
                 latest_quotation.approval_status != 'rejected' and
                 latest_quotation.approved_stages) or
                # 或者有确认徽章（产品明细已确认）
                (latest_quotation.confirmation_badge_status == 'confirmed')
            )
            
            if not has_approval:
                return {'error': f'报价单 {latest_quotation.quotation_number} 尚未完成审核，无法推进到签约阶段。请先完成报价单审核流程。'}
            
            # 检查是否已存在批价单且已审批通过
            existing_pricing_order = PricingOrder.query.filter_by(
                project_id=project_id,
                quotation_id=latest_quotation.id
            ).first()
            
            if not existing_pricing_order:
                return {'error': f'项目尚未创建批价单，无法推进到签约阶段。请先创建并完成批价单审批流程。'}
            
            # 检查批价单是否已审批通过
            if existing_pricing_order.status != 'approved':
                return {'error': f'批价单 {existing_pricing_order.order_number} 尚未审批通过（当前状态：{existing_pricing_order.status_label["zh"]}），无法推进到签约阶段。请先完成批价单审批流程。'}
            
            # 检查项目是否有授权编号
            if not project.authorization_code:
                return {'error': f'批价单 {existing_pricing_order.order_number} 已审批通过，但项目缺少授权编号，无法推进到签约阶段。请先申请项目授权编号。'}
        
        # 更新项目阶段
        project.current_stage = new_stage
        
        # 同步更新所有关联报价单的project_stage和project_type
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project.id).all()
        for q in quotations:
            q.project_stage = new_stage
            q.project_type = project.project_type
        
        # 创建阶段历史记录
        try:
            from app.models.projectpm_stage_history import ProjectStageHistory
            ProjectStageHistory.add_history_record(
                project_id=project.id,
                from_stage=old_stage,
                to_stage=new_stage,
                change_date=datetime.now(),
                remarks=f"业务逻辑推进: {user.username}",
                commit=False  # 不在方法内部提交，与主事务一同提交
            )
        except Exception as history_err:
            # 历史记录失败不应阻塞主流程
            pass
        
        db.session.commit()
        
        return {
            'success': True,
            'project_id': project_id,
            'old_stage': old_stage,
            'new_stage': new_stage,
            'message': '项目阶段更新成功'
        }
        
    except Exception as e:
        db.session.rollback()
        return {'error': f'更新项目阶段失败: {str(e)}'}

@project.route('/api/update_stage', methods=['POST'])
@login_required
@permission_required('project', 'edit')
def update_project_stage():
    """
    更新项目阶段
    用于项目阶段可视化进度条组件调用
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
            
        project_id = data.get('project_id')
        new_stage = data.get('current_stage')
        
        if not project_id or not new_stage:
            return jsonify({'success': False, 'message': '项目ID和阶段不能为空'}), 400
        
        # 如果传入的是中文阶段名称，转换为英文key
        if new_stage not in PROJECT_STAGE_LABELS:
            # 反查中文名称对应的英文key
            reverse_lookup = {v['zh']: k for k, v in PROJECT_STAGE_LABELS.items()}
            new_stage_key = reverse_lookup.get(new_stage, new_stage)
            if new_stage_key != new_stage:
                current_app.logger.info(f"阶段名称转换: {new_stage} -> {new_stage_key}")
                new_stage = new_stage_key
        
        # 查询项目 - 使用 with_for_update() 锁定行，防止并发更新
        try:
            project = db.session.query(Project).with_for_update().filter(Project.id == project_id).first()
            if not project:
                return jsonify({'success': False, 'message': '项目不存在'}), 404
                
            # 设置跳过自动历史记录的标志，因为我们会手动添加
            project._skip_history_recording = True
        except Exception as e:
            current_app.logger.error(f"查询项目时发生错误: {str(e)}")
            return jsonify({'success': False, 'message': f'查询错误: {str(e)}'}), 500
        
        # 检查项目是否被锁定
        from app.helpers.project_helpers import is_project_editable
        is_editable, lock_reason = is_project_editable(project_id, current_user.id)
        from app.permissions import is_admin_or_ceo
        if not is_editable and not is_admin_or_ceo():
            return jsonify({'success': False, 'message': f'项目已被锁定，无法推进阶段: {lock_reason}'}), 403
            
        # 检查权限
        allowed = False
        if is_admin_or_ceo():
            allowed = True
        elif project.owner_id == current_user.id:
            allowed = True
        elif project.vendor_sales_manager_id == current_user.id:
            # 厂商负责人享有与拥有人同等权限
            allowed = True
        else:
            allowed_user_ids = current_user.get_viewable_user_ids() if hasattr(current_user, 'get_viewable_user_ids') else [current_user.id]
            if project.owner_id in allowed_user_ids:
                allowed = True
        # 签约阶段加固：已签约项目不允许任何阶段变更（包括管理员）
        if project.current_stage == 'signed':
            return jsonify({'success': False, 'message': '已签约项目不允许变更阶段'}), 403
            
        # 防止将项目从任何阶段切换到搁置或失败（如果曾经签约过）
        if new_stage in ['paused', 'failed']:
            # 检查是否曾经有签约历史记录
            has_signed_history = ProjectStageHistory.query.filter(
                ProjectStageHistory.project_id == project_id,
                ProjectStageHistory.to_stage == 'signed'
            ).first()
            
            if has_signed_history:
                stage_name_map = {'paused': '搁置', 'failed': '失败'}
                return jsonify({
                    'success': False, 
                    'message': f'该项目曾经签约，不允许切换到{stage_name_map[new_stage]}状态'
                }), 403
        if not allowed:
            return jsonify({'success': False, 'message': '您没有权限修改此项目'}), 403
            
        # **新增: 签约阶段检测逻辑（批价流程）**
        old_stage = project.current_stage
        pricing_flow_info = None
        should_block_progress = False
        
        if new_stage == 'signed' and old_stage == 'quoted':
            # 从批价阶段推进到签约阶段，检查批价流程状态
            
            # 获取项目的最新报价单
            latest_quotation = Quotation.query.filter_by(project_id=project_id).order_by(
                Quotation.created_at.desc()
            ).first()
            
            if not latest_quotation:
                # 无报价单，阻止推进
                should_block_progress = True
                pricing_flow_info = {
                    'has_quotation': False,
                    'has_pricing_order': False,
                    'message': '项目未找到相关报价单，无法推进到签约阶段。请先创建报价单。',
                    'action_required': 'create_quotation'
                }
            else:
                # 检查报价单是否有审核标记
                has_approval = (
                    # 传统审核流程：有审核状态且不是pending/rejected，且有已审核阶段
                    (latest_quotation.approval_status and 
                     latest_quotation.approval_status != 'pending' and
                     latest_quotation.approval_status != 'rejected' and
                     latest_quotation.approved_stages) or
                    # 或者有确认徽章（产品明细已确认）
                    (latest_quotation.confirmation_badge_status == 'confirmed')
                )
                
                if not has_approval:
                    # 报价单没有审核标记，阻止推进
                    should_block_progress = True
                    pricing_flow_info = {
                        'has_quotation': True,
                        'has_approval': False,
                        'quotation_number': latest_quotation.quotation_number,
                        'message': f'报价单 {latest_quotation.quotation_number} 尚未完成审核，无法推进到签约阶段。请先完成报价单审核流程。',
                        'action_required': 'complete_quotation_approval',
                        'quotation_id': latest_quotation.id
                    }
                else:
                    # 有报价单且有审核标记，检查是否已存在批价单
                    existing_pricing_order = PricingOrder.query.filter_by(
                        project_id=project_id,
                        quotation_id=latest_quotation.id
                    ).first()
                    
                    if existing_pricing_order:
                        # 已存在批价单，检查审批状态
                        if existing_pricing_order.status == 'approved':
                            # 检查项目是否有授权编号
                            if not project.authorization_code:
                                # 批价单已通过但项目无授权编号，阻止推进
                                should_block_progress = True
                                pricing_flow_info = {
                                    'has_quotation': True,
                                    'has_approval': True,
                                    'has_pricing_order': True,
                                    'has_authorization': False,
                                    'quotation_number': latest_quotation.quotation_number,
                                    'pricing_order_number': existing_pricing_order.order_number,
                                    'pricing_order_status': existing_pricing_order.status,
                                    'message': f'批价单 {existing_pricing_order.order_number} 已审批通过，但项目缺少授权编号，无法推进到签约阶段。请先申请项目授权编号。',
                                    'action_required': 'apply_authorization',
                                    'project_id': project.id
                                }
                            else:
                                # 批价单已审批通过且有授权编号，可以推进到签约
                                pricing_flow_info = {
                                    'has_quotation': True,
                                    'has_approval': True,
                                    'has_pricing_order': True,
                                    'has_authorization': True,
                                    'quotation_number': latest_quotation.quotation_number,
                                    'pricing_order_number': existing_pricing_order.order_number,
                                    'pricing_order_status': existing_pricing_order.status,
                                    'authorization_code': project.authorization_code,
                                    'message': f'批价单 {existing_pricing_order.order_number} 已审批通过，项目授权编号 {project.authorization_code}，项目可以推进到签约阶段。',
                                    'action_required': 'view_pricing_order',
                                    'pricing_order_id': existing_pricing_order.id
                                }
                        else:
                            # 批价单存在但未审批通过，阻止推进
                            should_block_progress = True
                            pricing_flow_info = {
                                'has_quotation': True,
                                'has_approval': True,
                                'has_pricing_order': True,
                                'quotation_number': latest_quotation.quotation_number,
                                'pricing_order_number': existing_pricing_order.order_number,
                                'pricing_order_status': existing_pricing_order.status,
                                'message': f'批价单 {existing_pricing_order.order_number} 尚未审批通过（当前状态：{existing_pricing_order.status_label["zh"]}），无法推进到签约阶段。请先完成批价单审批流程。',
                                'action_required': 'view_pricing_order',
                                'pricing_order_id': existing_pricing_order.id
                            }
                    else:
                        # 有报价单有审核但无批价单，阻止推进并提示创建
                        should_block_progress = True
                        pricing_flow_info = {
                            'has_quotation': True,
                            'has_approval': True,
                            'has_pricing_order': False,
                            'quotation_number': latest_quotation.quotation_number,
                            'message': f'项目尚未创建批价单，无法推进到签约阶段。请先创建并完成批价单审批流程。',
                            'action_required': 'create_pricing_order',
                            'quotation_id': latest_quotation.id
                        }
        
        # 如果需要阻止推进，回滚到原阶段
        if should_block_progress:
            return jsonify({
                'success': False, 
                'message': pricing_flow_info['message'],
                'pricing_flow': pricing_flow_info,
                'current_stage': old_stage  # 保持原阶段
            }), 400
        
        # 更新项目阶段
        project.current_stage = new_stage
        
        # 如果项目推进到签约阶段，自动锁定项目
        if new_stage == 'signed' and not project.is_locked:
            project.is_locked = True
            project.locked_reason = '项目已签约，自动锁定'
            project.locked_by = current_user.id
            project.locked_at = datetime.now()
            current_app.logger.info(f'项目 {project.project_name} (ID: {project.id}) 由于签约自动锁定')
        
        # 同步更新所有关联报价单的project_stage和project_type
        quotations = Quotation.query.filter_by(project_id=project.id).all()
        for q in quotations:
            q.project_stage = new_stage
            q.project_type = project.project_type
        
        # 在一个事务中同时保存项目更新和阶段历史
        try:
            current_app.logger.info(f"开始为项目ID={project.id}创建阶段历史记录: {old_stage} -> {new_stage}")
            
            # 创建阶段历史记录但不提交
            ProjectStageHistory.add_history_record(
                project_id=project.id,
                from_stage=old_stage,
                to_stage=new_stage,
                change_date=datetime.now(),
                remarks=f"API推进: {current_user.username}",
                commit=False  # 不在方法内部提交，与主事务一同提交
            )
            current_app.logger.info(f"阶段历史记录已创建，准备提交事务")

            # 提交所有更改（让SQLAlchemy自动更新updated_at字段）
            db.session.commit()
            current_app.logger.info(f"数据库事务已提交")
            
            # 在提交后更新项目活跃度（使用最新的updated_at时间）
            current_app.logger.info(f"开始更新项目活跃度状态")
            update_active_status(project, commit=True)
            current_app.logger.info(f"项目ID={project.id}的阶段从{old_stage}更新为{new_stage}，历史记录已添加")
            
            # 提交后再单独重新计算项目评分（避免事务冲突）
            @after_this_request
            def calculate_score(response):
                try:
                    # 在请求完成后计算评分，使用独立事务
                    from app.models.project_scoring import ProjectScoringEngine
                    ProjectScoringEngine.calculate_project_score(project.id, commit=True)
                    current_app.logger.info(f"项目ID={project.id}阶段推进后评分已重新计算")
                except Exception as score_err:
                    current_app.logger.warning(f"重新计算项目评分失败: {str(score_err)}")
                return response
            
            # 验证更新是否生效
            db.session.refresh(project)
            if project.current_stage != new_stage:
                current_app.logger.error(f"项目阶段推进后数据库未更新: 项目ID={project.id}, 期望={new_stage}, 实际={project.current_stage}")
                return jsonify({'success': False, 'message': '数据库更新失败，请联系管理员'}), 500
            
            # 触发阶段变更通知
            if old_stage != new_stage:
                try:
                    import threading
                    from app.services.event_dispatcher import notify_project_status_updated
                    from app.utils.solution_manager_notifications import notify_solution_managers_project_stage_changed
                    
                    def send_stage_notifications_async():
                        """异步发送阶段变更通知"""
                        with current_app.app_context():
                            try:
                                # 触发项目阶段变更通知
                                notify_project_status_updated(project, current_user, old_stage)
                                # 通知解决方案经理
                                notify_solution_managers_project_stage_changed(project, old_stage, new_stage)
                                current_app.logger.debug('异步项目阶段变更通知已发送')
                            except Exception as notify_err:
                                current_app.logger.warning(f"异步触发项目阶段变更通知失败: {str(notify_err)}")
                    
                    # 启动异步通知线程
                    threading.Thread(target=send_stage_notifications_async, daemon=True).start()
                    current_app.logger.debug('异步项目阶段变更通知线程已启动')
                    
                except Exception as notify_err:
                    current_app.logger.warning(f"启动异步项目阶段变更通知失败: {str(notify_err)}")
            
            # 构建响应数据
            response_data = {
                'success': True, 
                'message': '项目阶段已更新',
                'data': {
                    'project_id': project.id,
                    'current_stage': project.current_stage,
                    'old_stage': old_stage
                }
            }
            
            # 如果有批价流程信息，添加到响应中
            if pricing_flow_info:
                response_data['pricing_flow'] = pricing_flow_info
            
            return jsonify(response_data), 200
            
        except Exception as db_err:
            import traceback
            db_error_traceback = traceback.format_exc()
            db.session.rollback()
            current_app.logger.error(f"提交阶段更新到数据库失败: {str(db_err)}")
            current_app.logger.error(f"数据库错误堆栈:\n{db_error_traceback}")
            return jsonify({
                'success': False, 
                'message': f'数据库错误: {str(db_err)}',
                'error_details': db_error_traceback if current_app.debug else None
            }), 500
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        current_app.logger.error(f"更新项目阶段出错: {str(e)}")
        current_app.logger.error(f"错误堆栈:\n{error_traceback}")
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'服务器错误: {str(e)}',
            'error_details': error_traceback if current_app.debug else None
        }), 500

@project.route('/add_action/<int:project_id>', methods=['GET', 'POST'])
@permission_required('customer', 'create')
def add_action_for_project(project_id):
    """为项目添加行动记录"""
    project = Project.query.get_or_404(project_id)
    
    # 查找项目相关的所有企业
    related_companies = []
    related_companies_dict = {}
    
    if project.end_user:
        company = Company.query.filter_by(company_name=project.end_user, is_deleted=False).first()
        if company:
            related_companies.append(company)
            related_companies_dict[company.id] = company
    
    if project.design_issues:
        company = Company.query.filter_by(company_name=project.design_issues, is_deleted=False).first()
        if company and company.id not in related_companies_dict:
            related_companies.append(company)
            related_companies_dict[company.id] = company
    
    if project.contractor:
        company = Company.query.filter_by(company_name=project.contractor, is_deleted=False).first()
        if company and company.id not in related_companies_dict:
            related_companies.append(company)
            related_companies_dict[company.id] = company
    
    if project.system_integrator:
        company = Company.query.filter_by(company_name=project.system_integrator, is_deleted=False).first()
        if company and company.id not in related_companies_dict:
            related_companies.append(company)
            related_companies_dict[company.id] = company
    
    if project.dealer:
        company = Company.query.filter_by(company_name=project.dealer, is_deleted=False).first()
        if company and company.id not in related_companies_dict:
            related_companies.append(company)
            related_companies_dict[company.id] = company
    
    # 获取默认选择的企业ID和锁定状态
    default_company_id = request.args.get('company_id')
    locked_company = request.args.get('locked') == 'true'  # 检查是否锁定客户
    selected_company = None
    company_contacts = []
    
    if default_company_id and default_company_id.isdigit():
        selected_company = Company.query.filter_by(id=int(default_company_id), is_deleted=False).first()
        if selected_company:
            company_contacts = Contact.query.filter_by(company_id=selected_company.id).all()
    elif related_companies:
        # 如果没有指定企业，默认选择第一个相关企业
        selected_company = related_companies[0]
        company_contacts = Contact.query.filter_by(company_id=selected_company.id).all()
    
    if request.method == 'POST':
        contact_id = request.form.get('contact_id')
        communication = request.form.get('communication')
        date = request.form.get('date')
        company_id = request.form.get('company_id')
        
        if not communication or not date:
            flash('请填写沟通情况和日期', 'danger')
        else:
            action = Action(
                date=datetime.strptime(date, '%Y-%m-%d'),
                contact_id=contact_id if contact_id else None,
                company_id=company_id if company_id else None,
                project_id=project_id,
                communication=communication,
                owner_id=current_user.id,
                is_shared='is_shared' in request.form  # 默认为False（如果未选中checkbox）
            )
            db.session.add(action)
            db.session.commit()
            # 新增：每次添加行动记录后自动刷新项目活跃度和更新时间
            project.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
            update_active_status(project, commit=False)
            db.session.commit()
            # 如果关联了客户，更新客户活跃状态
            if company_id and company_id.isdigit():
                check_company_activity(company_id=int(company_id), days_threshold=1)
            
            flash('行动记录添加成功！', 'success')
            return redirect(url_for('project.view_project', project_id=project_id))
    
    return render_template('project/add_action.html', 
                           project=project, 
                           related_companies=related_companies,
                           selected_company=selected_company,
                           company_contacts=company_contacts,
                           locked_company=locked_company)

@project.route('/api/get_company_contacts/<int:company_id>', methods=['GET'])
@permission_required('customer', 'view')
def get_company_contacts(company_id):
    """获取企业联系人API"""
    try:
        company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
        contacts = Contact.query.filter_by(company_id=company_id).all()
        
        result = [{
            'id': contact.id,
            'name': contact.name,
            'position': contact.position or '',
            'phone': contact.phone or '',
            'email': contact.email or ''
        } for contact in contacts]
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"获取企业联系人失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取企业联系人失败: {str(e)}'
        }), 500 

# 获取行动记录的所有回复（树形结构）
@project.route('/action/<int:action_id>/replies')
@login_required
@permission_required('customer', 'view')
def get_action_replies(action_id):
    action = Action.query.get_or_404(action_id)
    replies = ActionReply.query.filter_by(action_id=action_id, parent_reply_id=None).order_by(ActionReply.created_at.asc()).all()
    def build_tree(reply):
        return {
            'id': reply.id,
            'content': reply.content,
            'owner': reply.owner.real_name or reply.owner.username,
            'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M'),
            'can_delete': (current_user.id == reply.owner_id or current_user.role == 'admin'),
            'children': [build_tree(child) for child in reply.children]
        }
    return jsonify([build_tree(r) for r in replies])

# 添加回复
@project.route('/action/<int:action_id>/reply', methods=['POST'])
@login_required
@permission_required('customer', 'create')
def add_action_reply(action_id):
    action = Action.query.get_or_404(action_id)
    data = request.get_json()
    content = data.get('content', '').strip()
    parent_reply_id = data.get('parent_reply_id')
    if not content:
        return jsonify({'success': False, 'message': '回复内容不能为空'}), 400
    reply = ActionReply(
        action_id=action_id,
        parent_reply_id=parent_reply_id,
        content=content,
        owner_id=current_user.id
    )
    db.session.add(reply)
    db.session.commit()
    return jsonify({'success': True})

@project.route('/<int:project_id>/change_owner', methods=['POST'])
@permission_required('project', 'edit')
def change_project_owner(project_id):
    project = Project.query.get_or_404(project_id)
    if not can_change_project_owner(current_user, project):
        flash('您没有权限修改该项目的拥有人', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 检查项目是否被锁定
    from app.helpers.project_helpers import is_project_editable
    is_editable, lock_reason = is_project_editable(project_id, current_user.id)
    if not is_editable and current_user.role != 'admin':
        flash(f'项目已被锁定，无法修改拥有人: {lock_reason}', 'warning')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    new_owner_id = request.form.get('new_owner_id', type=int)
    if not new_owner_id:
        flash('请选择新的拥有人', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    from app.models.user import User
    new_owner = User.query.get(new_owner_id)
    if not new_owner:
        flash('新拥有人不存在', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 检查新拥有人是否是厂商企业账户
    is_vendor_company = new_owner.is_vendor_user()
    
    # 处理厂商销售负责人设置（保持原有值或设置新值）
    vendor_sales_manager_id = project.vendor_sales_manager_id  # 保持原有值
    
    if not is_vendor_company:
        # 如果新拥有人不是厂商企业账户，允许可选设置厂商销售负责人
        form_vendor_id = request.form.get('vendor_sales_manager_id', type=int)
        
        # 如果用户指定了新的厂商销售负责人，需要验证其有效性
        if form_vendor_id:
            vendor_sales_manager = User.query.get(form_vendor_id)
            if not vendor_sales_manager:
                flash('厂商销售负责人不存在', 'danger')
                return redirect(url_for('project.view_project', project_id=project_id))
            
            if not vendor_sales_manager.is_vendor_user():
                flash('厂商销售负责人必须是厂商企业账户', 'danger')
                return redirect(url_for('project.view_project', project_id=project_id))
            
            # 验证通过，更新为新的厂商销售负责人
            vendor_sales_manager_id = form_vendor_id
        # 如果没有指定新的厂商销售负责人，保持原有值（已在上面设置）
    else:
        # 如果新拥有人是厂商企业账户，自动设置为厂商销售负责人
        vendor_sales_manager_id = new_owner_id
    
    # 记录旧值用于ChangeLog
    old_owner_id = project.owner_id
    old_owner = User.query.get(old_owner_id) if old_owner_id else None

    # 更新项目拥有人和厂商销售负责人
    project.owner_id = new_owner_id
    project.vendor_sales_manager_id = vendor_sales_manager_id

    # 同步更新该项目下所有报价单的owner_id为新拥有人
    from app.models.quotation import Quotation
    quotations = Quotation.query.filter_by(project_id=project.id).all()
    for quotation in quotations:
        quotation.owner_id = new_owner_id

    # 记录owner_id变更到ChangeLog
    if old_owner_id != new_owner_id:
        from app.models.change_log import ChangeLog
        ChangeLog.log_update(
            module_name='project',
            table_name='projects',
            record_id=project.id,
            field_name='owner_id',
            old_value=old_owner.real_name or old_owner.username if old_owner else '无',
            new_value=new_owner.real_name or new_owner.username,
            user_id=current_user.id,
            user_name=current_user.real_name or current_user.username,
            description=f'项目负责人从 {old_owner.real_name if old_owner else "无"} 变更为 {new_owner.real_name}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

    db.session.commit()
    
    # 构建成功消息
    success_msg = '项目拥有人及关联报价单拥有人已更新'
    if vendor_sales_manager_id and vendor_sales_manager_id != new_owner_id:
        vendor_manager = User.query.get(vendor_sales_manager_id)
        success_msg += f'，厂商销售负责人已设置为 {vendor_manager.real_name or vendor_manager.username}'
    
    flash(success_msg, 'success')
    return redirect(url_for('project.view_project', project_id=project_id))

@project.route('/action/reply/<int:reply_id>/delete', methods=['POST'])
@login_required
@permission_required('customer', 'delete')
def delete_action_reply(reply_id):
    from app.models.action import ActionReply
    reply = ActionReply.query.get_or_404(reply_id)
    if reply.owner_id != current_user.id and current_user.role != 'admin':
        return jsonify({'success': False, 'message': '无权删除此回复'}), 403
    db.session.delete(reply)
    db.session.commit()
    return jsonify({'success': True})

@project.route('/api/project/<int:project_id>', methods=['GET'])
@login_required
@permission_required('project', 'view')
def get_project_api(project_id):
    """获取项目详情API"""
    project = Project.query.get_or_404(project_id)
    
    # 检查查看权限
    if not can_view_project(current_user, project):
        return jsonify({'error': '没有权限查看此项目'}), 403
    
    return jsonify({
        'id': project.id,
        'project_name': project.project_name,
        'current_stage': project.current_stage,
        'project_type': project.project_type,
        'owner_id': project.owner_id,
        'owner_name': project.owner.username if project.owner else None
    })

@project.route('/api/users', methods=['GET'])
@login_required
@permission_required('project', 'edit')
def get_users_api():
    """获取用户列表API，用于销售负责人选择"""
    user_type = request.args.get('type', 'all')  # vendor, dealer, all
    
    try:
        from app.models.user import User
        
        if user_type == 'vendor':
            # 获取厂商用户
            users = [user for user in User.query.all() if user.is_vendor_user()]
        elif user_type == 'dealer':
            # 获取代理商用户（非厂商用户）
            users = [user for user in User.query.all() if not user.is_vendor_user()]
        else:
            # 获取所有用户
            users = User.query.all()
        
        users_data = []
        for user in users:
            # 获取真实姓名，如果没有则使用用户名
            display_name = user.real_name if hasattr(user, 'real_name') and user.real_name else user.username
            # 获取角色的中文显示名
            role_display = get_role_display_name(user.role) if user.role else '未知角色'
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'real_name': display_name,
                'company_name': user.company_name,
                'role': user.role,
                'role_display': role_display,
                'display_text': f"{display_name} ({role_display})"  # 用于前端显示的组合文本
            })
        
        return jsonify({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        current_app.logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500 

@project.route('/api/project/<int:project_id>/latest-quotation', methods=['GET'])
@login_required
@permission_required('project', 'view')
def get_project_latest_quotation_api(project_id):
    """获取项目最新报价信息"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 检查权限
        if not can_view_project(project, current_user):
            return jsonify({'success': False, 'message': '无权限查看此项目'}), 403
        
        # 获取最新报价
        latest_quotation = Quotation.query.filter_by(project_id=project_id).order_by(Quotation.created_at.desc()).first()
        
        if latest_quotation:
            return jsonify({
                'success': True,
                'data': {
                    'id': latest_quotation.id,
                    'quotation_number': latest_quotation.quotation_number,
                    'amount': latest_quotation.amount,
                    'created_at': latest_quotation.created_at.strftime('%Y-%m-%d %H:%M:%S') if latest_quotation.created_at else None,
                    'owner': {
                        'id': latest_quotation.owner.id if latest_quotation.owner else None,
                        'name': latest_quotation.owner.real_name or latest_quotation.owner.username if latest_quotation.owner else None
                    }
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': None,
                'message': '暂无报价记录'
            })
            
    except Exception as e:
        logger.error(f"获取项目最新报价失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取报价信息失败'}), 500

# 项目评分相关API端点已迁移到新的评分系统
# 请使用 app/views/project_scoring_api.py 中的新API

def _get_project_owner_options(current_user):
    """获取项目拥有人筛选选项 - 只查询实际存在的拥有者"""
    try:
        # 获取当前用户可见的项目中的所有拥有者ID
        unique_owner_ids_query = get_viewable_data(Project, current_user)\
            .filter(Project.owner_id.isnot(None))\
            .with_entities(Project.owner_id.distinct())
        
        unique_owner_ids = {row[0] for row in unique_owner_ids_query.all()}
        
        if not unique_owner_ids:
            return []
        
        # 只查询需要的用户，避免加载所有用户
        # 移除活跃状态过滤，确保所有实际拥有项目的用户都出现在筛选选项中
        available_users = User.query.filter(
            User.id.in_(unique_owner_ids)
        ).order_by(User.real_name, User.username).all()
        
        return [
            {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
            for user in available_users
        ]
        
    except Exception as e:
        current_app.logger.error(f"获取项目拥有人选项失败: {e}")
        return []

def _format_currency_amount(amount, currency_symbol='¥'):
    """格式化金额，添加千位分隔符"""
    try:
        # 保留两位小数
        formatted = f"{amount:.2f}"
        # 分割整数和小数部分
        parts = formatted.split('.')
        # 为整数部分添加千位分隔符
        parts[0] = f"{int(parts[0]):,}"
        # 重新组合
        return f"{currency_symbol}{'.'.join(parts)}"
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"

def _create_stage_card(stage_key, title, icon, stage_stats, currency_symbol, color):
    """创建阶段统计卡片配置（使用传递的currency_symbol）"""
    stage_data = stage_stats.get(stage_key, {'count': 0, 'amount': 0})

    # 根据当前语言环境确定单位显示
    from app.utils.i18n import get_current_language
    current_lang = get_current_language()
    amount_unit = '万美元' if current_lang == 'en' else '万元'

    return {
        'id': stage_key,
        'title': _(title),
        'icon': icon,
        'value': stage_data['count'],
        'amount': round(stage_data['amount'] / 10000, 2),  # 转换为万元并保留2位小数
        'unit': _('个'),
        'amount_unit': amount_unit,  # 使用语言感知的单位
        'currency_symbol': currency_symbol,  # 添加货币符号
        'color': color,
        'clickable': True,  # 启用点击筛选功能
        'click_params': {'current_stage': stage_key},  # 点击时筛选对应阶段
        'data_key': stage_key
    }

def _get_vendor_manager_options(current_user):
    """获取厂商负责人筛选选项 - 只查询实际存在的负责人"""
    try:
        # 获取当前用户可见的项目中的所有厂商负责人ID
        unique_manager_ids_query = get_viewable_data(Project, current_user)\
            .filter(Project.vendor_sales_manager_id.isnot(None))\
            .with_entities(Project.vendor_sales_manager_id.distinct())
        
        unique_manager_ids = {row[0] for row in unique_manager_ids_query.all()}
        
        if not unique_manager_ids:
            return []
        
        # 只查询需要的用户，避免加载所有用户
        # 移除活跃状态过滤，确保所有实际负责项目的用户都出现在筛选选项中
        available_managers = User.query.filter(
            User.id.in_(unique_manager_ids)
        ).order_by(User.real_name, User.username).all()
        
        return [
            {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
            for user in available_managers
        ]
        
    except Exception as e:
        current_app.logger.error(f"获取厂商负责人选项失败: {e}")
        return []

def _calculate_stage_stats_fast(projects):
    """快速计算项目阶段统计（基于当前显示的项目）"""
    stage_stats = {}
    # 定义所有可能的阶段
    all_stages = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused']

    # 初始化所有阶段计数和金额为0
    for stage in all_stages:
        stage_stats[stage] = {'count': 0, 'amount': 0}

    # 快速统计（无汇率转换）
    for project in projects:
        stage = project.current_stage
        if stage in stage_stats:
            stage_stats[stage]['count'] += 1
            stage_stats[stage]['amount'] += project.quotation_customer or 0

    return stage_stats


def _apply_filters_to_query(query, current_user, search=None, owner_id=None, vendor_sales_manager_id=None,
                           is_active=None, industry=None, report_source=None, current_stage=None, project_type=None):
    """将筛选条件应用到查询对象，复用现有筛选逻辑"""
    from sqlalchemy import or_

    # 应用搜索条件
    if search:
        query = query.filter(
            or_(
                Project.project_name.ilike(f'%{search}%'),
                Project.authorization_code.ilike(f'%{search}%')
            )
        )

    # 应用筛选条件
    if owner_id:
        query = query.filter(Project.owner_id == owner_id)

    if vendor_sales_manager_id:
        query = query.filter(Project.vendor_sales_manager_id == vendor_sales_manager_id)

    if is_active:
        is_active_value = is_active.lower() == 'true'
        query = query.filter(Project.is_active == is_active_value)

    if industry:
        query = query.filter(Project.industry == industry)

    if report_source:
        query = query.filter(Project.report_source == report_source)

    if project_type:
        query = query.filter(Project.project_type == project_type)

    if current_stage:
        query = query.filter(Project.current_stage == current_stage)

    return query


def get_full_project_stats(base_query, target_currency='CNY'):
    """使用数据库聚合查询获取完整项目统计数据"""
    from sqlalchemy import func, case
    from app import db
    from app.services.exchange_rate_service import exchange_rate_service


    try:
        # 1. 基础统计查询 - 使用数据库聚合函数
        base_stats = base_query.with_entities(
            func.count(Project.id).label('total_count'),
            func.sum(Project.is_active.cast(db.Integer)).label('active_count'),
            func.sum((~Project.is_active).cast(db.Integer)).label('inactive_count'),
            func.sum(func.coalesce(Project.quotation_customer, 0)).label('total_amount')
        ).first()


        # 2. 阶段统计查询 - 按阶段分组聚合
        stage_stats_raw = base_query.with_entities(
            Project.current_stage,
            func.count(Project.id).label('count'),
            func.sum(func.coalesce(Project.quotation_customer, 0)).label('amount')
        ).group_by(Project.current_stage).all()

        # 3. 处理阶段统计数据
        all_stages = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused']
        stage_stats = {}

        # 初始化所有阶段
        for stage in all_stages:
            stage_stats[stage] = {'count': 0, 'amount': 0}

        # 填充查询结果
        total_cny_amount = 0
        for stage, count, amount in stage_stats_raw:
            if stage in stage_stats:
                stage_stats[stage]['count'] = count or 0
                stage_stats[stage]['amount'] = amount or 0
                total_cny_amount += (amount or 0)

        # 4. 汇率转换（如果需要）
        total_converted_amount = base_stats.total_amount or 0
        if target_currency == 'USD' and total_cny_amount > 0:
            total_converted_amount = exchange_rate_service.convert_amount(total_cny_amount, 'CNY', 'USD')

            # 按比例转换各阶段金额
            if total_cny_amount > 0:
                conversion_ratio = total_converted_amount / total_cny_amount
                for stage in stage_stats:
                    if stage_stats[stage]['amount'] > 0:
                        stage_stats[stage]['amount'] *= conversion_ratio

        result = {
            'total_count': base_stats.total_count or 0,
            'active_count': base_stats.active_count or 0,
            'inactive_count': base_stats.inactive_count or 0,
            'total_value': total_converted_amount,
            'stage_stats': stage_stats
        }

        return result

    except Exception as e:
        current_app.logger.error(f"获取完整项目统计失败: {str(e)}")
        # 返回默认值避免页面错误
        default_result = {
            'total_count': 0,
            'active_count': 0,
            'inactive_count': 0,
            'total_value': 0,
            'stage_stats': {stage: {'count': 0, 'amount': 0} for stage in ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused']}
        }
        return default_result

def _format_stats_for_ajax(full_stats):
    """将get_full_project_stats的输出格式化为AJAX接口需要的格式"""
    stage_stats = full_stats.get('stage_stats', {})

    return {
        'total': full_stats.get('total_count', 0),
        'total_amount': round(full_stats.get('total_value', 0) / 10000, 2),
        'discover': stage_stats.get('discover', {'count': 0})['count'],
        'discover_amount': round(stage_stats.get('discover', {'amount': 0})['amount'] / 10000, 2),
        'embed': stage_stats.get('embed', {'count': 0})['count'],
        'embed_amount': round(stage_stats.get('embed', {'amount': 0})['amount'] / 10000, 2),
        'pre_tender': stage_stats.get('pre_tender', {'count': 0})['count'],
        'pre_tender_amount': round(stage_stats.get('pre_tender', {'amount': 0})['amount'] / 10000, 2),
        'tendering': stage_stats.get('tendering', {'count': 0})['count'],
        'tendering_amount': round(stage_stats.get('tendering', {'amount': 0})['amount'] / 10000, 2),
        'awarded': stage_stats.get('awarded', {'count': 0})['count'],
        'awarded_amount': round(stage_stats.get('awarded', {'amount': 0})['amount'] / 10000, 2),
        'quoted': stage_stats.get('quoted', {'count': 0})['count'],
        'quoted_amount': round(stage_stats.get('quoted', {'amount': 0})['amount'] / 10000, 2),
        'signed': stage_stats.get('signed', {'count': 0})['count'],
        'signed_amount': round(stage_stats.get('signed', {'amount': 0})['amount'] / 10000, 2),
        'lost': stage_stats.get('lost', {'count': 0})['count'],
        'lost_amount': round(stage_stats.get('lost', {'amount': 0})['amount'] / 10000, 2),
        'paused': stage_stats.get('paused', {'count': 0})['count'],
        'paused_amount': round(stage_stats.get('paused', {'amount': 0})['amount'] / 10000, 2),
    }




@project.route('/update_project_sharing/<int:project_id>', methods=['POST'])
@login_required
@permission_required('project', 'edit')
def update_project_sharing(project_id):
    """更新项目共享设置"""
    try:
        project_obj = Project.query.get_or_404(project_id)
        
        # 检查用户是否有权限编辑项目共享设置
        from app.utils.sharing import SharingService
        if not SharingService.can_edit_sharing_settings(current_user, project_obj, 'project'):
            flash(_('您没有权限编辑此项目的共享设置'), 'error')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 更新共享设置
        if SharingService.update_sharing_from_request(project_obj, current_user, 'project'):
            db.session.commit()
            flash(_('项目共享设置已更新'), 'success')
            logger.info(f"用户 {current_user.username} 更新了项目 {project_obj.project_name} (ID: {project_id}) 的共享设置")
        else:
            flash(_('更新共享设置失败'), 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(_('更新共享设置时发生错误'), 'error')
        logger.error(f"更新项目共享设置失败: {e}")
    
    return redirect(url_for('project.view_project', project_id=project_id))

# ===== 项目-客户关联管理API =====

@project.route('/api/search_customers')
@login_required
def search_customers_temp():
    """搜索客户API - 优化版本，支持显示更多信息和排序（临时去掉权限检查）"""
    
    # 临时权限检查：如果用户未认证，返回错误
    if not current_user.is_authenticated:
        logger.error("用户未认证")
        return jsonify({'success': False, 'message': '用户未认证'}), 401
        
    # 如果不是admin，也检查权限
    if current_user.role != 'admin' and not current_user.has_permission('project', 'view'):
        logger.error("用户权限不足")
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    search_term = request.args.get('search', '').strip()
    if not search_term:
        search_term = request.args.get('q', '').strip()  # 兼容旧参数名
    
    if not search_term or len(search_term) < 2:
        return jsonify({
            'success': False,
            'message': '搜索关键词至少需要2个字符'
        })
    
    try:
        from app.models.customer import Company, Contact
        from app.models.user import User
        
        logger.info(f"搜索客户，关键词: {search_term}, 用户ID: {current_user.id}")
        
        # 简化查询，直接获取所有未删除的匹配公司，并加载关联数据
        companies = Company.query.filter(
            Company.is_deleted == False,
            Company.company_name.ilike(f'%{search_term}%')
        ).outerjoin(User, Company.owner_id == User.id).order_by(
            # 用户自己的客户排在前面
            db.case((Company.owner_id == current_user.id, 0), else_=1),
            Company.company_name
        ).limit(20).all()
        
        logger.info(f"找到客户总数: {len(companies)} 个")
        
        
        customers = []
        for company in companies:
            # 获取主联系人（简化版本，避免懒加载问题）
            primary_contact_name = ''
            try:
                primary_contact = Contact.query.filter_by(
                    company_id=company.id, 
                    is_primary=True
                ).first()
                if not primary_contact:
                    primary_contact = Contact.query.filter_by(company_id=company.id).first()
                if primary_contact:
                    primary_contact_name = primary_contact.name
            except Exception as e:
                logger.warning(f"获取联系人失败: {e}")
            
            # 构建客户信息
            customer_data = {
                'id': company.id,
                'company_name': company.company_name,
                'contact_person': primary_contact_name,
                'industry': company.industry or '',
                'owner': {
                    'id': company.owner.id if company.owner else None,
                    'username': company.owner.username if company.owner else '',
                    'real_name': company.owner.real_name if company.owner else '未设置',
                    'is_vendor_user': company.owner.is_vendor_user() if company.owner and hasattr(company.owner, 'is_vendor_user') else False
                },
                'is_active': bool(company.owner.is_active) if company.owner else False
            }
            customers.append(customer_data)
            logger.info(f"处理客户: {company.company_name}, 拥有人: {company.owner.real_name if company.owner else 'None'}")
        
        logger.info(f"返回搜索结果: {len(customers)} 个客户")
        return jsonify({
            'success': True,
            'results': customers
        })
        
    except Exception as e:
        logger.error(f"搜索客户失败: {e}")
        return jsonify({
            'success': False,
            'message': '搜索客户失败，请重试'
        }), 500

@project.route('/api/customer_associations/<int:project_id>')
@permission_required('project', 'view')  
def get_customer_associations(project_id):
    """获取项目的客户关联列表"""
    try:
        from app.models.project_customer_association import ProjectCustomerAssociation
        
        # 验证项目访问权限
        project_obj = Project.query.get_or_404(project_id)
        if not can_view_project(current_user, project_obj):
            return jsonify({
                'success': False,
                'message': '没有权限查看此项目的客户关联'
            }), 403
        
        # 获取活跃的客户关联
        associations = ProjectCustomerAssociation.get_active_associations(project_id)
        
        associations_data = []
        
        for assoc in associations:
            company = assoc.company
            # 检查当前用户是否有权限查看此客户
            from app.utils.access_control import can_view_company
            can_view_customer = can_view_company(current_user, company) if company else False
            
            # 检查是否可以移除此关联
            # 严格遵循"谁关联谁删除"原则
            can_remove = False
            
            # 只有管理员有完全权限
            if current_user.role == 'admin':
                can_remove = True
            # 只有创建者可以移除自己创建的关联
            elif (hasattr(assoc, 'created_by') and
                  assoc.created_by == current_user.id):
                can_remove = True
            
            # 获取拥有者信息，用于正确显示徽章
            owner_info = None
            if company.owner:
                owner_info = {
                    'real_name': company.owner.real_name,
                    'username': company.owner.username,
                    'is_vendor_user': company.owner.is_vendor_user()
                }
            
            # 获取创建者信息（安全处理）
            created_by_name = None
            try:
                if hasattr(assoc, 'creator') and assoc.creator:
                    created_by_name = assoc.creator.real_name or assoc.creator.username
            except Exception as e:
                # 如果creator字段不存在或查询失败，使用created_by字段
                logger.debug(f"获取创建者信息失败: {e}")
                if hasattr(assoc, 'created_by') and assoc.created_by:
                    try:
                        from app.models.user import User
                        creator_user = User.query.get(assoc.created_by)
                        if creator_user:
                            created_by_name = creator_user.real_name or creator_user.username
                    except Exception as e2:
                        logger.debug(f"查询创建者用户失败: {e2}")
                        created_by_name = f"用户#{assoc.created_by}" if hasattr(assoc, 'created_by') else None
            
            associations_data.append({
                'id': assoc.id,
                'company_id': assoc.company_id,
                'company_name': company.company_name,
                'customer_type': assoc.customer_type,
                'customer_type_label': assoc.customer_type_label,
                'company_type': company.company_type,
                'owner_name': company.owner.real_name if company.owner else None,
                'owner_info': owner_info,
                'is_active': company.owner.is_active if company.owner else False,
                'can_remove': can_remove,
                'can_view_customer': can_view_customer,
                'created_by': assoc.created_by,
                'created_by_name': created_by_name,
                'created_at': assoc.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'associations': associations_data
        })
        
    except Exception as e:
        logger.error(f"获取项目客户关联失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取客户关联失败，请重试'
        }), 500

@project.route('/api/add_customer_association', methods=['POST'])
@permission_required('project', 'view')
def add_customer_association():
    """添加项目-客户关联"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        company_id = data.get('company_id')
        customer_type = data.get('customer_type')
        
        if not all([project_id, company_id, customer_type]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        # 验证项目查看权限（有查看权限即可添加客户关联）
        project_obj = Project.query.get_or_404(project_id)
        if not can_view_project(current_user, project_obj):
            return jsonify({
                'success': False,
                'message': '没有权限访问此项目'
            }), 403
        
        # 验证客户类型
        valid_types = ['end_user', 'design_issues', 'contractor', 'system_integrator', 'dealer']
        if customer_type not in valid_types:
            return jsonify({
                'success': False,
                'message': '无效的客户类型'
            }), 400
        
        # 验证公司是否存在
        from app.models.customer import Company
        company = Company.query.filter_by(id=company_id, is_deleted=False).first()
        if not company:
            return jsonify({
                'success': False,
                'message': '指定的客户不存在'
            }), 404
        
        # 添加关联
        from app.models.project_customer_association import ProjectCustomerAssociation
        
        # 检查是否支持created_by字段
        try:
            # 尝试使用创建者ID
            success, result = ProjectCustomerAssociation.add_association(project_id, company_id, customer_type, current_user.id)
        except Exception as e:
            logger.debug(f"使用created_by字段失败，尝试不使用创建者ID: {e}")
            # 如果失败，尝试不使用created_by字段
            try:
                success, result = ProjectCustomerAssociation.add_association(project_id, company_id, customer_type)
            except Exception as e2:
                logger.error(f"添加关联完全失败: {e2}")
                return jsonify({
                    'success': False,
                    'message': '数据库错误，请联系管理员'
                }), 500
        
        if success:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '客户关联添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': result
            }), 400
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加客户关联失败: {e}")
        return jsonify({
            'success': False,
            'message': '添加客户关联失败，请重试'
        }), 500

@project.route('/api/remove_customer_association/<int:association_id>', methods=['POST'])
@permission_required('project', 'view')
def remove_customer_association(association_id):
    """移除项目-客户关联"""
    try:
        from app.models.project_customer_association import ProjectCustomerAssociation
        
        # 获取关联记录
        association = ProjectCustomerAssociation.query.get_or_404(association_id)
        
        # 验证移除权限
        # 严格遵循"谁关联谁删除"原则
        can_remove = False
        
        # 只有管理员有完全权限
        if current_user.role == 'admin':
            can_remove = True
        # 只有创建者可以移除自己创建的关联
        elif (hasattr(association, 'created_by') and
              association.created_by == current_user.id):
            can_remove = True
        
        if not can_remove:
            return jsonify({
                'success': False,
                'message': '您只能移除自己添加的客户关联'
            }), 403
        
        # 移除关联
        success, message = ProjectCustomerAssociation.remove_association(association_id)
        
        if success:
            db.session.commit()
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
        db.session.rollback()
        logger.error(f"移除客户关联失败: {e}")
        return jsonify({
            'success': False,
            'message': '移除客户关联失败，请重试'
        }), 500

@project.route('/api/customer_associations/<int:project_id>/render')
@permission_required('project', 'view')
def render_customer_associations_list(project_id):
    """渲染项目客户关联列表的通用组件HTML"""
    from flask import render_template
    from app.models.project_customer_association import ProjectCustomerAssociation
    
    try:
        # 验证项目访问权限
        project_obj = Project.query.get_or_404(project_id)
        if not can_view_project(current_user, project_obj):
            return jsonify({
                'success': False,
                'message': '没有权限查看此项目的客户关联'
            }), 403
        
        # 获取客户关联数据
        associations = ProjectCustomerAssociation.get_active_associations(project_id)
        
        # 准备数据供模板使用
        association_data = []
        for association in associations:
            company = association.company
            owner = company.owner if company else None
            
            can_remove = ((current_user.role == 'admin' or 
                          current_user.id == project_obj.owner_id) and 
                         (not project_obj.is_locked or current_user.role == 'admin'))
            
            # 检查当前用户是否有权限查看此客户
            from app.utils.access_control import can_view_company
            can_view_customer = can_view_company(current_user, company) if company else False
            
            association_data.append({
                'id': association.id,
                'company_id': company.id,
                'company_name': company.company_name,
                'customer_type_label': dict(ProjectCustomerAssociation.CUSTOMER_TYPE_CHOICES).get(
                    association.customer_type, association.customer_type
                ),
                'owner_name': owner.real_name if owner else None,
                'is_active': bool(owner.is_active) if owner else False,
                'can_remove': can_remove,
                'can_view_customer': can_view_customer,
                'company': company  # 为模板权限检查提供company对象
            })
        
        # 使用专门的模板渲染客户关联列表
        
        rendered_html = render_template(
            'project/customer_associations_list.html',
            associations=association_data
        )
        
        return jsonify({
            'success': True,
            'html': rendered_html
        })
        
    except Exception as e:
        logger.error(f"渲染客户关联列表失败: {e}")
        return jsonify({
            'success': False,
            'message': '渲染客户关联列表失败，请重试'
        }), 500


@project.route('/<int:project_id>/start_approval', methods=['POST'])
@login_required
@permission_required('project', 'edit')
def start_project_approval(project_id):
    """启动项目审批流程"""
    try:
        project_obj = Project.query.get_or_404(project_id)
        
        # 检查权限
        if not can_edit_data(project_obj, current_user):
            return jsonify({
                'success': False,
                'message': '您没有权限提交此项目的审批'
            }), 403
        
        # 检查项目类型是否填写
        if not project_obj.project_type or project_obj.project_type.strip() == '':
            return jsonify({
                'success': False,
                'message': '项目类型未填写，无法提交审批。请先完善项目信息。'
            }), 400
        
        # 检查是否已经有进行中的审批
        from app.helpers.approval_helpers import get_object_approval_instance
        existing_approval = get_object_approval_instance('project', project_id)
        if existing_approval and existing_approval.status == 'pending':
            return jsonify({
                'success': False,
                'message': '此项目已有进行中的审批流程'
            }), 400
        
        # 获取可用的审批模板
        from app.helpers.approval_helpers import get_available_templates
        templates = get_available_templates('project')
        if not templates:
            return jsonify({
                'success': False,
                'message': '未找到可用的项目审批模板，请联系管理员配置'
            }), 400
        
        # 使用第一个可用模板（通常是"测试流程分支"）
        template = templates[0]
        
        # 启动审批流程
        from app.helpers.approval_helpers import start_approval_process
        approval_instance = start_approval_process(
            object_type='project',
            object_id=project_id,
            template_id=template.id,
            user_id=current_user.id
        )
        
        if approval_instance:
            db.session.commit()
            logging.info(f"项目 {project_id} 审批流程启动成功，审批实例ID: {approval_instance.id}")
            return jsonify({
                'success': True,
                'message': '项目审批已提交成功',
                'approval_instance_id': approval_instance.id
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': '启动审批流程失败，请检查项目状态或联系管理员'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"启动项目审批失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'系统错误: {str(e)}'
        }), 500


# ==================== 订单审批系统风格的项目审批API端点 ====================

@project.route('/api/approval/<int:project_id>/templates')
@login_required
@permission_required('project', 'view')
def get_project_approval_templates(project_id):
    """获取项目审批模板列表"""
    try:
        # 检查项目访问权限
        viewable_projects = get_viewable_data(Project, current_user)
        project_obj = viewable_projects.filter_by(id=project_id).first()
        if not project_obj:
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404
        
        # 获取项目类型的审批模板
        from app.models.approval import ApprovalProcessTemplate
        templates = ApprovalProcessTemplate.query.filter_by(
            object_type='project',
            is_active=True
        ).order_by(ApprovalProcessTemplate.name).all()
        
        template_list = []
        for template in templates:
            template_list.append({
                'id': template.id,
                'name': template.name,
                'description': template.description or '',
                'total_steps': len(template.steps)
            })
        
        return jsonify({
            'success': True,
            'templates': template_list
        })
    except Exception as e:
        logging.error(f"获取项目审批模板失败：{str(e)}")
        return jsonify({'success': False, 'message': f'获取失败：{str(e)}'})


@project.route('/api/approval/<int:project_id>/preview-authorization', methods=['POST'])
@login_required
@permission_required('project', 'view')
def preview_project_authorization(project_id):
    """预览项目授权编码"""
    try:
        # 获取项目
        viewable_projects = get_viewable_data(Project, current_user)
        project_obj = viewable_projects.filter_by(id=project_id).first()
        if not project_obj:
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404
        
        # 获取当前审批实例和步骤
        from app.helpers.approval_helpers import get_object_approval_instance
        approval_instance = get_object_approval_instance('project', project_id)
        if not approval_instance:
            return jsonify({
                'success': False,
                'message': '项目暂无审批流程'
            })
        
        # 获取当前步骤
        from app.models.approval import ApprovalStep
        current_step = ApprovalStep.query.get(approval_instance.current_step)
        if not current_step:
            return jsonify({
                'success': False,
                'message': '未找到当前审批步骤'
            })
        
        # 检查是否为授权步骤（简化版本）
        is_auth_step = False
        if current_step.action_type == 'authorization':
            is_auth_step = True
        elif current_step.action_type == 'branch_decision' and current_step.branch_condition:
            try:
                import json
                branch_condition = current_step.branch_condition
                if isinstance(branch_condition, str):
                    branch_condition = json.loads(branch_condition)
                
                field_name = branch_condition.get('field')
                if field_name:
                    field_value = getattr(project_obj, field_name, None)
                    conditions = branch_condition.get('conditions', [])
                    for condition in conditions:
                        if ((condition.get('operator') == 'equals' and field_value == condition.get('value')) or
                            (condition.get('operator') == 'in' and field_value == condition.get('value')) or
                            (condition.get('operator') == 'contains' and condition.get('value') in str(field_value))):
                            is_auth_step = 'authorization' in condition.get('action', '')
                            break
            except Exception as e:
                logging.error(f"检查分支授权步骤失败: {e}")
                
        if not is_auth_step:
            return jsonify({
                'success': False,
                'message': '当前步骤不是授权步骤'
            })
        
        # 获取匹配的分支授权动作
        branch_action = None
        if current_step.action_type == 'branch_decision' and current_step.branch_condition:
            try:
                import json
                branch_condition = current_step.branch_condition
                if isinstance(branch_condition, str):
                    branch_condition = json.loads(branch_condition)
                
                field_name = branch_condition.get('field')
                if field_name:
                    field_value = getattr(project_obj, field_name, None)
                    conditions = branch_condition.get('conditions', [])
                    for condition in conditions:
                        if ((condition.get('operator') == 'equals' and field_value == condition.get('value')) or
                            (condition.get('operator') == 'in' and field_value == condition.get('value')) or
                            (condition.get('operator') == 'contains' and condition.get('value') in str(field_value))):
                            branch_action = condition.get('action')
                            break
            except Exception as e:
                logging.error(f"解析分支条件失败: {e}")
        
        # 使用重构后的授权处理函数（预览模式）
        from app.helpers.approval_helpers import _handle_project_authorization
        preview_code = _handle_project_authorization(
            approval_instance, 
            project_obj.project_type, 
            preview_only=True, 
            branch_action=branch_action
        )
        
        return jsonify({
            'success': True,
            'authorization_code': preview_code,
            'message': f'通过审批后将授予授权编码：{preview_code}'
        })
        
    except Exception as e:
        logging.error(f"预览授权编码失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'预览失败：{str(e)}'
        }), 500


@project.route('/api/approval/<int:project_id>/submit', methods=['POST'])
@login_required
@permission_required('project', 'edit')
def submit_project_approval_standard(project_id):
    """提交项目审批 - 标准化API"""
    try:
        logging.info(f"提交项目审批请求: project_id={project_id}, user_id={current_user.id}")
        
        # 获取项目
        viewable_projects = get_viewable_data(Project, current_user)
        project_obj = viewable_projects.filter_by(id=project_id).first()
        if not project_obj:
            logging.warning(f"项目不存在或无权限访问: project_id={project_id}")
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404
        
        logging.info(f"项目当前状态: status={project_obj.status}, is_locked={project_obj.is_locked}")
        
        # 检查项目状态
        if project_obj.status not in ['draft', 'rejected']:
            logging.warning(f"项目状态不允许提交审批: status={project_obj.status}")
            return jsonify({
                'success': False, 
                'message': '只有草稿或被拒绝状态的项目才能提交审批'
            })
        
        # 检查编辑权限
        if not can_edit_data(project_obj, current_user):
            logging.warning(f"无编辑权限: project_id={project_id}, user_id={current_user.id}")
            return jsonify({
                'success': False,
                'message': '只有项目创建人可以提交审批'
            }), 403
        
        # 导入审批相关函数
        from app.helpers.approval_helpers import start_approval_process, get_available_templates
        
        # 获取可用的审批模板
        templates = get_available_templates('project')
        if not templates:
            return jsonify({
                'success': False,
                'message': '未找到可用的项目审批模板'
            }), 400
        
        # 获取请求数据
        data = request.get_json() or {}
        template_id = data.get('template_id')
        
        # 如果未指定模板，使用默认模板
        if not template_id:
            from app.models.approval import ApprovalProcessTemplate
            default_template = ApprovalProcessTemplate.query.filter_by(
                object_type='project',
                is_active=True
            ).first()
            
            if not default_template:
                return jsonify({
                    'success': False,
                    'message': '未找到可用的项目审批模板'
                }), 400
                
            template_id = default_template.id
        
        # 启动审批流程
        approval_instance = start_approval_process('project', project_id, template_id, current_user.id)
        
        if approval_instance:
            # 更新项目状态为待审批
            project_obj.status = 'pending'
            # 确保项目状态更新也在同一个事务中
            db.session.add(project_obj)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '项目审批已提交',
                'approval_instance_id': approval_instance.id
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': '启动审批流程失败'
            }), 500
    except Exception as e:
        db.session.rollback()
        logging.error(f"提交项目审批失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'提交失败：{str(e)}'
        }), 500


@project.route('/api/approval/<int:project_id>/flow')
@login_required
@permission_required('project', 'view')
def get_project_approval_flow(project_id):
    """获取项目审批流程数据"""
    try:
        # 检查项目访问权限 - 优先检查是否为项目审批人
        from app.helpers.approval_helpers import is_current_approver
        is_approver = is_current_approver('project', project_id, current_user.id)
        
        if is_approver:
            # 如果是当前审批人，直接获取项目（绕过常规权限检查）
            project_obj = Project.query.filter_by(id=project_id).first()
        else:
            # 否则使用常规权限检查
            viewable_projects = get_viewable_data(Project, current_user)
            project_obj = viewable_projects.filter_by(id=project_id).first()
            
        if not project_obj:
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404
        
        # 获取审批实例
        from app.helpers.approval_helpers import get_object_approval_instance
        approval_instance = get_object_approval_instance('project', project_id)
        
        if not approval_instance:
            return jsonify({
                'success': True,
                'has_approval': False,
                'message': '项目暂无审批流程'
            })
        
        # 获取审批流程数据 - 使用与报销相同的格式
        from app.helpers.approval_helpers import can_recall_approval, can_resubmit_approval
        from app.models.approval import ApprovalRecord, ApprovalStep
        
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
        current_step_id = approval_instance.current_step  # 当前步骤ID
        
        # 获取当前步骤的顺序，用于状态判断
        current_step_order = None
        for step in steps:
            if step.get('step_id') == current_step_id:
                current_step_order = step['step_order']
                break
        
        for i, step in enumerate(steps):
            # 确定审批人
            from app.helpers.approval_helpers import get_step_actual_approver
            actual_approver = get_step_actual_approver(step, approval_instance)
            
            # 获取这个步骤的审批记录
            step_records = []
            if step.get('step_id'):
                step_records = [r for r in records if r.step_id == step['step_id']]
            
            stage_data = {
                'id': step['step_id'],
                'stage_name': step['step_name'],
                'stage_order': step['step_order'],
                'approver_name': actual_approver.real_name if actual_approver else '待确定',
                'approver_id': actual_approver.id if actual_approver else None,
                'status': 'pending',
                'completed_time': None,
                'comment': None,
                'action': None,
                'arrived_at': None,
                'can_approve': False
            }
            
            # 处理审批记录
            if step_records:
                latest_record = step_records[-1]
                stage_data.update({
                    'status': 'approved' if latest_record.action == 'approve' else 'rejected',
                    'completed_time': latest_record.timestamp.isoformat(),
                    'comment': latest_record.comment,
                    'action': latest_record.action,
                    'arrived_at': latest_record.timestamp.isoformat()
                })
            elif step['step_id'] == current_step_id:
                # 当前步骤：使用步骤ID比较而非步骤顺序
                stage_data['status'] = 'current'
                stage_data['can_approve'] = (actual_approver and actual_approver.id == current_user.id)
            elif current_step_order and step['step_order'] < current_step_order:
                # 已处理的步骤（通常是已通过）：仅在有当前步骤顺序时比较
                stage_data['status'] = 'approved'
            
            stages_data.append(stage_data)
        
        # 获取实际状态
        from app.models.approval import ApprovalStatus
        actual_status = approval_instance.status.value if hasattr(approval_instance.status, 'value') else str(approval_instance.status).lower()
        
        # 检查是否被召回
        last_record = records[-1] if records else None
        if last_record and last_record.action == 'recall':
            actual_status = 'recalled'
        
        return jsonify({
            'success': True,
            'approval_flow': {
                'instance_id': approval_instance.id,
                'stages': stages_data,
                'current_stage': current_step_order,
                'can_approve': any(stage.get('can_approve', False) for stage in stages_data),
                'status': actual_status,
                'can_recall': can_recall_approval('project', project_id, current_user.id),
                'can_resubmit': can_resubmit_approval('project', project_id, current_user.id),
                'is_creator': approval_instance.created_by == current_user.id,
                'creator_id': approval_instance.created_by
            }
        })
    except Exception as e:
        logging.error(f"获取项目审批流程失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败：{str(e)}'
        }), 500


@project.route('/api/approval/<int:project_id>/recall', methods=['POST'])
@login_required
@permission_required('project', 'edit')
def recall_project_approval(project_id):
    """召回项目审批"""
    try:
        logging.info(f"项目召回请求: project_id={project_id}, user_id={current_user.id}")
        
        # 获取项目
        viewable_projects = get_viewable_data(Project, current_user)
        project_obj = viewable_projects.filter_by(id=project_id).first()
        if not project_obj:
            logging.warning(f"项目不存在或无权限访问: project_id={project_id}")
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404
        
        # 获取审批实例
        from app.helpers.approval_helpers import get_object_approval_instance
        approval_instance = get_object_approval_instance('project', project_id)
        
        if not approval_instance:
            logging.warning(f"项目没有审批流程: project_id={project_id}")
            return jsonify({
                'success': False,
                'message': '项目没有审批流程'
            }), 400
        
        logging.info(f"审批实例状态: instance_id={approval_instance.id}, status={approval_instance.status}, created_by={approval_instance.created_by}")
        
        # 检查召回权限：发起人或管理员可以召回
        if approval_instance.created_by != current_user.id and current_user.role != 'admin':
            logging.warning(f"召回权限检查失败: created_by={approval_instance.created_by}, current_user={current_user.id}, role={current_user.role}")
            return jsonify({
                'success': False,
                'message': '只有审批发起人或管理员可以召回'
            }), 403
        
        if approval_instance.status != ApprovalStatus.PENDING:
            logging.warning(f"审批状态不正确: status={approval_instance.status}, 期望状态=ApprovalStatus.PENDING")
            return jsonify({
                'success': False,
                'message': '只有进行中的审批可以召回'
            }), 400
        
        # 执行召回
        from app.helpers.approval_helpers import recall_approval
        result = recall_approval('project', project_id, current_user.id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 500
    except Exception as e:
        db.session.rollback()
        logging.error(f"召回项目审批失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'召回失败：{str(e)}'
        }), 500


@project.route('/api/approval/<int:project_id>/resubmit', methods=['POST'])
@login_required
@permission_required('project', 'edit')
def resubmit_project_approval(project_id):
    """重新提交项目审批"""
    try:
        # 重新提交实际上就是提交审批，所以直接调用提交接口
        return submit_project_approval_standard(project_id)
    except Exception as e:
        logging.error(f"重新提交项目审批失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'重新提交失败：{str(e)}'
        }), 500


@project.route('/<int:project_id>/generate_authorization', methods=['POST'])
@login_required
@permission_required('project', 'edit')
def generate_authorization_code(project_id):
    """审批通过后生成项目授权编号"""
    try:
        # 获取项目
        viewable_projects = get_viewable_data(Project, current_user)
        project = viewable_projects.filter_by(id=project_id).first()
        if not project:
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404
        
        # 检查编辑权限
        if not can_edit_data(project, current_user):
            return jsonify({
                'success': False,
                'message': '只有项目创建人可以生成授权编号'
            }), 403
        
        # 检查是否已有授权编号
        if project.authorization_code and project.authorization_code.strip():
            return jsonify({
                'success': False,
                'message': '项目已有授权编号，无需重复生成'
            }), 400
        
        # 检查审批状态
        from app.helpers.approval_helpers import get_object_approval_instance
        approval_instance = get_object_approval_instance('project', project_id)
        
        if not approval_instance or approval_instance.status != 'approved':
            return jsonify({
                'success': False,
                'message': '只有审批通过的项目才能生成授权编号'
            }), 400
        
        # 生成授权编号
        from app.helpers.authorization_helpers import generate_project_authorization_code
        authorization_code = generate_project_authorization_code(project)
        
        if authorization_code:
            project.authorization_code = authorization_code
            project.authorization_status = 'approved'
            project.authorization_date = datetime.now()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '授权编号生成成功',
                'authorization_code': authorization_code
            })
        else:
            return jsonify({
                'success': False,
                'message': '授权编号生成失败'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"生成授权编号失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'生成失败：{str(e)}'
        }), 500
