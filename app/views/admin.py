from app.models.notification import EventRegistry
from app.extensions import db

@admin.route('/events', methods=['GET'])
@admin_required
def manage_events():
    """事件类型管理页面"""
    events = EventRegistry.query.order_by(EventRegistry.id).all()
    return render_template('admin/events.html', events=events)

@admin.route('/events/add', methods=['POST'])
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

@admin.route('/events/edit', methods=['POST'])
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

@admin.route('/events/delete', methods=['POST'])
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