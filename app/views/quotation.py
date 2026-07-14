from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_babel import gettext as _, ngettext
from config import Config
from app.models.quotation import Quotation, QuotationDetail
from app.models.product_code import ProductCodeField, ProductCodeFieldOption, ProductSubcategory
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.product import Product  # 添加产品模型导入
from app.models.user import User  # 添加User模型导入
from app.utils.product_helpers import find_product_by_name_and_model  # 产品查询辅助函数
from datetime import datetime, date
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from app import db
from flask_login import login_required, current_user
from app.decorators import permission_required, permission_required_with_approval_context  # 添加权限装饰器导入
from app.extensions import csrf
from app.utils.access_control import get_viewable_data, can_edit_data, can_view_project, can_change_quotation_owner, can_view_quotation
import logging
import os
from decimal import Decimal
import json
from flask import current_app
from app.utils.dictionary_helpers import project_type_label, project_stage_label, REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS, COMPANY_TYPE_LABELS, get_currency_type_options, get_available_quotation_currencies
from app.services.exchange_rate_service import exchange_rate_service
from app.utils.chinese_mapping_manager import mapping_manager
from app.helpers.project_helpers import is_project_editable
from app.utils.activity_tracker import check_company_activity, update_active_status
from app.models.settings import SystemSettings
from zoneinfo import ZoneInfo
from app.utils.role_mappings import get_role_display_name
from app.helpers.approval_helpers import get_object_approval_instance, get_current_step_info, can_user_approve
from app.utils.work_item_recorder import record_activity
from sqlalchemy import event
from app.models.quotation import update_quotation_implant_total, QuotationDetail
from app.utils.price_consistency import normalize_discount
from app.utils.query_filters import (
    extract_filter_params, apply_filters_to_query, extract_sort_params,
    extract_pagination_params
)

# 配置日志
logger = logging.getLogger(__name__)

quotation = Blueprint('quotation', __name__)

# ============================================================
# 报价单筛选配置（与客户/项目管理保持一致的通用模式）
# ============================================================
# 注意：search 字段不使用通用工具，因为需要同时搜索报价单编号和关联项目名称（跨表）
QUOTATION_FILTER_CONFIG = {
    'owner_filter': {'type': 'exact', 'field': 'owner_id'},
    'project_stage_filter': {'type': 'exact', 'field': 'project_stage'},
    'confirm_filter': {'type': 'exact', 'field': 'confirmation_badge_status'},
    # search 和 project_type_filter 需要关联 Project 表，在查询中手动处理
}

@quotation.route('/quotations')
@login_required
@permission_required('quotation', 'view')
def list_quotations():
    try:
        # ============================================================
        # 1. 使用通用工具提取参数（替代手动解析）
        # ============================================================
        from app.utils.query_filters import apply_default_owner_filter
        filters = extract_filter_params(request.args, QUOTATION_FILTER_CONFIG)
        offset, limit = extract_pagination_params(request.args, default_limit=30, max_limit=100)

        # 提取变量用于模板显示（search 从 request.args 获取，因为需要跨表搜索）
        search = request.args.get('search', '').strip()
        project_stage_filter = filters.get('project_stage_filter', '')

        # 默认筛选：首次加载时只显示当前用户的报价单
        # 注意：system/company级别权限用户不应用默认过滤
        owner_filter = apply_default_owner_filter(
            request.args, filters, current_user.id,
            owner_field='owner_filter',
            filter_keys=['search', 'project_stage_filter', 'project_type_filter', 'project'],
            module_id='quotation',
            model_class=Quotation
        )
        project_search = request.args.get('project', '')

        # 获取排序参数
        valid_sort_fields = ['quotation_number', 'created_at', 'updated_at', 'amount',
                            'approval_status', 'owner_id', 'project_name', 'project_stage', 'project_type']
        sort_field, sort_order = extract_sort_params(
            request.args, default_sort='updated_at', default_order='desc',
            allowed_fields=valid_sort_fields
        )

        # ============================================================
        # 2. 构建查询（权限控制，仅1次 get_viewable_data）
        # ============================================================
        base_query = get_viewable_data(Quotation, current_user)
        query = base_query

        # ============================================================
        # 3. 默认筛选（从权限配置的 content_filters 读取）
        # ============================================================
        project_type_filter = request.args.get('project_type_filter', '')
        if not project_type_filter:
            # 从权限配置中读取 content_filters 作为默认筛选
            # 注：用户的 quotation 权限配置中可设置 content_filters = {"project_type": ["channel_follow"]}
            # 这样用户首次访问时会自动应用该筛选条件
            permission = current_user.get_permission_config('quotation')
            if permission and hasattr(permission, 'content_filters') and permission.content_filters:
                content_filters = permission.content_filters
                if isinstance(content_filters, dict) and 'project_type' in content_filters:
                    default_types = content_filters.get('project_type', [])
                    if default_types and len(default_types) == 1:
                        project_type_filter = default_types[0]

        # ============================================================
        # 4. 应用筛选（使用通用工具 + 手动处理特殊情况）
        # ============================================================
        # 使用通用工具应用基本筛选（owner_filter, project_stage_filter）
        query = apply_filters_to_query(query, Quotation, filters, QUOTATION_FILTER_CONFIG)

        # 全局搜索（使用子查询避免与 content_filter 的 Project JOIN 冲突）
        if search:
            matching_project_ids = db.session.query(Project.id).filter(
                Project.project_name.ilike(f'%{search}%')
            )
            query = query.filter(
                or_(
                    Quotation.quotation_number.ilike(f'%{search}%'),
                    Quotation.project_id.in_(matching_project_ids)
                )
            )

        # 项目名称单独搜索（使用子查询）
        if project_search and not search:
            matching_project_ids = db.session.query(Project.id).filter(
                Project.project_name.ilike(f'%{project_search}%')
            )
            query = query.filter(Quotation.project_id.in_(matching_project_ids))

        # 项目类型筛选（使用子查询避免 JOIN 冲突）
        if project_type_filter:
            if project_type_filter == 'channel_follow':
                type_cond = Project.project_type == 'channel_follow'
            elif project_type_filter == 'sales_focus':
                type_cond = Project.project_type.in_(['sales_focus', 'sales_key'])
            elif project_type_filter == 'marketing_focus':
                type_cond = Project.project_type.in_(['sales_focus', 'sales_key', 'channel_follow'])
            else:
                type_cond = Project.project_type == project_type_filter

            matching_project_ids = db.session.query(Project.id).filter(type_cond)
            query = query.filter(Quotation.project_id.in_(matching_project_ids))

        # 保存过滤后的查询（无 ORDER BY），用于统计聚合
        filtered_query = query

        # ============================================================
        # 5. 应用排序
        # ============================================================
        if sort_field == 'project_name':
            query = query.outerjoin(Project, Quotation.project_id == Project.id)
            order_attr = Project.project_name
        elif sort_field == 'project_type':
            query = query.outerjoin(Project, Quotation.project_id == Project.id)
            order_attr = Project.project_type
        elif hasattr(Quotation, sort_field):
            order_attr = getattr(Quotation, sort_field)
        else:
            order_attr = Quotation.updated_at

        query = query.order_by(order_attr.desc() if sort_order == 'desc' else order_attr.asc())

        # ============================================================
        # 6. 分页
        # ============================================================
        total_count = query.count()
        quotations = query.offset(offset).limit(limit).all()
        has_more = (offset + limit) < total_count

        # 预加载所有报价单的所有者信息
        owner_ids = [q.owner_id for q in quotations if q.owner_id]
        if owner_ids:
            owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
            for q in quotations:
                if q.owner_id and q.owner_id in owners:
                    q.owner = owners[q.owner_id]
        
        # 获取实际存在的项目类型选项 - 复用 base_query 避免重复 get_viewable_data
        from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS

        # 获取当前语言
        from app.utils.i18n import get_current_language, get_default_currency, get_currency_symbol
        current_lang = get_current_language()

        # 复用 base_query（行91的 get_viewable_data），无需再次调用
        base_subquery = base_query.with_entities(Quotation.id).subquery()

        unique_project_types_query = db.session.query(Project.project_type.distinct())\
            .join(Quotation, Project.id == Quotation.project_id)\
            .filter(Quotation.id.in_(db.session.query(base_subquery.c.id)))\
            .filter(Project.project_type.isnot(None))\
            .filter(Project.project_type != '')

        unique_project_types = {row[0] for row in unique_project_types_query.all()}

        # 构建项目类型选项（不包含"全部"选项，因为模板中已经有了）
        project_type_options = []

        for project_type in unique_project_types:
            if project_type in PROJECT_TYPE_LABELS:
                project_type_options.append({
                    'value': project_type,
                    'label': PROJECT_TYPE_LABELS[project_type][current_lang]
                })
            else:
                project_type_options.append({
                    'value': project_type,
                    'label': project_type
                })

        # 获取筛选选项数据 - 复用 base_query
        unique_owner_ids = {row[0] for row in base_query.with_entities(
            Quotation.owner_id.distinct()
        ).filter(Quotation.owner_id.isnot(None)).all()}

        available_users = User.query.filter(
            User.id.in_(unique_owner_ids)
        ).order_by(User.real_name, User.username).all()

        # 报价阶段选项 - 复用 base_query
        from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS

        unique_project_stages = {row[0] for row in base_query.with_entities(
            Quotation.project_stage.distinct()
        ).filter(
            Quotation.project_stage.isnot(None),
            Quotation.project_stage != ''
        ).all()}

        # 构建报价阶段选项，只包含实际存在的阶段
        project_stage_options = []
        for stage in unique_project_stages:
            if stage in PROJECT_STAGE_LABELS:
                project_stage_options.append({
                    'value': stage,
                    'label': PROJECT_STAGE_LABELS[stage][current_lang]
                })
            else:
                # 处理没有在字典中定义的项目阶段
                project_stage_options.append({
                    'value': stage,
                    'label': stage
                })
        
        # 按标签排序
        project_stage_options.sort(key=lambda x: x['label'])
        
        # 配置语言感知的显示单位
        if current_lang == 'en':
            amount_unit = 'M'
            amount_divisor = 1000000
        else:
            amount_unit = Config.AMOUNT_UNIT
            amount_divisor = Config.AMOUNT_DIVISOR
        default_currency = Config.DEFAULT_CURRENCY
        currency_symbol = get_currency_symbol(default_currency)

        # 计算统计数据 —— count 仍用 SQL 聚合，amount 用 MultiCurrencyAggregationService 做跨货币换算
        from sqlalchemy import case
        from app.services.multi_currency_aggregation import MultiCurrencyAggregationService

        # 数量统计（不涉及货币，直接 SQL）
        count_result = filtered_query.with_entities(
            func.count(Quotation.id).label('total'),
            func.count(case((Quotation.approval_status == 'approved', Quotation.id))).label('approved_count'),
            func.count(case((Quotation.approval_status.in_(['pending', 'in_progress']), Quotation.id))).label('pending_count'),
            func.count(case((Quotation.approval_status == 'draft', Quotation.id))).label('draft_count'),
        ).first()

        # 金额统计（跨货币换算到系统默认货币）
        amount_stats = MultiCurrencyAggregationService.sum_converted_with_conditions(
            filtered_query,
            Quotation.amount,
            Quotation.currency,
            {
                'total': None,
                'approved': Quotation.approval_status == 'approved',
                'pending': Quotation.approval_status.in_(['pending', 'in_progress']),
                'draft': Quotation.approval_status == 'draft',
            }
        )

        total_stats_count = count_result.total or 0
        total_stats_amount = round(amount_stats['total'] / amount_divisor, 2)
        approved_count = count_result.approved_count or 0
        approved_amount = round(amount_stats['approved'] / amount_divisor, 2)
        pending_count = count_result.pending_count or 0
        pending_amount = round(amount_stats['pending'] / amount_divisor, 2)
        draft_count = count_result.draft_count or 0
        draft_amount = round(amount_stats['draft'] / amount_divisor, 2)
        
        # 构建标准化筛选配置
        filter_config = {
            'action_url': url_for('quotation.list_quotations'),
            'form_id': 'quotationFilterForm',
            'reset_url': url_for('quotation.list_quotations'),
            
            'search_field': {
                'name': 'search',
                'label': _(mapping_manager.get_field_display_name('common', 'search')),
                'placeholder': _('报价单编号或项目名称'),
                'value': search,
                'col_width': 4
            },
            
            'filter_fields': [
                {
                    'name': 'owner_filter',
                    'label': _('负责人'),
                    'all_option_text': _('全部负责人'),
                    'current_value': owner_filter,
                    'col_width': 2,
                    'options': [
                        {'value': str(user.id), 'label': user.real_name or user.username}
                        for user in available_users
                    ]
                },
                {
                    'name': 'project_type_filter',
                    'label': _(mapping_manager.get_field_display_name('project', 'project_type')),
                    'all_option_text': _('全部类型'),
                    'current_value': project_type_filter if project_type_filter and request.args else '',
                    'col_width': 2,
                    'options': project_type_options
                },
                {
                    'name': 'project_stage_filter',
                    'label': _('报价阶段'),
                    'all_option_text': _('全部阶段'),
                    'current_value': project_stage_filter if project_stage_filter and request.args else '',
                    'col_width': 2,
                    'options': project_stage_options
                },
                {
                    'name': 'confirm_filter',
                    'label': _('确认状态'),
                    'all_option_text': _('全部状态'),
                    'current_value': request.args.get('confirm_filter', ''),
                    'col_width': 2,
                    'options': [
                        {'value': 'pending', 'label': _('待确认')},
                        {'value': 'confirmed', 'label': _('已确认')},
                        {'value': 'reconfirm', 'label': _('再次确认')},
                    ]
                }
            ],
            
            # 启用自动提交和其他筛选功能
            'auto_submit': True,
            'ajax_mode': True,
            'dynamic_reset_button': True,
            'adaptive_width': True,
            'adaptive_button_layout': True,
            
            'search_button_text': _('搜索'),
            'reset_button_text': _('重置')
        }
        
        # 通用列表组件配置
        list_config = {
            'module_name': 'quotation',
            'title': None,  # 页面级标题由模板控制，此处不显示
            'ajax_mode': True,
            
            # 无限滚动配置
            'infinite_scroll': {
                'enabled': True,
                'page_size': 60,
                'scroll_threshold': 100,
                'container_selector': '.table-responsive'
            },
            
            # 统计卡片配置
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': _('全部报价单'),
                        'icon': 'fas fa-file-invoice-dollar',
                        'value': total_stats_count,
                        'amount': total_stats_amount,
                        'unit': _('份'),
                        'amount_unit': amount_unit,
                        'currency_symbol': currency_symbol,
                        'color': 'primary',
                        'clickable': True,
                        'click_params': {},
                        'data_key': 'total'
                    },
                    {
                        'id': 'approved',
                        'title': _('已批准'),
                        'icon': 'fas fa-check-circle',
                        'value': approved_count,
                        'amount': approved_amount,
                        'unit': _('份'),
                        'amount_unit': amount_unit,
                        'currency_symbol': currency_symbol,
                        'color': 'success',
                        'clickable': True,
                        'click_params': {'approval_status': 'approved'},
                        'data_key': 'approved'
                    },
                    {
                        'id': 'pending',
                        'title': _('待审批'),
                        'icon': 'fas fa-clock',
                        'value': pending_count,
                        'amount': pending_amount,
                        'unit': _('份'),
                        'amount_unit': amount_unit,
                        'currency_symbol': currency_symbol,
                        'color': 'warning',
                        'clickable': True,
                        'click_params': {'approval_status': 'pending'},
                        'data_key': 'pending'
                    },
                    {
                        'id': 'draft',
                        'title': _('草稿'),
                        'icon': 'fas fa-edit',
                        'value': draft_count,
                        'amount': draft_amount,
                        'unit': _('份'),
                        'amount_unit': amount_unit,
                        'currency_symbol': currency_symbol,
                        'color': 'secondary',
                        'clickable': True,
                        'click_params': {'approval_status': 'draft'},
                        'data_key': 'draft'
                    }
                ]
            },
            
            # 筛选配置
            'filter': filter_config,
            
            # 表格配置
            'table': {
                'ajax_target': 'quotationTableBody',
                'title': _('报价单列表'),
                'icon': 'fas fa-table',
                'fixed_height_scroll': True,     # 启用固定高度滚动（蓝色滚动条）
                'enhanced_striping': True,       # 启用增强斑马纹效果
                'table_name': None,              # 禁用动态映射，使用列配置中的label
                'columns': [
                    {
                        'key': 'owner',
                        'field': 'owner_id',
                        'label': _('负责人'),
                        'type': 'text',
                        'width': '100px',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'quotation_number',
                        'field': 'quotation_number',
                        'label': _(mapping_manager.get_field_display_name('quotation', 'quotation_number')),
                        'type': 'link',
                        'url_template': '/quotation/{id}/detail',
                        'width': '180px',
                        'min_width': '160px',
                        'render': 'render_quotation_number',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'project_name',
                        'field': 'project_id',
                        'label': _(mapping_manager.get_field_display_name('project', 'project_name')),
                        'type': 'text',
                        'width': '240px',
                        'min_width': '200px',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'amount',
                        'field': 'total_amount',
                        'label': _(mapping_manager.get_field_display_name('common', 'total_amount')),
                        'type': 'number',
                        'format': 'currency',
                        'align': 'end',
                        'width': '120px',
                        'sort_type': 'currency'
                    },
                    {
                        'key': 'project_stage',
                        'field': 'project_stage',
                        'label': _('报价阶段'),
                        'type': 'text',
                        'width': '100px',
                        'render': 'render_project_stage',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'project_type',
                        'field': 'project_type',
                        'label': _(mapping_manager.get_field_display_name('project', 'project_type')),
                        'type': 'text',
                        'width': '100px',
                        'render': 'render_project_type',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'updated_at',
                        'field': 'updated_at',
                        'label': _(mapping_manager.get_field_display_name('common', 'updated_at')),
                        'type': 'date',
                        'format': '%Y-%m-%d',
                        'width': '120px',
                        'sort_type': 'date'
                    },
                    {
                        'key': 'created_at',
                        'field': 'created_at',
                        'label': _(mapping_manager.get_field_display_name('common', 'created_at')),
                        'type': 'date',
                        'format': '%Y-%m-%d',
                        'width': '120px',
                        'sort_type': 'date'
                    }
                ]
            },
            
            # 智能移动端卡片配置
            'smart_mobile_card': {
                'module': 'quotation',
                'title_field': {'field': 'quotation_number', 'renderer': 'render_quotation_number'},
                'link_url': '/quotation/{id}/detail',
                'conditional_approval_badge': True,  # 启用条件审核通过徽章
                'badges': [
                    {'field': 'project_stage', 'renderer': 'project_stage'},
                    {'field': 'project_type', 'renderer': 'project_type'}
                ],
                'details': [
                    {'field': 'owner', 'label': '拥有人', 'renderer': 'owner'},
                    {'field': 'project_name', 'label': '关联项目'},
                    {'field': 'amount', 'label': '总价', 'format': 'currency'},
                    {'field': 'created_at', 'label': '创建时间', 'format': 'date'},
                    {'field': 'updated_at', 'label': '更新时间', 'format': 'date'}
                ]
            }
        }
        
        # 获取默认货币（用于模态框）
        default_currency = Config.DEFAULT_CURRENCY

        return render_template('quotation/tw_list.html',
                              quotations=quotations,
                              sort_field=sort_field,
                              sort_order=sort_order,
                              project_type=project_type_filter,
                              project_type_options=project_type_options,
                              project_stage_options=project_stage_options,
                              project_search=project_search,
                              offset=offset,
                              limit=limit,
                              has_more=has_more,
                              total_count=total_count,
                              available_users=available_users,
                              owner_filter=owner_filter,
                              project_type_filter=project_type_filter,
                              project_stage_filter=project_stage_filter,
                              filter_config=filter_config,
                              list_config=list_config,
                              currency_options=get_available_quotation_currencies(),
                              default_currency=default_currency)
                              
    except Exception as e:
        logger.error(f"加载报价单列表时出错: {str(e)}", exc_info=True)

        # 尝试回滚数据库事务
        try:
            db.session.rollback()
            logger.info("数据库事务已回滚")
        except Exception as rollback_error:
            logger.error(f"数据库事务回滚失败: {str(rollback_error)}")

        # 获取错误处理器需要的默认配置变量
        from app.utils.i18n import get_current_language, get_currency_symbol
        current_lang = get_current_language()
        # 使用系统货币配置的金额单位
        amount_unit = Config.AMOUNT_UNIT
        default_currency = Config.DEFAULT_CURRENCY
        currency_symbol = get_currency_symbol(default_currency)

        # 创建错误时的默认配置
        error_filter_config = {
            'action_url': url_for('quotation.list_quotations'),
            'form_id': 'quotationFilterForm',
            'reset_url': url_for('quotation.list_quotations'),
            'search_field': {
                'name': 'search',
                'label': _('搜索'),
                'placeholder': _('报价单编号或项目名称'),
                'value': '',
                'col_width': 4
            },
            'filter_fields': [],
            'search_button_text': _('搜索'),
            'reset_button_text': _('重置')
        }
        
        error_list_config = {
            'module_name': 'quotation',
            'title': _('报价单列表'),
            'ajax_mode': True,
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': _('全部报价单'),
                        'icon': 'fas fa-file-invoice-dollar',
                        'value': 0,
                        'amount': 0,
                        'unit': _('份'),
                        'amount_unit': amount_unit,
                        'currency_symbol': currency_symbol,
                        'color': 'primary',
                        'clickable': False,
                        'data_key': 'total'
                    }
                ]
            },
            'filter': error_filter_config,
            'table': {
                'ajax_target': 'quotationTableBody',
                'title': _('报价单列表'),
                'icon': 'fas fa-table',
                'columns': [
                    {'key': 'quotation_number', 'label': _('报价单编号'), 'type': 'text'},
                    {'key': 'owner', 'label': _('拥有人'), 'type': 'text'},
                    {'key': 'project_name', 'label': _('关联项目'), 'type': 'text'},
                    {'key': 'amount', 'label': _('总价'), 'type': 'number'},
                    {'key': 'project_stage', 'label': _('报价阶段'), 'type': 'text'},
                    {'key': 'project_type', 'label': _('类型'), 'type': 'text'},
                    {'key': 'updated_at', 'label': _('更新时间'), 'type': 'date'},
                    {'key': 'created_at', 'label': _('创建时间'), 'type': 'date'}
                ]
            }
        }
        
        flash(_('加载报价单失败：%s') % str(e), 'danger')
        return render_template('quotation/tw_list.html',
                              quotations=[],
                              sort_field='created_at',
                              sort_order='desc',
                              project_type='',
                              project_type_options=[],
                              project_stage_options=[],
                              available_users=[],
                              project_search='',
                              offset=0,
                              limit=20,
                              has_more=False,
                              total_count=0,
                              owner_filter='',
                              project_type_filter='',
                              project_stage_filter='',
                              filter_config=error_filter_config,
                              list_config=error_list_config,
                              currency_options=get_available_quotation_currencies(),
                              default_currency=default_currency)

@quotation.route('/at_new', methods=['GET'])
@login_required
@permission_required('quotation', 'create')
def at_new_quotation():
    """AT 风格新建报价 — 渲染空白详情页,首次保存时调 /quotation/create 落库。

    支持 ?project_id=X — 从项目详情页"新建报价"过来时预填项目关联,模板顶部
    渲染"返回 项目XX"链接,保存创建后跳回项目详情。
    """
    from types import SimpleNamespace
    from app.utils.dictionary_helpers import get_available_quotation_currencies
    from app.models.project import Project

    # 来源项目预填
    src_project_id = request.args.get('project_id', type=int)
    src_customer_arg = request.args.get('customer_id', type=int)  # 从客户详情新建报价
    src_project = None
    src_currency = Config.DEFAULT_CURRENCY   # 随环境(ovs=USD / sp8d=CNY),不再写死 CNY
    src_customer_id = None
    src_customer = None
    if src_project_id:
        src_project = Project.query.filter_by(id=src_project_id, is_deleted=False).first()
        if src_project and not can_view_project(current_user, src_project):
            src_project = None  # 无权访问的项目静默忽略
        if src_project:
            # Project 没"项目本币"字段,quotation_currency 仅是"最新一张报价单货币"的缓存,
            # 由报价保存事件回填。新项目还没有任何报价单时该字段是列硬编码默认 'CNY',
            # 不代表用户选择,不能继承(否则 SG/OVS 上新项目建报价会误默认成 CNY)。
            # 因此仅当项目"已有报价单"时才继承其货币,否则一律走环境默认(ovs=USD / sp8d=CNY)。
            has_existing_quotation = Quotation.query.filter_by(
                project_id=src_project.id
            ).first() is not None
            if has_existing_quotation:
                src_currency = (getattr(src_project, 'quotation_currency', None) or Config.DEFAULT_CURRENCY)
            # 预填客户:取第一个关联客户
            from app.models.project_customer_association import ProjectCustomerAssociation
            from app.models.customer import Company
            first_assoc = ProjectCustomerAssociation.query.filter_by(
                project_id=src_project.id
            ).first()
            if first_assoc:
                src_customer_id = first_assoc.company_id
                src_customer = Company.query.get(src_customer_id)
    # 客户详情来源(无 project_id)— 只预填客户
    elif src_customer_arg:
        from app.models.customer import Company
        from app.utils.access_control import can_view_company
        _c = Company.query.filter_by(id=src_customer_arg, is_deleted=False).first()
        if _c and can_view_company(current_user, _c):
            src_customer = _c
            src_customer_id = _c.id

    # 空 stub:让 at_view 模板里所有 quotation.xxx 调用不报错
    stub = SimpleNamespace(
        id=0, quotation_number=_('新建中'), amount=0, tax_rate=0,
        currency=src_currency, exchange_rate=1,
        project_id=(src_project.id if src_project else None),
        customer_id=src_customer_id,
        contact_id=None,
        project_stage=(src_project.current_stage if src_project else None),
        project_type=(src_project.project_type if src_project else None),
        notes=None, entity_id=None, extra_fields={}, is_locked=False,
        confirmation_badge_status='none', confirmation_badge_color=None,
        implant_total_amount=0, approval_history=[],
        created_at=None, updated_at=None, confirmed_at=None,
        owner=current_user, owner_id=current_user.id,
        project=src_project, customer=src_customer, contact=None, details=[],
    )
    available_currencies = get_available_quotation_currencies()
    from app.utils.dictionary_helpers import get_currency_symbol as _get_cur_sym
    return render_template(
        'quotation/at_view.html',
        quotation=stub,
        is_new=True,
        from_project=None,
        related={},
        actions=[],
        perms={'can_edit': True},
        currency_sym=_get_cur_sym(src_currency),
        grouped_details=[],
        details_payload=[],
        change_history=[],
        sm_is_owner=False,
        sm_is_assignee=False,
        sm_pending=[],
        sm_available_assignees=[],
        available_currencies=available_currencies,
    )


@quotation.route('/<int:id>/at_view')
@login_required
@permission_required('quotation', 'view')
def at_view_quotation(id):
    """AT 风格报价详情页"""
    from app.helpers.favorite_helpers import is_favorited as _fav_is, FAV_QUOTATION as _FAV_Q
    from app.utils.related_data import RelatedDataService
    from app.models.action import Action
    from app.models.product import Product
    from app import db as _db

    q = Quotation.query.get_or_404(id)
    if not can_view_quotation(current_user, q):
        from flask import abort
        abort(403)

    # ?from_project=X — 来自项目详情页"新建报价"的回链上下文,模板顶部据此渲染"返回 项目XX"
    from_project_id = request.args.get('from_project', type=int)
    from_project_obj = None
    if from_project_id:
        from app.models.project import Project
        from_project_obj = Project.query.filter_by(id=from_project_id, is_deleted=False).first()
        if from_project_obj and not can_view_project(current_user, from_project_obj):
            from_project_obj = None

    related = RelatedDataService.fetch_all('quotation', id, current_user, limit=5)
    actions = []
    if q.project_id:
        actions = get_viewable_data(Action, current_user,
            [Action.project_id == q.project_id]
        ).order_by(Action.created_at.desc()).limit(10).all()

    perms = {
        'can_edit': can_edit_data(q, current_user),
    }
    from app.utils.dictionary_helpers import get_currency_symbol as _qcur_sym
    currency_sym = _qcur_sym(q.currency or Config.DEFAULT_CURRENCY)

    # ── 按产品类别分组(主产品 only · 配置子产品跟随主产品)──
    # 排序按 product_categories.display_order(产品分类管理设定的顺序)
    # 用 product_categories FK 关系(更准),fallback 到旧的 string category 字段
    from app.models.product_code import ProductCategory
    main_details = [d for d in (q.details or []) if not d.parent_item_id]
    product_mns = list({d.product_mn for d in main_details if d.product_mn})
    category_map = {}
    if product_mns:
        rows = _db.session.query(
            Product.product_mn,
            ProductCategory.name,
            Product.category,
        ).outerjoin(ProductCategory, ProductCategory.id == Product.category_id
        ).filter(Product.product_mn.in_(product_mns)).all()
        # 优先用 category_obj.name,fallback 旧 string category
        category_map = {r[0]: (r[1] or r[2] or '') for r in rows}
    # 产品分类的全局显示顺序
    cat_order = {row[0]: row[1] for row in
                 _db.session.query(ProductCategory.name, ProductCategory.display_order).all()}

    _group_dict = {}
    for d in main_details:
        cat = (category_map.get(d.product_mn) or '').strip() or '自定义产品'
        _group_dict.setdefault(cat, []).append(d)
    grouped = []
    for cat, items in _group_dict.items():
        # 分组小计 = 主行 + 各主行的子产品行(子行独立计价,计入总额 — 全库 89/90 语义)
        subtotal = sum((d.total_price or 0) for d in items)
        subtotal += sum((c.total_price or 0) for d in items for c in (d.configurations or []))
        grouped.append({'label': cat, 'items': items, 'subtotal': subtotal, 'count': len(items)})
    # 排序:按 product_categories.display_order;自定义产品(无 order)排最后
    grouped.sort(key=lambda g: (
        1 if g['label'] == '自定义产品' else 0,
        cat_order.get(g['label'], 999),
        g['label'],
    ))

    # 详情完整字段 JSON(给前端 save 用 — 防止只 PATCH 局部字段导致后端校验失败清空数据)
    details_payload = []
    for d in (q.details or []):
        _is_temp = bool(d.product_mn and str(d.product_mn).startswith('TEMP_'))
        details_payload.append({
            'id': d.id,
            'product_name': d.product_name or '',
            'product_model': d.product_model or '',
            'product_desc': d.product_desc or '',
            'product_mn': d.product_mn or '',
            'brand': d.brand or '',
            'unit': d.unit or '套',
            'quantity': int(d.quantity or 0),
            'market_price': float(d.market_price or 0),
            'unit_price': float(d.unit_price or 0),
            # 自定义产品标识 — 后端 process_quotation_details 用此判断是否跳过 market_price<=0 校验
            'is_temp': _is_temp,
            'temp_product_id': (str(d.product_mn)[5:] if _is_temp else None),
            # 用 discount_rate(百分比 0-100)— 与后端 process_quotation_details 接口一致
            # discount 字段是 0-1 浮点,后端会按百分比再除 100,不能直接传 raw 值
            'discount_rate': float((d.discount or 1) * 100),
            'total_price': float(d.total_price or 0),
            'item_note': d.item_note or '',
            'row_type': getattr(d, 'row_type', None) or 'product',
            'section_label': getattr(d, 'section_label', None) or '',
            'parent_item_id': d.parent_item_id,
            'is_accessory': bool(getattr(d, 'is_accessory', False)),
            'config_type': getattr(d, 'config_type', None) or '',
            'config_base_quantity': getattr(d, 'config_base_quantity', None),
            'quantity_synced': bool(getattr(d, 'quantity_synced', True) if getattr(d, 'quantity_synced', None) is not None else True),
            'sort_order': getattr(d, 'sort_order', None),
            'currency': d.currency or (q.currency or 'CNY'),
        })

    # 变更历史 — 从 ChangeLog 表抓取;人员优先 real_name;时间 UTC→本地时区
    from app.models.change_log import ChangeLog
    from app.models import User
    from app.utils.filters import format_datetime_local
    # 值用 _() 字面量 → pybabel 可提取(原先 _(变量) 抓不到,导致 明细数量 等不翻译)
    _CH_FIELD_LABEL = {'amount': _('报价金额'), 'details_count': _('明细数量'), 'details': _('产品配置'),
                       'confirmation': _('技术确认')}
    _CH_OP_LABEL    = {'CREATE': _('创建'), 'UPDATE': _('修改'), 'DELETE': _('删除')}
    # 技术确认动作:new_value 状态码 → 可读(随 locale)
    _CH_CONFIRM_VAL = {'confirmed': _('技术确认通过'), 'reconfirm': _('需再次确认'),
                       'pending': _('提交技术确认'), 'none': _('撤销确认')}
    _logs = ChangeLog.get_record_history('quotation', 'quotations', q.id)
    _uids = {l.user_id for l in _logs if l.user_id}
    _user_real = {u.id: (u.real_name or u.username) for u in User.query.filter(User.id.in_(_uids)).all()} if _uids else {}
    change_history = []
    for h in _logs:
        display_name = _user_real.get(h.user_id) or h.user_name or _('系统')
        if h.field_name == 'confirmation':
            # 技术确认动作:直接用可读动作作标题,不显示 old→new 原始码
            _entry = {
                'op': h.operation_type,
                'title': _CH_CONFIRM_VAL.get(h.new_value, _('技术确认')),
                'time': format_datetime_local(h.created_at, '%Y-%m-%d %H:%M') if h.created_at else '',
                'user': display_name, 'old': None, 'new': None,
            }
        elif h.field_name == 'details':
            # 产品配置变更:old/new 是 product_signature 哈希,无意义 → 只显示动作
            _entry = {
                'op': h.operation_type,
                'title': _('修改了产品配置'),
                'time': format_datetime_local(h.created_at, '%Y-%m-%d %H:%M') if h.created_at else '',
                'user': display_name, 'old': None, 'new': None,
            }
        elif h.field_name == 'detail_deleted':
            # 再确认时删除的产品:old_value = "产品名 ×数量"
            _entry = {
                'op': 'DELETE',
                'title': _('删除产品') + '：' + (h.old_value or ''),
                'time': format_datetime_local(h.created_at, '%Y-%m-%d %H:%M') if h.created_at else '',
                'user': display_name, 'old': None, 'new': None,
            }
        else:
            label = _CH_FIELD_LABEL.get(h.field_name, h.field_name) if h.field_name else _CH_OP_LABEL.get(h.operation_type, h.operation_type)
            _entry = {
                'op':     h.operation_type,
                'title':  _(label) if label else _('变更'),
                'time':   format_datetime_local(h.created_at, '%Y-%m-%d %H:%M') if h.created_at else '',
                'user':   display_name,
                'old':    h.old_value,
                'new':    h.new_value,
            }
        change_history.append(_entry)

    # SM 确认上下文
    from app.models.quotation_confirmation_task import QuotationConfirmationTask
    sm_pending_tasks = QuotationConfirmationTask.query.filter_by(
        quotation_id=q.id, status='pending'
    ).all()
    sm_is_owner = (q.owner_id == current_user.id)
    sm_is_assignee = any(t.assignee_id == current_user.id for t in sm_pending_tasks)
    sm_pending = [{
        'id':            t.id,
        'assignee_id':   t.assignee_id,
        'assignee_name': (t.assignee.real_name or t.assignee.username) if t.assignee else '',
        'message':       t.message or '',
    } for t in sm_pending_tasks]
    # 可选被指派人列表(发起对话框用)— 仅 owner 时拉
    sm_available_assignees = []
    if sm_is_owner and not sm_pending_tasks:
        # 注意:User.is_active 是 property,DB 列为 _is_active(避免陷阱)
        # 仅方案经理(solution_manager)可作为确认人
        _u_rows = User.query.filter(
            User.role == 'solution_manager',
            User._is_active == True,
        ).order_by(User.real_name.asc(), User.username.asc()).all()
        sm_available_assignees = [{
            'id': u.id,
            'name': u.real_name or u.username,
            'role': u.role,
        } for u in _u_rows]

    # 标准审批 chip 状态 — 必须取自 ApprovalInstance,而非 quotation.approval_status
    # 因为 quotation.approval_status 是 SM 老机制字段(默认就是 'pending'),与标准审批无关
    # 注意:recall_approval 把 instance.status 设为 REJECTED,通过最后一条 record.action='recall' 区分
    from app.helpers.approval_helpers import get_object_approval_instance
    from app.models.approval import ApprovalRecord
    _q_ap_instance = get_object_approval_instance('quotation', q.id, include_rejected=True)
    if _q_ap_instance:
        _raw = _q_ap_instance.status.value if hasattr(_q_ap_instance.status, 'value') else str(_q_ap_instance.status)
        _at_ap_status = _raw if _raw in ('draft', 'pending', 'approved', 'rejected', 'recalled') else 'draft'
        # rejected 态需要进一步区分:最后一条 record action='recall' → 显示为 recalled
        if _at_ap_status == 'rejected':
            _last_rec = ApprovalRecord.query.filter_by(instance_id=_q_ap_instance.id) \
                .order_by(ApprovalRecord.timestamp.desc()).first()
            if _last_rec and _last_rec.action == 'recall':
                _at_ap_status = 'recalled'
    else:
        _at_ap_status = 'draft'

    # 本报价单「质量得分」= 出现过的推荐产品(citation_coefficient>0)系数之和(去重不看数量)
    from sqlalchemy import text as _text
    _qscore = db.session.execute(_text(
        "SELECT COALESCE(SUM(p.citation_coefficient),0) "
        "FROM (SELECT DISTINCT product_mn FROM quotation_details WHERE quotation_id=:qid) dp "
        "JOIN products p ON p.product_mn=dp.product_mn AND p.citation_coefficient>0"),
        {'qid': q.id}).scalar() or 0
    _qscore = round(float(_qscore), 1)
    from flask_babel import gettext as _gt
    _qrating = _gt('优秀') if _qscore >= 7 else (_gt('良好') if _qscore >= 5 else (_gt('及格') if _qscore >= 3 else _gt('待提升')))

    # 进行中批价单(草稿/待审批)— 用于「生成批价单 / 批价单」按钮
    from app.models.pricing_order import PricingOrder
    active_pricing_order = PricingOrder.query.filter(
        PricingOrder.quotation_id == q.id,
        PricingOrder.status.in_(['draft', 'pending'])
    ).order_by(PricingOrder.created_at.desc()).first()

    return render_template('quotation/at_view.html',
                           quotation=q,
                           active_pricing_order=active_pricing_order,
                           quality_score=_qscore,
                           quality_rating=_qrating,
                           is_new=False,
                           from_project=from_project_obj,
                           related=related,
                           actions=actions,
                           perms=perms,
                           currency_sym=currency_sym,
                           grouped_details=grouped,
                           details_payload=details_payload,
                           change_history=change_history,
                           sm_is_owner=sm_is_owner,
                           sm_is_assignee=sm_is_assignee,
                           sm_pending=sm_pending,
                           sm_available_assignees=sm_available_assignees,
                           at_ap_status=_at_ap_status,
                           is_favorited=_fav_is(current_user.id, _FAV_Q, q.id))


@quotation.route('/at_list')
@login_required
@permission_required('quotation', 'view')
def at_list_view():
    """AT 风格报价单列表"""
    from sqlalchemy import or_
    page = max(int(request.args.get('page', 1)), 1)
    per_page = 30
    tab = request.args.get('tab', 'all')
    search = request.args.get('search', '').strip()
    # 多选:同名多个 query 参数(状态维度已由 tab 表达,这里不再重复筛选)
    owner_values = [v for v in request.args.getlist('owner') if v.strip()]
    fav_only = request.args.get('fav') == '1'   # 「仅看关注」开关(与 tab 正交)

    base = get_viewable_data(Quotation, current_user)

    # ── 我关注的报价单(个人书签;只影响我自己)──
    from app.helpers.favorite_helpers import favorite_ids as _fav_ids, FAV_QUOTATION
    fav_ids = _fav_ids(current_user.id, FAV_QUOTATION)
    if fav_only:
        base = base.filter(Quotation.id.in_(fav_ids or [-1]))

    # ── 筛选选项(基于可见数据 → 含权限+归属);能看到他人数据才显示筛选 ──
    from app.utils.access_control import build_owner_filter_options
    _owner_ids = [r[0] for r in base.with_entities(Quotation.owner_id).distinct().all() if r[0]]
    show_filter = any(oid != current_user.id for oid in _owner_ids)
    owner_options = build_owner_filter_options(_owner_ids)

    # ── 应用筛选(多选 → IN)──
    _owner_ids_sel = [int(v) for v in owner_values if v.isdigit()]
    if _owner_ids_sel:
        base = base.filter(Quotation.owner_id.in_(_owner_ids_sel))

    # tab → confirmation_badge_status(待确认 tab 同时含已驳回,owner 可见驳回回流)
    TAB_BADGE_MAP = {
        'none':      ['none'],                 # 待审批
        'pending':   ['pending', 'rejected'],  # 待确认 / 已驳回
        'confirmed': ['confirmed'],            # 已成交
    }
    tab_counts = {'all': base.count()}
    for k, vs in TAB_BADGE_MAP.items():
        tab_counts[k] = base.filter(Quotation.confirmation_badge_status.in_(vs)).count()

    q = base
    if tab in TAB_BADGE_MAP:
        q = q.filter(Quotation.confirmation_badge_status.in_(TAB_BADGE_MAP[tab]))

    if search:
        like = f'%{search}%'
        q = q.filter(Quotation.quotation_number.ilike(like))

    # ── 点击列排序(日期列 + 金额列,均为模型真实 DB Column)──
    from sqlalchemy import nullslast
    _SORT_COLS = {
        'created_at': Quotation.created_at,
        'updated_at': Quotation.updated_at,
        'amount': Quotation.amount,
    }
    sort_field, sort_order = extract_sort_params(
        request.args, default_sort='updated_at', default_order='desc',
        allowed_fields=list(_SORT_COLS.keys()))
    _col = _SORT_COLS[sort_field]
    _ordered = _col.desc() if sort_order == 'desc' else _col.asc()

    pagination = q.order_by(nullslast(_ordered), Quotation.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False,
    )

    from app.helpers.quality_score import quotation_quality_scores
    quality_scores = quotation_quality_scores([q.id for q in pagination.items])

    return render_template('quotation/at_list.html',
                           quotations=pagination.items,
                           quality_scores=quality_scores,
                           pagination=pagination,
                           tab_counts=tab_counts,
                           current_tab=tab,
                           search=search,
                           show_filter=show_filter,
                           owner_options=owner_options,
                           owner_values=owner_values,
                           sort_field=sort_field,
                           sort_order=sort_order,
                           fav_ids=fav_ids,
                           fav_only=fav_only,
                           list_qs={k: v for k, v in {'search': search,
                                    'owner': owner_values,
                                    'fav': ('1' if fav_only else '')}.items() if v})


@quotation.route('/api/quotations/filter', methods=['GET'])
@login_required
@permission_required('quotation', 'view')
def quotations_list_ajax():
    """报价单列表AJAX筛选API - 使用通用工具"""
    try:
        # ============================================================
        # 1. 使用通用工具提取参数
        # ============================================================
        filters = extract_filter_params(request.args, QUOTATION_FILTER_CONFIG)
        offset, limit = extract_pagination_params(request.args, default_limit=30, max_limit=100)

        # 提取变量（search 从 request.args 获取，因为需要跨表搜索）
        search = request.args.get('search', '').strip()
        owner_filter = filters.get('owner_filter', '')
        project_stage_filter = filters.get('project_stage_filter', '')
        project_type_filter = request.args.get('project_type_filter', '')

        # 排序参数
        sort_field = request.args.get('sort_field', '')
        sort_direction = request.args.get('sort_direction', 'desc')

        # ============================================================
        # 2. 构建查询
        # ============================================================
        query = get_viewable_data(Quotation, current_user).options(
            joinedload(Quotation.project),
            joinedload(Quotation.owner)
        )

        # ============================================================
        # 3. 应用筛选（使用通用工具 + 手动处理特殊情况）
        # ============================================================
        query = apply_filters_to_query(query, Quotation, filters, QUOTATION_FILTER_CONFIG)

        # 搜索（使用子查询避免与 content_filter 的 Project JOIN 冲突）
        if search:
            matching_project_ids = db.session.query(Project.id).filter(
                Project.project_name.ilike(f'%{search}%')
            )
            query = query.filter(
                or_(
                    Quotation.quotation_number.ilike(f'%{search}%'),
                    Quotation.project_id.in_(matching_project_ids)
                )
            )

        # 项目类型筛选（使用子查询避免 JOIN 冲突）
        if project_type_filter:
            matching_project_ids = db.session.query(Project.id).filter(
                Project.project_type == project_type_filter
            )
            query = query.filter(Quotation.project_id.in_(matching_project_ids))

        # ============================================================
        # 4. 应用排序
        # ============================================================
        from app.utils.sorting_service import SortingService, create_user_relation_config, create_project_relation_config, create_basic_field_mappings

        sorting_config = {
            'field_mappings': create_basic_field_mappings(Quotation, [
                'quotation_number', 'amount', 'project_stage', 'project_type',
                'approval_status', 'created_at', 'updated_at'
            ]),
            'relation_mappings': {
                'owner_id': create_user_relation_config(Quotation.owner_id),
                'project_id': create_project_relation_config(Quotation.project_id)
            },
            'default_sort': {'field': 'updated_at', 'direction': 'desc'}
        }

        sorting_service = SortingService(Quotation, sorting_config)
        query = sorting_service.apply_sort(query, sort_field, sort_direction)

        # ============================================================
        # 5. 分页
        # ============================================================
        total_count = query.count()
        quotations = query.offset(offset).limit(limit).all()

        # 为报价单添加项目名称（用于移动端显示）
        for q in quotations:
            if hasattr(q, 'project') and q.project:
                q.project_name = getattr(q.project, 'project_name', '未知项目')
            else:
                q.project_name = '未关联项目'
            
        
        # 直接进行响应式渲染
        try:
            from flask import render_template_string
            from app.utils.mobile_helpers import is_mobile_request
            
            is_mobile = is_mobile_request()
            current_app.logger.info(f"移动端检测结果: {is_mobile}, mobile参数: {request.args.get('mobile')}")
            
            # 临时调试：在HTML中添加调试信息
            debug_info = f"<!-- DEBUG: is_mobile={is_mobile}, mobile_param={request.args.get('mobile')} -->"
            current_app.logger.info(f"🔍 AJAX调试: URL={request.url}, is_mobile={is_mobile}, User-Agent={request.headers.get('User-Agent', 'None')}")

            if request.args.get('ajax', '0') == '1':
                # Tailwind 表格行模板
                html = render_template('quotation/tw_list_rows.html', quotations=quotations)
                current_app.logger.info("Tailwind 表格行渲染成功")
            elif is_mobile:
                # 移动端：使用智能卡片配置
                current_app.logger.info("开始配置智能卡片")
                smart_mobile_card = {
                    'module': 'quotation',
                    'title_field': {'field': 'quotation_number', 'renderer': 'render_quotation_number'},
                    'link_url': '/quotation/{id}/detail',
                    'conditional_approval_badge': True,  # 启用条件审核通过徽章
                    'badges': [
                        {'field': 'project_stage', 'renderer': 'project_stage'},
                        {'field': 'project_type', 'renderer': 'project_type'}
                    ],
                    'details': [
                        {'field': 'project_name', 'label': '关联项目', 'renderer': 'project_link'},
                        {'field': 'owner', 'label': '拥有人', 'renderer': 'owner'},
                        {'field': 'amount', 'label': '总价', 'format': 'currency'},
                        {'field': 'created_at', 'label': '创建时间', 'format': 'date'},
                        {'field': 'updated_at', 'label': '更新时间', 'format': 'date'}
                    ]
                }
                current_app.logger.info(f"智能卡片配置: {smart_mobile_card}")
                
                try:
                    html = render_template_string('''
                        {% from 'macros/ui_helpers.html' import render_smart_mobile_cards %}
                        {{ render_smart_mobile_cards(quotations, card_config) }}
                    ''', quotations=quotations, card_config=smart_mobile_card)
                    current_app.logger.info(f"渲染移动端智能卡片: {len(quotations)}条记录")
                    current_app.logger.info(f"生成的HTML长度: {len(html)}")
                    html = debug_info + "<!-- MOBILE RENDER SUCCESS -->" + html
                except Exception as render_error:
                    current_app.logger.error(f"智能卡片渲染失败: {render_error}")
                    import traceback
                    current_app.logger.error(f"渲染异常堆栈: {traceback.format_exc()}")
                    # 回退到 Tailwind 模板
                    html = debug_info + f"<!-- MOBILE RENDER FAILED: {str(render_error)} -->" + render_template('quotation/tw_list_rows.html', quotations=quotations)
            else:
                # 桌面端：使用 Tailwind 表格
                html = debug_info + "<!-- DESKTOP RENDER -->" + render_template('quotation/tw_list_rows.html', quotations=quotations)
            current_app.logger.info("统一响应式渲染成功")
        except Exception as e:
            current_app.logger.error(f"统一响应式渲染失败: {e}")
            import traceback
            current_app.logger.error(f"完整异常堆栈: {traceback.format_exc()}")
            # 回退到 Tailwind 模板渲染
            try:
                html = render_template('quotation/tw_list_rows.html', quotations=quotations)
                current_app.logger.info("回退到 Tailwind 模板渲染成功")
            except Exception as fallback_error:
                current_app.logger.error(f"回退渲染也失败: {fallback_error}")
                html = f'<tr><td colspan="9" class="text-center text-muted">渲染失败: {str(e)}</td></tr>'
        
        # 计算统计数据 - 应用相同的筛选条件
        try:
            stats_query = get_viewable_data(Quotation, current_user)
            stats_joined = False
            
            # 应用相同的筛选条件到统计查询
            if search:
                stats_query = stats_query.join(Project, Quotation.project_id == Project.id)
                stats_joined = True
                stats_query = stats_query.filter(
                    or_(
                        Quotation.quotation_number.ilike(f'%{search}%'),
                        Project.project_name.ilike(f'%{search}%')
                    )
                )
            
            if owner_filter:
                stats_query = stats_query.filter(Quotation.owner_id == owner_filter)
            
            if project_type_filter:
                if not stats_joined:
                    stats_query = stats_query.join(Project, Quotation.project_id == Project.id)
                    stats_joined = True
                stats_query = stats_query.filter(Project.project_type == project_type_filter)
            
            if project_stage_filter:
                if not stats_joined:
                    stats_query = stats_query.join(Project, Quotation.project_id == Project.id)
                    stats_joined = True
                stats_query = stats_query.filter(Project.current_stage == project_stage_filter)
            
            # 使用统一的跨货币聚合服务（性能接近 SUM，只做 N 次 Python 层换算）
            from app.services.multi_currency_aggregation import MultiCurrencyAggregationService

            approved_statuses = [
                'discover_approved', 'embed_approved', 'pre_tender_approved',
                'tendering_approved', 'awarded_approved', 'quoted_approved', 'signed_approved'
            ]

            amount_stats = MultiCurrencyAggregationService.sum_converted_with_conditions(
                stats_query,
                Quotation.amount,
                Quotation.currency,
                {
                    'total': None,
                    'approved': Quotation.approval_status.in_(approved_statuses),
                    'pending': Quotation.approval_status == 'pending',
                    'rejected': Quotation.approval_status == 'rejected',
                }
            )

            total_stats_count = stats_query.count()
            total_stats_amount = round(amount_stats['total'] / 10000, 2)

            approved_count = stats_query.filter(Quotation.approval_status.in_(approved_statuses)).count()
            approved_amount = round(amount_stats['approved'] / 10000, 2)

            pending_count = stats_query.filter(Quotation.approval_status == 'pending').count()
            pending_amount = round(amount_stats['pending'] / 10000, 2)

            rejected_count = stats_query.filter(Quotation.approval_status == 'rejected').count()
            rejected_amount = round(amount_stats['rejected'] / 10000, 2)
            
            current_app.logger.info(f"筛选后统计数据: 总数={total_stats_count}, 总金额={total_stats_amount}万元")
            
        except Exception as e:
            current_app.logger.error(f"统计数据计算失败: {e}")
            # 使用默认值
            total_stats_count = total_count
            total_stats_amount = 0
            approved_count = approved_amount = 0
            pending_count = pending_amount = 0
            rejected_count = rejected_amount = 0
        
        # 获取货币配置信息（复用项目管理的成功逻辑）
        from app.utils.i18n import get_current_language, get_currency_symbol
        current_lang = get_current_language()
        default_currency = Config.DEFAULT_CURRENCY
        currency_symbol = get_currency_symbol(default_currency)

        # 调试输出 API 货币信息
        print(f"[调试] 报价单API返回 - 当前语言: {current_lang}")
        print(f"[调试] 报价单API返回 - 默认货币: {default_currency}")
        print(f"[调试] 报价单API返回 - 货币符号: {currency_symbol}")

        return jsonify({
            'success': True,
            'html': html,
            'total_count': total_count,
            'loaded_count': offset + len(quotations),
            'has_more': (offset + len(quotations)) < total_count,
            'statistics': {
                'total': total_stats_count,
                'total_amount': total_stats_amount,
                'approved': approved_count,
                'approved_amount': approved_amount,
                'pending': pending_count,
                'pending_amount': pending_amount,
                'rejected': rejected_count,
                'rejected_amount': rejected_amount
            },
            'currency_symbol': currency_symbol,  # 添加货币符号配置
            'currency': default_currency,  # 添加货币类型配置
            'language': current_lang  # 添加语言配置
        })
        
    except Exception as e:
        current_app.logger.error(f"报价单AJAX筛选失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '加载失败: %s' % str(e),
            'html': '<tr><td colspan="8" class="text-center text-muted">加载失败，请刷新重试</td></tr>',
            'total_count': 0,
            'loaded_count': 0,
            'has_more': False,
            'statistics': {
                'total': 0,
                'total_amount': 0,
                'approved': 0,
                'approved_amount': 0,
                'pending': 0,
                'pending_amount': 0,
                'rejected': 0,
                'rejected_amount': 0
            }
        }), 500


# ============================================================
# 公共函数：处理报价单产品明细（创建和编辑共用）
# ============================================================
def _render_excel_editor(quotation_id=None, project_id_preset=None):
    """渲染全屏 Excel-like 报价单编辑器（Beta 共存模式入口）。

    quotation_id 提供时为编辑模式，否则为新建模式。
    project_id_preset 用于新建模式预填项目（来自项目页跳转）。
    """
    import json
    from app.models.product import Product as _Product

    quotation = None
    quotation_details_json = '[]'
    can_edit_this_quotation = True

    if quotation_id:
        quotation = Quotation.query.get_or_404(quotation_id)
        if not can_edit_data(quotation, current_user):
            flash(_('您没有权限编辑此报价单'), 'danger')
            return redirect(url_for('quotation.at_view_quotation', id=quotation_id))
        if quotation.is_locked:
            flash(_('报价单已被锁定，无法编辑'), 'warning')
            return redirect(url_for('quotation.at_view_quotation', id=quotation_id))

        # 准备产品明细 JSON（与 view_quotation 中逻辑保持一致）
        non_temp_mns = list({
            str(getattr(d, 'product_mn', '') or '')
            for d in quotation.details
            if getattr(d, 'product_mn', None) and not str(d.product_mn).startswith('TEMP_')
        })
        product_mn_to_id = {}
        if non_temp_mns:
            _products = _Product.query.filter(_Product.product_mn.in_(non_temp_mns)).all()
            product_mn_to_id = {p.product_mn: p.id for p in _products}

        details_for_edit = []
        for detail in quotation.details:
            try:
                product_mn = str(getattr(detail, 'product_mn', '') or '')
                is_temp_product = product_mn.startswith('TEMP_')
                details_for_edit.append({
                    'item_id': detail.id,
                    'row_type': str(getattr(detail, 'row_type', 'product') or 'product'),
                    'section_label': str(getattr(detail, 'section_label', '') or ''),
                    'sort_order': getattr(detail, 'sort_order', None),
                    'product_id': product_mn_to_id.get(product_mn),
                    'product_name': str(detail.product_name or ''),
                    'product_model': str(detail.product_model or ''),
                    'product_desc': str(detail.product_desc or ''),
                    'brand': str(detail.brand or ''),
                    'unit': str(detail.unit or '个'),
                    'market_price': float(detail.market_price or 0),
                    'discount_rate': float(detail.discount * 100 if detail.discount is not None else 100.0),
                    'unit_price': float(detail.unit_price or 0),
                    'quantity': int(detail.quantity or 1),
                    'subtotal': float(detail.total_price or 0),
                    'product_mn': product_mn,
                    'is_temp': is_temp_product,
                    'is_accessory': bool(getattr(detail, 'is_accessory', False)),
                    'parent_item_id': getattr(detail, 'parent_item_id', None),
                    'config_type': str(getattr(detail, 'config_type', '') or ''),
                    'config_base_quantity': getattr(detail, 'config_base_quantity', None),
                    'quantity_synced': bool(getattr(detail, 'quantity_synced', True) if getattr(detail, 'quantity_synced', None) is not None else True),
                    'item_note': str(getattr(detail, 'item_note', '') or ''),
                })
            except Exception as e:
                current_app.logger.warning(f"明细处理出错: {e}")
        quotation_details_json = json.dumps(details_for_edit)

    # 预填项目信息（新建模式）
    preset_project = None
    if project_id_preset and not quotation_id:
        try:
            preset_project = Project.query.get(int(project_id_preset))
        except (ValueError, TypeError):
            preset_project = None

    # 公司主体列表：按部署地区过滤
    # CN NAS (sp8d) 只显示 region=CN；SG NAS (ovs) 显示 SG + MY（同一 NAS 服务两国）
    from app.models.company_entity import CompanyEntity
    db_type = (current_app.config.get('PMA_DB_TYPE') or os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE') or '').lower()
    if db_type == 'sp8d':
        allowed_regions = ['CN']
    elif db_type == 'ovs':
        allowed_regions = ['SG', 'MY']
    else:
        allowed_regions = ['CN', 'SG', 'MY']  # 本地无 PMA_DB_TYPE 时显示全部，方便开发
    entities = CompanyEntity.query.filter(CompanyEntity.region.in_(allowed_regions)) \
                                  .order_by(CompanyEntity.sort_order, CompanyEntity.id).all()
    entities_json = json.dumps([e.to_dict() for e in entities])
    # 默认 entity：编辑时用 quotation.entity_id（即使跨区域也保留，避免数据丢失）；新建时取列表第一个
    default_entity_id = None
    if quotation and quotation.entity_id:
        default_entity_id = quotation.entity_id
    elif entities:
        default_entity_id = next((e.id for e in entities if e.is_default), entities[0].id)

    extra_fields = (getattr(quotation, 'extra_fields', None) if quotation else None) or {}
    today_str = datetime.now().strftime('%Y%m%d')
    return render_template(
        'quotation/tw_quotation_edit.html',
        today_str=today_str,
        quotation=quotation,
        preset_project=preset_project,
        quotation_details_json=quotation_details_json,
        currency_options=get_available_quotation_currencies(),
        default_currency=(quotation.currency if quotation else Config.DEFAULT_CURRENCY),
        user_letterhead=getattr(current_user, 'quotation_letterhead', None) or {},
        user_signature=getattr(current_user, 'quotation_signature', None) or {},
        can_edit_this_quotation=can_edit_this_quotation,
        entities_json=entities_json,
        default_entity_id=default_entity_id,
        extra_fields_json=json.dumps(extra_fields),
    )


def process_quotation_details(quotation_id, details, currency=Config.DEFAULT_CURRENCY):
    """
    处理报价单产品明细，包括父子关系建立

    Args:
        quotation_id: 报价单ID
        details: 产品明细列表
        currency: 货币类型

    Returns:
        tuple: (created_details, errors) - 创建的明细列表和错误信息
    """
    created_details = []
    errors = []

    # 父子关系处理：用于两阶段保存
    detail_id_map = {}  # row_id -> detail 对象映射
    pending_configs = []  # 待处理的配置产品

    for index, detail in enumerate(details):
        try:
            if not isinstance(detail, dict):
                errors.append(f"第 {index+1} 行数据格式错误")
                continue

            # 标注行（row_type='section'）：单独处理，不走产品验证逻辑
            if detail.get('row_type') == 'section':
                section_detail = QuotationDetail(
                    quotation_id=quotation_id,
                    product_name='',
                    row_type='section',
                    section_label=str(detail.get('section_label', '') or ''),
                    sort_order=index,
                    market_price=0,
                    unit_price=0,
                    total_price=0,
                    quantity=0,
                    discount=0,
                    currency=currency,
                )
                db.session.add(section_detail)
                created_details.append(section_detail)
                continue

            product_name = detail.get('product_name', '').strip()
            if not product_name:
                errors.append(f"第 {index+1} 行产品名称不能为空")
                continue

            # 解析数值字段
            try:
                market_price = float(detail.get('market_price', 0))
            except (ValueError, TypeError):
                market_price = 0

            # 校验：market_price 必须 > 0（兜底前端校验，防止绕过）
            # 临时产品允许 market_price = 0（例如价格面议场景）
            is_temp_product = detail.get('is_temp') or detail.get('temp_product_id') or detail.get('status') == 'temp'
            if not is_temp_product and market_price <= 0:
                errors.append(f"第 {index+1} 行产品 \"{product_name}\" 未填写市场单价")
                continue

            try:
                discount = float(detail.get('discount_rate', detail.get('discount', 100))) / 100
                if discount < 0:
                    discount = 0
            except (ValueError, TypeError):
                discount = 1.0

            try:
                quantity = int(detail.get('quantity', 1))
                if quantity <= 0:
                    quantity = 1
            except (ValueError, TypeError):
                quantity = 1

            try:
                unit_price = float(detail.get('unit_price', 0))
                if unit_price < 0:
                    unit_price = 0
            except (ValueError, TypeError):
                unit_price = 0

            # 面价是基准、单价是事实:折扣一律由二者反算,杜绝「面价×折扣≠单价」的矛盾数据
            # (这种矛盾会在生成批价单时把报价单价冲成面价 —— 见 price_consistency 模块注释)
            discount = normalize_discount(market_price, unit_price, discount)

            try:
                total_price = float(detail.get('total_price', 0))
                if total_price < 0:
                    total_price = 0
            except (ValueError, TypeError):
                total_price = unit_price * quantity

            # 处理临时产品标识
            product_mn = detail.get('product_mn', '')
            if detail.get('is_temp') or detail.get('temp_product_id') or detail.get('status') == 'temp':
                if not product_mn.startswith('TEMP_'):
                    product_mn = f"TEMP_{detail.get('temp_product_id', 'MANUAL')}"

            # 处理动态规格配置
            configured_specs = detail.get('configured_specs')
            configured_mn = detail.get('configured_mn')
            price_adjustment_total = 0
            pending_product_creation = False

            if configured_specs:
                try:
                    price_adjustment_total = int(detail.get('price_adjustment_total', 0))
                except (ValueError, TypeError):
                    price_adjustment_total = 0
                pending_product_creation = detail.get('pending_product_creation', False)

            # 创建明细对象
            new_detail = QuotationDetail(
                quotation_id=quotation_id,
                product_name=product_name,
                product_model=detail.get('product_model', ''),
                product_desc=detail.get('product_desc', ''),
                brand=detail.get('brand', ''),
                unit=detail.get('unit', ''),
                quantity=quantity,
                discount=discount,
                market_price=market_price,
                unit_price=unit_price,
                total_price=total_price,
                product_mn=product_mn,
                currency=currency,
                configured_specs=configured_specs,
                configured_mn=configured_mn,
                price_adjustment_total=price_adjustment_total,
                pending_product_creation=pending_product_creation,
                item_note=detail.get('item_note', '') or '',
                row_type='product',
                sort_order=index,
            )

            # 计算植入小计
            new_detail.calculate_implant_subtotal_only()

            # 处理配置产品相关字段（父子关系）
            is_configuration = detail.get('is_configuration', False)
            if is_configuration == 'true' or is_configuration is True:
                new_detail.is_accessory = True
                new_detail.is_editable = False
                new_detail.config_type = detail.get('config_type')
                new_detail.config_base_quantity = int(detail.get('config_base_quantity', 1) or 1)
                new_detail.quantity_synced = detail.get('quantity_synced', True)

                pending_configs.append({
                    'detail': new_detail,
                    'parent_row_id': detail.get('parent_row_id')
                })
                current_app.logger.debug(f'第 {index+1} 行是配置产品: parent_row_id={detail.get("parent_row_id")}')
            else:
                # 主产品：记录 row_id 映射
                row_id = detail.get('row_id')
                if row_id:
                    detail_id_map[row_id] = new_detail

            db.session.add(new_detail)
            created_details.append(new_detail)
            current_app.logger.debug(f'创建第 {index+1} 行明细项: {product_name}')

        except Exception as e:
            errors.append(f"处理第 {index+1} 行明细时出错: {str(e)}")
            current_app.logger.error(f"处理第 {index+1} 行明细时出错: {str(e)}")

    # 第二阶段：建立配置产品的父子关系（需要先 flush 获取 ID）
    if pending_configs:
        current_app.logger.info(f"开始建立 {len(pending_configs)} 个配置产品的父子关系")
        db.session.flush()  # Flush 以获取所有 detail 的 ID

        for config_info in pending_configs:
            parent_detail = detail_id_map.get(config_info['parent_row_id'])
            if parent_detail:
                config_info['detail'].parent_item_id = parent_detail.id
                current_app.logger.debug(f"配置产品 {config_info['detail'].product_name} 关联到父产品 {parent_detail.product_name} (ID={parent_detail.id})")
            else:
                # 找不到父产品，回退为独立产品
                config_info['detail'].is_accessory = False
                config_info['detail'].is_editable = True
                current_app.logger.warning(f"配置产品 {config_info['detail'].product_name} 找不到父产品，已回退为独立产品，parent_row_id={config_info['parent_row_id']}")

        current_app.logger.info(f"配置产品父子关系建立完成")

    return created_details, errors


@quotation.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('quotation', 'create')  # 添加创建权限装饰器
def create_quotation():
    # 获取返回URL参数
    return_to = request.args.get('return_to')

    # 获取预设的项目ID
    preset_project_id = request.args.get('project_id')

    # GET:直接重定向到 AT 风格新建页(模板复用 at_view.html with is_new=True)
    if request.method == 'GET':
        return redirect(url_for('quotation.at_new_quotation'))

    if request.method == 'POST':
        try:
            # 检查请求是否为JSON数据
            if request.is_json:
                current_app.logger.debug("收到创建报价单的AJAX请求")
                # 获取请求中的JSON数据
                data = request.get_json()
                
                # 记录请求数据结构
                current_app.logger.debug(f"创建报价单请求数据结构: {data.keys() if isinstance(data, dict) else '非字典数据'}")
                
                # 验证数据是否为空
                if not data:
                    current_app.logger.error("请求数据为空或格式错误")
                    return jsonify({
                        'status': 'error',
                        'message': '请求数据为空或格式错误'
                    }), 400
                
                # 验证项目ID
                if not data.get('project_id'):
                    current_app.logger.error("请求数据中缺少project_id字段")
                    return jsonify({
                        'status': 'error',
                        'message': '项目不能为空'
                    }), 400
                
                # 确保项目ID是整数
                try:
                    project_id = int(data.get('project_id'))
                    
                    # 验证项目是否存在
                    project = Project.query.get(project_id)
                    if not project:
                        current_app.logger.error(f"项目ID {project_id} 不存在")
                        return jsonify({
                            'status': 'error',
                            'message': 'ID为%s的项目不存在' % project_id
                        }), 400
                except (ValueError, TypeError) as e:
                    current_app.logger.error(f"项目ID类型转换错误: {str(e)}")
                    return jsonify({
                        'status': 'error',
                        'message': '项目ID格式错误，必须是整数'
                    }), 400
                
                # 获取总金额
                try:
                    total_amount = float(data.get('total_amount', 0))
                    if total_amount < 0:
                        total_amount = 0
                except (ValueError, TypeError) as e:
                    current_app.logger.error(f"解析总金额失败: {str(e)}")
                    return jsonify({
                        'status': 'error',
                        'message': '总金额格式错误: %s' % str(e)
                    }), 400
                
                # 获取项目的完整信息（从项目表获取最新数据）
                project_stage = project.current_stage or ''
                project_type = project.project_type or ''
                current_app.logger.debug(f'从项目表获取信息: 项目名称={project.project_name}, 阶段={project_stage}, 类型={project_type}')
                
                # 创建新报价单
                quotation = Quotation(
                    project_id=project_id,
                    customer_id=data.get('customer_id'),  # 客户必填
                    contact_id=data.get('contact_id'),     # 联系人可选
                    amount=total_amount,
                    project_stage=project_stage,  # 从项目表获取最新阶段
                    project_type=project_type,    # 从项目表获取最新类型
                    currency=data.get('currency', Config.DEFAULT_CURRENCY),
                    owner_id=current_user.id,
                    notes=data.get('notes', '') or ''
                )
                # 公司主体（CN/SG/MY）
                if data.get('entity_id'):
                    try: quotation.entity_id = int(data.get('entity_id'))
                    except (ValueError, TypeError): pass
                if 'extra_fields' in data and isinstance(data.get('extra_fields'), dict):
                    quotation.extra_fields = data.get('extra_fields') or {}
                db.session.add(quotation)
                current_app.logger.debug(f"创建新报价单: {quotation.quotation_number}")
                
                # 添加明细项
                details = data.get('details', [])
                detail_errors = []
                
                if not details:
                    current_app.logger.warning("报价单没有明细项")
                    return jsonify({
                        'status': 'error',
                        'message': '报价单必须包含至少一个明细项'
                    }), 400
                
                if not isinstance(details, list):
                    current_app.logger.error(f'明细项不是列表格式: {type(details)}')
                    return jsonify({
                        'status': 'error',
                        'message': '明细项必须是数组格式'
                    }), 400

                # 为自建产品（source='custom'）批量分配 MN
                from app.utils.product_helpers import assign_custom_product_mns
                assign_custom_product_mns(details)

                current_app.logger.debug(f'开始处理 {len(details)} 个明细项')

                # 两阶段保存：先创建所有明细，再建立父子关系
                detail_id_map = {}  # {row_id: detail对象}
                pending_configs = []  # 待处理的配置产品列表

                for index, detail in enumerate(details):
                    try:
                        current_app.logger.debug(f'处理第 {index+1} 个明细项: {detail}')
                        
                        if not isinstance(detail, dict):
                            error_msg = f"第 {index+1} 行数据格式错误，必须是对象格式"
                            current_app.logger.error(error_msg)
                            detail_errors.append(error_msg)
                            continue
                        
                        # 验证必填字段
                        product_name = detail.get('product_name', '').strip()
                        if not product_name:
                            error_msg = f"第 {index+1} 行产品名称不能为空"
                            current_app.logger.warning(error_msg)
                            detail_errors.append(error_msg)
                            continue
                        
                        # 安全地获取数值字段
                        try:
                            market_price = float(detail.get('market_price', 0))
                        except (ValueError, TypeError) as e:
                            market_price = 0
                            error_msg = f"第 {index+1} 行市场价格格式无效"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        try:
                            discount = float(detail.get('discount_rate', 100)) / 100
                            # 确保折扣率不小于0，不限制上限
                            if discount < 0:
                                error_msg = f"第 {index+1} 行折扣率不能为负数"
                                current_app.logger.warning(error_msg)
                                detail_errors.append(error_msg)
                                discount = 0
                        except (ValueError, TypeError) as e:
                            discount = 1.0
                            error_msg = f"第 {index+1} 行折扣率格式无效，已设为100%"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        try:
                            quantity = int(detail.get('quantity', 1))
                            if quantity <= 0:
                                quantity = 1
                                error_msg = f"第 {index+1} 行数量必须大于0，已设为1"
                                current_app.logger.warning(error_msg)
                                detail_errors.append(error_msg)
                        except (ValueError, TypeError) as e:
                            quantity = 1
                            error_msg = f"第 {index+1} 行数量格式无效，已设为1"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        try:
                            unit_price = float(detail.get('unit_price', 0))
                            if unit_price < 0:
                                unit_price = 0
                                error_msg = f"第 {index+1} 行单价不能为负数，已设为0"
                                current_app.logger.warning(error_msg)
                                detail_errors.append(error_msg)
                        except (ValueError, TypeError) as e:
                            unit_price = 0
                            error_msg = f"第 {index+1} 行单价格式无效，已设为0"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        # 面价是基准、单价是事实:折扣一律由二者反算(同上,防矛盾数据流入批价单)
                        discount = normalize_discount(market_price, unit_price, discount)

                        try:
                            total_price = float(detail.get('total_price', 0))
                            if total_price < 0:
                                total_price = 0
                                error_msg = f"第 {index+1} 行小计不能为负数，已设为0"
                                current_app.logger.warning(error_msg)
                                detail_errors.append(error_msg)
                        except (ValueError, TypeError) as e:
                            # 如果小计无效，从单价和数量重新计算
                            total_price = unit_price * quantity
                            error_msg = f"第 {index+1} 行小计格式无效，已重新计算为: {total_price}"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        # 调试日志：记录JSON明细字段值
                        product_model_value = detail.get('product_model', '')
                        brand_value = detail.get('brand', '')
                        product_mn_value = detail.get('product_mn', '')
                        current_app.logger.debug(f'JSON明细第 {index+1} 行字段值: product_name="{product_name}", product_model="{product_model_value}", brand="{brand_value}", product_mn="{product_mn_value}"')
                        
                        # 创建新明细
                        new_detail = QuotationDetail(
                            product_name=product_name,
                            product_model=product_model_value,
                            product_desc=detail.get('product_desc', ''),
                            brand=brand_value,
                            unit=detail.get('unit', ''),
                            quantity=quantity,
                            discount=discount,
                            market_price=market_price,
                            unit_price=unit_price,
                            total_price=total_price,
                            product_mn=product_mn_value,
                            currency=data.get('currency', Config.DEFAULT_CURRENCY),  # 添加明细货币字段
                            item_note=detail.get('item_note', '') or ''
                        )

                        # 处理动态规格配置字段（用于创建研发产品）
                        configured_specs_str = detail.get('configured_specs')
                        if configured_specs_str:
                            if isinstance(configured_specs_str, str):
                                try:
                                    new_detail.configured_specs = json.loads(configured_specs_str)
                                except json.JSONDecodeError:
                                    new_detail.configured_specs = None
                            else:
                                new_detail.configured_specs = configured_specs_str

                        new_detail.configured_mn = str(detail.get('configured_mn', '')).strip() or None
                        new_detail.price_adjustment_total = int(detail.get('price_adjustment_total', 0) or 0)
                        pending_creation = detail.get('pending_product_creation', False)
                        if isinstance(pending_creation, str):
                            new_detail.pending_product_creation = pending_creation.lower() == 'true'
                        else:
                            new_detail.pending_product_creation = bool(pending_creation)

                        # 处理配置产品相关字段
                        is_configuration = detail.get('is_configuration', False)
                        if is_configuration:
                            new_detail.is_accessory = True
                            new_detail.is_editable = False
                            new_detail.config_type = detail.get('config_type')
                            new_detail.config_base_quantity = int(detail.get('config_base_quantity', 1))
                            new_detail.quantity_synced = detail.get('quantity_synced', True)  # ✅ 保存同步状态

                            # 添加到待处理配置列表
                            pending_configs.append({
                                'detail': new_detail,
                                'parent_row_id': detail.get('parent_row_id')
                            })
                            current_app.logger.debug(f'第 {index+1} 行是配置产品: parent_row_id={detail.get("parent_row_id")}')
                        else:
                            # 主产品：记录row_id映射
                            row_id = detail.get('row_id')
                            if row_id:
                                detail_id_map[row_id] = new_detail
                                current_app.logger.debug(f'第 {index+1} 行是主产品: row_id={row_id}')

                        # 计算植入小计
                        new_detail.calculate_prices()

                        current_app.logger.debug(f'创建第 {index+1} 行明细项')
                        quotation.details.append(new_detail)
                    except Exception as item_error:
                        error_msg = f"处理第 {index+1} 行明细时出错: {str(item_error)}"
                        current_app.logger.error(error_msg)
                        detail_errors.append(error_msg)
                
                try:
                    # 执行完整的数据计算和同步
                    # 1. 计算植入总额合计（基于产品明细的植入小计）
                    quotation.calculate_implant_total_amount()
                    current_app.logger.debug(f'植入总额计算完成: {quotation.implant_total_amount}')
                    
                    # 2. 生成产品签名（用于变更检测）
                    import hashlib
                    import json
                    signature_data = []
                    for detail in quotation.details:
                        signature_data.append({
                            'product_name': detail.product_name,
                            'product_model': detail.product_model,
                            'quantity': detail.quantity,
                            'unit_price': detail.unit_price
                        })
                    signature_json = json.dumps(signature_data, sort_keys=True)
                    quotation.product_signature = hashlib.md5(signature_json.encode()).hexdigest()[:16]
                    current_app.logger.debug(f'产品签名生成完成: {quotation.product_signature}')
                    
                    # 3. 手动更新时间戳
                    quotation.updated_at = datetime.utcnow()

                    # 3.5. 第二阶段：Flush获取ID，然后建立父子关系
                    if pending_configs:
                        current_app.logger.info(f"开始处理 {len(pending_configs)} 个配置产品的父子关系")
                        db.session.flush()  # Flush以获取所有detail的ID

                        for config_info in pending_configs:
                            parent_detail = detail_id_map.get(config_info['parent_row_id'])
                            if parent_detail:
                                config_info['detail'].parent_item_id = parent_detail.id
                                current_app.logger.debug(f"配置产品 {config_info['detail'].product_name} 关联到父产品 {parent_detail.product_name} (ID={parent_detail.id})")
                            else:
                                # 找不到父产品，回退为独立产品
                                config_info['detail'].is_accessory = False
                                config_info['detail'].is_editable = True
                                current_app.logger.warning(f"配置产品 {config_info['detail'].product_name} 找不到父产品，已回退为独立产品，parent_row_id={config_info['parent_row_id']}")

                        current_app.logger.info(f"配置产品父子关系建立完成")

                    # 4. 提交数据库更改
                    current_app.logger.info('准备提交所有更改到数据库...')
                    db.session.commit()
                    current_app.logger.info(f'报价单数据保存完成: 总额={quotation.amount}, 植入总额={quotation.implant_total_amount}')

                    # 记录创建历史
                    try:
                        from app.utils.change_tracker import ChangeTracker
                        ChangeTracker.log_create(quotation)
                    except Exception as track_err:
                        current_app.logger.warning(f"记录报价单创建历史失败: {str(track_err)}")
                    
                    # 更新关联项目的活跃度
                    try:
                        if quotation.project:
                            update_active_status(quotation.project)
                            current_app.logger.debug(f"报价单创建后更新项目 {quotation.project.id} 活跃度")
                    except Exception as activity_err:
                        current_app.logger.warning(f"更新项目活跃度失败: {str(activity_err)}")
                    
                    # 注意：项目金额更新交由SQLAlchemy事件监听器处理，此处无需手动更新
                    current_app.logger.info('项目报价金额将由事件监听器自动更新')

                    # 新建报价单默认 none 态(不自动发起技术确认)
                    # owner 在详情页主动点"技术确认"按钮再发起 + 选指定 SM

                    # 记录创建报价单到日历工作项
                    record_activity('create', 'quotation', quotation.quotation_number, current_user,
                        project_id=quotation.project_id, customer_id=quotation.customer_id,
                        start_time_str=data.get('page_load_time'),
                        description=f'为项目 {quotation.project.project_name if quotation.project else ""} 创建报价单')

                    # 检查并创建配置产品到研发产品库
                    try:
                        created_products = create_products_from_configured_specs(quotation)
                        if created_products:
                            db.session.commit()  # 提交研发产品的更改
                            current_app.logger.info(f'报价单 {quotation.id} 创建了 {len(created_products)} 个研发产品')
                    except Exception as e:
                        current_app.logger.error(f'创建研发产品失败: {str(e)}')

                    # 返回JSON响应供前端处理跳转
                    return jsonify({
                        'status': 'success',
                        'message': '报价单创建成功！',
                        'redirect_url': url_for('quotation.view_quotation', id=quotation.id),
                        'quotation_id': quotation.id
                    })
                except Exception as commit_error:
                    db.session.rollback()
                    error_type = type(commit_error).__name__
                    current_app.logger.error(f"提交更改时出错: {error_type} - {str(commit_error)}")
                    
                    # 返回错误信息
                    return jsonify({
                        'status': 'error',
                        'message': '保存失败: %s - %s' % (error_type, str(commit_error))
                    }), 500
            else:
                # 不再支持传统表单格式，只支持JSON格式提交
                current_app.logger.warning('收到传统表单提交请求，但系统已统一使用JSON格式')
                raise ValueError('系统已升级为统一数据格式，请使用现代浏览器或刷新页面重试')
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f'处理POST请求时发生错误: {type(e).__name__}')
            
            # 根据请求类型返回不同的响应
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': '%s: %s' % (type(e).__name__, str(e))
                }), 500
            else:
                flash(_('报价单创建失败：%s') % str(e), 'danger')
                print(f"Error: {str(e)}")  # 添加错误日志
    
    # GET 请求处理 - 渲染全屏 Excel-like 编辑器（Beta 共存模式）
    return _render_excel_editor(quotation_id=None, project_id_preset=preset_project_id)

@quotation.route('/get_project/<int:project_id>')
def get_project(project_id):
    try:
        logger.debug(f"获取项目 {project_id} 的信息...")
        project = Project.query.get_or_404(project_id)
        logger.debug(f"项目信息: 阶段={project.current_stage}, 类型={project.project_type}")
        
        # 导入翻译函数
        from app.utils.dictionary_helpers import project_stage_label, project_type_label
        
        # 获取翻译后的阶段和类型
        stage_display = project_stage_label(project.current_stage, 'zh') if project.current_stage else ''
        type_display = project_type_label(project.project_type, 'zh') if project.project_type else project.project_type
        
        # 设置缓存控制头
        response = jsonify({
            'success': True,
            'current_stage': stage_display,  # 返回翻译后的阶段
            'project_type': type_display,   # 返回翻译后的类型
            'project_name': project.project_name,
            'authorization_code': project.authorization_code
        })
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"获取项目信息时出错: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@quotation.route('/<int:id>/edit', methods=['GET'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以编辑自己的报价单数据
def edit_quotation(id):
    try:
        return _render_excel_editor(quotation_id=id, project_id_preset=None)
    except Exception as e:
        flash(_('加载报价单失败：%s') % str(e), 'danger')
        return redirect(url_for('quotation.list_quotations'))


@quotation.route('/<int:id>/copy', methods=['POST'])
@login_required
@permission_required('quotation', 'create')
def copy_quotation(id):
    try:
        original_quotation = Quotation.query.get_or_404(id)
        if not can_view_quotation(current_user, original_quotation):
            logger.debug(f"{current_user.username} 无权复制报价单 {original_quotation.id}")
            flash(_('您没有权限复制此报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))
        # 创建新报价单
        new_quotation = Quotation(
            project_id=original_quotation.project_id,
            contact_id=original_quotation.contact_id,
            project_stage=original_quotation.project_stage,
            project_type=original_quotation.project_type,
            owner_id=current_user.id  # 设置当前用户为所有者
        )
        
        # 复制明细
        for detail in original_quotation.details:
            new_detail = QuotationDetail(
                product_name=detail.product_name,
                product_model=detail.product_model,
                product_desc=detail.product_desc,
                brand=detail.brand,
                unit=detail.unit,
                quantity=detail.quantity,
                discount=detail.discount,
                market_price=detail.market_price,
                unit_price=detail.unit_price,
                total_price=detail.total_price,
                product_mn=detail.product_mn if hasattr(detail, 'product_mn') else ''  # 添加MN号
            )
            
            # 计算植入小计
            new_detail.calculate_prices()
            
            new_quotation.details.append(new_detail)
        
        # 设置总金额
        new_quotation.amount = original_quotation.amount
        
        # 计算植入总额
        new_quotation.calculate_implant_total_amount()
        
        db.session.add(new_quotation)
        db.session.commit()
        
        # 项目金额缓存由 after_insert 事件监听器自动刷新，无需手动处理
        flash(_('报价单复制成功！'), 'success')
        return redirect(url_for('quotation.edit_quotation', id=new_quotation.id))
    except Exception as e:
        db.session.rollback()
        flash(_('报价单复制失败：%s') % str(e), 'danger')
        return redirect(url_for('quotation.list_quotations'))

@quotation.route('/<int:id>/delete', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以删除自己的报价单数据
def delete_quotation(id):
    quotation = Quotation.query.get_or_404(id)

    # 使用统一的数据权限检查（包含数据归属逻辑）
    if not can_edit_data(quotation, current_user):
        flash(_('您没有权限删除此报价单'), 'danger')
        return redirect(url_for('quotation.list_quotations'))
    
    try:
        # 记录删除历史
        try:
            from app.utils.change_tracker import ChangeTracker
            ChangeTracker.log_delete(quotation)
        except Exception as track_err:
            current_app.logger.warning(f"记录报价单删除历史失败: {str(track_err)}")
        
        # === 新增：删除报价单审批实例和相关审批记录 ===
        from app.models.approval import ApprovalInstance, ApprovalRecord
        quotation_approvals = ApprovalInstance.query.filter_by(
            object_type='quotation', 
            object_id=id
        ).all()
        
        if quotation_approvals:
            approval_record_count = 0
            for approval in quotation_approvals:
                # 删除审批记录
                records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                approval_record_count += len(records)
                for record in records:
                    db.session.delete(record)
                # 删除审批实例
                db.session.delete(approval)
            
            current_app.logger.info(f"已删除 {len(quotation_approvals)} 个报价单审批实例和 {approval_record_count} 个审批记录")
        
        # 删除报价单确认任务
        from app.models.quotation_confirmation_task import QuotationConfirmationTask
        confirmation_tasks = QuotationConfirmationTask.query.filter_by(quotation_id=id).all()
        for ct in confirmation_tasks:
            db.session.delete(ct)

        # === 新增：显式删除报价单明细 ===
        from app.models.quotation import QuotationDetail
        quotation_details = QuotationDetail.query.filter_by(quotation_id=id).all()

        if quotation_details:
            for detail in quotation_details:
                db.session.delete(detail)
            current_app.logger.info(f"已删除 {len(quotation_details)} 个报价单明细")

        db.session.delete(quotation)
        db.session.commit()
        flash(_('报价单删除成功！'), 'success')
    except Exception as e:
        db.session.rollback()
        flash(_('删除失败：%s') % str(e), 'danger')
    
    return redirect(url_for('quotation.list_quotations'))

@quotation.route('/batch-delete', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以删除自己的报价单数据
def batch_delete_quotations():
    try:
        data = request.get_json()
        quotation_ids = data.get('quotation_ids', [])
        if not quotation_ids:
            return jsonify({'success': False, 'message': '未选择任何报价单'})
        deleted_count = 0
        error_ids = []
        project_ids = set()
        for quotation_id in quotation_ids:
            try:
                quotation = Quotation.query.get(quotation_id)
                if quotation:
                    if can_edit_data(quotation, current_user):
                        # 记录涉及的项目ID
                        if quotation.project_id:
                            project_ids.add(quotation.project_id)
                        
                        # === 新增：删除报价单审批实例和相关审批记录 ===
                        from app.models.approval import ApprovalInstance, ApprovalRecord
                        quotation_approvals = ApprovalInstance.query.filter_by(
                            object_type='quotation', 
                            object_id=quotation_id
                        ).all()
                        
                        if quotation_approvals:
                            for approval in quotation_approvals:
                                # 删除审批记录
                                records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                                for record in records:
                                    db.session.delete(record)
                                # 删除审批实例
                                db.session.delete(approval)
                        
                        # 删除报价单确认任务
                        from app.models.quotation_confirmation_task import QuotationConfirmationTask
                        for ct in QuotationConfirmationTask.query.filter_by(quotation_id=quotation_id).all():
                            db.session.delete(ct)

                        # === 新增：显式删除报价单明细 ===
                        from app.models.quotation import QuotationDetail
                        quotation_details = QuotationDetail.query.filter_by(quotation_id=quotation_id).all()

                        if quotation_details:
                            for detail in quotation_details:
                                db.session.delete(detail)

                        # 删除报价单
                        db.session.delete(quotation)
                        deleted_count += 1
                    else:
                        logger.warning(f"用户 {current_user.username} 无权删除报价单 {quotation_id}")
                        error_ids.append(quotation_id)
                else:
                    logger.warning(f"报价单 {quotation_id} 不存在")
                    error_ids.append(quotation_id)
            except Exception as item_error:
                logger.error(f"删除报价单 {quotation_id} 时出错: {str(item_error)}")
                error_ids.append(quotation_id)
        
        # 提交删除操作
        db.session.commit()
        
        # 注意：项目金额更新交由SQLAlchemy事件监听器处理，此处无需手动更新
        logger.info(f"批量删除涉及的项目IDs: {project_ids}，将由事件监听器自动更新金额")
        
        return jsonify({'success': True, 'deleted': deleted_count, 'error_ids': error_ids})
    except Exception as e:
        logger.error(f"批量删除报价单时出错: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@quotation.route('/search_projects')
@login_required
def search_projects():
    """搜索项目（用于报价单创建/编辑时选择项目）"""
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)

        if not query_term or len(query_term) < 2:
            return jsonify({'success': True, 'projects': []})

        # 使用现有的搜索辅助函数
        from app.utils.search_helpers import search_projects_by_name
        results = search_projects_by_name(query_term, current_user, limit)

        # 转换为前端期望的格式
        projects = []
        for r in results:
            projects.append({
                'id': r['id'],
                'name': r['project_name'],
                'owner': r.get('owner_name', ''),
                'type': r.get('project_type_display', r.get('project_type', '')),
                'type_code': r.get('project_type', ''),
                'stage': r.get('current_stage_display', r.get('current_stage', '')),
                'stage_code': r.get('current_stage', ''),
            })

        return jsonify({'success': True, 'projects': projects})

    except Exception as e:
        logger.error(f"搜索项目时出错: {str(e)}")
        return jsonify({'success': False, 'message': str(e), 'projects': []})

@quotation.route('/search_customers')
@login_required
def search_customers():
    """模糊搜客户(公司名/编码),用于报价单新建时独立选客户"""
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        if not query_term or len(query_term) < 2:
            return jsonify({'success': True, 'customers': []})
        from app.models import Company
        from app.utils.access_control import get_viewable_data
        like = f'%{query_term}%'
        base = get_viewable_data(Company, current_user, [Company.is_deleted == False])
        rows = base.filter(or_(
            Company.company_name.ilike(like),
            Company.company_code.ilike(like),
        )).order_by(Company.updated_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'customers': [{
            'id': c.id,
            'name': c.company_name,
            'code': c.company_code or '',
            'country': c.country or '',
        } for c in rows]})
    except Exception as e:
        logger.error(f"搜索客户失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e), 'customers': []})


@quotation.route('/get_customer_projects/<int:customer_id>')
@login_required
def get_customer_projects(customer_id):
    """反向取客户参与的项目列表(用于先选客户、再选项目的双向场景)"""
    try:
        from app.models import Project
        from app.models.project_customer_association import ProjectCustomerAssociation
        from app.utils.access_control import get_viewable_data
        # 查 ProjectCustomerAssociation
        assocs = ProjectCustomerAssociation.query.filter_by(customer_id=customer_id).all()
        pids = [a.project_id for a in assocs]
        if not pids:
            return jsonify({'success': True, 'projects': []})
        base = get_viewable_data(Project, current_user, [Project.id.in_(pids)])
        rows = base.order_by(Project.updated_at.desc()).limit(50).all()
        return jsonify({'success': True, 'projects': [{
            'id': p.id,
            'name': p.project_name,
            'type': p.project_type or '',
            'type_code': p.project_type or '',
            'stage': getattr(p, 'current_stage', '') or '',
            'stage_code': getattr(p, 'current_stage', '') or '',
        } for p in rows]})
    except Exception as e:
        logger.error(f"取客户项目失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e), 'projects': []})


@quotation.route('/get_project_customers/<int:project_id>')
def get_project_customers(project_id):
    """从ProjectCustomerAssociation关联表获取项目的客户列表"""
    try:
        print(f"开始获取项目 {project_id} 的客户列表...")

        # 获取项目
        project = Project.query.get_or_404(project_id)
        print(f"找到项目: {project.project_name}")

        # 从ProjectCustomerAssociation关联表获取客户
        from app.models.project_customer_association import ProjectCustomerAssociation

        associations = ProjectCustomerAssociation.query.filter_by(project_id=project_id).all()

        # 客户类型中英文映射
        customer_type_labels = {
            'end_user': '直接用户',
            'design_issues': '设计院',
            'contractor': '总承包单位',
            'system_integrator': '系统集成商',
            'dealer': '经销商'
        }

        # 构建客户列表
        companies = []
        company_ids = set()  # 用于去重

        for assoc in associations:
            company = Company.query.filter_by(id=assoc.company_id, is_deleted=False).first()
            if company and company.id not in company_ids:
                companies.append({
                    'id': company.id,
                    'name': company.company_name,
                    'type': customer_type_labels.get(assoc.customer_type, assoc.customer_type)
                })
                company_ids.add(company.id)
                print(f"- {company.company_name} ({customer_type_labels.get(assoc.customer_type, assoc.customer_type)})")

        print(f"找到 {len(companies)} 个唯一客户")

        return jsonify({'success': True, 'customers': companies})
    except Exception as e:
        print(f"获取项目客户列表时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400

@quotation.route('/get_customer_contacts/<int:customer_id>')
@login_required
def get_customer_contacts(customer_id):
    """获取客户的联系人列表"""
    try:
        # 获取客户
        company = Company.query.get_or_404(customer_id)

        # 获取联系人列表
        contacts = Contact.query.filter_by(company_id=customer_id).all()

        contact_list = []
        for contact in contacts:
            contact_list.append({
                'id': contact.id,
                'name': contact.name,
                'position': contact.position or ''
            })

        return jsonify({'success': True, 'contacts': contact_list})
    except Exception as e:
        logger.error(f"获取客户联系人列表时出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@quotation.route('/get_companies')
def get_companies():
    """获取所有公司列表的API，带权限控制"""
    try:
        print("正在获取所有公司列表...")
        
        # 使用访问控制过滤获取客户
        query = get_viewable_data(Company, current_user)
        
        # 如果有is_deleted字段，添加过滤条件
        if hasattr(Company, 'is_deleted'):
            query = query.filter_by(is_deleted=False)
            print("使用is_deleted过滤条件查询")
        
        companies = query.all()
        
        customers = []
        for company in companies:
            customers.append({
                'id': company.id,
                'name': company.company_name
            })
        
        print(f"成功获取到 {len(customers)} 个公司")
        if customers:
            print(f"公司示例: ID={customers[0]['id']}, 名称={customers[0]['name']}")
        
        return jsonify({'customers': customers})
    except Exception as e:
        print(f"获取公司列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': '获取公司列表失败',
            'message': str(e)
        }), 500

@quotation.route('/get_all_companies')
def get_all_companies():
    """获取所有公司列表的API（保持API兼容性）"""
    # 直接调用get_companies函数，避免代码重复
    return get_companies()

@quotation.route('/get_all_projects')
def get_all_projects():
    try:
        logger.debug("获取所有项目列表...")
        # 获取当前用户权限范围内可见的所有项目（不再限定owner_id）
        projects_query = get_viewable_data(Project, current_user)
        # 移除对已有报价单项目的过滤，因为一个项目可以有多个报价单
        projects = projects_query.all()
        # 构建项目列表，只返回必要的信息
        project_list = [{'id': p.id, 'name': p.project_name} for p in projects]
        logger.debug(f"找到 {len(project_list)} 个项目")
        # 设置缓存控制头
        response = jsonify({'projects': project_list})
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取项目列表失败',
            'message': str(e)
        }), 500

# 添加产品相关API接口
@quotation.route('/products', methods=['GET'])
def get_products():
    """获取产品列表API"""
    try:
        logger.debug('正在获取产品列表...')
        # 获取搜索词和查询类型
        term = request.args.get('term', '')
        query_type = request.args.get('type', 'search')  # 'search' 或 'exact'
        product_name = request.args.get('product_name', '')
        logger.debug(f'搜索词: {term}, 查询类型: {query_type}, 产品名称: {product_name}')
        
        # 根据查询类型执行不同的查询
        if query_type == 'exact':
            # 精确匹配产品名称，包括停产产品
            products = Product.query.filter_by(
                product_name=product_name,
            ).all()
        else:
            # 模糊搜索，包括停产产品
            query = Product.query
            if term:
                search_term = f'%{term}%'
                query = query.filter(
                    db.or_(
                        Product.product_name.ilike(search_term),
                        Product.product_mn.ilike(search_term)
                    )
                )
            products = query.all()
            
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
            
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'type': p.type,
                    'category': p.category,
                    'product_mn': p.product_mn,
                    'spec_mn': p.spec_mn,  # 完整规格MN（用于可配置字段计算）
                    'product_name': p.name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'status': p.status,  # 添加产品状态
                    'currency': p.currency or Config.DEFAULT_CURRENCY  # 添加货币信息
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.name}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        logger.debug(f'成功处理 {len(result)} 个产品')
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取产品列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品列表失败',
            'message': str(e)
        }), 500

@quotation.route('/products/categories', methods=['GET'])
@login_required
@permission_required('quotation', 'view')
def get_product_categories():
    """获取去重后的产品类别列表，按业务顺序排列"""
    try:
        logger.debug('正在获取产品类别列表...')
        # 从ProductCategory表查询，只返回有非停产产品的类别
        from app.models.product_code import ProductCategory
        from app.models.product_display_order import ProductDisplayOrder

        # 查询有非停产产品的类别（带 code_letter 用于关联 product_display_order）
        categories = db.session.query(
            ProductCategory.id,
            ProductCategory.name,
            ProductCategory.code_letter,
            ProductCategory.display_order
        ).join(
            Product, Product.category_id == ProductCategory.id
        ).filter(
            Product.status != '停产'
        ).distinct().all()

        # 使用 product_display_order 表获取排序（与产品列表保持一致）
        pdo_cat_rows = db.session.query(
            ProductDisplayOrder.category_code,
            func.min(ProductDisplayOrder.category_order)
        ).group_by(ProductDisplayOrder.category_code).all()
        pdo_cat_orders = {cc: co for cc, co in pdo_cat_rows}

        # 按 product_display_order 的 category_order 排序，fallback 到 display_order
        categories_sorted = sorted(
            categories,
            key=lambda c: (pdo_cat_orders.get(c[2], 9999) if c[2] else 9999, c[3] or 9999, c[0])
        )

        category_list = [cat[1] for cat in categories_sorted]
        logger.debug(f'找到 {len(category_list)} 个类别')
        return jsonify(category_list)
    except Exception as e:
        logger.error(f'获取产品类别列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品类别列表失败',
            'message': str(e)
        }), 500

@quotation.route('/products/by-category', methods=['GET'])
@login_required
@permission_required('quotation', 'view')
def get_products_by_category():
    """获取指定类别的产品列表，包括停产产品"""
    try:
        category = request.args.get('category', '')
        logger.debug(f'正在获取类别 "{category}" 的产品列表...')

        if not category:
            return jsonify([])

        # 导入子分类模型用于排序
        from app.models.product_code import ProductSubcategory

        # 查询指定类别的产品，按子分类 display_order 排序（与产品列表一致）
        products = Product.query.outerjoin(
            ProductSubcategory, Product.subcategory_id == ProductSubcategory.id
        ).filter(
            Product.category == category
        ).order_by(
            ProductSubcategory.display_order.asc().nullslast(),
            Product.id
        ).all()
        
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'product_name': p.name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn,
                    'spec_mn': p.spec_mn,  # 完整规格MN（用于可配置字段计算）
                    'status': p.status,  # 添加产品状态
                    'currency': p.currency or Config.DEFAULT_CURRENCY  # 添加货币字段
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.name}, MN: {p.product_mn}, 货币: {p.currency}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取类别产品列表时出错: {str(e)}')
        return jsonify({
            'error': '获取类别产品列表失败',
            'message': str(e)
        }), 500

@quotation.route('/products/models', methods=['GET'])
@login_required
@permission_required('quotation', 'view')
def get_product_models():
    """获取指定类别和产品名称的型号列表"""
    try:
        category = request.args.get('category', '')
        product_name = request.args.get('product_name', '')
        logger.debug(f'正在获取产品型号，类别: "{category}", 产品名称: "{product_name}"')
        
        if not category or not product_name:
            return jsonify([])
        
        # 查询指定类别和产品名称的产品（包括停产产品）
        products = Product.query.filter_by(
            category=category,
            product_name=product_name
        ).order_by(Product.id).all()
        
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'product_name': p.name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn,
                    'spec_mn': p.spec_mn,  # 完整规格MN（用于可配置字段计算）
                    'currency': p.currency or Config.DEFAULT_CURRENCY,  # 添加货币字段
                    'status': p.status  # 添加产品状态字段
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.name}, 型号: {p.model}, 货币: {p.currency}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取产品型号列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品型号列表失败',
            'message': str(e)
        }), 500

def parse_code_specs(snapshot):
    """
    解析产品编码快照并分离编码规格和非编码规格

    Args:
        snapshot: 产品的 code_definition_snapshot JSON字符串或字典

    Returns:
        tuple: (code_specs, non_code_specs) 两个规格列表
    """
    code_specs = []
    non_code_specs = []

    try:
        # 如果是字符串，解析为字典
        if isinstance(snapshot, str):
            import json
            parsed = json.loads(snapshot)
        else:
            parsed = snapshot

        # 提取 code_parts 数组
        code_parts = parsed.get('code_parts', [])

        for part in code_parts:
            # 只处理规格字段
            if part.get('field_type') == 'spec':
                spec_item = {
                    'field_name': part.get('field_name', ''),
                    'value': part.get('value', ''),
                    'unit': part.get('unit', '')
                }

                # 根据 use_in_code 标记分类（默认为 True，即编码规格）
                if part.get('use_in_code', True):
                    code_specs.append(spec_item)
                else:
                    non_code_specs.append(spec_item)

    except Exception as e:
        logger.warning(f'解析产品编码快照时出错: {str(e)}')

    return code_specs, non_code_specs


@quotation.route('/products/specs', methods=['GET'])
@login_required
@permission_required('quotation', 'view')
def get_product_specs():
    """获取指定类别、产品名称和型号的规格列表"""
    try:
        category = request.args.get('category', '')
        product_name = request.args.get('product_name', '')
        # 修复：同时支持 product_model 和 model 参数
        product_model = request.args.get('model', '') or request.args.get('product_model', '')
        logger.debug(f'正在获取产品规格，类别: "{category}", 产品名称: "{product_name}", 型号: "{product_model}"')
        
        if not category or not product_name or not product_model:
            return jsonify([])
        
        # 查询指定条件的产品
        products = Product.query.filter_by(
            category=category,
            product_name=product_name,
            model=product_model
        ).filter(Product.status != '停产').order_by(Product.id).all()
        
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = []
        for p in products:
            try:
                # 处理产品图片
                product_image = None
                if hasattr(p, 'image_path') and p.image_path:
                    # 确保图片路径是相对于static目录的
                    if p.image_path.startswith('/static/'):
                        product_image = p.image_path
                    elif p.image_path.startswith('static/'):
                        product_image = '/' + p.image_path
                    else:
                        product_image = '/static/' + p.image_path.lstrip('/')
                
                # 解析编码快照，分离编码规格和非编码规格
                code_specs, non_code_specs = parse_code_specs(p.code_definition_snapshot)

                product_dict = {
                    'id': p.id,
                    'product_name': p.name,
                    'model': p.model,  # 修复：使用正确的字段名
                    'specification': p.specification,  # 修复：使用正确的字段名
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn,
                    'spec_mn': p.spec_mn,  # 完整规格MN（用于可配置字段计算）
                    'currency': p.currency or Config.DEFAULT_CURRENCY,  # 添加货币字段
                    'image_path': product_image,  # 添加图片路径
                    'code_specs': code_specs,  # 编码规格（默认显示）
                    'non_code_specs': non_code_specs  # 非编码规格（默认折叠）
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.name}, 规格: {p.specification}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取产品规格列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品规格列表失败',
            'message': str(e)
        }), 500


@quotation.route('/api/product-meta-options', methods=['GET'])
@login_required
@permission_required('quotation', 'create')
def get_product_meta_options():
    """
    获取产品库中已有的品牌和单位列表（去重）
    用途：自建产品行的品牌/单位输入框下拉建议
    """
    try:
        brands = db.session.query(Product.brand).filter(
            Product.brand.isnot(None),
            Product.brand != '',
            Product.is_deleted == False
        ).distinct().order_by(Product.brand).all()

        units = db.session.query(Product.unit).filter(
            Product.unit.isnot(None),
            Product.unit != '',
            Product.is_deleted == False
        ).distinct().order_by(Product.unit).all()

        return jsonify({
            'brands': [b[0] for b in brands],
            'units': [u[0] for u in units]
        })
    except Exception as e:
        logger.error(f'获取产品元数据失败: {str(e)}')
        return jsonify({'brands': [], 'units': [], 'error': str(e)}), 500


@quotation.route('/api/product-suggestions', methods=['GET'])
@login_required
@permission_required('quotation', 'create')
def get_custom_product_suggestions():
    """
    Autocomplete: 从 quotation_details 聚合查询自建产品建议

    规则：
    - 只返回非产品库产品（LEFT JOIN products WHERE p.id IS NULL）
    - 按 product_name 或 product_model 模糊匹配
    - 按 (product_name, product_model) 聚合去重，取最近一条
    - 按使用次数降序 + 最近时间降序排列

    Query Params:
        q (str): 搜索关键词（必需）
        limit (int): 返回数量，默认 10

    Returns:
        JSON: {"results": [{product_name, product_model, product_desc, brand,
                           unit, product_mn, market_price, currency,
                           last_used_at, usage_count}, ...]}
    """
    from sqlalchemy import text

    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify({'results': []})

    limit = request.args.get('limit', 10, type=int)
    if limit <= 0 or limit > 50:
        limit = 10

    sql = text("""
        WITH latest AS (
            SELECT DISTINCT ON (qd.product_name, qd.product_model)
                qd.product_name, qd.product_model, qd.product_desc,
                qd.brand, qd.unit, qd.product_mn,
                qd.market_price, qd.currency,
                qd.created_at AS last_used_at
            FROM quotation_details qd
            LEFT JOIN products p
                ON p.product_mn = qd.product_mn AND p.is_deleted = FALSE
            WHERE p.id IS NULL
              AND qd.product_name IS NOT NULL
              AND qd.product_name != ''
              AND (qd.product_name ILIKE :pattern OR qd.product_model ILIKE :pattern)
            ORDER BY qd.product_name, qd.product_model, qd.created_at DESC
        ),
        stats AS (
            SELECT
                qd.product_name, qd.product_model,
                COUNT(DISTINCT qd.quotation_id) AS usage_count
            FROM quotation_details qd
            LEFT JOIN products p
                ON p.product_mn = qd.product_mn AND p.is_deleted = FALSE
            WHERE p.id IS NULL
              AND qd.product_name IS NOT NULL
              AND qd.product_name != ''
              AND (qd.product_name ILIKE :pattern OR qd.product_model ILIKE :pattern)
            GROUP BY qd.product_name, qd.product_model
        )
        SELECT
            l.product_name, l.product_model, l.product_desc,
            l.brand, l.unit, l.product_mn,
            l.market_price, l.currency,
            l.last_used_at, s.usage_count
        FROM latest l
        JOIN stats s
            ON s.product_name = l.product_name
           AND s.product_model = l.product_model
        ORDER BY s.usage_count DESC, l.last_used_at DESC
        LIMIT :limit
    """)

    try:
        rows = db.session.execute(sql, {
            'pattern': f'%{keyword}%',
            'limit': limit
        }).fetchall()

        results = []
        for row in rows:
            data = dict(row._mapping)
            # 序列化 datetime 和 Decimal
            if data.get('last_used_at'):
                data['last_used_at'] = data['last_used_at'].isoformat()
            if data.get('market_price') is not None:
                data['market_price'] = float(data['market_price'])
            results.append(data)

        return jsonify({'results': results})
    except Exception as e:
        logger.error(f'查询自建产品建议失败: {str(e)}')
        return jsonify({'results': [], 'error': str(e)}), 500


@quotation.route('/products/temp', methods=['GET'])
@login_required
@permission_required('quotation', 'create')
def get_temp_products():
    """
    获取临时产品列表 - 报价单模块专用端点
    """
    try:
        from app.models.temp_product import TempProduct
        
        category = request.args.get('category')
        limit = request.args.get('limit', 20, type=int)
        
        # 构建查询
        query = TempProduct.query.filter_by(
            created_by=current_user.id,
            is_deleted=False
        )
        
        if category:
            query = query.filter_by(category=category)
        
        # 按使用次数和更新时间排序
        products = query.order_by(
            TempProduct.usage_count.desc(),
            TempProduct.updated_at.desc()
        ).limit(limit).all()
        
        # 按产品名称分组组织临时产品
        product_groups = {}
        for product in products:
            product_name = product.product_name
            if product_name not in product_groups:
                product_groups[product_name] = []
            
            product_groups[product_name].append({
                'id': product.id,
                'product_name': product.product_name,
                'product_model': product.product_model,
                'product_desc': product.product_desc,
                'brand': product.brand,
                'unit': product.unit,
                'category': product.category,
                'category_path': product.category_path,
                'market_price': product.reference_price or 0,  # 使用参考价格作为市场价
                'retail_price': product.reference_price or 0,  # 使用参考价格
                'reference_price': product.reference_price or 0,  # 显示参考价格
                'product_mn': product.product_mn,  # 实际MN号
                'mn': product.product_mn,  # 兼容性字段
                'currency': Config.DEFAULT_CURRENCY,
                'status': 'temp',
                'is_temp': True,
                'usage_count': product.usage_count,
                'created_at': product.created_at.isoformat(),
                'last_used_at': product.last_used_at.isoformat() if product.last_used_at else None
            })
        
        # 返回分组后的结果，每个产品名称下的型号按使用次数排序
        result = []
        for product_name in sorted(product_groups.keys()):
            models = sorted(product_groups[product_name], 
                          key=lambda x: (x['usage_count'], x['created_at']), 
                          reverse=True)
            result.extend(models)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取临时产品列表失败: {str(e)}')
        return jsonify({
            'error': '获取临时产品列表失败',
            'message': str(e)
        }), 500


@quotation.route('/products/temp/by_category_product', methods=['GET'])
@login_required
@permission_required('quotation', 'create')
def get_temp_products_by_category_product():
    """
    根据类别和产品名称获取临时产品列表
    支持层级查询：类别→产品名称→型号
    """
    try:
        from app.models.temp_product import TempProduct
        
        category = request.args.get('category')
        product_name = request.args.get('product_name')
        limit = request.args.get('limit', 20, type=int)
        
        # 构建查询
        query = TempProduct.query.filter_by(
            created_by=current_user.id,
            is_deleted=False
        )
        
        if category:
            query = query.filter_by(category=category)
        
        if product_name:
            query = query.filter_by(product_name=product_name)
        
        # 按使用次数和更新时间排序
        products = query.order_by(
            TempProduct.usage_count.desc(),
            TempProduct.updated_at.desc()
        ).limit(limit).all()
        
        # 如果是查询特定产品名称下的型号，返回型号列表
        if product_name:
            result = []
            for product in products:
                result.append({
                    'id': product.id,
                    'product_name': product.product_name,
                    'product_model': product.product_model,
                    'product_desc': product.product_desc,
                    'brand': product.brand,
                    'unit': product.unit,
                    'category': product.category,
                    'category_path': product.category_path,
                    'market_price': product.reference_price or 0,
                    'retail_price': product.reference_price or 0,
                    'reference_price': product.reference_price or 0,
                    'currency': Config.DEFAULT_CURRENCY,
                    'status': 'temp',
                    'is_temp': True,
                    'usage_count': product.usage_count,
                    'product_mn': product.product_mn,  # 实际MN号
                    'mn': product.product_mn,  # 兼容性字段
                    'created_at': product.created_at.isoformat(),
                    'last_used_at': product.last_used_at.isoformat() if product.last_used_at else None
                })
            return jsonify(result)
        
        # 如果只查询类别，返回该类别下的产品名称分组
        product_names = {}
        for product in products:
            name = product.product_name
            if name not in product_names:
                product_names[name] = {
                    'product_name': name,
                    'category': product.category,
                    'temp_models': [],
                    'total_usage': 0
                }
            
            product_names[name]['temp_models'].append({
                'id': product.id,
                'product_model': product.product_model,
                'usage_count': product.usage_count,
                'reference_price': product.reference_price or 0
            })
            product_names[name]['total_usage'] += product.usage_count
        
        # 返回产品名称列表，按总使用次数排序
        result = []
        for name in sorted(product_names.keys(), 
                          key=lambda x: product_names[x]['total_usage'], 
                          reverse=True):
            result.append(product_names[name])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取分类临时产品列表失败: {str(e)}')
        return jsonify({
            'error': '获取分类临时产品列表失败',
            'message': str(e)
        }), 500


@quotation.route('/products/temp/save', methods=['POST'])
@csrf.exempt
@login_required
@permission_required('quotation', 'create')
def save_temp_product():
    """
    保存临时产品 - 报价单模块专用端点
    """
    try:
        from app.models.temp_product import TempProduct
        from app import db
        from datetime import datetime
        
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['product_name', 'product_model', 'product_desc', 'brand', 'unit']
        missing_fields = [field for field in required_fields if not data.get(field, '').strip()]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'缺少必需字段: {", ".join(missing_fields)}'
            }), 400
        
        # 检查是否已存在相同型号和产品名称的组合
        existing = TempProduct.query.filter_by(
            product_name=data['product_name'].strip(),
            product_model=data['product_model'].strip(),
            created_by=current_user.id,
            is_deleted=False
        ).first()
        
        if existing:
            # 更新现有产品
            existing.product_desc = data['product_desc'].strip()
            existing.brand = data['brand'].strip()
            existing.unit = data['unit'].strip()
            existing.category = data.get('category', '').strip()
            existing.category_path = data.get('category_path', '').strip()
            # 更新参考价格（使用unit_price或reference_price）
            reference_price = data.get('unit_price') or data.get('reference_price')
            if reference_price is not None and reference_price != '':
                try:
                    existing.reference_price = float(reference_price)
                except (ValueError, TypeError):
                    existing.reference_price = 0
            existing.increment_usage()
            
            product = existing
            action = 'updated'
        else:
            # 创建新产品 - 确保正确保存参考价格
            reference_price = data.get('unit_price') or data.get('reference_price') or 0
            try:
                reference_price = float(reference_price) if reference_price != '' else 0
            except (ValueError, TypeError):
                reference_price = 0
                
            product = TempProduct(
                product_name=data['product_name'].strip(),
                product_model=data['product_model'].strip(),
                product_desc=data['product_desc'].strip(),
                brand=data['brand'].strip(),
                unit=data['unit'].strip(),
                category=data.get('category', '').strip(),
                category_path=data.get('category_path', '').strip(),
                reference_price=reference_price,
                created_by=current_user.id,
                usage_count=1,
                last_used_at=datetime.utcnow()
            )
            
            # 如果前端已经提供了MN号，直接使用；否则生成新的MN号
            if data.get('product_mn'):
                product.product_mn = data['product_mn'].strip()
                logger.info(f"使用前端提供的MN号: {product.product_mn}")
            else:
                # 生成唯一的MN号
                product.generate_mn()
                logger.info(f"后端生成MN号: {product.product_mn}")
            
            db.session.add(product)
            action = 'created'
        
        db.session.commit()
        
        logger.info(f"临时产品{action}: {product.product_model} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'临时产品已{action}',
            'product': {
                'id': product.id,
                'product_name': product.product_name,
                'product_model': product.product_model,
                'reference_price': product.reference_price or 0,
                'usage_count': product.usage_count,
                'is_temp': True,
                'status': 'temp'
            }
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        logger.error(f'保存临时产品失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'保存临时产品失败: {str(e)}'
        }), 500


@quotation.route('/products/temp/<int:product_id>/increment', methods=['POST'])
@csrf.exempt
@login_required
@permission_required('quotation', 'create')
def increment_temp_product_usage(product_id):
    """
    增加临时产品使用次数
    """
    try:
        from app.models.temp_product import TempProduct
        from app import db
        from datetime import datetime
        
        # 查找临时产品
        temp_product = TempProduct.query.filter_by(
            id=product_id,
            created_by=current_user.id,
            is_deleted=False
        ).first()
        
        if not temp_product:
            return jsonify({
                'success': False,
                'message': '临时产品不存在或无权限访问'
            }), 404
        
        # 增加使用次数
        temp_product.increment_usage()
        db.session.commit()
        
        logger.info(f"临时产品使用次数已更新: {temp_product.product_model} -> {temp_product.usage_count}")
        
        return jsonify({
            'success': True,
            'message': '使用次数已更新',
            'usage_count': temp_product.usage_count
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        logger.error(f'更新临时产品使用次数失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新使用次数失败: {str(e)}'
        }), 500


@quotation.route('/<int:id>/detail')
@login_required
@permission_required_with_approval_context('quotation', 'view')
def view_quotation(id):
    try:
        quotation = Quotation.query.get_or_404(id)
        if not can_view_quotation(current_user, quotation):
            logger.debug(f"{current_user.username} 无权访问报价单 {quotation.id}")
            flash(_('您没有权限查看此报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))
        # 按产品库分类体系排序获取报价单明细
        from app.models.product_code import ProductCategory, ProductSubcategory
        from sqlalchemy import case

        # 获取排序后的明细：分类 → 子分类 → 产品名称 → 型号 → 明细ID
        sorted_details = db.session.query(QuotationDetail)\
            .outerjoin(Product, Product.product_name == QuotationDetail.product_name)\
            .outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)\
            .outerjoin(ProductCategory, ProductSubcategory.category_id == ProductCategory.id)\
            .filter(QuotationDetail.quotation_id == quotation.id)\
            .order_by(
                case((Product.id.is_(None), 1), else_=0),  # 无对应产品的排在最后
                ProductCategory.id.asc(),  # 按业务顺序排序
                ProductSubcategory.display_order.asc(),
                ProductSubcategory.name.asc(),  # 使用子分类名称
                Product.model.asc(),
                QuotationDetail.id.asc()
            ).all()

        # 替换原有的details
        quotation.details = sorted_details

        # 查询可选新拥有人 - 使用协作用户公共函数
        all_users = []
        if can_change_quotation_owner(current_user, quotation):
            from app.utils.user_helpers import get_collaborative_users
            all_users = get_collaborative_users(current_user)
            # 确保包含当前归属人
            if quotation.owner_id not in {u.id for u in all_users}:
                owner_user = User.query.get(quotation.owner_id)
                if owner_user:
                    all_users = list(all_users) + [owner_user]
        has_change_owner_permission = can_change_quotation_owner(current_user, quotation)

        # 生成用户树状数据
        from app.utils.user_helpers import generate_user_tree_data_from_users
        user_tree_data = None
        if has_change_owner_permission:
            user_tree_data = generate_user_tree_data_from_users(all_users)
        
        # 获取审批实例信息
        approval_instance = get_object_approval_instance('quotation', quotation.id)
        current_approval_step = None
        can_current_user_approve = False
        
        if approval_instance:
            current_approval_step = get_current_step_info(approval_instance)
            can_current_user_approve = can_user_approve(approval_instance.id, current_user.id)
            
        # 检查具体权限
        can_edit_this_quotation = can_edit_data(quotation, current_user)
        from app.utils.access_control import can_delete_quotation
        can_delete_this_quotation = can_delete_quotation(current_user, quotation)

        # 检查结算单查看权限（用于批价单弹窗）
        from app.services.pricing_order_service import PricingOrderService
        can_view_settlement = PricingOrderService.can_view_settlement_tab(current_user)

        # 获取同项目的其他报价单（用于关联报价单列表）- 需要权限过滤
        related_quotations = []
        if quotation.project_id:
            all_related = Quotation.query.filter(
                Quotation.project_id == quotation.project_id,
                Quotation.id != quotation.id
            ).order_by(Quotation.updated_at.desc()).limit(20).all()
            # 过滤用户有权限查看的报价单
            related_quotations = [q for q in all_related if can_view_quotation(current_user, q)][:10]

        # 获取产品经理和解决方案经理列表（用于确认任务选择器）
        confirmation_candidates = User.query.filter(
            User.role.in_(['product_manager', 'solution_manager']),
            User._is_active == True
        ).order_by(User.real_name).all()
        role_display_map = {u.id: get_role_display_name(u.role) for u in confirmation_candidates}

        template_name = "quotation/tw_quotation_detail.html"

        # 为编辑模态框准备产品明细JSON数据
        quotation_details_json = '[]'
        if can_edit_this_quotation:
            import json
            # 批量反查 product_mn → Product.id 映射（用于货币切换时拉地区面价）
            non_temp_mns = list({
                str(getattr(d, 'product_mn', '') or '')
                for d in quotation.details
                if getattr(d, 'product_mn', None) and not str(d.product_mn).startswith('TEMP_')
            })
            product_mn_to_id = {}
            if non_temp_mns:
                from app.models.product import Product as _Product
                _products = _Product.query.filter(_Product.product_mn.in_(non_temp_mns)).all()
                product_mn_to_id = {p.product_mn: p.id for p in _products}

            details_for_edit = []
            for detail in quotation.details:
                try:
                    product_mn = str(getattr(detail, 'product_mn', '') or '')
                    is_temp_product = product_mn.startswith('TEMP_')
                    detail_data = {
                        'item_id': detail.id,  # 数据库ID，用于父子关系映射
                        'row_type': str(getattr(detail, 'row_type', 'product') or 'product'),
                        'section_label': str(getattr(detail, 'section_label', '') or ''),
                        'sort_order': getattr(detail, 'sort_order', None),
                        'product_id': product_mn_to_id.get(product_mn),  # 反查 Product.id，用于货币切换拉地区面价
                        'product_name': str(detail.product_name or ''),
                        'product_model': str(detail.product_model or ''),
                        'product_desc': str(detail.product_desc or ''),
                        'brand': str(detail.brand or ''),
                        'unit': str(detail.unit or '个'),
                        'market_price': float(detail.market_price or 0),
                        'discount_rate': float(detail.discount * 100 if detail.discount is not None else 100.0),
                        'unit_price': float(detail.unit_price or 0),
                        'quantity': int(detail.quantity or 1),
                        'subtotal': float(detail.total_price or 0),
                        'product_mn': product_mn,
                        'is_temp': is_temp_product,
                        # 父子关系字段
                        'is_accessory': bool(getattr(detail, 'is_accessory', False)),
                        'parent_item_id': getattr(detail, 'parent_item_id', None),
                        'config_type': str(getattr(detail, 'config_type', '') or ''),
                        'config_base_quantity': getattr(detail, 'config_base_quantity', None),
                        'quantity_synced': bool(getattr(detail, 'quantity_synced', True) if getattr(detail, 'quantity_synced', None) is not None else True),
                        'item_note': str(getattr(detail, 'item_note', '') or ''),
                    }
                    details_for_edit.append(detail_data)
                except Exception as detail_err:
                    current_app.logger.warning(f"处理明细数据出错: {detail_err}")
            try:
                quotation_details_json = json.dumps(details_for_edit)
            except Exception as json_err:
                current_app.logger.error(f"JSON序列化失败: {json_err}")
                quotation_details_json = '[]'

        # 查询当前报价单的"进行中"批价单（草稿或待审批状态）
        active_pricing_order = None
        from app.models.pricing_order import PricingOrder
        active_pricing_order = PricingOrder.query.filter(
                PricingOrder.quotation_id == quotation.id,
                PricingOrder.status.in_(['draft', 'pending'])
            ).order_by(PricingOrder.created_at.desc()).first()

        return render_template(template_name,
                             quotation=quotation,
                             all_users=all_users,
                             has_change_owner_permission=has_change_owner_permission,
                             user_tree_data=user_tree_data,
                             approval_instance=approval_instance,
                             current_approval_step=current_approval_step,
                             can_current_user_approve=can_current_user_approve,
                             can_edit_this_quotation=can_edit_this_quotation,
                             can_delete_this_quotation=can_delete_this_quotation,
                             can_view_settlement=can_view_settlement,
                             related_quotations=related_quotations,
                             quotation_details_json=quotation_details_json,
                             currency_options=get_available_quotation_currencies(),
                             default_currency=quotation.currency or Config.DEFAULT_CURRENCY,
                             active_pricing_order=active_pricing_order,
                             confirmation_candidates=confirmation_candidates,
                             role_display_map=role_display_map,
                             user_letterhead=getattr(current_user, 'quotation_letterhead', None) or {},
                             user_signature=getattr(current_user, 'quotation_signature', None) or {})
    except Exception as e:
        import traceback
        logger.error(f"加载报价单详情失败: {str(e)}\n{traceback.format_exc()}")
        flash(_('加载报价单详情失败：%s') % str(e), 'danger')
        return redirect(url_for('quotation.list_quotations'))

@quotation.route('/get_quotation_details/<int:id>')
@login_required
def get_quotation_details(id):
    try:
        quotation = Quotation.query.get_or_404(id)
        if not can_view_quotation(current_user, quotation):
            logger.debug(f"{current_user.username} 无权访问报价单 {quotation.id}")
            return jsonify({'success': False, 'error': '无权访问此报价单'}), 403
        # 处理报价单明细数据
        details = []
        detail_errors = []
        
        for detail in quotation.details:
            try:
                # 确保total_price映射到subtotal
                subtotal = detail.total_price if detail.total_price is not None else 0
                # 确保discount映射到discount_rate（转换为百分比）
                discount_rate = detail.discount * 100 if detail.discount is not None else 100.0
                # 确保正确设置product_mn字段
                product_mn = ''
                if hasattr(detail, 'product_mn') and detail.product_mn:
                    product_mn = detail.product_mn
                else:
                    # 尝试从产品表中获取MN号（使用公共辅助函数）
                    try:
                        product = find_product_by_name_and_model(detail.product_name, detail.product_model)
                        if product:
                            product_mn = product.product_mn
                    except Exception as product_error:
                        current_app.logger.error(f"获取产品MN号失败: {str(product_error)}")
                
                # 安全地转换数值字段
                try:
                    market_price = float(detail.market_price) if detail.market_price is not None else 0
                except (ValueError, TypeError):
                    market_price = 0
                    current_app.logger.error(f"市场价格格式错误: {detail.market_price}")
                
                try:
                    unit_price = float(detail.unit_price) if detail.unit_price is not None else 0
                except (ValueError, TypeError):
                    unit_price = 0
                    current_app.logger.error(f"单价格式错误: {detail.unit_price}")
                
                try:
                    subtotal_value = float(subtotal) if subtotal is not None else 0
                except (ValueError, TypeError):
                    subtotal_value = 0
                    current_app.logger.error(f"小计格式错误: {subtotal}")
                
                detail_data = {
                    'product_name': detail.product_name or '',
                    'product_model': detail.product_model or '',
                    'product_desc': detail.product_desc or '',
                    'brand': detail.brand or '',
                    'unit': detail.unit or '',
                    'market_price': market_price,
                    'discount_rate': float(discount_rate),
                    'quantity': detail.quantity or 1,
                    'product_mn': product_mn
                }
                
                # 如果不是产品经理角色，添加单价和小计字段
                if current_user.role not in ['product_manager', 'product']:
                    detail_data['unit_price'] = unit_price
                    detail_data['subtotal'] = subtotal_value
                
                details.append(detail_data)
            except Exception as detail_error:
                # 记录明细处理错误但继续处理其他明细
                error_message = f"处理报价单明细错误: {str(detail_error)}"
                current_app.logger.error(error_message)
                detail_errors.append(error_message)
        
        # 安全获取总金额
        try:
            total_amount = float(quotation.amount) if quotation.amount is not None else 0
        except (ValueError, TypeError):
            total_amount = 0
            current_app.logger.error(f"总金额格式错误: {quotation.amount}")
        
        response_data = {
            'success': True, 
            'details': details,
            'total_amount': total_amount
        }
        
        # 如果有错误，添加到响应中，但不影响整体成功状态
        if detail_errors:
            response_data['warnings'] = detail_errors
            
        return jsonify(response_data)
    except Exception as e:
        current_app.logger.error(f"获取报价单明细时出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@quotation.route('/<int:id>/api/history')
@login_required
def get_quotation_history(id):
    """获取报价单变更历史"""
    try:
        quotation = Quotation.query.get_or_404(id)

        # 权限检查
        if not can_view_quotation(current_user, quotation):
            return jsonify({'success': False, 'message': '无权访问此报价单'}), 403

        from app.models.change_log import ChangeLog

        # 允许的字段（新键名 + 兼容旧中文数据）
        ALLOWED_FIELDS = {'amount', 'details_count', '报价金额', '明细数量'}

        # 键名到中文msgid的映射（用于_()翻译）
        FIELD_LABEL = {
            'amount': '报价金额',
            'details_count': '明细数量',
            'details': '产品明细',
        }
        DESC_LABEL = {
            'amount_changed': '修改了报价金额',
            'details_count_changed': '修改了产品明细',
            'details_changed': '修改了产品配置',
        }

        history = ChangeLog.get_record_history('quotation', 'quotations', id)

        # 过滤 + 翻译
        filtered_data = []
        for h in history:
            if h.field_name == 'detail_deleted':
                # 再确认时删除的产品:old_value = "产品名 ×数量",走删除线展示,description 仅作标题
                filtered_data.append({
                    'id': h.id,
                    'field_name': _('删除产品'),
                    'old_value': h.old_value,
                    'new_value': '',
                    'user_name': h.user_name,
                    'created_at': h.created_at.strftime('%m-%d %H:%M') if h.created_at else '',
                    'description': _('删除产品')
                })
            elif h.field_name in ALLOWED_FIELDS:
                # 获取中文msgid，然后用_()翻译
                field_label = FIELD_LABEL.get(h.field_name, h.field_name)
                desc_label = DESC_LABEL.get(h.description, h.description) if h.description else field_label

                filtered_data.append({
                    'id': h.id,
                    'field_name': _(field_label),
                    'old_value': h.old_value,
                    'new_value': h.new_value,
                    'user_name': h.user_name,
                    'created_at': h.created_at.strftime('%m-%d %H:%M') if h.created_at else '',
                    'description': _(desc_label)
                })

        return jsonify({'success': True, 'data': filtered_data})
    except Exception as e:
        current_app.logger.error(f"获取报价单变更历史时出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@quotation.route('/<int:id>/save', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以保存自己的报价单
def save_quotation(id):
    try:
        quotation = Quotation.query.get_or_404(id)

        # 使用统一的数据权限检查（包含数据归属逻辑）
        if not can_edit_data(quotation, current_user):
            return jsonify({
                'status': 'error',
                'message': '您没有权限编辑此报价单'
            }), 403
        
        # 检查报价单是否被锁定 — SM 确认被指派人绕过(他们需要核查时调整)
        if quotation.is_locked:
            from app.models.quotation_confirmation_task import QuotationConfirmationTask
            _is_pending_assignee = QuotationConfirmationTask.query.filter_by(
                quotation_id=quotation.id, assignee_id=current_user.id, status='pending'
            ).first() is not None
            if not _is_pending_assignee:
                lock_info = quotation.lock_status_display
                return jsonify({
                    'status': 'error',
                    'message': f'报价单已被锁定，无法编辑。锁定原因:{lock_info["reason"]}，锁定人:{lock_info["locked_by"]}'
                }), 403
        
        # 捕获修改前的值
        from app.utils.change_tracker import ChangeTracker
        old_values = ChangeTracker.capture_old_values(quotation)

        # 专门捕获关键字段用于变更历史显示
        old_amount = quotation.amount or 0
        old_details_count = len(quotation.details) if quotation.details else 0
        old_product_signature = quotation.calculate_product_signature()

        # 再确认变更高亮:保存会"删旧建新"明细,故在此(清空前)按 MN 留存旧行
        # {mn: {name, qty, flag}},用于重建后给"自上次确认以来新增/替换的行"打标 + 删除写历史。
        # 仅当报价单已(再)确认过才有意义。
        _was_confirmed = quotation.confirmation_badge_status in ('confirmed', 'reconfirm')
        _old_detail_map = {}
        if _was_confirmed:
            for _d in quotation.details:
                if _d.product_mn and _d.row_type != 'section':
                    _old_detail_map[_d.product_mn] = {
                        'name': _d.product_name or _d.product_mn,
                        'qty': _d.quantity or 0,
                        'flag': bool(getattr(_d, 'is_reconfirm_change', False)),
                    }

        # 使用 request.get_json() 获取JSON数据
        data = request.get_json()
        
        # 记录请求数据结构
        current_app.logger.debug(f"请求数据结构: {data.keys() if isinstance(data, dict) else '非字典数据'}")
        
        # 验证数据是否为空
        if not data:
            current_app.logger.error("请求数据为空或格式错误")
            return jsonify({
                'status': 'error',
                'message': '请求数据为空或格式错误'
            }), 400
        
        # 验证项目ID
        if not data.get('project_id'):
            current_app.logger.error("请求数据中缺少project_id字段")
            return jsonify({
                'status': 'error',
                'message': '项目不能为空'
            }), 400
        
        # 日志记录详细的请求数据
        current_app.logger.info(f"项目ID验证 - 请求中的project_id: {data.get('project_id')}, 类型: {type(data.get('project_id'))}")
        
        # 确保项目ID是整数
        try:
            project_id = int(data.get('project_id'))
            current_app.logger.info(f"处理后的project_id: {project_id}")
            
            # 验证项目是否存在
            project = Project.query.get(project_id)
            if not project:
                current_app.logger.error(f"项目ID {project_id} 不存在")
                return jsonify({
                    'status': 'error',
                    'message': 'ID为%s的项目不存在' % project_id
                }), 400
                
            # 设置报价单的项目ID
            quotation.project_id = project_id
            current_app.logger.info(f"设置报价单项目ID: {project_id}")
        except (ValueError, TypeError) as e:
            current_app.logger.error(f"项目ID类型转换错误: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': '项目ID格式错误，必须是整数'
            }), 400
        
        # 获取总金额，确保是有效的数值
        try:
            total_amount = float(data.get('total_amount', 0))
            current_app.logger.debug(f'解析到的总金额: {total_amount}')
            
            if total_amount < 0:
                current_app.logger.warning(f"总金额为负数: {total_amount}，已设置为0")
                total_amount = 0
        except (ValueError, TypeError) as amount_error:
            current_app.logger.error(f"解析总金额失败: {str(amount_error)}, 原始值: {data.get('total_amount')}")
            return jsonify({
                'status': 'error',
                'message': '总金额格式错误: %s' % str(amount_error)
            }), 400
        
        # 更新报价单基本信息 - 直接使用前端传来的总金额
        quotation.amount = total_amount
        quotation.currency = data.get('currency', Config.DEFAULT_CURRENCY)  # 添加货币字段更新
        quotation.notes = data.get('notes', '') or ''
        # 公司主体（多公司报价）
        if data.get('entity_id'):
            try: quotation.entity_id = int(data.get('entity_id'))
            except (ValueError, TypeError): pass
        # 非结构化字段（payment_terms/shipping_terms/validity/ref_no 等）
        if 'extra_fields' in data and isinstance(data.get('extra_fields'), dict):
            quotation.extra_fields = data.get('extra_fields') or {}
        # 税率(0-100 浮点,整张报价共用,合计 = 小计 × (1 + tax_rate/100))
        if 'tax_rate' in data:
            try:
                quotation.tax_rate = float(data.get('tax_rate') or 0)
            except (ValueError, TypeError):
                pass
        # 手动更新时间戳，确保updated_at字段正确
        quotation.updated_at = datetime.utcnow()
        current_app.logger.info(f'直接保存前端总金额到报价单: {total_amount}, 货币: {quotation.currency}')
        
        # 临时禁用事件监听器，避免删除重建过程中触发不必要的签名变化
        try:
            event.remove(QuotationDetail, 'after_insert', update_quotation_implant_total)
            event.remove(QuotationDetail, 'after_update', update_quotation_implant_total)
            event.remove(QuotationDetail, 'after_delete', update_quotation_implant_total)
        except Exception:
            # 如果监听器不存在，忽略错误
            pass
        
        try:
            # 先删除原有明细项
            try:
                old_details_count = QuotationDetail.query.filter_by(quotation_id=id).count()
                current_app.logger.debug(f'准备删除原有明细项，数量: {old_details_count}')
                
                for detail in quotation.details:
                    db.session.delete(detail)
                quotation.details.clear()
                current_app.logger.debug('成功删除原有明细项')
            except Exception as delete_error:
                current_app.logger.error(f"删除原有明细项失败: {str(delete_error)}")
                return jsonify({
                    'status': 'error',
                    'message': f'删除原有明细项失败: {str(delete_error)}'
                }), 500
            
            # 添加新的明细项（使用公共函数）
            details = data.get('details', [])

            if not details:
                current_app.logger.warning("报价单没有明细项")
                return jsonify({
                    'status': 'error',
                    'message': '报价单必须包含至少一个明细项'
                }), 400

            if not isinstance(details, list):
                current_app.logger.error(f'明细项不是列表格式: {type(details)}')
                return jsonify({
                    'status': 'error',
                    'message': '明细项必须是数组格式'
                }), 400

            # 为自建产品（source='custom'）批量分配 MN
            from app.utils.product_helpers import assign_custom_product_mns
            assign_custom_product_mns(details)

            current_app.logger.debug(f'开始处理 {len(details)} 个明细项')

            # 使用公共函数处理明细（包含父子关系）
            created_details, detail_errors = process_quotation_details(
                quotation_id=id,
                details=details,
                currency=data.get('currency', Config.DEFAULT_CURRENCY)
            )

            # 添加到报价单
            for detail_obj in created_details:
                quotation.details.append(detail_obj)

            # 计算植入总额
            try:
                quotation.calculate_implant_total_amount()
                current_app.logger.debug(f'计算植入总额完成: {quotation.implant_total_amount}')
            except Exception as implant_error:
                current_app.logger.error(f"计算植入总额失败: {str(implant_error)}")
            
            # 提交更改（在事件监听器被禁用的情况下）
            try:
                current_app.logger.info('准备提交所有更改到数据库...')
                db.session.commit()
                current_app.logger.info('数据库更改提交成功')

                # 处理需要创建新研发产品的明细项
                try:
                    created_products = create_products_from_configured_specs(quotation)
                    if created_products:
                        current_app.logger.info(f'报价单 {quotation.id} 保存时创建了 {len(created_products)} 个研发产品')
                except Exception as create_err:
                    current_app.logger.error(f'创建研发产品失败: {str(create_err)}')
                    # 不影响报价单保存成功

                # commit 后检测签名变化并更新确认状态
                try:
                    new_product_signature = quotation.calculate_product_signature()
                    if old_product_signature and new_product_signature != old_product_signature:
                        if quotation.confirmation_badge_status == 'confirmed':
                            # 已确认后改了产品配置 → 置「需再次确认」(reconfirm),提示需重新技术确认
                            quotation.confirmation_badge_status = 'reconfirm'
                            quotation.confirmation_badge_color = '#f59e0b'
                            current_app.logger.info(f"报价单 {quotation.id} 配置变更，确认状态置为 reconfirm")
                            # 记入变更历史
                            try:
                                from app.models.change_log import ChangeLog
                                ChangeLog.log_update(
                                    module_name='quotation', table_name='quotations',
                                    record_id=quotation.id, field_name='confirmation',
                                    old_value='confirmed', new_value='reconfirm',
                                    user_id=current_user.id,
                                    user_name=(current_user.real_name or current_user.username),
                                    description='confirm_reconfirm', ip_address=request.remote_addr)
                            except Exception:
                                pass

                    # 再确认变更高亮:对已(再)确认报价,标记自上次确认以来"新增/替换(MN变化)"的行;
                    # 删除的产品(旧集有、新集无)写入变更历史(产品名 ×数量)。仅产品(MN)增删换计入。
                    if _was_confirmed and old_product_signature and new_product_signature != old_product_signature:
                        new_mn_set = set()
                        for _d in quotation.details:
                            if _d.product_mn and _d.row_type != 'section':
                                new_mn_set.add(_d.product_mn)
                                # 新增(不在旧集) 或 旧行本就带标记(粘性,始终对齐到上次确认)
                                if (_d.product_mn not in _old_detail_map) or _old_detail_map[_d.product_mn]['flag']:
                                    _d.is_reconfirm_change = True
                        try:
                            from app.models.change_log import ChangeLog
                            for _mn, _info in _old_detail_map.items():
                                if _mn not in new_mn_set:
                                    ChangeLog.log_update(
                                        module_name='quotation', table_name='quotations',
                                        record_id=quotation.id, field_name='detail_deleted',
                                        old_value=f"{_info['name']} ×{_info['qty']}", new_value='',
                                        user_id=current_user.id,
                                        user_name=(current_user.real_name or current_user.username),
                                        description='detail_deleted', ip_address=request.remote_addr)
                        except Exception:
                            pass

                    quotation.product_signature = new_product_signature
                    db.session.commit()
                except Exception as sig_err:
                    current_app.logger.warning(f"签名检测失败: {str(sig_err)}")

                # reconfirm 后由 owner 在 UI 上手动点"技术确认"按钮重新选 SM 并发起,
                # 这里不再自动批量创建任务(原逻辑会给全公司 SM 都建 pending,
                # 导致按钮被 sm_pending 条件挡掉,与新流程冲突)

            except Exception as commit_error:
                db.session.rollback()
                error_type = type(commit_error).__name__
                current_app.logger.error(f"提交更改时出错: {error_type} - {str(commit_error)}")
                return jsonify({
                    'status': 'error',
                    'message': f'保存失败: {error_type} - {str(commit_error)}'
                }), 500
                    
        finally:
            # 确保事件监听器在任何情况下都能恢复
            try:
                # 安全地重新注册事件监听器
                if not event.contains(QuotationDetail, 'after_insert', update_quotation_implant_total):
                    event.listen(QuotationDetail, 'after_insert', update_quotation_implant_total)
                if not event.contains(QuotationDetail, 'after_update', update_quotation_implant_total):
                    event.listen(QuotationDetail, 'after_update', update_quotation_implant_total)
                if not event.contains(QuotationDetail, 'after_delete', update_quotation_implant_total):
                    event.listen(QuotationDetail, 'after_delete', update_quotation_implant_total)
                current_app.logger.debug("事件监听器已安全恢复")
            except Exception as restore_error:
                current_app.logger.error(f"恢复事件监听器时出错: {str(restore_error)}")
        
        # 记录变更历史（使用专门的格式化记录）
        try:
            from app.models.change_log import ChangeLog

            new_amount = quotation.amount or 0
            new_details_count = len(quotation.details) if quotation.details else 0
            user_name = current_user.real_name or current_user.username

            # 记录金额变更（使用键名，读取时翻译）
            if abs(old_amount - new_amount) > 0.01:  # 允许小数点误差
                ChangeLog.log_update(
                    module_name='quotation',
                    table_name='quotations',
                    record_id=quotation.id,
                    field_name='amount',
                    old_value=f'{old_amount:,.2f}',
                    new_value=f'{new_amount:,.2f}',
                    user_id=current_user.id,
                    user_name=user_name,
                    description='amount_changed',
                    ip_address=request.remote_addr
                )

            # 去泛化(2026-06-26):不再写"明细数量"(details_count)与"修改了产品配置"(details)
            # 两条泛化历史 —— 产品删除已有具体"删除产品 X×N"条目、新增靠明细行高亮、价格走
            # "报价金额"条目,泛化条目对用户冗余。仅保留金额 + 删除产品 + 再确认。

            db.session.commit()
            current_app.logger.info(f"报价单 {quotation.id} 变更历史已记录")
        except Exception as track_err:
            current_app.logger.warning(f"记录报价单变更历史失败: {str(track_err)}")
        
        # 项目金额缓存由 after_update 事件监听器自动刷新，无需手动处理

        record_activity('edit', 'quotation', quotation.quotation_number, current_user,
            project_id=quotation.project_id, customer_id=quotation.customer_id,
            description=f'编辑报价单 {quotation.quotation_number}')

        # 快速返回成功响应
        if detail_errors:
            current_app.logger.warning(f"报价单保存成功，但有以下警告: {', '.join(detail_errors)}")
            response_data = {
                'status': 'success',
                'message': '报价单更新成功',
                'warnings': detail_errors,
                'quotation_id': id
            }
            
            return jsonify(response_data), 200
        
        current_app.logger.info('报价单更新成功，无警告信息')
        response_data = {
            'status': 'success',
            'message': '报价单更新成功',
            'quotation_id': id
        }
        
        return jsonify(response_data)
                
    except Exception as e:
        error_type = type(e).__name__
        current_app.logger.exception(f'处理POST请求时发生错误: {error_type}')
        return jsonify({
            'status': 'error',
            'message': '%s: %s' % (error_type, str(e))
        }), 500

@quotation.route('/<int:id>/change_owner', methods=['POST'])
@login_required
@permission_required('quotation', 'edit')
def change_quotation_owner(id):
    quotation = Quotation.query.get_or_404(id)
    if not can_change_quotation_owner(current_user, quotation):
        flash(_('您没有权限修改该报价单的拥有人'), 'danger')
        return redirect(url_for('quotation.view_quotation', id=id))
    new_owner_id = request.form.get('new_owner_id', type=int)
    if not new_owner_id:
        flash(_('请选择新的拥有人'), 'danger')
        return redirect(url_for('quotation.view_quotation', id=id))
    from app.models.user import User
    new_owner = User.query.get(new_owner_id)
    if not new_owner:
        flash(_('新拥有人不存在'), 'danger')
        return redirect(url_for('quotation.view_quotation', id=id))
    quotation.owner_id = new_owner_id
    db.session.commit()

    flash(_('报价单拥有人已更新'), 'success')
    return redirect(url_for('quotation.view_quotation', id=id))


# 注意：can_view_quotation 函数已移至 app/utils/access_control.py
# 通过顶部 import 引入，确保全局使用统一的权限检查逻辑
@quotation.route('/detail/<int:detail_id>/toggle_confirmation', methods=['POST'])
@login_required
def toggle_detail_confirmation(detail_id):
    """切换产品明细的确认状态 - 需要报价单编辑权限"""
    try:
        # 检查权限 - 使用权限配置系统
        # 注：确认状态操作权限通过 quotation 模块的编辑权限控制
        # 需要在权限配置中为相关角色启用 quotation.edit 权限
        from app.permissions import is_admin_or_ceo
        if not is_admin_or_ceo() and not current_user.has_permission('quotation', 'edit'):
            return jsonify({
                'success': False,
                'message': '权限不足，您没有报价单编辑权限'
            }), 403
        
        # 查找产品明细
        detail = QuotationDetail.query.get_or_404(detail_id)
        
        # 检查报价单是否可编辑（锁定状态检查）
        if detail.quotation.is_locked:
            return jsonify({
                'success': False,
                'message': '报价单已被锁定，无法修改确认状态'
            }), 400
        
        # 暂时使用会话存储确认状态，避免数据库字段依赖
        session_key = f'detail_confirmation_{detail_id}'
        current_status = session.get(session_key, False)
        
        # 切换确认状态
        if current_status:
            # 取消确认
            session[session_key] = False
            action = 'unconfirmed'
            message = '已取消确认'
        else:
            # 确认
            session[session_key] = True
            action = 'confirmed'
            message = '已确认'
        
        return jsonify({
            'success': True,
            'message': message,
            'action': action,
            'is_confirmed': session[session_key],
            'confirmed_by': current_user.real_name or current_user.username,
            'confirmed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'操作失败：{str(e)}'
        }), 500

@quotation.route('/<int:quotation_id>/toggle_product_detail_confirmation', methods=['POST'])
@login_required
def toggle_product_detail_confirmation(quotation_id):
    """切换报价单产品明细的整体确认状态 - 只有解决方案经理和admin可以操作"""
    try:
        # 检查权限
        if current_user.role not in ['solution_manager', 'admin']:
            return jsonify({
                'success': False,
                'message': '权限不足，只有解决方案经理和管理员可以操作确认状态'
            }), 403
        
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查报价单是否可编辑（锁定状态检查）
        if quotation.is_locked:
            return jsonify({
                'success': False,
                'message': '报价单已被锁定，无法修改确认状态'
            }), 400
        
        # 使用数据库确认徽章字段而不是会话存储
        current_status = quotation.confirmation_badge_status == 'confirmed'
        
        # 切换确认状态
        if current_status:
            # 取消确认
            quotation.clear_confirmation_badge()
            action = 'unconfirmed'
            message = '已取消产品明细确认'
        else:
            # 确认 - 使用绿色徽章
            quotation.set_confirmation_badge('#28a745', current_user.id)
            action = 'confirmed'
            message = '已确认产品明细'

        # 确认时同步完成待办任务
        if action == 'confirmed':
            from app.models.quotation_confirmation_task import QuotationConfirmationTask
            pending_task = QuotationConfirmationTask.query.filter_by(
                quotation_id=quotation_id,
                assignee_id=current_user.id,
                status='pending'
            ).first()
            if pending_task:
                pending_task.status = 'confirmed'
                pending_task.confirmed_at = datetime.now()

        # 保存到数据库
        db.session.commit()

        # 确认时记录到日历工作项（同一天同一报价单只记录一次）
        if action == 'confirmed':
            record_activity('confirm', 'quotation', quotation.quotation_number, current_user,
                project_id=quotation.project_id, customer_id=quotation.customer_id,
                description=f'报价单确认 {quotation.quotation_number}')

            # 将确认人加入项目共享（支持人员）
            try:
                project = quotation.project
                if project and current_user.id != project.owner_id:
                    shared = project.shared_with_users or []
                    if current_user.id not in shared:
                        project.shared_with_users = shared + [current_user.id]
                        project.share_enabled = True
                        db.session.commit()
            except Exception as share_err:
                current_app.logger.warning(f"添加项目共享人员失败: {str(share_err)}")

        # 记录确认信息
        confirmed_by = current_user.real_name or current_user.username
        confirmed_at = quotation.confirmed_at.strftime('%Y-%m-%d %H:%M') if quotation.confirmed_at else None

        return jsonify({
            'success': True,
            'message': message,
            'action': action,
            'is_confirmed': quotation.confirmation_badge_status == 'confirmed',
            'confirmed_by': confirmed_by if quotation.confirmation_badge_status == 'confirmed' else None,
            'confirmed_at': confirmed_at if quotation.confirmation_badge_status == 'confirmed' else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'操作失败：{str(e)}'
        }), 500

@quotation.route('/<int:quotation_id>/product_detail_confirmation_status', methods=['GET'])
@login_required
def get_product_detail_confirmation_status(quotation_id):
    """获取报价单产品明细的确认状态"""
    try:
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            return jsonify({
                'success': False,
                'message': '权限不足，无法查看该报价单'
            }), 403
        
        # 从数据库获取确认状态
        is_confirmed = quotation.confirmation_badge_status == 'confirmed'
        
        # 获取确认信息
        confirmed_by = None
        confirmed_at = None
        
        if is_confirmed and quotation.confirmer:
            confirmed_by = quotation.confirmer.real_name or quotation.confirmer.username
            confirmed_at = quotation.confirmed_at.strftime('%Y-%m-%d %H:%M') if quotation.confirmed_at else None
        
        return jsonify({
            'success': True,
            'is_confirmed': is_confirmed,
            'confirmed_by': confirmed_by,
            'confirmed_at': confirmed_at
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取状态失败：{str(e)}'
        }), 500

# ========== 产品确认待办任务 API ==========

@quotation.route('/<int:quotation_id>/confirmation-tasks', methods=['POST'])
@login_required
def create_confirmation_tasks(quotation_id):
    """创建产品确认待办任务"""
    try:
        quotation_obj = Quotation.query.get_or_404(quotation_id)

        if not can_view_quotation(current_user, quotation_obj):
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 只有报价单创建者才能发起确认请求
        if quotation_obj.owner_id != current_user.id:
            return jsonify({'success': False, 'message': '只有报价单创建者才能请求确认'}), 403

        if quotation_obj.is_locked:
            return jsonify({'success': False, 'message': '报价单已被锁定'}), 400

        data = request.get_json() or {}
        assignee_ids = data.get('assignee_ids', [])
        message_text = data.get('message', '')
        due_date_str = data.get('due_date')

        if not assignee_ids:
            return jsonify({'success': False, 'message': '请选择至少一个确认人'}), 400

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'message': '日期格式无效'}), 400

        from app.models.quotation_confirmation_task import QuotationConfirmationTask
        from app.models.worklog import WorkItem
        from app.models.message import Message

        created_count = 0
        for uid in assignee_ids:
            user = User.query.get(uid)
            if not user:
                continue

            # 检查是否已有pending任务
            existing = QuotationConfirmationTask.query.filter_by(
                quotation_id=quotation_id,
                assignee_id=uid,
                status='pending'
            ).first()
            if existing:
                continue

            # 创建WorkItem日程
            work_item = WorkItem(
                title=f'报价单确认: {quotation_obj.quotation_number}',
                description=message_text or f'请确认报价单 {quotation_obj.quotation_number} 的产品选型和配置清单',
                planned_date=datetime.now(ZoneInfo('Asia/Shanghai')).date(),
                end_date=due_date.date() if due_date else None,
                is_all_day=True,
                work_type='presales_support',
                status='planned',
                owner_id=uid,
                project_id=quotation_obj.project_id
            )
            db.session.add(work_item)
            db.session.flush()  # 获取work_item.id

            # 创建确认任务
            task = QuotationConfirmationTask(
                quotation_id=quotation_id,
                assignee_id=uid,
                requester_id=current_user.id,
                message=message_text,
                due_date=due_date,
                workitem_id=work_item.id
            )
            db.session.add(task)

            # 发送消息通知
            msg = Message.create_confirmation_request(
                sender_id=current_user.id,
                recipient_id=uid,
                quotation=quotation_obj,
                message_text=message_text
            )
            db.session.add(msg)
            created_count += 1

        # 更新报价单确认状态为 pending + 锁定报价单(避免发起后还能改)
        if created_count > 0:
            quotation_obj.confirmation_badge_status = 'pending'
            quotation_obj.confirmation_badge_color = '#f97316'
            quotation_obj.product_signature = quotation_obj.calculate_product_signature()
            quotation_obj.lock('产品确认中', current_user.id)

        db.session.commit()

        # 查询当前进度
        all_tasks = QuotationConfirmationTask.query.filter_by(
            quotation_id=quotation_id
        ).filter(QuotationConfirmationTask.status.in_(['pending', 'confirmed'])).all()
        confirmed_count = sum(1 for t in all_tasks if t.status == 'confirmed')

        return jsonify({
            'success': True,
            'task_count': created_count,
            'confirmed': confirmed_count,
            'total': len(all_tasks)
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'创建确认任务失败: {str(e)}')
        return jsonify({'success': False, 'message': f'操作失败：{str(e)}'}), 500


@quotation.route('/<int:quotation_id>/confirmation-tasks/confirm', methods=['POST'])
@login_required
def confirm_quotation_task(quotation_id):
    """PM/SE确认产品选型"""
    try:
        quotation_obj = Quotation.query.get_or_404(quotation_id)

        if not can_view_quotation(current_user, quotation_obj):
            return jsonify({'success': False, 'message': '权限不足'}), 403

        from app.models.quotation_confirmation_task import QuotationConfirmationTask
        from app.models.message import Message

        # 查找当前用户的pending任务
        task = QuotationConfirmationTask.query.filter_by(
            quotation_id=quotation_id,
            assignee_id=current_user.id,
            status='pending'
        ).first()

        if not task:
            return jsonify({'success': False, 'message': '未找到待确认的任务'}), 404

        # 标记任务完成
        now = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
        task.status = 'confirmed'
        task.confirmed_at = now

        # 标记对应的 confirmation_request 消息为已读
        conf_msg = Message.query.filter_by(
            recipient_id=current_user.id,
            related_object_type='quotation',
            related_object_id=quotation_id,
            message_type='confirmation_request',
            is_read=False
        ).first()
        if conf_msg:
            conf_msg.is_read = True
            conf_msg.read_at = now

        # 完成关联的WorkItem
        if task.workitem:
            task.workitem.status = 'completed'
            task.workitem.completed_at = now

        # 检查是否全部确认
        all_tasks = QuotationConfirmationTask.query.filter_by(
            quotation_id=quotation_id
        ).filter(QuotationConfirmationTask.status.in_(['pending', 'confirmed'])).all()
        confirmed_count = sum(1 for t in all_tasks if t.status == 'confirmed')
        total = len(all_tasks)
        all_confirmed = confirmed_count == total

        if all_confirmed:
            # 全部确认完成，更新报价单状态 + 解锁(后续若改动 → reconfirm 流程)
            quotation_obj.set_confirmation_badge('#28a745', current_user.id)
            quotation_obj.unlock(current_user.id)
            # 通知发起人
            requester_ids = set(t.requester_id for t in all_tasks)
            for req_id in requester_ids:
                msg = Message.create_confirmation_completed(
                    sender_id=current_user.id,
                    recipient_id=req_id,
                    quotation=quotation_obj
                )
                db.session.add(msg)

        db.session.commit()

        # 记录到日历工作项（同一天同一报价单只记录一次）
        record_activity('confirm', 'quotation', quotation_obj.quotation_number, current_user,
            project_id=quotation_obj.project_id, customer_id=quotation_obj.customer_id,
            description=f'报价单确认 {quotation_obj.quotation_number}')

        # 将确认人加入项目共享（支持人员）
        try:
            project = quotation_obj.project
            if project and current_user.id != project.owner_id:
                shared = project.shared_with_users or []
                if current_user.id not in shared:
                    project.shared_with_users = shared + [current_user.id]
                    project.share_enabled = True
                    db.session.commit()
        except Exception as share_err:
            current_app.logger.warning(f"添加项目共享人员失败: {str(share_err)}")

        return jsonify({
            'success': True,
            'all_confirmed': all_confirmed,
            'confirmed': confirmed_count,
            'total': total
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'确认任务失败: {str(e)}')
        return jsonify({'success': False, 'message': f'操作失败：{str(e)}'}), 500


@quotation.route('/<int:quotation_id>/confirmation-tasks', methods=['DELETE'])
@login_required
def recall_confirmation_tasks(quotation_id):
    """召回:发起人撤销已发出的确认请求 — 删 pending 任务 + WorkItem + 解锁 + 通知被指派人"""
    try:
        quotation_obj = Quotation.query.get_or_404(quotation_id)
        if quotation_obj.owner_id != current_user.id:
            return jsonify({'success': False, 'message': '只有发起人可以召回'}), 403

        from app.models.quotation_confirmation_task import QuotationConfirmationTask
        from app.models.message import Message

        pending_tasks = QuotationConfirmationTask.query.filter_by(
            quotation_id=quotation_id, status='pending'
        ).all()
        if not pending_tasks:
            return jsonify({'success': False, 'message': '没有待召回的任务'}), 404

        recalled_count = 0
        for task in pending_tasks:
            # 删除关联 WorkItem
            if task.workitem:
                db.session.delete(task.workitem)
            # 通知被指派人
            msg = Message(
                sender_id=current_user.id,
                recipient_id=task.assignee_id,
                message_type='confirmation_recalled',
                title=f'确认请求已召回:{quotation_obj.quotation_number}',
                related_object_type='quotation',
                related_object_id=quotation_id,
                content=f'报价单 {quotation_obj.quotation_number} 的确认请求已被发起人召回',
            )
            db.session.add(msg)
            db.session.delete(task)
            recalled_count += 1

        # 解锁 + badge 回 none
        quotation_obj.unlock(current_user.id)
        quotation_obj.confirmation_badge_status = 'none'
        quotation_obj.confirmation_badge_color = None
        db.session.commit()

        return jsonify({'success': True, 'recalled': recalled_count})
    except Exception as e:
        db.session.rollback()
        logger.error(f'召回确认请求失败: {str(e)}')
        return jsonify({'success': False, 'message': f'操作失败：{str(e)}'}), 500


@quotation.route('/<int:quotation_id>/confirmation-tasks/reject', methods=['POST'])
@login_required
def reject_quotation_task(quotation_id):
    """驳回:被指派人拒绝确认 — 标记任务 rejected + 解锁 + badge=rejected + 通知发起人"""
    try:
        quotation_obj = Quotation.query.get_or_404(quotation_id)
        if not can_view_quotation(current_user, quotation_obj):
            return jsonify({'success': False, 'message': '权限不足'}), 403

        data = request.get_json() or {}
        reason = (data.get('reason') or '').strip()
        if not reason:
            return jsonify({'success': False, 'message': '请填写驳回原因'}), 400

        from app.models.quotation_confirmation_task import QuotationConfirmationTask
        from app.models.message import Message

        task = QuotationConfirmationTask.query.filter_by(
            quotation_id=quotation_id, assignee_id=current_user.id, status='pending'
        ).first()
        if not task:
            return jsonify({'success': False, 'message': '未找到待确认的任务'}), 404

        now = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
        task.status = 'rejected'
        task.confirmed_at = now
        task.message = (task.message or '') + f'\n[驳回理由] {reason}'
        if task.workitem:
            task.workitem.status = 'completed'
            task.workitem.completed_at = now

        # 解锁报价单(发起人可改后重发)+ badge 切 rejected(保留驳回态供 UI 展示)
        quotation_obj.unlock(current_user.id)
        quotation_obj.confirmation_badge_status = 'rejected'
        quotation_obj.confirmation_badge_color = '#dc2626'

        # 通知发起人
        rejector = current_user.real_name or current_user.username
        msg = Message(
            sender_id=current_user.id,
            recipient_id=task.requester_id,
            message_type='confirmation_rejected',
            title=f'{rejector} 驳回了报价单:{quotation_obj.quotation_number}',
            related_object_type='quotation',
            related_object_id=quotation_id,
            content=f'报价单 {quotation_obj.quotation_number} 已被 {rejector} 驳回:{reason}',
        )
        db.session.add(msg)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f'驳回确认失败: {str(e)}')
        return jsonify({'success': False, 'message': f'操作失败：{str(e)}'}), 500


@quotation.route('/<int:quotation_id>/confirmation-tasks', methods=['GET'])
@login_required
def get_confirmation_tasks(quotation_id):
    """查询确认任务状态"""
    try:
        quotation_obj = Quotation.query.get_or_404(quotation_id)

        if not can_view_quotation(current_user, quotation_obj):
            return jsonify({'success': False, 'message': '权限不足'}), 403

        from app.models.quotation_confirmation_task import QuotationConfirmationTask

        tasks = QuotationConfirmationTask.query.filter_by(
            quotation_id=quotation_id
        ).filter(
            QuotationConfirmationTask.status.in_(['pending', 'confirmed'])
        ).order_by(QuotationConfirmationTask.created_at.desc()).all()

        confirmed_count = sum(1 for t in tasks if t.status == 'confirmed')
        total = len(tasks)

        # 检查当前用户是否有pending任务
        has_pending_task = any(
            t.assignee_id == current_user.id and t.status == 'pending'
            for t in tasks
        )

        return jsonify({
            'success': True,
            'tasks': [t.to_dict() for t in tasks],
            'confirmed': confirmed_count,
            'total': total,
            'all_confirmed': confirmed_count == total and total > 0,
            'has_pending_task': has_pending_task
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation.route('/export_pdf/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def export_pdf(quotation_id):
    """
    导出报价单PDF（浏览器内打开）

    URL参数:
        template: 模板类型，可选值：
            - 'ovs': 使用OVS Singapore模板
            - 'sp8d': 使用SP8D默认模板
            - 不传：根据数据库类型自动选择

    示例:
        /quotation/export_pdf/123?template=ovs
    """
    try:
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)

        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            flash(_('权限不足，无法导出该报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))

        # 获取模板类型参数
        template_type = request.args.get('template', None)
        if template_type and template_type not in ['ovs', 'sp8d']:
            template_type = None  # 无效参数时使用自动检测

        from app.services.evertac_quotation_pdf_generator import EvertacQuotationPDFGenerator

        # 生成PDF
        pdf_generator = EvertacQuotationPDFGenerator()
        pdf_result = pdf_generator.generate_quotation_pdf(quotation, template_type=template_type)
        pdf_content = pdf_result['content']
        filename = pdf_result['filename']
        
        # 返回PDF文件
        from flask import make_response
        from urllib.parse import quote
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        # 改为inline显示，让PDF在浏览器中直接打开
        response.headers['Content-Disposition'] = f'inline; filename*=UTF-8\'\'{encoded_filename}'
        
        return response
        
    except Exception as e:
        logger.error(f"导出报价单PDF失败: {str(e)}", exc_info=True)
        flash(_('导出PDF失败：%s') % str(e), 'danger')
        return redirect(url_for('quotation.at_view_quotation', id=quotation_id))

@quotation.route('/download_pdf/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def download_pdf(quotation_id):
    """
    下载报价单PDF（强制下载）

    URL参数:
        template: 模板类型，可选值：
            - 'ovs': 使用OVS Singapore模板
            - 'sp8d': 使用SP8D默认模板
            - 不传：根据数据库类型自动选择

    示例:
        /quotation/download_pdf/123?template=ovs
    """
    try:
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)

        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            flash(_('权限不足，无法下载该报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))

        # 获取模板类型参数
        template_type = request.args.get('template', None)
        if template_type and template_type not in ['ovs', 'sp8d']:
            template_type = None  # 无效参数时使用自动检测

        from app.services.evertac_quotation_pdf_generator import EvertacQuotationPDFGenerator

        # 生成PDF
        pdf_generator = EvertacQuotationPDFGenerator()
        pdf_result = pdf_generator.generate_quotation_pdf(quotation, template_type=template_type)
        pdf_content = pdf_result['content']
        filename = pdf_result['filename']
        
        # 返回PDF文件（下载）
        from flask import make_response
        from urllib.parse import quote
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        # 使用attachment强制下载
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        
        return response
        
    except Exception as e:
        logger.error(f"下载报价单PDF失败: {str(e)}", exc_info=True)
        flash(_('下载PDF失败：%s') % str(e), 'danger')
        return redirect(url_for('quotation.at_view_quotation', id=quotation_id))


@quotation.route('/export_word/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def export_word(quotation_id):
    """导出报价单Word文档"""
    try:
        # 查找报价单
        quotation_obj = Quotation.query.get_or_404(quotation_id)

        # 检查查看权限
        if not can_view_quotation(current_user, quotation_obj):
            flash(_('权限不足，无法导出该报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))

        from app.services.word_generator import WordGenerator

        # 生成Word
        word_generator = WordGenerator()
        word_result = word_generator.generate_quotation_word(quotation_obj)
        word_content = word_result['content']
        filename = word_result['filename']

        # 返回Word文件
        from flask import make_response
        from urllib.parse import quote
        response = make_response(word_content)
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'

        return response

    except Exception as e:
        logger.error(f"导出报价单Word失败: {str(e)}", exc_info=True)
        flash(_('导出Word失败：%s') % str(e), 'danger')
        return redirect(url_for('quotation.at_view_quotation', id=quotation_id))


@quotation.route('/export_word_pdf/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def export_word_pdf(quotation_id):
    """使用Word模板导出报价单PDF"""
    try:
        # 查找报价单
        quotation_obj = Quotation.query.get_or_404(quotation_id)

        # 检查查看权限
        if not can_view_quotation(current_user, quotation_obj):
            flash(_('权限不足，无法导出该报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))

        from app.services.word_generator import WordGenerator

        # 使用Word模板生成PDF
        word_generator = WordGenerator()
        pdf_result = word_generator.generate_quotation_pdf(quotation_obj)
        pdf_content = pdf_result['content']
        filename = pdf_result['filename']

        # 返回PDF文件
        from flask import make_response
        from urllib.parse import quote
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'

        return response

    except Exception as e:
        logger.error(f"导出报价单PDF(Word模板)失败: {str(e)}", exc_info=True)
        flash(_('导出PDF失败：%s') % str(e), 'danger')
        return redirect(url_for('quotation.at_view_quotation', id=quotation_id))


@quotation.route('/export_excel/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def export_excel(quotation_id):
    """
    导出报价单Excel（使用Excel模板）

    URL参数:
        template: 模板类型，可选值：
            - 'ovs': 使用OVS Singapore模板
            - 'sp8d': 使用SP8D默认模板
            - 不传：根据数据库类型自动选择

    示例:
        /quotation/export_excel/123?template=ovs
    """
    try:
        # 查找报价单
        quotation_obj = Quotation.query.get_or_404(quotation_id)

        # 检查查看权限
        if not can_view_quotation(current_user, quotation_obj):
            flash(_('权限不足，无法导出该报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))

        # 获取模板类型参数
        template_type = request.args.get('template', None)
        if template_type and template_type not in ['ovs', 'sp8d']:
            template_type = None  # 无效参数时使用自动检测

        from app.services.word_generator import WordGenerator

        # 生成Excel
        word_generator = WordGenerator()
        excel_result = word_generator.generate_quotation_excel(quotation_obj, template_type=template_type)
        excel_content = excel_result['content']
        filename = excel_result['filename']

        # 返回Excel文件
        from flask import make_response
        from urllib.parse import quote
        response = make_response(excel_content)
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'

        return response
        
    except Exception as e:
        logger.error(f"导出报价单Excel失败: {str(e)}", exc_info=True)
        flash(_('导出Excel失败：%s') % str(e), 'danger')
        return redirect(url_for('quotation.at_view_quotation', id=quotation_id))


@quotation.route('/export_excel_pdf/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def export_excel_pdf(quotation_id):
    """
    导出报价单PDF（基于Excel模板）

    URL参数:
        template: 模板类型，可选值：
            - 'ovs': 使用OVS Singapore模板
            - 'sp8d': 使用SP8D默认模板
            - 不传：根据数据库类型自动选择

    示例:
        /quotation/export_excel_pdf/123?template=ovs
    """
    try:
        # 查找报价单
        quotation_obj = Quotation.query.get_or_404(quotation_id)

        # 检查查看权限
        if not can_view_quotation(current_user, quotation_obj):
            flash(_('权限不足，无法导出该报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))

        # 获取模板类型参数
        template_type = request.args.get('template', None)
        if template_type and template_type not in ['ovs', 'sp8d']:
            template_type = None  # 无效参数时使用自动检测

        from app.services.word_generator import WordGenerator

        # 生成PDF（基于Excel模板）
        word_generator = WordGenerator()
        pdf_result = word_generator.generate_quotation_excel_pdf(quotation_obj, template_type=template_type)
        pdf_content = pdf_result['content']
        filename = pdf_result['filename']

        # 返回PDF文件
        from flask import make_response
        from urllib.parse import quote
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'

        return response

    except Exception as e:
        logger.error(f"导出报价单PDF失败: {str(e)}", exc_info=True)
        flash(_('导出PDF失败：%s') % str(e), 'danger')
        return redirect(url_for('quotation.at_view_quotation', id=quotation_id))


@quotation.route('/export-batch')
@login_required
@permission_required('quotation', 'view')
def export_batch():
    """多选报价单 → 导出产品统计电子表格(薄壳;构建逻辑见 quotation_export_service)。
    ids 通过 ?ids=1,2,3 传入;仅导出当前用户有权查看的报价单。"""
    from flask import send_file
    from app.services.quotation_export_service import build_batch_product_xlsx
    try:
        from app.utils.i18n import get_current_language
        lang = get_current_language()
    except Exception:
        lang = 'zh'

    id_list = [int(x) for x in (request.args.get('ids') or '').split(',') if x.strip().isdigit()]
    if not id_list:
        flash(_('请先选择要导出的报价单'), 'warning')
        return redirect(url_for('quotation.at_list_view'))

    quotations = [q for q in (Quotation.query.get(i) for i in id_list)
                  if q and can_view_quotation(current_user, q)]
    if not quotations:
        flash(_('没有可导出的报价单'), 'warning')
        return redirect(url_for('quotation.at_list_view'))

    bio = build_batch_product_xlsx(quotations, lang)
    # 文件名:报价产品统计-YYYYMMDD-序号.xlsx(序号按当天递增,会话内计数)
    from datetime import datetime as _dt
    from flask import session
    today = _dt.now().strftime('%Y%m%d')
    _seq = session.get('quot_export_seq') or {}
    n = (_seq.get(today, 0) if isinstance(_seq, dict) else 0) + 1
    session['quot_export_seq'] = {today: n}   # 只保留当天,避免无限膨胀
    fname = '%s-%s-%d.xlsx' % (_('报价产品统计'), today, n)
    return send_file(bio, as_attachment=True, download_name=fname,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@quotation.route('/export_pdf_with_info', methods=['POST'])
@login_required
@permission_required('quotation', 'view')
def export_pdf_with_info():
    """导出带有补充信息的报价单PDF"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据格式错误'
            }), 400
        
        quotation_id = data.get('quotation_id')
        export_info = data.get('export_info', {})
        template_type = data.get('template_type')

        # 验证模板类型
        if template_type and template_type not in ['ovs', 'sp8d']:
            template_type = None

        if not quotation_id:
            return jsonify({
                'success': False,
                'message': '缺少报价单ID'
            }), 400
        
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            return jsonify({
                'success': False,
                'message': '权限不足，无法导出该报价单'
            }), 403
        
        from app.services.evertac_quotation_pdf_generator import EvertacQuotationPDFGenerator

        # 生成PDF
        pdf_generator = EvertacQuotationPDFGenerator()
        pdf_result = pdf_generator.generate_quotation_pdf(quotation, export_info, template_type=template_type)
        pdf_content = pdf_result['content']
        filename = pdf_result['filename']
        
        # 返回PDF文件
        from flask import make_response
        from urllib.parse import quote
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        # 改为inline显示，让PDF在浏览器中直接打开
        response.headers['Content-Disposition'] = f'inline; filename*=UTF-8\'\'{encoded_filename}'
        
        return response
        
    except Exception as e:
        logger.error(f"导出带补充信息的报价单PDF失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'导出PDF失败：{str(e)}'
        }), 500


@quotation.route('/debug/permissions')
@login_required
def debug_permissions():
    """调试权限信息 - 临时调试路由"""
    if current_user.username != 'liuwei':
        return "Access denied", 403
    
    from app.utils.access_control import get_viewable_data
    
    # 收集调试信息
    debug_info = {
        'user': {
            'username': current_user.username,
            'role': current_user.role,
            'company_name': current_user.company_name,
            'permission_level': current_user.get_permission_level('quotation'),
            'can_view': current_user.has_permission('quotation', 'view')
        },
        'data_counts': {
            'total_quotations': db.session.query(func.count(Quotation.id)).scalar(),
            'viewable_quotations': get_viewable_data(Quotation, current_user).count(),
            'company_quotations': 0,
            'other_company_quotations': 0
        }
    }
    
    # 统计按公司分布
    company_stats = db.session.query(
        User.company_name,
        func.count(Quotation.id)
    ).join(Project, Quotation.project_id == Project.id)     .join(User, Project.owner_id == User.id)     .group_by(User.company_name).all()
    
    debug_info['company_distribution'] = []
    for company, count in company_stats:
        is_user_company = (company == current_user.company_name)
        debug_info['company_distribution'].append({
            'company': company or 'Unknown',
            'count': count,
            'is_user_company': is_user_company
        })
        
        if is_user_company:
            debug_info['data_counts']['company_quotations'] = count
        else:
            debug_info['data_counts']['other_company_quotations'] += count
    
    # 检查权限一致性
    expected_count = debug_info['data_counts']['total_quotations']
    actual_count = debug_info['data_counts']['viewable_quotations']
    
    debug_info['permission_analysis'] = {
        'is_system_level': debug_info['user']['permission_level'] == 'system',
        'should_see_all': expected_count,
        'actually_sees': actual_count,
        'missing_count': expected_count - actual_count,
        'is_consistent': expected_count == actual_count
    }
    
    return jsonify(debug_info)


# ============================================================================
# 动态规格配置 API
# ============================================================================

@quotation.route('/api/subcategory/<int:subcategory_id>/spec-field-options', methods=['GET'])
@login_required
@csrf.exempt
def get_subcategory_spec_field_options(subcategory_id):
    """
    获取子分类的所有规格字段及其选项（包括继承的分类级字段）

    用于报价单步骤1规格选择时：
    - 可配置字段(allow_quotation_config=True)：显示全部指标选项
    - 非可配置字段：前端仍从现有产品中提取选项

    Args:
        subcategory_id: 子分类ID

    Returns:
        JSON: {
            success: bool,
            data: {
                subcategory_id: int,
                spec_fields: [
                    {
                        field_name: str,
                        position: int,
                        use_in_code: bool,
                        allow_quotation_config: bool,  # 是否可配置
                        options: [  # 全部激活的指标选项
                            {code: str, value: str, price_adjustment: int}
                        ]
                    }
                ]
            }
        }
    """
    try:
        # 使用现有方法获取所有字段（包括继承的分类级字段）
        all_fields = ProductCodeField.get_all_fields_for_subcategory(subcategory_id)

        # 合并继承字段和自有字段，筛选纳入编码的
        spec_fields = [
            f for f in (all_fields['inherited'] + all_fields['own'])
            if f.use_in_code
        ]

        result_fields = []
        for field in spec_fields:
            # 获取该字段的所有激活选项
            options = []
            # 获取字段的单位（从规格字典中获取）
            field_unit = None

            # 判断是否为继承字段（分类级字段，subcategory_id为None）
            is_inherited_field = field.subcategory_id is None

            # 根据字段类型决定选项过滤方式
            if is_inherited_field:
                # 继承字段：必须按当前子分类ID过滤选项
                field_options = ProductCodeFieldOption.query.filter_by(
                    field_id=field.id,
                    subcategory_id=subcategory_id,
                    is_active=True
                ).order_by(ProductCodeFieldOption.position).all()
            else:
                # 子分类自有字段：获取所有激活选项
                field_options = ProductCodeFieldOption.query.filter_by(
                    field_id=field.id,
                    is_active=True
                ).order_by(ProductCodeFieldOption.position).all()

            # 【调试】记录选项排序信息
            current_app.logger.info(f"【调试】字段 {field.name} (id={field.id}, is_inherited={is_inherited_field}) 的选项:")
            for idx, opt in enumerate(field_options):
                current_app.logger.info(f"  [{idx}] option_id={opt.id}, value={opt.effective_value}, code={opt.effective_code}, position={opt.position}")

            for option in field_options:
                # 获取单位（从 spec_option.spec.unit 获取）
                if not field_unit and option.spec_option and option.spec_option.spec:
                    field_unit = option.spec_option.spec.unit

                options.append({
                    'code': option.effective_code or '',
                    'value': option.effective_value,
                    'price_adjustment': option.price_adjustment or 0
                })

            # 保持数据库查询时的position排序，不再按值字母排序

            result_fields.append({
                'field_name': field.name,
                'position': field.position,
                'use_in_code': field.use_in_code,
                'allow_quotation_config': field.allow_quotation_config or False,
                'unit': field_unit,  # 字段的单位（从规格字典获取）
                'options': options
            })

        # 按 position 排序
        result_fields.sort(key=lambda x: x['position'])

        return jsonify({
            'success': True,
            'data': {
                'subcategory_id': subcategory_id,
                'spec_fields': result_fields
            }
        })

    except Exception as e:
        current_app.logger.error(f'获取子分类规格字段选项失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@quotation.route('/api/product/<int:product_id>/configurable-specs', methods=['GET'])
@login_required
@csrf.exempt
def get_configurable_specs(product_id):
    """
    获取产品可配置的规格字段及其选项

    根据产品所属的子分类，返回该子分类下定义的可配置规格字段选项。
    可配置性在子分类级别控制：只有在 ProductCodeFieldOption 表中
    subcategory_id 匹配且 allow_quotation_config=True 的选项才会返回。

    Args:
        product_id: 产品ID

    Returns:
        JSON: {
            success: bool,
            data: {
                product_id: int,
                product_name: str,
                spec_mn: str,  # 当前MN编码
                subcategory_id: int,
                configurable_fields: [
                    {
                        field_id: int,
                        field_name: str,
                        field_unit: str,
                        position: int,
                        current_value: str,  # 产品当前的规格值
                        current_code: str,   # 产品当前的编码字符
                        options: [
                            {
                                option_id: int,
                                value: str,
                                code: str,
                                price_adjustment: int,  # 价格增量（分）
                                is_current: bool  # 是否是当前产品使用的选项
                            }
                        ]
                    }
                ]
            }
        }
    """
    try:
        # 获取产品
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': '产品不存在'
            }), 404

        subcategory_id = product.subcategory_id
        if not subcategory_id:
            return jsonify({
                'success': False,
                'message': '产品未关联子分类，无法获取可配置规格'
            }), 400

        # 获取产品的编码快照，用于确定当前规格值
        code_snapshot = product.code_definition_snapshot or {}
        code_parts = code_snapshot.get('code_parts', [])

        # 构建字段名到当前值/编码的映射
        current_specs = {}
        for part in code_parts:
            field_name = part.get('field_name')
            if field_name:
                current_specs[field_name] = {
                    'value': part.get('value', ''),
                    'code': part.get('code', '')
                }

        # 使用现有的模型方法获取所有字段（包括继承的分类级字段）
        all_fields = ProductCodeField.get_all_fields_for_subcategory(subcategory_id)
        if not all_fields['inherited'] and not all_fields['own']:
            # 子分类不存在或无字段
            pass

        # 合并继承字段和自有字段
        all_field_list = all_fields['inherited'] + all_fields['own']

        result_fields = []
        for field in all_field_list:
            if not field.use_in_code:
                continue

            # 获取该字段在子分类级的可配置选项
            # 如果子分类没有定义该字段的选项，或没有启用 allow_quotation_config，则跳过
            subcategory_options = field.get_options_for_subcategory(subcategory_id)
            if not subcategory_options:
                continue

            current_spec = current_specs.get(field.name, {})
            current_value = current_spec.get('value', '')
            current_code = current_spec.get('code', '')

            # 使用子分类级选项
            options = []
            for option in subcategory_options:
                option_value = option.effective_value
                option_code = option.effective_code

                options.append({
                    'option_id': option.id,
                    'value': option_value,
                    'code': option_code or '',
                    'price_adjustment': option.price_adjustment or 0,
                    'is_current': (option_value == current_value)
                })

            # 保持数据库查询时的position排序，不再按值字母排序

            result_fields.append({
                'field_id': field.id,
                'field_name': field.name,
                'field_unit': field.unit or '',
                'position': field.position,
                'current_value': current_value,
                'current_code': current_code,
                'options': options
            })

        return jsonify({
            'success': True,
            'data': {
                'product_id': product.id,
                'product_name': product.name,
                'spec_mn': product.spec_mn or '',
                'subcategory_id': subcategory_id,
                'configurable_fields': result_fields
            }
        })

    except Exception as e:
        current_app.logger.error(f'获取可配置规格失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@quotation.route('/api/product/<int:product_id>/calculate-mn', methods=['POST'])
@login_required
@csrf.exempt
def calculate_configured_mn(product_id):
    """
    根据配置的规格选项计算新的MN编码

    Args:
        product_id: 产品ID

    Request Body:
        {
            "spec_config": {
                "field_name_1": "option_value_1",
                "field_name_2": "option_value_2",
                ...
            }
        }

    Returns:
        JSON: {
            success: bool,
            data: {
                original_mn: str,           # 原始MN
                configured_mn: str,         # 配置后的MN
                price_adjustment_total: int, # 总价格增量（分）
                existing_product_id: int|null,  # 如果已存在相同MN的产品，返回其ID
                existing_product_price: int|null,  # 已存在产品的价格（分）
                is_new_product: bool,       # 是否需要创建新产品
                spec_details: [             # 配置详情
                    {
                        field_name: str,
                        original_value: str,
                        configured_value: str,
                        original_code: str,
                        configured_code: str,
                        price_adjustment: int
                    }
                ]
            }
        }
    """
    try:
        # 获取产品
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': '产品不存在'
            }), 404

        data = request.get_json()
        spec_config = data.get('spec_config', {})

        if not spec_config:
            return jsonify({
                'success': False,
                'message': '请提供规格配置'
            }), 400

        subcategory_id = product.subcategory_id
        if not subcategory_id:
            return jsonify({
                'success': False,
                'message': '产品未关联子分类'
            }), 400

        # 获取产品的编码快照
        code_snapshot = product.code_definition_snapshot or {}
        code_parts = code_snapshot.get('code_parts', [])

        # 构建字段名到当前值/编码的映射
        current_specs = {}
        for part in code_parts:
            field_name = part.get('field_name')
            if field_name:
                current_specs[field_name] = {
                    'value': part.get('value', ''),
                    'code': part.get('code', ''),
                    'position': part.get('position', 999)
                }

        # 获取原始MN的各部分
        original_mn = product.spec_mn or ''

        # 使用现有的模型方法获取所有字段（包括继承的分类级字段）
        all_fields = ProductCodeField.get_all_fields_for_subcategory(subcategory_id)

        # 合并继承字段和自有字段，然后筛选可配置的
        configurable_fields = [
            f for f in (all_fields['inherited'] + all_fields['own'])
            if f.use_in_code and f.allow_quotation_config
        ]

        # 构建字段名到字段对象的映射
        field_map = {f.name: f for f in configurable_fields}

        # 计算配置后的编码和价格增量
        spec_details = []
        total_price_adjustment = 0

        # 复制原始MN用于修改
        mn_chars = list(original_mn) if original_mn else []

        for field_name, configured_value in spec_config.items():
            field = field_map.get(field_name)
            if not field:
                continue  # 跳过非可配置字段

            current_spec = current_specs.get(field_name, {})
            original_value = current_spec.get('value', '')
            original_code = current_spec.get('code', '')
            # 使用code_snapshot中的实际MN位置，而不是字段的排序位置
            position = current_spec.get('position')

            if position is None:
                continue  # 没有位置信息则跳过

            # 查找配置值对应的选项
            configured_option = None
            for option in field.options:
                if option.is_active and option.effective_value == configured_value:
                    configured_option = option
                    break

            if not configured_option:
                return jsonify({
                    'success': False,
                    'message': f'规格"{field_name}"的值"{configured_value}"不在可选范围内'
                }), 400

            configured_code = configured_option.effective_code or ''
            price_adjustment = configured_option.price_adjustment or 0

            # 更新MN中对应位置的编码字符
            if position < len(mn_chars) and configured_code:
                mn_chars[position] = configured_code

            # 记录详情
            spec_details.append({
                'field_name': field_name,
                'original_value': original_value,
                'configured_value': configured_value,
                'original_code': original_code,
                'configured_code': configured_code,
                'price_adjustment': price_adjustment
            })

            # 累计价格增量（只有当值发生变化时才计算增量差）
            if original_value != configured_value:
                # 找到原始值对应的选项，获取其价格增量
                original_price_adjustment = 0
                for option in field.options:
                    if option.is_active and option.effective_value == original_value:
                        original_price_adjustment = option.price_adjustment or 0
                        break

                # 价格变化 = 新选项增量 - 原选项增量
                total_price_adjustment += (price_adjustment - original_price_adjustment)

        configured_mn = ''.join(mn_chars)

        # 检查是否已存在相同MN的产品
        existing_product = None
        existing_product_id = None
        existing_product_price = None
        is_new_product = True

        if configured_mn:
            existing_product = Product.query.filter(
                Product.spec_mn == configured_mn,
                Product.is_deleted == False
            ).first()

            if existing_product:
                is_new_product = False
                existing_product_id = existing_product.id
                existing_product_price = existing_product.unit_price

        return jsonify({
            'success': True,
            'data': {
                'original_mn': original_mn,
                'configured_mn': configured_mn,
                'price_adjustment_total': total_price_adjustment,
                'existing_product_id': existing_product_id,
                'existing_product_price': existing_product_price,
                'is_new_product': is_new_product,
                'spec_details': spec_details
            }
        })

    except Exception as e:
        current_app.logger.error(f'计算配置MN失败: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'计算失败: {str(e)}'
        }), 500


def create_products_from_configured_specs(quotation):
    """
    从报价单明细中的配置规格创建研发产品

    遍历报价单的所有明细项，找到标记为 pending_product_creation=True 的项，
    基于原产品和配置的规格创建新的研发产品（DevProduct）。
    新创建的研发产品状态为"立项中"。

    Args:
        quotation: 报价单对象

    Returns:
        list: 创建的新研发产品列表
    """
    from app.models.dev_product import DevProduct, DevProductSpec
    from datetime import datetime

    current_app.logger.info(f'[DEBUG] create_products_from_configured_specs 被调用，报价单ID={quotation.id}，明细数={len(quotation.details)}')

    created_products = []

    for detail in quotation.details:
        # 🔍 调试：打印每个明细的配置字段
        current_app.logger.info(f'[DEBUG] 明细 {detail.id}: pending_product_creation={detail.pending_product_creation}, '
            f'configured_mn={detail.configured_mn}, configured_specs={detail.configured_specs}')

        # 检查是否需要创建新产品
        if not detail.pending_product_creation:
            continue

        if not detail.configured_specs or not detail.configured_mn:
            current_app.logger.warning(f'明细 {detail.id} 标记需创建产品但缺少配置数据')
            continue

        configured_mn = detail.configured_mn

        # 1. 检查研发产品库是否已存在相同MN
        existing_dev_product = DevProduct.query.filter(
            DevProduct.mn_code == configured_mn
        ).first()

        if existing_dev_product:
            current_app.logger.info(f'配置的MN {configured_mn} 已存在研发产品 {existing_dev_product.id}，跳过创建')

            # 追加报价单引用到 development_purpose
            quotation_no = quotation.quotation_number
            current_purpose = existing_dev_product.development_purpose or ''
            if quotation_no not in current_purpose:
                if '引用:' in current_purpose:
                    # 已有引用记录，追加
                    existing_dev_product.development_purpose = f'{current_purpose}, {quotation_no}'
                else:
                    # 首次添加引用
                    existing_dev_product.development_purpose = f'{current_purpose}\n引用: {quotation_no}'
                current_app.logger.info(f'研发产品 {existing_dev_product.id} 追加报价单引用: {quotation_no}')

            detail.pending_product_creation = False
            continue

        # 2. 检查标准产品库是否已存在相同MN
        existing_product = Product.query.filter(
            Product.spec_mn == configured_mn,
            Product.status != 'deleted'
        ).first()

        if existing_product:
            current_app.logger.info(f'配置的MN {configured_mn} 已存在标准产品 {existing_product.id}，跳过创建')
            detail.pending_product_creation = False
            continue

        # 3. 获取原产品信息
        configured_specs = detail.configured_specs or {}
        original_product_id = configured_specs.get('original_product_id')

        if not original_product_id:
            # 尝试从product_mn反向查找
            if detail.product_mn and not detail.product_mn.startswith('TEMP_'):
                original_product = Product.query.filter(
                    Product.spec_mn == detail.product_mn,
                    Product.status != 'deleted'
                ).first()
                if original_product:
                    original_product_id = original_product.id

        if not original_product_id:
            current_app.logger.warning(f'明细 {detail.id} 无法找到原产品')
            continue

        original_product = Product.query.get(original_product_id)
        if not original_product:
            current_app.logger.warning(f'原产品 {original_product_id} 不存在')
            continue

        try:
            # 4. 创建研发产品
            current_time = datetime.now()
            price_adjustment = detail.price_adjustment_total or 0

            # 计算新价格（price_adjustment 是分，retail_price 是元）
            original_price = float(original_product.retail_price or 0)
            new_price = original_price + (price_adjustment / 100)

            # 初始化阶段历史（立项阶段）
            initial_stage_history = [{
                'stage': 'planning',
                'startDate': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'endDate': None,
                'user_id': current_user.id,
                'description': f'从报价单 {quotation.quotation_number} 配置创建'
            }]

            new_dev_product = DevProduct(
                name=original_product.name,
                model=original_product.model,
                category_id=original_product.category_id,
                subcategory_id=original_product.subcategory_id,
                region_id=original_product.region_id,
                unit=original_product.unit,
                currency=original_product.currency or Config.DEFAULT_CURRENCY,
                mn_code=configured_mn,
                status='立项中',
                retail_price=new_price,
                development_purpose=f'从报价单 {quotation.quotation_number} 配置创建',
                # ⭐ 优先使用配置后的描述，否则使用报价单明细描述或原产品规格
                description=configured_specs.get('configured_description') or detail.product_desc or original_product.specification,
                created_by=current_user.id,
                owner_id=current_user.id,
                created_at=current_time,
                stage_history=initial_stage_history,
                image_path=original_product.image_path
            )

            db.session.add(new_dev_product)
            db.session.flush()  # 获取新产品ID

            # 5. 创建规格记录
            # 首先从原产品复制基础规格
            from app.models.product_spec import ProductSpec
            original_specs = ProductSpec.query.filter_by(product_id=original_product_id).all()

            # 构建配置选择的映射（fieldName -> 配置值）
            price_details = configured_specs.get('price_details', [])
            configurable_selections = configured_specs.get('configurable_selections', {})

            # 从 price_details 构建字段名到配置值的映射
            configured_values = {}
            for pd in price_details:
                field_name = pd.get('fieldName', '')
                if field_name:
                    configured_values[field_name] = {
                        'value': pd.get('value', ''),
                        'code': ''  # price_details 中没有 code，需要从 configurable_selections 获取
                    }

            # 从 configurable_selections 补充 code 信息
            # configurable_selections 的 key 是字段ID，需要通过查询获取字段名
            from app.models.product_code import ProductCodeField
            for field_id, selection in configurable_selections.items():
                field = ProductCodeField.query.get(int(field_id))
                if field and field.name in configured_values:
                    configured_values[field.name]['code'] = selection.get('code', '')

            current_app.logger.info(f'[DEBUG] 配置值映射: {configured_values}')

            # 复制原产品规格，替换配置的值
            for orig_spec in original_specs:
                field_name = orig_spec.field_name
                field_value = orig_spec.field_value
                field_code = orig_spec.field_code

                # 如果该字段有配置值，使用配置值
                if field_name in configured_values:
                    field_value = configured_values[field_name].get('value', field_value)
                    field_code = configured_values[field_name].get('code', field_code)
                    current_app.logger.info(f'[DEBUG] 字段 {field_name} 使用配置值: value={field_value}, code={field_code}')

                dev_spec = DevProductSpec(
                    dev_product_id=new_dev_product.id,
                    field_name=field_name,
                    field_value=field_value,
                    field_code=field_code,
                    include_in_description=True
                )
                db.session.add(dev_spec)

            current_app.logger.info(f'[DEBUG] 复制了 {len(original_specs)} 个规格到研发产品')

            # 6. 更新明细项
            detail.pending_product_creation = False
            detail.product_mn = configured_mn  # 更新为新的MN

            created_products.append(new_dev_product)
            current_app.logger.info(f'成功创建研发产品: ID={new_dev_product.id}, MN={configured_mn}, 状态=立项中')

        except Exception as e:
            current_app.logger.error(f'创建研发产品失败: {str(e)}')
            import traceback
            current_app.logger.error(traceback.format_exc())
            continue

    return created_products


# ==================== 账户级报价单抬头/签名 API ====================

@quotation.route('/api/user/quotation_template', methods=['POST'])
@login_required
def save_quotation_template():
    """保存当前用户的账户默认抬头/签名（字段级）。

    body: { "field": "letterhead.line1" | "signature.left" | ..., "value": "..." }
    """
    data = request.get_json() or {}
    field = data.get('field', '')
    value = data.get('value', '')

    if '.' not in field:
        return jsonify({'success': False, 'message': 'field 必须形如 letterhead.line1 / signature.left'}), 400
    group, key = field.split('.', 1)
    if group not in ('letterhead', 'signature'):
        return jsonify({'success': False, 'message': 'unknown group'}), 400

    user = current_user
    if group == 'letterhead':
        cur = dict(user.quotation_letterhead or {})
        cur[key] = value
        user.quotation_letterhead = cur
    else:
        cur = dict(user.quotation_signature or {})
        cur[key] = value
        user.quotation_signature = cur

    db.session.commit()
    return jsonify({'success': True})


@quotation.route('/mobile-view/<token>')
def mobile_view_quotation(token):
    """
    移动端报价单只读预览。
    直接验证 JWT preview token 并渲染专用模板，完全绕开 Flask-Login / permission 装饰器，
    页面内无 AJAX 调用，不依赖 session cookie，不会跳登录页。
    """
    try:
        from flask_jwt_extended import decode_token

        data = decode_token(token)
        if not data.get('mobile_preview'):
            return "链接无效", 403

        user_id = int(data.get('sub', 0))
        quotation_id = int(data.get('quotation_id', 0))

        user = User.query.get(user_id)
        if not user:
            return "用户不存在", 403

        quotation = Quotation.query.get_or_404(quotation_id)
        if not can_view_quotation(user, quotation):
            return "无权查看此报价单", 403

        details = QuotationDetail.query\
            .filter_by(quotation_id=quotation_id)\
            .order_by(QuotationDetail.sort_order, QuotationDetail.id)\
            .all()

        extra_fields = quotation.extra_fields or {}
        user_letterhead = getattr(quotation.owner, 'quotation_letterhead', None) or {}
        user_signature = getattr(quotation.owner, 'quotation_signature', None) or {}

        return render_template(
            'quotation/mobile_quotation_view.html',
            quotation=quotation,
            details=details,
            extra_fields=extra_fields,
            user_letterhead=user_letterhead,
            user_signature=user_signature,
        )

    except Exception as e:
        logger.error(f"mobile_view_quotation error: {e}", exc_info=True)
        return "链接已过期或无效，请重新打开", 403


# ════════════════════════════════════════════════════════════════
# AT 标准审批 API — 复用 ApprovalInstance/start_approval_process 框架
# 与现有 SM 销售指派机制并行(SM 用于 confirmation_badge_status,这套用于 ApprovalInstance)
# ════════════════════════════════════════════════════════════════

def _recommend_quotation_confirmer(quotation, candidate_ids):
    """推荐技术确认人(仅在候选池内):
       ① 同项目历史确认人(最近确认优先) → ② 项目跟进记录(Action)负责人 → ③ 系统设计 owner。
       命中第一个在候选池里的即返回;都没有则 None。"""
    if not candidate_ids:
        return None
    cset = set(candidate_ids)
    # ⓪ 本单自己的历史确认人(再次确认场景最相关)
    if quotation.confirmed_by and quotation.confirmed_by in cset:
        return quotation.confirmed_by
    pid = quotation.project_id
    if not pid:
        return None
    # ① 同项目其它报价单的历史确认人(最近确认优先)
    rows = (Quotation.query
            .filter(Quotation.project_id == pid,
                    Quotation.confirmed_by.isnot(None),
                    Quotation.id != quotation.id)
            .order_by(Quotation.confirmed_at.desc()).all())
    for r in rows:
        if r.confirmed_by in cset:
            return r.confirmed_by
    # ② 项目跟进记录(Action)负责人中的候选(最近优先)
    try:
        from app.models.action import Action
        acts = (Action.query.filter(Action.project_id == pid)
                .order_by(Action.date.desc(), Action.id.desc()).all())
        for a in acts:
            if a.owner_id in cset:
                return a.owner_id
    except Exception:
        pass
    # ③ 系统设计图 owner
    try:
        from app.models.system_diagram import SystemDiagram
        diag = (SystemDiagram.query.filter(SystemDiagram.project_id == pid)
                .order_by(SystemDiagram.id.desc()).first())
        if diag and diag.owner_id in cset:
            return diag.owner_id
    except Exception:
        pass
    return None


@quotation.route('/api/approval/<int:quotation_id>/templates')
@login_required
def at_get_quotation_approval_templates(quotation_id):
    """获取报价单可用的审批模板,含 designate_steps(submitter_designate 候选审批人 + 推荐人)"""
    try:
        from app.helpers.approval_helpers import get_approval_templates as _list_tpls
        from app.helpers.approval_helpers import get_designate_steps_info

        q = Quotation.query.get_or_404(quotation_id)
        if not can_view_quotation(current_user, q):
            return jsonify({'success': False, 'message': '无权限访问'}), 403

        tpls = _list_tpls(object_type='quotation', is_active=True)

        def _ser(t):
            steps = get_designate_steps_info(t.id)
            for s in steps:
                cids = [c['id'] for c in (s.get('candidates') or [])]
                rec = _recommend_quotation_confirmer(q, cids)
                s['recommended_id'] = rec
                for c in (s.get('candidates') or []):
                    c['recommended'] = (c['id'] == rec)
            return {
                'id': t.id,
                'name': t.name,
                'object_type': t.object_type,
                'required_fields': t.required_fields or [],
                'designate_steps': steps,
            }
        items = tpls.items if hasattr(tpls, 'items') else tpls
        return jsonify({'success': True, 'templates': [_ser(t) for t in items]})
    except Exception as e:
        logger.error(f"获取报价单审批模板失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation.route('/api/approval/<int:quotation_id>/flow')
@login_required
def at_get_quotation_approval_flow(quotation_id):
    """获取报价单标准审批流程(ApprovalInstance 视角)— 与 SM 机制并行"""
    try:
        from app.helpers.approval_helpers import (
            get_object_approval_instance, can_recall_approval, can_resubmit_approval,
            get_step_actual_approver, can_user_approve,
        )
        from app.models.approval import ApprovalRecord

        q = Quotation.query.get_or_404(quotation_id)
        if not can_view_quotation(current_user, q):
            return jsonify({'success': False, 'message': '无权限'}), 403

        instance = get_object_approval_instance('quotation', quotation_id)
        if not instance:
            # 草稿态 — 没有 ApprovalInstance
            return jsonify({
                'success': False,
                'message': '尚未提交审批',
                'approval_flow': None,
                'control_info': {
                    'status': 'draft',
                    'can_submit': (q.owner_id == current_user.id),
                    'can_recall': False, 'can_resubmit': False,
                },
            })

        steps = instance.get_steps() or []
        records = ApprovalRecord.query.filter_by(instance_id=instance.id) \
            .order_by(ApprovalRecord.timestamp.asc()).all()

        # 当前 step 解析(沿用 expense flow 同款逻辑:先 step_order,再 step_id 兜底)
        current_step_value = instance.current_step
        current_step_order = None
        for s in steps:
            if s.get('step_order') == current_step_value:
                current_step_order = current_step_value
                break
        if current_step_order is None:
            for s in steps:
                if s.get('step_id') == current_step_value:
                    current_step_order = s.get('step_order')
                    break

        stages = []
        for i, step in enumerate(steps):
            actual = get_step_actual_approver(step, instance)
            step_recs = [r for r in records if r.step_id == step.get('step_id')]
            if not step_recs and records:
                # 快照模式兜底
                approve_recs = [r for r in records if r.action in ('approve', 'reject')]
                if approve_recs and all(r.step_id is None for r in approve_recs):
                    order_n = step.get('step_order', i + 1)
                    if order_n <= len(approve_recs):
                        step_recs = [approve_recs[order_n - 1]]

            stage = {
                'id': step.get('step_id'),
                'stage_name': step.get('step_name'),
                'stage_order': step.get('step_order'),
                'approver_name': actual.real_name if actual else '待确定',
                'approver_id': actual.id if actual else None,
                'status': 'pending',
                'processed_at': None,
                'comment': None,
                'action': None,
                'can_approve': False,
            }
            if step_recs:
                latest = step_recs[-1]
                stage.update({
                    'status': 'skipped' if latest.action == 'skipped' else (
                        'approved' if latest.action == 'approve' else 'rejected'),
                    'processed_at': latest.timestamp.strftime('%Y-%m-%d %H:%M:%S') if latest.timestamp else None,
                    'comment': latest.comment,
                    'action': latest.action,
                    'approver_name': latest.approver.real_name if latest.approver else stage['approver_name'],
                    'approver_id': latest.approver_id,
                })
            elif step.get('step_order') == current_step_order:
                stage.update({
                    'status': 'current',
                    'arrived_at': instance.started_at.strftime('%Y-%m-%d %H:%M:%S') if instance.started_at else None,
                    'can_approve': can_user_approve(instance.id, current_user.id),
                })
            stages.append(stage)

        actual_status = instance.status.value if hasattr(instance.status, 'value') else str(instance.status)
        last_record = records[-1] if records else None
        if last_record and last_record.action == 'recall':
            actual_status = 'recalled'

        return jsonify({
            'success': True,
            'approval_flow': {
                'instance_id': instance.id,
                'stages': stages,
                'current_stage': current_step_order,
                'can_approve': any(s.get('can_approve') for s in stages),
                'status': actual_status,
                'can_recall': can_recall_approval('quotation', quotation_id, current_user.id),
                'can_resubmit': can_resubmit_approval('quotation', quotation_id, current_user.id),
                'is_creator': instance.created_by == current_user.id,
                'creator_id': instance.created_by,
            }
        })
    except Exception as e:
        logger.error(f"获取报价单审批流程失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation.route('/api/approval/<int:quotation_id>/submit', methods=['POST'])
@login_required
def at_submit_quotation_approval(quotation_id):
    """提交报价单到标准审批流程(支持 submitter_designate)"""
    try:
        from app.helpers.approval_helpers import (
            start_approval_process, get_approval_templates, get_object_approval_instance,
        )
        from app.models.approval import ApprovalStatus

        q = Quotation.query.get_or_404(quotation_id)
        if q.owner_id != current_user.id and current_user.role != 'admin':
            return jsonify({'success': False, 'message': '只有创建人或管理员可以提交审批'}), 403

        data = request.get_json(silent=True) or {}
        template_id = data.get('template_id')
        designated = data.get('designated_approvers')

        # 默认模板:取第一个可用
        if not template_id:
            tpls = get_approval_templates(object_type='quotation', is_active=True)
            tpl_items = tpls.items if hasattr(tpls, 'items') else tpls
            if not tpl_items:
                return jsonify({'success': False, 'message': '没有可用的报价单审批模板'}), 400
            template_id = tpl_items[0].id

        # 再次确认:旧 APPROVED 实例置 recalled(作废),否则 start 会因"已存在审批"拒绝
        _prev = get_object_approval_instance('quotation', quotation_id)
        if _prev and _prev.status == ApprovalStatus.APPROVED:
            _prev.status = ApprovalStatus.RECALLED
            db.session.commit()

        instance = start_approval_process(
            object_type='quotation',
            object_id=quotation_id,
            template_id=template_id,
            user_id=current_user.id,
            auto_commit=True,
            designated_approvers=designated,
        )
        if not instance:
            return jsonify({'success': False, 'message': '提交审批失败,请检查是否已有进行中的审批'}), 400
        # 徽章 = 审批结果显示:提交即进入「待确认」(pending)
        try:
            q.set_pending_confirmation_badge()
            db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({'success': True, 'message': '已提交审批', 'instance_id': instance.id})
    except Exception as e:
        logger.error(f"提交报价单审批失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation.route('/api/approval/<int:quotation_id>/sm-confirm', methods=['POST'])
@login_required
def at_sm_confirm_quotation(quotation_id):
    """解决方案经理一键技术确认 = 自动跑完审批流(建实例并指定自己为审批人 + 立即通过)。
    徽章由审批结果回调驱动,与 owner 提交→SM审批 殊途同归、状态单一。"""
    try:
        from app.helpers.approval_helpers import (
            get_object_approval_instance, process_approval,
            start_approval_process, get_approval_templates as _list_tpls,
            get_designate_steps_info,
        )
        from app.models.approval import ApprovalStatus

        if current_user.role not in ('solution_manager', 'admin'):
            return jsonify({'success': False, 'message': '只有解决方案经理可以直接技术确认'}), 403
        q = Quotation.query.get_or_404(quotation_id)
        if not can_view_quotation(current_user, q):
            return jsonify({'success': False, 'message': '无权限'}), 403

        inst = get_object_approval_instance('quotation', quotation_id)
        if inst and inst.status == ApprovalStatus.PENDING:
            ok = process_approval(inst.id, 'approve', user_id=current_user.id, comment='技术确认')
            if not ok:
                return jsonify({'success': False, 'message': '当前审批人不是您,请在审批流程中操作'}), 400
        else:
            tpls = _list_tpls(object_type='quotation', is_active=True)
            items = tpls.items if hasattr(tpls, 'items') else tpls
            if not items:
                return jsonify({'success': False, 'message': '没有可用的报价单审批模板'}), 400
            tpl_id = items[0].id
            steps = get_designate_steps_info(tpl_id)
            designated = {str(s['step_id']): current_user.id for s in steps}
            # 再次确认:旧 APPROVED 实例置 recalled(作废),否则 start 会因"已存在审批"拒绝
            _prev = get_object_approval_instance('quotation', quotation_id)
            if _prev and _prev.status == ApprovalStatus.APPROVED:
                _prev.status = ApprovalStatus.RECALLED
                db.session.commit()
            inst = start_approval_process('quotation', quotation_id, tpl_id, current_user.id,
                                          auto_commit=True, designated_approvers=designated)
            if not inst:
                return jsonify({'success': False, 'message': '发起确认失败(可能已有进行中的审批)'}), 400
            db.session.refresh(inst)
            # 发起人即审批人时步骤会被自动跳过、实例直接完成(不经 process_approval);
            # 仍 PENDING 则正常审批通过。
            if inst.status == ApprovalStatus.PENDING:
                ok = process_approval(inst.id, 'approve', user_id=current_user.id, comment='技术确认')
                if not ok:
                    return jsonify({'success': False, 'message': '确认失败'}), 400
        # 兜底:确保徽章点亮(自审跳过完成时回调可能未触发) —— 徽章=审批结果显示
        q = Quotation.query.get(quotation_id)
        if q and (q.confirmation_badge_status or 'none') != 'confirmed':
            q.set_confirmation_badge('#28a745', current_user.id)
            try:
                from app.models.change_log import ChangeLog
                ChangeLog.log_update(
                    module_name='quotation', table_name='quotations',
                    record_id=quotation_id, field_name='confirmation',
                    old_value='', new_value='confirmed',
                    user_id=current_user.id,
                    user_name=(current_user.real_name or current_user.username),
                    description='confirm_confirmed', ip_address=request.remote_addr)
            except Exception:
                pass
            db.session.commit()
        return jsonify({'success': True, 'message': '技术确认完成'})
    except Exception as e:
        logger.error(f"SM 技术确认失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation.route('/api/approval/<int:quotation_id>/recall', methods=['POST'])
@login_required
def at_recall_quotation_approval(quotation_id):
    """召回报价单审批"""
    try:
        from app.helpers.approval_helpers import recall_approval

        q = Quotation.query.get_or_404(quotation_id)
        data = request.get_json(silent=True) or {}
        reason = data.get('reason', '')
        result = recall_approval(
            object_type='quotation', object_id=quotation_id,
            user_id=current_user.id, reason=reason,
        )
        # recall_approval 返回 (success: bool, message: str) 或 tuple/dict — 兼容处理
        if isinstance(result, tuple) and len(result) >= 2:
            ok, msg = result[0], result[1]
        elif isinstance(result, dict):
            ok = result.get('success', False); msg = result.get('message', '')
        else:
            ok, msg = bool(result), ''

        # 召回成功后,解锁报价单 — 重新查避免 session expired,用模型 unlock() 方法清空所有锁字段
        if ok:
            try:
                fresh_q = Quotation.query.get(quotation_id)
                if fresh_q:
                    if hasattr(fresh_q, 'unlock'):
                        fresh_q.unlock(current_user.id)
                    else:
                        fresh_q.is_locked = False
                        fresh_q.lock_reason = None
                        fresh_q.locked_by = None
                        fresh_q.locked_at = None
                    # 徽章=审批结果:召回 → 回到未确认(none),与列表保持一致
                    if (fresh_q.confirmation_badge_status or 'none') != 'none':
                        fresh_q.clear_confirmation_badge()
                    db.session.commit()
                    logger.info(f"召回后已解锁报价单 #{quotation_id}, is_locked={fresh_q.is_locked}")
            except Exception as _unlock_err:
                logger.warning(f"召回后解锁报价单失败: {_unlock_err}", exc_info=True)
                db.session.rollback()

        return jsonify({'success': ok, 'message': msg or ('已召回' if ok else '召回失败')})
    except Exception as e:
        logger.error(f"召回报价单审批失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@quotation.route('/api/approval/<int:quotation_id>/resubmit', methods=['POST'])
@login_required
def at_resubmit_quotation_approval(quotation_id):
    """重新提交报价单审批(rejected / recalled 态)— 复用 submit 逻辑"""
    return at_submit_quotation_approval(quotation_id)
