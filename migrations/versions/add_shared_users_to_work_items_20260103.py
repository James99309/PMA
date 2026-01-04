# -*- coding: utf-8 -*-
"""add shared_with_users to work_items

Revision ID: add_shared_users_20260103
Revises:
Create Date: 2026-01-03

为工作项添加共享用户字段，支持将行程共享给其他用户查看
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_shared_users_20260103'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加 shared_with_users 字段到 work_items 表
    # 使用 JSON 类型存储用户ID列表 [3, 5, 8]
    op.add_column('work_items', sa.Column('shared_with_users', sa.JSON(), nullable=True, default=list))


def downgrade():
    # 删除字段
    op.drop_column('work_items', 'shared_with_users')
