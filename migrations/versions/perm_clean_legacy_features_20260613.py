"""清理旧功能页签(2026-06-13)

账户管理三模块:用户管理(账户列表,无 tab)/个人配置(pc_*)/配置管理(cm_*)。
删除旧账户详情页遗留的功能页签:
- user_management 全部旧 tab(tab_base/tab_perm/tab_aff/tab_perf/tab_salary)—— 列表无 tab
- config_management 旧 tab(tab_basic/tab_perm/tab_aff*/tab_perf/tab_budget/tab_salary_*)—— 仅留 cm_*

幂等:DELETE 不存在即无操作。

Revision ID: perm_clean_legacy_features_20260613
Revises: perm_person_config_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'perm_clean_legacy_features_20260613'
down_revision = 'perm_person_config_20260613'
branch_labels = None
depends_on = None

_LEGACY = {
    'user_management': ['tab_base', 'tab_perm', 'tab_aff', 'tab_perf', 'tab_salary'],
    'config_management': ['tab_basic', 'tab_perm', 'tab_affiliation', 'tab_perf',
                          'tab_budget', 'tab_salary_assign', 'tab_salary_config'],
}


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    for mod, feats in _LEGACY.items():
        conn.execute(text(
            "DELETE FROM role_feature_permissions WHERE module_id=:m AND feature_id = ANY(:f)"),
            {'m': mod, 'f': feats})
        conn.execute(text(
            "DELETE FROM permission_module_features WHERE module_id=:m AND feature_id = ANY(:f)"),
            {'m': mod, 'f': feats})


def downgrade():
    pass  # 旧页签不恢复(已废弃)
