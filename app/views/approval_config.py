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
from app.models.approval import ApprovalProcessTemplate, ApprovalStep
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
        
        if not name or not object_type:
            flash('模板名称和业务类型不能为空', 'danger')
            return redirect(url_for('approval_config.create_template'))
        
        # 创建模板
        template = create_approval_template(
            name=name, 
            object_type=object_type,
            required_fields=required_fields
        )
        
        flash('审批流程模板创建成功', 'success')
        return redirect(url_for('approval_config.template_detail', template_id=template.id))
    
    # GET请求，渲染创建表单
    object_types = get_object_types()
    field_options = get_object_field_options()  # 获取所有字段选项
    
    return render_template(
        'approval_config/template_form.html',
        object_types=object_types,
        field_options=field_options,
        is_edit=False
    )


@approval_config_bp.route('/process/<int:template_id>')
@login_required
@admin_required
def template_detail(template_id):
    """审批流程模板详情页"""
    # 获取模板详情
    template = get_template_details(template_id)
    
    # 获取模板步骤
    steps = get_template_steps(template_id)
    
    # 获取所有用户，用于选择审批人
    users = get_all_users()
    
    # 检查模板是否正在使用
    in_use = check_template_in_use(template_id)
    
    return render_template(
        'approval_config/template_detail.html',
        template=template,
        steps=steps,
        users=users,
        in_use=in_use,
        get_object_field_options=get_object_field_options
    )


@approval_config_bp.route('/process/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_template(template_id):
    """编辑审批流程模板"""
    # 获取模板详情
    template = get_template_details(template_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        object_type = request.form.get('object_type')
        is_active = request.form.get('is_active') == 'on'
        required_fields = request.form.getlist('required_fields')
        
        if not name or not object_type:
            flash('模板名称和业务类型不能为空', 'danger')
            return redirect(url_for('approval_config.edit_template', template_id=template_id))
        
        # 检查模板是否正在使用
        in_use = check_template_in_use(template_id)
        if in_use and template.object_type != object_type:
            flash('该模板已经关联了审批实例，无法修改业务类型', 'danger')
            return redirect(url_for('approval_config.edit_template', template_id=template_id))
        
        # 更新模板
        update_approval_template(
            template_id,
            name=name,
            object_type=object_type,
            is_active=is_active,
            required_fields=required_fields
        )
        
        flash('审批流程模板更新成功', 'success')
        return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # GET请求，渲染编辑表单
    object_types = get_object_types()
    field_options = get_object_field_options(template.object_type)  # 获取特定业务对象的字段选项
    
    return render_template(
        'approval_config/template_form.html',
        template=template,
        object_types=object_types,
        field_options=field_options,
        is_edit=True
    )


@approval_config_bp.route('/process/<int:template_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_template(template_id):
    """删除审批流程模板"""
    result = delete_approval_template(template_id)
    
    if result:
        flash('审批流程模板删除成功', 'success')
    else:
        flash('该模板已关联审批实例，已将其禁用', 'warning')
    
    return redirect(url_for('approval_config.template_list'))


@approval_config_bp.route('/process/<int:template_id>/step/add', methods=['POST'])
@login_required
@admin_required
def add_step(template_id):
    """添加审批步骤"""
    step_name = request.form.get('step_name')
    approver_id = request.form.get('approver_id')
    send_email = request.form.get('send_email') == 'on'
    action_type = request.form.get('action_type')
    
    if not step_name or not approver_id:
        flash('步骤名称和审批人不能为空', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # 添加步骤
    step = add_approval_step(
        template_id,
        step_name,
        approver_id,
        send_email
    )
    
    # 如果设置了动作类型，更新步骤
    if step and action_type:
        step.action_type = action_type
        db.session.commit()
    
    if step:
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
    approver_id = request.form.get('approver_id')
    send_email = request.form.get('send_email') == 'on'
    action_type = request.form.get('action_type')
    
    if not step_name or not approver_id:
        flash('步骤名称和审批人不能为空', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # 更新步骤
    updated_step = update_approval_step(
        step_id,
        step_name=step_name,
        approver_id=approver_id,
        send_email=send_email
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