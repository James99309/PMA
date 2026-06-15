"""营销总监团队考核指标定义(团队=部门成员含本人)

team_sales_amount / team_implant_amount / team_new_projects /
team_new_customers / team_customer_activity_rate
(team_project_activity_rate 已存在)

Revision ID: team_kpi_metrics_20260612
Revises: sales_mgr_kpi_seed_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'team_kpi_metrics_20260612'
down_revision = 'sales_mgr_kpi_seed_20260612'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO performance_metrics_definition
            (metric_code, metric_name, metric_category, data_type, default_unit,
             description, is_system_metric, is_active, created_at)
        VALUES
            ('team_sales_amount', '团队销售目标', '团队管理', 'amount', '',
             '本部门成员(含本人)每月批价单审批通过金额合计', true, true, NOW()),
            ('team_implant_amount', '团队植入额', '团队管理', 'amount', '',
             '本部门成员(含本人)名下报价单植入额合计', true, true, NOW()),
            ('team_new_projects', '团队新增项目', '团队管理', 'count', '个',
             '本部门成员(含本人)每月新建项目数', true, true, NOW()),
            ('team_new_customers', '团队新增客户', '团队管理', 'count', '个',
             '本部门成员(含本人)每月新建客户数', true, true, NOW()),
            ('team_customer_activity_rate', '团队客户活跃度', '团队管理', 'percentage', '%',
             '本部门成员(含本人)名下客户中 高度活跃/活跃/正常 的占比(快照)', true, true, NOW())
        ON CONFLICT (metric_code) DO NOTHING
    """)
    # 角色默认目标:团队客户活跃度 100%(团队项目活跃度 80% 已在前序迁移)
    op.execute("""
        INSERT INTO role_performance_targets (role_code, year, item_code, annual_target, created_at, updated_at)
        SELECT 'sales_director', 2026, 'team_customer_activity_rate', 100.0, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM role_performance_targets
            WHERE role_code='sales_director' AND year=2026 AND item_code='team_customer_activity_rate')
    """)


def downgrade():
    op.execute("DELETE FROM performance_metrics_definition WHERE metric_code IN "
               "('team_sales_amount','team_implant_amount','team_new_projects',"
               "'team_new_customers','team_customer_activity_rate')")
