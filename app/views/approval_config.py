from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.permissions import admin_required
from app.helpers.approval_helpers import (
    get_approval_templates,
    get_template_details,
    get_template_steps,
    create_approval_template,
    update_approval_template,
    delete_approval_template,
    add_approval_step,
    update_approval_step,
    delete_approval_step,
    reorder_approval_steps,
    get_all_users,
    get_object_types,
    check_template_in_use,
    get_object_field_options
)
from app.models.approval import ApprovalProcessTemplate, ApprovalStep, ApprovalInstance, ApprovalRecord, ApprovalStatus
from app.models.user import User
from app import db, csrf
from flask import current_app

# 创建Blueprint
approval_config_bp = Blueprint('approval_config', __name__, url_prefix='/admin/approval')


@approval_config_bp.route('/process')
@login_required
@admin_required
def template_list():
    """审批流程模板列表页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    object_type = request.args.get('object_type')
    
    # 获取模板列表
    templates = get_approval_templates(
        page=page, 
        per_page=per_page,
        object_type=object_type
    )
    
    # 获取业务对象类型列表
    object_types = get_object_types()
    
    return render_template(
        'approval_config/template_list.html',
        templates=templates,
        object_types=object_types,
        current_object_type=object_type
    )


@approval_config_bp.route('/process/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_template():
    """创建审批流程模板"""
    if request.method == 'POST':
        name = request.form.get('name')
        object_type = request.form.get('object_type')
        required_fields = request.form.getlist('required_fields')
        lock_object_on_start = request.form.get('lock_object_on_start') == 'on'
        lock_reason = request.form.get('lock_reason', '审批流程进行中，暂时锁定编辑')
        
        if not name or not object_type:
            flash('模板名称和业务对象类型不能为空', 'danger')
            return redirect(url_for('approval_config.create_template'))
        
        # 创建模板
        template = create_approval_template(
            name=name,
            object_type=object_type,
            creator_id=current_user.id,
            required_fields=required_fields,
            lock_object_on_start=lock_object_on_start,
            lock_reason=lock_reason
        )
        
        if template:
            flash('审批流程模板创建成功', 'success')
            return redirect(url_for('approval_config.template_detail', template_id=template.id))
        else:
            flash('创建审批流程模板失败', 'danger')
    
    # GET请求，显示创建表单
    object_types = get_object_types()
    return render_template('approval_config/template_form.html', 
                         object_types=object_types, 
                         is_edit=False)


@approval_config_bp.route('/process/<int:template_id>')
@login_required
@admin_required
def template_detail(template_id):
    """查看审批流程模板详情"""
    # 获取模板详情
    template = get_template_details(template_id)
    
    # 获取模板步骤
    steps = get_template_steps(template_id)
    
    # 获取所有用户，用于选择审批人
    users = get_all_users()
    
    # 统计实例状态
    all_instances = ApprovalInstance.query.filter_by(process_id=template_id).all()
    pending_instances = [i for i in all_instances if i.status == ApprovalStatus.PENDING]
    completed_instances = [i for i in all_instances if i.status != ApprovalStatus.PENDING]
    
    # 检查是否可以修改（只有进行中的实例才禁止修改）
    can_modify = len(pending_instances) == 0
    
    # 保持向后兼容的 in_use 变量（严格模式）
    in_use = check_template_in_use(template_id, strict_mode=True)
    
    # 获取关联的审批实例（最近的10个）
    approval_instances = ApprovalInstance.query.filter_by(
        process_id=template_id
    ).options(
        db.joinedload(ApprovalInstance.creator),
        db.joinedload(ApprovalInstance.process)
    ).order_by(ApprovalInstance.started_at.desc()).limit(10).all()
    
    return render_template(
        'approval_config/template_detail.html',
        template=template,
        steps=steps,
        users=users,
        in_use=in_use,  # 保持向后兼容
        can_modify=can_modify,  # 新增：是否可以修改
        pending_instances_count=len(pending_instances),  # 新增：进行中实例数量
        completed_instances_count=len(completed_instances),  # 新增：已完成实例数量
        approval_instances=approval_instances,
        get_object_field_options=get_object_field_options
    )


@approval_config_bp.route('/process/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_template(template_id):
    """编辑审批流程模板"""
    template = ApprovalProcessTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        object_type = request.form.get('object_type')
        is_active = request.form.get('is_active') == 'on'
        required_fields = request.form.getlist('required_fields')
        lock_object_on_start = request.form.get('lock_object_on_start') == 'on'
        lock_reason = request.form.get('lock_reason', '审批流程进行中，暂时锁定编辑')
        
        if not name:
            flash('模板名称不能为空', 'danger')
            return redirect(url_for('approval_config.edit_template', template_id=template_id))
        
        # 更新模板
        updated_template = update_approval_template(
            template_id=template_id,
            name=name,
            object_type=object_type,
            is_active=is_active,
            required_fields=required_fields,
            lock_object_on_start=lock_object_on_start,
            lock_reason=lock_reason
        )
        
        if updated_template:
            flash('审批流程模板更新成功', 'success')
            return redirect(url_for('approval_config.template_detail', template_id=template_id))
        else:
            flash('更新审批流程模板失败', 'danger')
    
    # GET请求，显示编辑表单
    object_types = get_object_types()
    in_use = check_template_in_use(template_id)
    
    return render_template('approval_config/template_form.html',
                         template=template,
                         object_types=object_types,
                         in_use=in_use,
                         is_edit=True)


@approval_config_bp.route('/process/<int:template_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_template(template_id):
    """删除审批流程模板"""
    result = delete_approval_template(template_id)
    
    if result['success']:
        flash('审批流程模板删除成功', 'success')
    else:
        # 如果是因为有关联实例而被禁用，显示详细信息
        if result['instances']:
            flash(result['message'], 'warning')
            current_app.logger.info(f"模板 {template_id} 因有关联实例被禁用，实例数量: {len(result['instances'])}")
        else:
            flash(result['message'], 'danger')
    
    return redirect(url_for('approval_config.template_list'))


@approval_config_bp.route('/process/<int:template_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_template(template_id):
    """启用/禁用审批流程模板"""
    template = ApprovalProcessTemplate.query.get_or_404(template_id)
    
    # 获取提交的状态值
    is_active = request.form.get('is_active', 'true').lower() == 'true'
    
    try:
        template.is_active = is_active
        db.session.commit()
        
        action = '启用' if is_active else '禁用'
        flash(f'审批流程模板"{template.name}"已{action}', 'success')
        current_app.logger.info(f"用户 {current_user.username} {action}了审批模板 {template.name} (ID: {template_id})")
    except Exception as e:
        db.session.rollback()
        flash(f'操作失败: {str(e)}', 'danger')
        current_app.logger.error(f"启用/禁用审批模板失败: {str(e)}")
    
    return redirect(url_for('approval_config.template_list'))


@approval_config_bp.route('/step/add', methods=['POST'])
@login_required
@admin_required
def add_step():
    """添加审批步骤"""
    template_id = request.form.get('template_id', type=int)
    step_name = request.form.get('step_name')
    approver_id = request.form.get('approver_id', type=int)
    send_email = request.form.get('send_email') == 'on'
    action_type = request.form.get('action_type')
    
    # 新增字段
    editable_fields = request.form.getlist('editable_fields')
    cc_users = request.form.getlist('cc_users')
    cc_enabled = request.form.get('cc_enabled') == 'on'
    
    # 如果是授权编号动作，则不需要指定审批人，将使用动态分配
    if action_type == 'authorization':
        approver_id = None
    
    if not template_id or not step_name or (not approver_id and action_type != 'authorization'):
        flash('模板ID、步骤名称不能为空，且非授权编号动作需要指定审批人', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # 添加步骤
    step = add_approval_step(
        template_id=template_id,
        step_name=step_name,
        approver_id=approver_id,
        send_email=send_email,
        editable_fields=editable_fields,
        cc_users=[int(user_id) for user_id in cc_users if user_id.isdigit()],
        cc_enabled=cc_enabled
    )
    
    # 如果添加成功且设置了动作类型，更新动作类型
    if step:
        step.action_type = action_type if action_type else None
        db.session.commit()
        flash('审批步骤添加成功', 'success')
    else:
        flash('添加审批步骤失败', 'danger')
    
    return redirect(url_for('approval_config.template_detail', template_id=template_id))


@approval_config_bp.route('/step/<int:step_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_step(step_id):
    """编辑审批步骤"""
    step = ApprovalStep.query.get_or_404(step_id)
    template_id = step.process_id
    
    step_name = request.form.get('step_name')
    approver_id = request.form.get('approver_id', type=int)
    send_email = request.form.get('send_email') == 'on'
    action_type = request.form.get('action_type')
    
    # 新增字段
    editable_fields = request.form.getlist('editable_fields')
    cc_users = request.form.getlist('cc_users')
    cc_enabled = request.form.get('cc_enabled') == 'on'
    
    # 如果是授权编号动作，则不需要指定审批人，将使用动态分配
    if action_type == 'authorization':
        approver_id = None
    
    if not step_name or (not approver_id and action_type != 'authorization'):
        flash('步骤名称不能为空，且非授权编号动作需要指定审批人', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # 更新步骤
    updated_step = update_approval_step(
        step_id,
        step_name=step_name,
        approver_id=approver_id,
        send_email=send_email,
        editable_fields=editable_fields,
        cc_users=[int(user_id) for user_id in cc_users if user_id.isdigit()],
        cc_enabled=cc_enabled,
        update_approver=True  # 明确指定要更新审批人
    )
    
    # 如果更新成功且设置了动作类型，更新动作类型
    if updated_step:
        updated_step.action_type = action_type if action_type else None
        db.session.commit()
        flash('审批步骤更新成功', 'success')
    else:
        flash('更新审批步骤失败', 'danger')
    
    return redirect(url_for('approval_config.template_detail', template_id=template_id))


@approval_config_bp.route('/step/<int:step_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_step(step_id):
    """删除审批步骤"""
    step = ApprovalStep.query.get_or_404(step_id)
    template_id = step.process_id
    
    # 删除步骤
    result = delete_approval_step(step_id)
    
    if result:
        flash('审批步骤删除成功', 'success')
    else:
        flash('删除审批步骤失败', 'danger')
    
    return redirect(url_for('approval_config.template_detail', template_id=template_id))


@approval_config_bp.route('/process/<int:template_id>/steps/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_steps(template_id):
    """重新排序审批步骤"""
    # 获取步骤顺序映射
    data = request.json
    if not data or 'steps' not in data:
        return jsonify({'success': False, 'message': '无效的请求数据'})
    
    # 构建步骤ID到顺序的映射
    step_order_map = {}
    for i, step_id in enumerate(data['steps'], 1):
        step_order_map[int(step_id)] = i
    
    # 重新排序步骤
    result = reorder_approval_steps(template_id, step_order_map)
    
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '重新排序步骤失败'})


@approval_config_bp.route('/field-options/<string:object_type>', methods=['GET'])
# 临时禁用登录和管理员权限检查，仅用于测试
# @login_required
# @admin_required
@csrf.exempt  # 豁免CSRF保护，允许Ajax直接访问
def get_field_options(object_type):
    """API端点：获取业务对象字段选项
    
    Args:
        object_type: 业务对象类型
    
    Returns:
        JSON格式的字段选项列表
    """
    current_app.logger.info(f"===== 获取字段选项API被调用 - 对象类型: {object_type} =====")
    
    try:
        # 添加CORS头，允许跨域访问（仅用于测试）
        if object_type not in ('project', 'quotation', 'customer'):
            current_app.logger.warning(f"无效的业务对象类型: {object_type}")
            response = jsonify({'success': False, 'message': '无效的业务对象类型'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        field_options = get_object_field_options(object_type)
        fields = [{'name': field[0], 'display_name': field[1]} for field in field_options]
        
        current_app.logger.info(f"字段选项获取成功 - 对象类型: {object_type}, 字段数量: {len(fields)}")
        current_app.logger.debug(f"字段选项内容: {fields}")
        
        response = jsonify({
            'success': True,
            'object_type': object_type,
            'fields': fields
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        current_app.logger.error(f"获取字段选项出错: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        response = jsonify({
            'success': False,
            'message': f'获取字段选项出错: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500 