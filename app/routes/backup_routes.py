#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份管理路由
提供Web界面管理 Supabase 自动备份功能
"""

from flask import Blueprint, render_template, request, jsonify, send_file, current_app, url_for
from flask_login import login_required, current_user
from app.permissions import permission_required
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')

@backup_bp.route('/')
@login_required
@permission_required('user', 'view')  # 使用用户管理权限作为系统管理权限
def index():
    """备份管理主页"""
    try:
        from app.services.supabase_backup_service import get_backup_service
        from flask_babel import gettext as _

        backup_service = get_backup_service()

        # 获取备份列表
        backups = backup_service.list_backups()

        # 获取存储使用情况
        storage_info = backup_service.get_storage_usage()

        # 准备显示数据并转换为字典对象（供通用组件使用）
        backup_objects = []
        sp8d_count = 0
        ovs_count = 0
        local_count = 0

        for backup in backups:
            # 计算文件年龄
            created_at = datetime.fromisoformat(backup['created_at'].replace('Z', '+00:00'))
            age_days = (datetime.now() - created_at.replace(tzinfo=None)).days

            # 格式化大小
            size_mb = backup['size'] / 1024 / 1024
            size_display = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{backup['size'] / 1024:.1f} KB"

            # 数据库类型统计
            db_type = backup.get('db_type', 'unknown')
            if db_type == 'sp8d':
                sp8d_count += 1
            elif db_type == 'ovs':
                ovs_count += 1
            elif db_type == 'local':
                local_count += 1

            # 创建备份对象（添加__class__属性以供通用组件识别）
            class BackupFile:
                def __init__(self, data):
                    self.filename = data['filename']
                    self.db_type = db_type
                    self.size = data['size']
                    self.size_display = size_display
                    self.created_at = created_at
                    self.created_display = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    self.age = f"{age_days}天前" if age_days > 0 else "今天"
                    self.path = data.get('storage_path', data['filename'])  # 使用 storage_path 获取完整路径

            backup_objects.append(BackupFile(backup))

        # 获取最后备份时间
        last_backup_time = backup_objects[0].created_display if backup_objects else '从未备份'
        last_backup_age = backup_objects[0].age if backup_objects else ''

        # 环境信息 - 动态读取当前数据库配置
        from config import Config
        db_url = Config.SQLALCHEMY_DATABASE_URI

        # 识别数据库类型并格式化显示
        if 'localhost' in db_url or '127.0.0.1' in db_url:
            db_display = 'pma_local@localhost'
        elif 'sqlite' in db_url:
            db_display = 'SQLite 本地数据库'
        elif 'iqcyimnjtnmomvfuwjzw' in db_url:
            db_display = 'SP8D@Supabase'
        elif 'pqzviljbpfoqvyfulakl' in db_url:
            db_display = 'OVS@Supabase'
        else:
            # 提取主机信息
            try:
                db_display = db_url.split('@')[1].split('/')[0] if '@' in db_url else '未知数据库'
            except:
                db_display = '未知数据库'

        env_info = {
            'environment': '本地开发' if Config.IS_LOCAL_ENV else '云端生产',
            'storage_location': '本地文件系统',
            'database': db_display
        }

        # 计算总存储使用
        total_storage_mb = storage_info.get('total_size', 0) / 1024 / 1024

        # 准备通用列表配置
        list_config = {
            'module_name': 'backup',
            'title': _('数据库备份管理'),
            'ajax_mode': False,  # 不使用AJAX模式，直接渲染

            # 统计卡片配置
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': _('备份总数'),
                        'icon': 'fas fa-database',
                        'value': len(backup_objects),
                        'unit': _('个'),
                        'color': 'primary',
                        'data_key': 'total'
                    },
                    {
                        'id': 'sp8d',
                        'title': 'SP8D ' + _('备份'),
                        'icon': 'fas fa-server',
                        'value': sp8d_count,
                        'unit': _('个'),
                        'color': 'info',
                        'data_key': 'sp8d'
                    },
                    {
                        'id': 'ovs',
                        'title': 'OVS ' + _('备份'),
                        'icon': 'fas fa-server',
                        'value': ovs_count,
                        'unit': _('个'),
                        'color': 'success',
                        'data_key': 'ovs'
                    },
                    {
                        'id': 'storage',
                        'title': _('存储使用'),
                        'icon': 'fas fa-hard-drive',
                        'value': f"{total_storage_mb:.1f}",
                        'unit': 'MB',
                        'color': 'warning',
                        'data_key': 'storage'
                    }
                ]
            },

            # 筛选配置
            'filter': {
                'action_url': url_for('backup.index'),
                'form_id': 'backupFilterForm',
                'reset_url': url_for('backup.index'),
                'search_field': {
                    'name': 'search',
                    'label': _('搜索'),
                    'placeholder': _('备份文件名'),
                    'value': request.args.get('search', ''),
                    'col_width': 4
                },
                'filter_fields': [
                    {
                        'name': 'db_type',
                        'label': _('数据库类型'),
                        'type': 'select',
                        'col_width': 2,
                        'options': [
                            {'value': '', 'label': _('全部')},
                            {'value': 'sp8d', 'label': 'SP8D'},
                            {'value': 'ovs', 'label': 'OVS'},
                            {'value': 'local', 'label': _('本地')}
                        ],
                        'value': request.args.get('db_type', '')
                    }
                ],
                'search_button_text': _('搜索'),
                'reset_button_text': _('重置')
            },

            # 表格配置
            'table': {
                'title': _('备份文件列表'),
                'icon': 'fas fa-table',
                'show_header': True,
                'columns': [
                    {
                        'key': 'filename',
                        'label': _('文件名'),
                        'type': 'text',
                        'width': '35%',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'db_type',
                        'label': _('数据库'),
                        'type': 'badge',
                        'render': 'render_backup_db_type_badge',
                        'width': '10%'
                    },
                    {
                        'key': 'size_display',
                        'label': _('文件大小'),
                        'type': 'text',
                        'width': '12%',
                        'align': 'right'
                    },
                    {
                        'key': 'created_display',
                        'label': _('备份时间'),
                        'type': 'text',
                        'width': '18%'
                    },
                    {
                        'key': 'age',
                        'label': _('备份年龄'),
                        'type': 'text',
                        'width': '10%'
                    },
                    {
                        'key': 'actions',
                        'label': _('操作'),
                        'type': 'actions',
                        'width': '15%',
                        'align': 'center'
                    }
                ],
                'empty_message': _('暂无备份文件，请点击"立即备份"按钮创建备份。')
            }
        }

        return render_template(
            'backup/index.html',
            list_config=list_config,
            backups=backup_objects,
            storage_info=storage_info,
            env_info=env_info,
            last_backup_time=last_backup_time,
            last_backup_age=last_backup_age
        )

    except Exception as e:
        import traceback
        logger.error(f"获取备份信息失败: {str(e)}")
        logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")

        # 错误情况下的配置
        error_list_config = {
            'module_name': 'backup',
            'title': _('数据库备份管理'),
            'ajax_mode': False,
            'stats': {'cards': []},
            'filter': {
                'action_url': url_for('backup.index'),
                'form_id': 'backupFilterForm',
                'search_field': {
                    'name': 'search',
                    'label': _('搜索'),
                    'placeholder': _('备份文件名'),
                    'value': ''
                },
                'filter_fields': []
            },
            'table': {
                'columns': [],
                'empty_message': _('加载备份列表失败：') + str(e)
            }
        }

        return render_template(
            'backup/index.html',
            list_config=error_list_config,
            backups=[],
            storage_info={},
            env_info={},
            error=str(e)
        )


@backup_bp.route('/create-now', methods=['POST'])
@login_required
@permission_required('user', 'view')
def create_backup_now():
    """立即创建备份（异步）"""
    try:
        from app.services.supabase_backup_service import get_backup_service

        backup_service = get_backup_service()

        # 安全获取JSON数据
        data = request.get_json()

        if data is None:
            data = {}

        db_type = data.get('db_type', 'both')  # both, sp8d, ovs

        # 启动异步备份任务
        task_id = backup_service.create_backup_async(db_type)

        return jsonify({
            'success': True,
            'message': '备份任务已启动',
            'task_id': task_id
        })

    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'备份失败: {str(e)}'
        }), 500


@backup_bp.route('/task-status/<task_id>')
@login_required
@permission_required('user', 'view')
def get_task_status(task_id):
    """获取备份任务状态"""
    try:
        from app.services.supabase_backup_service import get_backup_service

        backup_service = get_backup_service()
        status = backup_service.get_task_status(task_id)

        return jsonify(status)

    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@backup_bp.route('/download/<path:filename>')
@login_required
@permission_required('user', 'view')
def download_backup(filename):
    """下载备份文件（支持包含子目录的路径）"""
    try:
        from app.services.supabase_backup_service import get_backup_service

        backup_service = get_backup_service()

        # 从本地文件系统下载
        filepath = os.path.join(backup_service.backup_dir, filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': '文件不存在'}), 404

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"下载备份失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@backup_bp.route('/delete/<path:filename>', methods=['DELETE'])
@login_required
@permission_required('user', 'view')
def delete_backup(filename):
    """删除备份文件（支持包含子目录的路径）"""
    try:
        from app.services.supabase_backup_service import get_backup_service

        # 🔍 调试：记录接收到的文件名
        logger.info(f"🔍 删除路由接收到的 filename: {filename}")
        logger.info(f"🔍 URL编码后的值: {repr(filename)}")

        backup_service = get_backup_service()

        # 🔍 调试：准备调用删除服务
        logger.info(f"🔍 准备调用 delete_backup({filename})")
        success = backup_service.delete_backup(filename)
        logger.info(f"🔍 delete_backup 返回结果: {success}")

        if success:
            return jsonify({
                'success': True,
                'message': '备份已删除'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除失败'
            }), 500

    except Exception as e:
        logger.error(f"删除备份失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@backup_bp.route('/cleanup', methods=['POST'])
@login_required
@permission_required('user', 'view')
def cleanup_old_backups():
    """清理旧备份"""
    try:
        from app.services.supabase_backup_service import get_backup_service

        backup_service = get_backup_service()
        days = request.json.get('days', backup_service.retention_days)

        deleted_count = backup_service.cleanup_old_backups(days)

        return jsonify({
            'success': True,
            'message': f'清理完成，删除了 {deleted_count} 个备份',
            'deleted_count': deleted_count
        })

    except Exception as e:
        logger.error(f"清理备份失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@backup_bp.route('/storage-usage')
@login_required
@permission_required('user', 'view')
def get_storage_usage():
    """获取存储使用情况"""
    try:
        from app.services.supabase_backup_service import get_backup_service

        backup_service = get_backup_service()
        usage = backup_service.get_storage_usage()

        return jsonify({
            'success': True,
            'usage': usage
        })

    except Exception as e:
        logger.error(f"获取存储使用情况失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
