"""工作项关联任务/子任务字段

Revision ID: workitem_related_task_20260617
Revises: fail_attribution_note_20260616
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa


revision = 'workitem_related_task_20260617'
down_revision = 'fail_attribution_note_20260616'
branch_labels = None
depends_on = None


def _has_column(table, column):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return column in [c['name'] for c in insp.get_columns(table)]


def upgrade():
    if not _has_column('work_items', 'related_task_id'):
        op.add_column('work_items', sa.Column('related_task_id', sa.Integer(), nullable=True))
    if not _has_column('work_items', 'related_subtask_id'):
        op.add_column('work_items', sa.Column('related_subtask_id', sa.Integer(), nullable=True))


def downgrade():
    for col in ('related_subtask_id', 'related_task_id'):
        if _has_column('work_items', col):
            op.drop_column('work_items', col)
