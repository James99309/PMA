"""Add subtask_id to task_attachments and task_replies

Revision ID: task_subtask_assoc_20260419
Revises: task_multi_reviewers_20260419
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'task_subtask_assoc_20260419'
down_revision = 'task_multi_reviewers_20260419'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('task_attachments',
        sa.Column('subtask_id', sa.Integer(), sa.ForeignKey('subtasks.id', ondelete='SET NULL'), nullable=True,
                  comment='关联子任务'))
    op.add_column('task_replies',
        sa.Column('subtask_id', sa.Integer(), sa.ForeignKey('subtasks.id', ondelete='SET NULL'), nullable=True,
                  comment='关联子任务'))


def downgrade():
    op.drop_column('task_replies', 'subtask_id')
    op.drop_column('task_attachments', 'subtask_id')
