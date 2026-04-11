"""CLI 权限体系：表归属注册 + 角色 CLI 查询开关与范围

- 新建 cli_table_modules 表：每张业务表的权限归属（模块/跟随）
- role_permissions 新增 cli_can_query / cli_permission_level 两字段
- seed 18 张业务表的归属数据
- seed cli_agent 权限模块 + admin 角色的 can_view=True

Revision ID: cli_perm_20260411
Revises: c1i7mem0001
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import time


revision = 'cli_perm_20260411'
down_revision = 'c1i7mem0001'
branch_labels = None
depends_on = None


# --- seed 数据 -------------------------------------------------------------

CLI_TABLE_MODULES_SEED = [
    # (table_name, display_name, mode, module, parent_table, description, sort_order)
    ('companies',                     '客户公司',     'module', 'customer',       None,           '客户公司主表', 10),
    ('contacts',                      '联系人',       'follow', None,             'companies',    '客户公司下的联系人', 20),
    ('actions',                       '行动记录',     'follow', None,             'companies',    '客户跟进记录', 30),

    ('projects',                      '项目',         'module', 'project',        None,           '销售项目主表', 40),
    ('project_customer_associations', '项目客户关联', 'follow', None,             'projects',     '项目与客户的多对多关联', 50),
    ('project_stage_history',         '项目阶段历史', 'follow', None,             'projects',     '项目阶段变更记录', 60),
    ('tasks',                         '任务',         'follow', None,             'projects',     '项目/客户相关任务', 70),

    ('quotations',                    '报价单',       'module', 'quotation',      None,           '报价单主表', 80),
    ('quotation_details',             '报价明细',     'follow', None,             'quotations',   '报价单明细行', 90),

    ('expenses',                      '报销单',       'module', 'expense',        None,           '员工报销单', 100),

    ('sales_orders',                  '客户订单',     'module', 'order',          None,           '销售订单', 110),
    ('shipments',                     '发货记录',     'follow', None,             'sales_orders', '销售订单发货', 120),
    ('purchase_orders',               '采购订单',     'module', 'order',          None,           '对外采购订单', 130),

    ('pricing_orders',                '批价单',       'module', 'pricing_order',  None,           '项目批价/结算单', 140),

    ('products',                      '产品',         'module', 'product',        None,           '产品库', 150),

    ('worklogs',                      '工作日志',     'module', 'worklog',        None,           '员工工作日志', 160),
    ('work_items',                    '工作项',       'follow', None,             'worklogs',     '工作日志下的工作项', 170),

    ('users',                         '用户',         'module', 'user',           None,           '员工名册', 180),
]


CLI_AGENT_MODULE_SEED = {
    'module_id': 'cli_agent',
    'name': '智能终端 (CLI)',
    'name_en': 'Smart Terminal',
    'icon': 'terminal',
    'description': '允许使用 AI 智能终端进行自然语言数据查询与分析',
    'description_en': 'Allow using the AI smart terminal for natural-language data queries',
    'group_name': '工具',
    'group_name_en': 'Tools',
    'sort_order': 900,
    'supports_discount': False,
    'supports_owner_change': False,
    'supports_affiliation': False,
    'supports_content_filter': False,
    'is_active': True,
}


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    now = time.time()

    # 1) role_permissions 加两个字段 -----------------------------------------
    existing_cols = {c['name'] for c in inspector.get_columns('role_permissions')}

    if 'cli_can_query' not in existing_cols:
        op.add_column(
            'role_permissions',
            sa.Column('cli_can_query', sa.Boolean(), server_default=sa.false(), nullable=False),
        )
        print('✓ role_permissions.cli_can_query 已添加')
    else:
        print('- role_permissions.cli_can_query 已存在，跳过')

    if 'cli_permission_level' not in existing_cols:
        op.add_column(
            'role_permissions',
            sa.Column('cli_permission_level', sa.String(20), nullable=True),
        )
        print('✓ role_permissions.cli_permission_level 已添加')
    else:
        print('- role_permissions.cli_permission_level 已存在，跳过')

    # 2) cli_table_modules 表 ------------------------------------------------
    if 'cli_table_modules' not in inspector.get_table_names():
        op.create_table(
            'cli_table_modules',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('table_name', sa.String(50), unique=True, nullable=False),
            sa.Column('display_name', sa.String(100)),
            sa.Column('mode', sa.String(20), nullable=False),  # 'module' | 'follow'
            sa.Column('module', sa.String(50), nullable=True),
            sa.Column('parent_table', sa.String(50), nullable=True),
            sa.Column('description', sa.String(300)),
            sa.Column('sort_order', sa.Integer(), default=0),
            sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
            sa.Column('created_at', sa.Float(), default=time.time),
            sa.Column('updated_at', sa.Float(), default=time.time),
        )
        op.create_index('idx_cli_table_modules_module', 'cli_table_modules', ['module'])
        print('✓ 创建表 cli_table_modules')
    else:
        print('- 表 cli_table_modules 已存在，跳过')

    # 3) seed cli_table_modules ---------------------------------------------
    existing_rows = conn.execute(text('SELECT table_name FROM cli_table_modules')).fetchall()
    existing_names = {r[0] for r in existing_rows}
    inserted = 0
    for (table_name, display_name, mode, module, parent_table, description, sort_order) in CLI_TABLE_MODULES_SEED:
        if table_name in existing_names:
            continue
        conn.execute(
            text("""
                INSERT INTO cli_table_modules
                    (table_name, display_name, mode, module, parent_table,
                     description, sort_order, is_active, created_at, updated_at)
                VALUES
                    (:table_name, :display_name, :mode, :module, :parent_table,
                     :description, :sort_order, TRUE, :now, :now)
            """),
            {
                'table_name': table_name,
                'display_name': display_name,
                'mode': mode,
                'module': module,
                'parent_table': parent_table,
                'description': description,
                'sort_order': sort_order,
                'now': now,
            },
        )
        inserted += 1
    print(f'✓ cli_table_modules seed: 新增 {inserted} 行（已存在 {len(existing_names)}）')

    # 4) seed permission_modules: cli_agent ---------------------------------
    exists = conn.execute(
        text("SELECT 1 FROM permission_modules WHERE module_id='cli_agent'")
    ).fetchone()
    if not exists:
        conn.execute(
            text("""
                INSERT INTO permission_modules
                    (module_id, name, name_en, icon, description, description_en,
                     group_name, group_name_en, sort_order,
                     supports_discount, supports_owner_change, supports_affiliation,
                     supports_content_filter, is_active, created_at, updated_at)
                VALUES
                    (:module_id, :name, :name_en, :icon, :description, :description_en,
                     :group_name, :group_name_en, :sort_order,
                     :supports_discount, :supports_owner_change, :supports_affiliation,
                     :supports_content_filter, :is_active, :now, :now)
            """),
            {**CLI_AGENT_MODULE_SEED, 'now': now},
        )
        print('✓ permission_modules 新增 cli_agent 模块')
    else:
        print('- cli_agent 模块已存在，跳过')

    # 5) seed role_permissions: 为历史上能使用 CLI 的角色开启等价权限 ------
    #
    # 兼容策略: 原先 _is_cli_enabled_for 硬编码允许
    # admin / hrdp_manager / hr_manager / ceo 四个角色进入 CLI,且跳过所有权限注入。
    # 升级后硬编码路径取消,必须通过 role_permissions 表达等价权限,否则会锁出用户。
    #
    # 为这四个角色 seed:
    #   - cli_agent.can_view = TRUE         (能打开 CLI 终端)
    #   - 每个业务模块 cli_can_query=TRUE, cli_permission_level='system'
    #     (对等于旧"跳过权限注入 = 全量查询"的行为)
    LEGACY_CLI_ROLES = ['admin', 'hrdp_manager', 'hr_manager', 'ceo']
    CLI_BUSINESS_MODULES = [
        'customer', 'project', 'quotation', 'expense', 'order',
        'pricing_order', 'product', 'worklog', 'user',
    ]

    for role in LEGACY_CLI_ROLES:
        # 5.1 cli_agent 总开关
        has = conn.execute(
            text("SELECT id FROM role_permissions WHERE role=:r AND module='cli_agent'"),
            {'r': role},
        ).fetchone()
        if has:
            conn.execute(
                text("""
                    UPDATE role_permissions SET
                        can_view = TRUE,
                        cli_can_query = FALSE,
                        cli_permission_level = NULL
                    WHERE id = :id
                """),
                {'id': has[0]},
            )
        else:
            conn.execute(
                text("""
                    INSERT INTO role_permissions
                        (role, module, can_view, can_create, can_edit, can_delete,
                         can_change_owner, permission_level, cli_can_query, cli_permission_level)
                    VALUES
                        (:role, 'cli_agent', TRUE, FALSE, FALSE, FALSE,
                         FALSE, 'system', FALSE, NULL)
                """),
                {'role': role},
            )

        # 5.2 每个业务模块的 CLI 查询权限
        for module in CLI_BUSINESS_MODULES:
            existing = conn.execute(
                text("SELECT id FROM role_permissions WHERE role=:r AND module=:m"),
                {'r': role, 'm': module},
            ).fetchone()
            if existing:
                # 已有记录: 只补 cli_can_query / cli_permission_level,不动现有 CRUD 配置
                conn.execute(
                    text("""
                        UPDATE role_permissions SET
                            cli_can_query = TRUE,
                            cli_permission_level = 'system'
                        WHERE id = :id
                    """),
                    {'id': existing[0]},
                )
            else:
                # 没有记录: 新增一条,界面权限给最小配置(can_view=FALSE),仅用于承载 CLI 字段
                conn.execute(
                    text("""
                        INSERT INTO role_permissions
                            (role, module, can_view, can_create, can_edit, can_delete,
                             can_change_owner, permission_level, cli_can_query, cli_permission_level)
                        VALUES
                            (:role, :module, FALSE, FALSE, FALSE, FALSE,
                             FALSE, 'personal', TRUE, 'system')
                    """),
                    {'role': role, 'module': module},
                )

        print(f'✓ 角色 {role}: cli_agent + {len(CLI_BUSINESS_MODULES)} 个业务模块 CLI 权限已 seed')


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 清理本次 migration 新增的 role_permissions 记录
    # 只删 cli_agent;其他业务模块的 cli_can_query/cli_permission_level 字段会随列删除一起消失
    conn.execute(text("DELETE FROM role_permissions WHERE module='cli_agent'"))
    conn.execute(text("DELETE FROM permission_modules WHERE module_id='cli_agent'"))

    if 'cli_table_modules' in inspector.get_table_names():
        op.drop_index('idx_cli_table_modules_module', table_name='cli_table_modules')
        op.drop_table('cli_table_modules')

    existing_cols = {c['name'] for c in inspector.get_columns('role_permissions')}
    if 'cli_permission_level' in existing_cols:
        op.drop_column('role_permissions', 'cli_permission_level')
    if 'cli_can_query' in existing_cols:
        op.drop_column('role_permissions', 'cli_can_query')
