"""
审批步骤处理辅助函数模块

用于分解 add_step 和 edit_step 函数中的复杂逻辑，
提供可重用的步骤处理功能。
"""

import json
import time
from flask import current_app, flash, redirect, url_for, request, jsonify
from app import db
from app.models.approval import ApprovalStep


def validate_step_data(form_data, step_type='normal', is_edit=False):
    """验证步骤数据
    
    Args:
        form_data: 表单数据
        step_type: 步骤类型
        is_edit: 是否是编辑模式
        
    Returns:
        tuple: (is_valid, error_message, processed_data)
    """
    template_id = form_data.get('template_id', type=int) if not is_edit else None
    step_name = form_data.get('step_name', '').strip()
    
    # 如果是分支步骤且没有设置步骤名称，使用默认名称
    if not step_name and step_type == 'branch':
        step_name = '分支决策步骤'
    
    # 验证必填字段
    if not is_edit and not template_id:
        return False, '模板ID不能为空', None
    
    if not step_name:
        return False, '步骤名称不能为空', None
        
    processed_data = {
        'template_id': template_id,
        'step_name': step_name,
        'step_type': step_type
    }
    
    return True, None, processed_data


def process_approver_data(form_data, step_type):
    """处理审批人数据
    
    Args:
        form_data: 表单数据
        step_type: 步骤类型
        
    Returns:
        dict: 处理后的审批人数据
    """
    # 调试信息：记录所有相关表单字段
    current_app.logger.info(f"🔍 [调试] process_approver_data - 步骤类型: {step_type}")
    current_app.logger.info(f"🔍 [调试] 表单字段 approver_selection: {form_data.get('approver_selection')}")
    current_app.logger.info(f"🔍 [调试] 表单字段 approver_type: {form_data.get('approver_type')}")
    current_app.logger.info(f"🔍 [调试] 表单字段 approver_id: {form_data.get('approver_id')}")
    current_app.logger.info(f"🔍 [调试] 表单字段 action_type: {form_data.get('action_type')}")
    current_app.logger.info(f"🔍 [调试] 所有表单字段: {dict(form_data)}")
    
    approver_type = form_data.get('approver_type', 'user')
    approver_id = form_data.get('approver_id', type=int)
    action_type = form_data.get('action_type')
    
    # 后备逻辑：如果隐藏字段为空，尝试从approver_selection解析
    if not approver_id and form_data.get('approver_selection'):
        approver_selection = form_data.get('approver_selection')
        current_app.logger.info(f"🔍 [调试] 从approver_selection解析: {approver_selection}")
        
        if approver_selection == 'next_level':
            approver_type = 'next_level'
            approver_id = None
            current_app.logger.info("🔍 [调试] 解析结果: 上级领导")
        elif approver_selection.startswith('user_'):
            try:
                user_id = int(approver_selection.replace('user_', ''))
                approver_type = 'user'
                approver_id = user_id
                current_app.logger.info(f"🔍 [调试] 解析结果: 用户ID={user_id}")
            except ValueError:
                current_app.logger.error(f"🔍 [调试] 无法解析用户ID: {approver_selection}")
        else:
            current_app.logger.warning(f"🔍 [调试] 未知的approver_selection格式: {approver_selection}")
    
    # 分支步骤特殊处理
    if step_type == 'branch':
        approver_type = 'branch'
        approver_id = None
        current_app.logger.info("分支步骤：设置approver_type=branch, approver_id=None")
    
    # 根据审批人类型决定是否需要固定审批人
    if approver_type in ['next_level', 'auto'] or action_type == 'authorization':
        approver_id = None
    
    # 调试信息：记录处理结果
    result = {
        'approver_type': approver_type,
        'approver_id': approver_id,
        'action_type': action_type
    }
    current_app.logger.info(f"🔍 [调试] process_approver_data 返回结果: {result}")
    
    return result


def process_branch_condition_data(form_data, template_id=None, inherit_from_step=None):
    """处理分支条件数据（重构版本 - 使用统一服务层）
    
    Args:
        form_data: 表单数据
        template_id: 模板ID（用于生成branch_group_id）
        inherit_from_step: 继承的父步骤ID
        
    Returns:
        dict: 处理后的分支条件数据，如果无效则返回None
    """
    from app.services.branch_condition_service import BranchConditionService
    
    branch_field = form_data.get('branch_field')
    branch_operator = form_data.get('branch_operator')
    branch_value = form_data.get('branch_value')
    
    # 继承模式处理
    if inherit_from_step and (not branch_field or not branch_operator):
        parent_step = ApprovalStep.query.get(inherit_from_step)
        if parent_step and parent_step.branch_condition:
            parent_condition = parent_step.branch_condition
            if not branch_field:
                branch_field = parent_condition.get('field', '')
            if not branch_operator:
                # 从父条件的第一个条件中获取操作符
                conditions = parent_condition.get('conditions', [])
                if conditions:
                    branch_operator = conditions[0].get('operator', '')
    
    # 获取分支审批人和动作 - 适配新旧字段格式
    true_branch_approver = form_data.get('approver_selection') or form_data.get('true_branch_approver')
    true_branch_action = form_data.get('action_type') or form_data.get('true_branch_action')
    
    # 获取最终的条件值（来自值选择或手动输入）
    branch_value_final = form_data.get('branch_value_final')
    final_branch_value = branch_value_final if branch_value_final else branch_value
    
    # 使用服务层进行数据验证
    condition_data = {
        'operator': branch_operator,
        'value': final_branch_value
    }
    
    is_valid, error_msg = BranchConditionService.validate_condition_data(condition_data)
    if not is_valid:
        return {'error': error_msg}
    
    # 基础字段验证
    if not branch_field:
        return {'error': '分支步骤必须设置条件字段'}
    if not true_branch_approver:
        return {'error': '分支步骤必须设置条件满足时的审批人'}
    
    # 标准化操作符
    standard_operator = BranchConditionService.normalize_operator(branch_operator)
    
    # 解析审批人数据
    true_approver_type, true_approver_id = BranchConditionService._parse_approver_data(true_branch_approver)
    
    # 生成兼容的JSON结构（仅用于返回给调用者，实际存储由服务层处理）
    branch_condition = {
        'field': branch_field,
        'conditions': [{
            'operator': standard_operator,
            'value': final_branch_value,
            'approver_id': true_approver_id,
            'approver_type': true_approver_type,
            'action': true_branch_action
        }],
        'default_branch': {
            'approver_id': None,
            'approver_type': 'next_branch',
            'action': ''
        }
    }
    
    # 生成分支组ID
    branch_group_id = None
    if template_id:
        branch_group_id = f"branch_{int(time.time())}_{template_id}"
    
    return {
        'branch_condition': branch_condition,
        'branch_group_id': branch_group_id,
        'action_type': 'branch_decision'  # 分支步骤强制使用分支决策动作
    }


def parse_approver_data(approver_string):
    """解析审批人字符串
    
    Args:
        approver_string: 审批人字符串（如 'next_level', 'user_123', '123'）
        
    Returns:
        tuple: (approver_type, approver_id)
    """
    if approver_string == 'next_level':
        return 'next_level', None
    elif approver_string == 'next_branch':
        return 'next_branch', None
    elif approver_string and approver_string.startswith('user_'):
        return 'user', int(approver_string.replace('user_', ''))
    elif approver_string and approver_string.isdigit():
        return 'user', int(approver_string)
    else:
        return 'user', None


def process_additional_fields(form_data):
    """处理附加字段数据

    Args:
        form_data: 表单数据

    Returns:
        dict: 处理后的附加字段数据
    """
    # 支持创建模式和编辑模式的字段名
    # 支持多种值格式：'on' (复选框), 'true' (JavaScript布尔), true (布尔值)
    send_email_value = form_data.get('send_email') or form_data.get('edit_send_email')
    send_email = send_email_value in ('on', 'true', True)

    # 支持新格式的JSON字段数据（同时支持创建和编辑模式）
    editable_fields_json = (form_data.get('editable_fields_json') or
                            form_data.get('edit_editable_fields_json'))
    if editable_fields_json:
        try:
            editable_fields = json.loads(editable_fields_json)
        except (json.JSONDecodeError, TypeError):
            editable_fields = []
    else:
        # 兼容传统格式和隐藏字段（同时支持创建和编辑模式）
        editable_fields_list = (form_data.getlist('editable_fields') or
                               form_data.getlist('edit_editable_fields'))
        editable_fields_single = (form_data.get('editable_fields') or
                                 form_data.get('edit_editable_fields'))

        # 如果单个字段是JSON格式，尝试解析
        if editable_fields_single and (editable_fields_single.startswith('[') or editable_fields_single.startswith('{')):
            try:
                editable_fields = json.loads(editable_fields_single)
            except (json.JSONDecodeError, TypeError):
                editable_fields = editable_fields_list
        else:
            editable_fields = editable_fields_list

    # 支持创建模式和编辑模式的抄送字段
    cc_users_create = form_data.getlist('cc_users')
    cc_users_edit = form_data.getlist('edit_cc_users')
    cc_users = cc_users_create if cc_users_create else cc_users_edit

    # 支持多种值格式：'on' (复选框), 'true' (JavaScript布尔), true (布尔值)
    cc_enabled_value = form_data.get('cc_enabled') or form_data.get('edit_cc_enabled')
    cc_enabled = cc_enabled_value in ('on', 'true', True)

    # 处理cc_users，确保都是有效的整数
    processed_cc_users = []
    for user_id in cc_users:
        if isinstance(user_id, str) and user_id.isdigit():
            processed_cc_users.append(int(user_id))
        elif isinstance(user_id, int):
            processed_cc_users.append(user_id)

    return {
        'send_email': send_email,
        'editable_fields': editable_fields,
        'cc_users': processed_cc_users,
        'cc_enabled': cc_enabled
    }


def validate_approver_configuration(approver_type, approver_id, step_type, action_type):
    """验证审批人配置
    
    Args:
        approver_type: 审批人类型
        approver_id: 审批人ID
        step_type: 步骤类型
        action_type: 动作类型
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # 调试信息：记录验证参数
    current_app.logger.info(f"🔍 [调试] validate_approver_configuration - 参数:")
    current_app.logger.info(f"  - approver_type: {approver_type}")
    current_app.logger.info(f"  - approver_id: {approver_id}")
    current_app.logger.info(f"  - step_type: {step_type}")
    current_app.logger.info(f"  - action_type: {action_type}")
    
    # 分支步骤和特殊类型步骤不需要这个验证
    if step_type == 'branch':
        current_app.logger.info("🔍 [调试] 分支步骤，跳过验证")
        return True, None
        
    if action_type == 'authorization':
        current_app.logger.info("🔍 [调试] 授权动作，跳过验证")
        return True, None
        
    if approver_type == 'user' and not approver_id:
        current_app.logger.error(f"🔍 [调试] 验证失败：approver_type='{approver_type}', approver_id='{approver_id}'")
        return False, '选择指定用户时必须选择具体的审批人'
    
    return True, None


def log_step_operation(operation, step_data, additional_info=None):
    """记录步骤操作日志
    
    Args:
        operation: 操作类型 ('add' 或 'edit')
        step_data: 步骤数据
        additional_info: 附加信息
    """
    log_message = f"{operation.title()} step - "
    
    if 'step_name' in step_data:
        log_message += f"name: {step_data['step_name']}, "
    if 'step_type' in step_data:
        log_message += f"type: {step_data['step_type']}, "
    if 'approver_type' in step_data:
        log_message += f"approver_type: {step_data['approver_type']}, "
    if 'approver_id' in step_data:
        log_message += f"approver_id: {step_data['approver_id']}"
    
    if additional_info:
        log_message += f", {additional_info}"
    
    current_app.logger.info(log_message)


def create_step_response(success, message, template_id, message_type='success'):
    """创建步骤操作响应
    
    Args:
        success: 操作是否成功
        message: 消息内容
        template_id: 模板ID
        message_type: 消息类型 ('success', 'danger', 'warning')
        
    Returns:
        Flask redirect response 或 JSON response (取决于是否为AJAX请求)
    """
    # 检查是否为AJAX请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
    else:
        # 传统表单提交
        flash(message, message_type if not success else 'success')
        return redirect(url_for('approval_config.template_detail', template_id=template_id))


def get_default_step_params():
    """获取默认的步骤参数
    
    Returns:
        dict: 默认参数
    """
    return {
        'branch_level': 0,
        'parent_step_id': None,
        'is_parallel': False
    }


def get_edit_mode_info(form_data):
    """获取编辑模式信息
    
    Args:
        form_data: 表单数据
        
    Returns:
        dict: 编辑模式信息
    """
    return {
        'is_branch_edit': form_data.get('is_branch_edit') == 'true',
        'is_branch_condition_add': form_data.get('is_branch_condition_add') == 'true',
        'is_branch_condition_edit': form_data.get('is_branch_condition_edit') == 'true',
        'action': form_data.get('action'),
        'branch_type': form_data.get('branch_type')
    }


def handle_branch_edit_mode(step, form_data):
    """处理分支编辑模式
    
    Args:
        step: 步骤对象
        form_data: 表单数据
        
    Returns:
        Flask redirect response or None
    """
    step_name = form_data.get('step_name')
    branch_field = form_data.get('branch_field')
    branch_operator = form_data.get('branch_operator')
    branch_value = form_data.get('branch_value')
    
    # 分支审批人配置
    true_branch_approver = form_data.get('true_branch_approver')
    true_branch_action = form_data.get('true_branch_action')
    false_branch_approver = form_data.get('false_branch_approver')
    false_branch_action = form_data.get('false_branch_action')
    
    # 获取最终的条件值
    branch_value_final = form_data.get('branch_value_final')
    final_branch_value = branch_value_final if branch_value_final else branch_value
    
    # 验证必填字段
    if not step_name:
        return create_step_response(False, '步骤名称不能为空', step.process_id, 'danger')
    
    if not branch_field or not branch_operator:
        return create_step_response(False, '分支条件字段和操作符不能为空', step.process_id, 'danger')
    
    if not final_branch_value and branch_operator not in ['is_null', 'is_not_null', 'is_empty', 'is_not_empty']:
        return create_step_response(False, '分支条件值不能为空', step.process_id, 'danger')
    
    try:
        # 更新步骤名称
        step.step_name = step_name
        
        # 处理审批人
        true_approver_type, true_approver_id = parse_approver_data(true_branch_approver)
        false_approver_type, false_approver_id = parse_approver_data(false_branch_approver)
        
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
        
        return create_step_response(True, '分支条件更新成功', step.process_id)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新分支条件失败: {str(e)}")
        return create_step_response(False, f'更新失败: {str(e)}', step.process_id, 'danger')


def handle_regular_step_edit(step, form_data):
    """处理常规步骤编辑
    
    Args:
        step: 步骤对象
        form_data: 表单数据
        
    Returns:
        Flask redirect response or None
    """
    # 验证基本步骤数据（编辑模式）
    is_valid, error_message, step_data = validate_step_data(form_data, step.step_type, is_edit=True)
    if not is_valid:
        return create_step_response(False, error_message, step.process_id, 'danger')
    
    # 处理审批人数据
    approver_data = process_approver_data(form_data, step.step_type)
    
    # 处理附加字段
    additional_fields = process_additional_fields(form_data)
    
    # 验证审批人配置
    is_valid, error_message = validate_approver_configuration(
        approver_data['approver_type'], 
        approver_data['approver_id'], 
        step.step_type, 
        approver_data['action_type']
    )
    if not is_valid:
        return create_step_response(False, error_message, step.process_id, 'danger')
    
    log_step_operation('edit', {**step_data, **approver_data}, f"step_id: {step.id}")
    
    # 更新步骤
    from app.helpers.approval_helpers import update_approval_step
    
    updated_step = update_approval_step(
        step.id,
        step_name=step_data['step_name'],
        approver_id=approver_data['approver_id'],
        send_email=additional_fields['send_email'],
        editable_fields=additional_fields['editable_fields'],
        cc_users=additional_fields['cc_users'],
        cc_enabled=additional_fields['cc_enabled'],
        update_approver=True,
        approver_type=approver_data['approver_type']
    )
    
    if updated_step:
        updated_step.action_type = approver_data['action_type'] if approver_data['action_type'] else None
        db.session.commit()
        return create_step_response(True, '审批步骤更新成功', step.process_id)
    else:
        return create_step_response(False, '更新审批步骤失败', step.process_id, 'danger')


def create_branch_condition_records(step, branch_condition):
    """从JSON分支条件创建ApprovalBranchCondition表记录（重构版本 - 已废弃）
    
    此函数已被重构到 BranchConditionService 中，这里保留用于向后兼容。
    新代码应使用 BranchConditionService.sync_step_json_snapshot() 方法。
    
    Args:
        step: 审批步骤对象
        branch_condition: JSON格式的分支条件数据
    """
    from flask import current_app
    from app.services.branch_condition_service import BranchConditionService
    
    try:
        current_app.logger.warning(f"⚠️ 使用了已废弃的 create_branch_condition_records 函数，建议使用服务层")
        
        # 调用新的服务层方法
        BranchConditionService.sync_step_json_snapshot(step)
        current_app.logger.info(f"✅ 已通过服务层同步步骤 {step.id} 的分支条件")
        
    except Exception as e:
        current_app.logger.error(f"❌ 通过服务层同步分支条件失败: {str(e)}")
        raise e