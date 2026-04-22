
"""add notes fields to quotation and pricing order

Revision ID: 281843a6c6fb
Revises: ef4820999291
Create Date: 2026-04-22 21:30:50.059366

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '281843a6c6fb'
down_revision = 'ef4820999291'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('quotations', sa.Column('notes', sa.Text(), nullable=True, comment='报价单备注'))
    op.add_column('quotation_details', sa.Column('item_note', sa.Text(), nullable=True, comment='明细行备注'))
    op.add_column('pricing_orders', sa.Column('notes', sa.Text(), nullable=True, comment='批价单备注'))
    op.add_column('pricing_order_details', sa.Column('item_note', sa.Text(), nullable=True, comment='明细行备注'))


def downgrade():
    op.drop_column('pricing_order_details', 'item_note')
    op.drop_column('pricing_orders', 'notes')
    op.drop_column('quotation_details', 'item_note')
    op.drop_column('quotations', 'notes')
