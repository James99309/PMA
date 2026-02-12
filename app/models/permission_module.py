"""
权限模块模型

定义系统中的权限模块，支持数据库驱动的模块配置
"""
from app import db
import time


class PermissionModule(db.Model):
    """
    权限模块表

    存储系统中所有可配置权限的模块定义
    """
    __tablename__ = 'permission_modules'

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.String(50), unique=True, nullable=False)  # 模块标识符
    name = db.Column(db.String(100), nullable=False)  # 中文名称
    name_en = db.Column(db.String(100))  # 英文名称
    icon = db.Column(db.String(50))  # 图标名称 (Material Symbols)
    description = db.Column(db.String(500))  # 模块描述
    description_en = db.Column(db.String(500))  # 英文描述
    group_name = db.Column(db.String(50))  # 分组名称
    group_name_en = db.Column(db.String(50))  # 英文分组名称
    sort_order = db.Column(db.Integer, default=0)  # 排序顺序

    # 模块能力标志
    supports_discount = db.Column(db.Boolean, default=False)  # 支持折扣权限
    supports_owner_change = db.Column(db.Boolean, default=False)  # 支持拥有人修改
    supports_affiliation = db.Column(db.Boolean, default=False)  # 支持数据归属
    supports_content_filter = db.Column(db.Boolean, default=False)  # 支持内容筛选
    supports_export_email = db.Column(db.Boolean, default=False)  # 支持导出邮箱

    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.Float, default=time.time)
    updated_at = db.Column(db.Float, default=time.time, onupdate=time.time)

    # 关联子功能
    features = db.relationship('PermissionModuleFeature', backref='module', lazy='dynamic')

    __table_args__ = (
        db.Index('idx_permission_modules_group', 'group_name'),
        db.Index('idx_permission_modules_sort', 'sort_order'),
    )

    def to_dict(self, lang='zh'):
        """转换为字典，支持语言切换"""
        return {
            'id': self.module_id,
            'module_id': self.module_id,
            'name': self.name_en if lang == 'en' and self.name_en else self.name,
            'icon': self.icon,
            'description': self.description_en if lang == 'en' and self.description_en else self.description,
            'group': self.group_name_en if lang == 'en' and self.group_name_en else self.group_name,
            'group_name': self.group_name,
            'sort_order': self.sort_order,
            'supports_discount': self.supports_discount,
            'supports_owner_change': self.supports_owner_change,
            'supports_affiliation': self.supports_affiliation,
            'supports_content_filter': self.supports_content_filter,
            'supports_export_email': self.supports_export_email,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<PermissionModule {self.module_id}: {self.name}>'


class PermissionModuleFeature(db.Model):
    """
    权限模块子功能表

    存储模块下的子功能（如页签）定义
    """
    __tablename__ = 'permission_module_features'

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.String(50), db.ForeignKey('permission_modules.module_id'), nullable=False)
    feature_id = db.Column(db.String(50), nullable=False)  # 子功能标识符
    name = db.Column(db.String(100), nullable=False)  # 中文名称
    name_en = db.Column(db.String(100))  # 英文名称
    icon = db.Column(db.String(50))  # 图标名称
    description = db.Column(db.String(500))  # 功能描述
    sort_order = db.Column(db.Integer, default=0)  # 排序顺序
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.Float, default=time.time)
    updated_at = db.Column(db.Float, default=time.time, onupdate=time.time)

    __table_args__ = (
        db.UniqueConstraint('module_id', 'feature_id', name='uix_module_feature'),
    )

    def to_dict(self, lang='zh'):
        """转换为字典"""
        return {
            'feature_id': self.feature_id,
            'module_id': self.module_id,
            'name': self.name_en if lang == 'en' and self.name_en else self.name,
            'icon': self.icon,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<PermissionModuleFeature {self.module_id}.{self.feature_id}>'


class RoleFeaturePermission(db.Model):
    """
    角色子功能权限表

    存储角色对模块子功能的访问权限
    """
    __tablename__ = 'role_feature_permissions'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)  # 角色代码
    module_id = db.Column(db.String(50), nullable=False)  # 模块ID
    feature_id = db.Column(db.String(50), nullable=False)  # 子功能ID
    is_enabled = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.Float, default=time.time)
    updated_at = db.Column(db.Float, default=time.time, onupdate=time.time)

    __table_args__ = (
        db.UniqueConstraint('role', 'module_id', 'feature_id', name='uix_role_module_feature'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'role': self.role,
            'module_id': self.module_id,
            'feature_id': self.feature_id,
            'is_enabled': self.is_enabled
        }

    def __repr__(self):
        return f'<RoleFeaturePermission {self.role}.{self.module_id}.{self.feature_id}>'
