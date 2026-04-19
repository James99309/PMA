# -*- coding: utf-8 -*-
"""任务审计字段 + 里程碑条件字段

Revision ID: task_review_20260419
Revises: subtask_tables_20260418
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'task_review_20260419'
down_revision = 'subtask_tables_20260418'
branch_labels = None
depends_on = None


def upgrade():
    # tasks 表: 审计字段
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True, comment='审计对象'))
        batch_op.add_column(sa.Column('review_status', sa.String(20), nullable=True, comment='pending_review/approved/rejected'))
        batch_op.add_column(sa.Column('review_comment', sa.Text(), nullable=True, comment='审计意见'))
        batch_op.add_column(sa.Column('reviewed_at', sa.DateTime(), nullable=True))

    # subtasks 表: 里程碑条件
    with op.batch_alter_table('subtasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('milestone_criteria', sa.Text(), nullable=True, comment='里程碑达标条件'))


def downgrade():
    with op.batch_alter_table('subtasks', schema=None) as batch_op:
        batch_op.drop_column('milestone_criteria')

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_column('reviewed_at')
        batch_op.drop_column('review_comment')
        batch_op.drop_column('review_status')
        batch_op.drop_column('reviewer_id')
