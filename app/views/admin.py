from app.extensions import db
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort, jsonify
from flask_login import login_required, current_user
from app.decorators import admin_required
from app.models.settings import SystemSettings, DEFAULT_SETTINGS
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    """系统参数设置页面"""
    if request.method == 'POST':
        # 处理表单提交
        try:
            # 导入历史记录跟踪器
            from app.utils.change_tracker import ChangeTracker

            # 遍历表单数据，更新系统设置
            for key in DEFAULT_SETTINGS.keys():
                if key in request.form:
                    try:
                        # 尝试将值转换为整数
                        value = int(request.form.get(key))
                        # 确保值有效
                        if value <= 0:
                            flash(f'参数 {key} 必须大于0', 'danger')
                            continue
                    except (ValueError, TypeError):
                        flash(f'参数 {key} 必须是有效的数字', 'danger')
                        continue

                    # 获取旧值用于历史记录
                    old_value = SystemSettings.get(key, DEFAULT_SETTINGS[key]['value'])

                    # 更新设置，直接存储为int
                    SystemSettings.set(key, value)

                    # 记录变更历史
                    try:
                        # 创建一个虚拟对象来记录系统设置变更
                        class SystemSettingsRecord:
                            def __init__(self):
                                self.id = 0
                                self.__tablename__ = 'system_settings'

                        settings_obj = SystemSettingsRecord()
                        ChangeTracker.track_change(
                            obj=settings_obj,
                            action='update',
                            user_id=current_user.id,
                            changes={
                                key: {'old': old_value, 'new': value}
                            },
                            description=f'系统设置更新：{DEFAULT_SETTINGS[key]["label"]}'
                        )
                    except Exception as e:
                        logger.error(f"记录系统设置变更历史失败: {str(e)}")

            db.session.commit()
            flash('系统设置已更新', 'success')
            return redirect(url_for('admin.system_settings'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"更新系统设置失败: {str(e)}")
            flash(f'更新失败: {str(e)}', 'danger')

    # GET请求，显示设置页面
    settings = {}
    for key, config in DEFAULT_SETTINGS.items():
        settings[key] = {
            'label': config['label'],
            'description': config['description'],
            'value': SystemSettings.get(key, config['value']),
            'unit': config.get('unit', ''),
            'default': config['value']
        }

    return render_template('admin/system_settings.html', settings=settings)

@admin_bp.route('/refresh_project_activity', methods=['POST'])
@login_required
@admin_required
def refresh_project_activity():
    """手动刷新所有项目的活跃状态"""
    try:
        from app.models.project import Project
        from app.utils.project_activity import update_project_activity

        success_count = 0
        error_count = 0

        # 分批处理，避免一次性加载全部项目到内存
        batch_size = 100
        offset = 0
        while True:
            projects = Project.query.filter(Project.is_deleted == False) \
                .limit(batch_size).offset(offset).all()
            if not projects:
                break
            for project in projects:
                try:
                    update_project_activity(project)
                    success_count += 1
                except Exception as e:
                    logger.error(f"更新项目 {project.id} 活跃状态失败: {str(e)}")
                    error_count += 1
            db.session.commit()
            offset += batch_size

        message = f'项目活跃状态刷新完成：成功 {success_count} 个'
        if error_count > 0:
            message += f'，失败 {error_count} 个'

        flash(message, 'success' if error_count == 0 else 'warning')

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量刷新项目活跃状态失败: {str(e)}")
        flash(f'刷新失败: {str(e)}', 'danger')

    return redirect(url_for('admin.system_settings'))

@admin_bp.route('/')
@admin_required
def index():
    """管理员首页"""
    return redirect(url_for('admin.system_settings'))
