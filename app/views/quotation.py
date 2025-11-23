from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_babel import gettext as _, ngettext
from app.models.quotation import Quotation, QuotationDetail
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.product import Product  # 添加产品模型导入
from app.models.user import User  # 添加User模型导入
from app.utils.product_helpers import find_product_by_name_and_model  # 产品查询辅助函数
from datetime import datetime
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from app import db
from flask_login import login_required, current_user
from app.decorators import permission_required, permission_required_with_approval_context  # 添加权限装饰器导入
from app.extensions import csrf
from app.utils.access_control import get_viewable_data, can_edit_data, can_view_project, can_change_quotation_owner
import logging
from decimal import Decimal
import json
from flask import current_app
from app.utils.dictionary_helpers import project_type_label, project_stage_label, REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS, COMPANY_TYPE_LABELS, get_currency_type_options
from app.services.exchange_rate_service import exchange_rate_service
from app.utils.chinese_mapping_manager import mapping_manager
from app.utils.notification_helpers import trigger_event_notification
from app.services.event_dispatcher import notify_project_created, notify_project_status_updated
from app.helpers.project_helpers import is_project_editable
from app.utils.activity_tracker import check_company_activity, update_active_status
from app.models.settings import SystemSettings
from zoneinfo import ZoneInfo
from app.utils.role_mappings import get_role_display_name
from app.utils.solution_manager_notifications import notify_solution_managers_quotation_created, notify_solution_managers_quotation_updated
from app.helpers.approval_helpers import get_object_approval_instance, get_current_step_info, can_user_approve
from sqlalchemy import event
from app.models.quotation import update_quotation_product_signature, QuotationDetail

# 配置日志
logger = logging.getLogger(__name__)

quotation = Blueprint('quotation', __name__)

@quotation.route('/quotations')
@login_required
@permission_required('quotation', 'view')
def list_quotations():
    try:
        # 获取搜索参数
        search = request.args.get('search', '')
        project_search = request.args.get('project', '')
        
        # 滚动加载参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # 限制每次加载数量的范围
        if limit not in [10, 20, 30, 50]:
            limit = 20
        
        # 获取排序参数
        sort_field = request.args.get('sort', 'created_at')
        sort_order = request.args.get('order', 'desc')
        
        # 使用访问控制函数构建查询
        query = get_viewable_data(Quotation, current_user)
        # 🔍 调试: 检查系统级权限的查询结果
        if current_user.username == 'liuwei':  # 临时调试代码
            import logging
            debug_logger = logging.getLogger('quotation_debug')
            debug_logger.setLevel(logging.INFO)
            
            # 检查权限级别
            perm_level = current_user.get_permission_level('quotation')
            debug_logger.info(f"🔍 用户 {current_user.username} 的quotation权限级别: {perm_level}")
            
            # 检查基础查询结果
            base_count = query.count()
            debug_logger.info(f"📊 get_viewable_data返回的报价单数量: {base_count}")
            
            # 检查数据库中的总数
            total_count = db.session.query(func.count(Quotation.id)).scalar()
            debug_logger.info(f"📊 数据库中报价单总数: {total_count}")
            
            if perm_level == 'system' and base_count != total_count:
                debug_logger.warning(f"⚠️ 权限异常: 系统级权限应该看到所有{total_count}个报价单，但只返回了{base_count}个")

        
        # 渠道经理默认只查看渠道跟进项目的报价单
        project_type = request.args.get('project_type', '')
        if current_user.role and current_user.role.strip() == 'channel_manager' and not project_type:
            project_type = 'channel_follow'
        
        # 营销总监默认查看销售重点和渠道跟进项目的报价单
        if current_user.role and current_user.role.strip() == 'sales_director' and not project_type:
            project_type = 'marketing_focus'
        
        # 标记是否已经JOIN了Project表
        project_joined = False
        
        # 搜索过滤 - 在报价单编号中搜索
        if search:
            query = query.filter(Quotation.quotation_number.ilike(f'%{search}%'))
        
        # 项目名称搜索
        if project_search:
            query = query.join(Project)
            query = query.filter(Project.project_name.like(f'%{project_search}%'))
            project_joined = True
        
        # 筛选条件
        owner_filter = request.args.get('owner_filter')
        project_type_filter = request.args.get('project_type_filter') or project_type
        project_stage_filter = request.args.get('project_stage_filter')
        
        if owner_filter:
            query = query.filter(Quotation.owner_id == owner_filter)
        
        # 项目类型筛选
        if project_type_filter:
            if not project_joined:
                query = query.join(Project, Quotation.project_id == Project.id)
                project_joined = True
            
            if project_type_filter == 'channel_follow':
                query = query.filter(Project.project_type == 'channel_follow')
            elif project_type_filter == 'sales_focus':
                query = query.filter(Project.project_type.in_(['sales_focus', 'sales_key']))
            elif project_type_filter == 'marketing_focus':
                query = query.filter(Project.project_type.in_(['sales_focus', 'sales_key', 'channel_follow']))
            else:
                query = query.filter(Project.project_type == project_type_filter)
        
        # 报价阶段筛选（使用报价单的快照阶段）
        if project_stage_filter:
            query = query.filter(Quotation.project_stage == project_stage_filter)
        
        # 验证排序字段是否有效
        valid_sort_fields = ['quotation_number', 'created_at', 'updated_at', 'total_amount', 
                           'status', 'approval_status', 'owner_id', 'project_name', 
                           'project_stage', 'project_type']
        
        if sort_field not in valid_sort_fields:
            sort_field = 'created_at'
        
        # 处理排序
        if sort_field == 'project_name':
            if not project_joined:
                query = query.join(Project, Quotation.project_id == Project.id)
                project_joined = True
            if sort_order == 'desc':
                query = query.order_by(Project.project_name.desc())
            else:
                query = query.order_by(Project.project_name.asc())
        elif sort_field == 'project_stage':
            # 按报价单的快照阶段排序，而不是项目当前阶段
            if sort_order == 'desc':
                query = query.order_by(Quotation.project_stage.desc())
            else:
                query = query.order_by(Quotation.project_stage.asc())
        elif sort_field == 'project_type':
            if not project_joined:
                query = query.join(Project, Quotation.project_id == Project.id)
                project_joined = True
            if sort_order == 'desc':
                query = query.order_by(Project.project_type.desc())
            else:
                query = query.order_by(Project.project_type.asc())
        elif sort_field == 'owner_id':
            if sort_order == 'desc':
                query = query.order_by(Quotation.owner_id.desc())
            else:
                query = query.order_by(Quotation.owner_id.asc())
        else:
            # 其他字段直接使用
            if hasattr(Quotation, sort_field):
                sort_attr = getattr(Quotation, sort_field)
                if sort_order == 'desc':
                    query = query.order_by(sort_attr.desc())
                else:
                    query = query.order_by(sort_attr.asc())
        
        # 获取总记录数
        total_count = query.count()
        
        # 滚动加载查询
        quotations = query.offset(offset).limit(limit).all()
        
        # 计算是否还有更多数据
        has_more = (offset + limit) < total_count
        
        # 预加载所有报价单的所有者信息
        owner_ids = [quotation.owner_id for quotation in quotations if quotation.owner_id]
        if owner_ids:
            owners = {user.id: user for user in User.query.filter(User.id.in_(owner_ids)).all()}
            for quotation in quotations:
                if quotation.owner_id and quotation.owner_id in owners:
                    quotation.owner = owners[quotation.owner_id]
        
        # 获取实际存在的项目类型选项 - 优化查询避免N+1问题
        from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS
        
        # 获取当前语言
        from app.utils.i18n import get_current_language
        current_lang = get_current_language()
        
        # 使用高效的子查询获取项目类型，避免加载所有报价单数据
        viewable_quotation_subquery = get_viewable_data(Quotation, current_user).subquery()
        unique_project_types_query = db.session.query(Project.project_type.distinct())\
            .join(viewable_quotation_subquery, Project.id == viewable_quotation_subquery.c.project_id)\
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
                # 处理没有在字典中定义的项目类型
                project_type_options.append({
                    'value': project_type,
                    'label': project_type
                })
        
        # 获取筛选选项数据 - 优化用户查询避免N+1问题
        unique_owner_ids_query = get_viewable_data(Quotation, current_user)\
            .filter(Quotation.owner_id.isnot(None))\
            .with_entities(Quotation.owner_id.distinct())
        
        unique_owner_ids = {row[0] for row in unique_owner_ids_query.all()}
        
        # 只查询需要的用户，避免加载所有用户
        # 移除活跃状态过滤，确保所有实际拥有报价单的用户都出现在筛选选项中
        available_users = User.query.filter(
            User.id.in_(unique_owner_ids)
        ).order_by(User.real_name, User.username).all()
        
        # 报价阶段选项 - 使用报价单的快照阶段
        from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS

        # 使用高效查询获取实际存在的报价阶段
        # 获取可见报价单的ID列表（使用子查询）
        viewable_quotation_ids_query = get_viewable_data(Quotation, current_user).with_entities(Quotation.id)
        unique_project_stages_query = db.session.query(Quotation.project_stage.distinct())\
            .filter(Quotation.id.in_(viewable_quotation_ids_query))\
            .filter(Quotation.project_stage.isnot(None))\
            .filter(Quotation.project_stage != '')

        unique_project_stages = {row[0] for row in unique_project_stages_query.all()}

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
        
        # 计算统计数据
        stats_query = get_viewable_data(Quotation, current_user)
        total_stats_count = stats_query.count()

        # 获取当前语言环境的目标货币和显示配置
        from app.utils.i18n import get_current_language, get_default_currency, get_currency_symbol
        current_lang = get_current_language()
        target_currency = 'USD' if current_lang == 'en' else 'CNY'

        # 配置语言感知的显示单位和货币符号（复用项目管理的成功逻辑）
        amount_unit = '万美元' if current_lang == 'en' else '万元'
        default_currency = get_default_currency()
        currency_symbol = get_currency_symbol(default_currency)

        # 计算金额统计（转换为万元/万美元）
        def calculate_converted_amount(quotations_query):
            """计算转换后的金额总和"""
            quotations = quotations_query.all()
            total_converted = 0
            for quotation in quotations:
                original_amount = quotation.amount or 0
                original_currency = quotation.currency or 'CNY'

                if original_amount > 0:
                    converted_amount = exchange_rate_service.convert_amount(
                        original_amount, original_currency, target_currency
                    )
                    total_converted += converted_amount
            return total_converted

        total_stats_amount = round(calculate_converted_amount(stats_query) / 10000, 2)

        # 按状态统计
        approved_stats = stats_query.filter(Quotation.approval_status == 'approved')
        approved_count = approved_stats.count()
        approved_amount = round(calculate_converted_amount(approved_stats) / 10000, 2)

        pending_stats = stats_query.filter(Quotation.approval_status.in_(['pending', 'in_progress']))
        pending_count = pending_stats.count()
        pending_amount = round(calculate_converted_amount(pending_stats) / 10000, 2)

        draft_stats = stats_query.filter(Quotation.approval_status == 'draft')
        draft_count = draft_stats.count()
        draft_amount = round(calculate_converted_amount(draft_stats) / 10000, 2)
        
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
                    'label': _(mapping_manager.get_field_display_name('common', 'owner_id')),
                    'all_option_text': _('全部负责人'),
                    'current_value': owner_filter if owner_filter and request.args else '',
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
                        'key': 'quotation_number',
                        'field': 'quotation_number',
                        'label': _(mapping_manager.get_field_display_name('quotation', 'quotation_number')),
                        'type': 'link',
                        'url_template': '/quotation/{id}/detail',
                        'width': '160px',
                        'render': 'render_quotation_number',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'owner',
                        'field': 'owner_id',
                        'label': _(mapping_manager.get_field_display_name('common', 'owner_id')),
                        'type': 'text',
                        'width': '100px',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'project_name',
                        'field': 'project_id',
                        'label': _(mapping_manager.get_field_display_name('project', 'project_name')),
                        'type': 'text',
                        'width': '200px',
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
        
        return render_template('quotation/list.html', 
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
                              list_config=list_config)
                              
    except Exception as e:
        logger.error(f"加载报价单列表时出错: {str(e)}", exc_info=True)

        # 尝试回滚数据库事务
        try:
            db.session.rollback()
            logger.info("数据库事务已回滚")
        except Exception as rollback_error:
            logger.error(f"数据库事务回滚失败: {str(rollback_error)}")

        # 获取错误处理器需要的默认配置变量
        from app.utils.i18n import get_current_language, get_default_currency, get_currency_symbol
        current_lang = get_current_language()
        amount_unit = '万美元' if current_lang == 'en' else '万元'
        default_currency = get_default_currency()
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
        return render_template('quotation/list.html', 
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
                              list_config=error_list_config)

@quotation.route('/api/quotations/filter', methods=['GET'])
@login_required
@permission_required('quotation', 'view')
def quotations_list_ajax():
    """报价单列表AJAX筛选API"""
    try:
        current_app.logger.info("AJAX端点被调用")
        
        # 获取搜索和筛选参数
        search = request.args.get('search', '').strip()
        owner_filter = request.args.get('owner_filter', '')
        project_type_filter = request.args.get('project_type_filter', '')
        project_stage_filter = request.args.get('project_stage_filter', '')
        
        # 分页参数 - 默认60条支持无限滚动
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 60, type=int)
        
        # 排序参数
        sort_field = request.args.get('sort_field', '')
        sort_direction = request.args.get('sort_direction', 'asc')
        
        # 限制每次加载数量范围
        if limit > 100:
            limit = 100  # 最大100条防止性能问题
        
        current_app.logger.info(f"筛选参数: search={search}, owner_filter={owner_filter}, project_type_filter={project_type_filter}")
        
        # 基础查询
        try:
            query = get_viewable_data(Quotation, current_user).options(joinedload(Quotation.project))
            current_app.logger.info("基础查询创建成功")
        except Exception as e:
            current_app.logger.error(f"基础查询创建失败: {e}")
            raise
        
        # 应用搜索条件
        if search:
            try:
                query = query.join(Project, Quotation.project_id == Project.id)
                query = query.filter(
                    or_(
                        Quotation.quotation_number.ilike(f'%{search}%'),
                        Project.project_name.ilike(f'%{search}%')
                    )
                )
                current_app.logger.info(f"应用搜索条件: {search}")
            except Exception as e:
                current_app.logger.error(f"应用搜索条件失败: {e}")
                # 继续执行，不中断
        
        # 应用筛选条件
        if owner_filter:
            try:
                query = query.filter(Quotation.owner_id == owner_filter)
                current_app.logger.info(f"应用负责人筛选: {owner_filter}")
            except Exception as e:
                current_app.logger.error(f"应用负责人筛选失败: {e}")
        
        if project_type_filter:
            try:
                # 如果还没有JOIN Project表，先JOIN
                if not search:  # 如果没有搜索，则还没有JOIN
                    query = query.join(Project, Quotation.project_id == Project.id)
                query = query.filter(Project.project_type == project_type_filter)
                current_app.logger.info(f"应用项目类型筛选: {project_type_filter}")
            except Exception as e:
                current_app.logger.error(f"应用项目类型筛选失败: {e}")
        
        if project_stage_filter:
            try:
                # 如果还没有JOIN Project表，先JOIN
                if not search and not project_type_filter:  # 如果前面都没有JOIN
                    query = query.join(Project, Quotation.project_id == Project.id)
                query = query.filter(Project.current_stage == project_stage_filter)
                current_app.logger.info(f"应用项目阶段筛选: {project_stage_filter}")
            except Exception as e:
                current_app.logger.error(f"应用项目阶段筛选失败: {e}")
        
        # 预加载关联数据
        query = query.options(
            joinedload(Quotation.project),
            joinedload(Quotation.owner),
            joinedload(Quotation.confirmer)
        )
        
        # 计算总数
        total_count = query.count()
        
        # 使用通用排序服务
        from app.utils.sorting_service import SortingService, create_user_relation_config, create_project_relation_config, create_basic_field_mappings
        
        # 创建排序配置
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
        
        # 创建排序服务并应用排序
        sorting_service = SortingService(Quotation, sorting_config)
        query = sorting_service.apply_sort(query, sort_field, sort_direction)
        
        # 获取报价单数据（应用分页）
        try:
            quotations = query.offset(offset).limit(limit).all()
            current_app.logger.info(f"查询到 {len(quotations)} 条报价单 (总数: {total_count})")
        except Exception as e:
            current_app.logger.error(f"查询报价单失败: {e}")
            raise
        
        # 为报价单数据添加项目名称（用于移动端显示）
        for quotation in quotations:
            try:
                if hasattr(quotation, 'project') and quotation.project:
                    quotation.project_name = getattr(quotation.project, 'project_name', '未知项目')
                else:
                    quotation.project_name = '未关联项目'
                
                # project_stage 和 project_type 是报价单模型自己的字段，不需要从project获取
                # 这些字段已经在数据库查询时自动加载了
                    
            except Exception as e:
                current_app.logger.error(f"处理报价单 {quotation.id} 的项目数据时出错: {e}")
                quotation.project_name = '数据错误'
            
        
        # 直接进行响应式渲染
        try:
            from flask import render_template_string
            from app.utils.mobile_helpers import is_mobile_request
            
            is_mobile = is_mobile_request()
            current_app.logger.info(f"移动端检测结果: {is_mobile}, mobile参数: {request.args.get('mobile')}")
            
            # 临时调试：在HTML中添加调试信息
            debug_info = f"<!-- DEBUG: is_mobile={is_mobile}, mobile_param={request.args.get('mobile')} -->"
            current_app.logger.info(f"🔍 AJAX调试: URL={request.url}, is_mobile={is_mobile}, User-Agent={request.headers.get('User-Agent', 'None')}")
            
            if is_mobile:
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
                    # 回退到桌面模板
                    html = debug_info + f"<!-- MOBILE RENDER FAILED: {str(render_error)} -->" + render_template('quotation/quotation_rows.html', quotations=quotations)
            else:
                # 桌面端：使用表格
                html = debug_info + "<!-- DESKTOP RENDER -->" + render_template('quotation/quotation_rows.html', quotations=quotations)
            current_app.logger.info("统一响应式渲染成功")
        except Exception as e:
            current_app.logger.error(f"统一响应式渲染失败: {e}")
            import traceback
            current_app.logger.error(f"完整异常堆栈: {traceback.format_exc()}")
            # 回退到传统桌面端渲染
            try:
                html = render_template('quotation/quotation_rows.html', quotations=quotations)
                current_app.logger.info("回退到传统模板渲染成功")
            except Exception as fallback_error:
                current_app.logger.error(f"回退渲染也失败: {fallback_error}")
                html = f'<tr><td colspan="8" class="text-center text-muted">渲染失败: {str(e)}</td></tr>'
        
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
            
            # 获取当前语言环境的目标货币
            from app.utils.i18n import get_current_language
            current_lang = get_current_language()
            target_currency = 'USD' if current_lang == 'en' else 'CNY'

            # 货币转换函数
            def calculate_converted_amount_ajax(quotations_query):
                quotations = quotations_query.all()
                total_converted = 0
                for quotation in quotations:
                    original_amount = quotation.amount or 0
                    original_currency = quotation.currency or 'CNY'
                    if original_amount > 0:
                        converted_amount = exchange_rate_service.convert_amount(
                            original_amount, original_currency, target_currency
                        )
                        total_converted += converted_amount
                return total_converted

            # 基于筛选后的数据计算统计
            total_stats_count = stats_query.count()
            total_stats_amount = round(calculate_converted_amount_ajax(stats_query) / 10000, 2)

            # 按审核状态统计 - 使用正确的字段名 approval_status
            approved_filter = stats_query.filter(Quotation.approval_status.in_(['discover_approved', 'embed_approved', 'pre_tender_approved', 'tendering_approved', 'awarded_approved', 'quoted_approved', 'signed_approved']))
            approved_count = approved_filter.count()
            approved_amount = round(calculate_converted_amount_ajax(approved_filter) / 10000, 2)

            pending_filter = stats_query.filter(Quotation.approval_status == 'pending')
            pending_count = pending_filter.count()
            pending_amount = round(calculate_converted_amount_ajax(pending_filter) / 10000, 2)

            rejected_filter = stats_query.filter(Quotation.approval_status == 'rejected')
            rejected_count = rejected_filter.count()
            rejected_amount = round(calculate_converted_amount_ajax(rejected_filter) / 10000, 2)
            
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
        from app.utils.i18n import get_current_language, get_default_currency, get_currency_symbol
        current_lang = get_current_language()
        default_currency = get_default_currency()
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

@quotation.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('quotation', 'create')  # 添加创建权限装饰器
def create_quotation():
    # 获取返回URL参数
    return_to = request.args.get('return_to')
    
    # 获取预设的项目ID
    preset_project_id = request.args.get('project_id')
    
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
                    currency=data.get('currency', 'CNY'),
                    owner_id=current_user.id
                )
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
                            currency=data.get('currency', 'CNY')  # 添加明细货币字段
                        )

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
                                current_app.logger.warning(f"配置产品 {config_info['detail'].product_name} 找不到父产品，parent_row_id={config_info['parent_row_id']}")

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
                    
                    # 异步触发报价单创建通知，避免阻塞响应
                    try:
                        from app.utils.notification_helpers import trigger_event_notification
                        from flask import url_for
                        import threading
                        from app.utils.solution_manager_notifications import notify_solution_managers_quotation_created
                        
                        # 在线程外获取app实例和必要数据
                        app = current_app._get_current_object()
                        quotation_owner_id = quotation.owner_id
                        quotation_id = quotation.id
                        
                        def send_notifications_async():
                            """异步发送通知"""
                            with app.app_context():
                                try:
                                    # 重新查询quotation对象以获取最新状态
                                    fresh_quotation = Quotation.query.get(quotation_id)
                                    if fresh_quotation:
                                        # 构建URL而不使用url_for
                                        quotation_url = f"http://localhost:10000/quotation/{quotation_id}/detail"
                                        
                                        # 触发报价单创建通知
                                        trigger_event_notification(
                                            event_key='quotation_created',
                                            target_user_id=quotation_owner_id,
                                            context={
                                                'quotation': fresh_quotation,
                                                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                'quotation_url': quotation_url,
                                                'current_year': datetime.now().year
                                            }
                                        )
                                        # 通知解决方案经理（异步）
                                        notify_solution_managers_quotation_created(fresh_quotation)
                                        app.logger.debug('异步报价单创建通知已发送')
                                except Exception as notify_err:
                                    app.logger.warning(f"异步触发报价单创建通知失败: {str(notify_err)}")
                        
                        # 启动异步通知线程
                        threading.Thread(target=send_notifications_async, daemon=True).start()
                        current_app.logger.debug('异步通知线程已启动')
                        
                    except Exception as notify_err:
                        logger.warning(f"启动异步通知失败: {str(notify_err)}")
                    
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
    
    # GET 请求处理
    # 只显示未有报价单的项目
    subquery = db.session.query(Quotation.project_id).distinct()
    projects = get_viewable_data(Project, current_user).filter(~Project.id.in_(subquery)).all()
    
    # 创建一个新的空报价单对象用于模板显示
    quotation = None  # 创建模式下设为None，让模板正确识别
    
    # 如果有预设的项目ID，设置默认选中项目
    selected_project = None
    if preset_project_id:
        project_obj = Project.query.get(preset_project_id)
        if project_obj:
            # 转换为字典以支持JSON序列化
            selected_project = {
                'id': project_obj.id,
                'project_name': project_obj.project_name,
                'display_name': project_obj.display_name,
                'authorization_code': project_obj.authorization_code
            }

    # 预加载项目关联的客户（如果有预设项目）
    preset_customers = []
    if preset_project_id:
        from app.models.project_customer_association import ProjectCustomerAssociation
        from app.models.customer import Contact
        from app.utils.access_control import can_view_company

        associations = ProjectCustomerAssociation.get_active_associations(preset_project_id)
        for assoc in associations:
            if assoc.company and can_view_company(current_user, assoc.company):
                # 查询主要联系人
                primary_contact = Contact.query.filter_by(
                    company_id=assoc.company.id,
                    is_primary=True
                ).first()

                preset_customers.append({
                    'id': assoc.company.id,
                    'company_name': assoc.company.company_name,
                    'contact_person': primary_contact.name if primary_contact else None
                })

    # 获取产品库中ID为1的产品的货币类型作为默认货币
    from app.models.product import Product
    default_currency = 'CNY'  # 默认为人民币
    try:
        reference_product = Product.query.get(1)
        if reference_product and reference_product.currency:
            default_currency = reference_product.currency
            current_app.logger.debug(f"使用产品ID=1的货币类型作为默认值: {default_currency}")
        else:
            current_app.logger.debug("产品ID=1不存在或没有货币信息，使用默认货币CNY")
    except Exception as e:
        current_app.logger.warning(f"获取默认货币时出错: {str(e)}，使用默认货币CNY")
    
    return render_template('quotation/create.html',
                         projects=projects,
                         today_date=datetime.now().strftime('%Y-%m-%d'),
                         quotation=quotation,
                         preset_project_id=preset_project_id,
                         selected_project=selected_project,
                         preset_customers=preset_customers,
                         currency_options=get_currency_type_options(),
                         return_to=return_to,
                         default_currency=default_currency,
                         quotation_details_json="[]",
                         CURRENCY_TYPE_OPTIONS=get_currency_type_options())

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

@quotation.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以编辑自己的报价单数据
def edit_quotation(id):
    # 获取返回URL参数
    return_to = request.args.get('return_to')

    try:
        quotation = Quotation.query.get_or_404(id)

        # 使用统一的数据权限检查（包含数据归属逻辑）
        if not can_edit_data(quotation, current_user):
            flash(_('您没有权限编辑此报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))
        
        # 检查报价单是否被锁定
        if quotation.is_locked:
            lock_info = quotation.lock_status_display
            flash(f'报价单已被锁定，无法编辑。锁定原因：{lock_info["reason"]}，锁定人：{lock_info["locked_by"]}', 'warning')
            return redirect(url_for('quotation.view_quotation', id=id))
        
        # 按ID排序获取报价单明细（保留用户添加时的原有顺序）
        # 不再按产品库分类重新排序，避免每次编辑都打乱用户的排列
        quotation_details = db.session.query(QuotationDetail)\
            .filter(QuotationDetail.quotation_id == quotation.id)\
            .order_by(QuotationDetail.id.asc())\
            .all()

        # 替换原有的details
        quotation.details = quotation_details
        
        # 处理报价单明细数据
        for detail in quotation.details:
            # 确保total_price映射到subtotal
            detail.subtotal = detail.total_price
            # 确保discount映射到discount_rate（转换为百分比）
            detail.discount_rate = detail.discount * 100 if detail.discount is not None else 100.0
            # 确保正确设置product_mn字段
            if not hasattr(detail, 'product_mn') or detail.product_mn is None:
                # 尝试从产品表中获取MN号（使用公共辅助函数）
                product = find_product_by_name_and_model(detail.product_name, detail.product_model)
                if product:
                    detail.product_mn = product.product_mn
                else:
                    detail.product_mn = ''
        
        # 准备报价单详情的JSON数据，以便在模板中使用
        quotation_details = []
        for detail in quotation.details:
            try:
                # 检查是否为临时产品
                product_mn = str(getattr(detail, 'product_mn', '') or '')
                is_temp_product = product_mn.startswith('TEMP_')
                
                # 安全地获取所有字段，确保没有None或Undefined值，并强制类型转换
                detail_data = {
                    'product_name': str(detail.product_name or ''),
                    'product_model': str(detail.product_model or ''),
                    'product_desc': str(detail.product_desc or ''),
                    'brand': str(detail.brand or ''),
                    'unit': str(detail.unit or '个'),
                    'market_price': float(detail.market_price or 0),
                    'discount_rate': float(getattr(detail, 'discount_rate', detail.discount * 100 if detail.discount is not None else 100.0)),
                    'unit_price': float(detail.unit_price or 0),
                    'quantity': int(detail.quantity or 1),
                    'subtotal': float(detail.total_price or 0),
                    'product_mn': product_mn,
                    'is_temp': is_temp_product,  # 添加临时产品标识
                    'status': 'temp' if is_temp_product else 'regular',  # 添加状态标识
                    # 配置产品字段
                    'is_configuration': getattr(detail, 'is_accessory', False),
                    'parent_item_id': getattr(detail, 'parent_item_id', None),  # 传递parent_item_id，前端需要重建row关系
                    'config_type': getattr(detail, 'config_type', None),
                    'config_base_quantity': getattr(detail, 'config_base_quantity', None)
                }
                
                # 如果是临时产品，添加调试日志
                if is_temp_product:
                    current_app.logger.info(f"编辑页面检测到临时产品: {detail.product_name}, MN: {product_mn}")
                    # 确保单价和小计正确传递
                    detail_data['total_price'] = detail_data['subtotal']
                quotation_details.append(detail_data)
            except (TypeError, ValueError, AttributeError) as detail_error:
                current_app.logger.error(f"处理明细项时出错: {detail_error}")
                current_app.logger.error(f"问题明细: {detail}")
                # 添加一个安全的默认明细项
                quotation_details.append({
                    'product_name': '数据错误',
                    'product_model': '',
                    'product_desc': '',
                    'brand': '',
                    'unit': '个',
                    'market_price': 0.0,
                    'discount_rate': 100.0,
                    'unit_price': 0.0,
                    'quantity': 1,
                    'subtotal': 0.0,
                    'product_mn': ''
                })
        
        import json
        
        def safe_serialize_check(obj, path="root"):
            """递归检查对象的可序列化性"""
            try:
                if obj is None:
                    return True
                elif isinstance(obj, (str, int, float, bool)):
                    return True
                elif isinstance(obj, (list, tuple)):
                    for i, item in enumerate(obj):
                        safe_serialize_check(item, f"{path}[{i}]")
                    return True
                elif isinstance(obj, dict):
                    for key, value in obj.items():
                        safe_serialize_check(value, f"{path}.{key}")
                    return True
                else:
                    current_app.logger.error(f"🚨 发现不可序列化对象在 {path}: {obj} (类型: {type(obj).__name__})")
                    return False
            except Exception as e:
                current_app.logger.error(f"🚨 检查序列化时出错在 {path}: {e}")
                return False
        
        try:
            # 先检查数据结构
            current_app.logger.info("开始检查quotation_details的序列化安全性")
            safe_serialize_check(quotation_details, "quotation_details")
            
            quotation_details_json = json.dumps(quotation_details)
            current_app.logger.info("✅ JSON序列化成功")
        except (TypeError, ValueError) as e:
            current_app.logger.error(f"❌ JSON序列化错误: {str(e)}")
            current_app.logger.error(f"错误类型: {type(e).__name__}")
            
            # 逐个检查每个明细项，找出有问题的字段
            for i, detail_dict in enumerate(quotation_details):
                current_app.logger.error(f"检查明细 {i}: 开始检查字段")
                for key, value in detail_dict.items():
                    current_app.logger.error(f"  字段 {key}: {repr(value)} (类型: {type(value).__name__})")
                    try:
                        json.dumps(value)
                    except (TypeError, ValueError) as field_error:
                        current_app.logger.error(f"  ❌ 字段 {key} 序列化失败: {field_error}")
            
            # 提供一个安全的默认值
            quotation_details_json = '[]'
        
        # 获取所有项目
        projects = get_viewable_data(Project, current_user).all()
        
        if request.method == 'POST':
            try:
                # 捕获修改前的值
                from app.utils.change_tracker import ChangeTracker
                old_values = ChangeTracker.capture_old_values(quotation)
                
                # 捕获修改前的产品明细签名，用于检测变化
                old_product_signature = quotation.calculate_product_signature()
                
                # 验证必填字段
                if not request.form.get('project_id'):
                    raise ValueError('项目不能为空')
                
                # 获取关联的项目
                project = Project.query.get(request.form.get('project_id'))
                if project:
                    # 更新报价单的项目相关信息
                    quotation.project_id = project.id
                    quotation.project_stage = project.current_stage
                    quotation.project_type = project.project_type

                # 更新客户和联系人
                customer_id = request.form.get('customer_id')
                contact_id = request.form.get('contact_id')
                if customer_id:
                    quotation.customer_id = int(customer_id)
                if contact_id:
                    quotation.contact_id = int(contact_id) if contact_id else None

                # 更新报价单货币
                currency = request.form.get('currency', 'CNY')
                quotation.currency = currency
                
                # 安全地移除事件监听器，避免重复触发
                try:
                    event.remove(QuotationDetail, 'after_delete', update_quotation_product_signature)
                except Exception:
                    # 如果监听器不存在，忽略错误
                    pass
                
                try:
                    # 先移除旧的明细
                    for detail in quotation.details:
                        db.session.delete(detail)
                    quotation.details.clear()
                    
                    # 获取产品明细数据 - 支持JSON格式和传统表单格式
                    import json
                    product_details_json = request.form.get('product_details')
                    
                    if product_details_json:
                        # 新版：从JSON字段获取数据
                        try:
                            product_details = json.loads(product_details_json)
                            if not product_details:
                                raise ValueError('请至少添加一个产品')
                        except json.JSONDecodeError as e:
                            raise ValueError(f'产品数据格式错误：{str(e)}')
                    else:
                        # 旧版：从传统表单字段获取数据（兼容性支持）
                        product_names = request.form.getlist('product_name[]')
                        product_models = request.form.getlist('product_model[]')
                        product_descs = request.form.getlist('product_spec[]')
                        brands = request.form.getlist('product_brand[]')
                        units = request.form.getlist('product_unit[]')
                        discounts = request.form.getlist('discount_rate[]')
                        market_prices = request.form.getlist('product_price[]')
                        quantities = request.form.getlist('quantity[]')
                        product_mns = request.form.getlist('product_mn[]')
                        
                        # 验证是否有产品明细
                        if not product_names:
                            raise ValueError('请至少添加一个产品')
                        
                        # 验证所有列表长度是否一致
                        lists_length = [len(x) for x in [
                            product_names, product_models, product_descs, brands,
                            units, discounts, market_prices, quantities
                        ]]
                        if len(set(lists_length)) > 1:
                            raise ValueError('产品数据不完整，请检查后重试')
                        
                        # 转换为JSON格式以便统一处理
                        product_details = []
                        for i in range(len(product_names)):
                            product_details.append({
                                'product_name': product_names[i],
                                'product_model': product_models[i],
                                'product_desc': product_descs[i] if i < len(product_descs) else '',
                                'brand': brands[i] if i < len(brands) else '',
                                'unit': units[i] if i < len(units) else '',
                                'discount': float(discounts[i]) if i < len(discounts) and discounts[i] else 100,
                                'market_price': float(market_prices[i]) if i < len(market_prices) and market_prices[i] else 0,
                                'quantity': int(quantities[i]) if i < len(quantities) and quantities[i] else 1,
                                'product_mn': product_mns[i] if i < len(product_mns) else ''
                            })
                    
                    # 获取报价单货币，用于明细记录
                    detail_currency = request.form.get('currency', 'CNY')

                    # 两阶段保存：先创建所有明细，再建立父子关系
                    detail_id_map = {}  # {row_id: detail对象}
                    pending_configs = []  # 待处理的配置产品列表

                    total_amount = 0.0
                    for i, detail_data in enumerate(product_details):
                        try:
                            # 验证必填字段
                            product_name = str(detail_data.get('product_name', '')).strip()
                            product_model = str(detail_data.get('product_model', '')).strip()
                            
                            if not product_name:
                                raise ValueError(f'第 {i+1} 行产品名称不能为空')
                            
                            # 编辑模式下，如果product_model为空，尝试从原有数据获取或使用默认值
                            if not product_model:
                                # 尝试从原有明细中找到对应的产品型号
                                if i < len(quotation.details):
                                    original_detail = quotation.details[i]
                                    if original_detail.product_model:
                                        product_model = original_detail.product_model
                                        current_app.logger.info(f'第 {i+1} 行使用原有产品型号: {product_model}')
                                    else:
                                        # 如果原有数据也没有型号，使用默认值
                                        product_model = 'N/A'
                                        current_app.logger.info(f'第 {i+1} 行使用默认产品型号: {product_model}')
                                else:
                                    # 新增行且没有型号，使用默认值
                                    product_model = 'N/A'
                                    current_app.logger.info(f'第 {i+1} 行（新增）使用默认产品型号: {product_model}')
                            
                            # 清理并验证数值字段
                            try:
                                market_price_str = str(detail_data.get('market_price', '0')).replace(',', '')
                                discount_str = str(detail_data.get('discount', '100')).replace(',', '')
                                quantity_str = str(detail_data.get('quantity', '1')).replace(',', '')
                                
                                market_price = float(market_price_str) if market_price_str else 0
                                discount = float(discount_str) if discount_str else 100
                                quantity = int(float(quantity_str)) if quantity_str else 1
                                
                                if market_price < 0:
                                    raise ValueError(f'第 {i+1} 行市场价格不能为负数')
                                if discount < 0:
                                    raise ValueError(f'第 {i+1} 行折扣率不能为负数')
                                if quantity <= 0:
                                    raise ValueError(f'第 {i+1} 行数量必须大于0')
                            except (ValueError, TypeError) as e:
                                if str(e).startswith('第'):
                                    raise e
                                raise ValueError(f'第 {i+1} 行数据格式错误：{str(e)}')
                            
                            # 获取单价（如果前端提供了的话，优先使用；否则根据市场价和折扣率计算）
                            unit_price_str = str(detail_data.get('unit_price', '0')).replace(',', '')
                            provided_unit_price = float(unit_price_str) if unit_price_str else 0
                            
                            # 如果前端提供了单价且大于0，使用它；否则根据市场价和折扣率计算
                            if provided_unit_price > 0:
                                discounted_price = provided_unit_price
                            else:
                                discounted_price = market_price * (discount / 100)
                            
                            # 获取小计（如果前端提供了的话，优先使用；否则计算）
                            total_price_str = str(detail_data.get('total_price', '0')).replace(',', '')
                            provided_total_price = float(total_price_str) if total_price_str else 0
                            
                            # 如果前端提供了小计且大于0，使用它；否则计算
                            if provided_total_price > 0:
                                subtotal = provided_total_price
                            else:
                                subtotal = discounted_price * quantity
                            
                            total_amount += subtotal

                            # 创建明细记录
                            detail = QuotationDetail(
                                product_name=product_name,
                                product_model=product_model,
                                product_desc=str(detail_data.get('product_desc', '')).strip() or None,
                                brand=str(detail_data.get('brand', '')).strip() or None,
                                unit=str(detail_data.get('unit', '')).strip() or None,
                                discount=discount/100,
                                market_price=market_price,
                                quantity=quantity,
                                unit_price=discounted_price,
                                total_price=subtotal,
                                product_mn=str(detail_data.get('product_mn', '')).strip() or None,
                                currency=detail_currency
                            )

                            # 处理配置产品相关字段
                            is_configuration = detail_data.get('is_configuration', False)
                            if is_configuration:
                                detail.is_accessory = True
                                detail.is_editable = False
                                detail.config_type = detail_data.get('config_type')
                                detail.config_base_quantity = int(detail_data.get('config_base_quantity', 1))
                                detail.quantity_synced = detail_data.get('quantity_synced', True)  # ✅ 保存同步状态

                                # 添加到待处理配置列表
                                pending_configs.append({
                                    'detail': detail,
                                    'parent_row_id': detail_data.get('parent_row_id')
                                })
                            else:
                                # 主产品：记录row_id映射
                                row_id = detail_data.get('row_id')
                                if row_id:
                                    detail_id_map[row_id] = detail

                            # 计算植入小计
                            detail.calculate_prices()

                            quotation.details.append(detail)
                        except Exception as e:
                            raise ValueError(f'处理第 {i+1} 行数据时出错：{str(e)}')
                    
                    # 更新报价单总金额
                    quotation.amount = total_amount
                    
                    # 计算植入总额
                    quotation.calculate_implant_total_amount()

                    # 手动更新时间戳，确保updated_at字段正确
                    quotation.updated_at = datetime.utcnow()

                    # 第二阶段：Flush获取ID，然后建立父子关系
                    if pending_configs:
                        current_app.logger.info(f"开始处理 {len(pending_configs)} 个配置产品的父子关系")
                        db.session.flush()  # Flush以获取所有detail的ID

                        for config_info in pending_configs:
                            parent_detail = detail_id_map.get(config_info['parent_row_id'])
                            if parent_detail:
                                config_info['detail'].parent_item_id = parent_detail.id
                                current_app.logger.debug(f"配置产品 {config_info['detail'].product_name} 关联到父产品 {parent_detail.product_name}")
                            else:
                                current_app.logger.warning(f"配置产品 {config_info['detail'].product_name} 找不到父产品，parent_row_id={config_info['parent_row_id']}")

                        current_app.logger.info(f"配置产品父子关系建立完成")

                finally:
                    # 安全地重新注册事件监听器
                    try:
                        if not event.contains(QuotationDetail, 'after_insert', update_quotation_product_signature):
                            event.listen(QuotationDetail, 'after_insert', update_quotation_product_signature)
                        if not event.contains(QuotationDetail, 'after_update', update_quotation_product_signature):
                            event.listen(QuotationDetail, 'after_update', update_quotation_product_signature)
                        if not event.contains(QuotationDetail, 'after_delete', update_quotation_product_signature):
                            event.listen(QuotationDetail, 'after_delete', update_quotation_product_signature)
                    except Exception:
                        # 忽略重新注册时的错误
                        pass
                    
                    # 在重新注册事件监听器后立即进行签名检测和状态处理
                    try:
                        # 检测产品明细是否发生变化
                        new_product_signature = quotation.calculate_product_signature()
                        product_details_changed = old_product_signature != new_product_signature
                        
                        # 如果产品明细发生关键变化，手动清除确认状态
                        if product_details_changed and quotation.confirmation_badge_status == 'confirmed':
                            quotation.confirmation_badge_status = 'none'
                            quotation.confirmation_badge_color = None
                            quotation.confirmed_by = None
                            quotation.confirmed_at = None
                            current_app.logger.info(f"报价单 {quotation.id} 的产品明细发生关键变化（行数或MN号），已手动清除确认状态")
                        
                        # 更新产品签名
                        quotation.product_signature = new_product_signature
                        current_app.logger.debug(f"产品签名更新: {old_product_signature} -> {new_product_signature}, 变化: {product_details_changed}")
                        
                        # 临时再次禁用事件监听器，避免在提交时触发
                        try:
                            event.remove(QuotationDetail, 'after_insert', update_quotation_product_signature)
                            event.remove(QuotationDetail, 'after_update', update_quotation_product_signature)
                            event.remove(QuotationDetail, 'after_delete', update_quotation_product_signature)
                        except Exception:
                            # 如果监听器不存在，忽略错误
                            pass
                        
                    except Exception as signature_error:
                        current_app.logger.error(f"处理产品签名和确认状态时出错: {str(signature_error)}")
                
                # 记录变更历史
                try:
                    new_values = ChangeTracker.get_new_values(quotation, old_values.keys())
                    ChangeTracker.log_update(quotation, old_values, new_values)
                except Exception as track_err:
                    current_app.logger.warning(f"记录报价单变更历史失败: {str(track_err)}")
                
                # 强制刷新项目金额
                project = Project.query.get(quotation.project_id)
                if project:
                    total = db.session.query(db.func.sum(Quotation.amount)).filter(Quotation.project_id==project.id).scalar() or 0.0
                    project.quotation_customer = total
                    
                    # 更新关联项目的活跃度
                    try:
                        update_active_status(project)
                        current_app.logger.debug(f"报价单更新后更新项目 {project.id} 活跃度")
                    except Exception as activity_err:
                        current_app.logger.warning(f"更新项目活跃度失败: {str(activity_err)}")
                        
                db.session.commit()
                
                flash(_('报价单更新成功！'), 'success')
                return redirect(url_for('quotation.view_quotation', id=quotation.id))
                
            except ValueError as e:
                db.session.rollback()
                flash(str(e), 'error')
                return render_template('quotation/edit_new.html', 
                                     quotation=quotation,
                                     projects=projects,
                                     today_date=datetime.now().strftime('%Y-%m-%d'),
                                     quotation_details_json=quotation_details_json,
                                     currency_options=get_currency_type_options(),
                                     return_to=return_to)
            except Exception as e:
                db.session.rollback()
                flash(_('报价单更新失败：%s') % str(e), 'danger')
                return render_template('quotation/edit_new.html', 
                                     quotation=quotation,
                                     projects=projects,
                                     today_date=datetime.now().strftime('%Y-%m-%d'),
                                     quotation_details_json=quotation_details_json,
                                     currency_options=get_currency_type_options(),
                                     return_to=return_to)
        
        # GET请求 - 在渲染模板前检查所有对象
        try:
            current_app.logger.info("准备渲染编辑模板，检查传递的数据")
            
            # 检查quotation对象
            current_app.logger.info(f"quotation对象: {quotation}")
            current_app.logger.info(f"quotation类型: {type(quotation)}")
            
            # 检查projects对象
            current_app.logger.info(f"projects数量: {len(projects) if projects else 'None'}")
            
            # 检查currency_options
            currency_options = get_currency_type_options()
            current_app.logger.info(f"currency_options类型: {type(currency_options)}")
            
            # 安全检查quotation_details_json
            current_app.logger.info(f"quotation_details_json长度: {len(quotation_details_json)}")
            
            # 添加缺失的default_currency变量
            default_currency = 'CNY'
            try:
                from app.models.product import Product
                reference_product = Product.query.get(1)
                if reference_product and reference_product.currency:
                    default_currency = reference_product.currency
            except Exception as e:
                current_app.logger.warning(f"获取默认货币时出错: {str(e)}")
            
            # 创建一个安全的quotation对象，保持属性访问方式
            class SafeQuotation:
                def __init__(self, original_quotation):
                    self.id = original_quotation.id
                    self.quotation_number = getattr(original_quotation, 'quotation_number', None)
                    self.project_id = original_quotation.project_id
                    self.customer_id = original_quotation.customer_id  # 添加客户ID
                    self.contact_id = original_quotation.contact_id  # 添加联系人ID
                    self.amount = float(original_quotation.amount or 0)
                    self.currency = str(original_quotation.currency or 'CNY')
                    self.details = original_quotation.details  # 保留明细数据
                    self.project = original_quotation.project  # 保留项目数据
            
            # 在创建SafeQuotation之前检查原始对象
            current_app.logger.info(f"原始quotation.quotation_number: {getattr(quotation, 'quotation_number', 'MISSING')}")
            current_app.logger.info(f"原始quotation.project: {getattr(quotation, 'project', 'MISSING')}")
            if hasattr(quotation, 'project') and quotation.project:
                current_app.logger.info(f"原始quotation.project.owner: {getattr(quotation.project, 'owner', 'MISSING')}")
            
            safe_quotation = SafeQuotation(quotation)
            
            # 测试最简单的模板渲染
            try:
                simple_data = {
                    'quotation': safe_quotation,  # 使用对象而非字典
                    'projects': projects,
                    'today_date': datetime.now().strftime('%Y-%m-%d'),
                    'quotation_details_json': quotation_details_json,
                    'currency_options': get_currency_type_options(),
                    'default_currency': default_currency,
                    'existing_details': quotation_details,  # 添加现有明细数据
                    'return_to': return_to or ''
                }
                current_app.logger.info("尝试渲染简化数据")
                return render_template('quotation/edit_new.html', **simple_data)
            except Exception as simple_error:
                current_app.logger.error(f"简化数据渲染也失败: {simple_error}")
                # 如果连简化数据都失败，可能是模板本身的问题
                # 尝试渲染一个更基础的模板
                return f"<h1>编辑报价单 {quotation.id}</h1><p>模板渲染错误: {simple_error}</p>"
        except Exception as render_error:
            current_app.logger.error(f"模板渲染失败: {render_error}")
            current_app.logger.error(f"render_error类型: {type(render_error)}")
            raise render_error
        
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
        
        # 强制刷新项目金额
        project = Project.query.get(new_quotation.project_id)
        if project:
            total = db.session.query(db.func.sum(Quotation.amount)).filter(Quotation.project_id==project.id).scalar() or 0.0
            project.quotation_customer = total
        db.session.commit()
        
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

        return jsonify({'customers': companies})
    except Exception as e:
        print(f"获取项目客户列表时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

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
                    'product_name': p.product_name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'status': p.status,  # 添加产品状态
                    'currency': p.currency or 'CNY'  # 添加货币信息
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}')
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

        # 修复SQL错误：SELECT DISTINCT时，ORDER BY字段必须在SELECT列表中
        # 按产品分类的业务顺序（ProductCategory.id）排序
        categories = db.session.query(
            ProductCategory.id,
            ProductCategory.name
        ).join(
            Product, Product.category_id == ProductCategory.id
        ).filter(
            Product.status != '停产'
        ).distinct().order_by(ProductCategory.id).all()

        category_list = [cat[1] for cat in categories]  # cat[1] 是 name
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
        
        # 查询指定类别的产品，包括停产产品，添加按ID排序
        products = Product.query.filter_by(
            category=category
        ).order_by(Product.id).all()  # 移除停产过滤，包括所有产品
        
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
                    'product_name': p.product_name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn,
                    'status': p.status,  # 添加产品状态
                    'currency': p.currency or 'CNY'  # 添加货币字段
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}, MN: {p.product_mn}, 货币: {p.currency}')
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
                    'product_name': p.product_name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn,
                    'currency': p.currency or 'CNY',  # 添加货币字段
                    'status': p.status  # 添加产品状态字段
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}, 型号: {p.model}, 货币: {p.currency}')
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
                    'product_name': p.product_name,
                    'model': p.model,  # 修复：使用正确的字段名
                    'specification': p.specification,  # 修复：使用正确的字段名
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn,
                    'currency': p.currency or 'CNY',  # 添加货币字段
                    'image_path': product_image,  # 添加图片路径
                    'code_specs': code_specs,  # 编码规格（默认显示）
                    'non_code_specs': non_code_specs  # 非编码规格（默认折叠）
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}, 规格: {p.specification}')
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
                'currency': 'CNY',
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
                    'currency': 'CNY',
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
        # 项目权限校验 - 使用动态权限检查而不是硬编码角色
        if quotation.project:
            # 统一处理角色字符串，去除空格
            user_role = current_user.role.strip() if current_user.role else ''
            
            # 特殊角色：财务总监、解决方案经理、产品经理可以查看所有项目的报价单
            is_special_role = user_role in ['finance_director', 'finace_director', 'solution_manager', 'solution', 'product_manager', 'product']
            
            # 渠道经理可以查看渠道跟进项目
            is_channel_manager = user_role == 'channel_manager'
            is_channel_project = quotation.project.project_type == 'channel_follow'
            
            # 营销总监可以查看销售重点和渠道跟进项目
            is_sales_director = user_role == 'sales_director'
            is_marketing_project = quotation.project.project_type in ['sales_focus', 'sales_key', 'channel_follow']
            
            # 检查权限：特殊角色 OR (渠道经理 AND 渠道项目) OR (营销总监 AND 营销项目) OR 常规项目权限
            if not (is_special_role or (is_channel_manager and is_channel_project) or (is_sales_director and is_marketing_project) or can_view_project(current_user, quotation.project)):
                logger.debug(f"{current_user.username} 无权访问报价单 {quotation.id} 关联项目 {quotation.project_id}")
                flash(_('您没有权限查看该报价单关联的项目'), 'danger')
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

        # 查询可选新拥有人
        all_users = []
        if can_change_quotation_owner(current_user, quotation):
            from app.permissions import is_admin_or_ceo
            if is_admin_or_ceo():
                all_users = User.query.all()
            elif getattr(current_user, 'is_department_manager', False) or current_user.role == 'sales_director':
                # 部门负责人只能在本部门进行转移
                all_users = User.query.filter(
                    or_(User.role == 'admin', User._is_active == True),
                    User.department == current_user.department
                ).all()
            else:
                # 其他人只能改为自己
                all_users = User.query.filter(User.id.in_([current_user.id, quotation.owner_id])).all()
            if not all_users:
                all_users = User.query.filter(User.id.in_([current_user.id, quotation.owner_id])).all()
        has_change_owner_permission = can_change_quotation_owner(current_user, quotation)
        
        # 生成用户树状数据
        from app.utils.user_helpers import generate_user_tree_data
        user_tree_data = None
        if has_change_owner_permission:
            filter_by_dept = not is_admin_or_ceo()
            user_tree_data = generate_user_tree_data(filter_by_department=filter_by_dept)
        
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
        
        return render_template('quotation/detail.html', 
                             quotation=quotation, 
                             all_users=all_users, 
                             has_change_owner_permission=has_change_owner_permission, 
                             user_tree_data=user_tree_data,
                             approval_instance=approval_instance,
                             current_approval_step=current_approval_step,
                             can_current_user_approve=can_current_user_approve,
                             can_edit_this_quotation=can_edit_this_quotation,
                             can_delete_this_quotation=can_delete_this_quotation)
    except Exception as e:
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
        
        # 检查报价单是否被锁定
        if quotation.is_locked:
            lock_info = quotation.lock_status_display
            return jsonify({
                'status': 'error',
                'message': f'报价单已被锁定，无法编辑。锁定原因：{lock_info["reason"]}，锁定人：{lock_info["locked_by"]}'
            }), 403
        
        # 捕获修改前的值
        from app.utils.change_tracker import ChangeTracker
        old_values = ChangeTracker.capture_old_values(quotation)
        
        # 捕获修改前的产品明细签名，用于检测变化
        old_product_signature = quotation.calculate_product_signature()
        
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
        quotation.currency = data.get('currency', 'CNY')  # 添加货币字段更新
        # 手动更新时间戳，确保updated_at字段正确
        quotation.updated_at = datetime.utcnow()
        current_app.logger.info(f'直接保存前端总金额到报价单: {total_amount}, 货币: {quotation.currency}')
        
        # 临时禁用事件监听器，避免删除重建过程中触发不必要的签名变化
        try:
            event.remove(QuotationDetail, 'after_insert', update_quotation_product_signature)
            event.remove(QuotationDetail, 'after_update', update_quotation_product_signature)
            event.remove(QuotationDetail, 'after_delete', update_quotation_product_signature)
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
            
            # 添加新的明细项
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
            
            current_app.logger.debug(f'开始处理 {len(details)} 个明细项')
            
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
                    # 安全地获取数值字段 - 直接使用前端数据
                    try:
                        market_price = float(detail.get('market_price', 0))
                        current_app.logger.info(f'第 {index+1} 行 - 直接保存前端市场价格: {market_price}')
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
                        current_app.logger.debug(f'第 {index+1} 行数量: {quantity}')
                        
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
                        current_app.logger.info(f'第 {index+1} 行 - 直接保存前端单价: {unit_price}')
                        
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
                    
                    try:
                        total_price = float(detail.get('total_price', 0))
                        current_app.logger.info(f'第 {index+1} 行 - 直接保存前端小计: {total_price}')
                        
                        if total_price < 0:
                            total_price = 0
                            error_msg = f"第 {index+1} 行小计不能为负数，已设为0"
                            current_app.logger.warning(error_msg)
                            detail_errors.append(error_msg)
                    except (ValueError, TypeError) as e:
                        # 保持原有逻辑：如果小计无效，从单价和数量重新计算
                        total_price = unit_price * quantity
                        error_msg = f"第 {index+1} 行小计格式无效，已重新计算为: {total_price}"
                        current_app.logger.warning(f"{error_msg}: {str(e)}")
                        detail_errors.append(error_msg)
                    
                    # 检查是否为临时产品并设置标识
                    product_mn = detail.get('product_mn', '')
                    if detail.get('is_temp') or detail.get('temp_product_id') or detail.get('status') == 'temp':
                        # 为临时产品添加特殊前缀标识
                        if not product_mn.startswith('TEMP_'):
                            product_mn = f"TEMP_{detail.get('temp_product_id', 'MANUAL')}"
                        current_app.logger.info(f'第 {index+1} 行 - 检测到临时产品，标识: {product_mn}')
                    
                    # 创建新明细 - 直接保存前端数据，不进行重新计算
                    new_detail = QuotationDetail(
                        quotation_id=id,
                        product_name=product_name,
                        product_model=detail.get('product_model', ''),
                        product_desc=detail.get('product_desc', ''),
                        brand=detail.get('brand', ''),
                        unit=detail.get('unit', ''),
                        quantity=quantity,
                        discount=discount,
                        market_price=market_price,  # 直接使用前端的市场价格
                        unit_price=unit_price,     # 直接使用前端的单价
                        total_price=total_price,   # 直接使用前端的小计
                        product_mn=product_mn,     # 包含临时产品标识的料号
                        currency=data.get('currency', 'CNY')
                    )
                    
                    # 只计算植入小计，不修改其他价格字段
                    new_detail.calculate_implant_subtotal_only()
                    
                    current_app.logger.debug(f'创建第 {index+1} 行明细项 - 市场价: {market_price}, 单价: {unit_price}, 小计: {total_price}')
                    quotation.details.append(new_detail)
                except Exception as item_error:
                    error_msg = f"处理第 {index+1} 行明细时出错: {str(item_error)}"
                    current_app.logger.error(error_msg)
                    detail_errors.append(error_msg)
            
            # 在提交前进行签名检测和状态处理
            try:
                # 检测产品明细是否发生变化
                new_product_signature = quotation.calculate_product_signature()
                product_details_changed = old_product_signature != new_product_signature
                
                # 如果产品明细发生关键变化，手动清除确认状态
                if product_details_changed and quotation.confirmation_badge_status == 'confirmed':
                    quotation.confirmation_badge_status = 'none'
                    quotation.confirmation_badge_color = None
                    quotation.confirmed_by = None
                    quotation.confirmed_at = None
                    current_app.logger.info(f"报价单 {quotation.id} 的产品明细发生关键变化（行数或MN号），已手动清除确认状态")
                
                # 更新产品签名
                quotation.product_signature = new_product_signature
                current_app.logger.debug(f"产品签名更新: {old_product_signature} -> {new_product_signature}, 变化: {product_details_changed}")
                
            except Exception as signature_error:
                current_app.logger.error(f"处理产品签名和确认状态时出错: {str(signature_error)}")
            
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
                if not event.contains(QuotationDetail, 'after_insert', update_quotation_product_signature):
                    event.listen(QuotationDetail, 'after_insert', update_quotation_product_signature)
                if not event.contains(QuotationDetail, 'after_update', update_quotation_product_signature):
                    event.listen(QuotationDetail, 'after_update', update_quotation_product_signature)
                if not event.contains(QuotationDetail, 'after_delete', update_quotation_product_signature):
                    event.listen(QuotationDetail, 'after_delete', update_quotation_product_signature)
                current_app.logger.debug("事件监听器已安全恢复")
            except Exception as restore_error:
                current_app.logger.error(f"恢复事件监听器时出错: {str(restore_error)}")
        
        # 记录变更历史
        try:
            new_values = ChangeTracker.get_new_values(quotation, old_values.keys())
            ChangeTracker.log_update(quotation, old_values, new_values)
        except Exception as track_err:
            current_app.logger.warning(f"记录报价单变更历史失败: {str(track_err)}")
        
        # 强制刷新项目金额
        try:
            project = Project.query.get(quotation.project_id)
            if project:
                total = db.session.query(db.func.sum(Quotation.amount)).filter(Quotation.project_id==project.id).scalar() or 0.0
                project.quotation_customer = total
            db.session.commit()
        except Exception as project_update_error:
            current_app.logger.warning(f"更新项目金额失败: {str(project_update_error)}")
        
        # 异步触发通知，避免阻塞保存操作
        try:
            from app.utils.notification_helpers import trigger_event_notification
            from flask import url_for
            import threading
            from app.utils.solution_manager_notifications import notify_solution_managers_quotation_created
            
            # 在线程外获取app实例和必要数据
            app = current_app._get_current_object()
            quotation_owner_id = quotation.owner_id
            quotation_id = quotation.id
            
            def send_notifications_async():
                """异步发送通知"""
                with app.app_context():
                    try:
                        # 重新查询quotation对象以获取最新状态
                        fresh_quotation = Quotation.query.get(quotation_id)
                        if fresh_quotation:
                            # 构建URL而不使用url_for
                            quotation_url = f"http://localhost:10000/quotation/{quotation_id}/detail"
                            
                            # 触发报价单更新通知（而不是创建通知）
                            trigger_event_notification(
                                event_key='quotation_updated',
                                target_user_id=quotation_owner_id,
                                context={
                                    'quotation': fresh_quotation,
                                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'quotation_url': quotation_url,
                                    'current_year': datetime.now().year
                                }
                            )
                            app.logger.debug('异步事件通知已触发')
                    except Exception as notify_err:
                        app.logger.warning(f"异步触发通知失败: {str(notify_err)}")
            
            # 启动异步通知线程
            threading.Thread(target=send_notifications_async, daemon=True).start()
            current_app.logger.debug('异步通知线程已启动')
            
        except Exception as notify_err:
            current_app.logger.warning(f"启动异步通知失败: {str(notify_err)}")
        
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

def can_view_quotation(user, quotation):
    """
    判断用户是否有权查看该报价单：
    1. 归属人
    2. 厂商负责人（项目的厂商负责人可以查看项目相关的报价单）
    3. 归属链
    4. 基于四级权限系统的访问控制
    5. 特殊角色权限
    暂不考虑共享
    """
    if user.role == 'admin':
        return True
    if user.id == quotation.owner_id:
        return True
    
    # 厂商负责人可以查看项目相关的报价单
    if (hasattr(quotation, 'project') and quotation.project and 
        hasattr(quotation.project, 'vendor_sales_manager_id') and 
        quotation.project.vendor_sales_manager_id == user.id):
        return True
    
    # 统一处理角色字符串，去除空格
    user_role = user.role.strip() if user.role else ''
    
    # 财务总监可以查看所有报价单
    if user_role in ['finance_director', 'finace_director']:
        return True
    
    # 🔧 修复：使用四级权限系统进行权限判断，但不阻断后续检查
    if user.has_permission('quotation', 'view'):
        permission_level = user.get_permission_level('quotation')

        if permission_level == 'system':
            # 系统级权限：可以查看所有报价单
            return True
        elif permission_level == 'company' and user.company_name:
            # 企业级权限：可以查看企业下所有报价单
            if hasattr(quotation, 'project') and quotation.project:
                from app.models.user import User
                project_owner = User.query.get(quotation.project.owner_id)
                if project_owner and project_owner.company_name == user.company_name:
                    return True
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以查看部门下所有报价单
            if hasattr(quotation, 'project') and quotation.project:
                from app.models.user import User
                project_owner = User.query.get(quotation.project.owner_id)
                if (project_owner and
                    project_owner.company_name == user.company_name and
                    project_owner.department == user.department):
                    return True
        # 四级权限系统检查失败时，继续检查归属链和特殊权限

    # 归属链检查 - 数据归属优先于四级权限系统
    from app.models.user import Affiliation
    affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
    if quotation.owner_id in affiliation_owner_ids:
        return True
        
    # 营销总监特殊处理：可以查看销售重点和渠道跟进项目的报价单
    if user_role == 'sales_director':
        # 获取关联项目
        from app.models.project import Project
        project = Project.query.get(quotation.project_id)
        if project and project.project_type in ['sales_focus', 'sales_key', 'channel_follow']:
            return True
        
    # 渠道经理特殊处理：可以查看渠道跟进项目的报价单
    if user_role == 'channel_manager':
        from app.models.project import Project
        project = Project.query.get(quotation.project_id)
        if project and project.project_type == 'channel_follow':
            return True
    
    return False
@quotation.route('/detail/<int:detail_id>/toggle_confirmation', methods=['POST'])
@login_required
def toggle_detail_confirmation(detail_id):
    """切换产品明细的确认状态 - 只有解决方案经理和admin可以操作"""
    try:
        # 检查权限
        if current_user.role not in ['solution_manager', 'admin']:
            return jsonify({
                'success': False,
                'message': '权限不足，只有解决方案经理和管理员可以操作确认状态'
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
        
        # 保存到数据库
        db.session.commit()
        
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

@quotation.route('/export_pdf/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def export_pdf(quotation_id):
    """导出报价单PDF"""
    try:
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            flash(_('权限不足，无法导出该报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))
        
        from app.services.evertac_quotation_pdf_generator import EvertacQuotationPDFGenerator
        
        # 生成PDF
        pdf_generator = EvertacQuotationPDFGenerator()
        pdf_result = pdf_generator.generate_quotation_pdf(quotation)
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
        return redirect(url_for('quotation.view_quotation', id=quotation_id))

@quotation.route('/download_pdf/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def download_pdf(quotation_id):
    """下载报价单PDF"""
    try:
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            flash(_('权限不足，无法下载该报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))
        
        from app.services.evertac_quotation_pdf_generator import EvertacQuotationPDFGenerator
        
        # 生成PDF
        pdf_generator = EvertacQuotationPDFGenerator()
        pdf_result = pdf_generator.generate_quotation_pdf(quotation)
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
        return redirect(url_for('quotation.view_quotation', id=quotation_id))

@quotation.route('/export_excel/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def export_excel(quotation_id):
    """导出报价单Excel"""
    try:
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            flash(_('权限不足，无法导出该报价单'), 'danger')
            return redirect(url_for('quotation.list_quotations'))
        
        from app.services.excel_generator import ExcelGenerator
        
        # 获取导出信息参数（如果有的话）
        export_info = None
        customer_id = request.args.get('customer_id')
        contact_id = request.args.get('contact_id')
        notes = request.args.get('notes', '')
        
        if customer_id or notes:
            # 构建导出信息
            export_info = {
                'notes': notes
            }
            
            # 获取客户信息
            if customer_id:
                try:
                    from app.models.customer import Company
                    customer = Company.query.get(int(customer_id))
                    if customer:
                        export_info['customer'] = {
                            'id': customer.id,
                            'company_name': customer.company_name,
                            'address': customer.address
                        }
                except (ValueError, TypeError):
                    pass
            
            # 获取联系人信息
            if contact_id:
                try:
                    from app.models.customer import Contact
                    contact = Contact.query.get(int(contact_id))
                    if contact:
                        export_info['contact'] = {
                            'id': contact.id,
                            'name': contact.name,
                            'phone': contact.phone,
                            'email': contact.email
                        }
                except (ValueError, TypeError):
                    pass
        
        # 生成Excel（传递export_info参数，与PDF保持一致）
        excel_generator = ExcelGenerator()
        excel_content = excel_generator.generate_quotation_excel(quotation, current_user, export_info)
        
        # 设置文件名：报价单编号 & 项目名称
        project_name = quotation.project.project_name if quotation.project else "未知项目"
        # 清理文件名中的特殊字符
        safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{quotation.quotation_number} & {safe_project_name}.xlsx"
        
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
        return redirect(url_for('quotation.view_quotation', id=quotation_id))

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
        
        # 添加调试日志
        logger.info(f"🚀 PDF导出请求: quotation_id={quotation_id}")
        logger.info(f"📦 导出信息: {export_info}")
        
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
        pdf_result = pdf_generator.generate_quotation_pdf(quotation, export_info)
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

