"""销售经理考核组合 seed:销售目标/植入额/报价单数/新增客户/新增项目/客户活跃度

角色默认行(2026,目标值留空待配置页填写;已有值的不覆盖)。
连同既有 project_activity_rate(90%),销售经理考核共 7 项。

Revision ID: sales_mgr_kpi_seed_20260612
Revises: project_activity_kpi_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'sales_mgr_kpi_seed_20260612'
down_revision = 'project_activity_kpi_20260612'
branch_labels = None
depends_on = None

ITEMS = ['sales_target', 'implant_amount',
         'new_customers', 'new_projects', 'customer_activity_rate']


def upgrade():
    for code in ITEMS:
        op.execute(f"""
            INSERT INTO role_performance_targets (role_code, year, item_code, created_at, updated_at)
            SELECT 'sales_manager', 2026, '{code}', NOW(), NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM role_performance_targets
                WHERE role_code='sales_manager' AND year=2026 AND item_code='{code}')
        """)


def downgrade():
    op.execute("DELETE FROM role_performance_targets WHERE role_code='sales_manager' AND year=2026 "
               "AND item_code IN ('sales_target','implant_amount',"
               "'new_customers','new_projects','customer_activity_rate') AND annual_target IS NULL")
