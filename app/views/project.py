from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from app.models.project import Project
from app.models.customer import Company
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
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'desc')
    
    # 使用数据访问控制
    query = get_viewable_data(Project, current_user)
    
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
    
    return render_template('project/list.html', projects=projects, search_term=search, Quotation=Quotation, filter_params=filter_params)

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
    
    return render_template('project/detail.html', project=project, Quotation=Quotation, related_companies=related_companies)

@project.route('/add', methods=['GET', 'POST'])
@permission_required('project', 'create')
def add_project():
    if request.method == 'POST':
        try:
            # 解析日期
            report_time = None
            if request.form.get('report_time'):
                report_time = datetime.strptime(request.form['report_time'], '%Y-%m-%d').date()
                
            delivery_forecast = None
            if request.form.get('delivery_forecast'):
                delivery_forecast = datetime.strptime(request.form['delivery_forecast'], '%Y-%m-%d').date()
            
            # 获取项目类型
            project_type = request.form.get('project_type', 'normal')
            
            # 项目类型中英文转换
            type_mapping = {
                '渠道跟进': 'channel_follow',
                '销售重点': 'sales_focus',
                'normal': 'normal'
            }
            
            # 如果是中文类型，转换为英文代码
            if project_type in type_mapping:
                project_type = type_mapping[project_type]
            
            # 生成授权编号
            authorization_code = None
            if project_type in ['channel_follow', 'sales_focus']:
                # 映射项目类型到旧的格式以兼容现有函数
                old_type_mapping = {
                    'channel_follow': '渠道跟进',
                    'sales_focus': '销售重点'
                }
                old_type = old_type_mapping.get(project_type, '')
                authorization_code = Project.generate_authorization_code(old_type)
            
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
                owner_id=current_user.id  # 设置当前用户为所有者
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('项目添加成功！', 'success')
            return redirect(url_for('project.view_project', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            flash(f'保存失败：{str(e)}', 'danger')
    
    # 获取公司列表
    companies = get_viewable_data(Company, current_user).all()
    
    return render_template('project/add.html', companies=companies)

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
                
                # 如果项目类型变更，可能需要更新授权编号
                if new_project_type in ['channel_follow', 'sales_focus']:
                    # 映射项目类型到旧的格式以兼容现有函数
                    old_type_mapping = {
                        'channel_follow': '渠道跟进',
                        'sales_focus': '销售重点'
                    }
                    old_type = old_type_mapping.get(new_project_type, '')
                    project.authorization_code = Project.generate_authorization_code(old_type)
                else:
                    project.authorization_code = None
            
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
    current_id = data.get('current_id', None)
    
    if not project_name:
        return jsonify({'similar_projects': []})
    
    # 使用SQLAlchemy查询而非MongoDB
    query = Project.query.filter(Project.authorization_status != 'rejected')
    
    if current_id:
        query = query.filter(Project.id != current_id)
    
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
        
        # 生成授权编号 - 使用标准化的授权编号生成方法
        authorization_code = Project.generate_authorization_code(project.project_type)
        
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
            'message': f'操作失败: {str(e)}'
        }) 