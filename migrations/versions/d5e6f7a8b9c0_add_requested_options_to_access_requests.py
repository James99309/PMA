"""add requested_options to access_requests

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('access_requests', sa.Column('requested_options', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('access_requests', 'requested_options')
