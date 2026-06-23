from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import time
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app, has_request_context
try:
    from flask import g
except ImportError:
    g = None

class User(db.Model, UserMixin):
    """
    用户模型
    
    注意：用户名和邮箱查询现在都是不区分大小写的。实际比较是在查询时通过
    SQLAlchemy的func.lower()函数完成，而不是在模型层实现。
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # 用户名
    password_hash = db.Column(db.String(256), nullable=False)  # 密码哈希
    real_name = db.Column(db.String(80))  # 真实姓名
    company_name = db.Column(db.String(100))  # 企业名称
    email = db.Column(db.String(120), unique=True, nullable=True)  # 邮箱地址
    phone = db.Column(db.String(20))  # 联系电话（带国家号）
    department = db.Column(db.String(100))  # 部门归属
    is_department_manager = db.Column(db.Boolean, default=False)  # 是否为部门负责人
    probation_start = db.Column(db.Date)  # 试用期开始日期(账户级)
    probation_end = db.Column(db.Date)    # 试用期结束日期;过期后试用期徽章自动消失
    role = db.Column(db.String(20), default='user')  # 用户角色
    is_profile_complete = db.Column(db.Boolean, default=False)  # 是否已完善信息
    wechat_openid = db.Column(db.String(64), unique=True)  # 微信ID
    wechat_nickname = db.Column(db.String(64))  # 微信昵称
    wechat_avatar = db.Column(db.String(256))  # 微信头像URL
    _is_active = db.Column(db.Boolean, default=False, name="is_active")  # 账号是否激活，使用不同名称避免与属性冲突
    language_preference = db.Column(db.String(10), default='zh')  # 语言偏好设置，默认简体中文
    settlement_currency = db.Column(db.String(10), default=None)  # 结算货币，NULL则使用系统默认
    push_token = db.Column(db.String(512), nullable=True)  # FCM/APNs 设备推送 token
    push_platform = db.Column(db.String(10), nullable=True)  # ios 或 android
    linked_company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)  # 关联外部用户到Company表(供应商/代理商/客户)
    storage_quota = db.Column(db.BigInteger, default=10737418240)  # 存储配额(字节), 默认10GB
    storage_used = db.Column(db.BigInteger, default=0)  # 已用存储(字节)
    # Claude AI 代理（cliproxy 集成）
    claude_ai_enabled = db.Column(db.Boolean, default=False, nullable=False)  # 是否启用 Claude AI 代理
    claude_ai_token = db.Column(db.String(64), unique=True, nullable=True, index=True)  # 代理认证 token
    claude_ai_quota_tokens = db.Column(db.BigInteger, default=0, nullable=False)  # 月度配额（0 = 用全局默认）
    claude_ai_enabled_at = db.Column(db.DateTime, nullable=True)  # 启用时间，审计用

    # 报价单 Excel-like 编辑器：账户级默认抬头/签名（字段级保存）
    quotation_letterhead = db.Column(db.JSON, nullable=True)  # {logo_url, line1, line2, line3}
    quotation_signature = db.Column(db.JSON, nullable=True)   # {left, right}

    # 个人档案(用工资料)— HR 专属;元数据列表,每项 {filename,url,size,doc_type,uploaded_at,uploaded_by,uploaded_by_name}
    hr_documents = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.Float, default=time.time)
    updated_at = db.Column(db.Float, default=time.time, onupdate=time.time)
    last_login = db.Column(db.Float)  # 最后登录时间

    # ─── 跨系统镜像 (Federation Lite) ───────────────────────────────
    # 当前用户是否对另一个系统可见（CN 端勾选 → 自动 mirror 到 SG）
    cross_team_visible = db.Column(db.Boolean, default=False, nullable=False)
    cross_team_label = db.Column(db.String(50), nullable=True)  # 对外身份标签, 如"海外技术支持"
    # 镜像账户标记 (本行是从对方系统镜像过来的)
    source_system = db.Column(db.String(20), nullable=True)     # 'sp8d' / 'ovs' / NULL=本地原生
    source_user_id = db.Column(db.Integer, nullable=True)        # 源系统的 user.id
    is_mirror = db.Column(db.Boolean, default=False, nullable=False)
    mirrored_at = db.Column(db.Float, nullable=True)             # 上次同步时间
    
    # 关系
    permissions = db.relationship('Permission', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    linked_company = db.relationship('Company', foreign_keys=[linked_company_id], backref=db.backref('linked_users', lazy='dynamic'))  # 关联的公司(供应商/代理商/客户)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.created_at = time.time()
        self.updated_at = time.time()

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
    def in_probation(self):
        """当前是否处于试用期(有结束日期且今天未超过结束日期);结束后自动 False"""
        if not self.probation_end:
            return False
        from datetime import date
        return date.today() <= self.probation_end

    @property
    def name(self):
        """返回用户的名称，优先使用真实姓名，如果没有则使用用户名"""
        return self.real_name or self.username

    @property
    def managed_department_ids(self):
        """获取用户管理的部门ID列表"""
        from app.models.expense import Department
        departments = Department.query.filter_by(manager_id=self.id).all()
        return [d.id for d in departments]

    # managed_departments 属性由 expense.py 中 Department.manager 的 backref 自动提供

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
            'linked_company_id': self.linked_company_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login': self.last_login,
            # 跨系统镜像 (Federation Lite)
            'cross_team_visible': bool(getattr(self, 'cross_team_visible', False)),
            'cross_team_label': getattr(self, 'cross_team_label', None),
            'is_mirror': bool(getattr(self, 'is_mirror', False)),
            'source_system': getattr(self, 'source_system', None),
            'source_user_id': getattr(self, 'source_user_id', None),
            'mirrored_at': getattr(self, 'mirrored_at', None),
            # 个人偏好
            'settlement_currency': self.settlement_currency,
            'language_preference': self.language_preference,
        }
    
    def _load_permission_cache(self):
        """
        批量加载该用户的所有权限数据到 flask.g 缓存。

        整个请求周期内只查询数据库 2 次（RolePermission + Permission），
        后续所有 has_permission() / get_permission_level() 调用直接从缓存读取。

        缓存结构:
            g._perm_cache = {
                'user_id': int,
                'role_perms': { module: RolePermission_obj, ... },
                'personal_perms': { module: Permission_obj, ... }
            }

        非请求上下文（如CLI脚本）自动回退到 None，调用方应直接查库。
        """
        if not has_request_context():
            return None

        cache = getattr(g, '_perm_cache', None)
        if cache and cache.get('user_id') == self.id:
            return cache

        from app.models.role_permissions import RolePermission

        # 批量加载角色权限（1次查询）
        role_perms_list = RolePermission.query.filter_by(role=self.role).all()
        role_perms = {rp.module: rp for rp in role_perms_list}

        # 批量加载个人权限（1次查询）
        personal_perms_list = Permission.query.filter_by(user_id=self.id).all()
        personal_perms = {pp.module: pp for pp in personal_perms_list}

        cache = {
            'user_id': self.id,
            'role_perms': role_perms,
            'personal_perms': personal_perms
        }
        g._perm_cache = cache
        return cache

    def _get_cached_permissions(self, module):
        """
        从缓存获取指定模块的角色权限和个人权限。

        返回:
            (role_permission, personal_permission) 元组
            如果非请求上下文或缓存加载失败，回退到直接查库。
        """
        try:
            cache = self._load_permission_cache()
        except Exception:
            cache = None

        if cache:
            return cache['role_perms'].get(module), cache['personal_perms'].get(module)

        # 回退：非请求上下文，直接查库
        from app.models.role_permissions import RolePermission
        role_permission = RolePermission.query.filter_by(role=self.role, module=module).first()
        personal_permission = Permission.query.filter_by(user_id=self.id, module=module).first()
        return role_permission, personal_permission

    @staticmethod
    def _check_action_permission(perm_obj, action):
        """从权限对象中检查指定动作的权限"""
        if not perm_obj:
            return False
        if getattr(perm_obj, 'permission_level', None) == 'none':
            return False
        if action == 'view':
            return perm_obj.can_view
        elif action == 'create':
            return perm_obj.can_create
        elif action == 'edit':
            return perm_obj.can_edit
        elif action == 'delete':
            return perm_obj.can_delete
        elif action == 'change_owner':
            return getattr(perm_obj, 'can_change_owner', False)
        elif action == 'export_email':
            return getattr(perm_obj, 'can_export_email', False)
        return False

    def has_permission(self, module, action):
        """
        检查用户是否具有指定模块和动作的权限

        权限合并逻辑：
        1. 如果设置了个人权限，使用个人权限（完全覆盖角色权限）
        2. 如果没有个人权限，使用角色权限（继承默认权限）
        3. 如果权限级别为 'none'，则拒绝所有权限

        参数:
            module: 权限模块名称
            action: 权限动作 ('view', 'create', 'edit', 'delete')

        返回:
            bool: 是否拥有该权限
        """
        try:
            # 管理员默认拥有所有权限
            if self.role == 'admin':
                return True

            role_permission, personal_permission = self._get_cached_permissions(module)

            # 个人权限完全覆盖角色权限
            if personal_permission:
                return self._check_action_permission(personal_permission, action)
            else:
                return self._check_action_permission(role_permission, action)

        except Exception as e:
            # 发生数据库错误时，回滚事务并记录错误
            print(f"[ERROR][has_permission] Database error: {str(e)}")
            try:
                from app import db
                db.session.rollback()
            except Exception as rollback_error:
                print(f"[ERROR][has_permission] Rollback failed: {str(rollback_error)}")

            # 对于权限检查失败，默认返回False（安全策略）
            # 但对于管理员，即使数据库出错也应该有权限
            if self.role == 'admin':
                return True

            return False
    
    def get_data_scope(self, module):
        """模块数据范围:system/company/department/personal(admin→system;未配置→personal)。"""
        if self.role == 'admin':
            return 'system'
        try:
            role_permission, personal_permission = self._get_cached_permissions(module)
            perm = personal_permission or role_permission
            return (perm.permission_level if perm and perm.permission_level else 'personal')
        except Exception:
            return 'personal'

    def can_view_person(self, target_user, module):
        """按模块数据范围判断能否查看某人(用于个人配置等以「人」为对象的页面)。"""
        if self.role == 'admin':
            return True
        if not self.has_permission(module, 'view'):
            return False
        scope = self.get_data_scope(module)
        if scope == 'system':
            return True
        if scope == 'company':
            return (target_user.company_name or '') == (self.company_name or '')
        if scope == 'department':
            return ((target_user.company_name or '') == (self.company_name or '')
                    and (target_user.department or '') == (self.department or ''))
        return target_user.id == self.id   # personal

    def has_feature(self, module_id, feature_id):
        """模块内功能开关(tab 等):白名单制 —— admin 恒真;否则查 role_feature_permissions,
        仅当存在记录且 is_enabled 时为真(未配置=隐藏)。"""
        try:
            if self.role == 'admin':
                return True
            from app.models.permission_module import RoleFeaturePermission
            rec = RoleFeaturePermission.query.filter_by(
                role=self.role, module_id=module_id, feature_id=feature_id).first()
            return bool(rec and rec.is_enabled)
        except Exception as e:
            print(f'[ERROR][has_feature] {e}')
            try:
                from app import db
                db.session.rollback()
            except Exception:
                pass
            return self.role == 'admin'

    def has_cli_permission(self, module):
        """
        检查用户是否具有 CLI 查询该模块数据的权限

        与 has_permission() 完全独立: CLI 查询权限由 role_permissions.cli_can_query 决定,
        不受 can_view 的影响。这样可以实现"用户不能打开客户列表页,但能在 CLI 查客户"的场景。

        参数:
            module: 权限模块名称 (customer/project/quotation/...)

        返回:
            bool: 是否允许在 CLI 里查询该模块对应的数据表
        """
        try:
            if self.role == 'admin':
                return True
            role_permission, personal_permission = self._get_cached_permissions(module)
            # 个人权限目前不影响 CLI 查询,只看角色配置
            if role_permission is None:
                return False
            return bool(role_permission.cli_can_query)
        except Exception as e:
            print(f'[ERROR][has_cli_permission] {e}')
            return False

    def get_cli_permission_level(self, module):
        """
        获取用户在 CLI 查询该模块时的数据范围

        返回 'system' / 'company' / 'department' / 'personal',默认 'personal'。
        若 cli_permission_level 为 NULL(未配置),视为 'personal'(最严)。
        """
        try:
            if self.role == 'admin':
                return 'system'
            role_permission, _ = self._get_cached_permissions(module)
            if role_permission is None or not role_permission.cli_can_query:
                return 'personal'
            return role_permission.cli_permission_level or 'personal'
        except Exception as e:
            print(f'[ERROR][get_cli_permission_level] {e}')
            return 'personal'

    def get_permission_level(self, module):
        """
        获取用户在指定模块的权限级别

        权限级别逻辑：
        1. 权限级别由角色权限决定
        2. 用户个人权限只能在角色权限基础上增加权限开关，不能提升权限级别
        3. 如果用户有该模块的任何权限，使用角色权限的级别
        4. 如果用户没有权限，返回 personal 级别

        参数:
            module: 权限模块名称

        返回:
            str: 权限级别 ('system', 'company', 'department', 'personal')
        """
        try:
            # 管理员默认拥有系统级权限
            if self.role == 'admin':
                return 'system'

            role_permission, permission = self._get_cached_permissions(module)

            # 1. 获取角色权限级别（基础权限级别）
            role_level = 'personal'  # 默认个人级
            if role_permission:
                role_level = role_permission.permission_level or 'personal'

            # 2. 直接检查用户是否有该模块的任何权限
            role_has_any_permission = False
            if role_permission:
                role_has_any_permission = (role_permission.can_view or role_permission.can_create or
                                         role_permission.can_edit or role_permission.can_delete)

            personal_has_any_permission = False
            if permission:
                personal_has_any_permission = (permission.can_view or permission.can_create or
                                             permission.can_edit or permission.can_delete)

            # 合并权限检查
            user_has_permission = role_has_any_permission or personal_has_any_permission

            # 3. 权限级别优先级：使用 permission_level 作为判断基准
            if user_has_permission:
                if permission and permission.permission_level is not None:
                    final_level = permission.permission_level
                else:
                    final_level = role_level
            else:
                final_level = 'personal'

            return final_level

        except Exception as e:
            print(f"[ERROR][get_permission_level] Database error: {str(e)}")
            return 'personal'

    def get_permission_config(self, module):
        """
        获取用户在指定模块的权限配置对象
        用于读取 content_filters 等配置字段。

        参数:
            module: 模块名称（如 'project', 'quotation', 'customer'）

        返回:
            Permission 或 RolePermission 对象，包含 content_filters 等字段
            如果没有找到配置，返回 None
        """
        try:
            role_permission, personal_permission = self._get_cached_permissions(module)

            # 优先返回个人权限
            if personal_permission:
                return personal_permission

            # 其次返回角色权限
            return role_permission
        except Exception as e:
            print(f"[ERROR][get_permission_config] Database error: {str(e)}")
            return None

    def is_module_enabled(self, module_name):
        """
        检查用户是否启用了指定模块（即是否有任何有效权限）

        模块被视为"启用"的条件：
        - 至少有一个基础权限（can_view, can_create, can_edit, can_delete）为 True

        参数:
            module_name: 模块名称

        返回:
            bool: 模块是否启用
        """
        from app.utils.permission_helpers import is_module_enabled as _is_module_enabled

        try:
            # 管理员所有模块默认启用
            if self.role == 'admin':
                return True

            role_permission, personal_permission = self._get_cached_permissions(module_name)

            if personal_permission and _is_module_enabled(personal_permission):
                return True

            return _is_module_enabled(role_permission)

        except Exception as e:
            print(f"[ERROR][is_module_enabled] Database error: {str(e)}")
            if self.role == 'admin':
                return True
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
        
        # 部门负责人可见同公司同部门所有成员
        if getattr(self, 'is_department_manager', False) and getattr(self, 'department', None) and getattr(self, 'company_name', None):
            dept_users = User.query.filter_by(department=self.department, company_name=self.company_name).all()
            for u in dept_users:
                if u.id not in viewable_ids:
                    viewable_ids.append(u.id)
        
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

    def is_vendor_user(self):
        """检查用户是否属于厂商企业"""
        if not self.company_name:
            return False
        
        from app.models.dictionary import Dictionary
        company_dict = Dictionary.query.filter_by(
            type='company',
            value=self.company_name,
            is_active=True,
            is_vendor=True
        ).first()
        
        return company_dict is not None

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

    # ── Claude AI 代理 ────────────────────────────────────────────────────

    def generate_claude_ai_token(self):
        """生成新的 Claude AI 代理 token，格式 cp-{user_id}-{random32}"""
        import secrets
        return f"cp-{self.id}-{secrets.token_urlsafe(24)}"

    def enable_claude_ai(self, quota_tokens=None):
        """启用 Claude AI 代理；返回 (token, is_new) 元组。已启用则不重发 token。"""
        is_new = False
        if not self.claude_ai_token:
            self.claude_ai_token = self.generate_claude_ai_token()
            is_new = True
        self.claude_ai_enabled = True
        if self.claude_ai_enabled_at is None:
            self.claude_ai_enabled_at = datetime.utcnow()
        if quota_tokens is not None:
            self.claude_ai_quota_tokens = int(quota_tokens)
        return self.claude_ai_token, is_new

    def reset_claude_ai_token(self):
        """重置 token（旧 token 立即失效）；返回新 token。"""
        self.claude_ai_token = self.generate_claude_ai_token()
        return self.claude_ai_token

    def disable_claude_ai(self):
        """禁用 Claude AI 代理（保留 token 不删除，便于审计）。"""
        self.claude_ai_enabled = False


class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module = db.Column(db.String(50), nullable=False)  # 模块名称
    can_view = db.Column(db.Boolean, default=False)  # 查看权限
    can_create = db.Column(db.Boolean, default=False)  # 创建权限
    can_edit = db.Column(db.Boolean, default=False)  # 编辑权限
    can_delete = db.Column(db.Boolean, default=False)  # 删除权限
    can_change_owner = db.Column(db.Boolean, default=False)  # 拥有人修改权限
    can_export_email = db.Column(db.Boolean, default=False)  # 导出邮箱权限

    # 权限级别相关字段（与角色权限表保持一致）
    permission_level = db.Column(db.String(20), default='personal')  # 权限级别：system, company, department, personal
    permission_level_description = db.Column(db.Text)  # 权限级别说明
    pricing_discount_limit = db.Column(db.Float, nullable=True)  # 批价折扣下限（百分比形式）
    settlement_discount_limit = db.Column(db.Float, nullable=True)  # 结算折扣下限（百分比形式）
    content_filters = db.Column(db.JSON, nullable=True)  # 内容筛选配置，存储格式：{"project_type": ["type1", "type2"], "industry": ["ind1"]}

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
            'can_delete': self.can_delete,
            'can_change_owner': self.can_change_owner,
            'can_export_email': self.can_export_email,
            'permission_level': self.permission_level,
            'permission_level_description': self.permission_level_description,
            'pricing_discount_limit': self.pricing_discount_limit,
            'settlement_discount_limit': self.settlement_discount_limit,
            'content_filters': self.content_filters
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


class DataAffiliation(Affiliation):
    """
    兼容层：与Affiliation完全相同，用于保持向后兼容
    实际上直接使用Affiliation的功能
    
    这个类将逐步淘汰，所有新代码应直接使用Affiliation
    """
    __table__ = Affiliation.__table__
    
    def __repr__(self):
        return f'<DataAffiliation(兼容层) {self.owner_id}->{self.viewer_id}>'

def sync_department_manager_affiliations(manager_user):
    """
    同步部门负责人与本部门所有成员的归属关系（viewer为负责人，owner为成员，不能包括自己）
    """
    from app import db
    if not manager_user.is_department_manager or not manager_user.department or not manager_user.company_name:
        return
    # 获取本部门所有成员（不包括自己）
    members = User.query.filter(
        User.department == manager_user.department,
        User.company_name == manager_user.company_name,
        User.id != manager_user.id
    ).all()
    for member in members:
        # 检查是否已存在归属关系
        exists = Affiliation.query.filter_by(owner_id=member.id, viewer_id=manager_user.id).first()
        if not exists:
            db.session.add(Affiliation(owner_id=member.id, viewer_id=manager_user.id))
    db.session.commit()

def remove_department_manager_affiliations(manager_user):
    """
    移除该负责人和本部门成员的所有归属关系
    """
    from app import db
    if not manager_user.department or not manager_user.company_name:
        return
    Affiliation.query.filter(
        Affiliation.viewer_id == manager_user.id,
        Affiliation.owner.has(department=manager_user.department, company_name=manager_user.company_name)
    ).delete(synchronize_session=False)
    db.session.commit()

def sync_affiliations_for_new_member(new_member):
    """
    新成员加入部门时，自动为本部门所有负责人添加归属关系
    """
    from app import db
    if not new_member.department or not new_member.company_name:
        return
    managers = User.query.filter_by(department=new_member.department, company_name=new_member.company_name, is_department_manager=True).all()
    for manager in managers:
        if manager.id == new_member.id:
            continue
        exists = Affiliation.query.filter_by(owner_id=new_member.id, viewer_id=manager.id).first()
        if not exists:
            db.session.add(Affiliation(owner_id=new_member.id, viewer_id=manager.id))
    db.session.commit()

def transfer_member_affiliations_on_department_change(user, old_department, old_company):
    """
    当员工部门或公司变更时，自动将其从原部门所有负责人的归属关系中移除，并添加到新部门所有负责人的归属关系中。
    """
    from app import db
    # 1. 移除原部门所有负责人对该员工的归属
    if old_department and old_company:
        old_managers = User.query.filter_by(department=old_department, company_name=old_company, is_department_manager=True).all()
        for manager in old_managers:
            db.session.query(Affiliation).filter_by(owner_id=user.id, viewer_id=manager.id).delete()
    # 2. 添加到新部门所有负责人的归属
    if user.department and user.company_name:
        new_managers = User.query.filter_by(department=user.department, company_name=user.company_name, is_department_manager=True).all()
        for manager in new_managers:
            exists = Affiliation.query.filter_by(owner_id=user.id, viewer_id=manager.id).first()
            if not exists and manager.id != user.id:
                db.session.add(Affiliation(owner_id=user.id, viewer_id=manager.id))
    db.session.commit() 