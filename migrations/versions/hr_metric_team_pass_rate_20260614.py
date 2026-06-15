"""HR 绩效指标 #1:团队绩效合格率 team_pass_rate(2026-06-14)

HRBP 结果锚:负责部门中有考核成员当季绩效得分≥60 的占比(系统聚合)。默认目标 80%。
配套:role_kpi_schemes 加 hr_manager 方案(代码);_act_team_pass_rate 自动计算。

幂等:已存在则跳过。

Revision ID: hr_metric_team_pass_rate_20260614
Revises: cm_salary_run_feature_20260614
Create Date: 2026-06-14
"""
from alembic import op
from sqlalchemy import text

revision = 'hr_metric_team_pass_rate_20260614'
down_revision = 'cm_salary_run_feature_20260614'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text(
        "SELECT setval(pg_get_serial_sequence('performance_metrics_definition','id'), "
        "GREATEST((SELECT COALESCE(MAX(id),1) FROM performance_metrics_definition),1))"))
    exists = conn.execute(text(
        "SELECT 1 FROM performance_metrics_definition WHERE metric_code='team_pass_rate'")).first()
    if not exists:
        conn.execute(text(
            "INSERT INTO performance_metrics_definition "
            "(metric_code, metric_name, metric_category, data_type, default_unit, description, "
            " is_system_metric, is_active, entry_frequency) "
            "VALUES ('team_pass_rate','团队绩效合格率','人力资源','percentage','%',"
            "'负责部门中有考核成员当季绩效得分≥60(合格)的占比;默认目标 80%',"
            "true, true, 'quarterly')"))


def downgrade():
    op.get_bind().execute(text(
        "DELETE FROM performance_metrics_definition WHERE metric_code='team_pass_rate'"))
