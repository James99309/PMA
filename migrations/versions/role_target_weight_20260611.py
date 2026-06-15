"""add weight column to role_performance_targets (角色级考核权重覆盖)

绩效配置页支持修改权重(总和≤100%):空=用岗位方案(role_kpi_schemes)默认权重。
幂等 IF NOT EXISTS。

Revision ID: role_target_weight_20260611
Revises: se_kpi_metrics_20260611
Create Date: 2026-06-11

"""
from alembic import op

revision = 'role_target_weight_20260611'
down_revision = 'se_kpi_metrics_20260611'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE role_performance_targets ADD COLUMN IF NOT EXISTS weight NUMERIC(5,2)")


def downgrade():
    op.execute("ALTER TABLE role_performance_targets DROP COLUMN IF EXISTS weight")
