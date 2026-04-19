# -*- coding: utf-8 -*-
"""任务/里程碑会审表 + 旧单审计数据迁移

Revision ID: task_multi_review_20260419
Revises: task_review_20260419
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'task_multi_review_20260419'
down_revision = ('task_review_20260419', 'points_business_hooks_20260418')
branch_labels = None
depends_on = None


def upgrade():
    # 创建 task_reviewers 表
    op.create_table(
        'task_reviewers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False, comment='pending/approved/rejected'),
        sa.Column('comment', sa.Text(), nullable=True, comment='审计意见'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_task_reviewers_task_reviewer', 'task_reviewers', ['task_id', 'reviewer_id'], unique=True)

    # 创建 milestone_reviewers 表
    op.create_table(
        'milestone_reviewers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('subtask_id', sa.Integer(), sa.ForeignKey('subtasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False, comment='pending/confirmed/rejected'),
        sa.Column('comment', sa.Text(), nullable=True, comment='确认意见'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_milestone_reviewers_subtask_reviewer', 'milestone_reviewers', ['subtask_id', 'reviewer_id'], unique=True)

    # 迁移旧数据: tasks.reviewer_id -> task_reviewers
    op.execute("""
        INSERT INTO task_reviewers (task_id, reviewer_id, status, comment, reviewed_at, created_at)
        SELECT id, reviewer_id,
               COALESCE(review_status, 'pending'),
               review_comment,
               reviewed_at,
               created_at
        FROM tasks
        WHERE reviewer_id IS NOT NULL
    """)

    # 迁移旧数据: subtasks.milestone_confirmer_id -> milestone_reviewers
    op.execute("""
        INSERT INTO milestone_reviewers (subtask_id, reviewer_id, status, comment, reviewed_at, created_at)
        SELECT id, milestone_confirmer_id,
               CASE
                   WHEN milestone_status = 'confirmed' THEN 'confirmed'
                   WHEN milestone_status = 'rejected' THEN 'rejected'
                   ELSE 'pending'
               END,
               milestone_comment,
               milestone_confirmed_at,
               created_at
        FROM subtasks
        WHERE milestone_confirmer_id IS NOT NULL
    """)


def downgrade():
    op.drop_index('ix_milestone_reviewers_subtask_reviewer', table_name='milestone_reviewers')
    op.drop_table('milestone_reviewers')
    op.drop_index('ix_task_reviewers_task_reviewer', table_name='task_reviewers')
    op.drop_table('task_reviewers')
