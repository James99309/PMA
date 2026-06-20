"""HR 绩效指标 #3:培训组织 hr_training_count(2026-06-14)

培训次数,数据源=任务(task_type='hr_training',状态 completed 即计,不需审核)。
正向;权重 15%;默认目标 8 次/年(可逐季覆盖)。
配套:role_kpi_schemes 加入 hr_manager;_act_hr_training_count 计数。

幂等:已存在则跳过。

Revision ID: hr_metric_training_20260614
Revises: hr_metric_recruit_20260614
Create Date: 2026-06-14
"""
from alembic import op
from sqlalchemy import text

revision = 'hr_metric_training_20260614'
down_revision = 'hr_metric_recruit_20260614'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text(
        "SELECT setval(pg_get_serial_sequence('performance_metrics_definition','id'), "
        "GREATEST((SELECT COALESCE(MAX(id),1) FROM performance_metrics_definition),1))"))
    if not conn.execute(text(
            "SELECT 1 FROM performance_metrics_definition WHERE metric_code='hr_training_count'")).first():
        conn.execute(text(
            "INSERT INTO performance_metrics_definition "
            "(metric_code, metric_name, metric_category, data_type, default_unit, description, "
            " is_system_metric, is_active, entry_frequency) "
            "VALUES ('hr_training_count','培训组织','人力资源','count','次',"
            "'组织培训次数(任务 hr_training,完成即计);默认 8 次/年,可逐季调',"
            "true, true, 'quarterly')"))


def downgrade():
    op.get_bind().execute(text(
        "DELETE FROM performance_metrics_definition WHERE metric_code='hr_training_count'"))
