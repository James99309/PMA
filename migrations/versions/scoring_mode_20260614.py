"""绩效计分方式 scoring_mode 单一事实源(2026-06-14)

给指标定义加 scoring_mode 列(target/inverse/cumulative),收敛原本散落前后端的
反向/累计判断。按代码默认播种:失败率类=inverse,质量处理/新品上市/上市支持=cumulative,
其余留 NULL(运行时兜底为 target)。

Revision ID: scoring_mode_20260614
Revises: task_audit_rating_20260614
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'scoring_mode_20260614'
down_revision = 'task_audit_rating_20260614'
branch_labels = None
depends_on = None


def _has_col(bind, table, col):
    return col in [c['name'] for c in sa.inspect(bind).get_columns(table)]


def upgrade():
    bind = op.get_bind()
    if not _has_col(bind, 'performance_metrics_definition', 'scoring_mode'):
        op.add_column('performance_metrics_definition',
                      sa.Column('scoring_mode', sa.String(20), nullable=True,
                                comment='target/inverse/cumulative;NULL 走代码兜底'))
    # 按默认播种(幂等)
    bind.execute(text(
        "UPDATE performance_metrics_definition SET scoring_mode='inverse', updated_at=NOW() "
        "WHERE metric_code IN ('fail_rate','team_fail_rate','channel_fail_rate')"))
    bind.execute(text(
        "UPDATE performance_metrics_definition SET scoring_mode='cumulative', updated_at=NOW() "
        "WHERE metric_code IN ('pm_quality_rate','pm_new_launch','pm_support_count')"))


def downgrade():
    bind = op.get_bind()
    if _has_col(bind, 'performance_metrics_definition', 'scoring_mode'):
        op.drop_column('performance_metrics_definition', 'scoring_mode')
