"""配置管理新增「薪资审批」独立功能开关 cm_salary_run(2026-06-14)

之前薪资审批 tab 复用了「薪资配置 cm_salary」开关,矩阵里没有独立项。新增独立 feature,
镜像 cm_salary 当前已启用的角色(hr_manager/finace_director/ceo)以保持访问不变。

幂等:已存在则跳过;含序列复位避免 pkey 冲突。

Revision ID: cm_salary_run_feature_20260614
Revises: dept_hrbp_20260614
Create Date: 2026-06-14
"""
from alembic import op
from sqlalchemy import text

revision = 'cm_salary_run_feature_20260614'
down_revision = 'dept_hrbp_20260614'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # 序列复位(历史显式 id 种子可能导致 nextval 落后)
    for tbl in ('permission_module_features', 'role_feature_permissions'):
        conn.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{tbl}','id'), "
            f"GREATEST((SELECT COALESCE(MAX(id),1) FROM {tbl}), 1))"))

    # 1) feature 定义
    exists = conn.execute(text(
        "SELECT 1 FROM permission_module_features "
        "WHERE module_id='config_management' AND feature_id='cm_salary_run'")).first()
    if not exists:
        conn.execute(text(
            "INSERT INTO permission_module_features (module_id, feature_id, name, name_en, icon, sort_order, is_active) "
            "VALUES ('config_management','cm_salary_run','薪资审批','Salary Approval','fact_check',6,true)"))
    else:
        conn.execute(text(
            "UPDATE permission_module_features SET is_active=true "
            "WHERE module_id='config_management' AND feature_id='cm_salary_run' AND is_active IS DISTINCT FROM true"))

    # 2) 镜像 cm_salary 已启用角色 → cm_salary_run
    roles = [r[0] for r in conn.execute(text(
        "SELECT role FROM role_feature_permissions "
        "WHERE module_id='config_management' AND feature_id='cm_salary' AND is_enabled=true")).fetchall()]
    for role in roles:
        has = conn.execute(text(
            "SELECT 1 FROM role_feature_permissions "
            "WHERE role=:r AND module_id='config_management' AND feature_id='cm_salary_run'"),
            {'r': role}).first()
        if not has:
            conn.execute(text(
                "INSERT INTO role_feature_permissions (role, module_id, feature_id, is_enabled, created_at, updated_at) "
                "VALUES (:r,'config_management','cm_salary_run',true, extract(epoch from now()), extract(epoch from now()))"),
                {'r': role})


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DELETE FROM role_feature_permissions WHERE module_id='config_management' AND feature_id='cm_salary_run'"))
    conn.execute(text("DELETE FROM permission_module_features WHERE module_id='config_management' AND feature_id='cm_salary_run'"))
