"""项目活跃度考核指标(销售个人版 + 营销总监团队版)+ 角色默认目标 seed

口径:负责(owner 或厂商销售)的项目中,排除 签约/失败/搁置,
跟进超 20 天的占比 → 活跃度% = (1 - 超期数/总数) × 100。
销售角色目标 ≥90%(超期 ≤10%);营销总监(部门成员+自己)≥80%(超期 ≤20%)。

Revision ID: project_activity_kpi_20260612
Revises: win_lock_quotation_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'project_activity_kpi_20260612'
down_revision = 'win_lock_quotation_20260612'
branch_labels = None
depends_on = None


def upgrade():
    # 指标定义(幂等)
    op.execute("""
        INSERT INTO performance_metrics_definition
            (metric_code, metric_name, metric_category, data_type, default_unit,
             description, is_system_metric, is_active, created_at)
        VALUES
            ('project_activity_rate', '项目活跃度', '项目管理', 'percentage', '%',
             '本人负责(负责人/厂商销售)的未签约·未失败·未搁置项目中,跟进未超 20 天的占比;目标 ≥90%(超期项目 ≤10%)',
             true, true, NOW()),
            ('team_project_activity_rate', '团队项目活跃度', '项目管理', 'percentage', '%',
             '本部门成员(含本人)负责的未签约·未失败·未搁置项目中,跟进未超 20 天的占比;目标 ≥80%(超期项目 ≤20%)',
             true, true, NOW())
        ON CONFLICT (metric_code) DO NOTHING
    """)
    # 角色默认目标(2026;幂等):销售家族 90% / 营销总监 80%(水平目标,不分摊)
    op.execute("""
        INSERT INTO role_performance_targets (role_code, year, item_code, annual_target, created_at, updated_at)
        SELECT r.role_code, 2026, r.item_code, r.annual_target, NOW(), NOW()
        FROM (VALUES
            ('sales_manager',  'project_activity_rate',      90.0),
            ('customer_sales', 'project_activity_rate',      90.0),
            ('sales_director', 'team_project_activity_rate', 80.0)
        ) AS r(role_code, item_code, annual_target)
        WHERE NOT EXISTS (
            SELECT 1 FROM role_performance_targets t
            WHERE t.role_code = r.role_code AND t.year = 2026 AND t.item_code = r.item_code)
    """)


def downgrade():
    op.execute("DELETE FROM role_performance_targets WHERE item_code IN "
               "('project_activity_rate','team_project_activity_rate')")
    op.execute("DELETE FROM performance_metrics_definition WHERE metric_code IN "
               "('project_activity_rate','team_project_activity_rate')")
