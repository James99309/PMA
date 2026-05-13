"""add highlights to meeting_minutes

Revision ID: a8c1d2e3f4b5
Revises: ef51c26fdf35
Create Date: 2026-05-12 14:30:00

只加 meeting_minutes.highlights 列。
"""
from alembic import op
import sqlalchemy as sa


revision = 'a8c1d2e3f4b5'
down_revision = 'ef51c26fdf35'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('meeting_minutes', sa.Column('highlights', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('meeting_minutes', 'highlights')
