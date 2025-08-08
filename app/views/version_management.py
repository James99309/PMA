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
from app.utils.version_auto_generator import version_generator, get_current_app_version, auto_upgrade_version, get_upgrade_info
from app.decorators import admin_required
from datetime import datetime, timedelta
import json
import os
import re
import glob
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

@version_management_bp.route('/api/versions')
@login_required
def api_versions():
    """获取版本列表API - 支持分页"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 限制每页数量，防止过量请求
        if per_page > 50:
            per_page = 50
        
        versions = VersionRecord.query.order_by(VersionRecord.release_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'versions': [version.to_dict() for version in versions.items],
            'total': versions.total,
            'pages': versions.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': versions.has_next,
            'has_prev': versions.has_prev
        }
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"获取版本列表失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取版本列表失败', 'error': str(e)}), 500

@version_management_bp.route('/api/upgrade-statistics')
@login_required
def api_upgrade_statistics():
    """获取升级统计信息API"""
    try:
        stats = {
            'total_upgrades': UpgradeLog.query.count(),
            'success_count': UpgradeLog.query.filter_by(status='success').count(),
            'failed_count': UpgradeLog.query.filter_by(status='failed').count(),
            'rollback_count': UpgradeLog.query.filter_by(status='rollback').count()
        }
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        logger.error(f"获取升级统计信息失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取升级统计信息失败', 'error': str(e)}), 500

@version_management_bp.route('/api/auto-upgrade', methods=['POST'])
@login_required
@admin_required
def api_auto_upgrade():
    """自动升级版本API"""
    try:
        # 执行自动版本升级
        new_version = auto_upgrade_version()
        
        if new_version:
            return jsonify({
                'success': True, 
                'message': '自动升级成功',
                'data': new_version.to_dict()
            })
        else:
            return jsonify({
                'success': False, 
                'message': '自动升级失败，可能没有新的Git提交'
            }), 400
            
    except Exception as e:
        logger.error(f"自动升级版本失败: {str(e)}")
        return jsonify({'success': False, 'message': '自动升级失败', 'error': str(e)}), 500

@version_management_bp.route('/api/generate-next-version', methods=['POST'])
@login_required
@admin_required
def api_generate_next_version():
    """生成下一个版本号API"""
    try:
        data = request.get_json()
        change_type = data.get('change_type', 'patch')  # major, minor, patch
        
        # 生成下一个版本号
        next_version = version_generator.generate_next_version(change_type)
        
        return jsonify({
            'success': True,
            'data': {
                'next_version': next_version,
                'change_type': change_type
            }
        })
        
    except Exception as e:
        logger.error(f"生成下一个版本号失败: {str(e)}")
        return jsonify({'success': False, 'message': '生成版本号失败', 'error': str(e)}), 500

@version_management_bp.route('/api/upgrade-info')
@login_required
def api_upgrade_info():
    """获取当前版本升级信息API"""
    try:
        version_number = request.args.get('version')
        logger.info(f"获取版本升级信息: {version_number}")
        
        upgrade_info = get_upgrade_info(version_number)
        logger.info(f"基础升级信息获取: {'成功' if upgrade_info else '失败'}")
        
        # 获取完整的版本升级文档
        if upgrade_info:
            try:
                # 获取当前版本记录对象
                current_version_record = VersionRecord.get_current_version()
                
                # 读取详细的升级文档
                upgrade_docs = get_detailed_upgrade_docs(current_version_record)
                logger.info(f"详细文档获取: {'成功' if upgrade_docs else '失败'}")
                
                if upgrade_docs:
                    # 限制文档数量和大小以避免响应过大
                    if len(upgrade_docs) > 5:
                        upgrade_docs = upgrade_docs[:5]
                        logger.info("限制文档数量为5个")
                    
                    # 限制每个文档的章节内容长度
                    for doc in upgrade_docs:
                        if doc.get('sections'):
                            for section_key, section_content in doc['sections'].items():
                                if len(section_content) > 2000:
                                    doc['sections'][section_key] = section_content[:2000] + '...'
                    
                    upgrade_info['detailed_docs'] = upgrade_docs
                    logger.info(f"添加了 {len(upgrade_docs)} 个详细文档")
                
            except Exception as doc_error:
                logger.warning(f"获取详细文档失败，使用基础信息: {str(doc_error)}")
                # 即使详细文档失败，仍然返回基础信息
                pass
            
            return jsonify({'success': True, 'data': upgrade_info})
        else:
            logger.warning("未找到版本升级信息")
            return jsonify({'success': False, 'message': '未找到版本升级信息'}), 404
            
    except Exception as e:
        logger.error(f"获取版本升级信息失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': '获取升级信息失败', 'error': str(e)}), 500


def get_detailed_upgrade_docs(version_record):
    """获取版本的详细升级文档"""
    if not version_record or not version_record.git_commit:
        return None
    
    try:
        # 基于Git提交查找相关的文档文件
        docs = []
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        
        # 查找可能的升级文档文件
        doc_patterns = [
            '*IMPROVEMENTS_SUMMARY.md',
            '*EXPANSION_SUMMARY.md', 
            '*UPGRADE_SUMMARY.md',
            '*CHANGES.md'
        ]
        
        for pattern in doc_patterns:
            matching_files = glob.glob(os.path.join(project_root, pattern))
            for file_path in matching_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 解析文档内容
                        doc_info = parse_upgrade_document(content, os.path.basename(file_path))
                        if doc_info:
                            docs.append(doc_info)
                            
                except Exception as e:
                    logger.warning(f"读取升级文档失败 {file_path}: {str(e)}")
                    continue
        
        return docs if docs else None
        
    except Exception as e:
        logger.error(f"获取详细升级文档失败: {str(e)}")
        return None


def parse_upgrade_document(content, filename):
    """解析升级文档内容"""
    try:
        lines = content.split('\n')
        
        # 提取标题
        title = ""
        for line in lines[:5]:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # 提取主要章节
        sections = {}
        current_section = None
        current_content = []
        
        for line in lines:
            # 检测章节标题
            if line.startswith('## '):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # 添加最后一个章节
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # 提取关键信息
        doc_info = {
            'filename': filename,
            'title': title or filename.replace('.md', '').replace('_', ' ').title(),
            'sections': sections
        }
        
        # 提取改进统计
        stats = extract_improvement_stats(content)
        if stats:
            doc_info['stats'] = stats
            
        # 提取主要改进点
        improvements = extract_key_improvements(content)
        if improvements:
            doc_info['key_improvements'] = improvements
            
        return doc_info
        
    except Exception as e:
        logger.error(f"解析升级文档失败: {str(e)}")
        return None


def extract_improvement_stats(content):
    """提取改进统计信息"""
    try:
        stats = {}
        
        # 查找统计信息
        patterns = [
            (r'(\d+).*文件.*变更', 'files_changed'),
            (r'(\d+).*行.*增加', 'lines_added'),
            (r'(\d+).*行.*删除', 'lines_removed'),
            (r'(\d+).*功能', 'features'),
            (r'(\d+).*修复', 'fixes'),
            (r'(\d+).*改进', 'improvements')
        ]
        
        for pattern, key in patterns:
            matches = re.findall(pattern, content)
            if matches:
                stats[key] = int(matches[0])
        
        return stats if stats else None
        
    except Exception as e:
        return None


def extract_key_improvements(content):
    """提取关键改进点"""
    try:
        improvements = []
        
        # 查找改进点标记
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 查找标记改进的行
            if any(marker in line_stripped for marker in ['✅', '🎯', '💡', '🛠️', '🚀']):
                # 提取改进描述
                improvement_text = re.sub(r'^[✅🎯💡🛠️🚀\s\*\-\d\.]*', '', line_stripped).strip()
                if improvement_text and len(improvement_text) > 10:
                    improvements.append({
                        'text': improvement_text,
                        'type': get_improvement_type(line_stripped)
                    })
        
        return improvements[:10] if improvements else None  # 限制最多10个要点
        
    except Exception as e:
        return None


def get_improvement_type(line):
    """根据标记获取改进类型"""
    if '✅' in line:
        return 'completed'
    elif '🎯' in line:
        return 'target'
    elif '💡' in line:
        return 'insight'
    elif '🛠️' in line:
        return 'fix'
    elif '🚀' in line:
        return 'enhancement'
    else:
        return 'general' 