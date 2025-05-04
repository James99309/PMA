from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import time
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

class User(db.Model, UserMixin):
    """
    用户模型
    
    注意：用户名和邮箱查询现在都是不区分大小写的。实际比较是在查询时通过
    SQLAlchemy的func.lower()函数完成，而不是在模型层实现。
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # 用户名
    password_hash = db.Column(db.String(128), nullable=False)  # 密码哈希
    real_name = db.Column(db.String(80))  # 真实姓名
    company_name = db.Column(db.String(100))  # 企业名称
    email = db.Column(db.String(120), unique=True, nullable=True)  # 邮箱地址
    phone = db.Column(db.String(20))  # 联系电话（带国家号）
    department = db.Column(db.String(100))  # 部门归属
    is_department_manager = db.Column(db.Boolean, default=False)  # 是否为部门负责人
    role = db.Column(db.String(20), default='user')  # 用户角色
    is_profile_complete = db.Column(db.Boolean, default=False)  # 是否已完善信息
    wechat_openid = db.Column(db.String(64), unique=True)  # 微信ID
    wechat_nickname = db.Column(db.String(64))  # 微信昵称
    wechat_avatar = db.Column(db.String(256))  # 微信头像URL
    _is_active = db.Column(db.Boolean, default=False, name="is_active")  # 账号是否激活，使用不同名称避免与属性冲突
    created_at = db.Column(db.Float)
    last_login = db.Column(db.Float)  # 最后登录时间
    
    # 关系
    permissions = db.relationship('Permission', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.created_at = time.time()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        self.last_login = time.time()
        db.session.commit()

    # 实现Flask-Login需要的方法
    def get_id(self):
        return str(self.id)
        
    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_anonymous(self):
        return False
        
    @property
    def is_active(self):
        """覆盖is_active属性，确保管理员账户总是激活的"""
        # 管理员账户总是激活的
        if self.role == 'admin':
            return True
        # 其他用户根据数据库字段决定
        return bool(self._is_active)
        
    @is_active.setter
    def is_active(self, value):
        """设置is_active属性"""
        self._is_active = bool(value)
        
    @property
    def name(self):
        """返回用户的名称，优先使用真实姓名，如果没有则使用用户名"""
        return self.real_name or self.username

    def to_dict(self):
        """将用户信息转为字典，用于API响应"""
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'company_name': self.company_name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'is_department_manager': self.is_department_manager,
            'is_active': self.is_active,
            'is_profile_complete': self.is_profile_complete,
            'role': self.role,
            'last_login': self.last_login
        }
    
    def has_permission(self, module, action):
        """检查用户是否有指定模块的指定操作权限"""
        # 管理员默认拥有所有权限
        if self.role == 'admin':
            return True
            
        # 查找对应模块的权限记录
        permission = Permission.query.filter_by(user_id=self.id, module=module).first()
        
        if not permission:
            return False
            
        # 根据操作类型检查权限
        if action == 'view':
            return permission.can_view
        elif action == 'create':
            return permission.can_create
        elif action == 'edit':
            return permission.can_edit
        elif action == 'delete':
            return permission.can_delete
        
        return False
        
    def get_permissions(self):
        """获取用户的所有权限，转换为字典格式"""
        permissions_dict = {}
        
        # 如果是管理员，拥有所有权限
        if self.role == 'admin':
            modules = ['customer', 'project', 'quotation', 'product', 'product_code', 'user', 'permission']
            for module in modules:
                permissions_dict[module] = ['view', 'create', 'edit', 'delete']
            return permissions_dict
        
        # 获取用户的权限记录
        for permission in self.permissions:
            if permission.module not in permissions_dict:
                permissions_dict[permission.module] = []
                
            if permission.can_view:
                permissions_dict[permission.module].append('view')
            if permission.can_create:
                permissions_dict[permission.module].append('create')
            if permission.can_edit:
                permissions_dict[permission.module].append('edit')
            if permission.can_delete:
                permissions_dict[permission.module].append('delete')
        
        return permissions_dict

    def get_viewable_user_ids(self):
        """获取当前用户可以查看数据的所有用户ID"""
        # 管理员可以查看所有
        if self.role == 'admin':
            return [user.id for user in User.query.all()]
            
        # 基本情况：用户可以查看自己的数据
        viewable_ids = [self.id]
        
        # 代理商和普通用户只能看到自己的数据
        if self.role in ['dealer', 'user']:
            return viewable_ids
        
        # 产品经理和解决方案经理可以查看所有报价单所有者的数据
        if self.role in ['product_manager', 'solution_manager']:
            from app.models.quotation import Quotation
            # 获取所有报价单所有者的ID
            owner_ids = db.session.query(Quotation.owner_id).distinct().all()
            for owner_id in owner_ids:
                if owner_id[0] and owner_id[0] not in viewable_ids:
                    viewable_ids.append(owner_id[0])
        
        # 服务经理可以查看所有客户和项目相关人员的数据
        if self.role == 'service':
            from app.models.customer import Company
            from app.models.project import Project
            
            # 获取所有客户和项目所有者的ID
            company_owner_ids = db.session.query(Company.owner_id).distinct().all()
            project_owner_ids = db.session.query(Project.owner_id).distinct().all()
            
            # 添加到可查看ID列表
            for owner_id in company_owner_ids + project_owner_ids:
                if owner_id[0] and owner_id[0] not in viewable_ids:
                    viewable_ids.append(owner_id[0])
        
        # 获取通过归属关系可以查看的用户
        for affiliation in self.can_view_from:
            viewable_ids.append(affiliation.owner_id)
            
        # 渠道经理和营销总监有特殊权限，需在查询时处理
        
        # 去重并返回
        return list(set(viewable_ids))

    def __repr__(self):
        return f'<User {self.username}>'

    def generate_reset_token(self):
        """
        生成密码重置令牌
        
        返回值:
            str: 加密的令牌
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset')
    
    @staticmethod
    def verify_reset_token(token, expiration=1800):  # 默认30分钟有效期
        """
        验证密码重置令牌
        
        参数:
            token: 重置令牌
            expiration: 过期时间（秒）
            
        返回值:
            User: 成功返回用户对象，失败返回None
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='password-reset', max_age=expiration)
        except SignatureExpired:
            # 令牌已过期
            return None
        except BadSignature:
            # 令牌无效
            return None
            
        user_id = data.get('user_id')
        if not user_id:
            return None
            
        return User.query.get(user_id)


class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module = db.Column(db.String(50), nullable=False)  # 模块名称
    can_view = db.Column(db.Boolean, default=False)  # 查看权限
    can_create = db.Column(db.Boolean, default=False)  # 创建权限
    can_edit = db.Column(db.Boolean, default=False)  # 编辑权限
    can_delete = db.Column(db.Boolean, default=False)  # 删除权限
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'module', name='uix_user_module'),
    )
    
    def to_dict(self):
        """将权限信息转为字典，用于API响应"""
        return {
            'module': self.module,
            'can_view': self.can_view,
            'can_create': self.can_create,
            'can_edit': self.can_edit,
            'can_delete': self.can_delete
        }
    
    def __repr__(self):
        return f'<Permission {self.user_id}-{self.module}>'


class Affiliation(db.Model):
    """
    数据归属关系模型：定义用户之间的数据查看关系
    owner_id: 数据所有者ID
    viewer_id: 数据查看者ID
    """
    __tablename__ = 'affiliations'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 数据所有者ID
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 可查看者ID
    created_at = db.Column(db.Float, default=time.time)  # 创建时间
    
    # 与User模型的关系
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('shared_with', lazy='dynamic'))
    viewer = db.relationship('User', foreign_keys=[viewer_id], backref=db.backref('can_view_from', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('owner_id', 'viewer_id', name='uix_owner_viewer'),
    )
    
    def to_dict(self):
        """将归属关系转为字典，用于API响应"""
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'viewer_id': self.viewer_id,
            'created_at': self.created_at
        }
    
    def __repr__(self):
        return f'<Affiliation {self.owner_id}->{self.viewer_id}>'


class DataAffiliation(db.Model):
    """
    用户数据归属关系模型：定义用户之间的数据查看关系
    与Affiliation类似，但专门用于前端数据归属关系管理
    owner_id: 数据所有者ID
    viewer_id: 数据查看者ID
    """
    __tablename__ = 'data_affiliations'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 数据所有者ID
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 可查看者ID
    created_at = db.Column(db.Float, default=time.time)  # 创建时间
    
    # 与User模型的关系
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('data_shared_with', lazy='dynamic'))
    viewer = db.relationship('User', foreign_keys=[viewer_id], backref=db.backref('can_view_data_from', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('owner_id', 'viewer_id', name='uix_data_owner_viewer'),
    )
    
    def to_dict(self):
        """将数据归属关系转为字典，用于API响应"""
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'viewer_id': self.viewer_id,
            'created_at': self.created_at
        }
    
    def __repr__(self):
        return f'<DataAffiliation {self.owner_id}->{self.viewer_id}>' 