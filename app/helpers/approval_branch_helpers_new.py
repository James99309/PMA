"""
审批分支条件处理辅助函数模块 - 新版（使用独立数据表）

从原有的JSON格式重构为使用独立的 approval_branch_condition 数据表
提供更高效和可靠的分支条件管理功能
"""

import json
from flask import current_app, flash, redirect, url_for, jsonify
from app import db
from app.models.approval import ApprovalStep
from app.models.approval_branch_condition import ApprovalBranchCondition


def handle_branch_condition_add(step, form_data, api_mode=False):
    """处理分支条件添加 - 使用新表结构
    
    Args:
        step: 审批步骤对象
        form_data: 表单数据，包含分支条件信息
        api_mode: 是否为API模式，True返回JSON，False返回重定向
    
    Returns:
        API模式: JSON响应
        表单模式: 重定向响应
    """
    try:
        current_app.logger.info(f"🔧 [新版] 添加分支条件 - 步骤ID: {step.id}")
        
        # 获取表单数据
        branch_operator = form_data.get('branch_operator')
        branch_value = form_data.get('branch_value')
        branch_value_final = form_data.get('branch_value_final')
        branch_value_select = form_data.get('branch_value_select')
        true_branch_approver = form_data.get('approver_selection')
        true_branch_action = form_data.get('action_type')
        
        current_app.logger.info(f"🔍 表单数据: operator={branch_operator}, value={branch_value}, approver={true_branch_approver}")
        
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
        
        current_app.logger.info(f"🔍 处理后数据: operator={standard_operator}, value={final_branch_value}, approver_id={true_approver_id}, approver_type={true_approver_type}")
        
        # 检查重复条件
        existing_condition = ApprovalBranchCondition.check_duplicate(
            step.id, standard_operator, final_branch_value
        )
        
        if existing_condition:
            current_app.logger.info(f"🔍 发现重复条件: {final_branch_value} {standard_operator}")
            conflict_info = {
                'has_conflict': True,
                'existing_condition': {
                    'id': existing_condition.id,
                    'operator': existing_condition.operator,
                    'field_value': existing_condition.field_value,
                    'display_value': raw_branch_value,  # 用户友好的显示值
                    'approver_name': existing_condition.approver.real_name if existing_condition.approver else None,
                    'approver_type': existing_condition.approver_type,
                    'created_at': existing_condition.created_at.isoformat() if existing_condition.created_at else None
                },
                'attempted_condition': {
                    'operator': standard_operator,
                    'field_value': final_branch_value,
                    'display_value': raw_branch_value,
                    'approver_id': true_approver_id,
                    'approver_type': true_approver_type
                }
            }
            
            if api_mode:
                return jsonify({
                    'success': False,
                    'conflict': conflict_info,
                    'message': f'条件冲突："{raw_branch_value}"已存在相同条件'
                }), 409  # 使用409 Conflict状态码
            else:
                # 非API模式保持原有行为（向后兼容）
                flash(f'添加失败：条件"{raw_branch_value}"已存在，无法重复添加', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 创建新条件
        new_condition = ApprovalBranchCondition.create_condition(
            step_id=step.id,
            operator=standard_operator,
            field_value=final_branch_value,
            approver_id=true_approver_id,
            approver_type=true_approver_type,
            action=true_branch_action
        )
        
        current_app.logger.info(f"🔧 创建新条件: ID={new_condition.id}, value={new_condition.field_value}")
        
        # 保存到数据库
        db.session.add(new_condition)
        db.session.commit()
        
        current_app.logger.info(f"✅ 分支条件添加成功 - 条件ID: {new_condition.id}")
        
        # 更新步骤的迁移状态（如果尚未标记）
        update_step_migration_status(step)
        
        # 统计当前条件数
        total_conditions = ApprovalBranchCondition.query.filter(
            ApprovalBranchCondition.step_id == step.id
        ).count()
        
        if api_mode:
            return jsonify({
                'success': True,
                'message': f'分支条件添加成功，当前共有 {total_conditions} 个条件',
                'condition_id': new_condition.id,
                'total_conditions': total_conditions
            })
        else:
            flash(f'分支条件添加成功，当前共有 {total_conditions} 个条件', 'success')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ 添加分支条件失败: {str(e)}")
        
        if api_mode:
            return jsonify({
                'success': False,
                'message': f'添加失败: {str(e)}'
            }), 500
        else:
            flash(f'添加失败: {str(e)}', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))


def handle_branch_condition_edit(step, form_data, api_mode=False):
    """处理分支条件编辑 - 使用新表结构
    
    Args:
        step: 审批步骤对象
        form_data: 表单数据，包含condition_id和更新内容
        api_mode: 是否为API模式，True返回JSON，False返回重定向
    
    Returns:
        API模式: JSON响应
        表单模式: 重定向响应
    """
    try:
        # 获取条件ID
        condition_id = form_data.get('condition_id')
        
        if not condition_id:
            current_app.logger.error("❌ 编辑分支条件缺少condition_id参数")
            if api_mode:
                return jsonify({
                    'success': False,
                    'message': '编辑失败：缺少条件标识符'
                }), 400
            else:
                flash('编辑失败：缺少条件标识符', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        current_app.logger.info(f"🔧 [新版] 编辑分支条件 - 步骤ID: {step.id}, 条件ID: {condition_id}")
        
        # 查找条件
        condition = ApprovalBranchCondition.query.filter(
            ApprovalBranchCondition.id == condition_id,
            ApprovalBranchCondition.step_id == step.id
        ).first()
        
        if not condition:
            current_app.logger.error(f"❌ 找不到条件: {condition_id}")
            if api_mode:
                return jsonify({
                    'success': False,
                    'message': '编辑失败：找不到指定的分支条件'
                }), 404
            else:
                flash('编辑失败：找不到指定的分支条件', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 获取表单数据
        branch_operator = form_data.get('branch_operator')
        branch_value = form_data.get('branch_value')
        branch_value_final = form_data.get('branch_value_final')
        branch_value_select = form_data.get('branch_value_select')
        true_branch_approver = form_data.get('approver_selection')
        true_branch_action = form_data.get('action_type')
        
        # 处理数据（与添加逻辑相同）
        raw_branch_value = branch_value_final if branch_value_final and branch_value_final != 'None' else (
            branch_value_select if branch_value_select else branch_value
        )
        
        value_mapping = {
            '客户服务': 'business_opportunity',
            '渠道跟进': 'channel_follow', 
            '销售重点': 'sales_focus'
        }
        final_branch_value = value_mapping.get(raw_branch_value, raw_branch_value)
        
        standard_operator = branch_operator
        if branch_operator == 'equals_from_list':
            standard_operator = 'equals'
        elif branch_operator == 'in_from_list':
            standard_operator = 'in'
        elif branch_operator == 'from_field_list':
            standard_operator = 'equals'
        
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
        
        # 检查是否与其他条件重复（排除自己）
        existing_condition = ApprovalBranchCondition.check_duplicate(
            step.id, standard_operator, final_branch_value, exclude_id=condition_id
        )
        
        if existing_condition:
            current_app.logger.info(f"🔍 编辑时发现重复条件: {final_branch_value} {standard_operator}")
            conflict_info = {
                'has_conflict': True,
                'existing_condition': {
                    'id': existing_condition.id,
                    'operator': existing_condition.operator,
                    'field_value': existing_condition.field_value,
                    'display_value': raw_branch_value,
                    'approver_name': existing_condition.approver.real_name if existing_condition.approver else None,
                    'approver_type': existing_condition.approver_type,
                    'created_at': existing_condition.created_at.isoformat() if existing_condition.created_at else None
                },
                'editing_condition': {
                    'id': condition_id,
                    'operator': standard_operator,
                    'field_value': final_branch_value,
                    'display_value': raw_branch_value,
                    'approver_id': true_approver_id,
                    'approver_type': true_approver_type
                }
            }
            
            if api_mode:
                return jsonify({
                    'success': False,
                    'conflict': conflict_info,
                    'message': f'编辑冲突：条件"{raw_branch_value}"已存在相同配置'
                }), 409  # 使用409 Conflict状态码
            else:
                # 非API模式保持原有行为（向后兼容）
                flash(f'编辑失败：条件"{raw_branch_value}"已存在，无法重复', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 更新条件
        condition.update_condition(
            operator=standard_operator,
            field_value=final_branch_value,
            approver_id=true_approver_id,
            approver_type=true_approver_type,
            action=true_branch_action
        )
        
        db.session.commit()
        
        current_app.logger.info(f"✅ 分支条件编辑成功 - 条件ID: {condition_id}")
        
        if api_mode:
            return jsonify({
                'success': True,
                'message': '分支条件编辑成功'
            })
        else:
            flash('分支条件编辑成功', 'success')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ 编辑分支条件失败: {str(e)}")
        
        if api_mode:
            return jsonify({
                'success': False,
                'message': f'编辑失败: {str(e)}'
            }), 500
        else:
            flash(f'编辑失败: {str(e)}', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))


def handle_branch_condition_delete(step, form_data, api_mode=False):
    """处理分支条件删除 - 使用新表结构
    
    Args:
        step: 审批步骤对象
        form_data: 表单数据，包含condition_id
        api_mode: 是否为API模式，True返回JSON，False返回重定向
    
    Returns:
        API模式: JSON响应
        表单模式: 重定向响应
    """
    try:
        # 获取条件ID
        condition_id = form_data.get('condition_id')
        
        if not condition_id:
            current_app.logger.error("❌ 删除分支条件缺少condition_id参数")
            if api_mode:
                return jsonify({
                    'success': False,
                    'message': '删除失败：缺少条件标识符'
                }), 400
            else:
                flash('删除失败：缺少条件标识符', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        current_app.logger.info(f"🔧 [新版] 删除分支条件 - 步骤ID: {step.id}, 条件ID: {condition_id}")
        
        # 查找条件
        condition = ApprovalBranchCondition.query.filter(
            ApprovalBranchCondition.id == condition_id,
            ApprovalBranchCondition.step_id == step.id
        ).first()
        
        if not condition:
            current_app.logger.error(f"❌ 找不到条件: {condition_id}")
            if api_mode:
                return jsonify({
                    'success': False,
                    'message': '删除失败：找不到指定的分支条件'
                }), 404
            else:
                flash('删除失败：找不到指定的分支条件', 'danger')
                return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 检查是否至少保留一个条件
        total_conditions = ApprovalBranchCondition.query.filter(
            ApprovalBranchCondition.step_id == step.id
        ).count()
        
        if total_conditions <= 1:
            current_app.logger.warning(f"⚠️ 尝试删除最后一个分支条件")
            if api_mode:
                return jsonify({
                    'success': False,
                    'message': '至少需要保留一个分支条件'
                }), 400
            else:
                flash('至少需要保留一个分支条件', 'warning')
                return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
        # 删除条件
        condition_value = condition.field_value
        db.session.delete(condition)
        db.session.commit()
        
        remaining_count = total_conditions - 1
        
        current_app.logger.info(f"✅ 分支条件删除成功 - 条件ID: {condition_id}, 剩余: {remaining_count} 个")
        
        if api_mode:
            return jsonify({
                'success': True,
                'message': f'分支条件删除成功，剩余 {remaining_count} 个条件',
                'remaining_count': remaining_count
            })
        else:
            flash(f'分支条件删除成功，剩余 {remaining_count} 个条件', 'success')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ 删除分支条件失败: {str(e)}")
        
        if api_mode:
            return jsonify({
                'success': False,
                'message': f'删除失败: {str(e)}'
            }), 500
        else:
            flash(f'删除失败: {str(e)}', 'danger')
            return redirect(url_for('approval_config.template_detail', template_id=step.process_id))


def get_step_conditions_data(step):
    """获取步骤的分支条件数据（新版格式）"""
    conditions = ApprovalBranchCondition.get_step_conditions(step.id)
    return [condition.to_dict() for condition in conditions]


def get_step_conditions_legacy_format(step):
    """获取步骤的分支条件数据（旧版兼容格式）"""
    conditions = ApprovalBranchCondition.get_step_conditions(step.id)
    return [condition.to_legacy_format() for condition in conditions]


def update_step_migration_status(step):
    """更新步骤的迁移状态标记 - 已简化，统一使用新表"""
    # 确保JSON字段存在基本配置（保留字段名和默认分支配置）
    if not step.branch_condition:
        step.branch_condition = {}
    
    # 确保有基本的字段配置
    if 'field' not in step.branch_condition:
        step.branch_condition.update({
            'field': 'project_type',  # 默认字段
        })
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(step, 'branch_condition')


def validate_branch_condition_data(form_data):
    """验证分支条件数据的完整性"""
    branch_field = form_data.get('branch_field')
    branch_operator = form_data.get('branch_operator')
    branch_value = form_data.get('branch_value')
    branch_value_final = form_data.get('branch_value_final')
    true_branch_approver = form_data.get('approver_selection')
    
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


def get_branch_condition_summary(step):
    """获取分支条件的摘要信息"""
    if not step.is_branch_step():
        return {
            'field': None,
            'condition_count': 0,
            'has_default': False
        }
    
    condition_count = ApprovalBranchCondition.query.filter(
        ApprovalBranchCondition.step_id == step.id
    ).count()
    
    return {
        'field': step.get_branch_field(),
        'condition_count': condition_count,
        'has_default': bool(step.get_default_branch())
    }


# 数据迁移相关函数



def migrate_all_steps_to_new_table():
    """批量迁移所有分支步骤到新表"""
    branch_steps = ApprovalStep.query.filter(
        ApprovalStep.step_type == 'branch'
    ).all()
    
    migrated_count = 0
    failed_count = 0
    
    for step in branch_steps:
        try:
            if migrate_step_to_new_table(step):
                migrated_count += 1
            else:
                current_app.logger.warning(f"步骤 {step.id} 迁移跳过")
        except Exception as e:
            current_app.logger.error(f"步骤 {step.id} 迁移失败: {str(e)}")
            failed_count += 1
    
    if migrated_count > 0:
        db.session.commit()
    
    return migrated_count, failed_count


# 向后兼容性函数（用于过渡期间）



from datetime import datetime