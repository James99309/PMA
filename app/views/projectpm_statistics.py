from flask import Blueprint, jsonify, request, render_template
from app.models.projectpm_statistics import ProjectStatistics
from app.decorators import permission_required
from flask_login import login_required, current_user
import logging

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
    """获取可用于统计的账户列表（只返回有真实项目且为owner的账户，彻底排除伪数据账户）"""
    from sqlalchemy import distinct, text
    from app.models.projectpm_stage_history import ProjectStageHistory
    from app.models.project import Project
    from app import db
    from app.models.user import User
    from app.utils.access_control import get_viewable_data
    
    # 使用单独的会话以避免事务干扰
    try:
        # 当前用户有权限的项目，且有授权编码
        viewable_projects_query = get_viewable_data(Project, current_user).filter(
            Project.authorization_code.isnot(None),
            Project.authorization_code != ''
        )
        
        # 使用列表推导式前先确保查询成功
        try:
            viewable_projects = viewable_projects_query.all()
            if not viewable_projects:
                return jsonify({'success': True, 'data': []})
        except Exception as e:
            logger.error(f"获取可查看项目失败: {str(e)}", exc_info=True)
            # 回滚会话以清除失败的事务
            db.session.rollback()
            return jsonify({'success': True, 'data': []})
        
        # 只统计这些项目的owner
        try:
            project_ids = [p.id for p in viewable_projects]
            owner_ids = set([p.owner_id for p in viewable_projects if p.owner_id])
            
            if not project_ids or not owner_ids:
                return jsonify({'success': True, 'data': []})
        except Exception as e:
            logger.error(f"处理项目所有者数据失败: {str(e)}", exc_info=True)
            db.session.rollback()
            return jsonify({'success': True, 'data': []})

        # 这些项目的历史记录中有数据的账户ID - 使用更安全的查询方式
        try:
            # 使用较简单的查询以降低错误风险
            distinct_accounts_query = db.session.query(
                distinct(ProjectStageHistory.account_id)
            ).filter(
                ProjectStageHistory.account_id.isnot(None)
            )
            
            # 分块处理大型ID列表，避免查询过大
            if project_ids:
                if len(project_ids) > 500:
                    # 分批处理大型ID列表
                    chunks = [project_ids[i:i+500] for i in range(0, len(project_ids), 500)]
                    account_ids_with_data = set()
                    for chunk in chunks:
                        chunk_result = distinct_accounts_query.filter(
                            ProjectStageHistory.project_id.in_(chunk)
                        ).all()
                        account_ids_with_data.update([account[0] for account in chunk_result])
                else:
                    distinct_accounts = distinct_accounts_query.filter(
                        ProjectStageHistory.project_id.in_(project_ids)
                    ).all()
                    account_ids_with_data = set([account[0] for account in distinct_accounts])
            else:
                account_ids_with_data = set()
                
            # 交集：既是owner又有历史记录
            valid_account_ids = owner_ids & account_ids_with_data
            
            if not valid_account_ids:
                return jsonify({'success': True, 'data': []})
        except Exception as e:
            logger.error(f"获取历史记录账户数据失败: {str(e)}", exc_info=True)
            db.session.rollback()
            return jsonify({'success': True, 'data': []})

        # 查询账户信息
        try:
            accounts = []
            # 使用列表查询而不是循环单个查询
            if valid_account_ids:
                users = User.query.filter(User.id.in_(list(valid_account_ids))).all()
                for user in users:
                    accounts.append({
                        'id': user.id,
                        'name': user.name or user.username
                    })
                    
            return jsonify({
                'success': True,
                'data': accounts
            })
        except Exception as e:
            logger.error(f"查询用户信息失败: {str(e)}", exc_info=True)
            db.session.rollback()
            return jsonify({'success': True, 'data': []})
            
    except Exception as e:
        logger.error(f"获取可用账户列表失败: {str(e)}", exc_info=True)
        # 确保任何错误都会导致会话回滚
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'获取可用账户列表失败: {str(e)}'
        }), 500 