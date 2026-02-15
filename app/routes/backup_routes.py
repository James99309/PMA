#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份管理路由
提供 Web 界面和 API 管理数据库备份
"""

from flask import Blueprint, render_template, request, jsonify, send_file, current_app, url_for, Response
from flask_login import login_required, current_user
from app.permissions import permission_required
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')


@backup_bp.route('/')
@login_required
@permission_required('user', 'view')
def index():
    """备份管理主页 — Tailwind 版"""
    try:
        from app.services.supabase_backup_service import get_backup_service
        from flask_babel import gettext as _

        backup_service = get_backup_service()

        # 获取备份列表
        backups = backup_service.list_backups()

        # 统计
        stats = backup_service.get_backup_statistics()
        settings = backup_service.get_backup_settings()
        health = backup_service.get_health_status()

        # 为每个备份添加显示属性
        for backup in backups:
            created_at = datetime.fromisoformat(backup['created_at'].replace('Z', '').replace('+00:00', ''))
            age_delta = datetime.now() - created_at
            age_days = age_delta.days
            age_hours = int(age_delta.total_seconds() / 3600)

            backup['created_display'] = created_at.strftime('%Y-%m-%d %H:%M')
            backup['size_display'] = _format_size(backup['size'])

            if age_days > 0:
                backup['age'] = f"{age_days}" + _('天前')
            elif age_hours > 0:
                backup['age'] = f"{age_hours}" + _('小时前')
            else:
                backup['age'] = _("刚刚")

        # 计算下次备份时间
        next_backup = _get_next_backup_time(settings)

        # 环境信息
        from config import Config
        db_url = Config.SQLALCHEMY_DATABASE_URI

        if 'localhost' in db_url or '127.0.0.1' in db_url:
            db_display = 'pma_local@localhost'
        elif 'sqlite' in db_url:
            db_display = 'SQLite'
        else:
            try:
                db_display = db_url.split('@')[1].split('/')[0] if '@' in db_url else '未知'
            except Exception:
                db_display = '未知'

        # 存储位置显示
        if backup_service.use_nas_storage:
            storage_display = f'NAS WebDAV ({backup_service.nas_backup_path})'
        else:
            storage_display = None  # 模板中按 is_local 判断

        return render_template(
            'backup/tw_index.html',
            backups=backups,
            stats=stats,
            settings=settings,
            health=health,
            db_display=db_display,
            next_backup=next_backup,
            is_local=Config.IS_LOCAL_ENV,
            storage_display=storage_display,
        )

    except Exception as e:
        import traceback
        logger.error(f"获取备份信息失败: {str(e)}")
        logger.error(traceback.format_exc())

        return render_template(
            'backup/tw_index.html',
            backups=[],
            stats={'total_count': 0, 'total_size_mb': 0, 'sp8d_count': 0, 'ovs_count': 0, 'local_count': 0, 'latest_backup': None},
            settings={'retention_days': 30, 'auto_backup_enabled': False, 'auto_backup_time': '03:00', 'notify_enabled': True, 'db_type': 'unknown', 'backup_dir': ''},
            health={'is_healthy': False, 'last_backup_time': None, 'last_backup_age_hours': None, 'message': '加载失败'},
            db_display='错误',
            next_backup='未知',
            is_local=True,
            storage_display=None,
            error=str(e),
        )


# ==================== API 端点 ====================

@backup_bp.route('/api/statistics')
@login_required
@permission_required('user', 'view')
def api_statistics():
    """备份统计 API"""
    try:
        from app.services.supabase_backup_service import get_backup_service
        stats = get_backup_service().get_backup_statistics()
        return jsonify({'success': True, **stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@backup_bp.route('/api/settings')
@login_required
@permission_required('user', 'view')
def api_settings():
    """备份配置 API"""
    try:
        from app.services.supabase_backup_service import get_backup_service
        settings = get_backup_service().get_backup_settings()
        return jsonify({'success': True, **settings})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@backup_bp.route('/api/health')
@login_required
@permission_required('user', 'view')
def api_health():
    """健康检查 API"""
    try:
        from app.services.supabase_backup_service import get_backup_service
        health = get_backup_service().get_health_status()
        return jsonify({'success': True, **health})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@backup_bp.route('/api/scheduler-status')
@login_required
@permission_required('user', 'view')
def api_scheduler_status():
    """调度器状态 API"""
    try:
        from app.utils.scheduled_tasks import get_scheduler_status
        status = get_scheduler_status()
        return jsonify({'success': True, **status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 操作端点 ====================

@backup_bp.route('/create-now', methods=['POST'])
@login_required
@permission_required('user', 'view')
def create_backup_now():
    """立即创建备份（异步）"""
    try:
        from app.services.supabase_backup_service import get_backup_service

        backup_service = get_backup_service()
        data = request.get_json() or {}
        db_type = data.get('db_type', 'both')

        task_id = backup_service.create_backup_async(db_type)

        return jsonify({
            'success': True,
            'message': '备份任务已启动',
            'task_id': task_id
        })

    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return jsonify({'success': False, 'message': f'备份失败: {str(e)}'}), 500


@backup_bp.route('/task-status/<task_id>')
@login_required
@permission_required('user', 'view')
def get_task_status(task_id):
    """获取备份任务状态"""
    try:
        from app.services.supabase_backup_service import get_backup_service
        status = get_backup_service().get_task_status(task_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@backup_bp.route('/download/<path:filename>')
@login_required
@permission_required('user', 'view')
def download_backup(filename):
    """下载备份文件"""
    try:
        from app.services.supabase_backup_service import get_backup_service
        from io import BytesIO

        backup_service = get_backup_service()

        if backup_service.use_nas_storage:
            # NAS 模式：从 WebDAV 下载内容后返回
            content = backup_service.download_backup_content(filename)
            if not content:
                return jsonify({'success': False, 'message': '文件不存在'}), 404
            return send_file(
                BytesIO(content),
                as_attachment=True,
                download_name=os.path.basename(filename)
            )
        else:
            # 本地模式
            filepath = _validate_backup_path(backup_service.backup_dir, filename)
            if not os.path.exists(filepath):
                return jsonify({'success': False, 'message': '文件不存在'}), 404
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filename))

    except Exception as e:
        logger.error(f"下载备份失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@backup_bp.route('/delete/<path:filename>', methods=['DELETE'])
@login_required
@permission_required('user', 'view')
def delete_backup(filename):
    """删除备份文件"""
    try:
        from app.services.supabase_backup_service import get_backup_service

        backup_service = get_backup_service()

        if not backup_service.use_nas_storage:
            # 本地模式：验证路径防止 path traversal
            _validate_backup_path(backup_service.backup_dir, filename)

        success = backup_service.delete_backup(filename)

        if success:
            return jsonify({'success': True, 'message': '备份已删除'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 500

    except Exception as e:
        logger.error(f"删除备份失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@backup_bp.route('/cleanup', methods=['POST'])
@login_required
@permission_required('user', 'view')
def cleanup_old_backups():
    """清理旧备份"""
    try:
        from app.services.supabase_backup_service import get_backup_service

        backup_service = get_backup_service()
        data = request.get_json() or {}
        days = data.get('days', backup_service.retention_days)

        deleted_count = backup_service.cleanup_old_backups(days)

        return jsonify({
            'success': True,
            'message': f'清理完成，删除了 {deleted_count} 个备份',
            'deleted_count': deleted_count
        })

    except Exception as e:
        logger.error(f"清理备份失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@backup_bp.route('/storage-usage')
@login_required
@permission_required('user', 'view')
def get_storage_usage():
    """获取存储使用情况"""
    try:
        from app.services.supabase_backup_service import get_backup_service
        usage = get_backup_service().get_storage_usage()
        return jsonify({'success': True, 'usage': usage})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 辅助函数 ====================

def _validate_backup_path(backup_dir: str, filename: str) -> str:
    """验证备份文件路径，防止 path traversal 攻击"""
    filepath = os.path.realpath(os.path.join(backup_dir, filename))
    if not filepath.startswith(os.path.realpath(backup_dir)):
        raise ValueError('非法文件路径')
    return filepath


def _format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1048576:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / 1048576:.1f} MB"


def _get_next_backup_time(settings: dict) -> str:
    """计算下次备份时间"""
    if not settings.get('auto_backup_enabled'):
        return '未启用'

    backup_time = settings.get('auto_backup_time', '03:00')
    try:
        hour, minute = map(int, backup_time.split(':'))
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)

        delta = next_run - now
        hours = int(delta.total_seconds() / 3600)
        if hours < 1:
            return f"{backup_time} (不到1小时)"
        elif hours < 24:
            return f"{backup_time} ({hours}小时后)"
        else:
            return f"{backup_time} (明日)"
    except Exception:
        return backup_time
