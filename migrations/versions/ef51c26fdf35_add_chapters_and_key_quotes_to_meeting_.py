"""add chapters and key_quotes to meeting_minutes

Revision ID: ef51c26fdf35
Revises: 27b5f37f1c30
Create Date: 2026-05-12 09:04:24.655223

只加 meeting_minutes.chapters / key_quotes 两列。
（autogenerate 检测到了其他表的差异，但那些是 PMA 现存的 model/db drift，
不在本次 V2 改动范围，已手动剔除）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'ef51c26fdf35'
down_revision = '27b5f37f1c30'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('meeting_minutes', sa.Column('chapters', sa.JSON(), nullable=True))
    op.add_column('meeting_minutes', sa.Column('key_quotes', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('meeting_minutes', 'key_quotes')
    op.drop_column('meeting_minutes', 'chapters')
