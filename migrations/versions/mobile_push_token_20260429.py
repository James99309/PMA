"""add push_token and push_platform to users for mobile app

Revision ID: mobile_push_token_20260429
Revises: xlsx_skill_system_20260420
Create Date: 2026-04-29 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'mobile_push_token_20260429'
down_revision = 'xlsx_skill_system_20260420'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('push_token', sa.String(512), nullable=True))
    op.add_column('users', sa.Column('push_platform', sa.String(10), nullable=True))


def downgrade():
    op.drop_column('users', 'push_platform')
    op.drop_column('users', 'push_token')
