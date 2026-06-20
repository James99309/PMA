from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import json
from app.permissions import admin_required, permission_required
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
    get_object_field_options,
    get_step_branch_conditions_count,
    get_step_branch_field_from_step_data,
    should_lock_branch_field
)
from app.helpers.approval_branch_helpers_new import (
    handle_branch_condition_add,
    handle_branch_condition_edit,
    handle_branch_condition_delete,
    validate_branch_condition_data,
    get_branch_condition_summary
)
from app.helpers.approval_step_helpers import (
    validate_step_data,
    process_approver_data,
    process_branch_condition_data,
    process_additional_fields,
    validate_approver_configuration,
    log_step_operation,
    create_step_response,
    get_default_step_params,
    get_edit_mode_info,
    handle_branch_edit_mode,
    handle_regular_step_edit
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
    is_active = request.args.get('is_active')
    creator_id = request.args.get('creator_id')
    search = request.args.get('search', '').strip()

    # 获取模板列表 - 支持筛选
    templates = get_approval_templates(
        page=page,
        per_page=per_page,
        object_type=object_type,
        is_active=True if is_active == 'true' else False if is_active == 'false' else None,
        search=search,
        creator_id=creator_id
    )

    # 获取业务对象类型列表
    object_types = get_object_types()

    # 查询实际数据生成筛选选项
    from app.models.user import User
    from sqlalchemy import distinct

    # 获取所有实际创建过模板的用户
    creator_ids = db.session.query(distinct(ApprovalProcessTemplate.created_by)).all()
    creator_ids = [c[0] for c in creator_ids if c[0]]
    creators = User.query.filter(User.id.in_(creator_ids)).order_by(User.real_name, User.username).all() if creator_ids else []

    # 获取实际存在的业务类型
    actual_object_types = db.session.query(distinct(ApprovalProcessTemplate.object_type)).all()
    actual_object_types = [t[0] for t in actual_object_types if t[0]]
    # 筛选出实际存在的业务类型选项
    actual_object_type_options = [(code, name) for code, name in object_types if code in actual_object_types]

    # 配置标准化的筛选搜索
    filter_config = {
        'action_url': url_for('approval_config.template_list'),
        'reset_url': url_for('approval_config.template_list'),
        'form_id': 'templateFilterForm',
        'auto_submit': True,
        'dynamic_reset_button': True,
        'search_field': {
            'name': 'search',
            'label': '搜索模板',
            'placeholder': '搜索模板名称...',
            'value': search
        },
        'filter_fields': [
            {
                'name': 'object_type',
                'label': '业务类型',
                'all_option_text': '全部业务类型',
                'current_value': object_type or '',
                'auto_submit': True,
                'options': [
                    {'value': code, 'label': name, 'translate': False} for code, name in actual_object_type_options
                ],
                'col_width': 'col-md-3'
            },
            {
                'name': 'is_active',
                'label': '模板状态',
                'all_option_text': '全部状态',
                'current_value': is_active or '',
                'auto_submit': True,
                'options': [
                    {'value': 'true', 'label': '活跃', 'translate': False},
                    {'value': 'false', 'label': '非活跃', 'translate': False}
                ],
                'col_width': 'col-md-3'
            },
            {
                'name': 'creator_id',
                'label': '创建人',
                'all_option_text': '全部创建人',
                'current_value': creator_id or '',
                'auto_submit': True,
                'options': [
                    {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
                    for user in creators
                ],
                'col_width': 'col-md-3'
            }
        ],
        'search_button_text': '搜索',
        'reset_button_text': '重置'
    }

    # 配置标准化的数据列表
    list_config = {
        'module_name': 'approval_template',
        'title': None,  # 页面级标题由模板控制，此处不显示
        'ajax_mode': False,
        'filter': filter_config,
        'table': {
            'columns': [
                {'key': 'name', 'field': 'name', 'label': '模板名称', 'sortable': True, 'width': '20%', 'type': 'link', 'url_template': '/admin/approval/process/{id}/edit'},
                {'key': 'object_type', 'field': 'object_type', 'label': '业务类型', 'sortable': True, 'width': '15%', 'render': 'get_object_type_display'},
                {'key': 'is_active', 'field': 'is_active', 'label': '状态', 'sortable': False, 'width': '10%', 'render': 'render_status_badge'},
                {'key': 'creator', 'field': 'creator', 'label': '创建人', 'sortable': True, 'width': '15%', 'render': 'render_owner'},
                {'key': 'created_at', 'field': 'created_at', 'label': '创建时间', 'sortable': True, 'width': '20%'},
                {'key': 'actions', 'type': 'actions', 'label': '操作', 'sortable': False, 'width': '20%'}
            ],
            'enhanced_striping': True,
            'show_header': True
        },
        'pagination': templates if hasattr(templates, 'pages') else None
    }

    return render_template(
        'approval_config/template_list.html',
        templates=templates,
        object_types=object_types,
        current_object_type=object_type,
        filter_config=filter_config,
        list_config=list_config,
        can_modify=True  # 管理员权限页面默认可修改
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
            flash('创建审批流程模板失败，请重试', 'danger')
            return redirect(url_for('approval_config.create_template'))
    
    # GET请求 - 显示创建模板的表单页面
    try:
        # 获取业务对象类型列表
        object_types = get_object_types()
        
        # 渲染创建模板的表单页面
        return render_template('approval_config/template_form.html',
                             title='创建审批流程模板',
                             object_types=object_types)
    except Exception as e:
        current_app.logger.error(f"显示创建模板页面时出错: {e}")
        flash('加载创建模板页面失败，请重试', 'danger')
        return redirect(url_for('approval_config.list_templates'))


@approval_config_bp.route('/api/get-value-mapping')
@login_required
@admin_required
def get_value_mapping():
    """获取字段值的中文映射API"""
    field_name = request.args.get('field')
    field_value = request.args.get('value')
    
    if not field_name or not field_value:
        return jsonify({
            'success': False,
            'message': '缺少必要参数 field 或 value'
        }), 400
    
    try:
        from app.utils.field_value_helper import get_project_type_mapping, get_project_stage_mapping, get_report_source_mapping
        from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS, PROJECT_STAGE_LABELS, REPORT_SOURCE_LABELS
        
        # 根据字段名选择对应的映射函数
        mapping_functions = {
            'project_type': get_project_type_mapping,
            'current_stage': get_project_stage_mapping, 
            'report_source': get_report_source_mapping
        }
        
        mapped_value = field_value  # 默认使用原值
        
        if field_name in mapping_functions:
            mapping_dict = mapping_functions[field_name]()
            if field_value in mapping_dict:
                mapped_value = mapping_dict[field_value]
                current_app.logger.info(f"字段值映射成功: {field_name}.{field_value} → {mapped_value}")
            else:
                current_app.logger.info(f"未找到映射: {field_name}.{field_value}")
        else:
            current_app.logger.info(f"不支持的字段映射: {field_name}")
        
        return jsonify({
            'success': True,
            'field': field_name,
            'original_value': field_value,
            'mapped_value': mapped_value
        })
        
    except Exception as e:
        current_app.logger.error(f"获取字段值映射失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取字段值映射失败: {str(e)}'
        }), 500


@approval_config_bp.route('/api/get-field-values')
@login_required
@admin_required
def get_field_values():
    """获取指定字段的可选值API"""
    object_type = request.args.get('object_type')
    field_name = request.args.get('field_name')
    
    if not object_type or not field_name:
        return jsonify({
            'success': False,
            'message': '缺少必要参数 object_type 或 field_name'
        }), 400
    
    try:
        from app.utils.field_value_helper import get_field_available_values
        
        # 获取字段可选值
        values = get_field_available_values(object_type, field_name)
        
        return jsonify({
            'success': True,
            'field_name': field_name,
            'object_type': object_type,
            'values': values
        })
        
    except Exception as e:
        current_app.logger.error(f"获取字段值失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取字段值失败: {str(e)}'
        }), 500


@approval_config_bp.route('/process/<int:template_id>')
@login_required
@admin_required
def template_detail(template_id):
    """查看审批流程模板详情"""
    # 获取模板详情
    template = get_template_details(template_id)
    
    # 获取模板步骤
    steps = get_template_steps(template_id)
    
    # 为分支步骤添加新表的条件数据
    from app.helpers.approval_branch_helpers_new import get_step_conditions_legacy_format
    for step in steps:
        if step.step_type == 'branch':
            # 获取新表的条件数据，但保持与旧格式兼容
            step.new_table_conditions = get_step_conditions_legacy_format(step)
    
    # 获取所有用户，用于选择审批人
    users = get_all_users()
    
    # 统计实例状态
    all_instances = ApprovalInstance.query.filter_by(process_id=template_id).all()
    pending_instances = [i for i in all_instances if i.status == ApprovalStatus.PENDING]
    completed_instances = [i for i in all_instances if i.status != ApprovalStatus.PENDING]
    
    # 🔥 优化权限逻辑：基于快照机制分析的结论
    # 快照机制已完全保护运行中的审批实例，允许结构性修改
    # 结构性修改（删除步骤、重新排序）：允许，快照机制提供完全保护
    can_modify_structure = True
    # 内容编辑（修改步骤属性）：总是允许，因为使用快照机制
    can_edit_content = True
    # 为了向后兼容，保持can_modify变量，设置为True允许所有修改
    can_modify = True
    
    # 仅对危险操作（删除整个模板、禁用模板）保持限制
    can_delete_template = len(pending_instances) == 0
    
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
        can_modify=can_modify,  # 优化：现在总是True，允许所有修改
        can_modify_structure=can_modify_structure,  # 优化：现在总是True，快照机制保护
        can_edit_content=can_edit_content,  # 内容编辑权限（总是True）
        can_delete_template=can_delete_template,  # 新增：删除模板权限（有进行中实例时禁止）
        pending_instances_count=len(pending_instances),  # 进行中实例数量
        completed_instances_count=len(completed_instances),  # 已完成实例数量
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
    step_type = request.form.get('step_type', 'normal')
    inherit_from_step = request.form.get('inherit_from_step', type=int)
    
    # 验证基本步骤数据
    is_valid, error_message, step_data = validate_step_data(request.form, step_type)
    if not is_valid:
        return create_step_response(False, error_message, step_data.get('template_id') if step_data else None, 'danger')
    
    template_id = step_data['template_id']
    log_step_operation('add', step_data, f"step_type: {step_type}")
    
    # 处理审批人数据
    approver_data = process_approver_data(request.form, step_type)
    
    # 处理分支条件（如果是分支步骤）
    branch_condition = None
    branch_group_id = None
    if step_type == 'branch':
        branch_result = process_branch_condition_data(request.form, template_id, inherit_from_step)
        if 'error' in branch_result:
            return create_step_response(False, branch_result['error'], template_id, 'danger')
        
        branch_condition = branch_result.get('branch_condition')
        branch_group_id = branch_result.get('branch_group_id')
        approver_data['action_type'] = branch_result.get('action_type')
    
    # 处理附加字段
    additional_fields = process_additional_fields(request.form)
    
    # 验证审批人配置
    is_valid, error_message = validate_approver_configuration(
        approver_data['approver_type'], 
        approver_data['approver_id'], 
        step_type, 
        approver_data['action_type']
    )
    if not is_valid:
        return create_step_response(False, error_message, template_id, 'danger')
    
    # 获取默认参数并添加步骤
    default_params = get_default_step_params()
    
    step = add_approval_step(
        template_id=template_id,
        step_name=step_data['step_name'],
        approver_id=approver_data['approver_id'],
        send_email=additional_fields['send_email'],
        editable_fields=additional_fields['editable_fields'],
        cc_users=additional_fields['cc_users'],
        cc_enabled=additional_fields['cc_enabled'],
        approver_type=approver_data['approver_type'],
        step_type=step_type,
        branch_condition=branch_condition,
        branch_group_id=branch_group_id,
        branch_level=default_params['branch_level'],
        parent_step_id=default_params['parent_step_id'],
        is_parallel=default_params['is_parallel'],
        execution_condition=additional_fields.get('execution_condition')
    )
    
    # 更新动作类型并提交
    if step:
        step.action_type = approver_data['action_type'] if approver_data['action_type'] else None
        # submitter_designate 步骤:保存可选范围(designate_pool)
        # PMA 用户/企业模型用的是 User.company_name 字符串,不是 department_id
        if approver_data['approver_type'] == 'submitter_designate':
            roles = request.form.getlist('designate_pool_roles') or []
            companies = request.form.getlist('designate_pool_companies') or []
            step.designate_pool = {'roles': roles, 'companies': companies}
        else:
            step.designate_pool = None
        db.session.commit()
        
        # 如果是分支步骤，使用统一服务层创建分支条件
        if step_type == 'branch':
            from app.services.branch_condition_service import BranchConditionService
            
            # 使用统一服务层创建分支条件
            result = BranchConditionService.create_branch_step_conditions(step, request.form)
            if not result['success']:
                # 如果分支条件创建失败，需要回滚步骤创建
                db.session.delete(step)
                db.session.commit()
                return create_step_response(False, f"创建分支条件失败: {result['error']}", template_id, 'danger')
        
        return create_step_response(True, '审批步骤添加成功', template_id)
    else:
        return create_step_response(False, '添加审批步骤失败', template_id, 'danger')


@approval_config_bp.route('/step/<int:step_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_step(step_id):
    """编辑审批步骤"""
    step = ApprovalStep.query.get_or_404(step_id)
    template_id = step.process_id
    
    # 获取编辑模式信息
    edit_mode = get_edit_mode_info(request.form)
    
    current_app.logger.info(f"编辑模式检查 - {edit_mode}")
    current_app.logger.info(f"🔍 edit_step收到的所有表单数据: {dict(request.form)}")
    
    # 处理分支条件相关操作
    if edit_mode['action'] == 'delete_branch_condition':
        current_app.logger.info(f"🗑️ 进入删除分支条件处理逻辑 - 步骤ID: {step_id}")
        api_mode = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        return handle_branch_condition_delete(step, request.form, api_mode=api_mode)
    
    if edit_mode['is_branch_condition_add']:
        api_mode = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        return handle_branch_condition_add(step, request.form, api_mode=api_mode)
    
    if edit_mode['is_branch_condition_edit']:
        api_mode = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        return handle_branch_condition_edit(step, request.form, api_mode=api_mode)
    
    # 处理分支编辑模式
    if edit_mode['is_branch_edit'] and edit_mode['branch_type']:
        return handle_branch_edit_mode(step, request.form)
    
    # 处理常规步骤编辑
    return handle_regular_step_edit(step, request.form)


@approval_config_bp.route('/step/<int:step_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_step(step_id):
    """删除审批步骤"""
    step = ApprovalStep.query.get_or_404(step_id)
    template_id = step.process_id
    
    # 删除步骤 - 基于快照机制保护，允许强制删除
    result = delete_approval_step(step_id, force=True)
    
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


@approval_config_bp.route('/template/<int:template_id>/field-options', methods=['GET'])
@login_required
@admin_required
def get_template_field_options(template_id):
    """API端点：获取指定模板的字段选项
    
    Args:
        template_id: 模板ID
    
    Returns:
        JSON格式的字段选项数据
    """
    current_app.logger.info(f"===== 获取模板字段选项API被调用 - 模板ID: {template_id} =====")
    
    try:
        # 获取模板信息
        template = ApprovalProcessTemplate.query.get(template_id)
        if not template:
            current_app.logger.warning(f"模板不存在: {template_id}")
            return jsonify({
                'success': False,
                'message': '模板不存在'
            }), 404
        
        # 获取字段选项
        field_options = get_object_field_options(template.object_type)
        
        current_app.logger.info(f"模板字段选项获取成功 - 模板ID: {template_id}, 对象类型: {template.object_type}")
        current_app.logger.debug(f"字段选项数据: {field_options}")
        
        return jsonify({
            'success': True,
            'template_id': template_id,
            'object_type': template.object_type,
            'field_options': field_options
        })
        
    except Exception as e:
        current_app.logger.error(f"获取模板字段选项出错: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'message': f'获取模板字段选项出错: {str(e)}'
        }), 500


@approval_config_bp.route('/field-values', methods=['GET'])
@login_required
@admin_required
def get_field_distinct_values_api():
    """获取字段的所有可能值（去重后）"""
    try:
        template_id = request.args.get('template_id')
        field_name = request.args.get('field_name')
        
        current_app.logger.info(f"获取字段值 - 模板ID: {template_id}, 字段名: {field_name}")
        
        if not template_id or not field_name:
            response = jsonify({
                'success': False,
                'message': '缺少必要参数'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # 获取模板信息
        template = ApprovalProcessTemplate.query.get(template_id)
        if not template:
            response = jsonify({
                'success': False,
                'message': '模板不存在'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        # 根据对象类型和字段名获取字段值
        values = get_field_distinct_values(template.object_type, field_name)
        
        current_app.logger.info(f"字段值获取成功 - 对象类型: {template.object_type}, 字段: {field_name}, 值数量: {len(values)}")
        current_app.logger.debug(f"字段值内容: {values[:10]}...")  # 只记录前10个值
        
        response = jsonify({
            'success': True,
            'object_type': template.object_type,
            'field_name': field_name,
            'values': values
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        current_app.logger.error(f"获取字段值失败: {str(e)}")
        
        response = jsonify({
            'success': False,
            'message': f'获取字段值失败: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


def get_field_distinct_values(object_type, field_name):
    """获取指定对象类型和字段的去重值列表"""
    try:
        values = []
        
        # 对于特定的枚举字段，优先使用标准映射
        if field_name == 'project_type' or field_name == 'project.project_type':
            from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS
            from app.utils.i18n import get_current_language
            try:
                lang = get_current_language()
            except:
                lang = 'zh'
            values = [v[lang] for v in PROJECT_TYPE_LABELS.values()]
        elif field_name == 'project_stage':
            from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS
            from app.utils.i18n import get_current_language
            try:
                lang = get_current_language()
            except:
                lang = 'zh'
            values = [v[lang] for v in PROJECT_STAGE_LABELS.values()]
        elif field_name == 'currency':
            from app.utils.dictionary_helpers import get_currency_type_options
            values = [name for code, name in get_currency_type_options()]
        elif field_name in ['status', 'approval_status']:
            from app.utils.dictionary_helpers import APPROVAL_STATUS_LABELS
            from app.utils.i18n import get_current_language
            try:
                lang = get_current_language()
            except:
                lang = 'zh'
            values = [v[lang] for v in APPROVAL_STATUS_LABELS.values()]
        else:
            # 根据对象类型查询对应的数据表
            if object_type == 'quotation':
                from app.models.quotation import Quotation, QuotationItem
                if hasattr(Quotation, field_name):
                    # 主表字段
                    query_values = db.session.query(getattr(Quotation, field_name)).distinct().filter(
                        getattr(Quotation, field_name).isnot(None),
                        getattr(Quotation, field_name) != ''
                    ).limit(50).all()  # 限制结果数量
                    values = [str(v[0]) for v in query_values if v[0] is not None]
                elif hasattr(QuotationItem, field_name):
                    # 明细表字段
                    query_values = db.session.query(getattr(QuotationItem, field_name)).distinct().filter(
                        getattr(QuotationItem, field_name).isnot(None),
                        getattr(QuotationItem, field_name) != ''
                    ).limit(50).all()
                    values = [str(v[0]) for v in query_values if v[0] is not None]
                    
            elif object_type == 'pricing_order':
                from app.models.pricing_order import PricingOrder, PricingOrderItem
                if hasattr(PricingOrder, field_name):
                    # 主表字段
                    query_values = db.session.query(getattr(PricingOrder, field_name)).distinct().filter(
                        getattr(PricingOrder, field_name).isnot(None),
                        getattr(PricingOrder, field_name) != ''
                    ).limit(50).all()
                    values = [str(v[0]) for v in query_values if v[0] is not None]
                elif hasattr(PricingOrderItem, field_name):
                    # 明细表字段
                    query_values = db.session.query(getattr(PricingOrderItem, field_name)).distinct().filter(
                        getattr(PricingOrderItem, field_name).isnot(None),
                        getattr(PricingOrderItem, field_name) != ''
                    ).limit(50).all()
                    values = [str(v[0]) for v in query_values if v[0] is not None]
                    
            elif object_type == 'expense':
                from app.models.expense import Expense, ExpenseItem
                if hasattr(Expense, field_name):
                    # 主表字段
                    query_values = db.session.query(getattr(Expense, field_name)).distinct().filter(
                        getattr(Expense, field_name).isnot(None),
                        getattr(Expense, field_name) != ''
                    ).limit(50).all()
                    values = [str(v[0]) for v in query_values if v[0] is not None]
                elif hasattr(ExpenseItem, field_name):
                    # 明细表字段
                    query_values = db.session.query(getattr(ExpenseItem, field_name)).distinct().filter(
                        getattr(ExpenseItem, field_name).isnot(None),
                        getattr(ExpenseItem, field_name) != ''
                    ).limit(50).all()
                    values = [str(v[0]) for v in query_values if v[0] is not None]
        
        # 去重并排序
        values = sorted(list(set(values))) if values else []
        
        return values[:50]  # 最多返回50个值
        
    except Exception as e:
        current_app.logger.error(f"获取字段值时出错: {str(e)}")
        return []


@approval_config_bp.route('/api/get-field-options', methods=['GET'])
@login_required
@admin_required
def get_field_options_api():
    """获取对象的字段选项API"""
    object_type = request.args.get('object_type')
    template_id = request.args.get('template_id')
    
    if not object_type:
        return jsonify({'success': False, 'message': '缺少对象类型参数'}), 400
    
    try:
        # 获取字段选项
        field_options = get_object_field_options(object_type)
        
        # 转换为前端需要的格式
        if isinstance(field_options, dict) and 'master' in field_options:
            # 分组格式 (master/detail)
            fields = {
                'master': dict(field_options['master']) if field_options.get('master') else {},
                'detail': dict(field_options['detail']) if field_options.get('detail') else {}
            }
        else:
            # 简单格式
            fields = dict(field_options) if field_options else {}
        
        current_app.logger.info(f"字段选项获取成功 - 对象类型: {object_type}, 模板ID: {template_id}")
        
        return jsonify({
            'success': True,
            'object_type': object_type,
            'template_id': template_id,
            'fields': fields
        })
        
    except Exception as e:
        current_app.logger.error(f"获取字段选项时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'获取字段选项失败: {str(e)}'}), 500


@approval_config_bp.route('/api/dynamic-fields/<string:object_type>', methods=['GET'])
@login_required
@admin_required
def get_dynamic_fields(object_type):
    """API端点：获取对象的动态字段列表
    
    Args:
        object_type: 对象类型 (project, quotation, customer, etc.)
    
    Returns:
        JSON格式的动态字段列表
    """
    try:
        from app.utils.field_value_helper import get_supported_fields_for_object
        
        print(f"🔍 [调试] API获取动态字段开始:")
        print(f"  - 对象类型: {object_type}")
        
        # 获取支持的字段
        supported_fields = get_supported_fields_for_object(object_type)
        
        print(f"  - 原始字段数量: {len(supported_fields)}")
        for i, field in enumerate(supported_fields):
            print(f"    [{i+1}] {field}")
        
        # 转换为前端需要的格式
        fields = []
        for field_info in supported_fields:
            field_data = {
                'value': field_info['field'],
                'label': field_info['label'],
                'has_mapping': field_info.get('has_mapping', False),
                'type': field_info.get('type', 'string')
            }
            fields.append(field_data)
            print(f"    转换后: {field_data}")
        
        current_app.logger.info(f"动态字段获取成功 - 对象类型: {object_type}, 字段数量: {len(fields)}")
        
        return jsonify({
            'success': True,
            'object_type': object_type,
            'fields': fields
        })
        
    except Exception as e:
        current_app.logger.error(f"获取动态字段失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'message': f'获取字段失败: {str(e)}'
        }), 500


@approval_config_bp.route('/step/<int:step_id>/details', methods=['GET'])
@login_required
@permission_required('approval', 'edit')
def get_step_details(step_id):
    """API端点：获取步骤详细信息
    
    Args:
        step_id: 步骤ID
    
    Returns:
        JSON格式的步骤详细信息
    """
    try:
        step = ApprovalStep.query.get_or_404(step_id)
        
        # 🔍 调试：记录原始步骤数据
        current_app.logger.info(f"🔍 [API-step_details] 步骤ID: {step_id}")
        current_app.logger.info(f"🔍 [API-step_details] 可编辑字段类型: {type(step.editable_fields)}")
        current_app.logger.info(f"🔍 [API-step_details] 可编辑字段值: {step.editable_fields}")
        
        step_data = {
            'id': step.id,
            'step_name': step.step_name,
            'step_type': step.step_type,
            'approver_type': step.approver_type,
            'approver_user_id': step.approver_user_id,
            'action_type': step.action_type,
            'branch_condition': step.branch_condition,
            'editable_fields': step.editable_fields or []
        }
        
        # 🔍 调试：记录返回的数据
        current_app.logger.info(f"🔍 [API-step_details] 返回数据: {step_data}")
        
        return jsonify({
            'success': True,
            'step': step_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取步骤详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取步骤详情失败: {str(e)}'
        }), 500


# 分支条件管理API
@approval_config_bp.route('/step/<int:step_id>/condition/<int:condition_index>/data', methods=['GET'])
@login_required
@admin_required
def get_branch_condition_data(step_id, condition_index):
    """获取分支条件数据"""
    try:
        step = ApprovalStep.query.get_or_404(step_id)
        
        if not step.branch_condition or 'conditions' not in step.branch_condition:
            return jsonify({
                'success': False,
                'message': '步骤不包含分支条件'
            }), 400
        
        conditions = step.branch_condition['conditions']
        if condition_index >= len(conditions):
            return jsonify({
                'success': False,
                'message': '分支条件索引超出范围'
            }), 400
        
        condition = conditions[condition_index]
        original_field = step.branch_condition.get('field')
        
        # 获取原始值和显示值
        raw_value = condition.get('value')
        display_value = raw_value
        
        # 使用现有的字典映射函数处理值显示（在字段标准化之前）
        # 支持多值映射（逗号分隔的值）
        def map_multi_value(value, mapping_func):
            """通用多值映射函数"""
            if not value:
                return value
            
            value_str = str(value)
            if ',' in value_str:
                # 处理多值情况（逗号分隔）
                values = [v.strip() for v in value_str.split(',') if v.strip()]
                mapped_values = []
                for single_value in values:
                    mapped_value = mapping_func(single_value, 'zh')
                    mapped_values.append(mapped_value if mapped_value else single_value)
                return ','.join(mapped_values)
            else:
                # 处理单值情况
                return mapping_func(value, 'zh')
        
        # 默认显示值等于原始值
        display_value = raw_value
        
        # 根据字段类型选择对应的映射函数
        if original_field == 'project_type':
            print(f"🔍 [调试] 项目类型映射开始:")
            print(f"  - 原始字段名: {original_field}")
            print(f"  - 原始值: {raw_value}")
            from app.utils.dictionary_helpers import project_type_label
            display_value = map_multi_value(raw_value, project_type_label)
            print(f"  - 映射后显示值: {display_value}")
            print(f"🔍 [调试] 项目类型映射完成")
        elif original_field == 'project_stage':
            from app.utils.dictionary_helpers import project_stage_label
            display_value = map_multi_value(raw_value, project_stage_label)
        elif original_field == 'report_source':
            from app.utils.dictionary_helpers import report_source_label
            display_value = map_multi_value(raw_value, report_source_label)
        elif original_field == 'authorization_status':
            from app.utils.dictionary_helpers import authorization_status_label
            display_value = map_multi_value(raw_value, authorization_status_label)
        elif original_field == 'company_type':
            from app.utils.dictionary_helpers import company_type_label
            display_value = map_multi_value(raw_value, company_type_label)
        # 可以继续添加其他字段类型的映射支持
        
        # 直接使用原始字段名，不再进行任何转换
        field = original_field
        
        # 调试API返回数据
        condition_data = {
            'field': field,
            'operator': condition.get('operator'),
            'value': raw_value,
            'display_value': display_value,
            'approver_id': condition.get('approver_id'),
            'approver_type': condition.get('approver_type'),
            'action': condition.get('action'),
            'action_type': condition.get('action_type') or condition.get('action')
        }
        
        print(f"🚀 [调试] API返回分支条件数据:")
        print(f"  - 字段: {field}")
        print(f"  - 原始值: {raw_value}")
        print(f"  - 显示值: {display_value}")
        print(f"  - 完整条件: {condition_data}")
        
        return jsonify({
            'success': True,
            'condition': condition_data,
            'step': {
                'editable_fields': step.editable_fields or [],
                'cc_users': step.cc_users or [],
                'send_email': step.send_email or False,
                'cc_enabled': step.cc_enabled or False
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取分支条件数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取数据失败: {str(e)}'
        }), 500


@approval_config_bp.route('/step/<int:step_id>/data', methods=['GET'])
@login_required
@admin_required
def get_step_data(step_id):
    """获取步骤数据 - 用于编辑步骤表单"""
    try:
        step = ApprovalStep.query.get_or_404(step_id)

        step_data = {
            'id': step.id,
            'step_name': step.step_name,
            'editable_fields': step.editable_fields or [],
            'cc_users': step.cc_users or [],
            'send_email': step.send_email or False,
            'cc_enabled': step.cc_enabled or False,
            'approver_user_id': step.approver_user_id,
            'approver_type': step.approver_type or 'user',
            'action_type': step.action_type or '',
            'execution_condition': step.execution_condition
        }
        
        return jsonify({
            'success': True,
            'step': step_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取步骤数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取步骤数据失败: {str(e)}'
        }), 500


@approval_config_bp.route('/step/<int:step_id>/branch-stats', methods=['GET'])
@login_required
@admin_required
def get_step_branch_stats(step_id):
    """获取步骤的分支条件统计信息"""
    try:
        current_app.logger.info(f"获取步骤 {step_id} 的分支条件统计信息")
        
        # 获取分支条件数量
        conditions_count = get_step_branch_conditions_count(step_id)
        
        # 获取统一的条件字段
        unified_field = get_step_branch_field_from_step_data(step_id)
        
        current_app.logger.info(f"步骤 {step_id} 统计: 条件数量={conditions_count}, 统一字段={unified_field}")
        
        return jsonify({
            'success': True,
            'step_id': step_id,
            'conditions_count': conditions_count,
            'unified_field': unified_field,
            'has_conditions': conditions_count > 0
        })
        
    except Exception as e:
        current_app.logger.error(f"获取步骤分支统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取分支条件统计失败: {str(e)}'
        }), 500


@approval_config_bp.route('/step/<int:step_id>/branch-lock-status/<int:condition_index>', methods=['GET'])
@login_required
@admin_required
def get_branch_field_lock_status(step_id, condition_index):
    """获取分支条件字段的锁定状态"""
    try:
        current_app.logger.info(f"检查步骤 {step_id} 条件 {condition_index} 的字段锁定状态")
        
        # 判断是否需要锁定
        should_lock = should_lock_branch_field(step_id, condition_index)
        
        # 获取条件字段（如果需要预填充）
        unified_field = get_step_branch_field_from_step_data(step_id) if should_lock else None
        
        current_app.logger.info(f"步骤 {step_id} 条件 {condition_index}: 锁定={should_lock}, 字段={unified_field}")
        
        return jsonify({
            'success': True,
            'step_id': step_id,
            'condition_index': condition_index,
            'should_lock': should_lock,
            'unified_field': unified_field,
            'lock_reason': _get_lock_reason(step_id, condition_index, should_lock)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取字段锁定状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取字段锁定状态失败: {str(e)}'
        }), 500


def _get_lock_reason(step_id, condition_index, should_lock):
    """获取锁定原因的描述文本"""
    if not should_lock:
        return "第一个条件且无其他条件，可以编辑"
    
    if condition_index == 0:
        return "第一个条件但已有其他条件，为保持一致性已锁定"
    else:
        return f"第{condition_index + 1}个条件，必须使用与第一个条件相同的字段"


@approval_config_bp.route('/step/<int:step_id>/validate-condition', methods=['POST'])
@login_required
@admin_required
def validate_branch_condition(step_id):
    """验证分支条件是否有冲突"""
    try:
        current_app.logger.info(f"验证步骤 {step_id} 的分支条件")
        
        # 获取步骤
        step = ApprovalStep.query.get_or_404(step_id)
        
        # 获取表单数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少验证数据'
            }), 400
        
        # 提取条件数据
        operator = data.get('operator')
        field_value = data.get('field_value')
        condition_id = data.get('condition_id')  # 编辑时排除自己
        
        if not operator or not field_value:
            return jsonify({
                'success': False,
                'message': '条件操作符和值不能为空'
            }), 400
        
        # 检查重复条件
        from app.models.approval_branch_condition import ApprovalBranchCondition
        existing_condition = ApprovalBranchCondition.check_duplicate(
            step_id, operator, field_value, exclude_id=condition_id
        )
        
        if existing_condition:
            # 存在冲突
            conflict_info = {
                'has_conflict': True,
                'existing_condition': {
                    'id': existing_condition.id,
                    'operator': existing_condition.operator,
                    'field_value': existing_condition.field_value,
                    'approver_name': existing_condition.approver.real_name if existing_condition.approver else None,
                    'approver_type': existing_condition.approver_type,
                    'created_at': existing_condition.created_at.isoformat() if existing_condition.created_at else None
                }
            }
            
            return jsonify({
                'success': False,
                'has_conflict': True,
                'conflict': conflict_info,
                'message': f'条件冲突：该条件配置已存在'
            }), 409
        
        # 无冲突
        return jsonify({
            'success': True,
            'has_conflict': False,
            'message': '条件验证通过'
        })
        
    except Exception as e:
        current_app.logger.error(f"验证分支条件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'验证失败: {str(e)}'
        }), 500


@approval_config_bp.route('/step/<int:step_id>/suggest-condition-values', methods=['POST'])
@login_required 
@admin_required
def suggest_condition_values(step_id):
    """为避免冲突建议条件值"""
    try:
        # 获取步骤
        step = ApprovalStep.query.get_or_404(step_id)
        
        data = request.get_json()
        field_type = data.get('field_type', '')
        operator = data.get('operator', '')
        
        suggestions = []
        
        # 根据字段类型提供建议值
        if field_type == 'project_type':
            suggestions = [
                {'value': 'business_opportunity', 'label': '客户服务'},
                {'value': 'channel_follow', 'label': '渠道跟进'},
                {'value': 'sales_focus', 'label': '销售重点'}
            ]
        elif field_type == 'amount':
            suggestions = [
                {'value': '10000', 'label': '1万元以上'},
                {'value': '50000', 'label': '5万元以上'},
                {'value': '100000', 'label': '10万元以上'}
            ]
        
        # 获取已使用的值，过滤掉冲突的建议
        from app.models.approval_branch_condition import ApprovalBranchCondition
        existing_values = [
            c.field_value for c in 
            ApprovalBranchCondition.query.filter_by(step_id=step_id, operator=operator).all()
        ]
        
        available_suggestions = [
            s for s in suggestions 
            if s['value'] not in existing_values
        ]
        
        return jsonify({
            'success': True,
            'suggestions': available_suggestions,
            'existing_values': existing_values
        })
        
    except Exception as e:
        current_app.logger.error(f"获取条件值建议失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取建议失败: {str(e)}'
        }), 500


@approval_config_bp.route('/step/<int:step_id>/condition/<int:condition_index>/edit', methods=['POST'])
@login_required
@admin_required
def edit_branch_condition(step_id, condition_index):
    """编辑分支条件"""
    try:
        step = ApprovalStep.query.get_or_404(step_id)
        
        if not step.branch_condition or 'conditions' not in step.branch_condition:
            return jsonify({
                'success': False,
                'message': '步骤不包含分支条件'
            }), 400
        
        branch_condition = step.branch_condition.copy()
        conditions = branch_condition['conditions']
        
        if condition_index >= len(conditions):
            return jsonify({
                'success': False,
                'message': '分支条件索引超出范围'
            }), 400
        
        # 获取表单数据
        field = request.form.get('field') or request.form.get('branch_field')
        operator = request.form.get('operator') or request.form.get('branch_operator')
        value = request.form.get('value') or request.form.get('branch_value')
        approver_id = request.form.get('approver_id') or request.form.get('approver_selection')
        action = request.form.get('action') or request.form.get('action_type')
        
        # 处理审批人ID
        if approver_id and approver_id.startswith('user_'):
            approver_id = int(approver_id.replace('user_', ''))
            approver_type = 'user'
        elif approver_id == 'next_level':
            approver_id = None
            approver_type = 'next_level'
        else:
            approver_id = int(approver_id) if approver_id and approver_id.isdigit() else None
            approver_type = 'user'
        
        # 更新条件
        conditions[condition_index] = {
            'operator': operator,
            'value': value,
            'approver_id': approver_id,
            'approver_type': approver_type,
            'action': action
        }
        
        # 更新字段（如果提供）
        if field:
            branch_condition['field'] = field
        
        branch_condition['conditions'] = conditions
        step.branch_condition = branch_condition
        
        db.session.commit()
        
        flash(f'分支条件 {condition_index + 1} 更新成功', 'success')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"编辑分支条件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'编辑失败: {str(e)}'
        }), 500


@approval_config_bp.route('/step/<int:step_id>/condition/<int:condition_index>/delete', methods=['POST'])
@login_required
@admin_required
def delete_branch_condition(step_id, condition_index):
    """删除分支条件"""
    try:
        step = ApprovalStep.query.get_or_404(step_id)
        
        if not step.branch_condition or 'conditions' not in step.branch_condition:
            return jsonify({
                'success': False,
                'message': '步骤不包含分支条件'
            }), 400
        
        branch_condition = step.branch_condition.copy()
        conditions = branch_condition['conditions']
        
        if condition_index >= len(conditions):
            return jsonify({
                'success': False,
                'message': '分支条件索引超出范围'
            }), 400
        
        if len(conditions) <= 1:
            return jsonify({
                'success': False,
                'message': '至少需要保留一个分支条件'
            }), 400
        
        # 删除条件
        conditions.pop(condition_index)
        branch_condition['conditions'] = conditions
        step.branch_condition = branch_condition
        
        db.session.commit()
        
        current_app.logger.info(f"用户 {current_user.username} 删除了步骤 {step_id} 的分支条件 {condition_index}")
        
        return jsonify({
            'success': True,
            'message': f'分支条件删除成功，剩余 {len(conditions)} 个条件'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除分支条件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@approval_config_bp.route('/migrate-branch-condition-ids', methods=['POST'])
@login_required
@admin_required
def migrate_branch_condition_ids_route():
    """手动触发分支条件ID迁移"""
    try:
        from app.models.approval import ApprovalStep
        
        current_app.logger.info("🚀 开始手动触发分支条件ID迁移")
        
        # 查找所有有分支条件的步骤
        steps_with_conditions = ApprovalStep.query.filter(
            ApprovalStep.branch_condition.isnot(None),
            ApprovalStep.step_type == 'branch'
        ).all()
        
        current_app.logger.info(f"📊 找到 {len(steps_with_conditions)} 个分支步骤需要检查")
        
        updated_count = 0
        
        for step in steps_with_conditions:
            try:
                current_app.logger.info(f"🔍 检查步骤: {step.id} - {step.step_name}")
                
                # 检查是否需要迁移
                needs_update = migrate_branch_condition_ids(step)
                
                if needs_update:
                    current_app.logger.info(f"✅ 为步骤 {step.id} 添加了条件ID")
                    updated_count += 1
                    
                    # 显示更新后的条件
                    if step.branch_condition and 'conditions' in step.branch_condition:
                        conditions = step.branch_condition['conditions']
                        for i, condition in enumerate(conditions):
                            condition_id = condition.get('id', 'N/A')
                            condition_value = condition.get('value', 'N/A')
                            current_app.logger.info(f"📋 条件 {i+1}: ID={condition_id}, 值={condition_value}")
                else:
                    current_app.logger.info(f"⏭️ 步骤 {step.id} 的条件已有ID，跳过")
                    
            except Exception as e:
                current_app.logger.error(f"❌ 处理步骤 {step.id} 时出错: {str(e)}")
                db.session.rollback()
                continue
        
        if updated_count > 0:
            db.session.commit()
            current_app.logger.info(f"✅ 迁移完成！已更新 {updated_count} 个步骤")
            flash(f'迁移成功！已为 {updated_count} 个分支步骤的条件添加了ID', 'success')
        else:
            current_app.logger.info("✅ 所有分支条件都已经有ID，无需迁移")
            flash('所有分支条件都已经有ID，无需迁移', 'info')
        
        return redirect(request.referrer or url_for('approval_config.index'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"迁移分支条件ID失败: {str(e)}")
        flash(f'迁移失败: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('approval_config.index'))


# 新表格式的分支条件管理API (基于条件ID)

@approval_config_bp.route('/step/<int:step_id>/condition/by-id/<string:condition_id>/data', methods=['GET'])
@login_required
@admin_required
def get_branch_condition_data_by_id(step_id, condition_id):
    """基于条件ID获取分支条件数据（重构版本 - 使用统一服务层）"""
    try:
        from app.services.branch_condition_service import BranchConditionService
        
        # 验证步骤存在
        step = ApprovalStep.query.get_or_404(step_id)
        
        # 使用服务层获取条件数据
        result = BranchConditionService.get_condition_for_edit(condition_id)
        
        if not result['success']:
            return jsonify({
                'success': False,
                'message': result['error']
            }), 404 if '不存在' in result['error'] else 500
        
        # 为前端添加字段映射的显示值
        condition_data = result['condition']
        raw_value = condition_data['field_value']
        
        # 获取分支字段（优先从step的branch_condition中获取，如果没有则默认为project.project_type）
        field = 'project.project_type'
        if hasattr(step, 'branch_condition') and step.branch_condition:
            field = step.branch_condition.get('field', 'project.project_type')
        
        # 根据字段类型进行值映射
        display_value = raw_value
        field_base = field.split('.')[-1]  # 去掉前缀，如 project.project_type -> project_type
        
        if field_base == 'project_type':
            from app.utils.dictionary_helpers import project_type_label
            display_value = project_type_label(raw_value, 'zh')
        elif field_base == 'project_stage':
            from app.utils.dictionary_helpers import project_stage_label
            display_value = project_stage_label(raw_value, 'zh')
        
        # 更新condition_data格式以匹配前端期望
        condition_data.update({
            'field': field,
            'value': raw_value,
            'display_value': display_value or raw_value
        })
        
        return jsonify({
            'success': True,
            'condition': condition_data,
            'step': result['step']
        })
        
    except Exception as e:
        current_app.logger.error(f"获取分支条件数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取数据失败: {str(e)}'
        }), 500


@approval_config_bp.route('/step/<int:step_id>/condition/by-id/<string:condition_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_branch_condition_by_id(step_id, condition_id):
    """基于条件ID编辑分支条件（重构版本 - 使用统一服务层）"""
    try:
        from app.services.branch_condition_service import BranchConditionService
        
        # 验证步骤存在
        step = ApprovalStep.query.get_or_404(step_id)
        
        # 使用服务层更新条件
        result = BranchConditionService.update_condition(condition_id, request.form)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '分支条件更新成功',
                'condition': result['condition'].to_dict() if hasattr(result['condition'], 'to_dict') else {}
            })
        else:
            return jsonify({
                'success': False,
                'message': result['error']
            }), 400
        
    except Exception as e:
        current_app.logger.error(f"编辑分支条件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'编辑失败: {str(e)}'
        }), 500


@approval_config_bp.route('/step/<int:step_id>/condition/by-id/<string:condition_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_branch_condition_by_id(step_id, condition_id):
    """基于条件ID删除分支条件（重构版本 - 使用统一服务层）"""
    try:
        from app.services.branch_condition_service import BranchConditionService
        
        # 验证步骤存在
        step = ApprovalStep.query.get_or_404(step_id)
        
        # 使用服务层删除条件
        result = BranchConditionService.delete_condition(condition_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '分支条件删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': result['error']
            }), 400
        
    except Exception as e:
        current_app.logger.error(f"删除分支条件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500
 