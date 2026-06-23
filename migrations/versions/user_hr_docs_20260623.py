"""个人档案(用工资料)HR 专属(2026-06-23)

- users 加 hr_documents JSON 列(存档案元数据列表:含 doc_type/url/上传人等)
- person_config 模块新增功能开关 pc_hr_docs「个人档案」(白名单,默认仅 HR)
- 授予 ceo / hr_manager(admin 隐式全开),与 pc_salary 一致的 HR 专属策略

幂等:列用 IF NOT EXISTS;种子 ON CONFLICT DO NOTHING。

Revision ID: user_hr_docs_20260623
Revises: qualified_at_20260621
Create Date: 2026-06-23
"""
from alembic import op

revision = 'user_hr_docs_20260623'
down_revision = 'qualified_at_20260621'
branch_labels = None
depends_on = None

_HR_FEATURE = ('pc_hr_docs', '个人档案', 'folder_shared', 7)
_HR_ROLES = ('ceo', 'hr_manager')   # admin 隐式全开


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    import time
    now = time.time()

    # 1) users.hr_documents JSON 列(幂等)
    conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS hr_documents JSON"))

    # 2) 自增序列防失步(历史显式灌数后 INSERT 撞 pkey)
    for tbl in ('permission_module_features', 'role_feature_permissions'):
        conn.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{tbl}','id'), "
            f"GREATEST((SELECT COALESCE(MAX(id),0) FROM {tbl}), 1))"))

    # 3) 功能开关 pc_hr_docs
    fid, name, icon, so = _HR_FEATURE
    conn.execute(text(
        "INSERT INTO permission_module_features "
        "(module_id, feature_id, name, icon, sort_order, is_active, created_at, updated_at) "
        "VALUES ('person_config',:f,:n,:i,:s,true,:t,:t) "
        "ON CONFLICT (module_id, feature_id) DO NOTHING"),
        {'f': fid, 'n': name, 'i': icon, 's': so, 't': now})

    # 4) 白名单授予:ceo / hr_manager(admin 隐式)
    for role in _HR_ROLES:
        conn.execute(text(
            "INSERT INTO role_feature_permissions "
            "(role, module_id, feature_id, is_enabled, created_at, updated_at) "
            "VALUES (:r,'person_config',:f,true,:t,:t) "
            "ON CONFLICT (role, module_id, feature_id) DO NOTHING"),
            {'r': role, 'f': fid, 't': now})
        # 确保有 person_config 模块 view(prior 迁移通常已建,兜底)
        conn.execute(text(
            "INSERT INTO role_permissions "
            "(role, module, can_view, can_create, can_edit, can_delete, permission_level) "
            "VALUES (:r,'person_config',true,false,true,false,'company') "
            "ON CONFLICT (role, module) DO NOTHING"),
            {'r': role})


def downgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    fid = _HR_FEATURE[0]
    conn.execute(text("DELETE FROM role_feature_permissions WHERE feature_id=:f"), {'f': fid})
    conn.execute(text("DELETE FROM permission_module_features WHERE feature_id=:f"), {'f': fid})
    conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS hr_documents"))
