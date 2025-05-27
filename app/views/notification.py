from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user, login_required
from app.routes.notification import notification
from app.models.notification import EventRegistry, UserEventSubscription, SolutionManagerEmailSettings
from app.models.user import User
from app.extensions import db, csrf
from app.utils.access_control import get_viewable_data
import logging

logger = logging.getLogger(__name__)

@notification.route('/center', methods=['GET'])
@login_required
def center():
    """通知中心页面，用户管理其订阅的账户和事件"""
    # 获取当前用户可以查看的所有用户
    try:
        # 根据用户角色获取可以订阅的用户列表
        if current_user.role == 'admin':
            viewable_users = User.query.all()
        elif hasattr(current_user, 'is_department_manager') and current_user.is_department_manager and current_user.department:
            # 部门经理可以查看本部门用户
            viewable_users = User.query.filter_by(department=current_user.department).all()
        else:
            # 其他用户只能查看自己
            viewable_users = [current_user]
        
        # 获取所有启用的事件类型
        events = EventRegistry.query.filter_by(enabled=True).all()
        
        # 获取当前用户的所有订阅
        user_subscriptions = UserEventSubscription.query.filter_by(user_id=current_user.id).all()
        
        # 格式化订阅数据，便于前端使用
        subscription_map = {}
        for sub in user_subscriptions:
            if sub.target_user_id not in subscription_map:
                subscription_map[sub.target_user_id] = {}
            subscription_map[sub.target_user_id][sub.event.event_key] = sub.enabled
        
        # 检查是否为解决方案经理角色
        is_solution_manager = current_user.role == 'solution_manager'
        solution_manager_settings = None
        
        if is_solution_manager:
            # 获取或创建解决方案经理的邮件设置
            solution_manager_settings = SolutionManagerEmailSettings.query.filter_by(user_id=current_user.id).first()
            if not solution_manager_settings:
                solution_manager_settings = SolutionManagerEmailSettings(user_id=current_user.id)
                db.session.add(solution_manager_settings)
                db.session.commit()
        
        return render_template(
            'notification/center.html',
            viewable_users=viewable_users,
            events=events,
            subscription_map=subscription_map,
            is_solution_manager=is_solution_manager,
            solution_manager_settings=solution_manager_settings
        )
    except Exception as e:
        logger.error(f"加载通知中心出错: {str(e)}", exc_info=True)
        flash(f"加载通知中心出错: {str(e)}", "danger")
        return render_template('notification/center.html', viewable_users=[], events=[], subscription_map={}, is_solution_manager=False, solution_manager_settings=None)

@notification.route('/api/subscriptions', methods=['GET'])
@login_required
def get_subscriptions():
    """API接口：获取当前用户的订阅配置"""
    try:
        # 获取所有启用的事件
        events = EventRegistry.query.filter_by(enabled=True).all()
        event_dict = {e.id: e.event_key for e in events}
        
        # 获取当前用户的所有订阅
        subscriptions = UserEventSubscription.query.filter_by(user_id=current_user.id).all()
        
        # 组织成前端需要的格式
        result = []
        target_users = {}
        
        for sub in subscriptions:
            if sub.target_user_id not in target_users:
                target_users[sub.target_user_id] = {
                    "target_user_id": sub.target_user_id,
                    "target_user_name": sub.target_user.real_name or sub.target_user.username,
                    "events": {}
                }
            
            target_users[sub.target_user_id]["events"][event_dict[sub.event_id]] = sub.enabled
        
        result = list(target_users.values())
        
        return jsonify({"success": True, "subscriptions": result})
    
    except Exception as e:
        logger.error(f"获取订阅失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"获取订阅失败: {str(e)}"}), 500

@notification.route('/api/subscriptions', methods=['POST'])
@login_required
@csrf.exempt  # API接口不需要CSRF保护，但生产环境应该使用Token验证
def save_subscriptions():
    """API接口：保存用户的订阅配置"""
    try:
        data = request.get_json()
        
        if not data or 'subscriptions' not in data:
            return jsonify({"success": False, "message": "数据格式错误"}), 400
        
        # 获取所有事件的ID映射
        events = EventRegistry.query.filter_by(enabled=True).all()
        event_keys = {e.event_key: e.id for e in events}
        
        # 获取用户可见的账户
        if current_user.role == 'admin':
            viewable_users = User.query.all()
        elif hasattr(current_user, 'is_department_manager') and current_user.is_department_manager and current_user.department:
            # 部门经理可以查看本部门用户
            viewable_users = User.query.filter_by(department=current_user.department).all()
        else:
            # 其他用户只能查看自己
            viewable_users = [current_user]
        
        viewable_user_ids = [u.id for u in viewable_users]
        
        # 删除当前用户的所有订阅
        UserEventSubscription.query.filter_by(user_id=current_user.id).delete()
        
        # 添加新的订阅
        for sub in data['subscriptions']:
            target_user_id = sub.get('target_user_id')
            events_dict = sub.get('events', {})
            
            # 验证目标用户ID是否在可见范围内
            if target_user_id not in viewable_user_ids:
                logger.warning(f"用户 {current_user.id} 尝试订阅无权限查看的用户 {target_user_id}")
                continue
            
            # 添加新的订阅
            for event_key, enabled in events_dict.items():
                if event_key in event_keys:
                    subscription = UserEventSubscription(
                        user_id=current_user.id,
                        target_user_id=target_user_id,
                        event_id=event_keys[event_key],
                        enabled=enabled
                    )
                    db.session.add(subscription)
        
        db.session.commit()
        flash('订阅设置已保存', 'success')
        return jsonify({"success": True, "message": "订阅设置已保存"})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存订阅失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"保存订阅失败: {str(e)}"}), 500

@notification.route('/restore-defaults', methods=['POST'])
@login_required
def restore_default_subscriptions():
    """恢复默认订阅设置"""
    try:
        # 获取所有启用的事件
        events = EventRegistry.query.filter_by(enabled=True, default_enabled=True).all()
        
        # 删除当前用户的所有订阅
        UserEventSubscription.query.filter_by(user_id=current_user.id).delete()
        
        # 添加默认订阅 - 仅订阅自己的所有事件
        for event in events:
            subscription = UserEventSubscription(
                user_id=current_user.id,
                target_user_id=current_user.id,  # 默认只订阅自己
                event_id=event.id,
                enabled=True
            )
            db.session.add(subscription)
        
        db.session.commit()
        flash('已恢复默认订阅设置', 'success')
        return redirect(url_for('notification.center'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"恢复默认订阅失败: {str(e)}", exc_info=True)
        flash(f'恢复默认订阅失败: {str(e)}', 'danger')
        return redirect(url_for('notification.center'))

@notification.route('/api/solution-manager-settings', methods=['GET'])
@login_required
def get_solution_manager_settings():
    """API接口：获取解决方案经理的邮件设置"""
    try:
        if current_user.role != 'solution_manager':
            return jsonify({"success": False, "message": "权限不足"}), 403
        
        settings = SolutionManagerEmailSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = SolutionManagerEmailSettings(user_id=current_user.id)
            db.session.add(settings)
            db.session.commit()
        
        return jsonify({
            "success": True,
            "settings": {
                "quotation_created": settings.quotation_created,
                "quotation_updated": settings.quotation_updated,
                "project_created": settings.project_created,
                "project_stage_changed": settings.project_stage_changed
            }
        })
    
    except Exception as e:
        logger.error(f"获取解决方案经理设置失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"获取设置失败: {str(e)}"}), 500

@notification.route('/api/solution-manager-settings', methods=['POST'])
@login_required
@csrf.exempt
def save_solution_manager_settings():
    """API接口：保存解决方案经理的邮件设置"""
    try:
        if current_user.role != 'solution_manager':
            return jsonify({"success": False, "message": "权限不足"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "数据格式错误"}), 400
        
        settings = SolutionManagerEmailSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = SolutionManagerEmailSettings(user_id=current_user.id)
            db.session.add(settings)
        
        # 更新设置
        settings.quotation_created = data.get('quotation_created', True)
        settings.quotation_updated = data.get('quotation_updated', True)
        settings.project_created = data.get('project_created', True)
        settings.project_stage_changed = data.get('project_stage_changed', True)
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "设置已保存"})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存解决方案经理设置失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"保存设置失败: {str(e)}"}), 500 