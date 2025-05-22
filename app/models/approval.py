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
    approver_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="审批人账号ID")
    step_name = db.Column(db.String(100), nullable=False, comment="步骤说明（如\"财务审批\"）")
    send_email = db.Column(db.Boolean, default=True, comment="是否发送邮件通知")
    action_type = db.Column(db.String(50), nullable=True, comment="步骤动作类型，如 authorization")
    action_params = db.Column(db.JSON, nullable=True, comment="动作参数，JSON格式")

    # 关联关系
    approver = db.relationship("User", backref="approval_steps")

    def __repr__(self):
        return f"<ApprovalStep {self.step_name}>"


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

    # 关联关系
    process = db.relationship("ApprovalProcessTemplate")
    creator = db.relationship("User", backref="created_approvals")
    records = db.relationship("ApprovalRecord", backref="instance", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ApprovalInstance {self.id} - {self.object_type}:{self.object_id}>"


class ApprovalRecord(db.Model):
    """审批记录"""
    __tablename__ = "approval_record"

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.Integer, db.ForeignKey("approval_instance.id"), nullable=False, comment="审批流程实例")
    step_id = db.Column(db.Integer, db.ForeignKey("approval_step.id"), nullable=False, comment="流程步骤ID")
    approver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="审批人ID")
    action = db.Column(db.String(50), nullable=False, comment="同意/拒绝")
    comment = db.Column(db.Text, comment="审批意见")
    timestamp = db.Column(db.DateTime, default=datetime.now, comment="审批时间")

    # 关联关系
    step = db.relationship("ApprovalStep")
    approver = db.relationship("User", backref="approval_records")

    def __repr__(self):
        return f"<ApprovalRecord {self.id} - {self.action}>" 