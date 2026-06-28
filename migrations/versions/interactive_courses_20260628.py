"""add interactive_courses table

互动课程登记表(取代硬编码 INTERACTIVE_COURSES)。
非破坏性:只新增 1 张表。

Revision ID: interactive_courses_20260628
Revises: pm_new_launch_listing_20260623
Create Date: 2026-06-28
"""
from alembic import op
import sqlalchemy as sa


revision = 'interactive_courses_20260628'
down_revision = 'pm_new_launch_listing_20260623'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'interactive_courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=80), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('subtitle', sa.String(length=200), nullable=True),
        sa.Column('desc', sa.Text(), nullable=True),
        sa.Column('accent', sa.String(length=20), nullable=True, server_default='#1A0E3D'),
        sa.Column('topic', sa.String(length=100), nullable=True, server_default='产品技术'),
        sa.Column('cover_page', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('has_thumbs', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('article_id', sa.Integer(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.create_index('ix_interactive_courses_key', 'interactive_courses', ['key'])


def downgrade():
    op.drop_index('ix_interactive_courses_key', table_name='interactive_courses')
    op.drop_table('interactive_courses')
