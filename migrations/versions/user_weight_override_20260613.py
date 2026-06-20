"""个人绩效权重覆盖(2026-06-13)

user_performance_targets 增列 weight_override(%):个人绩效页可改权重比例,
空=继承角色/方案默认权重。

幂等:ADD COLUMN IF NOT EXISTS。

Revision ID: user_weight_override_20260613
Revises: perf_settlement_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'user_weight_override_20260613'
down_revision = 'perf_settlement_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE user_performance_targets ADD COLUMN IF NOT EXISTS weight_override NUMERIC(5,2);
    """)


def downgrade():
    op.execute("""
        ALTER TABLE user_performance_targets DROP COLUMN IF EXISTS weight_override;
    """)
