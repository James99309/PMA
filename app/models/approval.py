from datetime import datetime
from zoneinfo import ZoneInfo
from enum import Enum
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
    BUSINESS_AUTHORIZATION = "business_authorization"  # 业务授权
    
    # 新增：分支动作
    BRANCH_DECISION = "branch_decision"  # 分支决策
    
    # 新增：批价审批动作
    PRICING_APPROVAL = "pricing_approval"  # 批价单审批（包含批价单和结算单权限检查）
    
    # 动作类型标签
    ACTION_TYPE_LABELS = {
        'authorization': {'zh': '授权审批', 'en': 'Authorization'},
        'quotation_approval': {'zh': '报价审核', 'en': 'Quotation Approval'},
        'email_cc': {'zh': '邮件抄送', 'en': 'Email CC'},
        'payment_processing': {'zh': '支付处理', 'en': 'Payment Processing'},
        'project_authorization': {'zh': '项目授权', 'en': 'Project Authorization'},
        'channel_authorization': {'zh': '渠道授权', 'en': 'Channel Authorization'},
        'business_authorization': {'zh': '业务授权', 'en': 'Business Authorization'},
        'branch_decision': {'zh': '分支决策', 'en': 'Branch Decision'},
        'pricing_approval': {'zh': '批价审批', 'en': 'Pricing Approval'}
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
    branch_condition = db.Column(db.JSON, nullable=True, comment="分支条件配置")
    
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

    def is_branch_step(self):
        """判断是否为分支步骤"""
        return self.step_type == 'branch'
    
    # 注意：原来的并行分支相关方法已移除，现在使用简化的分支链模式

    @property
    def action_type_label(self):
        """获取动作类型标签"""
        return ApprovalActionType.get_label(self.action_type) if self.action_type else ''

    def execute_action(self, approval_record, target_object):
        """执行审批动作"""
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
        elif self.action_type == ApprovalActionType.BRANCH_DECISION:
            return self._execute_branch_decision(approval_record, target_object)
        elif self.action_type == ApprovalActionType.PRICING_APPROVAL:
            return self._execute_pricing_approval(approval_record, target_object)
        return True

    def evaluate_branch_condition(self, target_object):
        """评估分支条件"""
        if not self.branch_condition or self.step_type != 'branch':
            return None
            
        condition = self.branch_condition
        
        # 检查是否为新的多条件格式
        if 'conditions' in condition and isinstance(condition['conditions'], list):
            return self._evaluate_multiple_conditions(target_object, condition)
        else:
            # 兼容旧的单条件格式
            return self._evaluate_single_condition(target_object, condition)
    
    def _evaluate_multiple_conditions(self, target_object, branch_config):
        """评估多个分支条件，按顺序处理，返回第一个匹配的条件"""
        field = branch_config.get('field')
        conditions = branch_config.get('conditions', [])
        
        if not field or not conditions:
            print(f"多条件配置不完整: field={field}, conditions count={len(conditions)}")
            return None
            
        try:
            # 获取目标对象的字段值
            object_value = self._get_object_field_value(target_object, field)
            print(f"多条件评估: 字段={field}, 对象值={object_value}, 条件数量={len(conditions)}")
            
            # 按顺序评估每个条件，返回第一个匹配的条件配置
            for index, condition in enumerate(conditions):
                operator = condition.get('operator')
                value = condition.get('value')
                
                if not operator:
                    print(f"条件{index+1}配置不完整: operator={operator}")
                    continue
                    
                # 执行条件判断
                result = self._evaluate_condition(object_value, operator, value)
                print(f"条件{index+1}评估结果: {result} (operator={operator}, value={value})")
                
                if result:
                    print(f"✅ 匹配到条件{index+1}，停止后续条件评估")
                    # 返回匹配的条件配置（包含审批人和动作信息）
                    return {
                        'matched': True,
                        'condition_index': index,
                        'condition': condition,
                        'approver_id': condition.get('approver_id'),
                        'approver_type': condition.get('approver_type'),
                        'action': condition.get('action'),
                        'next_step_order': condition.get('next_step_order')
                    }
            
            # 如果没有条件匹配，返回默认分支
            print("❌ 没有条件匹配，使用默认分支")
            default_branch = branch_config.get('default_branch', {})
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
            print(f"多条件评估异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _evaluate_single_condition(self, target_object, condition):
        """评估单个分支条件（兼容旧格式）"""
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        if not field or not operator:
            print(f"单条件配置不完整: field={field}, operator={operator}")
            return None
            
        try:
            # 获取目标对象的字段值
            object_value = self._get_object_field_value(target_object, field)
            print(f"单条件评估: 字段={field}, 对象值={object_value}, 操作符={operator}, 条件值={value}")
            
            # 执行条件判断
            result = self._evaluate_condition(object_value, operator, value)
            print(f"单条件评估结果: {result}")
            return result
        except Exception as e:
            print(f"单条件评估异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_object_field_value(self, target_object, field):
        """获取目标对象的字段值"""
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
                            print(f"方法 {method_name} 不存在于对象 {type(value)}")
                            return None
                    else:
                        # 普通属性访问
                        if hasattr(value, part):
                            value = getattr(value, part)
                        else:
                            print(f"属性 {part} 不存在于对象 {type(value)} (路径: {'.'.join(parts[:i+1])})")
                            return None
                return value
            else:
                # 支持方法调用
                if field.endswith('()'):
                    method_name = field[:-2]
                    if hasattr(target_object, method_name):
                        return getattr(target_object, method_name)()
                    else:
                        print(f"方法 {method_name} 不存在于对象 {type(target_object)}")
                        return None
                else:
                    # 普通属性访问
                    return getattr(target_object, field, None)
        except (AttributeError, TypeError) as e:
            print(f"获取字段值失败: field={field}, error={str(e)}")
            return None
    
    def _evaluate_condition(self, object_value, operator, condition_value):
        """评估条件表达式"""
        if object_value is None:
            return operator in ['is_null', 'is_empty']
            
        # 字符串化处理
        obj_str = str(object_value)
        cond_str = str(condition_value)
        
        try:
            if operator == 'equals':
                return obj_str == cond_str
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
                # 支持逗号分隔的多值匹配
                values = [v.strip() for v in cond_str.split(',')]
                return obj_str in values
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
                import re
                return bool(re.search(cond_str, obj_str, re.IGNORECASE))
            else:
                print(f"不支持的操作符: {operator}")
                return False
        except Exception as e:
            print(f"条件评估异常: operator={operator}, object_value={object_value}, condition_value={condition_value}, error={str(e)}")
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
            print(f"执行报价审核动作失败: {str(e)}")
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
            print(f"执行授权动作失败: {str(e)}")
            return False

    def _execute_payment_processing(self, approval_record, target_object):
        """执行支付处理动作"""
        try:
            # 目前主要支持报销单的支付处理
            if target_object.__class__.__name__ == 'Expense':
                return self._process_expense_payment(approval_record, target_object)
            else:
                # 其他对象类型的支付处理可以在此扩展
                print(f"不支持的支付处理对象类型: {target_object.__class__.__name__}")
                return True
        except Exception as e:
            print(f"执行支付处理动作失败: {str(e)}")
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
            import json
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
            else:
                project.authorization_status = 'rejected'
                
            return True
        except Exception as e:
            print(f"执行项目授权动作失败: {str(e)}")
            return False

    def _execute_channel_authorization(self, approval_record, project):
        """执行渠道授权动作"""
        try:
            print(f"🔥 开始执行渠道授权动作")
            print(f"🔥 审批动作: {approval_record.action}")
            print(f"🔥 项目ID: {project.id}, 项目类型: {project.project_type}")
            print(f"🔥 当前授权编码: {project.authorization_code}")
            
            from app.utils.authorization import generate_channel_authorization_code
            
            if approval_record.action == 'approve':
                if not project.authorization_code:
                    print(f"🔥 开始生成授权编码...")
                    project.authorization_code = generate_channel_authorization_code(
                        project.project_type,
                        project.id, 
                        approval_record.approver_id
                    )
                    print(f"🔥 生成的授权编码: {project.authorization_code}")
                else:
                    print(f"🔥 项目已有授权编码，跳过生成")
                
                project.authorization_status = 'approved'
                project.authorization_type = 'channel'
                print(f"🔥 设置授权状态: approved, 类型: channel")
            else:
                project.authorization_status = 'rejected'
                print(f"🔥 设置授权状态: rejected")
                
            print(f"🔥 渠道授权动作执行成功")
            return True
        except Exception as e:
            print(f"🔥 执行渠道授权动作失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _execute_business_authorization(self, approval_record, project):
        """执行业务授权动作"""
        try:
            from app.utils.authorization import generate_business_authorization_code
            
            if approval_record.action == 'approve':
                if not project.authorization_code:
                    project.authorization_code = generate_business_authorization_code(
                        project.project_type,
                        project.id,
                        approval_record.approver_id  
                    )
                project.authorization_status = 'approved'
                project.authorization_type = 'business'
            else:
                project.authorization_status = 'rejected'
                
            return True
        except Exception as e:
            print(f"执行业务授权动作失败: {str(e)}")
            return False

    def _execute_branch_decision(self, approval_record, target_object):
        """执行分支决策动作"""
        try:
            # 分支决策步骤主要用于条件判断，确定下一步的流程走向
            
            # 评估分支条件
            condition_result = self.evaluate_branch_condition(target_object)
            if condition_result is None:
                print(f"分支条件评估失败，步骤ID: {self.id}")
                return False
            
            # 处理新的多条件格式返回结果
            if isinstance(condition_result, dict) and 'matched' in condition_result:
                # 新的多条件格式，直接使用返回的配置
                branch_result = {
                    'approver_id': condition_result.get('approver_id'),
                    'approver_type': condition_result.get('approver_type'),
                    'action': condition_result.get('action')
                }
                print(f"使用多条件结果: 匹配={condition_result.get('matched')}, 条件索引={condition_result.get('condition_index')}")
            else:
                # 兼容旧的单条件格式
                branch_result = self.get_branch_result(condition_result)
                if not branch_result:
                    print(f"未找到分支结果配置，条件结果: {condition_result}")
                    return False
            
            # 记录分支决策结果
            self._record_branch_decision(approval_record, condition_result, branch_result)
            
            # 检查是否需要跳转到下一个分支
            if branch_result.get('approver_type') == 'next_branch':
                next_branch_step = self.get_next_branch_step(condition_result)
                if next_branch_step:
                    print(f"跳转到下一个分支步骤: {next_branch_step.step_name}")
                    # 递归执行下一个分支步骤
                    return next_branch_step._execute_branch_decision(approval_record, target_object)
                else:
                    print(f"警告：未找到下一个分支步骤，将采用默认处理")
                    return True
            
            # 如果分支结果中指定了动作，执行对应动作
            if branch_result.get('action'):
                action_type = branch_result.get('action')
                print(f"🔥 分支决策: 准备执行动作 {action_type}")
                print(f"🔥 分支结果: {branch_result}")
                print(f"🔥 审批记录: action={approval_record.action}, approver_id={approval_record.approver_id}")
                print(f"🔥 目标对象: type={type(target_object).__name__}, id={getattr(target_object, 'id', 'N/A')}")
                
                temp_step = type(self)()
                temp_step.action_type = action_type
                temp_step.action_params = branch_result.get('action_params', {})
                
                print(f"🔥 创建临时步骤: action_type={temp_step.action_type}")
                
                result = temp_step.execute_action(approval_record, target_object)
                print(f"🔥 执行动作结果: {result}")
                
                return result
            
            return True
        except Exception as e:
            print(f"执行分支决策动作失败: {str(e)}")
            import traceback
            traceback.print_exc()
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
            print(f"记录分支决策失败: {str(e)}")
    
    def _execute_pricing_approval(self, approval_record, pricing_order):
        """执行批价单审批权限检查动作"""
        try:
            from app.models.user import User
            from app.permissions import get_role_permission
            
            approver = User.query.get(approval_record.approver_id)
            if not approver:
                print(f"批价审批失败：找不到审批人 {approval_record.approver_id}")
                return False
            
            # 获取审批人角色的权限下限配置
            role_permission = get_role_permission(approver.role, 'pricing_order')
            if not role_permission:
                print(f"批价审批失败：找不到角色权限配置 {approver.role}")
                return False
            
            pricing_limit = role_permission.pricing_discount_limit or 0
            settlement_limit = role_permission.settlement_discount_limit or 0
            
            # 检查批价单和结算单折扣率
            violations = []
            current_pricing_rate = (pricing_order.pricing_total_discount_rate or 1.0) * 100
            current_settlement_rate = (pricing_order.settlement_total_discount_rate or 1.0) * 100
            
            if current_pricing_rate < pricing_limit:
                violations.append(f"批价单折扣率{current_pricing_rate:.1f}%低于权限下限{pricing_limit}%")
            
            if settlement_limit > 0 and current_settlement_rate < settlement_limit:
                violations.append(f"结算单折扣率{current_settlement_rate:.1f}%低于权限下限{settlement_limit}%")
            
            # 如果有违规，在审批记录中标记
            if violations:
                violation_text = "; ".join(violations)
                warning_msg = f"[权限下限违规提醒] {violation_text}"
                
                if approval_record.comment:
                    approval_record.comment = f"{approval_record.comment}\n\n{warning_msg}"
                else:
                    approval_record.comment = warning_msg
                
                print(f"批价审批权限违规: {violation_text}")
            else:
                print("批价审批权限检查通过")
            
            return True
            
        except Exception as e:
            print(f"执行批价审批动作失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _execute_settlement_approval(self, approval_record, settlement_order):
        """执行结算单审批权限检查动作"""
        try:
            from app.models.user import User
            from app.permissions import get_role_permission
            
            approver = User.query.get(approval_record.approver_id)
            if not approver:
                print(f"结算审批失败：找不到审批人 {approval_record.approver_id}")
                return False
            
            # 获取审批人角色的权限下限配置
            role_permission = get_role_permission(approver.role, 'settlement_order')
            if not role_permission:
                print(f"结算审批失败：找不到角色权限配置 {approver.role}")
                return False
            
            settlement_limit = role_permission.settlement_discount_limit or 0
            
            # 检查结算单折扣率
            violations = []
            current_settlement_rate = (settlement_order.total_discount_rate or 1.0) * 100
            
            if settlement_limit > 0 and current_settlement_rate < settlement_limit:
                violations.append(f"结算单折扣率{current_settlement_rate:.1f}%低于权限下限{settlement_limit}%")
            
            # 如果有违规，在审批记录中标记
            if violations:
                violation_text = "; ".join(violations)
                warning_msg = f"[权限下限违规提醒] {violation_text}"
                
                if approval_record.comment:
                    approval_record.comment = f"{approval_record.comment}\n\n{warning_msg}"
                else:
                    approval_record.comment = warning_msg
                
                print(f"结算审批权限违规: {violation_text}")
            else:
                print("结算审批权限检查通过")
            
            return True
            
        except Exception as e:
            print(f"执行结算审批动作失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    # 注意：原来的子步骤查找方法已移除，现在使用分支链模式


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
        """获取当前步骤信息"""
        steps = self.get_steps()
        if isinstance(steps, list) and len(steps) > 0:
            # 快照数据（字典列表）
            if isinstance(steps[0], dict):
                for step in steps:
                    # 🔥 修复：current_step存储的是step_id，优先用step_id匹配
                    if step.get('step_id') == self.current_step:
                        return step
                    # 兼容性：如果没有step_id字段，回退到step_order匹配
                    elif 'step_id' not in step and step.get('step_order') == self.current_step:
                        return step
            # 模型对象列表
            else:
                for step in steps:
                    # 对于模型对象，current_step存储的是step_id
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