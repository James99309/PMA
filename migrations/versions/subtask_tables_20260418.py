"""add subtask tables and extend task model

Revision ID: subtask_tables_20260418
Revises: dingtalk_integration_20260414
Create Date: 2026-04-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'subtask_tables_20260418'
down_revision = 'dingtalk_integration_20260414'
branch_labels = None
depends_on = None


def _table_exists(name):
    bind = op.get_bind()
    insp = inspect(bind)
    return name in insp.get_table_names()


def _column_exists(table, column):
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [c['name'] for c in insp.get_columns(table)]
    return column in columns


def upgrade():
    # 1. 扩展 tasks 表（幂等）
    if not _column_exists('tasks', 'start_date'):
        op.add_column('tasks', sa.Column('start_date', sa.Date(), nullable=True, comment='任务开始日期'))
    if not _column_exists('tasks', 'shared_with_users'):
        op.add_column('tasks', sa.Column('shared_with_users', sa.JSON(), nullable=True, comment='协助人员ID列表'))
    if not _column_exists('tasks', 'task_type'):
        op.add_column('tasks', sa.Column('task_type', sa.String(30), nullable=True, server_default='general', comment='任务类型'))

    # 2. 创建 subtasks 表（幂等）
    if _table_exists('subtasks'):
        return  # db.create_all() 已创建所有表，跳过

    op.create_table('subtasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assignee_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('is_milestone', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('milestone_confirmer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('milestone_status', sa.String(20), nullable=True, comment='pending_confirmation/confirmed/rejected'),
        sa.Column('milestone_confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('milestone_comment', sa.Text(), nullable=True, comment='确认/驳回意见'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_index('ix_subtasks_task_id', 'subtasks', ['task_id'])
    op.create_index('ix_subtasks_task_status', 'subtasks', ['task_id', 'status'])

    # 3. 创建 subtask_updates 表
    op.create_table('subtask_updates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('subtask_id', sa.Integer(), sa.ForeignKey('subtasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_index('ix_subtask_updates_subtask_id', 'subtask_updates', ['subtask_id'])

    # 4. 创建 subtask_attachments 表
    op.create_table('subtask_attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('update_id', sa.Integer(), sa.ForeignKey('subtask_updates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), server_default='0'),
        sa.Column('file_type', sa.String(100), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_index('ix_subtask_attachments_update_id', 'subtask_attachments', ['update_id'])


def downgrade():
    op.drop_table('subtask_attachments')
    op.drop_table('subtask_updates')
    op.drop_table('subtasks')
    op.drop_column('tasks', 'task_type')
    op.drop_column('tasks', 'shared_with_users')
    op.drop_column('tasks', 'start_date')
