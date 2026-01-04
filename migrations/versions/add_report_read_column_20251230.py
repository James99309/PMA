# -*- coding: utf-8 -*-
"""添加 report_read 列到 user_daily_login_records 表

Revision ID: add_report_read_col
Revises:
Create Date: 2025-12-30
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_report_read_col'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加 report_read 列
    op.add_column('user_daily_login_records',
        sa.Column('report_read', sa.Boolean(), nullable=True, server_default='false')
    )


def downgrade():
    op.drop_column('user_daily_login_records', 'report_read')
