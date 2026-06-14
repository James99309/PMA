"""HR 绩效指标 #2:招聘到岗 hr_recruit_count(2026-06-14)

到岗次数,数据源=任务(task_type='hr_recruit' 且审核通过 review_status='approved')。
正向;目标按季招聘计划逐季填(不写死默认);权重 20%。
配套:role_kpi_schemes 加入 hr_manager;_act_hr_recruit_count 计数。

幂等:已存在则跳过。

Revision ID: hr_metric_recruit_20260614
Revises: hr_metric_team_pass_rate_20260614
Create Date: 2026-06-14
"""
from alembic import op
from sqlalchemy import text

revision = 'hr_metric_recruit_20260614'
down_revision = 'hr_metric_team_pass_rate_20260614'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text(
        "SELECT setval(pg_get_serial_sequence('performance_metrics_definition','id'), "
        "GREATEST((SELECT COALESCE(MAX(id),1) FROM performance_metrics_definition),1))"))
    if not conn.execute(text(
            "SELECT 1 FROM performance_metrics_definition WHERE metric_code='hr_recruit_count'")).first():
        conn.execute(text(
            "INSERT INTO performance_metrics_definition "
            "(metric_code, metric_name, metric_category, data_type, default_unit, description, "
            " is_system_metric, is_active, entry_frequency) "
            "VALUES ('hr_recruit_count','招聘到岗','人力资源','count','次',"
            "'到岗次数(任务 hr_recruit 且审核通过);目标按季招聘计划逐季填',"
            "true, true, 'quarterly')"))


def downgrade():
    op.get_bind().execute(text(
        "DELETE FROM performance_metrics_definition WHERE metric_code='hr_recruit_count'"))
