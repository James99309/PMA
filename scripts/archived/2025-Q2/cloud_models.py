from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, Double, Enum, ForeignKeyConstraint, Index, Integer, JSON, Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import decimal

class Base(DeclarativeBase):
    pass


class Dictionaries(Base):
    __tablename__ = 'dictionaries'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='dictionaries_pkey'),
        UniqueConstraint('type', 'key', name='uix_type_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50))
    key: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[float]] = mapped_column(Double(53))
    updated_at: Mapped[Optional[float]] = mapped_column(Double(53))


class EventRegistry(Base):
    __tablename__ = 'event_registry'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='event_registry_pkey'),
        UniqueConstraint('event_key', name='event_registry_event_key_key'),
        Index('ix_event_registry_event_key', 'event_key', unique=True)
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_key: Mapped[str] = mapped_column(String(50), comment='事件唯一键')
    label_zh: Mapped[str] = mapped_column(String(100), comment='中文名称')
    label_en: Mapped[str] = mapped_column(String(100), comment='英文名称')
    default_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, comment='是否默认开启')
    enabled: Mapped[Optional[bool]] = mapped_column(Boolean, comment='是否在通知中心展示')
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    user_event_subscriptions: Mapped[List['UserEventSubscriptions']] = relationship('UserEventSubscriptions', back_populates='event')


class ProductCategories(Base):
    __tablename__ = 'product_categories'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='product_categories_pkey'),
        UniqueConstraint('code_letter', name='product_categories_code_letter_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    code_letter: Mapped[str] = mapped_column(String(1))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    product_subcategories: Mapped[List['ProductSubcategories']] = relationship('ProductSubcategories', back_populates='category')
    dev_products: Mapped[List['DevProducts']] = relationship('DevProducts', back_populates='category')
    product_codes: Mapped[List['ProductCodes']] = relationship('ProductCodes', back_populates='category')


class ProductRegions(Base):
    __tablename__ = 'product_regions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='product_regions_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    code_letter: Mapped[str] = mapped_column(String(1))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    dev_products: Mapped[List['DevProducts']] = relationship('DevProducts', back_populates='region')


class RolePermissions(Base):
    __tablename__ = 'role_permissions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='role_permissions_pkey'),
        UniqueConstraint('role', 'module', name='uix_role_module')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(50))
    module: Mapped[str] = mapped_column(String(50))
    can_view: Mapped[Optional[bool]] = mapped_column(Boolean)
    can_create: Mapped[Optional[bool]] = mapped_column(Boolean)
    can_edit: Mapped[Optional[bool]] = mapped_column(Boolean)
    can_delete: Mapped[Optional[bool]] = mapped_column(Boolean)


class SystemSettings(Base):
    __tablename__ = 'system_settings'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='system_settings_pkey'),
        Index('ix_system_settings_key', 'key', unique=True)
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100))
    value: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key'),
        UniqueConstraint('username', name='users_username_key'),
        UniqueConstraint('wechat_openid', name='users_wechat_openid_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(256))
    real_name: Mapped[Optional[str]] = mapped_column(String(80))
    company_name: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    is_department_manager: Mapped[Optional[bool]] = mapped_column(Boolean)
    role: Mapped[Optional[str]] = mapped_column(String(20))
    is_profile_complete: Mapped[Optional[bool]] = mapped_column(Boolean)
    wechat_openid: Mapped[Optional[str]] = mapped_column(String(64))
    wechat_nickname: Mapped[Optional[str]] = mapped_column(String(64))
    wechat_avatar: Mapped[Optional[str]] = mapped_column(String(256))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[Optional[float]] = mapped_column(Double(53))
    last_login: Mapped[Optional[float]] = mapped_column(Double(53))
    updated_at: Mapped[Optional[float]] = mapped_column(Double(53))

    affiliations: Mapped[List['Affiliations']] = relationship('Affiliations', foreign_keys='[Affiliations.owner_id]', back_populates='owner')
    affiliations_: Mapped[List['Affiliations']] = relationship('Affiliations', foreign_keys='[Affiliations.viewer_id]', back_populates='viewer')
    approval_process_template: Mapped[List['ApprovalProcessTemplate']] = relationship('ApprovalProcessTemplate', back_populates='users')
    companies: Mapped[List['Companies']] = relationship('Companies', back_populates='owner')
    permissions: Mapped[List['Permissions']] = relationship('Permissions', back_populates='user')
    products: Mapped[List['Products']] = relationship('Products', back_populates='owner')
    projects: Mapped[List['Projects']] = relationship('Projects', back_populates='owner')
    user_event_subscriptions: Mapped[List['UserEventSubscriptions']] = relationship('UserEventSubscriptions', foreign_keys='[UserEventSubscriptions.target_user_id]', back_populates='target_user')
    user_event_subscriptions_: Mapped[List['UserEventSubscriptions']] = relationship('UserEventSubscriptions', foreign_keys='[UserEventSubscriptions.user_id]', back_populates='user')
    approval_instance: Mapped[List['ApprovalInstance']] = relationship('ApprovalInstance', back_populates='users')
    approval_step: Mapped[List['ApprovalStep']] = relationship('ApprovalStep', back_populates='approver_user')
    contacts: Mapped[List['Contacts']] = relationship('Contacts', back_populates='owner')
    dev_products: Mapped[List['DevProducts']] = relationship('DevProducts', foreign_keys='[DevProducts.created_by]', back_populates='users')
    dev_products_: Mapped[List['DevProducts']] = relationship('DevProducts', foreign_keys='[DevProducts.owner_id]', back_populates='owner')
    product_codes: Mapped[List['ProductCodes']] = relationship('ProductCodes', back_populates='users')
    project_members: Mapped[List['ProjectMembers']] = relationship('ProjectMembers', back_populates='user')
    project_stage_history: Mapped[List['ProjectStageHistory']] = relationship('ProjectStageHistory', back_populates='user')
    actions: Mapped[List['Actions']] = relationship('Actions', back_populates='owner')
    approval_record: Mapped[List['ApprovalRecord']] = relationship('ApprovalRecord', back_populates='approver')
    quotations: Mapped[List['Quotations']] = relationship('Quotations', back_populates='owner')
    action_reply: Mapped[List['ActionReply']] = relationship('ActionReply', back_populates='owner')


class Affiliations(Base):
    __tablename__ = 'affiliations'
    __table_args__ = (
        ForeignKeyConstraint(['owner_id'], ['users.id'], name='affiliations_owner_id_fkey'),
        ForeignKeyConstraint(['viewer_id'], ['users.id'], name='affiliations_viewer_id_fkey'),
        PrimaryKeyConstraint('id', name='affiliations_pkey'),
        UniqueConstraint('owner_id', 'viewer_id', name='uix_owner_viewer')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer)
    viewer_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[Optional[float]] = mapped_column(Double(53))

    owner: Mapped['Users'] = relationship('Users', foreign_keys=[owner_id], back_populates='affiliations')
    viewer: Mapped['Users'] = relationship('Users', foreign_keys=[viewer_id], back_populates='affiliations_')


class ApprovalProcessTemplate(Base):
    __tablename__ = 'approval_process_template'
    __table_args__ = (
        ForeignKeyConstraint(['created_by'], ['users.id'], name='approval_process_template_created_by_fkey'),
        PrimaryKeyConstraint('id', name='approval_process_template_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), comment='流程名称')
    object_type: Mapped[str] = mapped_column(String(50), comment='适用对象（如 quotation）')
    created_by: Mapped[int] = mapped_column(Integer, comment='创建人账号ID')
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, comment='是否启用')
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    required_fields: Mapped[Optional[dict]] = mapped_column(JSON, comment='发起审批时必填字段列表')

    users: Mapped['Users'] = relationship('Users', back_populates='approval_process_template')
    approval_instance: Mapped[List['ApprovalInstance']] = relationship('ApprovalInstance', back_populates='process')
    approval_step: Mapped[List['ApprovalStep']] = relationship('ApprovalStep', back_populates='process')


class Companies(Base):
    __tablename__ = 'companies'
    __table_args__ = (
        ForeignKeyConstraint(['owner_id'], ['users.id'], name='companies_owner_id_fkey'),
        PrimaryKeyConstraint('id', name='companies_pkey'),
        UniqueConstraint('company_code', name='companies_company_code_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_code: Mapped[str] = mapped_column(String(20))
    company_name: Mapped[str] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(50))
    region: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(String(200))
    industry: Mapped[Optional[str]] = mapped_column(String(50))
    company_type: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer)
    shared_with_users: Mapped[Optional[dict]] = mapped_column(JSON)
    share_contacts: Mapped[Optional[bool]] = mapped_column(Boolean)

    owner: Mapped[Optional['Users']] = relationship('Users', back_populates='companies')
    contacts: Mapped[List['Contacts']] = relationship('Contacts', back_populates='company')
    actions: Mapped[List['Actions']] = relationship('Actions', back_populates='company')


class Permissions(Base):
    __tablename__ = 'permissions'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], name='permissions_user_id_fkey'),
        PrimaryKeyConstraint('id', name='permissions_pkey'),
        UniqueConstraint('user_id', 'module', name='uix_user_module')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    module: Mapped[str] = mapped_column(String(50))
    can_view: Mapped[Optional[bool]] = mapped_column(Boolean)
    can_create: Mapped[Optional[bool]] = mapped_column(Boolean)
    can_edit: Mapped[Optional[bool]] = mapped_column(Boolean)
    can_delete: Mapped[Optional[bool]] = mapped_column(Boolean)

    user: Mapped['Users'] = relationship('Users', back_populates='permissions')


class ProductSubcategories(Base):
    __tablename__ = 'product_subcategories'
    __table_args__ = (
        ForeignKeyConstraint(['category_id'], ['product_categories.id'], name='product_subcategories_category_id_fkey'),
        PrimaryKeyConstraint('id', name='product_subcategories_pkey'),
        UniqueConstraint('category_id', 'code_letter', name='uq_subcategory_code_letter')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))
    code_letter: Mapped[str] = mapped_column(String(1))
    description: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    category: Mapped['ProductCategories'] = relationship('ProductCategories', back_populates='product_subcategories')
    dev_products: Mapped[List['DevProducts']] = relationship('DevProducts', back_populates='subcategory')
    product_code_fields: Mapped[List['ProductCodeFields']] = relationship('ProductCodeFields', back_populates='subcategory')
    product_codes: Mapped[List['ProductCodes']] = relationship('ProductCodes', back_populates='subcategory')


class Products(Base):
    __tablename__ = 'products'
    __table_args__ = (
        ForeignKeyConstraint(['owner_id'], ['users.id'], name='products_owner_id_fkey'),
        PrimaryKeyConstraint('id', name='products_pkey'),
        UniqueConstraint('product_mn', name='products_product_mn_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[Optional[str]] = mapped_column(String(50))
    category: Mapped[Optional[str]] = mapped_column(String(50))
    product_mn: Mapped[Optional[str]] = mapped_column(String(50))
    product_name: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    specification: Mapped[Optional[str]] = mapped_column(Text)
    brand: Mapped[Optional[str]] = mapped_column(String(50))
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    retail_price: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 2))
    status: Mapped[Optional[str]] = mapped_column(String(20))
    image_path: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer)

    owner: Mapped[Optional['Users']] = relationship('Users', back_populates='products')
    product_codes: Mapped[List['ProductCodes']] = relationship('ProductCodes', back_populates='product')


class Projects(Base):
    __tablename__ = 'projects'
    __table_args__ = (
        ForeignKeyConstraint(['owner_id'], ['users.id'], name='projects_owner_id_fkey'),
        PrimaryKeyConstraint('id', name='projects_pkey'),
        Index('ix_projects_authorization_code', 'authorization_code'),
        Index('ix_projects_project_name', 'project_name')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_name: Mapped[str] = mapped_column(String(64))
    report_time: Mapped[Optional[datetime.date]] = mapped_column(Date)
    project_type: Mapped[Optional[str]] = mapped_column(String(64))
    report_source: Mapped[Optional[str]] = mapped_column(String(64))
    product_situation: Mapped[Optional[str]] = mapped_column(String(128))
    end_user: Mapped[Optional[str]] = mapped_column(String(128))
    design_issues: Mapped[Optional[str]] = mapped_column(String(128))
    dealer: Mapped[Optional[str]] = mapped_column(String(128))
    contractor: Mapped[Optional[str]] = mapped_column(String(128))
    system_integrator: Mapped[Optional[str]] = mapped_column(String(128))
    current_stage: Mapped[Optional[str]] = mapped_column(String(64))
    stage_description: Mapped[Optional[str]] = mapped_column(Text)
    authorization_code: Mapped[Optional[str]] = mapped_column(String(64))
    delivery_forecast: Mapped[Optional[datetime.date]] = mapped_column(Date)
    quotation_customer: Mapped[Optional[float]] = mapped_column(Double(53))
    authorization_status: Mapped[Optional[str]] = mapped_column(String(20))
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    owner_id: Mapped[Optional[int]] = mapped_column(Integer)

    owner: Mapped[Optional['Users']] = relationship('Users', back_populates='projects')
    project_members: Mapped[List['ProjectMembers']] = relationship('ProjectMembers', back_populates='project')
    project_stage_history: Mapped[List['ProjectStageHistory']] = relationship('ProjectStageHistory', back_populates='project')
    actions: Mapped[List['Actions']] = relationship('Actions', back_populates='project')
    quotations: Mapped[List['Quotations']] = relationship('Quotations', back_populates='project')


class UserEventSubscriptions(Base):
    __tablename__ = 'user_event_subscriptions'
    __table_args__ = (
        ForeignKeyConstraint(['event_id'], ['event_registry.id'], name='user_event_subscriptions_event_id_fkey'),
        ForeignKeyConstraint(['target_user_id'], ['users.id'], name='user_event_subscriptions_target_user_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='user_event_subscriptions_user_id_fkey'),
        PrimaryKeyConstraint('id', name='user_event_subscriptions_pkey'),
        UniqueConstraint('user_id', 'target_user_id', 'event_id', name='uq_user_target_event')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, comment='订阅者用户ID')
    target_user_id: Mapped[int] = mapped_column(Integer, comment='被订阅的用户ID')
    event_id: Mapped[int] = mapped_column(Integer, comment='事件ID')
    enabled: Mapped[Optional[bool]] = mapped_column(Boolean, comment='是否启用订阅')
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    event: Mapped['EventRegistry'] = relationship('EventRegistry', back_populates='user_event_subscriptions')
    target_user: Mapped['Users'] = relationship('Users', foreign_keys=[target_user_id], back_populates='user_event_subscriptions')
    user: Mapped['Users'] = relationship('Users', foreign_keys=[user_id], back_populates='user_event_subscriptions_')


class ApprovalInstance(Base):
    __tablename__ = 'approval_instance'
    __table_args__ = (
        ForeignKeyConstraint(['created_by'], ['users.id'], name='approval_instance_created_by_fkey'),
        ForeignKeyConstraint(['process_id'], ['approval_process_template.id'], name='approval_instance_process_id_fkey'),
        PrimaryKeyConstraint('id', name='approval_instance_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    process_id: Mapped[int] = mapped_column(Integer, comment='流程模板ID')
    object_id: Mapped[int] = mapped_column(Integer, comment='对应单据ID')
    object_type: Mapped[str] = mapped_column(String(50), comment='单据类型（如 project）')
    created_by: Mapped[int] = mapped_column(Integer, comment='发起人ID')
    current_step: Mapped[Optional[int]] = mapped_column(Integer, comment='当前步骤序号')
    status: Mapped[Optional[str]] = mapped_column(Enum('PENDING', 'APPROVED', 'REJECTED', name='approvalstatus'), comment='状态')
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='流程发起时间')
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='审批完成时间')

    users: Mapped['Users'] = relationship('Users', back_populates='approval_instance')
    process: Mapped['ApprovalProcessTemplate'] = relationship('ApprovalProcessTemplate', back_populates='approval_instance')
    approval_record: Mapped[List['ApprovalRecord']] = relationship('ApprovalRecord', back_populates='instance')


class ApprovalStep(Base):
    __tablename__ = 'approval_step'
    __table_args__ = (
        ForeignKeyConstraint(['approver_user_id'], ['users.id'], name='approval_step_approver_user_id_fkey'),
        ForeignKeyConstraint(['process_id'], ['approval_process_template.id'], name='approval_step_process_id_fkey'),
        PrimaryKeyConstraint('id', name='approval_step_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    process_id: Mapped[int] = mapped_column(Integer, comment='所属流程模板')
    step_order: Mapped[int] = mapped_column(Integer, comment='流程顺序')
    approver_user_id: Mapped[int] = mapped_column(Integer, comment='审批人账号ID')
    step_name: Mapped[str] = mapped_column(String(100), comment='步骤说明（如"财务审批"）')
    send_email: Mapped[Optional[bool]] = mapped_column(Boolean, comment='是否发送邮件通知')
    action_type: Mapped[Optional[str]] = mapped_column(String(50), comment='步骤动作类型，如 authorization')
    action_params: Mapped[Optional[dict]] = mapped_column(JSON, comment='动作参数，JSON格式')

    approver_user: Mapped['Users'] = relationship('Users', back_populates='approval_step')
    process: Mapped['ApprovalProcessTemplate'] = relationship('ApprovalProcessTemplate', back_populates='approval_step')
    approval_record: Mapped[List['ApprovalRecord']] = relationship('ApprovalRecord', back_populates='step')


class Contacts(Base):
    __tablename__ = 'contacts'
    __table_args__ = (
        ForeignKeyConstraint(['company_id'], ['companies.id'], name='contacts_company_id_fkey'),
        ForeignKeyConstraint(['owner_id'], ['users.id'], name='contacts_owner_id_fkey'),
        PrimaryKeyConstraint('id', name='contacts_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(50))
    department: Mapped[Optional[str]] = mapped_column(String(50))
    position: Mapped[Optional[str]] = mapped_column(String(50))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer)
    override_share: Mapped[Optional[bool]] = mapped_column(Boolean)
    shared_disabled: Mapped[Optional[bool]] = mapped_column(Boolean)

    company: Mapped['Companies'] = relationship('Companies', back_populates='contacts')
    owner: Mapped[Optional['Users']] = relationship('Users', back_populates='contacts')
    actions: Mapped[List['Actions']] = relationship('Actions', back_populates='contact')
    quotations: Mapped[List['Quotations']] = relationship('Quotations', back_populates='contact')


class DevProducts(Base):
    __tablename__ = 'dev_products'
    __table_args__ = (
        ForeignKeyConstraint(['category_id'], ['product_categories.id'], name='dev_products_category_id_fkey'),
        ForeignKeyConstraint(['created_by'], ['users.id'], name='dev_products_created_by_fkey'),
        ForeignKeyConstraint(['owner_id'], ['users.id'], name='dev_products_owner_id_fkey'),
        ForeignKeyConstraint(['region_id'], ['product_regions.id'], name='dev_products_region_id_fkey'),
        ForeignKeyConstraint(['subcategory_id'], ['product_subcategories.id'], name='dev_products_subcategory_id_fkey'),
        PrimaryKeyConstraint('id', name='dev_products_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer)
    subcategory_id: Mapped[Optional[int]] = mapped_column(Integer)
    region_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[Optional[str]] = mapped_column(String(50))
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    retail_price: Mapped[Optional[float]] = mapped_column(Double(53))
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_path: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    mn_code: Mapped[Optional[str]] = mapped_column(String(20))

    category: Mapped[Optional['ProductCategories']] = relationship('ProductCategories', back_populates='dev_products')
    users: Mapped[Optional['Users']] = relationship('Users', foreign_keys=[created_by], back_populates='dev_products')
    owner: Mapped[Optional['Users']] = relationship('Users', foreign_keys=[owner_id], back_populates='dev_products_')
    region: Mapped[Optional['ProductRegions']] = relationship('ProductRegions', back_populates='dev_products')
    subcategory: Mapped[Optional['ProductSubcategories']] = relationship('ProductSubcategories', back_populates='dev_products')
    dev_product_specs: Mapped[List['DevProductSpecs']] = relationship('DevProductSpecs', back_populates='dev_product')


class ProductCodeFields(Base):
    __tablename__ = 'product_code_fields'
    __table_args__ = (
        ForeignKeyConstraint(['subcategory_id'], ['product_subcategories.id'], name='product_code_fields_subcategory_id_fkey'),
        PrimaryKeyConstraint('id', name='product_code_fields_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subcategory_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))
    field_type: Mapped[str] = mapped_column(String(20))
    position: Mapped[int] = mapped_column(Integer)
    code: Mapped[Optional[str]] = mapped_column(String(10))
    description: Mapped[Optional[str]] = mapped_column(Text)
    max_length: Mapped[Optional[int]] = mapped_column(Integer)
    is_required: Mapped[Optional[bool]] = mapped_column(Boolean)
    use_in_code: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    subcategory: Mapped['ProductSubcategories'] = relationship('ProductSubcategories', back_populates='product_code_fields')
    product_code_field_options: Mapped[List['ProductCodeFieldOptions']] = relationship('ProductCodeFieldOptions', back_populates='field')
    product_code_field_values: Mapped[List['ProductCodeFieldValues']] = relationship('ProductCodeFieldValues', back_populates='field')


class ProductCodes(Base):
    __tablename__ = 'product_codes'
    __table_args__ = (
        ForeignKeyConstraint(['category_id'], ['product_categories.id'], name='product_codes_category_id_fkey'),
        ForeignKeyConstraint(['created_by'], ['users.id'], name='product_codes_created_by_fkey'),
        ForeignKeyConstraint(['product_id'], ['products.id'], name='product_codes_product_id_fkey'),
        ForeignKeyConstraint(['subcategory_id'], ['product_subcategories.id'], name='product_codes_subcategory_id_fkey'),
        PrimaryKeyConstraint('id', name='product_codes_pkey'),
        UniqueConstraint('full_code', name='product_codes_full_code_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer)
    category_id: Mapped[int] = mapped_column(Integer)
    subcategory_id: Mapped[int] = mapped_column(Integer)
    full_code: Mapped[str] = mapped_column(String(50))
    created_by: Mapped[int] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    category: Mapped['ProductCategories'] = relationship('ProductCategories', back_populates='product_codes')
    users: Mapped['Users'] = relationship('Users', back_populates='product_codes')
    product: Mapped['Products'] = relationship('Products', back_populates='product_codes')
    subcategory: Mapped['ProductSubcategories'] = relationship('ProductSubcategories', back_populates='product_codes')
    product_code_field_values: Mapped[List['ProductCodeFieldValues']] = relationship('ProductCodeFieldValues', back_populates='product_code')


class ProjectMembers(Base):
    __tablename__ = 'project_members'
    __table_args__ = (
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='project_members_project_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='project_members_user_id_fkey'),
        PrimaryKeyConstraint('id', name='project_members_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    project: Mapped['Projects'] = relationship('Projects', back_populates='project_members')
    user: Mapped['Users'] = relationship('Users', back_populates='project_members')


class ProjectStageHistory(Base):
    __tablename__ = 'project_stage_history'
    __table_args__ = (
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='project_stage_history_project_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='project_stage_history_user_id_fkey'),
        PrimaryKeyConstraint('id', name='project_stage_history_pkey'),
        Index('ix_project_stage_history_project_id', 'project_id'),
        Index('ix_project_stage_history_user_id', 'user_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer)
    to_stage: Mapped[str] = mapped_column(String(64))
    change_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    from_stage: Mapped[Optional[str]] = mapped_column(String(64))
    change_week: Mapped[Optional[int]] = mapped_column(Integer)
    change_month: Mapped[Optional[int]] = mapped_column(Integer)
    change_year: Mapped[Optional[int]] = mapped_column(Integer)
    account_id: Mapped[Optional[int]] = mapped_column(Integer)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    user_id: Mapped[Optional[int]] = mapped_column(Integer)

    project: Mapped['Projects'] = relationship('Projects', back_populates='project_stage_history')
    user: Mapped[Optional['Users']] = relationship('Users', back_populates='project_stage_history')


class Actions(Base):
    __tablename__ = 'actions'
    __table_args__ = (
        ForeignKeyConstraint(['company_id'], ['companies.id'], name='actions_company_id_fkey'),
        ForeignKeyConstraint(['contact_id'], ['contacts.id'], name='actions_contact_id_fkey'),
        ForeignKeyConstraint(['owner_id'], ['users.id'], name='actions_owner_id_fkey'),
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='actions_project_id_fkey'),
        PrimaryKeyConstraint('id', name='actions_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date)
    communication: Mapped[str] = mapped_column(Text)
    contact_id: Mapped[Optional[int]] = mapped_column(Integer)
    company_id: Mapped[Optional[int]] = mapped_column(Integer)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer)

    company: Mapped[Optional['Companies']] = relationship('Companies', back_populates='actions')
    contact: Mapped[Optional['Contacts']] = relationship('Contacts', back_populates='actions')
    owner: Mapped[Optional['Users']] = relationship('Users', back_populates='actions')
    project: Mapped[Optional['Projects']] = relationship('Projects', back_populates='actions')
    action_reply: Mapped[List['ActionReply']] = relationship('ActionReply', back_populates='action')


class ApprovalRecord(Base):
    __tablename__ = 'approval_record'
    __table_args__ = (
        ForeignKeyConstraint(['approver_id'], ['users.id'], name='approval_record_approver_id_fkey'),
        ForeignKeyConstraint(['instance_id'], ['approval_instance.id'], name='approval_record_instance_id_fkey'),
        ForeignKeyConstraint(['step_id'], ['approval_step.id'], name='approval_record_step_id_fkey'),
        PrimaryKeyConstraint('id', name='approval_record_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(Integer, comment='审批流程实例')
    step_id: Mapped[int] = mapped_column(Integer, comment='流程步骤ID')
    approver_id: Mapped[int] = mapped_column(Integer, comment='审批人ID')
    action: Mapped[str] = mapped_column(String(50), comment='同意/拒绝')
    comment: Mapped[Optional[str]] = mapped_column(Text, comment='审批意见')
    timestamp: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='审批时间')

    approver: Mapped['Users'] = relationship('Users', back_populates='approval_record')
    instance: Mapped['ApprovalInstance'] = relationship('ApprovalInstance', back_populates='approval_record')
    step: Mapped['ApprovalStep'] = relationship('ApprovalStep', back_populates='approval_record')


class DevProductSpecs(Base):
    __tablename__ = 'dev_product_specs'
    __table_args__ = (
        ForeignKeyConstraint(['dev_product_id'], ['dev_products.id'], name='dev_product_specs_dev_product_id_fkey'),
        PrimaryKeyConstraint('id', name='dev_product_specs_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dev_product_id: Mapped[Optional[int]] = mapped_column(Integer)
    field_name: Mapped[Optional[str]] = mapped_column(String(100))
    field_value: Mapped[Optional[str]] = mapped_column(String(255))
    field_code: Mapped[Optional[str]] = mapped_column(String(10))

    dev_product: Mapped[Optional['DevProducts']] = relationship('DevProducts', back_populates='dev_product_specs')


class ProductCodeFieldOptions(Base):
    __tablename__ = 'product_code_field_options'
    __table_args__ = (
        ForeignKeyConstraint(['field_id'], ['product_code_fields.id'], name='product_code_field_options_field_id_fkey'),
        PrimaryKeyConstraint('id', name='product_code_field_options_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    field_id: Mapped[int] = mapped_column(Integer)
    value: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(10))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean)
    position: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    field: Mapped['ProductCodeFields'] = relationship('ProductCodeFields', back_populates='product_code_field_options')
    product_code_field_values: Mapped[List['ProductCodeFieldValues']] = relationship('ProductCodeFieldValues', back_populates='option')


class Quotations(Base):
    __tablename__ = 'quotations'
    __table_args__ = (
        ForeignKeyConstraint(['contact_id'], ['contacts.id'], name='quotations_contact_id_fkey'),
        ForeignKeyConstraint(['owner_id'], ['users.id'], name='quotations_owner_id_fkey'),
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='quotations_project_id_fkey'),
        PrimaryKeyConstraint('id', name='quotations_pkey'),
        UniqueConstraint('quotation_number', name='quotations_quotation_number_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quotation_number: Mapped[str] = mapped_column(String(20))
    project_id: Mapped[int] = mapped_column(Integer)
    contact_id: Mapped[Optional[int]] = mapped_column(Integer)
    amount: Mapped[Optional[float]] = mapped_column(Double(53))
    project_stage: Mapped[Optional[str]] = mapped_column(String(20))
    project_type: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    owner_id: Mapped[Optional[int]] = mapped_column(Integer)

    contact: Mapped[Optional['Contacts']] = relationship('Contacts', back_populates='quotations')
    owner: Mapped[Optional['Users']] = relationship('Users', back_populates='quotations')
    project: Mapped['Projects'] = relationship('Projects', back_populates='quotations')
    quotation_details: Mapped[List['QuotationDetails']] = relationship('QuotationDetails', back_populates='quotation')


class ActionReply(Base):
    __tablename__ = 'action_reply'
    __table_args__ = (
        ForeignKeyConstraint(['action_id'], ['actions.id'], name='action_reply_action_id_fkey'),
        ForeignKeyConstraint(['owner_id'], ['users.id'], name='action_reply_owner_id_fkey'),
        ForeignKeyConstraint(['parent_reply_id'], ['action_reply.id'], name='action_reply_parent_reply_id_fkey'),
        PrimaryKeyConstraint('id', name='action_reply_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action_id: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(Integer)
    parent_reply_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    action: Mapped['Actions'] = relationship('Actions', back_populates='action_reply')
    owner: Mapped['Users'] = relationship('Users', back_populates='action_reply')
    parent_reply: Mapped[Optional['ActionReply']] = relationship('ActionReply', remote_side=[id], back_populates='parent_reply_reverse')
    parent_reply_reverse: Mapped[List['ActionReply']] = relationship('ActionReply', remote_side=[parent_reply_id], back_populates='parent_reply')


class ProductCodeFieldValues(Base):
    __tablename__ = 'product_code_field_values'
    __table_args__ = (
        ForeignKeyConstraint(['field_id'], ['product_code_fields.id'], name='product_code_field_values_field_id_fkey'),
        ForeignKeyConstraint(['option_id'], ['product_code_field_options.id'], name='product_code_field_values_option_id_fkey'),
        ForeignKeyConstraint(['product_code_id'], ['product_codes.id'], name='product_code_field_values_product_code_id_fkey'),
        PrimaryKeyConstraint('id', name='product_code_field_values_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_code_id: Mapped[int] = mapped_column(Integer)
    field_id: Mapped[int] = mapped_column(Integer)
    option_id: Mapped[Optional[int]] = mapped_column(Integer)
    custom_value: Mapped[Optional[str]] = mapped_column(String(100))

    field: Mapped['ProductCodeFields'] = relationship('ProductCodeFields', back_populates='product_code_field_values')
    option: Mapped[Optional['ProductCodeFieldOptions']] = relationship('ProductCodeFieldOptions', back_populates='product_code_field_values')
    product_code: Mapped['ProductCodes'] = relationship('ProductCodes', back_populates='product_code_field_values')


class QuotationDetails(Base):
    __tablename__ = 'quotation_details'
    __table_args__ = (
        ForeignKeyConstraint(['quotation_id'], ['quotations.id'], name='quotation_details_quotation_id_fkey'),
        PrimaryKeyConstraint('id', name='quotation_details_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quotation_id: Mapped[Optional[int]] = mapped_column(Integer)
    product_name: Mapped[Optional[str]] = mapped_column(String(100))
    product_model: Mapped[Optional[str]] = mapped_column(String(100))
    product_desc: Mapped[Optional[str]] = mapped_column(Text)
    brand: Mapped[Optional[str]] = mapped_column(String(50))
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    discount: Mapped[Optional[float]] = mapped_column(Double(53))
    market_price: Mapped[Optional[float]] = mapped_column(Double(53))
    unit_price: Mapped[Optional[float]] = mapped_column(Double(53))
    total_price: Mapped[Optional[float]] = mapped_column(Double(53))
    product_mn: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    quotation: Mapped[Optional['Quotations']] = relationship('Quotations', back_populates='quotation_details')
