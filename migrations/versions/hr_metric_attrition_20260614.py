"""HR 骨干流失率 hr_attrition_rate —— 评审后去掉(2026-06-14)

骨干流失率无离职/骨干数据源、口径难统一、需手工,价值低成本高,决定不纳入 HR 绩效。
本迁移确保该指标定义不存在(幂等删除);权重已并入其它项(role_kpi_schemes)。

Revision ID: hr_metric_attrition_20260614
Revises: hr_metric_admin_20260614
Create Date: 2026-06-14
"""
from alembic import op
from sqlalchemy import text

revision = 'hr_metric_attrition_20260614'
down_revision = 'hr_metric_admin_20260614'
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(text(
        "DELETE FROM performance_metrics_definition WHERE metric_code='hr_attrition_rate'"))


def downgrade():
    pass
