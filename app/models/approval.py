from datetime import datetime, date
from zoneinfo import ZoneInfo
from enum import Enum
import json
import re
import traceback
from flask import current_app
from app import db
from app.models.user import User

def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class ApprovalStatus(Enum):
    """审批状态枚举"""
    PENDING = "pending"    # 审批中
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝
    RECALLED = "recalled"  # 已召回


class ApprovalAction(Enum):
    """审批动作枚举"""
    APPROVE = "approve"  # 同意
    REJECT = "reject"    # 拒绝

    @classmethod
    def from_string(cls, action_str):
        """从字符串获取枚举值"""
        for action in cls:
            if action.value == action_str:
                return action
        return None


class ApprovalActionType:
    """审批动作类型常量"""
    AUTHORIZATION = "authorization"  # 授权动作
    QUOTATION_APPROVAL = "quotation_approval"  # 报价审核动作
    EMAIL_CC = "email_cc"  # 邮件抄送动作
    PAYMENT_PROCESSING = "payment_processing"  # 支付处理动作
    
    # 新增：专项授权动作
    PROJECT_AUTHORIZATION = "project_authorization"  # 项目授权
    CHANNEL_AUTHORIZATION = "channel_authorization"  # 渠道授权
    BUSINESS_AUTHORIZATION = "business_authorization"  # 业务授权（向后兼容）
    CUSTOMER_SERVICE_AUTHORIZATION = "customer_service_authorization"  # 客服授权
    
    # 新增：分支动作
    BRANCH_DECISION = "branch_decision"  # 分支决策
    
    # 新增：批结算审批动作
    PRICING_SETTLEMENT_APPROVAL = "pricing_settlement_approval"  # 批结算审批（同时检查批价单和结算单权限）

    # 新增：产品入库动作
    PRODUCT_WAREHOUSING = "product_warehousing"  # 研发产品入库

    # 新增：表单确认动作（采购流程中的供应商确认、测试、发货、验收等）
    FORM_CONFIRM = "form_confirm"  # 表单确认动作

    # 动作类型标签
    ACTION_TYPE_LABELS = {
        'authorization': {'zh': '授权审批', 'en': 'Authorization'},
        'quotation_approval': {'zh': '报价审核', 'en': 'Quotation Approval'},
        'email_cc': {'zh': '邮件抄送', 'en': 'Email CC'},
        'payment_processing': {'zh': '支付处理', 'en': 'Payment Processing'},
        'project_authorization': {'zh': '项目授权', 'en': 'Project Authorization'},
        'channel_authorization': {'zh': '渠道授权', 'en': 'Channel Authorization'},
        'business_authorization': {'zh': '业务授权', 'en': 'Business Authorization'},
        'customer_service_authorization': {'zh': '客服授权', 'en': 'Customer Service Authorization'},
        'branch_decision': {'zh': '分支决策', 'en': 'Branch Decision'},
        'pricing_settlement_approval': {'zh': '批结算审批', 'en': 'Pricing Settlement Approval'},
        'product_warehousing': {'zh': '产品入库', 'en': 'Product Warehousing'},
        'form_confirm': {'zh': '表单确认', 'en': 'Form Confirm'}
    }
    
    @classmethod
    def get_label(cls, action_type, lang='zh'):
        """获取动作类型标签"""
        return cls.ACTION_TYPE_LABELS.get(action_type, {}).get(lang, action_type)


class ApprovalProcessTemplate(db.Model):
    """审批流程模板"""
    __tablename__ = "approval_process_template"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment="流程名称")
    object_type = db.Column(db.String(50), nullable=False, comment="适用对象（如 quotation）")
    is_active = db.Column(db.Boolean, default=True, comment="是否启用")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="创建人账号ID")
    created_at = db.Column(db.DateTime, default=get_local_time, comment="创建时间")
    required_fields = db.Column(db.JSON, default=list, comment="发起审批时必填字段列表")
    
    # 新增字段：对象锁定配置
    lock_object_on_start = db.Column(db.Boolean, default=True, comment="发起审批后是否锁定对象编辑")
    lock_reason = db.Column(db.String(200), default="审批流程进行中，暂时锁定编辑", comment="锁定原因说明")

    # 关联关系
    creator = db.relationship("User", backref="created_templates", foreign_keys=[created_by])
    steps = db.relationship("ApprovalStep", backref="process", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ApprovalProcessTemplate {self.name}>"


class ApprovalStep(db.Model):
    """流程步骤"""
    __tablename__ = "approval_step"

    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey("approval_process_template.id"), nullable=False, comment="所属流程模板")
    step_order = db.Column(db.Integer, nullable=False, comment="流程顺序")
    approver_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, comment="审批人账号ID")
    approver_type = db.Column(db.String(20), default='user', comment="审批人类型：user(固定用户) 或 auto(自动选择)")
    description = db.Column(db.Text, comment="步骤描述")
    step_name = db.Column(db.String(100), nullable=False, comment="步骤说明（如\"财务审批\"）")
    send_email = db.Column(db.Boolean, default=True, comment="是否发送邮件通知")
    action_type = db.Column(db.String(50), nullable=True, comment="步骤动作类型，如 authorization, quotation_approval")
    action_params = db.Column(db.JSON, nullable=True, comment="动作参数，JSON格式")
    
    # 新增字段：可编辑字段配置
    editable_fields = db.Column(db.JSON, default=list, comment="在此步骤可编辑的字段列表")
    
    # 新增字段：邮件抄送配置
    cc_users = db.Column(db.JSON, default=list, comment="邮件抄送用户ID列表")
    cc_enabled = db.Column(db.Boolean, default=False, comment="是否启用邮件抄送")
    
    # 分支步骤支持
    step_type = db.Column(db.String(20), default='normal', comment="步骤类型：normal(常规) 或 branch(分支)")
    branch_condition = db.Column(db.JSON, nullable=True, comment="分支条件配置（兼容性保留，新版使用独立表）")

    # 步骤执行条件
    execution_condition = db.Column(db.JSON, nullable=True, comment="步骤执行条件：满足条件时才执行此步骤，为空则无条件执行")
    
    # 废弃字段：复杂并行分支功能已简化，以下字段保留但不再使用
    parent_step_id = db.Column(db.Integer, db.ForeignKey("approval_step.id"), nullable=True, comment="[废弃] 上级步骤ID，用于并行分支")
    is_parallel = db.Column(db.Boolean, default=False, comment="[废弃] 是否为并行分支")
    branch_group_id = db.Column(db.String(50), nullable=True, comment="[废弃] 分支组ID，用于标识同一组并行分支")
    branch_level = db.Column(db.Integer, default=0, comment="[废弃] 分支层级，0为主流程，1为一级分支，以此类推")
    branch_path = db.Column(db.String(100), nullable=True, comment="[废弃] 分支路径，如 'true.false.true' 表示分支选择路径")
    merge_step_id = db.Column(db.Integer, db.ForeignKey("approval_step.id"), nullable=True, comment="[废弃] 分支合并步骤ID")

    # 关联关系
    approver = db.relationship("User", backref="approval_steps")
    parent_step = db.relationship(
        "ApprovalStep", 
        remote_side=[id], 
        foreign_keys=[parent_step_id],
        backref="child_steps"
    )
    merge_step = db.relationship(
        "ApprovalStep", 
        remote_side=[id], 
        foreign_keys=[merge_step_id],
        backref="branch_steps"
    )

    def __repr__(self):
        return f"<ApprovalStep {self.step_name}>"

    @classmethod
    def from_snapshot(cls, snapshot_data, process_id=None):
        """从模板快照数据创建临时ApprovalStep对象

        Args:
            snapshot_data: 快照数据字典或ApprovalStep对象
            process_id: 流程模板ID（可选）

        Returns:
            ApprovalStep临时对象，用于调用execute_action等方法
        """
        if isinstance(snapshot_data, cls):
            # 已经是ApprovalStep对象，直接返回
            return snapshot_data

        if not isinstance(snapshot_data, dict):
            # 既不是字典也不是对象，返回None
            return None

        # 从快照字典创建临时对象
        step = cls()
        step.id = snapshot_data.get('step_id')
        step.step_name = snapshot_data.get('step_name', '')
        step.step_order = snapshot_data.get('step_order', 0)
        step.action_type = snapshot_data.get('action_type')
        step.approver_type = snapshot_data.get('approver_type', 'user')
        step.approver_user_id = snapshot_data.get('approver_user_id')
        step.step_type = snapshot_data.get('step_type', 'normal')
        step.branch_condition = snapshot_data.get('branch_condition')
        step.action_params = snapshot_data.get('action_params')
        step.execution_condition = snapshot_data.get('execution_condition')
        step.process_id = process_id or snapshot_data.get('process_id')

        return step

    def is_branch_step(self):
        """判断是否为分支步骤"""
        return self.step_type == 'branch'

    def evaluate_execution_condition(self, target_object):
        """评估步骤执行条件，决定是否需要执行此步骤

        Returns:
            True  → 条件满足，执行此步骤
            False → 条件不满足，跳过此步骤
            None  → 无条件（未设置条件），正常执行
        """
        condition = self.execution_condition
        if not condition or not isinstance(condition, dict):
            return None  # 无条件，正常执行

        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')

        if not field or not operator:
            return None  # 配置不完整，视为无条件

        # 复用已有的字段值获取和条件评估方法
        object_value = self._get_object_field_value(target_object, field)
        return self._evaluate_condition(object_value, operator, value)

    def get_branch_conditions(self):
        """获取分支条件 - 统一使用新表数据"""
        from app.models.approval_branch_condition import ApprovalBranchCondition
        return ApprovalBranchCondition.get_step_conditions(self.id)
    
    def get_branch_field(self):
        """获取分支字段名"""
        if self.branch_condition:
            return self.branch_condition.get('field')
        return None
    
    def get_default_branch(self):
        """获取默认分支配置"""
        if self.branch_condition:
            return self.branch_condition.get('default_branch', {})
        return {}
    
    
    # 注意：原来的并行分支相关方法已移除，现在使用简化的分支链模式

    @property
    def action_type_label(self):
        """获取动作类型标签"""
        return ApprovalActionType.get_label(self.action_type) if self.action_type else ''

    def execute_action(self, approval_record, target_object, pricing_order_data=None):
        """执行审批动作"""
        from app.models.approval import ApprovalActionType

        if self.action_type == ApprovalActionType.QUOTATION_APPROVAL:
            return self._execute_quotation_approval(approval_record, target_object)
        elif self.action_type == ApprovalActionType.AUTHORIZATION:
            return self._execute_authorization(approval_record, target_object)
        elif self.action_type == ApprovalActionType.PAYMENT_PROCESSING:
            return self._execute_payment_processing(approval_record, target_object)
        elif self.action_type == ApprovalActionType.PROJECT_AUTHORIZATION:
            return self._execute_project_authorization(approval_record, target_object)
        elif self.action_type == ApprovalActionType.CHANNEL_AUTHORIZATION:
            return self._execute_channel_authorization(approval_record, target_object)
        elif self.action_type == ApprovalActionType.BUSINESS_AUTHORIZATION:
            return self._execute_business_authorization(approval_record, target_object)
        elif self.action_type == ApprovalActionType.CUSTOMER_SERVICE_AUTHORIZATION:
            return self._execute_customer_service_authorization(approval_record, target_object)
        elif self.action_type == ApprovalActionType.BRANCH_DECISION:
            return self._execute_branch_decision(approval_record, target_object)
        elif self.action_type == ApprovalActionType.PRICING_SETTLEMENT_APPROVAL:
            return self._execute_pricing_settlement_approval(approval_record, target_object, pricing_order_data)
        elif self.action_type == ApprovalActionType.PRODUCT_WAREHOUSING:
            return self._execute_product_warehousing(approval_record, target_object)

        return True

    def evaluate_branch_condition(self, target_object):
        """评估分支条件 - 统一使用新表数据"""
        if self.step_type != 'branch' and self.action_type != 'branch_decision':
            return None
        
        # 直接从新表获取所有分支条件
        from app.models.approval_branch_condition import ApprovalBranchCondition
        conditions = ApprovalBranchCondition.get_step_conditions(self.id)

        if not conditions:
            return None

        # 获取字段名（从JSON配置或使用默认值）
        field_name = self.get_branch_field() or 'project_type'
        
        try:
            # 获取目标对象的字段值
            object_value = self._get_object_field_value(target_object, field_name)
            
            # 按顺序评估每个条件，返回第一个匹配的条件配置
            for index, condition in enumerate(conditions):
                operator = condition.operator
                value = condition.field_value

                if not operator:
                    continue

                # 执行条件判断
                result = self._evaluate_condition(object_value, operator, value)

                if result:
                    # 返回匹配的条件配置（包含审批人和动作信息）
                    return {
                        'matched': True,
                        'condition_index': index,
                        'condition': condition,
                        'approver_id': condition.approver_id,
                        'approver_type': condition.approver_type or 'user',
                        'action': condition.action,
                        'next_step_order': None
                    }
            
            # 如果没有条件匹配，返回默认分支
            default_branch = self.get_default_branch()
            return {
                'matched': False,
                'condition_index': -1,
                'condition': default_branch,
                'approver_id': default_branch.get('approver_id'),
                'approver_type': default_branch.get('approver_type'),
                'action': default_branch.get('action'),
                'next_step_order': default_branch.get('next_step_order')
            }
            
        except Exception as e:
            current_app.logger.error(f"分支条件评估异常: {str(e)}")
            return None
    
    
    def _get_object_field_value(self, target_object, field):
        """获取目标对象的字段值"""

        # 特殊处理：批价单的 project_type 字段
        if field == 'project_type' and hasattr(target_object, 'quotation'):
            if target_object.quotation and hasattr(target_object.quotation, 'project_type'):
                result = target_object.quotation.project_type
                return result
            elif hasattr(target_object, 'project') and target_object.project and hasattr(target_object.project, 'project_type'):
                # 后备方案：如果没有报价单，从关联项目获取
                result = target_object.project.project_type
                return result
        
        try:
            # 支持点分隔的嵌套字段访问，如 project.project_type
            if '.' in field:
                parts = field.split('.')
                value = target_object

                for i, part in enumerate(parts):
                    if value is None:
                        break

                    # 支持方法调用，如 get_status()
                    if part.endswith('()'):
                        method_name = part[:-2]
                        if hasattr(value, method_name):
                            value = getattr(value, method_name)()
                        else:
                            return None
                    else:
                        # 普通属性访问
                        if hasattr(value, part):
                            value = getattr(value, part)
                        else:
                            return None

                return value
            else:
                # 支持方法调用
                if field.endswith('()'):
                    method_name = field[:-2]
                    if hasattr(target_object, method_name):
                        result = getattr(target_object, method_name)()
                        return result
                    else:
                        return None
                else:
                    # 普通属性访问
                    if hasattr(target_object, field):
                        result = getattr(target_object, field, None)
                        return result
                    else:
                        return None
        except (AttributeError, TypeError) as e:
            return None
    
    def _evaluate_condition(self, object_value, operator, condition_value):
        """评估条件表达式"""

        if object_value is None:
            result = operator in ['is_null', 'is_empty']
            return result
            
        # 字符串化处理
        obj_str = str(object_value)
        cond_str = str(condition_value)
        
        try:
            if operator == 'equals':
                # 增强equals逻辑：如果条件值包含逗号，自动转换为多值匹配逻辑
                if ',' in cond_str:
                    values = [v.strip() for v in cond_str.split(',')]
                    result = self._check_multi_value_match(obj_str, values)
                    return result
                else:
                    result = obj_str == cond_str
                    return result
            elif operator == 'not_equals':
                return obj_str != cond_str
            elif operator == 'contains':
                return cond_str.lower() in obj_str.lower()
            elif operator == 'not_contains':
                return cond_str.lower() not in obj_str.lower()
            elif operator == 'starts_with':
                return obj_str.lower().startswith(cond_str.lower())
            elif operator == 'ends_with':
                return obj_str.lower().endswith(cond_str.lower())
            elif operator == 'in':
                # 增强的多值匹配
                values = [v.strip() for v in cond_str.split(',')]
                result = self._check_multi_value_match(obj_str, values)
                return result
            elif operator == 'not_in':
                values = [v.strip() for v in cond_str.split(',')]
                return obj_str not in values
            elif operator == 'greater_than':
                return self._compare_numeric(object_value, condition_value, '>')
            elif operator == 'less_than':
                return self._compare_numeric(object_value, condition_value, '<')
            elif operator == 'greater_equal':
                return self._compare_numeric(object_value, condition_value, '>=')
            elif operator == 'less_equal':
                return self._compare_numeric(object_value, condition_value, '<=')
            elif operator == 'is_null':
                return object_value is None
            elif operator == 'is_not_null':
                return object_value is not None
            elif operator == 'is_empty':
                return not obj_str or obj_str.strip() == ''
            elif operator == 'is_not_empty':
                return bool(obj_str and obj_str.strip())
            elif operator == 'regex_match':
                return bool(re.search(cond_str, obj_str, re.IGNORECASE))
            else:
                return False
        except Exception as e:
            return False
    
    def _check_multi_value_match(self, object_value, condition_values):
        """
        检查多值匹配，支持字典映射

        Args:
            object_value: 对象的实际值
            condition_values: 条件值列表

        Returns:
            bool: 是否匹配
        """

        # 直接匹配
        if object_value in condition_values:
            return True

        # 字典映射匹配（project_type等枚举字段）
        try:
            from app.utils.field_value_helper import get_project_type_mapping
            mapping = get_project_type_mapping()

            # 检查英文值 -> 中文值映射
            mapped_value = mapping.get(object_value)
            if mapped_value and mapped_value in condition_values:
                return True

            # 检查中文值 -> 英文值的反向映射
            reverse_mapping = {v: k for k, v in mapping.items()}
            for cond_value in condition_values:
                if cond_value in reverse_mapping and reverse_mapping[cond_value] == object_value:
                    return True

        except Exception as e:
            pass

        return False
    
    def _compare_numeric(self, value1, value2, operator):
        """数值比较"""
        try:
            num1 = float(value1)
            num2 = float(value2)
            
            if operator == '>':
                return num1 > num2
            elif operator == '<':
                return num1 < num2
            elif operator == '>=':
                return num1 >= num2
            elif operator == '<=':
                return num1 <= num2
            else:
                return False
        except (ValueError, TypeError):
            # 如果不能转换为数值，进行字符串比较
            str1 = str(value1)
            str2 = str(value2)
            
            if operator == '>':
                return str1 > str2
            elif operator == '<':
                return str1 < str2
            elif operator == '>=':
                return str1 >= str2
            elif operator == '<=':
                return str1 <= str2
            else:
                return False

    def get_branch_result(self, condition_result):
        """根据条件结果获取分支配置"""
        if not self.branch_condition:
            return None
            
        branch_key = 'true_branch' if condition_result else 'false_branch'
        return self.branch_condition.get(branch_key)
    
    def get_next_branch_step(self, condition_result):
        """获取下一个分支步骤（如果分支结果指向next_branch）"""
        branch_result = self.get_branch_result(condition_result)
        if not branch_result or branch_result.get('approver_type') != 'next_branch':
            return None
        
        # 查找模板中下一个分支步骤
        next_steps = ApprovalStep.query.filter(
            ApprovalStep.process_id == self.process_id,
            ApprovalStep.step_order > self.step_order,
            ApprovalStep.step_type == 'branch'
        ).order_by(ApprovalStep.step_order.asc()).all()
        
        return next_steps[0] if next_steps else None
    
    def should_continue_to_next_branch(self, condition_result):
        """判断是否应该继续到下一个分支步骤"""
        branch_result = self.get_branch_result(condition_result)
        return branch_result and branch_result.get('approver_type') == 'next_branch'

    def _execute_quotation_approval(self, approval_record, quotation):
        """执行报价审核动作"""
        try:
            # 获取当前项目阶段
            if not quotation.project or not quotation.project.current_stage:
                return False
            
            current_stage = quotation.project.current_stage
            
            # 检查是否可以审核该阶段
            if not quotation.can_approve_for_stage(current_stage):
                return False
            
            # 添加审核记录
            action = 'approve' if approval_record.action == 'approve' else 'reject'
            quotation.add_approval_record(
                stage=current_stage,
                approver_id=approval_record.approver_id,
                action=action,
                comment=approval_record.comment
            )
            
            return True
        except Exception as e:
            return False

    def _execute_authorization(self, approval_record, project):
        """执行授权动作"""
        try:
            # 现有的授权逻辑
            from app.utils.authorization import generate_authorization_code
            
            if approval_record.action == 'approve':
                if not project.authorization_code:
                    project.authorization_code = generate_authorization_code(project.project_type)
                project.authorization_status = 'approved'
            else:
                project.authorization_status = 'rejected'
                
            return True
        except Exception as e:
            return False

    def _execute_payment_processing(self, approval_record, target_object):
        """执行支付处理动作"""
        try:
            # 目前主要支持报销单的支付处理
            if target_object.__class__.__name__ == 'Expense':
                return self._process_expense_payment(approval_record, target_object)
            else:
                # 其他对象类型的支付处理可以在此扩展
                return True
        except Exception as e:
            return False

    def _process_expense_payment(self, approval_record, expense):
        """处理报销单支付"""
        from app.utils.time_utils import get_local_time
        
        if approval_record.action == 'approve':
            # 确认支付
            expense.status = 'paid'
            if hasattr(expense, 'payment_status'):
                expense.payment_status = 'paid'
            if hasattr(expense, 'payment_date'):
                expense.payment_date = get_local_time()
            if hasattr(expense, 'paid_by'):
                expense.paid_by = approval_record.approver_id
            
            # 从评论中解析支付信息（如果有的话）
            if approval_record.comment:
                payment_info = self._parse_payment_info(approval_record.comment)
                if hasattr(expense, 'payment_amount') and payment_info.get('amount'):
                    expense.payment_amount = float(payment_info['amount'])
                if hasattr(expense, 'payment_method') and payment_info.get('method'):
                    expense.payment_method = payment_info['method']
                if hasattr(expense, 'payment_reference') and payment_info.get('reference'):
                    expense.payment_reference = payment_info['reference']
                if hasattr(expense, 'payment_notes') and payment_info.get('notes'):
                    expense.payment_notes = payment_info['notes']
        else:
            # 拒绝支付，转回待支付状态
            expense.status = 'awaiting_payment'
            if hasattr(expense, 'payment_status'):
                expense.payment_status = 'awaiting'
        
        return True

    def _parse_payment_info(self, comment):
        """从评论中解析支付信息"""
        try:
            # 尝试解析JSON格式的支付信息
            return json.loads(comment)
        except (json.JSONDecodeError, ValueError):
            # 如果不是JSON格式，返回空字典
            return {}

    def _execute_project_authorization(self, approval_record, project):
        """执行项目授权动作"""
        try:
            from app.utils.authorization import generate_project_authorization_code
            
            if approval_record.action == 'approve':
                if not project.authorization_code:
                    project.authorization_code = generate_project_authorization_code(
                        project.project_type, 
                        project.id,
                        approval_record.approver_id
                    )
                project.authorization_status = 'approved'
                project.authorization_type = 'project'

                # 授权通过后更新报备时间为当前日期
                project.report_time = date.today()
            else:
                project.authorization_status = 'rejected'

            # 提交数据库事务
            db.session.commit()

            return True
        except Exception as e:
            return False

    def _execute_channel_authorization(self, approval_record, project):
        """执行渠道授权动作"""
        try:

            # 添加日志记录
            current_app.logger.info(f"[CHANNEL_AUTH] 执行渠道授权 - 项目ID:{project.id}, 类型:{project.project_type}")

            from app.utils.authorization import generate_channel_authorization_code

            if approval_record.action == 'approve':
                if not project.authorization_code:
                    # 生成授权编码
                    authorization_code = generate_channel_authorization_code(
                        project.project_type,
                        project.id,
                        approval_record.approver_id
                    )

                    # 赋值给项目
                    project.authorization_code = authorization_code

                project.authorization_status = 'approved'
                project.authorization_type = 'channel'
                # 授权通过后更新报备时间为当前日期
                project.report_time = date.today()

            else:
                project.authorization_status = 'rejected'

            # 提交数据库事务
            db.session.commit()

            # 验证是否真的保存了
            db.session.refresh(project)

            return True
        except Exception as e:
            return False

    def _execute_business_authorization(self, approval_record, project):
        """执行业务授权动作（向后兼容，重定向到客服授权）"""
        try:
            return self._execute_customer_service_authorization(approval_record, project)
        except Exception as e:
            return False

    def _execute_customer_service_authorization(self, approval_record, project):
        """执行客服授权动作"""
        try:
            from app.utils.authorization import generate_customer_service_authorization_code
            
            if approval_record.action == 'approve':
                if not project.authorization_code:
                    project.authorization_code = generate_customer_service_authorization_code(
                        project.project_type,
                        project.id,
                        approval_record.approver_id  
                    )
                project.authorization_status = 'approved'
                project.authorization_type = 'customer_service'
                
                # 授权通过后更新报备时间为当前日期
                project.report_time = date.today()
            else:
                project.authorization_status = 'rejected'

            # 提交数据库事务
            db.session.commit()

            return True
        except Exception as e:
            return False

    def _execute_branch_decision(self, approval_record, target_object):
        """执行分支决策动作"""
        try:
            # 分支决策步骤主要用于条件判断，确定下一步的流程走向

            # 评估分支条件
            condition_result = self.evaluate_branch_condition(target_object)

            if condition_result is None:
                return False
            
            # 处理新的多条件格式返回结果
            if isinstance(condition_result, dict) and 'matched' in condition_result:
                # 新的多条件格式，直接使用返回的配置
                branch_result = {
                    'approver_id': condition_result.get('approver_id'),
                    'approver_type': condition_result.get('approver_type'),
                    'action': condition_result.get('action')
                }
            else:
                # 兼容旧的单条件格式
                branch_result = self.get_branch_result(condition_result)
                if not branch_result:
                    return False
            
            # 记录分支决策结果
            self._record_branch_decision(approval_record, condition_result, branch_result)
            
            # 检查是否需要跳转到下一个分支
            if branch_result.get('approver_type') == 'next_branch':
                next_branch_step = self.get_next_branch_step(condition_result)
                if next_branch_step:
                    # 递归执行下一个分支步骤
                    return next_branch_step._execute_branch_decision(approval_record, target_object)
                else:
                    return True
            
            # 如果分支结果中指定了动作，执行对应动作
            if branch_result.get('action'):
                action_type = branch_result.get('action')

                temp_step = type(self)()
                temp_step.action_type = action_type
                temp_step.action_params = branch_result.get('action_params', {})

                result = temp_step.execute_action(approval_record, target_object)
                
                return result
            
            return True
        except Exception as e:
            return False
    
    def _record_branch_decision(self, approval_record, condition_result, branch_result):
        """记录分支决策结果"""
        try:
            # 在审批记录的评论中记录分支决策信息
            decision_info = {
                'branch_condition': self.branch_condition,
                'condition_result': condition_result,
                'selected_branch': 'true_branch' if condition_result else 'false_branch',
                'branch_config': branch_result
            }
            
            if approval_record.comment:
                approval_record.comment += f"\n\n[分支决策] {decision_info}"
            else:
                approval_record.comment = f"[分支决策] {decision_info}"
                
        except Exception as e:
            pass
    
    def _execute_pricing_settlement_approval(self, approval_record, pricing_order, pricing_order_data=None):
        """执行批结算审批 - 接收外部页面数据并保存到数据库"""
        try:
            from app.services.pricing_order_service import PricingOrderService
            
            
            current_app.logger.info(f"批结算审批 - 动作开始执行，批价单ID: {pricing_order.id}")
            current_app.logger.info(f"批结算审批 - 接收到的数据: {pricing_order_data}")
            current_app.logger.info(f"批结算审批 - 数据类型: {type(pricing_order_data)}")
            
            approver = User.query.get(approval_record.approver_id)
            if not approver:
                current_app.logger.error(f"批结算审批失败：找不到审批人 {approval_record.approver_id}")
                return False
            
            
            # 如果有外部传递的批价单数据，保存到数据库
            if pricing_order_data:
                current_app.logger.info(f"批结算审批 - 开始保存外部页面数据: {pricing_order_data}")
                
                
                # 使用成熟的核心保存逻辑 - 修复函数签名
                service = PricingOrderService()
                from flask_login import current_user
                success, message = service.save_pricing_order_core_data(pricing_order.id, pricing_order_data, current_user)


                if not success:
                    current_app.logger.error(f"批结算审批 - 保存批价单数据失败: {message}")
                    return False
                    
                current_app.logger.info("批结算审批 - 批价单数据保存成功")
            else:
                current_app.logger.warning("批结算审批 - 没有外部页面数据传递，跳过数据保存")
                current_app.logger.info(f"批结算审批 - 当前批价单折扣率: {pricing_order.pricing_total_discount_rate}")
            
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"执行批结算审批动作失败: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return False
    
    def _get_approval_request_data(self, approval_record):
        """从审批记录中获取前端提交的数据
        
        解析approval_record.frontend_data中的JSON数据，返回标准格式的请求数据
        """
        try:
            
            # 从frontend_data中解析数据
            if approval_record.frontend_data:
                data = json.loads(approval_record.frontend_data)
                
                # 转换为标准的请求数据格式
                request_data = {}
                
                # 基本信息字段
                for field in ['company_name', 'contact_person', 'contact_phone', 'remarks', 
                             'dealer_id', 'distributor_id', 'factory_pickup', 'total_discount_rate']:
                    if field in data:
                        request_data[field] = data[field]
                
                # 明细数据处理
                if 'details' in data:
                    request_data['details'] = data['details']
                elif 'table_data' in data and data['table_data']:
                    # 兼容不同的前端数据格式
                    request_data['details'] = data['table_data']
                else:
                    request_data['details'] = []
                
                return request_data
            
            # 如果没有frontend_data，返回空的请求数据
            return {'details': []}
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return {'details': []}

    def _execute_product_warehousing(self, approval_record, dev_product):
        """执行研发产品入库动作

        DEPRECATED (2025-12-26): 研发库功能已废弃，此方法不再执行实际操作。
        保留此方法是为了兼容历史审批记录，避免审批流程执行时报错。

        Args:
            approval_record: 审批记录对象
            dev_product: 研发产品对象 (DevProduct)

        Returns:
            bool: 始终返回 True
        """
        current_app.logger.warning(
            f"[DEPRECATED] 研发产品入库功能已废弃，跳过执行。"
            f"DevProduct#{dev_product.id if dev_product else 'N/A'}, "
            f"ApprovalRecord#{approval_record.id if approval_record else 'N/A'}"
        )
        return True


class ApprovalInstance(db.Model):
    """流程实例"""
    __tablename__ = "approval_instance"

    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey("approval_process_template.id"), nullable=False, comment="流程模板ID")
    object_id = db.Column(db.Integer, nullable=False, comment="对应单据ID")
    object_type = db.Column(db.String(50), nullable=False, comment="单据类型（如 project）")
    current_step = db.Column(db.Integer, default=1, comment="当前步骤序号")
    status = db.Column(db.Enum(ApprovalStatus), default=ApprovalStatus.PENDING, comment="状态")
    started_at = db.Column(db.DateTime, default=get_local_time, comment="流程发起时间")
    ended_at = db.Column(db.DateTime, comment="审批完成时间")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="发起人ID")
    
    # 新增：模板版本化字段
    template_snapshot = db.Column(db.JSON, comment="创建时的模板快照")
    template_version = db.Column(db.String(50), comment="模板版本号")

    # 关联关系
    process = db.relationship("ApprovalProcessTemplate")
    creator = db.relationship("User", backref="created_approvals")
    records = db.relationship("ApprovalRecord", backref="instance", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ApprovalInstance {self.id} - {self.object_type}:{self.object_id}>"
    
    def get_steps(self):
        """获取审批步骤 - 优先使用快照"""
        if self.template_snapshot and 'steps' in self.template_snapshot:
            # 使用创建时的快照
            return self.template_snapshot['steps']
        else:
            # 回退到当前模板（兼容旧数据）
            return ApprovalStep.query.filter_by(
                process_id=self.process_id
            ).order_by(ApprovalStep.step_order.asc()).all()
    
    def get_current_step_info(self):
        """获取当前步骤信息

        current_step 可能存储 step_order（正常情况）或 step_id（历史数据/重新提交场景）
        优先按 step_order 匹配，如果匹配不到则按 step_id 匹配
        """
        steps = self.get_steps()
        if isinstance(steps, list) and len(steps) > 0:
            # 快照数据（字典列表）
            if isinstance(steps[0], dict):
                # 优先按 step_order 匹配
                for step in steps:
                    if step.get('step_order') == self.current_step:
                        return step
                # 如果 step_order 匹配不到，尝试按 step_id 匹配（兼容历史数据）
                for step in steps:
                    if step.get('step_id') == self.current_step:
                        return step
            # 模型对象列表
            else:
                # 优先按 step_order 匹配
                for step in steps:
                    if step.step_order == self.current_step:
                        return step
                # 如果 step_order 匹配不到，尝试按 step_id 匹配（兼容历史数据）
                for step in steps:
                    if step.id == self.current_step:
                        return step
        return None
    
    def get_template_info(self):
        """获取模板信息"""
        if self.template_snapshot:
            return {
                'name': self.template_snapshot.get('template_name', ''),
                'version': self.template_version,
                'created_at': self.template_snapshot.get('created_at', ''),
                'is_snapshot': True
            }
        else:
            return {
                'name': self.process.name if self.process else '',
                'version': 'current',
                'created_at': '',
                'is_snapshot': False
            }


class ApprovalRecord(db.Model):
    """审批记录"""
    __tablename__ = "approval_record"

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.Integer, db.ForeignKey("approval_instance.id"), nullable=False, comment="审批流程实例")
    step_id = db.Column(db.Integer, db.ForeignKey("approval_step.id"), nullable=True, comment="流程步骤ID（模板快照时可为NULL）")
    approver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="审批人ID")
    action = db.Column(db.String(50), nullable=False, comment="同意/拒绝")
    comment = db.Column(db.Text, comment="审批意见")
    timestamp = db.Column(db.DateTime, default=get_local_time, comment="审批时间")

    # 关联关系
    step = db.relationship("ApprovalStep")
    approver = db.relationship("User", backref="approval_records")

    def __repr__(self):
        return f"<ApprovalRecord {self.id} - {self.action}>"


class ApprovalExternalToken(db.Model):
    """
    审批外部访问令牌

    用于允许外部人员（无需登录）访问特定的审批步骤表单。
    适用场景：
    - 供应商的工厂测试人员访问测试表单
    - 外部验收人员访问验收表单

    访问链接格式: /approval/external/{token}
    """
    __tablename__ = "approval_external_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True, comment="访问令牌（32字符hex）")

    # 关联信息
    step_id = db.Column(db.Integer, db.ForeignKey("approval_step.id"), nullable=True, comment="关联审批步骤模板ID")
    instance_id = db.Column(db.Integer, db.ForeignKey("approval_instance.id"), nullable=True, comment="关联审批实例ID")
    object_type = db.Column(db.String(50), nullable=False, comment="对象类型（purchase_order等）")
    object_id = db.Column(db.Integer, nullable=False, comment="对象ID")

    # 表单信息
    form_id = db.Column(db.String(50), nullable=True, comment="表单模板ID（factory_test_form等）")

    # 有效期控制
    expires_at = db.Column(db.DateTime, nullable=False, comment="过期时间")
    max_uses = db.Column(db.Integer, default=1, comment="最大使用次数（0=无限制）")
    use_count = db.Column(db.Integer, default=0, comment="已使用次数")

    # 使用记录
    used_at = db.Column(db.DateTime, nullable=True, comment="最后使用时间")
    used_ip = db.Column(db.String(50), nullable=True, comment="最后使用IP")
    submitted_at = db.Column(db.DateTime, nullable=True, comment="表单提交时间")

    # 提交人信息（外部人员无账号，记录姓名）
    submitted_by_name = db.Column(db.String(100), nullable=True, comment="提交人姓名")

    # 元数据
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = db.Column(db.DateTime, default=get_local_time, comment="创建时间")
    notes = db.Column(db.Text, nullable=True, comment="备注说明")

    # 关系
    step = db.relationship("ApprovalStep", backref="external_tokens")
    instance = db.relationship("ApprovalInstance", backref="external_tokens")
    created_by = db.relationship("User", backref="created_external_tokens")

    def __repr__(self):
        return f"<ApprovalExternalToken {self.token[:8]}...>"

    @property
    def is_valid(self):
        """检查令牌是否有效"""
        from datetime import datetime
        now = datetime.now()

        # 检查是否过期
        if self.expires_at and now > self.expires_at:
            return False

        # 检查使用次数
        if self.max_uses > 0 and self.use_count >= self.max_uses:
            return False

        # 检查是否已提交
        if self.submitted_at:
            return False

        return True

    @property
    def status(self):
        """获取令牌状态"""
        if self.submitted_at:
            return 'submitted'
        if not self.is_valid:
            return 'expired'
        return 'active'

    @property
    def status_label(self):
        """状态标签"""
        labels = {
            'active': '有效',
            'expired': '已过期',
            'submitted': '已提交'
        }
        return labels.get(self.status, self.status)

    @classmethod
    def generate_token(cls):
        """生成随机令牌"""
        import secrets
        return secrets.token_hex(16)  # 32字符的hex字符串

    @classmethod
    def create_token(cls, object_type, object_id, form_id, created_by_id,
                     step_id=None, instance_id=None, expires_hours=72, max_uses=1, notes=None):
        """
        创建外部访问令牌

        Args:
            object_type: 对象类型
            object_id: 对象ID
            form_id: 表单模板ID
            created_by_id: 创建人ID
            step_id: 审批步骤ID（可选）
            instance_id: 审批实例ID（可选）
            expires_hours: 有效期小时数（默认72小时）
            max_uses: 最大使用次数（默认1次）
            notes: 备注说明

        Returns:
            ApprovalExternalToken: 创建的令牌对象
        """
        from datetime import datetime, timedelta

        token = cls(
            token=cls.generate_token(),
            object_type=object_type,
            object_id=object_id,
            form_id=form_id,
            step_id=step_id,
            instance_id=instance_id,
            expires_at=datetime.now() + timedelta(hours=expires_hours),
            max_uses=max_uses,
            created_by_id=created_by_id,
            notes=notes
        )

        db.session.add(token)
        db.session.flush()

        return token

    def record_access(self, ip_address=None):
        """记录访问"""
        from datetime import datetime
        self.use_count += 1
        self.used_at = datetime.now()
        if ip_address:
            self.used_ip = ip_address

    def mark_submitted(self, submitter_name=None):
        """标记为已提交"""
        from datetime import datetime
        self.submitted_at = datetime.now()
        if submitter_name:
            self.submitted_by_name = submitter_name