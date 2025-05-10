from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from app.models.project import Project
from app.models.customer import Company, Contact
from app import db
from datetime import datetime
from flask_login import current_user, login_required
from app.decorators import permission_required
from app.utils.access_control import get_viewable_data, can_edit_data, get_accessible_data
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
from app.models.action import Action

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
        if hasattr(Project, field):
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

    # 管理员可以查看所有项目
    if current_user.role == 'admin':
        has_permission = True
    # 渠道经理可以查看渠道跟进项目
    elif current_user.role == 'channel_manager' and project.project_type in ['channel_follow', '渠道跟进']:
        has_permission = True
    # 营销总监可以查看渠道跟进和销售重点项目
    elif current_user.role == 'marketing_director' and project.project_type in ['channel_follow', 'sales_focus', '渠道跟进', '销售重点']:
        has_permission = True
    # 服务经理可以查看业务机会项目
    elif current_user.role in ['service', 'service_manager'] and project.project_type == '业务机会':
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

    return render_template('project/detail.html', project=project, Quotation=Quotation, related_companies=related_companies, stageHistory=stage_history, project_actions=project_actions)

@project.route('/add', methods=['GET', 'POST'])
@permission_required('project', 'create')
def add_project():
    if request.method == 'POST':
        try:
            # 验证必填字段
            if not request.form.get('project_name'):
                flash('项目名称不能为空', 'danger')
                return render_template('project/add.html', **get_company_data())
                
            if not request.form.get('report_time'):
                flash('报备日期不能为空', 'danger')
                return render_template('project/add.html', **get_company_data())
                
            if not request.form.get('current_stage'):
                flash('当前阶段不能为空', 'danger')
                return render_template('project/add.html', **get_company_data())
            
            # 解析日期
            report_time = None
            if request.form.get('report_time'):
                report_time = datetime.strptime(request.form['report_time'], '%Y-%m-%d').date()
                
            delivery_forecast = None
            if request.form.get('delivery_forecast'):
                delivery_forecast = datetime.strptime(request.form['delivery_forecast'], '%Y-%m-%d').date()
            
            # 获取项目类型
            project_type = request.form.get('project_type', 'normal')
            logger.info(f"原始项目类型: {project_type}")
            
            # 项目类型中英文转换
            type_mapping = {
                '渠道跟进': 'channel_follow',
                '销售重点': 'sales_focus',
                '业务机会': 'business_opportunity',
                'normal': 'normal'
            }
            
            # 如果是中文类型，转换为英文代码
            if project_type in type_mapping:
                project_type = type_mapping[project_type]
                logger.info(f"转换后的项目类型: {project_type}")
            
            # 不再自动生成授权编号，授权编号必须通过申请流程获得
            authorization_code = None
            
            # 报价字段设置为无效，不处理
            quotation_customer = None
            
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
                owner_id=current_user.id  # 设置当前用户为所有者
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('项目添加成功！', 'success')
            return redirect(url_for('project.view_project', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存项目失败: {str(e)}", exc_info=True)
            flash(f'保存失败：{str(e)}', 'danger')
    
    return render_template('project/add.html', **get_company_data())

# 辅助函数，获取公司数据
def get_company_data():
    company_query = get_viewable_data(Company, current_user)
    return {
        'end_users': company_query.filter_by(company_type='用户').all(),
        'designers': company_query.filter_by(company_type='设计院及顾问').all(),
        'contractors': company_query.filter_by(company_type='总承包单位').all(),
        'integrators': company_query.filter_by(company_type='系统集成商').all(),
        'dealers': company_query.filter_by(company_type='经销商').all()
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
    
    if request.method == 'POST':
        try:
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
            project.current_stage = request.form.get('current_stage')
            project.dealer = request.form.get('dealer')
            project.end_user = request.form.get('end_user')
            project.contractor = request.form.get('contractor')
            project.system_integrator = request.form.get('system_integrator')
            project.stage_description = request.form.get('stage_description')
            
            # 更新项目类型
            new_project_type = request.form.get('project_type', 'normal')
            
            # 项目类型中英文转换
            type_mapping = {
                '渠道跟进': 'channel_follow',
                '销售重点': 'sales_focus',
                'normal': 'normal'
            }
            
            # 如果是中文类型，转换为英文代码
            if new_project_type in type_mapping:
                new_project_type = type_mapping[new_project_type]
                
            if new_project_type != project.project_type:
                project.project_type = new_project_type
                
                # 不再自动更新授权编号，即使项目类型变更
                # 授权编号必须通过申请流程获得
            
            db.session.commit()
            flash('项目更新成功！', 'success')
            return redirect(url_for('project.view_project', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'danger')
    
    # 获取公司列表 - 修改为字典格式
    company_query = get_viewable_data(Company, current_user)
    companies = {
        'users': company_query.filter_by(company_type='用户').all(),
        'designers': company_query.filter_by(company_type='设计院及顾问').all(),
        'contractors': company_query.filter_by(company_type='总承包单位').all(),
        'integrators': company_query.filter_by(company_type='系统集成商').all(),
        'dealers': company_query.filter_by(company_type='经销商').all()
    }
    
    return render_template('project/edit.html', project=project, companies=companies)

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

        # 管理员可以批准所有项目授权申请
        if current_db_user.role == 'admin':
            can_approve = True
        # 渠道经理可以批准渠道跟进项目
        elif current_db_user.role == 'channel_manager' and project.project_type == '渠道跟进':
            can_approve = True
        # 营销总监可以批准销售重点项目
        elif current_db_user.role == 'marketing_director' and project.project_type == '销售重点':
            can_approve = True
        # 销售经理不能批准业务机会项目
        elif current_db_user.role == 'sales' and project.project_type != '业务机会':
            can_approve = True
        # 服务经理可以批准业务机会项目
        elif current_db_user.role in ['service', 'service_manager'] and project.project_type == '业务机会':
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
        type_mapping = {
            'channel_follow': '渠道跟进',
            'sales_focus': '销售重点',
            'business_opportunity': '业务机会',
            '渠道跟进': '渠道跟进',
            '销售重点': '销售重点',
            '业务机会': '业务机会'
        }
        project_type_for_code = type_mapping.get(project.project_type, project.project_type)
        authorization_code = Project.generate_authorization_code(project_type_for_code)
        
        if not authorization_code:
            flash('无法为此类型的项目生成授权编号', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 更新项目
        project.authorization_code = authorization_code
        project.authorization_status = None  # 清除pending状态
        project.feedback = approval_note if approval_note else None
        
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

        # 管理员可以拒绝所有项目授权申请
        if current_db_user.role == 'admin':
            can_reject = True
        # 渠道经理可以拒绝渠道跟进项目
        elif current_db_user.role == 'channel_manager' and project.project_type == '渠道跟进':
            can_reject = True
        # 营销总监可以拒绝销售重点项目
        elif current_db_user.role == 'marketing_director' and project.project_type == '销售重点':
            can_reject = True
        # 销售经理不能拒绝业务机会项目
        elif current_db_user.role == 'sales' and project.project_type != '业务机会':
            can_reject = True
        # 服务经理可以拒绝业务机会项目
        elif current_db_user.role in ['service', 'service_manager'] and project.project_type == '业务机会':
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
            
        # 查询项目
        project = Project.query.get_or_404(project_id)
        
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
        
        # 在阶段说明中添加阶段变更记录
        change_record = f"\n[阶段变更] {old_stage} → {new_stage} (更新者: {current_user.username}, 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        if project.stage_description:
            project.stage_description += change_record
        else:
            project.stage_description = change_record
            
        # 保存更新
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '项目阶段已更新',
            'data': {
                'project_id': project.id,
                'current_stage': project.current_stage,
                'old_stage': old_stage
            }
        }), 200
        
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