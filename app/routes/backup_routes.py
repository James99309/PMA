#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份管理路由
提供Web界面管理数据库备份功能
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.database_backup import get_backup_service
from app.permissions import permission_required
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')

@backup_bp.route('/')
@login_required
@permission_required('user', 'view')  # 使用用户管理权限作为系统管理权限
def index():
    """备份管理主页"""
    try:
        backup_service = get_backup_service()
        if not backup_service:
            flash('备份服务未启用', 'warning')
            return render_template('backup/index.html', backup_status=None)
        
        backup_status = backup_service.get_backup_status()
        return render_template('backup/index.html', backup_status=backup_status)
        
    except Exception as e:
        logger.error(f"获取备份状态失败: {str(e)}")
        flash(f'获取备份状态失败: {str(e)}', 'error')
        return render_template('backup/index.html', backup_status=None)

@backup_bp.route('/create', methods=['POST'])
@login_required
@permission_required('user', 'view')
def create_backup():
    """手动创建备份"""
    try:
        backup_type = request.form.get('backup_type', 'full')
        if backup_type not in ['full', 'schema_only', 'data_only']:
            return jsonify({'success': False, 'message': '无效的备份类型'})
        
        backup_service = get_backup_service()
        if not backup_service:
            return jsonify({'success': False, 'message': '备份服务未启用'})
        
        backup_path = backup_service.create_backup(backup_type)
        
        if backup_path:
            logger.info(f"用户 {current_user.username} 手动创建了备份: {backup_path}")
            return jsonify({
                'success': True, 
                'message': f'{backup_type} 备份创建成功',
                'backup_path': backup_path
            })
        else:
            return jsonify({'success': False, 'message': '备份创建失败'})
            
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建备份失败: {str(e)}'})

@backup_bp.route('/status')
@login_required
@permission_required('user', 'view')
def backup_status():
    """获取备份状态API"""
    try:
        backup_service = get_backup_service()
        if not backup_service:
            return jsonify({'success': False, 'message': '备份服务未启用'})
        
        status = backup_service.get_backup_status()
        return jsonify({'success': True, 'data': status})
        
    except Exception as e:
        logger.error(f"获取备份状态失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取备份状态失败: {str(e)}'})

@backup_bp.route('/cleanup', methods=['POST'])
@login_required
@permission_required('user', 'view')
def cleanup_backups():
    """清理过期备份"""
    try:
        backup_service = get_backup_service()
        if not backup_service:
            return jsonify({'success': False, 'message': '备份服务未启用'})
        
        backup_service.cleanup_old_backups()
        logger.info(f"用户 {current_user.username} 执行了备份清理操作")
        
        return jsonify({'success': True, 'message': '过期备份清理完成'})
        
    except Exception as e:
        logger.error(f"清理备份失败: {str(e)}")
        return jsonify({'success': False, 'message': f'清理备份失败: {str(e)}'})

@backup_bp.route('/download/<filename>')
@login_required
@permission_required('user', 'view')
def download_backup(filename):
    """下载备份文件"""
    try:
        backup_service = get_backup_service()
        if not backup_service:
            flash('备份服务未启用', 'warning')
            return redirect(url_for('backup.index'))
        
        # 安全检查：确保文件名符合备份文件格式
        if not filename.startswith('cloud_backup_') or not filename.endswith('.sql'):
            flash('无效的备份文件', 'error')
            return redirect(url_for('backup.index'))
        
        from flask import send_file
        import os
        
        backup_path = os.path.join(backup_service.backup_location, filename)
        
        if not os.path.exists(backup_path):
            flash('备份文件不存在', 'error')
            return redirect(url_for('backup.index'))
        
        logger.info(f"用户 {current_user.username} 下载了备份文件: {filename}")
        return send_file(backup_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"下载备份文件失败: {str(e)}")
        flash(f'下载失败: {str(e)}', 'error')
        return redirect(url_for('backup.index'))

@backup_bp.route('/incremental', methods=['POST'])
@login_required
@permission_required('user', 'view')
def create_incremental_backup():
    """创建增量备份"""
    try:
        backup_service = get_backup_service()
        if not backup_service:
            return jsonify({'success': False, 'message': '备份服务未启用'})
        
        backup_path = backup_service.create_incremental_backup()
        
        if backup_path:
            logger.info(f"用户 {current_user.username} 创建了增量备份: {backup_path}")
            return jsonify({
                'success': True, 
                'message': '增量备份创建成功',
                'backup_path': backup_path
            })
        else:
            return jsonify({'success': False, 'message': '增量备份创建失败'})
            
    except Exception as e:
        logger.error(f"创建增量备份失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建增量备份失败: {str(e)}'})

@backup_bp.route('/details/<filename>')
@login_required
@permission_required('user', 'view')
def backup_details(filename):
    """获取备份文件详情"""
    try:
        backup_service = get_backup_service()
        if not backup_service:
            return jsonify({
                'success': False,
                'message': '备份服务未启用'
            })
        
        # 获取备份文件信息
        import os
        backup_path = os.path.join(backup_service.backup_location, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'message': '备份文件不存在'
            })
        
        # 获取文件基本信息
        file_stat = os.stat(backup_path)
        file_size_mb = file_stat.st_size / (1024 * 1024)
        created_at = datetime.fromtimestamp(file_stat.st_mtime)
        
        # 确定备份类型
        backup_type = '数据+结构备份'
        if 'incremental' in filename:
            backup_type = '增量备份'
        elif 'schema' in filename:
            backup_type = '结构备份'
        elif 'data' in filename:
            backup_type = '数据备份'
        
        # 获取数据库信息
        db_info = get_database_info()
        
        details = {
            'filename': filename,
            'size': f'{file_size_mb:.1f} MB',
            'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'backup_type': backup_type,
            'database_name': db_info.get('database_name', 'pma_local'),
            'table_count': db_info.get('table_count', 0),
            'total_records': db_info.get('total_records', 0),
            'data_size': db_info.get('data_size', '未知'),
            'tables': db_info.get('tables', []),
            'changes': [
                f'备份时间: {created_at.strftime("%Y-%m-%d %H:%M:%S")}',
                f'备份大小: {file_size_mb:.1f} MB',
                f'包含 {db_info.get("table_count", 0)} 个数据表',
                f'总计 {db_info.get("total_records", 0):,} 条记录'
            ]
        }
        
        return jsonify({
            'success': True,
            'details': details
        })
        
    except Exception as e:
        logger.error(f"获取备份详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取备份详情失败: {str(e)}'
        })

def get_database_info():
    """获取当前数据库信息"""
    try:
        from app import db
        from datetime import datetime
        
        with db.engine.connect() as conn:
            # 获取数据库名称
            result = conn.execute(db.text("SELECT current_database()"))
            database_name = result.fetchone()[0]
            
            # 获取表数量和信息
            result = conn.execute(db.text("""
                SELECT 
                    schemaname as schema_name,
                    tablename as table_name,
                    n_tup_ins as rows_inserted,
                    n_tup_upd as rows_updated,
                    n_tup_del as rows_deleted
                FROM pg_stat_user_tables 
                ORDER BY schemaname, tablename
            """))
            
            tables_info = result.fetchall()
            table_count = len(tables_info)
            
            # 获取总记录数
            total_records = 0
            tables_detail = []
            
            for table_info in tables_info:
                table_name = table_info[1]
                try:
                    # 获取表记录数
                    count_result = conn.execute(db.text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = count_result.fetchone()[0]
                    total_records += row_count
                    
                    # 获取表大小
                    size_result = conn.execute(db.text(f"SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))"))
                    table_size = size_result.fetchone()[0]
                    
                    tables_detail.append({
                        'name': table_name,
                        'rows': row_count,
                        'size': table_size,
                        'status': 'unchanged'  # 默认状态
                    })
                except Exception as e:
                    logger.warning(f"获取表 {table_name} 信息失败: {str(e)}")
                    tables_detail.append({
                        'name': table_name,
                        'rows': 0,
                        'size': 'N/A',
                        'status': 'unknown'
                    })
            
            # 获取数据库大小
            size_result = conn.execute(db.text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
            data_size = size_result.fetchone()[0]
            
            return {
                'database_name': database_name,
                'table_count': table_count,
                'total_records': total_records,
                'data_size': data_size,
                'tables': sorted(tables_detail, key=lambda x: x['rows'], reverse=True)
            }
            
    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        return {
            'database_name': 'unknown',
            'table_count': 0,
            'total_records': 0,
            'data_size': 'unknown',
            'tables': []
        }



@backup_bp.route('/config', methods=['GET', 'POST'])
@login_required
@permission_required('user', 'view')
def backup_config():
    """备份配置管理"""
    if request.method == 'GET':
        try:
            backup_service = get_backup_service()
            if not backup_service:
                return render_template('backup/config.html', config=None)
            
            config = {
                'backup_enabled': backup_service.backup_enabled,
                'backup_schedule': backup_service.backup_schedule,
                'retention_days': backup_service.retention_days,
                'backup_location': backup_service.backup_location,
                'cloud_storage': backup_service.cloud_storage
            }
            
            return render_template('backup/config.html', config=config)
            
        except Exception as e:
            logger.error(f"获取备份配置失败: {str(e)}")
            flash(f'获取备份配置失败: {str(e)}', 'error')
            return render_template('backup/config.html', config=None)
    
    elif request.method == 'POST':
        try:
            # 这里可以实现配置更新功能
            # 由于配置更改涉及到重启服务，建议通过配置文件修改
            flash('配置更新功能需要重启应用才能生效，请修改配置文件后重启', 'info')
            return redirect(url_for('backup.backup_config'))
            
        except Exception as e:
            logger.error(f"更新备份配置失败: {str(e)}")
            flash(f'更新备份配置失败: {str(e)}', 'error')
            return redirect(url_for('backup.backup_config')) 