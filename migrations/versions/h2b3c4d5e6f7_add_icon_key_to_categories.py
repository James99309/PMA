"""add icon_key to product_categories and product_subcategories

Revision ID: h2b3c4d5e6f7
Revises: g1a2b3c4d5e6
Create Date: 2026-02-21 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h2b3c4d5e6f7'
down_revision = 'g1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('product_categories', sa.Column('icon_key', sa.String(length=30), nullable=True, comment='系统图图标标识'))
    op.add_column('product_subcategories', sa.Column('icon_key', sa.String(length=30), nullable=True, comment='系统图图标标识'))


def downgrade():
    op.drop_column('product_subcategories', 'icon_key')
    op.drop_column('product_categories', 'icon_key')
