from flask import Blueprint, jsonify, request, render_template
from app.models.projectpm_statistics import ProjectStatistics
from app.decorators import permission_required
from flask_login import login_required, current_user
from app.permissions import has_permission
import logging
from sqlalchemy import distinct
from sqlalchemy import func
from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS

logger = logging.getLogger(__name__)

projectpm_statistics = Blueprint('projectpm_statistics', __name__)

@projectpm_statistics.route('/api/project_statistics', methods=['GET'])
@login_required
@permission_required('project', 'view')
def get_project_statistics_api():
    """获取项目统计数据 API"""
    try:
        period = request.args.get('period', 'all')
        if period not in ['week', 'month', 'all']:
            period = 'all'
            
        # 获取账户ID参数
        account_id = request.args.get('account_id')
        if account_id:
            try:
                account_id = int(account_id)
            except ValueError:
                account_id = None
            
        # 获取统计数据
        statistics = ProjectStatistics.get_project_statistics(current_user, period, account_id)
        
        # 格式化金额为两位小数
        for key in statistics:
            if 'amount' in key and isinstance(statistics[key], (int, float)):
                statistics[key] = round(statistics[key], 2)
                
        # 对于阶段金额字典单独处理
        if 'stage_amounts' in statistics:
            for stage in statistics['stage_amounts']:
                statistics['stage_amounts'][stage] = round(statistics['stage_amounts'][stage], 2)
        
        return jsonify({
            'success': True,
            'data': statistics,
            'period': period,
            'account_id': account_id
        })
    except Exception as e:
        logger.error(f"获取项目统计数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取项目统计数据失败: {str(e)}'
        }), 500

@projectpm_statistics.route('/api/project_stage_trends', methods=['GET'])
@login_required
@permission_required('project', 'view')
def get_project_stage_trends_api():
    """获取项目阶段趋势数据 API"""
    try:
        period = request.args.get('period', 'week')
        if period not in ['week', 'month']:
            period = 'week'
            
        stage = request.args.get('stage')
        
        # 获取账户ID参数
        account_id = request.args.get('account_id')
        if account_id:
            try:
                account_id = int(account_id)
            except ValueError:
                account_id = None
        
        # 获取趋势数据
        if stage:
            # 获取单个阶段的趋势
            trends_data = ProjectStatistics.get_stage_trend_data(stage, period, current_user, account_id)
        else:
            # 获取所有阶段趋势
            trends_data = ProjectStatistics.get_all_stage_trends(period, current_user, account_id)
        
        return jsonify({
            'success': True,
            'data': trends_data,
            'period': period,
            'account_id': account_id
        })
    except Exception as e:
        logger.error(f"获取项目阶段趋势数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取项目阶段趋势数据失败: {str(e)}'
        }), 500

# 添加API获取可用账户列表
@projectpm_statistics.route('/api/available_accounts', methods=['GET'])
@login_required
@permission_required('project', 'view')
def get_available_accounts_api():
    """获取可用于统计的账户列表（基于严格的权限控制）"""
    try:
        from sqlalchemy import distinct
        from app.models.projectpm_stage_history import ProjectStageHistory
        from app.models.project import Project
        from app import db
        from app.models.user import User, Affiliation
        from app.utils.access_control import get_viewable_data

        # 管理员可以看到所有有项目的账户
        if has_permission('project', 'admin'):
            owner_ids = set([p.owner_id for p in Project.query.filter(
                Project.owner_id.isnot(None),
                Project.authorization_code.isnot(None),
                func.length(Project.authorization_code) > 0
            ).all()])
        else:
            # 基于四级权限系统的账户筛选逻辑
            permission_level = current_user.get_permission_level('project')
            
            if permission_level == 'system':
                # 系统级权限：可以看到所有有项目的账户
                owner_ids = set([p.owner_id for p in Project.query.filter(
                    Project.owner_id.isnot(None),
                    Project.authorization_code.isnot(None),
                    func.length(Project.authorization_code) > 0
                ).all()])
            elif permission_level == 'company' and current_user.company_name:
                # 企业级权限：可以看到企业内所有用户的账户
                company_users = User.query.filter_by(company_name=current_user.company_name).all()
                viewable_user_ids = [u.id for u in company_users]
                
                # 只返回这些用户中有项目数据的账户
                owner_ids = set()
                for user_id in viewable_user_ids:
                    if Project.query.filter(
                        Project.owner_id == user_id,
                        Project.authorization_code.isnot(None),
                        func.length(Project.authorization_code) > 0
                    ).first():
                        owner_ids.add(user_id)
            elif permission_level == 'department' and current_user.department and current_user.company_name:
                # 部门级权限：可以看到部门内所有用户的账户
                dept_users = User.query.filter(
                    User.department == current_user.department,
                    User.company_name == current_user.company_name
                ).all()
                viewable_user_ids = [u.id for u in dept_users]
                
                # 只返回这些用户中有项目数据的账户
                owner_ids = set()
                for user_id in viewable_user_ids:
                    if Project.query.filter(
                        Project.owner_id == user_id,
                        Project.authorization_code.isnot(None),
                        func.length(Project.authorization_code) > 0
                    ).first():
                        owner_ids.add(user_id)
            else:
                # 个人级权限：使用原有逻辑
                viewable_user_ids = [current_user.id]  # 首先包含自己
                
                # 检查用户角色和权限
                user_role = current_user.role.strip() if current_user.role else ''
                
                # 部门负责人可以看到本部门所有用户的账户
                if getattr(current_user, 'is_department_manager', False) and current_user.department:
                    dept_users = User.query.filter_by(department=current_user.department).all()
                    viewable_user_ids.extend([u.id for u in dept_users])
                
                # 商务助理可以看到同部门用户的账户
                elif user_role == 'business_admin':
                    if current_user.department and current_user.company_name:
                        dept_users = User.query.filter(
                            User.department == current_user.department,
                            User.company_name == current_user.company_name
                        ).all()
                        viewable_user_ids.extend([u.id for u in dept_users])
                
                # 添加通过归属关系可以查看的用户
                affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
                for affiliation in affiliations:
                    viewable_user_ids.append(affiliation.owner_id)
                
                # 去重
                viewable_user_ids = list(set(viewable_user_ids))
                
                # 只返回这些用户中有项目数据的账户
                owner_ids = set()
                for user_id in viewable_user_ids:
                    if Project.query.filter(
                        Project.owner_id == user_id,
                        Project.authorization_code.isnot(None),
                        func.length(Project.authorization_code) > 0
                    ).first():
                        owner_ids.add(user_id)

        # 查询账户信息
        accounts = []
        for acc_id in owner_ids:
            user = User.query.get(acc_id)
            if user:
                accounts.append({
                    'id': acc_id,
                    'name': user.name or user.username
                })

        return jsonify({
            'success': True,
            'data': accounts
        })
    except Exception as e:
        logger.error(f"获取可用账户列表失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取可用账户列表失败: {str(e)}'
        }), 500

# 添加新的API端点，提供阶段标签映射
@projectpm_statistics.route('/api/stage_labels', methods=['GET'])
def get_stage_labels_api():
    """返回项目阶段标签映射，供前端使用"""
    try:
        return jsonify({
            'success': True,
            'labels': PROJECT_STAGE_LABELS
        })
    except Exception as e:
        logger.error(f"获取阶段标签映射失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取阶段标签映射失败: {str(e)}'
        }), 500 