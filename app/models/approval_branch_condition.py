"""
审批分支条件模型

独立的分支条件数据表，用于高效管理审批步骤的分支决策逻辑
"""

from app import db
from datetime import datetime
import uuid


class ApprovalBranchCondition(db.Model):
    """审批分支条件模型"""
    
    __tablename__ = 'approval_branch_condition'
    
    # 主键和关联
    id = db.Column(db.String(50), primary_key=True, comment="条件唯一标识符")
    step_id = db.Column(db.Integer, db.ForeignKey('approval_step.id', ondelete='CASCADE'), 
                       nullable=False, comment="关联的审批步骤ID")
    condition_order = db.Column(db.Integer, default=0, comment="条件在步骤中的排序位置")
    
    # 条件配置
    operator = db.Column(db.String(50), nullable=False, comment="条件操作符")
    field_value = db.Column(db.String(255), nullable=False, comment="条件匹配的字段值")
    
    # 审批人配置
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), 
                           nullable=True, comment="满足条件时的审批人用户ID")
    approver_type = db.Column(db.String(50), default='user', comment="审批人类型")
    action = db.Column(db.String(100), comment="满足条件时执行的业务动作")
    
    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系定义
    step = db.relationship('ApprovalStep', backref='branch_conditions')
    approver = db.relationship('User', backref='branch_conditions')
    
    # 表约束
    __table_args__ = (
        # 防止同一步骤下的重复条件
        db.UniqueConstraint('step_id', 'operator', 'field_value', 
                           name='uk_step_operator_value'),
        
        # 检查约束
        db.CheckConstraint(
            operator.in_([
                'equals', 'not_equals', 'contains', 'not_contains',
                'greater_than', 'less_than', 'in', 'not_in', 
                'starts_with', 'ends_with', 'is_null', 'is_not_null'
            ]),
            name='chk_operator_valid'
        ),
        
        db.CheckConstraint(
            approver_type.in_(['user', 'next_level', 'next_branch']),
            name='chk_approver_type_valid'
        ),
        
        db.CheckConstraint(
            'condition_order >= 0',
            name='chk_condition_order_positive'
        ),
    )
    
    @staticmethod
    def generate_id():
        """生成条件唯一ID"""
        return f"cond_{uuid.uuid4().hex[:8]}"
    
    @classmethod
    def create_condition(cls, step_id, operator, field_value, approver_id=None, 
                        approver_type='user', action=None, condition_order=None):
        """创建新的分支条件"""
        
        # 自动计算排序位置
        if condition_order is None:
            max_order = db.session.query(db.func.max(cls.condition_order))\
                .filter(cls.step_id == step_id).scalar()
            condition_order = (max_order or 0) + 1
        
        condition = cls(
            id=cls.generate_id(),
            step_id=step_id,
            condition_order=condition_order,
            operator=operator,
            field_value=field_value,
            approver_id=approver_id,
            approver_type=approver_type,
            action=action
        )
        
        return condition
    
    @classmethod
    def check_duplicate(cls, step_id, operator, field_value, exclude_id=None):
        """检查是否存在重复条件"""
        query = cls.query.filter(
            cls.step_id == step_id,
            cls.operator == operator,
            cls.field_value == field_value
        )
        
        if exclude_id:
            query = query.filter(cls.id != exclude_id)
            
        return query.first()
    
    @classmethod
    def get_step_conditions(cls, step_id, ordered=True):
        """获取步骤的所有条件"""
        query = cls.query.filter(cls.step_id == step_id)
        
        if ordered:
            query = query.order_by(cls.condition_order, cls.created_at)
            
        return query.all()
    
    @classmethod
    def reorder_conditions(cls, step_id, condition_ids):
        """重新排序条件"""
        for index, condition_id in enumerate(condition_ids):
            condition = cls.query.get(condition_id)
            if condition and condition.step_id == step_id:
                condition.condition_order = index
        
        db.session.commit()
    
    def update_condition(self, operator=None, field_value=None, approver_id=None, 
                        approver_type=None, action=None):
        """更新条件信息"""
        if operator is not None:
            self.operator = operator
        if field_value is not None:
            self.field_value = field_value
        if approver_id is not None:
            self.approver_id = approver_id
        if approver_type is not None:
            self.approver_type = approver_type
        if action is not None:
            self.action = action
            
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'step_id': self.step_id,
            'condition_order': self.condition_order,
            'operator': self.operator,
            'field_value': self.field_value,
            'approver_id': self.approver_id,
            'approver_type': self.approver_type,
            'action': self.action,
            'approver_name': self.approver.real_name if self.approver else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_legacy_format(self):
        """转换为旧版JSON格式（向后兼容）"""
        return {
            'id': self.id,
            'operator': self.operator,
            'value': self.field_value,
            'approver_id': self.approver_id,
            'approver_type': self.approver_type,
            'action': self.action
        }
    
    @classmethod
    def from_legacy_data(cls, step_id, legacy_condition, condition_order=0):
        """从旧版JSON数据创建条件（用于数据迁移）"""
        return cls(
            id=legacy_condition.get('id') or cls.generate_id(),
            step_id=step_id,
            condition_order=condition_order,
            operator=legacy_condition.get('operator', 'equals'),
            field_value=legacy_condition.get('value', ''),
            approver_id=legacy_condition.get('approver_id'),
            approver_type=legacy_condition.get('approver_type', 'user'),
            action=legacy_condition.get('action')
        )
    
    def __repr__(self):
        return f"<ApprovalBranchCondition {self.id}: {self.field_value} {self.operator}>"
    
    def __str__(self):
        approver_name = self.approver.real_name if self.approver else self.approver_type
        return f"条件: {self.field_value} {self.operator} → {approver_name}"


# 操作符选项（用于前端）
OPERATOR_CHOICES = [
    ('equals', '等于'),
    ('not_equals', '不等于'),
    ('contains', '包含'),
    ('not_contains', '不包含'),
    ('greater_than', '大于'),
    ('less_than', '小于'),
    ('in', '属于'),
    ('not_in', '不属于'),
    ('starts_with', '以...开头'),
    ('ends_with', '以...结尾'),
    ('is_null', '为空'),
    ('is_not_null', '不为空'),
]

# 审批人类型选项
APPROVER_TYPE_CHOICES = [
    ('user', '指定用户'),
    ('next_level', '上一级领导'),
    ('next_branch', '下一分支'),
]