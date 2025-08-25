"""
分支条件统一管理服务

这个服务层统一管理所有分支条件的CRUD操作，确保JSON快照和表记录的数据一致性。
核心设计原则：
1. ApprovalBranchCondition表作为主数据源
2. approval_step.branch_condition字段作为执行时的快照
3. 任何数据变更都通过此服务层，确保数据同步
"""

from flask import current_app
from app import db
from app.models.approval import ApprovalStep
from app.models.approval_branch_condition import ApprovalBranchCondition
import json
import uuid
from datetime import datetime


class BranchConditionService:
    """分支条件统一管理服务"""
    
    # 操作符映射表：前端操作符 -> 标准操作符
    OPERATOR_MAPPING = {
        'from_field_list': 'equals',
        'equals_from_list': 'equals',
        'in_from_list': 'in',
        'equals': 'equals',
        'not_equals': 'not_equals',
        'contains': 'contains',
        'not_contains': 'not_contains',
        'greater_than': 'greater_than',
        'less_than': 'less_than',
        'in': 'in',
        'not_in': 'not_in',
        'starts_with': 'starts_with',
        'ends_with': 'ends_with',
        'is_null': 'is_null',
        'is_not_null': 'is_not_null'
    }
    
    @staticmethod
    def normalize_operator(operator):
        """标准化操作符"""
        return BranchConditionService.OPERATOR_MAPPING.get(operator, operator)
    
    @staticmethod
    def determine_smart_operator(form_operator, form_value):
        """
        智能确定操作符
        
        对于 from_field_list 操作符，根据值的数量智能选择 equals 或 in
        
        Args:
            form_operator: 前端传入的操作符
            form_value: 条件值
            
        Returns:
            str: 智能确定的标准操作符
        """
        # 如果不是字段列表选择，直接标准化
        if form_operator != 'from_field_list':
            return BranchConditionService.normalize_operator(form_operator)
        
        # 处理字段列表选择的情况
        if not form_value:
            current_app.logger.info('🔍 智能操作符判断: 无值 → 默认使用 equals')
            return 'equals'
        
        # 检查是否为多值（包含逗号）
        value_str = str(form_value).strip()
        if ',' in value_str:
            # 分割并清理值
            values = [v.strip() for v in value_str.split(',') if v.strip()]
            if len(values) > 1:
                current_app.logger.info(f'✅ 智能操作符判断: 检测到 {len(values)} 个值 → 使用 in 操作符')
                return 'in'
            elif len(values) == 1:
                current_app.logger.info('✅ 智能操作符判断: 检测到 1 个值 → 使用 equals 操作符')
                return 'equals'
        else:
            current_app.logger.info('✅ 智能操作符判断: 单个值 → 使用 equals 操作符')
            return 'equals'
        
        # 默认情况
        current_app.logger.info('ℹ️ 智能操作符判断: 默认 → 使用 equals 操作符')
        return 'equals'
    
    @staticmethod
    def validate_condition_data(condition_data):
        """验证分支条件数据"""
        required_fields = ['operator', 'value']
        for field in required_fields:
            if field not in condition_data or condition_data[field] is None:
                return False, f"缺少必需字段: {field}"
        
        # 验证操作符有效性
        normalized_operator = BranchConditionService.normalize_operator(condition_data['operator'])
        if normalized_operator not in BranchConditionService.OPERATOR_MAPPING.values():
            return False, f"无效的操作符: {condition_data['operator']}"
        
        return True, None
    
    @staticmethod
    def create_branch_step_conditions(step, form_data):
        """
        创建分支步骤条件（统一入口）
        
        Args:
            step: ApprovalStep对象
            form_data: 表单数据
            
        Returns:
            dict: 包含branch_condition JSON和创建结果
        """
        try:
            current_app.logger.info(f"🔧 开始为步骤 {step.id} 创建分支条件")
            
            # 提取分支条件数据
            branch_field = form_data.get('branch_field')
            branch_operator = form_data.get('branch_operator')
            branch_value = form_data.get('branch_value')
            branch_value_final = form_data.get('branch_value_final')
            approver_selection = form_data.get('approver_selection')
            action_type = form_data.get('action_type')
            
            # 使用最终值（如果有的话）
            final_value = branch_value_final if branch_value_final else branch_value
            
            # 项目类型值标准化映射
            final_value = BranchConditionService._normalize_project_type_value(final_value)
            
            current_app.logger.info(f"📋 分支条件原始数据: field={branch_field}, operator={branch_operator}, value={final_value}")
            
            # 解析审批人数据
            approver_type, approver_id = BranchConditionService._parse_approver_data(approver_selection)
            
            # 标准化操作符
            standard_operator = BranchConditionService.normalize_operator(branch_operator)
            current_app.logger.info(f"🔄 操作符标准化: {branch_operator} -> {standard_operator}")
            
            # 创建表记录
            condition_record = ApprovalBranchCondition.create_condition(
                step_id=step.id,
                operator=standard_operator,
                field_value=final_value,
                approver_id=approver_id,
                approver_type=approver_type,
                action=action_type,
                condition_order=1
            )
            
            db.session.add(condition_record)
            db.session.flush()  # 获取ID但不提交
            
            current_app.logger.info(f"✅ 创建表记录: {condition_record.id}")
            
            # 同步生成JSON快照
            branch_condition_json = BranchConditionService.sync_step_json_snapshot(step)
            
            db.session.commit()
            current_app.logger.info(f"✅ 分支条件创建完成")
            
            return {
                'success': True,
                'branch_condition': branch_condition_json,
                'condition_record': condition_record
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"❌ 创建分支条件失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def sync_step_json_snapshot(step):
        """
        同步表记录到JSON快照
        
        Args:
            step: ApprovalStep对象
            
        Returns:
            dict: 生成的JSON快照数据
        """
        try:
            # 获取步骤的所有分支条件
            conditions = ApprovalBranchCondition.get_step_conditions(step.id, ordered=True)
            
            if not conditions:
                # 没有条件时清空JSON
                step.branch_condition = None
                return None
            
            # 构建JSON格式（兼容现有审批执行逻辑）
            json_conditions = []
            for condition in conditions:
                json_conditions.append({
                    'id': condition.id,
                    'operator': condition.operator,
                    'value': condition.field_value,
                    'approver_id': condition.approver_id,
                    'approver_type': condition.approver_type,
                    'action': condition.action
                })
            
            # 使用第一个条件的字段信息（假设同一步骤的条件使用相同字段）
            first_condition = conditions[0]
            branch_condition_json = {
                'field': 'project_type',  # 修复：直接使用字段名，不加前缀
                'conditions': json_conditions,
                'default_branch': {
                    'approver_id': None,
                    'approver_type': 'next_branch',
                    'action': ''
                }
            }
            
            # 更新步骤的JSON快照
            step.branch_condition = branch_condition_json
            
            current_app.logger.info(f"🔄 JSON快照已同步: {len(json_conditions)} 个条件")
            
            return branch_condition_json
            
        except Exception as e:
            current_app.logger.error(f"❌ JSON快照同步失败: {str(e)}")
            raise e
    
    @staticmethod
    def get_condition_for_edit(condition_id):
        """
        获取条件编辑数据
        
        Args:
            condition_id: 条件ID
            
        Returns:
            dict: 标准化的条件编辑数据
        """
        try:
            condition = ApprovalBranchCondition.query.get(condition_id)
            if not condition:
                return {'success': False, 'error': '条件不存在'}
            
            # 获取关联的步骤信息
            step = condition.step
            if not step:
                return {'success': False, 'error': '关联步骤不存在'}
            
            # 从步骤的branch_condition中获取字段信息
            raw_field_name = None
            if step.branch_condition and isinstance(step.branch_condition, dict):
                raw_field_name = step.branch_condition.get('field', 'project_type')  # 默认为project_type
            else:
                raw_field_name = 'project_type'  # 兜底默认值
            
            # 统一使用原始字段名，不进行格式转换
            field_name = raw_field_name
            current_app.logger.info(f"✅ 字段名统一格式: {field_name}")
                
            # 构建标准化的编辑数据
            condition_data = {
                'id': condition.id,
                'field': field_name,  # 添加字段信息，前端需要此字段来设置条件字段选择器
                'operator': condition.operator,
                'field_value': condition.field_value,
                'display_value': condition.field_value,  # 显示值，可能需要后续处理
                'approver_id': condition.approver_id,
                'approver_type': condition.approver_type,
                'action': condition.action,
                'action_type': condition.action  # 兼容前端字段名
            }
            
            
            # 检查步骤是否有其他分支条件（用于字段锁定逻辑）
            other_conditions_count = ApprovalBranchCondition.query.filter_by(step_id=step.id).count()
            has_multiple_conditions = other_conditions_count > 1
            
            # 步骤相关数据
            step_data = {
                'editable_fields': BranchConditionService._parse_editable_fields(step),
                'send_email': getattr(step, 'send_email', False),
                'cc_enabled': getattr(step, 'cc_enabled', False),
                'cc_users': BranchConditionService._get_step_cc_users(step),
                'branch_field': field_name,  # 分支字段名，用于前端字段锁定判断
                'has_multiple_conditions': has_multiple_conditions  # 是否有多个条件，用于字段锁定
            }
            
            current_app.logger.info(f"📋 获取条件编辑数据: {condition_id}")
            
            return {
                'success': True,
                'condition': condition_data,
                'step': step_data
            }
            
        except Exception as e:
            current_app.logger.error(f"❌ 获取条件编辑数据失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_condition(condition_id, form_data):
        """
        更新分支条件
        
        Args:
            condition_id: 条件ID
            form_data: 表单数据
            
        Returns:
            dict: 更新结果
        """
        try:
            condition = ApprovalBranchCondition.query.get(condition_id)
            if not condition:
                return {'success': False, 'error': '条件不存在'}
            
            # 更新条件数据
            if 'branch_operator' in form_data:
                # 获取值用于智能操作符判断
                form_value = form_data.get('branch_value_final') or form_data.get('branch_value')
                # 使用智能操作符判断
                condition.operator = BranchConditionService.determine_smart_operator(
                    form_data['branch_operator'], 
                    form_value
                )
            
            if 'branch_value' in form_data or 'branch_value_final' in form_data:
                final_value = form_data.get('branch_value_final') or form_data.get('branch_value')
                # 项目类型值标准化映射（编辑时也需要）
                final_value = BranchConditionService._normalize_project_type_value(final_value)
                condition.field_value = final_value
            
            if 'approver_selection' in form_data:
                approver_type, approver_id = BranchConditionService._parse_approver_data(form_data['approver_selection'])
                condition.approver_id = approver_id
                condition.approver_type = approver_type
            
            if 'action_type' in form_data:
                condition.action = form_data['action_type']
            
            condition.updated_at = datetime.utcnow()
            
            # 更新关联步骤的配置（分支条件编辑时也需要更新步骤级别的设置）
            step = condition.step
            if step:
                # 更新可编辑字段
                if 'editable_fields' in form_data:
                    editable_fields_value = form_data['editable_fields']
                    # 确保数据格式正确
                    if isinstance(editable_fields_value, str):
                        if editable_fields_value.strip():
                            try:
                                # 验证是否为有效JSON
                                import json
                                parsed = json.loads(editable_fields_value)
                                step.editable_fields = parsed
                                current_app.logger.info(f"📝 更新步骤可编辑字段: {parsed}")
                            except:
                                # 如果不是JSON，按逗号分割
                                fields = [f.strip() for f in editable_fields_value.split(',') if f.strip()]
                                step.editable_fields = fields
                                current_app.logger.info(f"📝 更新步骤可编辑字段(分割): {fields}")
                        else:
                            step.editable_fields = []
                            current_app.logger.info(f"📝 清空步骤可编辑字段")
                    elif isinstance(editable_fields_value, list):
                        step.editable_fields = editable_fields_value
                        current_app.logger.info(f"📝 更新步骤可编辑字段(列表): {editable_fields_value}")
                
                # 更新邮件通知设置
                if 'send_email' in form_data:
                    step.send_email = form_data.get('send_email') == 'true'
                    current_app.logger.info(f"📧 更新邮件通知设置: {step.send_email}")
                
                # 更新抄送设置
                if 'cc_enabled' in form_data:
                    step.cc_enabled = form_data.get('cc_enabled') == 'true'
                    current_app.logger.info(f"📤 更新抄送设置: {step.cc_enabled}")
                
                # 更新抄送用户（如果有的话）
                if 'cc_users' in form_data:
                    cc_users = form_data.getlist('cc_users') if hasattr(form_data, 'getlist') else form_data.get('cc_users', [])
                    if cc_users:
                        # 转换为整数列表
                        cc_user_ids = []
                        for user_id in cc_users:
                            try:
                                cc_user_ids.append(int(user_id))
                            except (ValueError, TypeError):
                                current_app.logger.warning(f"⚠️ 无效的抄送用户ID: {user_id}")
                        if cc_user_ids:
                            step.cc_users = cc_user_ids
                            current_app.logger.info(f"👥 更新抄送用户: {cc_user_ids}")
            
            # 同步更新JSON快照
            BranchConditionService.sync_step_json_snapshot(step)
            
            db.session.commit()
            current_app.logger.info(f"✅ 条件更新完成: {condition_id}")
            
            return {'success': True, 'condition': condition}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"❌ 条件更新失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_condition(condition_id):
        """
        删除分支条件
        
        Args:
            condition_id: 条件ID
            
        Returns:
            dict: 删除结果
        """
        try:
            condition = ApprovalBranchCondition.query.get(condition_id)
            if not condition:
                return {'success': False, 'error': '条件不存在'}
            
            step = condition.step
            
            # 删除条件记录
            db.session.delete(condition)
            
            # 同步更新JSON快照
            BranchConditionService.sync_step_json_snapshot(step)
            
            db.session.commit()
            current_app.logger.info(f"✅ 条件删除完成: {condition_id}")
            
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"❌ 条件删除失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _normalize_project_type_value(value):
        """标准化项目类型值：中文转英文键值"""
        if not value:
            return value
        
        # 项目类型中文到英文的映射
        type_mapping = {
            '客户服务': 'business_opportunity',
            '渠道跟进': 'channel_follow', 
            '销售重点': 'sales_focus',
            '销售关键': 'sales_key'  # 向sales_focus统一
        }
        
        return type_mapping.get(value, value)  # 如果找不到映射，返回原值
    
    @staticmethod
    def _parse_approver_data(approver_selection):
        """解析审批人数据"""
        if not approver_selection:
            return 'next_branch', None
        
        # 支持两种格式: user:6 和 user_6
        if approver_selection.startswith('user:'):
            return 'user', int(approver_selection.split(':')[1])
        elif approver_selection.startswith('user_'):
            return 'user', int(approver_selection.split('_')[1])
        elif approver_selection == 'next_level':
            return 'next_level', None
        else:
            return 'next_branch', None
    
    @staticmethod
    def _parse_editable_fields(step):
        """解析步骤的可编辑字段（修复双重JSON编码问题）"""
        if not hasattr(step, 'editable_fields') or not step.editable_fields:
            return []
        
        editable_fields = step.editable_fields
        current_app.logger.info(f"🔍 解析可编辑字段: type={type(editable_fields)}, value={editable_fields}")
        
        # 如果已经是列表，直接返回
        if isinstance(editable_fields, list):
            current_app.logger.info(f"✅ 字段已是列表格式: {editable_fields}")
            return editable_fields
        
        # 如果是字符串，尝试解析JSON
        if isinstance(editable_fields, str):
            try:
                # 第一次解析
                parsed = json.loads(editable_fields)
                current_app.logger.info(f"🔍 第一次解析结果: type={type(parsed)}, value={parsed}")
                
                if isinstance(parsed, list):
                    # 直接是数组，返回
                    current_app.logger.info(f"✅ 第一次解析得到列表: {parsed}")
                    return parsed
                elif isinstance(parsed, str):
                    # 嵌套的JSON字符串，再次解析
                    try:
                        nested_parsed = json.loads(parsed)
                        current_app.logger.info(f"🔍 第二次解析结果: type={type(nested_parsed)}, value={nested_parsed}")
                        if isinstance(nested_parsed, list):
                            current_app.logger.info(f"✅ 第二次解析得到列表: {nested_parsed}")
                            return nested_parsed
                    except:
                        current_app.logger.warning(f"⚠️ 第二次JSON解析失败: {parsed}")
                        pass
            except:
                current_app.logger.warning(f"⚠️ 第一次JSON解析失败: {editable_fields}")
                pass
        
        # 解析失败，返回空列表
        current_app.logger.warning(f"❌ 无法解析可编辑字段，返回空列表: {editable_fields}")
        return []
    
    @staticmethod
    def _get_step_cc_users(step):
        """获取步骤的抄送用户"""
        # 这里需要根据实际的步骤模型字段来实现
        # 暂时返回空列表
        return []