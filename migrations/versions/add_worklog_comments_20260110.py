"""add worklog comments table

Revision ID: add_worklog_comments_20260110
Revises:
Create Date: 2026-01-10

创建工作日志评论表，用于存储日志评论
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_worklog_comments_20260110'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建 worklog_comments 表"""
    op.create_table('worklog_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worklog_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, default=False),
        sa.ForeignKeyConstraint(['worklog_id'], ['worklogs.id'], ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_worklog_comments_worklog_id', 'worklog_comments', ['worklog_id'], unique=False)
    op.create_index('ix_worklog_comments_created_at', 'worklog_comments', ['created_at'], unique=False)


def downgrade():
    """删除 worklog_comments 表"""
    op.drop_index('ix_worklog_comments_created_at', table_name='worklog_comments')
    op.drop_index('ix_worklog_comments_worklog_id', table_name='worklog_comments')
    op.drop_table('worklog_comments')
