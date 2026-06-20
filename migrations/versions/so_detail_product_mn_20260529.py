"""sales_order_details add product_mn + backfill

Revision ID: so_detail_product_mn_20260529
Revises: q_tax_rate_20260526
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa


revision = 'so_detail_product_mn_20260529'
down_revision = ('q_tax_rate_20260526', 'folder_shares_20260520')
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('sales_order_details') as batch_op:
        batch_op.add_column(sa.Column('product_mn', sa.String(length=100), nullable=True))

    op.execute("""
        UPDATE sales_order_details AS sod
        SET    product_mn = p.product_mn
        FROM   products AS p
        WHERE  sod.product_id = p.id
          AND  sod.product_mn IS NULL
          AND  p.product_mn IS NOT NULL
          AND  p.product_mn <> ''
    """)


def downgrade():
    with op.batch_alter_table('sales_order_details') as batch_op:
        batch_op.drop_column('product_mn')
