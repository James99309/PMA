"""添加权限模块表和子功能表

Revision ID: add_permission_modules_20251228
Revises:
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import time

# revision identifiers, used by Alembic.
revision = 'add_permission_modules_20251228'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建权限模块表、子功能表和初始化数据"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. 创建 permission_modules 表
    if 'permission_modules' not in existing_tables:
        op.create_table(
            'permission_modules',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('module_id', sa.String(50), unique=True, nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('name_en', sa.String(100)),
            sa.Column('icon', sa.String(50)),
            sa.Column('description', sa.String(500)),
            sa.Column('description_en', sa.String(500)),
            sa.Column('group_name', sa.String(50)),
            sa.Column('group_name_en', sa.String(50)),
            sa.Column('sort_order', sa.Integer(), default=0),
            sa.Column('supports_discount', sa.Boolean(), default=False),
            sa.Column('supports_owner_change', sa.Boolean(), default=False),
            sa.Column('supports_affiliation', sa.Boolean(), default=False),
            sa.Column('supports_content_filter', sa.Boolean(), default=False),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.Float(), default=time.time),
            sa.Column('updated_at', sa.Float(), default=time.time),
        )
        op.create_index('idx_permission_modules_group', 'permission_modules', ['group_name'])
        op.create_index('idx_permission_modules_sort', 'permission_modules', ['sort_order'])
        print("✓ 创建表 permission_modules")
    else:
        print("- 表 permission_modules 已存在，跳过")

    # 2. 创建 permission_module_features 表
    if 'permission_module_features' not in existing_tables:
        op.create_table(
            'permission_module_features',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('module_id', sa.String(50), nullable=False),
            sa.Column('feature_id', sa.String(50), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('name_en', sa.String(100)),
            sa.Column('icon', sa.String(50)),
            sa.Column('description', sa.String(500)),
            sa.Column('sort_order', sa.Integer(), default=0),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.Float(), default=time.time),
            sa.Column('updated_at', sa.Float(), default=time.time),
            sa.UniqueConstraint('module_id', 'feature_id', name='uix_module_feature'),
            sa.ForeignKeyConstraint(['module_id'], ['permission_modules.module_id'])
        )
        print("✓ 创建表 permission_module_features")
    else:
        print("- 表 permission_module_features 已存在，跳过")

    # 3. 创建 role_feature_permissions 表
    if 'role_feature_permissions' not in existing_tables:
        op.create_table(
            'role_feature_permissions',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('role', sa.String(50), nullable=False),
            sa.Column('module_id', sa.String(50), nullable=False),
            sa.Column('feature_id', sa.String(50), nullable=False),
            sa.Column('is_enabled', sa.Boolean(), default=True),
            sa.Column('created_at', sa.Float(), default=time.time),
            sa.Column('updated_at', sa.Float(), default=time.time),
            sa.UniqueConstraint('role', 'module_id', 'feature_id', name='uix_role_module_feature'),
        )
        print("✓ 创建表 role_feature_permissions")
    else:
        print("- 表 role_feature_permissions 已存在，跳过")

    # 4. 初始化权限模块数据（21个模块，按导航栏顺序）
    now = time.time()
    modules = [
        # 业务管理
        ('customer', '客户管理', 'Customer', 'contacts', '管理客户信息和联系人', 'Manage customer information', '业务管理', 'Business', 1, False, True, True, True),
        ('project', '项目管理', 'Project', 'cases', '管理销售项目和跟进', 'Manage sales projects', '业务管理', 'Business', 2, False, True, True, True),
        ('quotation', '报价管理', 'Quotation', 'request_quote', '管理产品报价', 'Manage quotations', '业务管理', 'Business', 3, False, True, True, False),
        ('expense', '报销管理', 'Expense', 'receipt_long', '管理员工报销申请', 'Manage expense claims', '业务管理', 'Business', 4, False, False, False, False),
        # 产品管理
        ('product', '产品管理', 'Product', 'inventory_2', '管理产品信息和价格', 'Manage products', '产品管理', 'Product', 5, False, False, False, False),
        ('product_code', '产品编码', 'Product Code', 'category', '管理产品编码系统', 'Manage product codes', '产品管理', 'Product', 6, False, False, False, False),
        # 订单结算
        ('order', '订单管理', 'Order', 'list_alt', '管理销售订单', 'Manage orders', '订单结算', 'Order', 7, False, False, False, False),
        ('settlement', '结算管理', 'Settlement', 'payments', '管理财务结算', 'Manage settlement', '订单结算', 'Order', 8, False, False, False, False),
        ('inventory', '库存管理', 'Inventory', 'warehouse', '管理产品库存', 'Manage inventory', '订单结算', 'Order', 9, False, False, False, False),
        ('pricing_order', '批价单管理', 'Pricing Order', 'sell', '管理批价单', 'Manage pricing orders', '订单结算', 'Order', 10, True, False, False, False),
        ('settlement_order', '结算单管理', 'Settlement Order', 'credit_card', '管理结算单', 'Manage settlement orders', '订单结算', 'Order', 11, True, False, False, False),
        # 账户管理
        ('user_management', '用户管理', 'User', 'group', '管理系统用户', 'Manage users', '账户管理', 'Account', 12, False, False, False, False),
        ('config_management', '配置管理', 'Configuration', 'settings', '管理系统权限和配置', 'Manage system permissions', '账户管理', 'Account', 13, False, False, False, False),
        ('dictionary_management', '字典管理', 'Dictionary', 'menu_book', '管理系统字典数据', 'Manage dictionaries', '账户管理', 'Account', 14, False, False, False, False),
        # 系统管理
        ('approval', '审批中心', 'Approval Center', 'task_alt', '管理审批流程和审批记录', 'Manage approval workflows', '系统管理', 'System', 15, False, False, False, False),
        ('system_settings', '系统参数设置', 'System Settings', 'settings_applications', '管理系统参数配置', 'Manage system settings', '系统管理', 'System', 16, False, False, False, False),
        ('version_management', '版本管理', 'Version Management', 'update', '管理系统版本', 'Manage system versions', '系统管理', 'System', 17, False, False, False, False),
        ('approval_config', '审批流程配置', 'Approval Config', 'rule', '配置审批流程模板', 'Configure approval workflows', '系统管理', 'System', 18, False, False, False, False),
        ('notification', '通知中心', 'Notification Center', 'notifications', '管理系统通知', 'Manage notifications', '系统管理', 'System', 19, False, False, False, False),
        ('change_history', '历史记录', 'Change History', 'history', '查看操作历史记录', 'View change history', '系统管理', 'System', 20, False, False, False, False),
        ('backup', '数据库备份', 'Database Backup', 'cloud_upload', '管理数据库备份', 'Manage database backups', '系统管理', 'System', 21, False, False, False, False),
    ]

    for m in modules:
        existing = conn.execute(text(
            "SELECT id FROM permission_modules WHERE module_id = :module_id"
        ), {'module_id': m[0]}).fetchone()

        if existing:
            # 更新现有记录
            conn.execute(text("""
                UPDATE permission_modules SET
                    name = :name, name_en = :name_en, icon = :icon,
                    description = :description, description_en = :description_en,
                    group_name = :group_name, group_name_en = :group_name_en,
                    sort_order = :sort_order,
                    supports_discount = :supports_discount,
                    supports_owner_change = :supports_owner_change,
                    supports_affiliation = :supports_affiliation,
                    supports_content_filter = :supports_content_filter,
                    updated_at = :updated_at
                WHERE module_id = :module_id
            """), {
                'module_id': m[0], 'name': m[1], 'name_en': m[2], 'icon': m[3],
                'description': m[4], 'description_en': m[5],
                'group_name': m[6], 'group_name_en': m[7], 'sort_order': m[8],
                'supports_discount': m[9], 'supports_owner_change': m[10],
                'supports_affiliation': m[11], 'supports_content_filter': m[12],
                'updated_at': now
            })
        else:
            # 插入新记录
            conn.execute(text("""
                INSERT INTO permission_modules
                (module_id, name, name_en, icon, description, description_en,
                 group_name, group_name_en, sort_order,
                 supports_discount, supports_owner_change, supports_affiliation, supports_content_filter,
                 is_active, created_at, updated_at)
                VALUES
                (:module_id, :name, :name_en, :icon, :description, :description_en,
                 :group_name, :group_name_en, :sort_order,
                 :supports_discount, :supports_owner_change, :supports_affiliation, :supports_content_filter,
                 true, :created_at, :updated_at)
            """), {
                'module_id': m[0], 'name': m[1], 'name_en': m[2], 'icon': m[3],
                'description': m[4], 'description_en': m[5],
                'group_name': m[6], 'group_name_en': m[7], 'sort_order': m[8],
                'supports_discount': m[9], 'supports_owner_change': m[10],
                'supports_affiliation': m[11], 'supports_content_filter': m[12],
                'created_at': now, 'updated_at': now
            })

    print(f"✓ 初始化权限模块数据 ({len(modules)} 条)")

    # 5. 初始化子功能数据（11个子功能）
    features = [
        # 用户管理模块 (user_management)
        ('user_management', 'tab_base', '基本信息', 'Basic Info', 'person', 1),
        ('user_management', 'tab_perm', '权限配置', 'Permissions', 'admin_panel_settings', 2),
        ('user_management', 'tab_aff', '归属关系', 'Affiliation', 'groups', 3),
        ('user_management', 'tab_perf', '绩效目标', 'Performance', 'trending_up', 4),
        ('user_management', 'tab_salary', '薪资明细', 'Salary', 'payments', 5),
        # 配置管理模块 (config_management)
        ('config_management', 'tab_perm', '权限配置', 'Permission Config', 'admin_panel_settings', 1),
        ('config_management', 'tab_perf', '绩效配置', 'Performance Config', 'monitoring', 2),
        ('config_management', 'tab_budget', '财务配置', 'Budget Config', 'account_balance', 3),
        # 审批中心模块 (approval)
        ('approval', 'tab_created', '我发起的', 'Created by Me', 'outbox', 1),
        ('approval', 'tab_pending', '待我审批', 'Pending Approval', 'pending_actions', 2),
        ('approval', 'tab_completed', '已完成的', 'Completed', 'check_circle', 3),
    ]

    for f in features:
        existing = conn.execute(text(
            "SELECT id FROM permission_module_features WHERE module_id = :module_id AND feature_id = :feature_id"
        ), {'module_id': f[0], 'feature_id': f[1]}).fetchone()

        if existing:
            conn.execute(text("""
                UPDATE permission_module_features SET
                    name = :name, name_en = :name_en, icon = :icon,
                    sort_order = :sort_order, updated_at = :updated_at
                WHERE module_id = :module_id AND feature_id = :feature_id
            """), {
                'module_id': f[0], 'feature_id': f[1],
                'name': f[2], 'name_en': f[3], 'icon': f[4], 'sort_order': f[5],
                'updated_at': now
            })
        else:
            conn.execute(text("""
                INSERT INTO permission_module_features
                (module_id, feature_id, name, name_en, icon, sort_order, is_active, created_at, updated_at)
                VALUES
                (:module_id, :feature_id, :name, :name_en, :icon, :sort_order, true, :created_at, :updated_at)
            """), {
                'module_id': f[0], 'feature_id': f[1],
                'name': f[2], 'name_en': f[3], 'icon': f[4], 'sort_order': f[5],
                'created_at': now, 'updated_at': now
            })

    print(f"✓ 初始化子功能数据 ({len(features)} 条)")
    print("\n=== 迁移完成 ===")


def downgrade():
    """删除表"""
    op.drop_table('role_feature_permissions')
    op.drop_table('permission_module_features')
    op.drop_table('permission_modules')
    print("✓ 删除权限模块相关表")
