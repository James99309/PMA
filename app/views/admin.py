from app.models.notification import EventRegistry
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

@admin_bp.route('/events', methods=['GET'])
@admin_required
def manage_events():
    """事件类型管理页面"""
    events = EventRegistry.query.order_by(EventRegistry.id).all()
    return render_template('admin/events.html', events=events)

@admin_bp.route('/events/add', methods=['POST'])
@admin_required
def add_event():
    """添加事件类型"""
    try:
        event_key = request.form.get('event_key')
        label_zh = request.form.get('label_zh')
        label_en = request.form.get('label_en')
        default_enabled = 'default_enabled' in request.form
        enabled = 'enabled' in request.form
        
        # 检查事件key是否已存在
        existing_event = EventRegistry.query.filter_by(event_key=event_key).first()
        if existing_event:
            flash(f'事件KEY "{event_key}" 已存在', 'danger')
            return redirect(url_for('admin.manage_events'))
        
        event = EventRegistry(
            event_key=event_key,
            label_zh=label_zh,
            label_en=label_en,
            default_enabled=default_enabled,
            enabled=enabled
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash(f'事件类型 "{label_zh}" 添加成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'添加事件失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_events'))

@admin_bp.route('/events/edit', methods=['POST'])
@admin_required
def edit_event():
    """编辑事件类型"""
    try:
        event_id = request.form.get('event_id')
        event_key = request.form.get('event_key')
        label_zh = request.form.get('label_zh')
        label_en = request.form.get('label_en')
        default_enabled = 'default_enabled' in request.form
        enabled = 'enabled' in request.form
        
        event = EventRegistry.query.get_or_404(event_id)
        
        # 更新事件信息
        event.label_zh = label_zh
        event.label_en = label_en
        event.default_enabled = default_enabled
        event.enabled = enabled
        
        db.session.commit()
        
        flash(f'事件类型 "{label_zh}" 更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'更新事件失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_events'))

@admin_bp.route('/events/delete', methods=['POST'])
@admin_required
def delete_event():
    """删除事件类型"""
    try:
        event_id = request.form.get('event_id')
        event = EventRegistry.query.get_or_404(event_id)
        
        # 删除所有相关的订阅记录
        from app.models.notification import UserEventSubscription
        UserEventSubscription.query.filter_by(event_id=event_id).delete()
        
        # 删除事件类型
        db.session.delete(event)
        db.session.commit()
        
        flash(f'事件类型 "{event.label_zh}" 已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除事件失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_events'))

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
                        setting_obj = type('SystemSetting', (), {
                            'id': f'setting_{key}',
                            '__class__': type('SystemSetting', (), {'__name__': 'SystemSetting'}),
                            '__tablename__': 'system_settings',
                            key: value
                        })()
                        
                        old_values = {key: old_value}
                        new_values = {key: value}
                        
                        if old_value != value:
                            ChangeTracker.log_update(setting_obj, old_values, new_values)
                    except Exception as track_err:
                        logger.warning(f"记录系统设置变更历史失败: {str(track_err)}")
                    
                    logger.info(f"用户 {current_user.username} 更新系统设置: {key}={value}")
            flash('系统设置已成功更新', 'success')
            return redirect(url_for('admin.system_settings'))
        except Exception as e:
            logger.error(f"更新系统设置时出错: {str(e)}", exc_info=True)
            flash(f'更新系统设置失败: {str(e)}', 'danger')
    # 准备所有系统设置数据
    settings_data = {}
    for key, default_config in DEFAULT_SETTINGS.items():
        # 获取当前设置值，如果不存在则使用默认值
        value = SystemSettings.get(key, default_config['value'])
        # 保证value为int类型
        try:
            value = int(value)
        except Exception:
            value = default_config['value']
        settings_data[key] = {
            'value': value,
            'description': default_config['description']
        }
    return render_template('admin/system_settings.html', settings=settings_data)

@admin_bp.route('/refresh_project_activity', methods=['POST'])
@login_required
@admin_required
def refresh_project_activity():
    """手动触发项目活跃度刷新"""
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 导入活跃度检查函数
        from app.utils.activity_tracker import check_project_activity
        from app import db
        from app.models.project import Project
        
        # 获取当前设置的活跃度阈值
        days_threshold = SystemSettings.get('project_activity_threshold', 7)
        
        # 执行活跃度检查
        active_projects, inactive_projects = check_project_activity(days_threshold=days_threshold)
        
        updated_count = 0
        # 更新活跃项目
        for project in active_projects:
            if not project.is_active:
                project.is_active = True
                db.session.add(project)
                updated_count += 1
        
        # 更新不活跃项目
        for project in inactive_projects:
            if project.is_active:
                project.is_active = False
                db.session.add(project)
                updated_count += 1
        
        # 提交更改
        db.session.commit()
        
        # 计算执行时间
        duration = round(time.time() - start_time, 2)
        
        # 记录日志
        logger.info(f"用户 {current_user.username} 手动刷新项目活跃度，处理 {len(active_projects) + len(inactive_projects)} 个项目，更新 {updated_count} 个状态，耗时 {duration}秒")
        
        # 返回结果
        return jsonify({
            'success': True,
            'message': f'项目活跃度刷新完成！共扫描 {len(active_projects) + len(inactive_projects)} 个项目，更新 {updated_count} 个项目状态。',
            'stats': {
                'active_count': len(active_projects),
                'inactive_count': len(inactive_projects),
                'updated_count': updated_count,
                'duration': duration
            }
        })
    except Exception as e:
        logger.error(f"刷新项目活跃度时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'刷新项目活跃度失败: {str(e)}'
        }), 500

@admin_bp.route('/refresh_customer_activity', methods=['POST'])
@login_required
@admin_required
def refresh_customer_activity():
    """手动触发客户活跃度刷新"""
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 导入活跃度检查函数
        from app.utils.activity_tracker import check_company_activity
        from app import db
        
        # 获取当前设置的活跃度阈值
        days_threshold = SystemSettings.get('customer_activity_threshold', 30)
        
        # 执行活跃度检查
        updated_count, active_count, inactive_count = check_company_activity(days_threshold=days_threshold)
        
        # 计算执行时间
        duration = round(time.time() - start_time, 2)
        
        # 记录日志
        logger.info(f"用户 {current_user.username} 手动刷新客户活跃度，活跃客户 {active_count} 个，不活跃客户 {inactive_count} 个，更新 {updated_count} 个状态，耗时 {duration}秒")
        
        # 返回结果
        return jsonify({
            'success': True,
            'message': f'客户活跃度刷新完成！活跃客户 {active_count} 个，不活跃客户 {inactive_count} 个，更新 {updated_count} 个客户状态。',
            'stats': {
                'active_count': active_count,
                'inactive_count': inactive_count,
                'updated_count': updated_count,
                'duration': duration
            }
        })
    except Exception as e:
        logger.error(f"刷新客户活跃度时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'刷新客户活跃度失败: {str(e)}'
        }), 500 