"""任务审计三档评价(2026-06-14)

审计任务的审核结果由"通过/驳回"升级为三档评价:
  低于预期(below=0.5) / 符合预期(meet=1.0) / 超出预期(exceed=1.5)
低于预期需填原因。审计类 KPI 由"计数"改为"按评价加权求和"(SUM review_score)。

新增列:
  task_reviewers.rating  —— 单个审计人的评价(below/meet/exceed)
  tasks.review_score     —— 审核通过时各审计人权重均值(无评价默认 1.0,兼容旧数据)

Revision ID: task_audit_rating_20260614
Revises: pm_metric_task_driven_20260614
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa

revision = 'task_audit_rating_20260614'
down_revision = 'pm_metric_task_driven_20260614'
branch_labels = None
depends_on = None


def _has_col(bind, table, col):
    return col in [c['name'] for c in sa.inspect(bind).get_columns(table)]


def upgrade():
    bind = op.get_bind()
    if not _has_col(bind, 'task_reviewers', 'rating'):
        op.add_column('task_reviewers',
                      sa.Column('rating', sa.String(10), nullable=True,
                                comment='below/meet/exceed 低于/符合/超出预期'))
    if not _has_col(bind, 'tasks', 'review_score'):
        op.add_column('tasks',
                      sa.Column('review_score', sa.Float, nullable=True,
                                comment='审核通过时各审计人评价权重均值(below0.5/meet1/exceed1.5)'))


def downgrade():
    bind = op.get_bind()
    if _has_col(bind, 'tasks', 'review_score'):
        op.drop_column('tasks', 'review_score')
    if _has_col(bind, 'task_reviewers', 'rating'):
        op.drop_column('task_reviewers', 'rating')
