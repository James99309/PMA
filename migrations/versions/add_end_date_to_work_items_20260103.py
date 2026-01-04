# -*- coding: utf-8 -*-
"""add end_date to work_items

Revision ID: add_end_date_20260103
Revises:
Create Date: 2026-01-03

为工作项添加结束日期字段，支持跨天任务
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_end_date_20260103'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加 end_date 字段到 work_items 表
    op.add_column('work_items', sa.Column('end_date', sa.Date(), nullable=True))


def downgrade():
    # 删除 end_date 字段
    op.drop_column('work_items', 'end_date')
