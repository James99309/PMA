"""产品经理指标改任务驱动(2026-06-14)

研发计划达成(pm_dev_rate)、批次质量(pm_quality_rate)由"率%"改为"任务计数"
(完成且审核通过的 研发任务/质量任务 数,达成率=完成÷目标);上市支持(pm_support_count)
由人工录入改为完成的上市支持任务数。本迁移只动指标定义(口径在代码层):
  1) pm_quality_rate 改名「批次质量」→「质量处理」
  2) pm_dev_rate / pm_quality_rate 的 data_type 由 percentage 改 count,单位 % → 次
幂等,可重复执行。

Revision ID: pm_metric_task_driven_20260614
Revises: se_metric_redefine_20260614
Create Date: 2026-06-14
"""
from alembic import op
from sqlalchemy import text

revision = 'pm_metric_task_driven_20260614'
down_revision = 'se_metric_redefine_20260614'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    bind.execute(text(
        "UPDATE performance_metrics_definition SET metric_name='质量处理', updated_at=NOW() "
        "WHERE metric_code='pm_quality_rate'"))
    bind.execute(text(
        "UPDATE performance_metrics_definition "
        "SET data_type='count', default_unit='次', updated_at=NOW() "
        "WHERE metric_code IN ('pm_dev_rate','pm_quality_rate')"))


def downgrade():
    bind = op.get_bind()
    bind.execute(text(
        "UPDATE performance_metrics_definition SET metric_name='批次质量' "
        "WHERE metric_code='pm_quality_rate'"))
    bind.execute(text(
        "UPDATE performance_metrics_definition "
        "SET data_type='percentage', default_unit='%' "
        "WHERE metric_code IN ('pm_dev_rate','pm_quality_rate')"))
