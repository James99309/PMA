"""个人配置纳入权限系统(2026-06-13)- 三模块 + tab 功能开关

正确设计(用户确认):仅 3 个模块 —— user_management(账户列表)/ person_config(个人配置,新)
/ config_management(配置管理);各 tab 由模块内功能开关(permission_module_features +
role_feature_permissions)控制,数据范围用标准四级。
设计:docs/plans/2026-06-13-perm-modularize-design.md

白名单策略:tab 默认隐藏,种子把现有可访问角色勾上(admin 隐式全开)。
幂等:ON CONFLICT DO NOTHING。

Revision ID: perm_person_config_20260613
Revises: user_weight_override_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'perm_person_config_20260613'
down_revision = 'user_weight_override_20260613'
branch_labels = None
depends_on = None

# 个人配置 tab 功能开关
_PC_FEATURES = [
    ('pc_permission', '权限覆盖', 'shield_person', 1),
    ('pc_affiliation', '归属关系', 'lan', 2),
    ('pc_budget', '费用预算', 'account_balance_wallet', 3),
    ('pc_performance', '绩效目标', 'flag', 4),
    ('pc_salary', '薪资', 'payments', 5),
    ('pc_ai', 'AI 代理', 'smart_toy', 6),
]
# 配置管理 tab 功能开关(AT 版)
_CM_FEATURES = [
    ('cm_permission', '权限配置', 'admin_panel_settings', 1),
    ('cm_budget', '部门预算', 'savings', 2),
    ('cm_performance', '绩效配置', 'leaderboard', 3),
    ('cm_flow', '流程配置', 'account_tree', 4),
    ('cm_salary', '薪资配置', 'request_quote', 5),
]
_SALARY_FEATS = ('pc_salary', 'cm_salary')   # 薪资 tab 默认仅 admin/ceo/hr_manager


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    import time
    now = time.time()

    # 0) 修复历史显式灌数导致的自增序列失步(否则 INSERT 撞 pkey)
    for tbl in ('permission_modules', 'permission_module_features',
                'role_feature_permissions', 'role_permissions'):
        conn.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{tbl}','id'), "
            f"GREATEST((SELECT COALESCE(MAX(id),0) FROM {tbl}), 1))"))

    # 1) person_config 模块
    conn.execute(text(
        "INSERT INTO permission_modules (module_id, name, icon, group_name, sort_order, is_active, created_at, updated_at) "
        "VALUES ('person_config','个人配置','manage_accounts','账户管理',13,true,:t,:t) "
        "ON CONFLICT (module_id) DO NOTHING"), {'t': now})

    # 2) features
    for fid, name, icon, so in _PC_FEATURES:
        conn.execute(text(
            "INSERT INTO permission_module_features (module_id, feature_id, name, icon, sort_order, is_active, created_at, updated_at) "
            "VALUES ('person_config',:f,:n,:i,:s,true,:t,:t) ON CONFLICT (module_id, feature_id) DO NOTHING"),
            {'f': fid, 'n': name, 'i': icon, 's': so, 't': now})
    for fid, name, icon, so in _CM_FEATURES:
        conn.execute(text(
            "INSERT INTO permission_module_features (module_id, feature_id, name, icon, sort_order, is_active, created_at, updated_at) "
            "VALUES ('config_management',:f,:n,:i,:s,true,:t,:t) ON CONFLICT (module_id, feature_id) DO NOTHING"),
            {'f': fid, 'n': name, 'i': icon, 's': so, 't': now})

    # 3) role_permissions:person_config 沿用 config_management 的 view/edit/级别
    conn.execute(text(
        "INSERT INTO role_permissions (role, module, can_view, can_create, can_edit, can_delete, permission_level) "
        "SELECT rp.role, 'person_config', rp.can_view, false, rp.can_edit, false, COALESCE(rp.permission_level,'personal') "
        "FROM role_permissions rp WHERE rp.module='config_management' AND rp.can_view=true "
        "ON CONFLICT (role, module) DO NOTHING"))

    # 4) role_feature_permissions 种子(白名单):有 config_management view 的角色 → 勾非薪资 tab
    roles = [r[0] for r in conn.execute(text(
        "SELECT DISTINCT role FROM role_permissions WHERE module='config_management' AND can_view=true")).fetchall()]
    non_salary = [f[0] for f in (_PC_FEATURES + _CM_FEATURES) if f[0] not in _SALARY_FEATS]
    for role in roles:
        for fid in non_salary:
            mod = 'person_config' if fid.startswith('pc_') else 'config_management'
            conn.execute(text(
                "INSERT INTO role_feature_permissions (role, module_id, feature_id, is_enabled, created_at, updated_at) "
                "VALUES (:r,:m,:f,true,:t,:t) ON CONFLICT (role, module_id, feature_id) DO NOTHING"),
                {'r': role, 'm': mod, 'f': fid, 't': now})
    # 薪资 tab:ceo / hr_manager
    for role in ('ceo', 'hr_manager'):
        for fid in _SALARY_FEATS:
            mod = 'person_config' if fid.startswith('pc_') else 'config_management'
            conn.execute(text(
                "INSERT INTO role_feature_permissions (role, module_id, feature_id, is_enabled, created_at, updated_at) "
                "VALUES (:r,:m,:f,true,:t,:t) ON CONFLICT (role, module_id, feature_id) DO NOTHING"),
                {'r': role, 'm': mod, 'f': fid, 't': now})
        # 确保 ceo/hr 有 person_config 模块 view
        conn.execute(text(
            "INSERT INTO role_permissions (role, module, can_view, can_create, can_edit, can_delete, permission_level) "
            "VALUES (:r,'person_config',true,false,true,false,'company') ON CONFLICT (role, module) DO NOTHING"),
            {'r': role})


def downgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    pc = [f[0] for f in _PC_FEATURES]
    cm = [f[0] for f in _CM_FEATURES]
    conn.execute(text("DELETE FROM role_feature_permissions WHERE feature_id = ANY(:f)"), {'f': pc + cm})
    conn.execute(text("DELETE FROM permission_module_features WHERE feature_id = ANY(:f)"), {'f': pc + cm})
    conn.execute(text("DELETE FROM role_permissions WHERE module='person_config'"))
    conn.execute(text("DELETE FROM permission_modules WHERE module_id='person_config'"))
