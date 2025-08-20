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
    get_object_field_options
)
from app.models.approval import ApprovalProcessTemplate, ApprovalStep, ApprovalInstance, ApprovalRecord, ApprovalStatus
from app.models.user import User
from app import db, csrf
from flask import current_app

def handle_branch_condition_add(step, form_data):
    """处理分支条件添加"""
    try:
        # 获取表单数据
        branch_operator = form_data.get('branch_operator')
        branch_value = form_data.get('branch_value')
        branch_value_final = form_data.get('branch_value_final')
        branch_value_select = form_data.get('branch_value_select')  # 新增：获取下拉框值
        true_branch_approver = form_data.get('true_branch_approver')
        true_branch_action = form_data.get('true_branch_action')
        
        # 获取最终的条件值 - 优先使用branch_value_final，然后是下拉框值，最后是文本输入值
        final_branch_value = branch_value_final if branch_value_final and branch_value_final != 'None' else (
            branch_value_select if branch_value_select else branch_value
        )
        
        # 处理操作符转换
        standard_operator = branch_operator
        if branch_operator == 'equals_from_list':
            standard_operator = 'equals'
        elif branch_operator == 'in_from_list':
            standard_operator = 'in'
        
        # 详细调试信息
        current_app.logger.info(f"添加分支条件调试 - 所有表单数据: {dict(form_data)}")
        current_app.logger.info(f"添加分支条件 - operator: '{branch_operator}' -> '{standard_operator}', branch_value: '{branch_value}', branch_value_select: '{branch_value_select}', branch_value_final: '{branch_value_final}', final_value: '{final_branch_value}'")
        current_app.logger.info(f"添加分支条件 - approver: '{true_branch_approver}', action: '{true_branch_action}'")
        
        # 验证必填字段
        if not branch_operator:
            flash('条件操作符不能为空', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        if not final_branch_value and branch_operator not in ['is_null', 'is_not_null', 'is_empty', 'is_not_empty']:
            current_app.logger.error(f"条件值验证失败 - final_branch_value: '{final_branch_value}', operator: '{branch_operator}'")
            current_app.logger.error(f"原始数据 - branch_value: '{branch_value}', branch_value_final: '{branch_value_final}'")
            flash('条件值不能为空', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        if not true_branch_approver:
            flash('审批人不能为空', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 处理审批人类型
        approver_type = 'user'
        approver_id = None
        current_app.logger.info(f"处理审批人 - true_branch_approver: '{true_branch_approver}', 类型: {type(true_branch_approver)}")
        if true_branch_approver == 'next_level':
            approver_type = 'next_level'
            current_app.logger.info("设置审批人类型为 next_level")
        elif true_branch_approver == 'next_branch':
            approver_type = 'next_branch'
            current_app.logger.info("设置审批人类型为 next_branch")
        elif true_branch_approver and true_branch_approver.isdigit():
            approver_id = int(true_branch_approver)
            current_app.logger.info(f"设置审批人ID为 {approver_id}")
        
        current_app.logger.info(f"最终审批人配置 - approver_type: '{approver_type}', approver_id: {approver_id}")
        
        # 获取当前分支条件
        current_condition = step.branch_condition or {}
        
        # 如果当前是简单的true/false结构，转换为多条件结构
        if 'true_branch' in current_condition and 'false_branch' in current_condition:
            # 转换为新的多条件结构
            field = current_condition.get('field')
            conditions = []
            
            # 添加原有的true_branch作为第一个条件
            if current_condition.get('operator') and current_condition.get('value'):
                conditions.append({
                    'operator': current_condition['operator'],
                    'value': current_condition['value'],
                    'approver_id': current_condition['true_branch'].get('approver_id'),
                    'approver_type': current_condition['true_branch'].get('approver_type', 'user'),
                    'action': current_condition['true_branch'].get('action')
                })
            
            new_condition = {
                'field': field,
                'conditions': conditions,
                'default_branch': current_condition.get('false_branch', {})
            }
            current_condition = new_condition
        
        # 添加新的条件
        if 'conditions' not in current_condition:
            current_condition['conditions'] = []
        
        # 添加新条件
        new_condition_item = {
            'operator': standard_operator,
            'value': final_branch_value,
            'approver_id': approver_id,
            'approver_type': approver_type,
            'action': true_branch_action
        }
        
        current_app.logger.info(f"准备添加新条件: {new_condition_item}")
        current_app.logger.info(f"当前分支条件结构: {current_condition}")
        
        current_condition['conditions'].append(new_condition_item)
        
        current_app.logger.info(f"添加条件后的分支条件结构: {current_condition}")
        current_app.logger.info(f"条件数量: {len(current_condition['conditions'])}")
        
        # 更新步骤
        step.branch_condition = current_condition
        
        # 标记字段为已修改 - 确保SQLAlchemy检测到JSON字段的变化
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(step, 'branch_condition')
        
        current_app.logger.info(f"准备提交数据库更改...")
        db.session.commit()
        current_app.logger.info(f"数据库更改已提交")
        
        flash('分支条件添加成功', 'success')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加分支条件失败: {str(e)}")
        flash(f'添加失败: {str(e)}', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))


def handle_branch_condition_edit(step, form_data):
    """处理分支条件编辑"""
    try:
        condition_index = int(form_data.get('condition_index', 0))
        
        # 获取表单数据
        branch_operator = form_data.get('branch_operator')
        branch_value = form_data.get('branch_value')
        branch_value_final = form_data.get('branch_value_final')
        branch_value_select = form_data.get('branch_value_select')
        true_branch_approver = form_data.get('true_branch_approver')
        true_branch_action = form_data.get('true_branch_action')
        
        # 获取最终的条件值
        final_branch_value = branch_value_final if branch_value_final and branch_value_final != 'None' else (
            branch_value_select if branch_value_select else branch_value
        )
        
        current_app.logger.info(f"编辑分支条件 - 索引: {condition_index}, operator: '{branch_operator}', final_value: '{final_branch_value}'")
        
        # 验证必填字段
        if not branch_operator:
            flash('条件操作符不能为空', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        if not final_branch_value and branch_operator not in ['is_null', 'is_not_null', 'is_empty', 'is_not_empty']:
            flash('条件值不能为空', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        if not true_branch_approver:
            flash('审批人不能为空', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 处理审批人类型
        approver_type = 'user'
        approver_id = None
        if true_branch_approver == 'next_level':
            approver_type = 'next_level'
        elif true_branch_approver == 'next_branch':
            approver_type = 'next_branch'
        elif true_branch_approver and true_branch_approver.isdigit():
            approver_id = int(true_branch_approver)
        
        # 获取当前分支条件
        current_condition = step.branch_condition or {}
        
        if 'conditions' in current_condition and condition_index < len(current_condition['conditions']):
            # 更新指定索引的条件
            current_condition['conditions'][condition_index] = {
                'operator': branch_operator,
                'value': final_branch_value,
                'approver_id': approver_id,
                'approver_type': approver_type,
                'action': true_branch_action
            }
            
            # 更新步骤
            step.branch_condition = current_condition
            db.session.commit()
            
            flash('分支条件编辑成功', 'success')
        else:
            flash('指定的分支条件不存在', 'danger')
            
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"编辑分支条件失败: {str(e)}")
        flash(f'编辑失败: {str(e)}', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))


def handle_branch_condition_delete(step, form_data):
    """处理分支条件删除"""
    try:
        condition_index = int(form_data.get('condition_index', 0))
        
        current_app.logger.info(f"🗑️ 删除分支条件请求 - 步骤ID: {step.id}, 条件索引: {condition_index}")
        current_app.logger.info(f"🔍 删除请求表单数据: {dict(form_data)}")
        
        # 获取当前分支条件
        current_condition = step.branch_condition or {}
        current_app.logger.info(f"📊 删除前的分支条件: {current_condition}")
        
        if 'conditions' in current_condition:
            current_app.logger.info(f"📋 删除前条件数量: {len(current_condition['conditions'])}")
            for i, cond in enumerate(current_condition['conditions']):
                current_app.logger.info(f"  条件 {i}: {cond.get('value')} -> 审批人 {cond.get('approver_id')}")
        else:
            current_app.logger.error("❌ current_condition中没有conditions字段")
        
        if 'conditions' not in current_condition:
            current_app.logger.error(f"❌ 分支条件中没有conditions字段")
            flash('分支条件数据结构错误', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
            
        if condition_index >= len(current_condition['conditions']):
            current_app.logger.error(f"❌ 条件索引 {condition_index} 超出范围，总条件数: {len(current_condition['conditions'])}")
            flash('指定的分支条件不存在', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
            
        # 检查是否还有其他条件
        if len(current_condition['conditions']) <= 1:
            current_app.logger.error(f"❌ 不能删除最后一个分支条件，当前条件数: {len(current_condition['conditions'])}")
            flash('不能删除最后一个分支条件', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 删除指定索引的条件
        deleted_condition = current_condition['conditions'][condition_index]
        current_app.logger.info(f"🗑️ 即将删除的条件: {deleted_condition}")
        
        del current_condition['conditions'][condition_index]
        current_app.logger.info(f"📋 删除后条件数量: {len(current_condition['conditions'])}")
        
        # 更新步骤 - 使用深拷贝确保SQLAlchemy检测到变化
        import copy
        step.branch_condition = copy.deepcopy(current_condition)
        
        # 标记字段为已修改
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(step, 'branch_condition')
        
        current_app.logger.info(f"📝 准备提交数据库事务...")
        db.session.commit()
        current_app.logger.info(f"✅ 数据库事务提交成功")
        
        flash(f'分支条件删除成功，剩余 {len(current_condition["conditions"])} 个条件', 'success')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除分支条件失败: {str(e)}")
        flash(f'删除失败: {str(e)}', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))

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
        current_object_type=object_type,
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
    
    # 获取所有用户，用于选择审批人
    users = get_all_users()
    
    # 统计实例状态
    all_instances = ApprovalInstance.query.filter_by(process_id=template_id).all()
    pending_instances = [i for i in all_instances if i.status == ApprovalStatus.PENDING]
    completed_instances = [i for i in all_instances if i.status != ApprovalStatus.PENDING]
    
    # 修正权限逻辑：区分结构性修改和内容编辑
    # 结构性修改（删除步骤、重新排序）：进行中实例时禁止
    can_modify_structure = len(pending_instances) == 0
    # 内容编辑（修改步骤属性）：总是允许，因为使用快照机制
    can_edit_content = True
    # 为了向后兼容，保持can_modify变量，但改为允许内容编辑
    can_modify = can_edit_content
    
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
        can_modify=can_modify,  # 修正：内容编辑权限（总是True）
        can_modify_structure=can_modify_structure,  # 新增：结构性修改权限
        can_edit_content=can_edit_content,  # 新增：内容编辑权限
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
    step_name = request.form.get('step_name', '').strip()
    approver_type = request.form.get('approver_type', 'user')
    approver_id = request.form.get('approver_id', type=int)
    send_email = request.form.get('send_email') == 'on'
    action_type = request.form.get('action_type')
    
    # 调试信息
    current_app.logger.info(f"添加步骤 - approver_type: {approver_type}, approver_id: {approver_id}")
    
    # 如果是分支步骤且没有设置步骤名称，使用默认名称
    if not step_name and request.form.get('step_type') == 'branch':
        step_name = '分支决策步骤'
    
    # 新增：分支步骤支持
    step_type = request.form.get('step_type', 'normal')
    
    # 更详细的调试信息
    current_app.logger.info(f"添加步骤详细信息 - step_type: {step_type}, step_name: {step_name}")
    current_app.logger.info(f"表单所有参数: {dict(request.form)}")
    
    # 分支步骤立即设置特殊的审批人类型，避免后续验证问题
    if step_type == 'branch':
        approver_type = 'branch'
        approver_id = None  # 分支步骤不需要主审批人
        current_app.logger.info("分支步骤：设置approver_type=branch, approver_id=None")
    
    branch_condition = None
    branch_group_id = None
    branch_level = 0
    parent_step_id = None
    is_parallel = False
    
    # 检查是否是继承模式（添加新分支时从已有分支继承条件字段）
    inherit_from_step = request.form.get('inherit_from_step', type=int)
    
    if step_type == 'branch':
        # 处理分支条件
        branch_field = request.form.get('branch_field')
        branch_operator = request.form.get('branch_operator') 
        branch_value = request.form.get('branch_value')
        
        # 如果是继承模式且字段为空，从父步骤继承条件字段和操作符
        if inherit_from_step and (not branch_field or not branch_operator):
            parent_step = ApprovalStep.query.get(inherit_from_step)
            if parent_step and parent_step.branch_condition:
                parent_condition = parent_step.branch_condition
                if not branch_field:
                    branch_field = parent_condition.get('field', '')
                if not branch_operator:
                    branch_operator = parent_condition.get('operator', '')
                # 注意：不继承值，新分支需要设置自己的值
        
        true_branch_approver = request.form.get('true_branch_approver')
        true_branch_action = request.form.get('true_branch_action')
        false_branch_approver = request.form.get('false_branch_approver')
        false_branch_action = request.form.get('false_branch_action')
        
        # 获取最终的条件值（来自值选择或手动输入）
        branch_value_final = request.form.get('branch_value_final')
        final_branch_value = branch_value_final if branch_value_final else branch_value
        
        if branch_field and branch_operator and final_branch_value:
            # 转换列表选择操作符为标准操作符
            standard_operator = branch_operator
            if branch_operator == 'equals_from_list':
                standard_operator = 'equals'
            elif branch_operator == 'in_from_list':
                standard_operator = 'in'
            
            # 处理true分支
            true_approver_type = 'user'
            true_approver_id = None
            if true_branch_approver == 'next_level':
                true_approver_type = 'next_level'
            elif true_branch_approver == 'next_branch':
                true_approver_type = 'next_branch'
            elif true_branch_approver and true_branch_approver.isdigit():
                true_approver_id = int(true_branch_approver)
            
            # 处理false分支
            false_approver_type = 'user'
            false_approver_id = None
            if false_branch_approver == 'next_level':
                false_approver_type = 'next_level'
            elif false_branch_approver == 'next_branch':
                false_approver_type = 'next_branch'
            elif false_branch_approver and false_branch_approver.isdigit():
                false_approver_id = int(false_branch_approver)
            
            branch_condition = {
                'field': branch_field,
                'operator': standard_operator,
                'value': final_branch_value,
                'true_branch': {
                    'approver_id': true_approver_id,
                    'approver_type': true_approver_type,
                    'action': true_branch_action
                },
                'false_branch': {
                    'approver_id': false_approver_id,
                    'approver_type': false_approver_type,
                    'action': false_branch_action
                }
            }
            # 分支步骤强制使用分支决策动作
            action_type = 'branch_decision'
            
            # 生成分支组ID（用当前时间戳生成唯一ID）
            import time
            branch_group_id = f"branch_{int(time.time())}_{template_id}"
            
            # 分支步骤的审批人已在前面设置为None和'branch'类型
        else:
            # 分支条件不完整时的错误处理
            if not branch_field:
                flash('分支步骤必须设置条件字段', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=template_id))
            if not branch_operator:
                flash('分支步骤必须设置条件操作符', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=template_id))
            if not final_branch_value and branch_operator not in ['is_null', 'is_not_null', 'is_empty', 'is_not_empty']:
                flash('分支步骤必须设置条件值', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=template_id))
            if not true_branch_approver:
                flash('分支步骤必须设置条件满足时的审批人', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=template_id))
            if not false_branch_approver:
                flash('分支步骤必须设置条件不满足时的审批人', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # 新增字段
    # 支持新格式的JSON字段数据
    editable_fields_json = request.form.get('editable_fields_json')
    if editable_fields_json:
        try:
            editable_fields = json.loads(editable_fields_json)
        except (json.JSONDecodeError, TypeError):
            editable_fields = []
    else:
        # 兼容传统格式
        editable_fields = request.form.getlist('editable_fields')
    
    cc_users = request.form.getlist('cc_users')
    cc_enabled = request.form.get('cc_enabled') == 'on'
    
    # 根据审批人类型决定是否需要固定审批人
    if approver_type in ['next_level', 'auto'] or action_type == 'authorization':
        approver_id = None
    
    # 验证必填字段
    if not template_id or not step_name:
        flash('模板ID和步骤名称不能为空', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # 验证审批人配置（分支步骤和特殊类型步骤不需要这个验证）
    # 分支步骤的审批人在分支条件中指定，不在主步骤中
    if step_type != 'branch' and approver_type == 'user' and not approver_id and action_type != 'authorization':
        flash('选择指定用户时必须选择具体的审批人', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # 添加步骤
    step = add_approval_step(
        template_id=template_id,
        step_name=step_name,
        approver_id=approver_id,
        send_email=send_email,
        editable_fields=editable_fields,
        cc_users=[int(user_id) for user_id in cc_users if user_id.isdigit()],
        cc_enabled=cc_enabled,
        approver_type=approver_type,
        step_type=step_type,
        branch_condition=branch_condition,
        branch_group_id=branch_group_id,
        branch_level=branch_level,
        parent_step_id=parent_step_id,
        is_parallel=is_parallel
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
    
    # 检查编辑模式
    is_branch_edit = request.form.get('is_branch_edit') == 'true'
    is_branch_condition_add = request.form.get('is_branch_condition_add') == 'true'
    is_branch_condition_edit = request.form.get('is_branch_condition_edit') == 'true'
    action = request.form.get('action')
    branch_type = request.form.get('branch_type')
    
    current_app.logger.info(f"编辑模式检查 - is_branch_edit: {is_branch_edit}, is_branch_condition_add: {is_branch_condition_add}, is_branch_condition_edit: {is_branch_condition_edit}, action: {action}")
    current_app.logger.info(f"🔍 edit_step收到的所有表单数据: {dict(request.form)}")
    
    if action == 'delete_branch_condition':
        # 处理分支条件删除
        current_app.logger.info(f"🗑️ 进入删除分支条件处理逻辑 - 步骤ID: {step_id}")
        return handle_branch_condition_delete(step, request.form)
    
    if is_branch_condition_add:
        # 处理分支条件添加
        return handle_branch_condition_add(step, request.form)
    
    if is_branch_condition_edit:
        # 处理分支条件编辑
        return handle_branch_condition_edit(step, request.form)
    
    if is_branch_edit and branch_type:
        # 处理分支编辑，现在支持完整的分支条件编辑
        step_name = request.form.get('step_name')
        branch_field = request.form.get('branch_field')
        branch_operator = request.form.get('branch_operator')
        branch_value = request.form.get('branch_value')
        
        # 分支审批人配置
        true_branch_approver = request.form.get('true_branch_approver')
        true_branch_action = request.form.get('true_branch_action')
        false_branch_approver = request.form.get('false_branch_approver')
        false_branch_action = request.form.get('false_branch_action')
        
        # 获取最终的条件值（来自值选择或手动输入）
        branch_value_final = request.form.get('branch_value_final')
        final_branch_value = branch_value_final if branch_value_final else branch_value
        
        # 验证必填字段
        if not step_name:
            flash('步骤名称不能为空', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=template_id))
        
        if not branch_field or not branch_operator:
            flash('分支条件字段和操作符不能为空', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=template_id))
        
        if not final_branch_value and branch_operator not in ['is_null', 'is_not_null', 'is_empty', 'is_not_empty']:
            flash('分支条件值不能为空', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=template_id))
        
        try:
            # 更新步骤名称
            step.step_name = step_name
            
            # 处理true分支审批人
            true_approver_type = 'user'
            true_approver_id = None
            if true_branch_approver == 'next_level':
                true_approver_type = 'next_level'
            elif true_branch_approver == 'next_branch':
                true_approver_type = 'next_branch'
            elif true_branch_approver and true_branch_approver.startswith('user_'):
                true_approver_id = int(true_branch_approver.replace('user_', ''))
            
            # 处理false分支审批人
            false_approver_type = 'user'
            false_approver_id = None
            if false_branch_approver == 'next_level':
                false_approver_type = 'next_level'
            elif false_branch_approver == 'next_branch':
                false_approver_type = 'next_branch'
            elif false_branch_approver and false_branch_approver.startswith('user_'):
                false_approver_id = int(false_branch_approver.replace('user_', ''))
            
            # 更新完整的分支条件配置
            step.branch_condition = {
                'field': branch_field,
                'operator': branch_operator,
                'value': final_branch_value,
                'true_branch': {
                    'approver_id': true_approver_id,
                    'approver_type': true_approver_type,
                    'action': true_branch_action
                },
                'false_branch': {
                    'approver_id': false_approver_id,
                    'approver_type': false_approver_type,
                    'action': false_branch_action
                }
            }
            
            # 确保动作类型为分支决策
            step.action_type = 'branch_decision'
            
            # 标记字段为已修改并保存
            db.session.merge(step)
            db.session.commit()
            
            flash('分支条件更新成功', 'success')
            return redirect(url_for('approval_config.template_detail', template_id=template_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新分支条件失败: {str(e)}")
            flash(f'更新失败: {str(e)}', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # 常规步骤编辑逻辑
    step_name = request.form.get('step_name')
    approver_type = request.form.get('approver_type', 'user')
    approver_id = request.form.get('approver_id', type=int)
    send_email = request.form.get('send_email') == 'on'
    action_type = request.form.get('action_type')
    
    # 调试信息
    current_app.logger.info(f"编辑步骤 {step_id} - step.step_type: {step.step_type}")
    current_app.logger.info(f"编辑步骤参数 - approver_type: {approver_type}, approver_id: {approver_id}")
    current_app.logger.info(f"表单所有参数: {dict(request.form)}")
    
    # 如果当前步骤是分支步骤，设置正确的审批人类型
    if step.step_type == 'branch':
        approver_type = 'branch'
        approver_id = None  # 分支步骤不需要主审批人
        current_app.logger.info("分支步骤编辑：设置approver_type=branch, approver_id=None")
    
    # 新增字段
    # 支持新格式的JSON字段数据
    editable_fields_json = request.form.get('editable_fields_json')
    if editable_fields_json:
        try:
            editable_fields = json.loads(editable_fields_json)
        except (json.JSONDecodeError, TypeError):
            editable_fields = []
    else:
        # 兼容传统格式
        editable_fields = request.form.getlist('editable_fields')
    
    cc_users = request.form.getlist('cc_users')
    cc_enabled = request.form.get('cc_enabled') == 'on'
    
    # 根据审批人类型决定是否需要固定审批人
    if approver_type in ['next_level', 'auto'] or action_type == 'authorization':
        approver_id = None
    
    # 验证必填字段
    if not step_name:
        flash('步骤名称不能为空', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=template_id))
    
    # 验证审批人配置（分支步骤和特殊类型步骤不需要这个验证）
    # 分支步骤的审批人在分支条件中指定，不在主步骤中
    if step.step_type != 'branch' and approver_type == 'user' and not approver_id and action_type != 'authorization':
        flash('选择指定用户时必须选择具体的审批人', 'danger')
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
        update_approver=True,  # 明确指定要更新审批人
        approver_type=approver_type
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
        if field_name == 'project_type':
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
            from app.utils.dictionary_helpers import CURRENCY_TYPE_LABELS
            from app.utils.i18n import get_current_language
            try:
                lang = get_current_language()
            except:
                lang = 'zh'
            values = [v[lang] for v in CURRENCY_TYPE_LABELS.values()]
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
        
        # 获取支持的字段
        supported_fields = get_supported_fields_for_object(object_type)
        
        # 转换为前端需要的格式
        fields = []
        for field_info in supported_fields:
            fields.append({
                'value': field_info['field'],
                'label': field_info['label'],
                'has_mapping': field_info.get('has_mapping', False),
                'type': field_info.get('type', 'string')
            })
        
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


 