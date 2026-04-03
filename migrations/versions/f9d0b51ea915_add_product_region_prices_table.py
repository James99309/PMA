
"""add product_region_prices table

Revision ID: f9d0b51ea915
Revises: 240f1150d812
Create Date: 2026-04-02 14:54:10.088899

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f9d0b51ea915'
down_revision = '240f1150d812'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('product_region_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('market_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'currency', name='uq_product_region_price')
    )


def downgrade():
    op.drop_table('product_region_prices')
