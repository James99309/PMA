"""add Quotation.tax_rate field

Revision ID: q_tax_rate_20260526
Revises: a7d5b1c3e2f4
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa


revision = 'q_tax_rate_20260526'
down_revision = 'a7d5b1c3e2f4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'quotations',
        sa.Column('tax_rate', sa.Float(), nullable=False, server_default='0'),
    )


def downgrade():
    op.drop_column('quotations', 'tax_rate')
