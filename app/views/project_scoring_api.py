# -*- coding: utf-8 -*-
"""
项目评分API - 新的统一评分系统
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.project_scoring import ProjectScoringEngine, ProjectTotalScore, ProjectScoringRecord
from app.models.project import Project
from app.decorators import permission_required
from app.views.project import can_view_project
import logging

logger = logging.getLogger(__name__)

project_scoring_api = Blueprint('project_scoring_api', __name__)

@project_scoring_api.route('/api/project/<int:project_id>/scoring/status', methods=['GET'], endpoint='scoring_status')
@login_required
def get_project_scoring_status(project_id):
    """获取项目评分状态 - 对所有登录用户开放"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 移除权限检查，让所有登录用户都可以查看评分状态
        # 注释掉原有的权限检查
        # if not can_view_project(current_user, project):
        #     return jsonify({'success': False, 'message': '无权限查看此项目'}), 403
        
        # 获取项目总评分
        total_score = ProjectTotalScore.query.filter_by(project_id=project_id).first()
        
        if not total_score:
            # 如果没有评分记录，先计算一次
            result = ProjectScoringEngine.calculate_project_score(project_id)
            if result:
                total_score = ProjectTotalScore.query.filter_by(project_id=project_id).first()
        
        # 检查用户是否已给予手动奖励
        user_manual_awards = ProjectScoringRecord.query.filter_by(
            project_id=project_id,
            category='manual',
            awarded_by=current_user.id,
            auto_calculated=False
        ).all()
        
        user_has_awarded = len(user_manual_awards) > 0
        
        return jsonify({
            'success': True,
            'data': {
                'project_id': project.id,
                'total_score': float(total_score.total_score) if total_score else 0.0,
                'star_rating': total_score.star_rating if total_score else 0,
                'information_score': float(total_score.information_score) if total_score else 0.0,
                'quotation_score': float(total_score.quotation_score) if total_score else 0.0,
                'stage_score': float(total_score.stage_score) if total_score else 0.0,
                'manual_score': float(total_score.manual_score) if total_score else 0.0,
                'user_has_awarded': user_has_awarded,
                'last_calculated': total_score.last_calculated.isoformat() if total_score else None
            }
        })
        
    except Exception as e:
        logger.error(f"获取项目评分状态失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取评分状态失败'}), 500

@project_scoring_api.route('/api/project/<int:project_id>/scoring/manual-award', methods=['POST'], endpoint='manual_award')
@login_required
def toggle_manual_award(project_id):
    """切换手动奖励（添加或移除）"""
    try:
        # 检查项目评分权限
        if current_user.role != 'admin' and not current_user.has_permission('project_rating', 'create'):
            return jsonify({'success': False, 'message': '您没有权限设置项目评分'}), 403
        
        project = Project.query.get_or_404(project_id)
        
        # 检查项目查看权限
        if not can_view_project(current_user, project):
            return jsonify({'success': False, 'message': '无权限访问此项目'}), 403
        
        # 获取操作类型
        data = request.get_json()
        action = data.get('action', 'toggle')  # 'add', 'remove', 'toggle'
        award_type = data.get('award_type', 'supervisor_award')
        notes = data.get('notes', '')
        
        # 检查用户是否已给予奖励（更精确的查询条件）
        existing_award = ProjectScoringRecord.query.filter_by(
            project_id=project_id,
            category='manual',
            field_name=award_type,
            awarded_by=current_user.id,
            auto_calculated=False  # 确保是手动奖励
        ).first()
        
        logger.info(f"检查奖励记录: project_id={project_id}, user_id={current_user.id}, existing={existing_award is not None}")
        
        if action == 'toggle':
            action = 'remove' if existing_award else 'add'
        
        if action == 'add':
            if existing_award:
                return jsonify({'success': False, 'message': '您已经给予过此类奖励'}), 400
            
            success, message = ProjectScoringEngine.add_manual_award(
                project_id, current_user.id, award_type, notes
            )
        elif action == 'remove':
            if not existing_award:
                return jsonify({'success': False, 'message': '您尚未给予此类奖励'}), 400
            
            success, message = ProjectScoringEngine.remove_manual_award(
                project_id, current_user.id, award_type
            )
        else:
            return jsonify({'success': False, 'message': '无效的操作类型'}), 400
        
        if not success:
            return jsonify({'success': False, 'message': message}), 400
        
        # 获取更新后的评分信息
        total_score = ProjectTotalScore.query.filter_by(project_id=project_id).first()
        
        # 重新检查用户是否有手动奖励
        final_award_check = ProjectScoringRecord.query.filter_by(
            project_id=project_id,
            category='manual',
            field_name=award_type,
            awarded_by=current_user.id,
            auto_calculated=False
        ).first()
        
        logger.info(f"用户 {current_user.username} {action} 项目 {project.project_name} 的手动奖励")
        
        return jsonify({
            'success': True,
            'data': {
                'project_id': project.id,
                'total_score': float(total_score.total_score) if total_score else 0.0,
                'star_rating': total_score.star_rating if total_score else 0,
                'user_has_awarded': final_award_check is not None
            }
        })
        
    except Exception as e:
        logger.error(f"切换手动奖励失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': '操作失败'}), 500

@project_scoring_api.route('/api/project/<int:project_id>/scoring/details', methods=['GET'], endpoint='scoring_details')
@login_required
def get_project_scoring_details(project_id):
    """获取项目评分详情 - 对所有登录用户开放"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 移除权限检查，让所有登录用户都可以查看评分详情
        # 注释掉原有的权限检查
        # if not can_view_project(current_user, project):
        #     return jsonify({'success': False, 'message': '无权限查看此项目'}), 403
        
        # 获取所有评分记录
        scoring_records = ProjectScoringRecord.query.filter_by(project_id=project_id).all()
        
        # 按类别分组
        grouped_records = {
            'information': [],
            'quotation': [],
            'stage': [],
            'manual': []
        }
        
        for record in scoring_records:
            if record.category in grouped_records:
                record_data = {
                    'field_name': record.field_name,
                    'score_value': float(record.score_value),
                    'auto_calculated': record.auto_calculated,
                    'notes': record.notes,
                    'created_at': record.created_at.isoformat(),
                    'awarded_by': None
                }
                
                # 显示奖励者信息，让所有用户都能看到是谁给予的奖励
                if record.awarded_by_user:
                    record_data['awarded_by'] = {
                        'id': record.awarded_by_user.id,
                        'name': record.awarded_by_user.real_name or record.awarded_by_user.username
                    }
                
                grouped_records[record.category].append(record_data)
        
        # 获取总评分
        total_score = ProjectTotalScore.query.filter_by(project_id=project_id).first()
        
        return jsonify({
            'success': True,
            'data': {
                'project_id': project.id,
                'project_name': project.project_name,
                'total_score': float(total_score.total_score) if total_score else 0.0,
                'star_rating': total_score.star_rating if total_score else 0,
                'score_breakdown': {
                    'information_score': float(total_score.information_score) if total_score else 0.0,
                    'quotation_score': float(total_score.quotation_score) if total_score else 0.0,
                    'stage_score': float(total_score.stage_score) if total_score else 0.0,
                    'manual_score': float(total_score.manual_score) if total_score else 0.0
                },
                'scoring_records': grouped_records,
                'last_calculated': total_score.last_calculated.isoformat() if total_score else None
            }
        })
        
    except Exception as e:
        logger.error(f"获取项目评分详情失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取评分详情失败'}), 500

@project_scoring_api.route('/api/project/<int:project_id>/scoring/recalculate', methods=['POST'], endpoint='scoring_recalculate')
@login_required
@permission_required('project', 'edit')
def recalculate_project_score(project_id):
    """重新计算项目评分"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 检查权限
        if not can_view_project(current_user, project):
            return jsonify({'success': False, 'message': '无权限访问此项目'}), 403
        
        # 重新计算评分
        result = ProjectScoringEngine.calculate_project_score(project_id)
        
        if result:
            logger.info(f"用户 {current_user.username} 重新计算了项目 {project.project_name} 的评分")
            
            return jsonify({
                'success': True,
                'message': '评分重新计算成功',
                'data': result
            })
        else:
            return jsonify({'success': False, 'message': '评分计算失败'}), 500
        
    except Exception as e:
        logger.error(f"重新计算项目评分失败: {str(e)}")
        return jsonify({'success': False, 'message': '重新计算失败'}), 500
