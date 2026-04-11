from app import db

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    can_view = db.Column(db.Boolean, default=False)
    can_create = db.Column(db.Boolean, default=False)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_change_owner = db.Column(db.Boolean, default=False)  # 拥有人修改权限
    can_export_email = db.Column(db.Boolean, default=False)  # 导出邮箱权限
    
    # 批价单和结算单特殊权限字段
    pricing_discount_limit = db.Column(db.Float, nullable=True)  # 批价折扣下限（百分比形式，如40.5表示40.5%）
    settlement_discount_limit = db.Column(db.Float, nullable=True)  # 结算折扣下限（百分比形式）
    
    # 四级权限控制字段
    permission_level = db.Column(db.String(20), default='personal')  # 权限级别：system, company, department, personal
    permission_level_description = db.Column(db.Text)  # 权限级别说明

    # 内容筛选字段
    content_filters = db.Column(db.JSON, nullable=True)  # 内容筛选配置，存储格式：{"project_type": ["type1", "type2"], "industry": ["ind1"]}

    # CLI 智能终端查询权限（独立于界面权限）
    cli_can_query = db.Column(db.Boolean, default=False, nullable=False)  # 是否允许在 CLI 查询该模块的数据
    cli_permission_level = db.Column(db.String(20), nullable=True)  # CLI 查询数据范围: system/company/department/personal；NULL=未配置(默认禁止)

    __table_args__ = (db.UniqueConstraint('role', 'module', name='uix_role_module'),)

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'role': self.role,
            'module': self.module,
            'can_view': self.can_view,
            'can_create': self.can_create,
            'can_edit': self.can_edit,
            'can_delete': self.can_delete,
            'can_change_owner': self.can_change_owner,
            'can_export_email': self.can_export_email,
            'pricing_discount_limit': self.pricing_discount_limit,
            'settlement_discount_limit': self.settlement_discount_limit,
            'permission_level': self.permission_level,
            'permission_level_description': self.permission_level_description,
            'content_filters': self.content_filters,
            'cli_can_query': self.cli_can_query,
            'cli_permission_level': self.cli_permission_level,
        }
