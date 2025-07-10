from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort, session, after_this_request
from datetime import datetime, date, timedelta
from flask_login import login_required, current_user
from app import db, csrf
from app.models.project import Project
from app.models.customer import Company, Contact
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
from app.models.relation import ProjectMember
from app.permissions import check_permission, Permissions
from werkzeug.utils import secure_filename
import os
from flask_wtf.csrf import CSRFProtect
from app.models.action import Action, ActionReply
from app.models.projectpm_stage_history import ProjectStageHistory  # 导入阶段历史记录模型
from app.utils.dictionary_helpers import project_type_label, project_stage_label, REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS, COMPANY_TYPE_LABELS, INDUSTRY_OPTIONS
from sqlalchemy import or_, func
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
    """API端点 - 为项目获取企业列表"""
    try:
        from app.utils.access_control import get_viewable_data, can_view_company
        
        # 获取用户可查看的企业
        query = get_viewable_data(Company, current_user)
        query = query.filter(Company.is_deleted == False)
        
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
        
        companies = query.order_by(Company.company_name).all()
        
        # 格式化返回数据，区分当前用户和其他用户的公司
        result = []
        current_user_companies = []
        other_companies = []
        
        for company in companies:
            company_data = {
                'id': company.id,
                'name': company.company_name,
                'type': company.company_type,
                'owner_name': company.owner.real_name if company.owner else '未指定',
                'owner_id': company.owner_id,
                'is_readable': can_view_company(current_user, company),
                'is_own': company.owner_id == current_user.id
            }
            
            # 分组：当前用户的公司优先
            if company.owner_id == current_user.id:
                current_user_companies.append(company_data)
            else:
                other_companies.append(company_data)
        
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
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'updated_at')
    order = request.args.get('order', 'desc')
    my_projects = request.args.get('my_projects', '0')
    # 获取account_id参数用于账户过滤
    account_id = request.args.get('account_id')
    # 检查是否需要保持面板打开
    keep_panel = request.args.get('keep_panel', 'false') == 'true'
    
    # 使用数据访问控制
    query = get_viewable_data(Project, current_user)
    
    # 如果启用了"只看自己"筛选
    if my_projects == '1':
        # 过滤包括拥有人是自己的和厂商负责人是自己的项目
        query = query.filter(
            db.or_(
                Project.owner_id == current_user.id,
                Project.vendor_sales_manager_id == current_user.id
            )
        )
    # 如果指定了账户ID，按owner_id过滤项目
    elif account_id and account_id.isdigit():
        query = query.filter(Project.owner_id == int(account_id))
    
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
        
        projects = query.order_by(sort_column).all()
    except Exception as e:
        logger.warning(f"排序出错：{str(e)}，使用默认排序")
        projects = query.order_by(Project.id.desc()).all()
    
    # 将筛选参数传递到模板
    filter_params = {key: value for key, value in request.args.items() if key.startswith('filter_')}
    
    # 检查是否是AJAX请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.args.get('format') == 'json':
        # 返回JSON格式的项目列表HTML片段
        html = render_template('project/list_partial.html', projects=projects, search_term=search, Quotation=Quotation, filter_params=filter_params)
        return jsonify({'success': True, 'html': html})
    
    # 传递keep_panel参数到模板
    return render_template('project/list.html', projects=projects, search_term=search, Quotation=Quotation, filter_params=filter_params, keep_panel=keep_panel)

@project.route('/view/<int:project_id>')
@permission_required_with_approval_context('project', 'view')
def view_project(project_id):
    # 导入权限检查函数，确保在所有代码路径中都可用
    from app.permissions import is_admin_or_ceo
    
    project = Project.query.get_or_404(project_id)
    
    # 检查查看权限
    has_permission = False
    
    # 统一处理角色字符串，去除空格
    user_role = current_user.role.strip() if current_user.role else ''

    # 管理员可以查看所有项目
    if user_role == 'admin':
        has_permission = True
    # 财务总监、解决方案经理、产品经理可以查看所有项目
    elif user_role in ['finance_director', 'finace_director', 'solution_manager', 'solution', 'product_manager', 'product']:
        has_permission = True
    # 渠道经理可以查看渠道跟进项目
    elif user_role == 'channel_manager' and project.project_type in ['channel_follow', '渠道跟进']:
        has_permission = True
    # 销售总监可以查看渠道跟进和销售重点项目
    elif user_role == 'sales_director' and project.project_type in ['channel_follow', 'sales_focus', '渠道跟进', '销售重点']:
        has_permission = True
    # 服务经理可以查看业务机会项目
    elif user_role in ['service', 'service_manager'] and project.project_type == '业务机会':
        has_permission = True
    # 项目拥有者可以查看自己的项目
    elif project.owner_id == current_user.id:
        has_permission = True
    # 厂商销售负责人可以查看自己负责的项目
    elif project.vendor_sales_manager_id == current_user.id:
        has_permission = True
    # 通过归属关系获得权限
    else:
        allowed_user_ids = current_user.get_viewable_user_ids() if hasattr(current_user, 'get_viewable_user_ids') else [current_user.id]
        if project.owner_id in allowed_user_ids:
            has_permission = True

    if not has_permission:
        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试查看无权限的项目: {project_id} (类型: {project.project_type}, 所有者: {project.owner_id})")
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
    project_actions = Action.query.filter_by(project_id=project_id).order_by(Action.date.desc(), Action.created_at.desc()).all()

    # 传递阶段key给前端，确保一致性
    current_stage_key = project.current_stage
    # 如果是英文key，转换为中文名称
    if current_stage_key in PROJECT_STAGE_LABELS:
        current_stage_key = PROJECT_STAGE_LABELS[current_stage_key]['zh']
    # 如果已经是中文名，保持不变

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
            all_users = User.query.filter(User.id.in_([current_user.id, project.owner_id])).all()
        if not all_users:
            all_users = User.query.filter(User.id.in_([current_user.id, project.owner_id])).all()
    has_change_owner_permission = can_change_project_owner(current_user, project)

    # 生成用户树状数据
    from app.utils.user_helpers import generate_user_tree_data
    user_tree_data = None
    if has_change_owner_permission:
        filter_by_dept = not is_admin_or_ceo()
        user_tree_data = generate_user_tree_data(filter_by_department=filter_by_dept)

    # 获取系统设置
    settings = {
        "project_activity_threshold": SystemSettings.get('project_activity_threshold', 7)
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
                         can_start_approval=can_start_approval)

@project.route('/add', methods=['GET', 'POST'])
@permission_required('project', 'create')
def add_project():
    if request.method == 'POST':
        try:
            # 验证必填字段
            if not request.form.get('project_name'):
                flash('项目名称不能为空', 'danger')
                return render_template('project/add.html', REPORT_SOURCE_OPTIONS=REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS=PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS=PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS=PROJECT_STAGE_LABELS, **get_company_data())
            if not request.form.get('report_time'):
                flash('报备日期不能为空', 'danger')
                return render_template('project/add.html', REPORT_SOURCE_OPTIONS=REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS=PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS=PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS=PROJECT_STAGE_LABELS, **get_company_data())
            if not request.form.get('current_stage'):
                flash('当前阶段不能为空', 'danger')
                return render_template('project/add.html', REPORT_SOURCE_OPTIONS=REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS=PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS=PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS=PROJECT_STAGE_LABELS, **get_company_data())
            if not request.form.get('industry'):
                flash('项目行业不能为空', 'danger')
                return render_template('project/add.html', REPORT_SOURCE_OPTIONS=REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS=PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS=PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS=PROJECT_STAGE_LABELS, **get_company_data())
            
            # 解析日期
            report_time = None
            if request.form.get('report_time'):
                report_time = datetime.strptime(request.form['report_time'], '%Y-%m-%d').date()
                
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
                current_stage=request.form.get('current_stage'),
                dealer=request.form.get('dealer'),
                end_user=request.form.get('end_user'),
                contractor=request.form.get('contractor'),
                system_integrator=request.form.get('system_integrator'),
                stage_description=request.form.get('stage_description'),
                authorization_code=authorization_code,
                project_type=project_type,
                quotation_customer=quotation_customer,
                industry=request.form.get('industry'),  # 添加行业字段
                owner_id=current_user.id,  # 设置当前用户为所有者
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
            
            flash('项目添加成功！', 'success')
            return redirect(url_for('project.view_project', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存项目失败: {str(e)}", exc_info=True)
            flash(f'保存失败：{str(e)}', 'danger')
            return render_template('project/add.html', REPORT_SOURCE_OPTIONS=REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS=PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS=PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS=PROJECT_STAGE_LABELS, **get_company_data())
    
    return render_template(
        'project/add.html',
        REPORT_SOURCE_OPTIONS=REPORT_SOURCE_OPTIONS,
        PROJECT_TYPE_OPTIONS=PROJECT_TYPE_OPTIONS,
        PRODUCT_SITUATION_OPTIONS=PRODUCT_SITUATION_OPTIONS,
        PROJECT_STAGE_LABELS=PROJECT_STAGE_LABELS,
        **get_company_data()
    )

# 辅助函数，获取公司数据
def get_company_data():
    company_query = get_viewable_data(Company, current_user)
    return {
        key: company_query.filter_by(company_type=key).all()
        for key in COMPANY_TYPE_LABELS.keys()
    }

# 新的编辑项目后台逻辑函数
def get_edit_project_data():
    """获取编辑项目需要的数据"""
    return {
        'PRODUCT_SITUATION_OPTIONS': PRODUCT_SITUATION_OPTIONS,
        'REPORT_SOURCE_OPTIONS': REPORT_SOURCE_OPTIONS,
        'PROJECT_TYPE_OPTIONS': PROJECT_TYPE_OPTIONS,
        'INDUSTRY_OPTIONS': INDUSTRY_OPTIONS,
        **get_company_data()
    }

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
        
        try:
            # 必填项校验
            if not request.form.get('project_name'):
                flash('项目名称不能为空', 'danger')
                return render_template('project/edit.html', project=project, **get_edit_project_data())
            if not request.form.get('report_time'):
                flash('报备日期不能为空', 'danger')
                return render_template('project/edit.html', project=project, **get_edit_project_data())
            if not request.form.get('current_stage'):
                flash('当前阶段不能为空', 'danger')
                return render_template('project/edit.html', project=project, **get_edit_project_data())
            if not request.form.get('industry'):
                flash('项目行业不能为空', 'danger')
                return render_template('project/edit.html', project=project, **get_edit_project_data())
            # 解析日期
            if request.form.get('report_time'):
                project.report_time = datetime.strptime(request.form['report_time'], '%Y-%m-%d').date()
            else:
                project.report_time = None
            if request.form.get('delivery_forecast'):
                project.delivery_forecast = datetime.strptime(request.form['delivery_forecast'], '%Y-%m-%d').date()
            else:
                project.delivery_forecast = None
            # 更新项目信息
            project.project_name = request.form['project_name']
            project.report_source = request.form.get('report_source')
            project.product_situation = request.form.get('product_situation')
            project.design_issues = request.form.get('design_issues')
            project.industry = request.form.get('industry')  # 添加行业字段更新
            
            # 保存旧阶段用于后续比较
            old_stage = project.current_stage
            new_stage = request.form.get('current_stage')
            
            # 如果传入的是中文阶段名称，转换为英文key
            if new_stage not in PROJECT_STAGE_LABELS:
                # 反查中文名称对应的英文key
                reverse_lookup = {v['zh']: k for k, v in PROJECT_STAGE_LABELS.items()}
                new_stage_key = reverse_lookup.get(new_stage, new_stage)
                if new_stage_key != new_stage:
                    current_app.logger.info(f"阶段名称转换: {new_stage} -> {new_stage_key}")
                    new_stage = new_stage_key
            
            # 更新当前阶段
            project.current_stage = new_stage
            project.dealer = request.form.get('dealer')
            project.end_user = request.form.get('end_user')
            project.contractor = request.form.get('contractor')
            project.system_integrator = request.form.get('system_integrator')
            project.stage_description = request.form.get('stage_description')
            
            # 更新销售负责人字段
            vendor_sales_manager_id = request.form.get('vendor_sales_manager_id')
            
            # 如果厂商销售负责人字段为空，默认将拥有人账户作为内容
            if not vendor_sales_manager_id and project.owner and project.owner.is_vendor_user():
                vendor_sales_manager_id = project.owner_id
            
            if vendor_sales_manager_id:
                project.vendor_sales_manager_id = int(vendor_sales_manager_id) if vendor_sales_manager_id != '' else None
            
            # 更新项目类型
            new_project_type = request.form.get('project_type', 'normal')
            new_project_type = {
                '渠道跟进': 'channel_follow',
                '销售重点': 'sales_focus',
                '业务机会': 'business_opportunity',
                'normal': 'normal',
                'channel_follow': 'channel_follow',
                'sales_focus': 'sales_focus',
                'business_opportunity': 'business_opportunity'
            }.get(new_project_type, 'normal')
            if new_project_type != project.project_type:
                project.project_type = new_project_type
            db.session.commit()
            
            # 记录变更历史
            try:
                new_values = ChangeTracker.get_new_values(project, old_values.keys())
                ChangeTracker.log_update(project, old_values, new_values)
            except Exception as track_err:
                logger.warning(f"记录项目变更历史失败: {str(track_err)}")
            
            # 新增：每次保存后自动刷新活跃度
            update_active_status(project)
            
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
                    check_company_activity(company_id=company.id, days_threshold=1)
            
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
        
        # === 关联数据清理结束 ===
        
        # 8. 最后删除项目
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
        # 销售经理不能批准业务机会项目
        elif user_role == 'sales' and project.project_type != 'business_opportunity':
            can_approve = True
        # 服务经理可以批准业务机会项目
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
        project_type_for_code = project_type_label(project.project_type)
        authorization_code = Project.generate_authorization_code(project_type_for_code)
        
        if not authorization_code:
            flash('无法为此类型的项目生成授权编号', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 更新项目
        project.authorization_code = authorization_code
        project.authorization_status = None  # 清除pending状态
        project.feedback = approval_note if approval_note else None
        
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
        # 销售经理不能拒绝业务机会项目
        elif user_role == 'sales' and project.project_type != 'business_opportunity':
            can_reject = True
        # 服务经理可以拒绝业务机会项目
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
        # 签约阶段加固：非管理员禁止任何阶段变更
        if project.current_stage == '签约' and not is_admin_or_ceo():
            return jsonify({'success': False, 'message': '签约阶段仅管理员可变更项目阶段'}), 403
        if not allowed:
            return jsonify({'success': False, 'message': '您没有权限修改此项目'}), 403
            
        # **新增: 签约阶段检测逻辑（批价流程）**
        old_stage = project.current_stage
        pricing_flow_info = None
        should_block_progress = False
        
        if new_stage == 'signed' and old_stage == 'quoted':
            # 从批价阶段推进到签约阶段，检查批价流程状态
            from app.models.quotation import Quotation
            from app.models.pricing_order import PricingOrder
            
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
        # 同步更新所有关联报价单的project_stage和project_type
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project.id).all()
        for q in quotations:
            q.project_stage = new_stage
            q.project_type = project.project_type
        
        # 在一个事务中同时保存项目更新和阶段历史
        try:
            # 创建阶段历史记录但不提交
            ProjectStageHistory.add_history_record(
                project_id=project.id,
                from_stage=old_stage,
                to_stage=new_stage,
                change_date=datetime.now(),
                remarks=f"API推进: {current_user.username}",
                commit=False  # 不在方法内部提交，与主事务一同提交
            )

            # 更新项目活跃度（在提交前）
            update_active_status(project, commit=False)
            
            # 提交所有更改
            db.session.commit()
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
            db.session.rollback()
            current_app.logger.error(f"提交阶段更新到数据库失败: {str(db_err)}")
            return jsonify({'success': False, 'message': f'数据库错误: {str(db_err)}'}), 500
        
    except Exception as e:
        current_app.logger.error(f"更新项目阶段出错: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

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
    
    # 获取默认选择的企业ID
    default_company_id = request.args.get('company_id')
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
                owner_id=current_user.id
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
                           company_contacts=company_contacts)

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
    
    # 如果新拥有人不是厂商企业账户，需要设置厂商销售负责人
    vendor_sales_manager_id = None
    if not is_vendor_company:
        vendor_sales_manager_id = request.form.get('vendor_sales_manager_id', type=int)
        if not vendor_sales_manager_id:
            flash('当项目拥有人不是厂商企业账户时，必须指定厂商销售负责人', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 验证厂商销售负责人是否存在且是厂商企业账户
        vendor_sales_manager = User.query.get(vendor_sales_manager_id)
        if not vendor_sales_manager:
            flash('厂商销售负责人不存在', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        if not vendor_sales_manager.is_vendor_user():
            flash('厂商销售负责人必须是厂商企业账户', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))
    else:
        # 如果新拥有人是厂商企业账户，自动设置为厂商销售负责人
        vendor_sales_manager_id = new_owner_id
    
    # 更新项目拥有人和厂商销售负责人
    project.owner_id = new_owner_id
    project.vendor_sales_manager_id = vendor_sales_manager_id
    
    # 同步更新该项目下所有报价单的owner_id为新拥有人
    from app.models.quotation import Quotation
    quotations = Quotation.query.filter_by(project_id=project.id).all()
    for quotation in quotations:
        quotation.owner_id = new_owner_id
    
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
