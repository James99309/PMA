
"""add attachments to work_items

Revision ID: e8e8a3490025
Revises: f9d0b51ea915
Create Date: 2026-04-03 11:46:27.300518

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e8e8a3490025'
down_revision = 'f9d0b51ea915'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('work_items', sa.Column('attachments', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('work_items', 'attachments')
