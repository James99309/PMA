"""
审批分支条件处理辅助函数模块

从 app.views.approval_config 中提取的分支条件相关业务逻辑，
用于处理审批步骤的分支条件添加、编辑和删除操作。
"""

import json
from flask import current_app, flash, redirect, url_for
from app import db
from app.models.approval import ApprovalStep


def handle_branch_condition_add(step, form_data):
    """处理分支条件添加"""
    try:
        # 获取表单数据
        branch_operator = form_data.get('branch_operator')
        branch_value = form_data.get('branch_value')
        branch_value_final = form_data.get('branch_value_final')
        branch_value_select = form_data.get('branch_value_select')  # 新增：获取下拉框值
        
        # 修复字段映射问题 - 前端实际传递的字段名
        true_branch_approver = form_data.get('approver_selection')  # 前端传递的是 approver_selection
        true_branch_action = form_data.get('action_type')           # 前端传递的是 action_type
        
        # 获取最终的条件值 - 优先使用branch_value_final，然后是下拉框值，最后是文本输入值
        raw_branch_value = branch_value_final if branch_value_final and branch_value_final != 'None' else (
            branch_value_select if branch_value_select else branch_value
        )
        
        # 修复：将中文显示值映射为数据库值
        value_mapping = {
            '客户服务': 'business_opportunity',
            '渠道跟进': 'channel_follow', 
            '销售重点': 'sales_focus'
        }
        final_branch_value = value_mapping.get(raw_branch_value, raw_branch_value)
        
        # 处理操作符转换
        standard_operator = branch_operator
        if branch_operator == 'equals_from_list':
            standard_operator = 'equals'
        elif branch_operator == 'in_from_list':
            standard_operator = 'in'
        elif branch_operator == 'from_field_list':  # 修复：添加from_field_list转换
            standard_operator = 'equals'
        
        # 详细调试信息
        current_app.logger.info(f"添加分支条件调试 - 所有表单数据: {dict(form_data)}")
        current_app.logger.info(f"条件值处理 - 原始值: {raw_branch_value}, 映射后: {final_branch_value}, 原始输入: {branch_value}")
        current_app.logger.info(f"操作符转换 - 原始: {branch_operator}, 标准: {standard_operator}")
        current_app.logger.info(f"审批人配置 - approver: {true_branch_approver}, action: {true_branch_action}")
        
        # 处理true分支审批人
        true_approver_type = 'user'
        true_approver_id = None
        if true_branch_approver == 'next_level':
            true_approver_type = 'next_level'
        elif true_branch_approver == 'next_branch':
            true_approver_type = 'next_branch'
        elif true_branch_approver and true_branch_approver.startswith('user_'):
            true_approver_id = int(true_branch_approver.replace('user_', ''))
        elif true_branch_approver and true_branch_approver.isdigit():
            true_approver_id = int(true_branch_approver)
        
        # 获取现有的branch_condition，如果没有则创建新的
        current_condition = step.branch_condition if step.branch_condition else {
            'field': form_data.get('branch_field'),
            'conditions': [],
            'default_branch': {
                'approver_id': None,
                'approver_type': 'next_branch',
                'action': ''
            }
        }
        
        # 确保现有条件都有ID（向后兼容）
        existing_conditions = ensure_conditions_have_ids(current_condition.get('conditions', []))
        current_condition['conditions'] = existing_conditions
        
        # 创建新的条件（包含唯一ID）
        new_condition = {
            'id': generate_condition_id(),  # 🔑 关键：为新条件生成唯一ID
            'operator': standard_operator,
            'value': final_branch_value,
            'approver_id': true_approver_id,
            'approver_type': true_approver_type,
            'action': true_branch_action
        }
        
        # 🔍 检查是否与现有条件重复
        is_duplicate, duplicate_condition = check_condition_duplicate(new_condition, existing_conditions)
        
        if is_duplicate:
            current_app.logger.error(f"❌ 发现重复条件，无法添加")
            current_app.logger.error(f"新条件: {new_condition}")
            current_app.logger.error(f"重复条件: {duplicate_condition}")
            flash(f'添加失败：条件"{final_branch_value}"已存在，无法重复添加', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 添加新条件到条件列表
        current_condition['conditions'].append(new_condition)
        current_app.logger.info(f"✅ 添加新条件成功 - 条件ID: {new_condition['id']}")
        
        # 🔍 保存前数据状态详细记录
        current_app.logger.info(f"🔍 === 保存前数据状态分析 === 步骤ID: {step.id}")
        current_app.logger.info(f"原始branch_condition: {step.branch_condition}")
        current_app.logger.info(f"即将添加的新条件: {new_condition}")
        current_app.logger.info(f"更新后的完整条件配置: {current_condition}")
        current_app.logger.info(f"预期条件总数: {len(current_condition['conditions'])}")
        
        # 🔍 SQLAlchemy JSON字段更新机制调试
        current_app.logger.info(f"🔍 === SQLAlchemy JSON字段更新调试 === 步骤ID: {step.id}")
        current_app.logger.info(f"更新前 step.branch_condition: {step.branch_condition}")
        current_app.logger.info(f"准备设置的 current_condition: {current_condition}")
        
        # 更新步骤 - 使用多种方式确保JSON字段被正确标记为dirty
        step.branch_condition = current_condition
        
        # 强制标记字段为dirty（确保SQLAlchemy知道字段已被修改）
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(step, 'branch_condition')
        
        current_app.logger.info(f"🔄 已更新step对象的branch_condition字段并标记为dirty")
        current_app.logger.info(f"更新后 step.branch_condition: {step.branch_condition}")
        
        try:
            current_app.logger.info(f"📤 准备提交数据库事务 - 步骤ID: {step.id}")
            
            # 🔍 添加SQL执行调试
            from sqlalchemy import event
            sql_queries = []
            
            @event.listens_for(db.engine, "before_cursor_execute", once=True)
            def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                sql_queries.append({
                    'statement': statement,
                    'parameters': parameters
                })
                current_app.logger.info(f"🔍 即将执行SQL: {statement}")
                current_app.logger.info(f"🔍 SQL参数: {parameters}")
            
            db.session.commit()
            current_app.logger.info(f"✅ 数据库事务提交完成 - 步骤ID: {step.id}")
            current_app.logger.info(f"🔍 本次提交执行的SQL数量: {len(sql_queries)}")
            
            # 🔍 立即验证数据是否真的保存了
            current_app.logger.info(f"🔍 === 提交后立即验证 ===")
            verification_step = ApprovalStep.query.get(step.id)
            if verification_step and verification_step.branch_condition:
                actual_conditions = verification_step.branch_condition.get('conditions', [])
                current_app.logger.info(f"🔍 验证结果 - 实际保存的条件数: {len(actual_conditions)}")
                current_app.logger.info(f"🔍 验证结果 - 完整数据: {verification_step.branch_condition}")
                
                # 详细检查每个条件
                for i, condition in enumerate(actual_conditions):
                    current_app.logger.info(f"🔍 条件{i+1}: {condition}")
                    
                if len(actual_conditions) != len(current_condition['conditions']):
                    current_app.logger.error(f"❌ 数据不一致! 预期{len(current_condition['conditions'])}个条件，实际保存了{len(actual_conditions)}个")
                else:
                    current_app.logger.info(f"✅ 数据验证通过! 条件数量一致: {len(actual_conditions)}")
            else:
                current_app.logger.error(f"❌ 验证失败! 无法从数据库重新获取步骤数据")
                
        except Exception as commit_error:
            current_app.logger.error(f"❌ 数据库事务提交失败: {commit_error}")
            current_app.logger.error(f"❌ 错误详情: {type(commit_error).__name__}: {str(commit_error)}")
            db.session.rollback()
            raise commit_error
        
        current_app.logger.info(f"🎉 分支条件添加流程完成 - 步骤ID: {step.id}")
        flash(f'分支条件添加成功，当前共有 {len(current_condition["conditions"])} 个条件', 'success')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加分支条件失败: {str(e)}")
        flash(f'添加失败: {str(e)}', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))


def handle_branch_condition_edit(step, form_data):
    """处理分支条件编辑 - 基于条件ID"""
    try:
        # 🔑 关键：获取条件ID（如果有的话）
        condition_id = form_data.get('condition_id')
        condition_index = int(form_data.get('condition_index', 0))
        
        current_app.logger.info(f"🔍 编辑分支条件 - 步骤ID: {step.id}, 条件ID: {condition_id}, 条件索引: {condition_index}")
        
        # 获取表单数据
        branch_operator = form_data.get('branch_operator')
        branch_value = form_data.get('branch_value')
        branch_value_final = form_data.get('branch_value_final')
        branch_value_select = form_data.get('branch_value_select')
        true_branch_approver = form_data.get('approver_selection') or form_data.get('true_branch_approver')
        true_branch_action = form_data.get('action_type') or form_data.get('true_branch_action')
        
        # 获取最终的条件值
        raw_branch_value = branch_value_final if branch_value_final and branch_value_final != 'None' else (
            branch_value_select if branch_value_select else branch_value
        )
        
        # 处理值映射
        value_mapping = {
            '客户服务': 'business_opportunity',
            '渠道跟进': 'channel_follow', 
            '销售重点': 'sales_focus'
        }
        final_branch_value = value_mapping.get(raw_branch_value, raw_branch_value)
        
        # 处理操作符转换
        standard_operator = branch_operator
        if branch_operator == 'equals_from_list':
            standard_operator = 'equals'
        elif branch_operator == 'in_from_list':
            standard_operator = 'in'
        elif branch_operator == 'from_field_list':
            standard_operator = 'equals'
        
        # 处理审批人
        true_approver_type = 'user'
        true_approver_id = None
        if true_branch_approver == 'next_level':
            true_approver_type = 'next_level'
        elif true_branch_approver == 'next_branch':
            true_approver_type = 'next_branch'
        elif true_branch_approver and true_branch_approver.startswith('user_'):
            true_approver_id = int(true_branch_approver.replace('user_', ''))
        elif true_branch_approver and true_branch_approver.isdigit():
            true_approver_id = int(true_branch_approver)
        
        # 获取当前条件配置
        current_condition = step.branch_condition.copy() if step.branch_condition else {
            'field': form_data.get('branch_field'),
            'conditions': [],
            'default_branch': {
                'approver_id': None,
                'approver_type': 'next_branch',
                'action': ''
            }
        }
        
        # 确保现有条件都有ID
        existing_conditions = ensure_conditions_have_ids(current_condition.get('conditions', []))
        current_condition['conditions'] = existing_conditions
        
        # 如果有条件ID，基于ID查找条件
        target_condition = None
        target_index = None
        
        if condition_id:
            for i, condition in enumerate(existing_conditions):
                if condition.get('id') == condition_id:
                    target_condition = condition
                    target_index = i
                    break
        
        # 如果没找到，使用索引（兼容性）
        if target_condition is None:
            if condition_index < len(existing_conditions):
                target_condition = existing_conditions[condition_index]
                target_index = condition_index
            else:
                current_app.logger.error(f"❌ 找不到要编辑的条件 - ID: {condition_id}, 索引: {condition_index}")
                flash('编辑失败：找不到指定的分支条件', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 创建更新后的条件数据
        updated_condition = {
            'id': target_condition.get('id') or generate_condition_id(),  # 保持原ID或生成新ID
            'operator': standard_operator,
            'value': final_branch_value,
            'approver_id': true_approver_id,
            'approver_type': true_approver_type,
            'action': true_branch_action
        }
        
        # 🔍 检查是否与其他条件重复（排除自己）
        is_duplicate, duplicate_condition = check_condition_duplicate(
            updated_condition, existing_conditions, exclude_id=updated_condition['id']
        )
        
        if is_duplicate:
            current_app.logger.error(f"❌ 编辑后的条件与其他条件重复，无法更新")
            current_app.logger.error(f"更新条件: {updated_condition}")
            current_app.logger.error(f"重复条件: {duplicate_condition}")
            flash(f'编辑失败：条件"{final_branch_value}"已存在，无法重复', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 更新指定条件
        current_condition['conditions'][target_index] = updated_condition
        
        # 更新字段（如果提供）
        branch_field = form_data.get('branch_field')
        if branch_field:
            current_condition['field'] = branch_field
        
        # 保存更新
        step.branch_condition = current_condition
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(step, 'branch_condition')
        
        db.session.commit()
        
        current_app.logger.info(f"✅ 分支条件编辑成功 - 步骤ID: {step.id}, 条件ID: {updated_condition['id']}")
        flash(f'分支条件编辑成功', 'success')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"编辑分支条件失败: {str(e)}")
        flash(f'编辑失败: {str(e)}', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))


def handle_branch_condition_delete(step, form_data):
    """处理分支条件删除 - 支持基于ID或索引"""
    try:
        # 获取条件ID和索引
        condition_id = form_data.get('condition_id')
        condition_index = int(form_data.get('condition_index', 0))
        
        current_app.logger.info(f"🗑️ 删除分支条件 - 步骤ID: {step.id}, 条件ID: {condition_id}, 条件索引: {condition_index}")
        
        # 获取当前条件配置
        current_condition = step.branch_condition.copy() if step.branch_condition else None
        if not current_condition or 'conditions' not in current_condition:
            flash('步骤不包含分支条件', 'warning')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        conditions = current_condition['conditions']
        
        # 检查是否至少保留一个条件
        if len(conditions) <= 1:
            flash('至少需要保留一个分支条件', 'warning')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 找到要删除的条件
        target_condition = None
        target_index = None
        
        # 优先使用ID查找
        if condition_id:
            for i, condition in enumerate(conditions):
                if condition.get('id') == condition_id:
                    target_condition = condition
                    target_index = i
                    break
        
        # 如果没找到，使用索引（兼容性）
        if target_condition is None:
            if 0 <= condition_index < len(conditions):
                target_condition = conditions[condition_index]
                target_index = condition_index
            else:
                flash('条件索引无效', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 删除条件
        removed_condition = conditions.pop(target_index)
        current_condition['conditions'] = conditions
        
        # 保存更新
        step.branch_condition = current_condition
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(step, 'branch_condition')
        
        db.session.commit()
        
        current_app.logger.info(f"✅ 分支条件删除成功 - 步骤ID: {step.id}, 剩余条件数: {len(conditions)}")
        current_app.logger.info(f"已删除条件ID: {removed_condition.get('id', 'N/A')}")
        
        flash(f'分支条件删除成功，剩余 {len(current_condition["conditions"])} 个条件', 'success')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除分支条件失败: {str(e)}")
        flash(f'删除失败: {str(e)}', 'danger')
        return redirect(url_for('approval_config.template_detail', template_id=step.process_id))


def validate_branch_condition_data(form_data):
    """验证分支条件数据的完整性
    
    Args:
        form_data: 表单数据字典
        
    Returns:
        tuple: (is_valid, error_message)
    """
    branch_field = form_data.get('branch_field')
    branch_operator = form_data.get('branch_operator')
    branch_value = form_data.get('branch_value')
    branch_value_final = form_data.get('branch_value_final')
    true_branch_approver = form_data.get('true_branch_approver')
    
    # 获取最终的条件值
    final_branch_value = branch_value_final if branch_value_final else branch_value
    
    if not branch_field:
        return False, '分支步骤必须设置条件字段'
    
    if not branch_operator:
        return False, '分支步骤必须设置条件操作符'
        
    if not final_branch_value and branch_operator not in ['is_null', 'is_not_null', 'is_empty', 'is_not_empty']:
        return False, '分支步骤必须设置条件值'
        
    if not true_branch_approver:
        return False, '分支步骤必须设置审批人'
    
    return True, None


def get_branch_condition_summary(branch_condition):
    """获取分支条件的摘要信息
    
    Args:
        branch_condition: 分支条件JSON数据
        
    Returns:
        dict: 包含条件数量、字段名等摘要信息
    """
    if not branch_condition:
        return {
            'field': None,
            'condition_count': 0,
            'has_default': False
        }
    
    return {
        'field': branch_condition.get('field'),
        'condition_count': len(branch_condition.get('conditions', [])),
        'has_default': 'default_branch' in branch_condition and 
                      branch_condition['default_branch'].get('approver_type') is not None
    }


def generate_condition_id():
    """生成分支条件的唯一ID"""
    import uuid
    return f"cond_{uuid.uuid4().hex[:8]}"


def check_condition_duplicate(new_condition, existing_conditions, exclude_id=None):
    """检查条件是否与现有条件重复
    
    Args:
        new_condition: 新的条件数据
        existing_conditions: 现有条件列表
        exclude_id: 排除的条件ID（编辑时排除自己）
        
    Returns:
        tuple: (is_duplicate, duplicate_condition)
    """
    for condition in existing_conditions:
        # 排除指定ID（编辑时排除自己）
        if exclude_id and condition.get('id') == exclude_id:
            continue
            
        # 检查核心条件是否重复：操作符 + 值
        if (condition.get('operator') == new_condition.get('operator') and
            condition.get('value') == new_condition.get('value')):
            return True, condition
    
    return False, None


def ensure_conditions_have_ids(conditions):
    """确保所有条件都有唯一ID（向后兼容）"""
    for condition in conditions:
        if not condition.get('id'):
            condition['id'] = generate_condition_id()
    return conditions


def migrate_branch_condition_ids(step):
    """为现有分支条件添加ID（数据迁移）"""
    if not step.branch_condition or 'conditions' not in step.branch_condition:
        return False
    
    conditions = step.branch_condition['conditions']
    needs_update = False
    
    for condition in conditions:
        if not condition.get('id'):
            condition['id'] = generate_condition_id()
            needs_update = True
    
    if needs_update:
        # 使用 flag_modified 确保更新
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(step, 'branch_condition')
        
    return needs_update