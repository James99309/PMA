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
    
    # 批价单和结算单特殊权限字段
    pricing_discount_limit = db.Column(db.Float, nullable=True)  # 批价折扣下限（百分比形式，如40.5表示40.5%）
    settlement_discount_limit = db.Column(db.Float, nullable=True)  # 结算折扣下限（百分比形式）
    
    # 四级权限控制字段
    permission_level = db.Column(db.String(20), default='personal')  # 权限级别：system, company, department, personal
    permission_level_description = db.Column(db.Text)  # 权限级别说明
    
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
            'pricing_discount_limit': self.pricing_discount_limit,
            'settlement_discount_limit': self.settlement_discount_limit,
            'permission_level': self.permission_level,
            'permission_level_description': self.permission_level_description
        } 