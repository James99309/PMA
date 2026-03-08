
"""add is_deleted to product, dev_product, project

Revision ID: a1742ee99753
Revises: 4e121e39a998
Create Date: 2026-03-08 09:20:41.249356

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1742ee99753'
down_revision = '4e121e39a998'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('dev_products', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('projects', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade():
    op.drop_column('projects', 'is_deleted')
    op.drop_column('dev_products', 'is_deleted')
    op.drop_column('products', 'is_deleted')
