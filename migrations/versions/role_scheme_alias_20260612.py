"""服务经理=营销总监方案 / 客户销售=销售方案 的率类角色默认 + 销售经理改名区域销售

Revision ID: role_scheme_alias_20260612
Revises: fail_attribution_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'role_scheme_alias_20260612'
down_revision = 'fail_attribution_20260612'
branch_labels = None
depends_on = None


def upgrade():
    # 服务经理(团队方案)率类默认目标:团队客户活跃度 100 / 团队项目活跃度 80
    op.execute("""
        INSERT INTO role_performance_targets (role_code, year, item_code, annual_target, created_at, updated_at)
        SELECT r.role_code, 2026, r.item_code, r.annual_target, NOW(), NOW()
        FROM (VALUES
            ('service_manager', 'team_customer_activity_rate', 100.0),
            ('service_manager', 'team_project_activity_rate',  80.0),
            ('customer_sales',  'customer_activity_rate',      100.0)
        ) AS r(role_code, item_code, annual_target)
        WHERE NOT EXISTS (
            SELECT 1 FROM role_performance_targets t
            WHERE t.role_code = r.role_code AND t.year = 2026 AND t.item_code = r.item_code)
    """)
    # 销售经理 → 区域销售(显示名,全站经字典同步;code 不变)
    op.execute("UPDATE dictionaries SET value='区域销售' WHERE type='role' AND key='sales_manager' AND value='销售经理'")


def downgrade():
    op.execute("UPDATE dictionaries SET value='销售经理' WHERE type='role' AND key='sales_manager' AND value='区域销售'")
    op.execute("DELETE FROM role_performance_targets WHERE year=2026 AND ("
               "(role_code='service_manager' AND item_code IN ('team_customer_activity_rate','team_project_activity_rate'))"
               " OR (role_code='customer_sales' AND item_code='customer_activity_rate'))")
