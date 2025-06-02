#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本管理视图

此模块提供版本管理相关的视图和API：
1. 版本信息展示
2. 升级日志管理
3. 功能变更记录
4. 系统指标监控
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.version_management import VersionRecord, UpgradeLog, FeatureChange, SystemMetrics
from app.utils.version_check import get_app_version, update_version_check
from app.decorators import admin_required
from datetime import datetime, timedelta
import json
import os
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
version_management_bp = Blueprint('version_management', __name__, url_prefix='/admin/version')

@version_management_bp.route('/')
@login_required
@admin_required
def index():
    """版本管理主页"""
    try:
        # 获取当前版本信息
        current_version = VersionRecord.get_current_version()
        
        # 获取最近的版本记录
        recent_versions = VersionRecord.query.order_by(VersionRecord.release_date.desc()).limit(10).all()
        
        # 获取最近的升级日志
        recent_upgrades = UpgradeLog.query.order_by(UpgradeLog.upgrade_date.desc()).limit(5).all()
        
        # 获取版本统计
        version_stats = {
            'total_versions': VersionRecord.query.count(),
            'total_upgrades': UpgradeLog.query.count(),
            'successful_upgrades': UpgradeLog.query.filter_by(status='success').count(),
            'failed_upgrades': UpgradeLog.query.filter_by(status='failed').count()
        }
        
        return render_template('admin/version_management/index.html',
                             current_version=current_version,
                             recent_versions=recent_versions,
                             recent_upgrades=recent_upgrades,
                             version_stats=version_stats)
    except Exception as e:
        logger.error(f"版本管理主页加载失败: {str(e)}")
        flash('版本管理页面加载失败', 'error')
        return redirect(url_for('admin.index'))

@version_management_bp.route('/versions')
@login_required
@admin_required
def versions():
    """版本列表页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        versions = VersionRecord.query.order_by(VersionRecord.release_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/version_management/versions.html', versions=versions)
    except Exception as e:
        logger.error(f"版本列表加载失败: {str(e)}")
        flash('版本列表加载失败', 'error')
        return redirect(url_for('version_management.index'))

@version_management_bp.route('/version/<int:version_id>')
@login_required
@admin_required
def version_detail(version_id):
    """版本详情页面"""
    try:
        version = VersionRecord.query.get_or_404(version_id)
        
        # 获取该版本的功能变更
        feature_changes = FeatureChange.query.filter_by(version_id=version_id).all()
        
        # 获取该版本的升级日志
        upgrade_logs = UpgradeLog.query.filter_by(version_id=version_id).all()
        
        # 按类型分组功能变更
        changes_by_type = {}
        for change in feature_changes:
            if change.change_type not in changes_by_type:
                changes_by_type[change.change_type] = []
            changes_by_type[change.change_type].append(change)
        
        return render_template('admin/version_management/version_detail.html',
                             version=version,
                             changes_by_type=changes_by_type,
                             upgrade_logs=upgrade_logs)
    except Exception as e:
        logger.error(f"版本详情加载失败: {str(e)}")
        flash('版本详情加载失败', 'error')
        return redirect(url_for('version_management.versions'))

@version_management_bp.route('/upgrade-logs')
@login_required
@admin_required
def upgrade_logs():
    """升级日志页面"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', '')
        per_page = 20
        
        query = UpgradeLog.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        logs = query.order_by(UpgradeLog.upgrade_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/version_management/upgrade_logs.html', 
                             logs=logs, status_filter=status_filter)
    except Exception as e:
        logger.error(f"升级日志加载失败: {str(e)}")
        flash('升级日志加载失败', 'error')
        return redirect(url_for('version_management.index'))

# API接口
@version_management_bp.route('/api/current-version')
@login_required
def api_current_version():
    """获取当前版本信息API"""
    try:
        # 获取数据库中的版本信息
        current_version = VersionRecord.get_current_version()
        
        # 获取应用配置中的版本信息
        app_version_info = get_app_version()
        
        result = {
            'database_version': current_version.to_dict() if current_version else None,
            'app_version_info': app_version_info,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"获取当前版本信息失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取版本信息失败', 'error': str(e)}), 500

@version_management_bp.route('/api/create-version', methods=['POST'])
@login_required
@admin_required
def api_create_version():
    """创建新版本记录API"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['version_number', 'version_name', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必填字段: {field}'}), 400
        
        # 检查版本号是否已存在
        existing_version = VersionRecord.query.filter_by(version_number=data['version_number']).first()
        if existing_version:
            return jsonify({'success': False, 'message': '版本号已存在'}), 400
        
        # 创建新版本记录
        new_version = VersionRecord(
            version_number=data['version_number'],
            version_name=data['version_name'],
            description=data['description'],
            environment=data.get('environment', 'production'),
            total_features=data.get('total_features', 0),
            total_fixes=data.get('total_fixes', 0),
            total_improvements=data.get('total_improvements', 0),
            git_commit=data.get('git_commit'),
            build_number=data.get('build_number')
        )
        
        db.session.add(new_version)
        
        # 如果设置为当前版本，更新其他版本状态
        if data.get('is_current', False):
            VersionRecord.query.update({'is_current': False})
            new_version.is_current = True
        
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 创建了新版本: {data['version_number']}")
        return jsonify({'success': True, 'message': '版本创建成功', 'data': new_version.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建版本失败: {str(e)}")
        return jsonify({'success': False, 'message': '创建版本失败', 'error': str(e)}), 500

@version_management_bp.route('/api/set-current-version', methods=['POST'])
@login_required
@admin_required
def api_set_current_version():
    """设置当前版本API"""
    try:
        data = request.get_json()
        version_number = data.get('version_number')
        
        if not version_number:
            return jsonify({'success': False, 'message': '缺少版本号'}), 400
        
        # 设置当前版本
        version = VersionRecord.set_current_version(version_number)
        if not version:
            return jsonify({'success': False, 'message': '版本不存在'}), 404
        
        # 记录升级日志
        previous_version = VersionRecord.query.filter(
            VersionRecord.version_number != version_number,
            VersionRecord.is_current == False
        ).order_by(VersionRecord.release_date.desc()).first()
        
        upgrade_log = UpgradeLog(
            version_id=version.id,
            from_version=previous_version.version_number if previous_version else None,
            to_version=version_number,
            upgrade_type='manual',
            status='success',
            operator_id=current_user.id,
            operator_name=current_user.username,
            environment=current_app.config.get('FLASK_ENV', 'production'),
            upgrade_notes=data.get('notes', '手动设置当前版本')
        )
        
        db.session.add(upgrade_log)
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 设置当前版本为: {version_number}")
        return jsonify({'success': True, 'message': '当前版本设置成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"设置当前版本失败: {str(e)}")
        return jsonify({'success': False, 'message': '设置当前版本失败', 'error': str(e)}), 500

@version_management_bp.route('/api/add-feature-change', methods=['POST'])
@login_required
@admin_required
def api_add_feature_change():
    """添加功能变更记录API"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['version_id', 'change_type', 'title']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必填字段: {field}'}), 400
        
        # 验证版本是否存在
        version = VersionRecord.query.get(data['version_id'])
        if not version:
            return jsonify({'success': False, 'message': '版本不存在'}), 404
        
        # 创建功能变更记录
        feature_change = FeatureChange(
            version_id=data['version_id'],
            change_type=data['change_type'],
            module_name=data.get('module_name'),
            title=data['title'],
            description=data.get('description'),
            priority=data.get('priority', 'medium'),
            impact_level=data.get('impact_level', 'minor'),
            affected_files=json.dumps(data.get('affected_files', [])) if data.get('affected_files') else None,
            git_commits=json.dumps(data.get('git_commits', [])) if data.get('git_commits') else None,
            test_status=data.get('test_status', 'pending'),
            test_notes=data.get('test_notes'),
            developer_id=current_user.id,
            developer_name=current_user.username
        )
        
        db.session.add(feature_change)
        
        # 更新版本统计
        if data['change_type'] == 'feature':
            version.total_features += 1
        elif data['change_type'] == 'fix':
            version.total_fixes += 1
        elif data['change_type'] == 'improvement':
            version.total_improvements += 1
        
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 添加了功能变更: {data['title']}")
        return jsonify({'success': True, 'message': '功能变更记录添加成功', 'data': feature_change.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加功能变更记录失败: {str(e)}")
        return jsonify({'success': False, 'message': '添加功能变更记录失败', 'error': str(e)}), 500

@version_management_bp.route('/api/version-statistics')
@login_required
def api_version_statistics():
    """获取版本统计信息API"""
    try:
        # 基本统计
        stats = {
            'total_versions': VersionRecord.query.count(),
            'total_upgrades': UpgradeLog.query.count(),
            'successful_upgrades': UpgradeLog.query.filter_by(status='success').count(),
            'failed_upgrades': UpgradeLog.query.filter_by(status='failed').count(),
            'total_features': db.session.query(db.func.sum(VersionRecord.total_features)).scalar() or 0,
            'total_fixes': db.session.query(db.func.sum(VersionRecord.total_fixes)).scalar() or 0,
            'total_improvements': db.session.query(db.func.sum(VersionRecord.total_improvements)).scalar() or 0
        }
        
        # 最近30天的升级趋势
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_upgrades = UpgradeLog.query.filter(
            UpgradeLog.upgrade_date >= thirty_days_ago
        ).order_by(UpgradeLog.upgrade_date).all()
        
        upgrade_trend = []
        for log in recent_upgrades:
            upgrade_trend.append({
                'date': log.upgrade_date.strftime('%Y-%m-%d'),
                'version': log.to_version,
                'status': log.status
            })
        
        # 功能变更类型分布
        change_type_stats = db.session.query(
            FeatureChange.change_type,
            db.func.count(FeatureChange.id).label('count')
        ).group_by(FeatureChange.change_type).all()
        
        change_distribution = {item[0]: item[1] for item in change_type_stats}
        
        result = {
            'basic_stats': stats,
            'upgrade_trend': upgrade_trend,
            'change_distribution': change_distribution
        }
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"获取版本统计信息失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取统计信息失败', 'error': str(e)}), 500

@version_management_bp.route('/api/refresh-version-check', methods=['POST'])
@login_required
@admin_required
def api_refresh_version_check():
    """刷新版本检查API"""
    try:
        # 执行版本检查
        success = update_version_check()
        
        if success:
            # 获取最新的版本信息
            version_info = get_app_version()
            return jsonify({
                'success': True, 
                'message': '版本检查已刷新',
                'data': version_info
            })
        else:
            return jsonify({'success': False, 'message': '版本检查刷新失败'}), 500
            
    except Exception as e:
        logger.error(f"刷新版本检查失败: {str(e)}")
        return jsonify({'success': False, 'message': '刷新版本检查失败', 'error': str(e)}), 500

@version_management_bp.route('/api/system-metrics', methods=['POST'])
@login_required
@admin_required
def api_record_system_metrics():
    """记录系统指标API"""
    try:
        data = request.get_json()
        
        # 获取当前版本
        current_version = VersionRecord.get_current_version()
        
        # 创建系统指标记录
        metrics = SystemMetrics(
            version_id=current_version.id if current_version else None,
            avg_response_time=data.get('avg_response_time'),
            max_response_time=data.get('max_response_time'),
            error_rate=data.get('error_rate'),
            active_users=data.get('active_users'),
            total_requests=data.get('total_requests'),
            database_size=data.get('database_size'),
            cpu_usage=data.get('cpu_usage'),
            memory_usage=data.get('memory_usage'),
            disk_usage=data.get('disk_usage')
        )
        
        db.session.add(metrics)
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 记录了系统指标")
        return jsonify({'success': True, 'message': '系统指标记录成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"记录系统指标失败: {str(e)}")
        return jsonify({'success': False, 'message': '记录系统指标失败', 'error': str(e)}), 500 