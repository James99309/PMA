"""add notes to settlement_orders

Revision ID: settlement_order_notes_20260430
Revises: widen_stakeholder_fields_20260429
Create Date: 2026-04-30

"""
from alembic import op
import sqlalchemy as sa

revision = 'settlement_order_notes_20260430'
down_revision = 'widen_stakeholder_fields_20260429'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('settlement_orders', sa.Column('notes', sa.Text(), nullable=True, comment='结算单备注'))


def downgrade():
    op.drop_column('settlement_orders', 'notes')
