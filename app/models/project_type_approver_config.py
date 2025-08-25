"""
项目类型审批人配置模型
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from app import db
from app.models.user import User

def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class ProjectTypeApproverConfig(db.Model):
    """项目类型审批人配置"""
    __tablename__ = "project_type_approver_config"

    id = db.Column(db.Integer, primary_key=True)
    project_type = db.Column(db.String(50), nullable=False, unique=True, comment="项目类型")
    approver_type = db.Column(db.String(20), default='user', comment="审批人类型：user(指定用户) 或 role(按角色)")
    approver_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, comment="指定审批人用户ID")
    approver_role = db.Column(db.String(50), nullable=True, comment="审批人角色")
    fallback_role = db.Column(db.String(50), default='ceo', comment="找不到指定审批人时的备用角色")
    is_active = db.Column(db.Boolean, default=True, comment="是否启用")
    created_at = db.Column(db.DateTime, default=get_local_time, comment="创建时间")
    updated_at = db.Column(db.DateTime, default=get_local_time, onupdate=get_local_time, comment="更新时间")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="创建人")

    # 关联关系
    approver_user = db.relationship("User", foreign_keys=[approver_user_id], backref="approved_project_types")
    creator = db.relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ProjectTypeApproverConfig {self.project_type}>"

    @property
    def approver_display_name(self):
        """获取审批人显示名称"""
        if self.approver_type == 'user' and self.approver_user:
            return f"{self.approver_user.real_name} ({self.approver_user.username})"
        elif self.approver_type == 'role':
            from app.models.user import User
            role_labels = {
                'admin': '管理员',
                'ceo': '总经理',
                'sales_director': '营销总监',
                'channel_manager': '渠道经理',
                'service_manager': '服务经理',
                'business_admin': '商务助理',
                'finance': '财务',
                'hr': '人事',
                'user': '普通用户'
            }
            return f"角色：{role_labels.get(self.approver_role, self.approver_role)}"
        return "未配置"

    @property 
    def project_type_display_name(self):
        """获取项目类型显示名称"""
        type_labels = {
            'channel_follow': '渠道跟进',
            'sales_focus': '销售重点',
            'sales_key': '销售重点',  # 向sales_focus统一
            'business_opportunity': '客户服务'
        }
        return type_labels.get(self.project_type, self.project_type)

    def get_approver(self):
        """
        获取审批人
        
        Returns:
            User对象或None
        """
        if not self.is_active:
            return None
            
        if self.approver_type == 'user' and self.approver_user_id:
            # 指定用户模式
            approver = User.query.filter_by(id=self.approver_user_id, is_active=True).first()
            if approver:
                return approver
        elif self.approver_type == 'role' and self.approver_role:
            # 角色模式
            approver = User.query.filter_by(role=self.approver_role, is_active=True).first()
            if approver:
                return approver
        
        # 找不到指定审批人时使用备用角色
        if self.fallback_role:
            fallback_approver = User.query.filter_by(role=self.fallback_role, is_active=True).first()
            if fallback_approver:
                return fallback_approver
        
        # 最后备用：总经理
        return User.query.filter_by(role='ceo', is_active=True).first()

    @classmethod
    def get_approver_for_project_type(cls, project_type):
        """
        根据项目类型获取审批人
        
        Args:
            project_type (str): 项目类型
            
        Returns:
            User对象或None
        """
        config = cls.query.filter_by(
            project_type=project_type, 
            is_active=True
        ).first()
        
        if config:
            return config.get_approver()
        else:
            # 如果没有配置，使用默认逻辑（保持向后兼容）
            return cls._get_default_approver(project_type)
    
    @classmethod
    def _get_default_approver(cls, project_type):
        """
        默认审批人获取逻辑（向后兼容）
        
        Args:
            project_type (str): 项目类型
            
        Returns:
            User对象或None
        """
        # 保持原有的硬编码映射作为默认值
        default_mapping = {
            'channel_follow': 'channel_manager',
            'sales_focus': 'sales_director',
            'sales_key': 'sales_director',  # 向sales_focus统一
            'business_opportunity': 'service_manager'
        }
        
        target_role = default_mapping.get(project_type, 'ceo')
        approver = User.query.filter_by(role=target_role, is_active=True).first()
        
        if not approver:
            approver = User.query.filter_by(role='ceo', is_active=True).first()
            
        return approver

    @classmethod
    def create_default_configs(cls, created_by_id):
        """
        创建默认配置
        
        Args:
            created_by_id (int): 创建人ID
        """
        default_configs = [
            {
                'project_type': 'channel_follow',
                'approver_type': 'role',
                'approver_role': 'channel_manager',
                'fallback_role': 'ceo'
            },
            {
                'project_type': 'sales_focus',
                'approver_type': 'role',
                'approver_role': 'sales_director',
                'fallback_role': 'ceo'
            },
            {
                'project_type': 'business_opportunity',
                'approver_type': 'role',
                'approver_role': 'service_manager',
                'fallback_role': 'ceo'
            }
        ]
        
        for config_data in default_configs:
            existing = cls.query.filter_by(project_type=config_data['project_type']).first()
            if not existing:
                config = cls(
                    project_type=config_data['project_type'],
                    approver_type=config_data['approver_type'],
                    approver_role=config_data['approver_role'],
                    fallback_role=config_data['fallback_role'],
                    created_by=created_by_id
                )
                db.session.add(config)
        
        db.session.commit()