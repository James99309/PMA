"""add use_in_code to product_specs

Revision ID: dc05c44c29e9
Revises: f1b4189bb6da
Create Date: 2026-04-03 22:27:47.321158

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dc05c44c29e9'
down_revision = 'f1b4189bb6da'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('product_specs',
                  sa.Column('use_in_code', sa.Boolean(), nullable=True, default=False))


def downgrade():
    op.drop_column('product_specs', 'use_in_code')
