# -*- coding: utf-8 -*-
"""
项目评分配置管理视图
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.project_scoring import ProjectScoringConfig, ProjectScoringEngine
from app.decorators import permission_required
import logging

logger = logging.getLogger(__name__)

scoring_config = Blueprint('scoring_config', __name__)

@scoring_config.route('/admin/scoring-config')
@login_required
@permission_required('admin', 'view')
def scoring_config_list():
    """评分配置列表页面"""
    try:
        # 按类别分组获取配置
        configs = ProjectScoringConfig.query.order_by(
            ProjectScoringConfig.category,
            ProjectScoringConfig.field_name
        ).all()
        
        # 按类别分组
        grouped_configs = {}
        category_labels = {
            'information': '信息完整性得分项',
            'quotation': '报价完整性得分项', 
            'stage': '阶段得分项',
            'manual': '手动奖励'
        }
        
        for config in configs:
            category = config.category
            if category not in grouped_configs:
                grouped_configs[category] = {
                    'label': category_labels.get(category, category),
                    'configs': []
                }
            grouped_configs[category]['configs'].append(config)
        
        return render_template('admin/scoring_config_list.html', 
                             grouped_configs=grouped_configs,
                             category_labels=category_labels)
        
    except Exception as e:
        logger.error(f"获取评分配置失败: {str(e)}")
        flash('获取评分配置失败', 'error')
        return redirect(url_for('admin.system_settings'))

@scoring_config.route('/admin/scoring-config/edit/<int:config_id>', methods=['GET', 'POST'])
@login_required
@permission_required('admin', 'edit')
def edit_scoring_config(config_id):
    """编辑评分配置"""
    config = ProjectScoringConfig.query.get_or_404(config_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            config.field_label = data.get('field_label', config.field_label)
            config.score_value = float(data.get('score_value', config.score_value))
            config.prerequisite = data.get('prerequisite', config.prerequisite)
            config.is_active = data.get('is_active', config.is_active)
            
            db.session.commit()
            
            logger.info(f"用户 {current_user.username} 更新了评分配置 {config.category}.{config.field_name}")
            
            return jsonify({
                'success': True,
                'message': '配置更新成功'
            })
            
        except Exception as e:
            logger.error(f"更新评分配置失败: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'更新失败: {str(e)}'
            }), 500
    
    return jsonify({
        'success': True,
        'data': {
            'id': config.id,
            'category': config.category,
            'field_name': config.field_name,
            'field_label': config.field_label,
            'score_value': float(config.score_value),
            'prerequisite': config.prerequisite,
            'is_active': config.is_active
        }
    })

@scoring_config.route('/admin/scoring-config/batch-update', methods=['POST'])
@login_required
@permission_required('admin', 'edit')
def batch_update_scoring_config():
    """批量更新评分配置"""
    try:
        data = request.get_json()
        configs = data.get('configs', [])
        
        for config_data in configs:
            config_id = config_data.get('id')
            config = ProjectScoringConfig.query.get(config_id)
            
            if config:
                config.score_value = float(config_data.get('score_value', config.score_value))
                config.is_active = config_data.get('is_active', config.is_active)
        
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 批量更新了 {len(configs)} 个评分配置")
        
        return jsonify({
            'success': True,
            'message': f'成功更新 {len(configs)} 个配置'
        })
        
    except Exception as e:
        logger.error(f"批量更新评分配置失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'批量更新失败: {str(e)}'
        }), 500

@scoring_config.route('/admin/scoring-config/recalculate-all', methods=['POST'])
@login_required
@permission_required('admin', 'edit')
def recalculate_all_projects():
    """重新计算所有项目评分"""
    try:
        from app.models.project import Project
        
        projects = Project.query.all()
        success_count = 0
        error_count = 0
        
        for project in projects:
            try:
                result = ProjectScoringEngine.calculate_project_score(project.id)
                if result:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"重新计算项目 {project.id} 评分失败: {str(e)}")
                error_count += 1
        
        logger.info(f"用户 {current_user.username} 重新计算了所有项目评分: 成功 {success_count}, 失败 {error_count}")
        
        return jsonify({
            'success': True,
            'message': f'重新计算完成: 成功 {success_count} 个项目, 失败 {error_count} 个项目'
        })
        
    except Exception as e:
        logger.error(f"重新计算所有项目评分失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'重新计算失败: {str(e)}'
        }), 500 