"""失败归因标签 + 失败率考核指标(个人/团队,反向指标)

归因在失败审核流程打标:步骤1 部门经理勾「个人因素为主」(fail_owner_fault),
步骤2 总经理勾「团队管理失责」(fail_mgmt_fault);驳回/召回时清标。
个人失败率 = 当年个人因素失败数 ÷ 本人负责项目总数;
团队失败率 = 当年管理失责失败数 ÷ 团队当年失败项目总数。目标语义:≤ 目标为达标。

Revision ID: fail_attribution_20260612
Revises: team_kpi_metrics_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'fail_attribution_20260612'
down_revision = 'team_kpi_metrics_20260612'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS fail_owner_fault BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS fail_mgmt_fault BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("""
        INSERT INTO performance_metrics_definition
            (metric_code, metric_name, metric_category, data_type, default_unit,
             description, is_system_metric, is_active, created_at)
        VALUES
            ('fail_rate', '个人失败率', '项目管理', 'percentage', '%',
             '当年被认定「个人因素为主」的失败项目数 ÷ 本人负责的项目总数;反向指标,实际 ≤ 目标为达标(归因由部门经理在失败审核中认定)',
             true, true, NOW()),
            ('team_fail_rate', '团队失败率', '团队管理', 'percentage', '%',
             '当年被认定「团队管理失责」的失败项目数 ÷ 本部门当年失败项目总数;反向指标,实际 ≤ 目标为达标(归因由总经理在失败审核中认定)',
             true, true, NOW())
        ON CONFLICT (metric_code) DO NOTHING
    """)


def downgrade():
    op.execute("DELETE FROM performance_metrics_definition WHERE metric_code IN ('fail_rate','team_fail_rate')")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS fail_mgmt_fault")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS fail_owner_fault")
