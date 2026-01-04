"""add mention fields to worklog

Revision ID: add_mention_20260103
Revises:
Create Date: 2026-01-03

为 worklogs 表添加 @ 用户和 # 项目引用功能所需字段
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_mention_20260103'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加 mentioned_users 和 mentioned_projects JSON 字段"""
    # 添加 mentioned_users 字段 - 存储被 @ 的用户ID列表
    op.add_column('worklogs', sa.Column('mentioned_users', sa.JSON(), nullable=True, default=list))

    # 添加 mentioned_projects 字段 - 存储被 # 引用的项目ID列表
    op.add_column('worklogs', sa.Column('mentioned_projects', sa.JSON(), nullable=True, default=list))


def downgrade():
    """移除 mention 字段"""
    op.drop_column('worklogs', 'mentioned_projects')
    op.drop_column('worklogs', 'mentioned_users')
