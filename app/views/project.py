from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from app.models.project import Project
from app.models.customer import Company, Contact
from app import db
from datetime import datetime
from flask_login import current_user, login_required
from app.decorators import permission_required
from app.utils.access_control import get_viewable_data, can_edit_data, get_accessible_data, can_change_project_owner
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
from app.utils.dictionary_helpers import project_type_label, project_stage_label, REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS, COMPANY_TYPE_LABELS
from sqlalchemy import or_, func
from app.utils.notification_helpers import trigger_event_notification
from app.services.event_dispatcher import notify_project_created, notify_project_status_updated
from app.helpers.project_helpers import is_project_editable
from app.utils.activity_tracker import check_company_activity, update_active_status
from app.models.settings import SystemSettings
from zoneinfo import ZoneInfo
from app.utils.role_mappings import get_role_display_name

csrf = CSRFProtect()

logger = logging.getLogger(__name__)

project = Blueprint('project', __name__)

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
        query = query.filter(Project.owner_id == current_user.id)
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
            for stage in excluded_stages:
                stage = stage.strip()
                if stage:
                    query = query.filter(Project.current_stage != stage)
        elif field == 'updated_this_month':
            # 筛选本月有阶段变更的项目
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
@permission_required('project', 'view')
def view_project(project_id):
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
    # 通过归属关系获得权限
    else:
        allowed_user_ids = current_user.get_viewable_user_ids() if hasattr(current_user, 'get_viewable_user_ids') else [current_user.id]
        if project.owner_id in allowed_user_ids:
            has_permission = True

    if not has_permission:
        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试查看无权限的项目: {project_id} (类型: {project.project_type}, 所有者: {project.owner_id})")
        flash('您没有权限查看此项目', 'danger')
        return redirect(url_for('project.list_projects'))
    
    # 查询相关单位对应的企业ID
    related_companies = {}
    
    # 查询直接用户
    if project.end_user:
        end_user_company = Company.query.filter_by(company_name=project.end_user).first()
        related_companies['end_user'] = end_user_company.id if end_user_company else None
    
    # 查询设计院及顾问
    if project.design_issues:
        design_company = Company.query.filter_by(company_name=project.design_issues).first()
        related_companies['design_issues'] = design_company.id if design_company else None
    
    # 查询经销商
    if project.dealer:
        dealer_company = Company.query.filter_by(company_name=project.dealer).first()
        related_companies['dealer'] = dealer_company.id if dealer_company else None
    
    # 查询总承包单位
    if project.contractor:
        contractor_company = Company.query.filter_by(company_name=project.contractor).first()
        related_companies['contractor'] = contractor_company.id if contractor_company else None
    
    # 查询系统集成商
    if project.system_integrator:
        integrator_company = Company.query.filter_by(company_name=project.system_integrator).first()
        related_companies['system_integrator'] = integrator_company.id if integrator_company else None
    
    # 解析阶段变更历史，生成stageHistory结构
    stage_history = []
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
    # 如果是中文名，反查key
    if current_stage_key not in PROJECT_STAGE_LABELS:
        reverse_lookup = {v['zh']: k for k, v in PROJECT_STAGE_LABELS.items()}
        current_stage_key = reverse_lookup.get(current_stage_key, current_stage_key)

    # 查询可选新拥有人
    all_users = []
    if can_change_project_owner(current_user, project):
        if current_user.role == 'admin':
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
        filter_by_dept = current_user.role != 'admin'
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
        if user_role == 'admin':
            can_edit_stage = True
        elif project.owner_id == current_user.id:
            can_edit_stage = True and (is_editable or user_role == 'admin')
        else:
            # 对于非拥有者，需要检查是否在可查看用户列表中，但渠道经理等角色不能编辑其他人的项目
            allowed_user_ids = current_user.get_viewable_user_ids() if hasattr(current_user, 'get_viewable_user_ids') else [current_user.id]
            if project.owner_id in allowed_user_ids:
                # 即使可以查看，也不能编辑其他人的项目（除非是管理员）
                can_edit_stage = False

    return render_template("project/detail.html", project=project, Quotation=Quotation, related_companies=related_companies, stageHistory=stage_history, project_actions=project_actions, current_stage_key=current_stage_key, all_users=all_users, has_change_owner_permission=has_change_owner_permission, user_tree_data=user_tree_data, settings=settings, can_edit_stage=can_edit_stage)

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
            if not vendor_sales_manager_id and current_user.company_name == '和源通信（上海）股份有限公司':
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
                owner_id=current_user.id,  # 设置当前用户为所有者
                vendor_sales_manager_id=vendor_sales_manager_id  # 设置厂商销售负责人
            )
            
            db.session.add(project)
            db.session.commit()
            
            # 触发项目创建通知
            try:
                notify_project_created(project, current_user)
            except Exception as notify_err:
                logger.warning(f"触发项目创建通知失败: {str(notify_err)}")
            
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
        try:
            # 必填项校验
            if not request.form.get('project_name'):
                flash('项目名称不能为空', 'danger')
                return render_template('project/edit.html', project=project, companies=get_company_data())
            if not request.form.get('report_time'):
                flash('报备日期不能为空', 'danger')
                return render_template('project/edit.html', project=project, companies=get_company_data())
            if not request.form.get('current_stage'):
                flash('当前阶段不能为空', 'danger')
                return render_template('project/edit.html', project=project, companies=get_company_data())
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
            
            # 保存旧阶段用于后续比较
            old_stage = project.current_stage
            new_stage = request.form.get('current_stage')
            
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
            if not vendor_sales_manager_id and project.owner and project.owner.company_name == '和源通信（上海）股份有限公司':
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
            
            # 新增：每次保存后自动刷新活跃度
            update_active_status(project)
            
            # 如果项目阶段发生变更，触发通知
            if old_stage != new_stage:
                try:
                    from app.services.event_dispatcher import notify_project_status_updated
                    notify_project_status_updated(project, current_user, old_stage)
                except Exception as notify_err:
                    logger.warning(f"触发项目阶段变更通知失败: {str(notify_err)}")
            
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
                company = Company.query.filter_by(company_name=company_name).first()
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
    
    # 使用集中定义的字典生成公司数据
    from app.utils.dictionary_helpers import COMPANY_TYPE_LABELS
    company_query = get_viewable_data(Company, current_user)
    companies = {
        key: company_query.filter_by(company_type=key).all()
        for key in COMPANY_TYPE_LABELS.keys()
    }
    
    return render_template(
        'project/edit.html',
        project=project,
        companies=companies,
        PRODUCT_SITUATION_OPTIONS=PRODUCT_SITUATION_OPTIONS,
        REPORT_SOURCE_OPTIONS=REPORT_SOURCE_OPTIONS,
        PROJECT_TYPE_OPTIONS=PROJECT_TYPE_OPTIONS
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
        # 先删除项目关联的所有报价单
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project_id).all()
        if quotations:
            for quotation in quotations:
                db.session.delete(quotation)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotations)} 个报价单")
        
        # 先删除项目关联的所有阶段历史记录
        from app.models.projectpm_stage_history import ProjectStageHistory
        stage_histories = ProjectStageHistory.query.filter_by(project_id=project_id).all()
        if stage_histories:
            for history in stage_histories:
                db.session.delete(history)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(stage_histories)} 条阶段历史记录")
        
        # 再删除项目
        db.session.delete(project)
        db.session.commit()
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
    
    # 检查权限 - 只有项目拥有者或管理员可以申请
    if current_user.id != project.owner_id and current_user.role != 'admin':
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
                
                # 再删除项目
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
        if not is_editable and current_user.role != 'admin':
            return jsonify({'success': False, 'message': f'项目已被锁定，无法推进阶段: {lock_reason}'}), 403
            
        # 检查权限
        allowed = False
        if current_user.role == 'admin':
            allowed = True
        elif project.owner_id == current_user.id:
            allowed = True
        else:
            allowed_user_ids = current_user.get_viewable_user_ids() if hasattr(current_user, 'get_viewable_user_ids') else [current_user.id]
            if project.owner_id in allowed_user_ids:
                allowed = True
        # 签约阶段加固：非管理员禁止任何阶段变更
        if project.current_stage == '签约' and current_user.role != 'admin':
            return jsonify({'success': False, 'message': '签约阶段仅管理员可变更项目阶段'}), 403
        if not allowed:
            return jsonify({'success': False, 'message': '您没有权限修改此项目'}), 403
            
        # 更新项目阶段
        old_stage = project.current_stage
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

            # 提交所有更改
            db.session.commit()
            # 新增：每次阶段推进后自动刷新活跃度
            update_active_status(project)
            current_app.logger.info(f"项目ID={project.id}的阶段从{old_stage}更新为{new_stage}，历史记录已添加")
            
            # 验证更新是否生效
            db.session.refresh(project)
            if project.current_stage != new_stage:
                current_app.logger.error(f"项目阶段推进后数据库未更新: 项目ID={project.id}, 期望={new_stage}, 实际={project.current_stage}")
                return jsonify({'success': False, 'message': '数据库更新失败，请联系管理员'}), 500
            
            # 触发阶段变更通知
            try:
                notify_project_status_updated(project, current_user, old_stage)
            except Exception as notify_err:
                current_app.logger.warning(f"触发项目阶段变更通知失败: {str(notify_err)}")
            
            return jsonify({
                'success': True, 
                'message': '项目阶段已更新',
                'data': {
                    'project_id': project.id,
                    'current_stage': project.current_stage,
                    'old_stage': old_stage
                }
            }), 200
            
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
        company = Company.query.filter_by(company_name=project.end_user).first()
        if company:
            related_companies.append(company)
            related_companies_dict[company.id] = company
    
    if project.design_issues:
        company = Company.query.filter_by(company_name=project.design_issues).first()
        if company and company.id not in related_companies_dict:
            related_companies.append(company)
            related_companies_dict[company.id] = company
    
    if project.contractor:
        company = Company.query.filter_by(company_name=project.contractor).first()
        if company and company.id not in related_companies_dict:
            related_companies.append(company)
            related_companies_dict[company.id] = company
            
    if project.system_integrator:
        company = Company.query.filter_by(company_name=project.system_integrator).first()
        if company and company.id not in related_companies_dict:
            related_companies.append(company)
            related_companies_dict[company.id] = company
    
    if project.dealer:
        company = Company.query.filter_by(company_name=project.dealer).first()
        if company and company.id not in related_companies_dict:
            related_companies.append(company)
            related_companies_dict[company.id] = company
    
    # 获取默认选择的企业ID
    default_company_id = request.args.get('company_id')
    selected_company = None
    company_contacts = []
    
    if default_company_id and default_company_id.isdigit():
        selected_company = Company.query.get(int(default_company_id))
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
            update_active_status(project)
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
        company = Company.query.get_or_404(company_id)
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
    is_vendor_company = new_owner.company_name == '和源通信（上海）股份有限公司'
    
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
        
        if vendor_sales_manager.company_name != '和源通信（上海）股份有限公司':
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
            # 获取厂商用户（和源通信公司）
            users = User.query.filter_by(company_name='和源通信（上海）股份有限公司').all()
        elif user_type == 'dealer':
            # 获取代理商用户（非和源通信公司）
            users = User.query.filter(User.company_name != '和源通信（上海）股份有限公司').all()
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
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500 

@project.route('/api/project/<int:project_id>/latest-quotation', methods=['GET'])
@login_required
@permission_required('project', 'view')
def get_project_latest_quotation_api(project_id):
    """获取项目最新报价单API"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 检查查看权限
        if not can_view_project(current_user, project):
            return jsonify({
                'success': False,
                'message': '您没有权限访问该项目'
            }), 403
        
        # 获取项目的最新报价单
        from app.models.quotation import Quotation
        latest_quotation = project.quotations.order_by(Quotation.created_at.desc()).first()
        
        if latest_quotation:
            return jsonify({
                'success': True,
                'quotation_id': latest_quotation.id,
                'quotation_number': latest_quotation.quotation_number,
                'amount': latest_quotation.amount,
                'created_at': latest_quotation.created_at.isoformat() if latest_quotation.created_at else None
            })
        else:
            return jsonify({
                'success': False,
                'message': '该项目暂无报价单'
            })
        
    except Exception as e:
        logger.error(f"获取项目最新报价单API失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '获取项目报价单信息失败'
        }), 500 
