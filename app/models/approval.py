from datetime import datetime
from enum import Enum
from app import db
from app.models.user import User


class ApprovalStatus(Enum):
    """审批状态枚举"""
    PENDING = "pending"    # 审批中
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝


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
    
    # 动作类型标签
    ACTION_TYPE_LABELS = {
        'authorization': {'zh': '授权审批', 'en': 'Authorization'},
        'quotation_approval': {'zh': '报价审核', 'en': 'Quotation Approval'},
        'email_cc': {'zh': '邮件抄送', 'en': 'Email CC'}
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
    created_at = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
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

    # 关联关系
    approver = db.relationship("User", backref="approval_steps")

    def __repr__(self):
        return f"<ApprovalStep {self.step_name}>"

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
        return True

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


class ApprovalInstance(db.Model):
    """流程实例"""
    __tablename__ = "approval_instance"

    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey("approval_process_template.id"), nullable=False, comment="流程模板ID")
    object_id = db.Column(db.Integer, nullable=False, comment="对应单据ID")
    object_type = db.Column(db.String(50), nullable=False, comment="单据类型（如 project）")
    current_step = db.Column(db.Integer, default=1, comment="当前步骤序号")
    status = db.Column(db.Enum(ApprovalStatus), default=ApprovalStatus.PENDING, comment="状态")
    started_at = db.Column(db.DateTime, default=datetime.now, comment="流程发起时间")
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
                    if step.get('step_order') == self.current_step:
                        return step
            # 模型对象列表
            else:
                for step in steps:
                    if step.step_order == self.current_step:
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
    timestamp = db.Column(db.DateTime, default=datetime.now, comment="审批时间")

    # 关联关系
    step = db.relationship("ApprovalStep")
    approver = db.relationship("User", backref="approval_records")

    def __repr__(self):
        return f"<ApprovalRecord {self.id} - {self.action}>" 