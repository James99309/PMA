"""add pdf_original_name to products

Revision ID: product_pdf_original_name_20260608
Revises: approval_submitter_designate_20260601
Create Date: 2026-06-08

"""
from alembic import op
import sqlalchemy as sa

revision = 'product_pdf_original_name_20260608'
down_revision = 'approval_submitter_designate_20260601'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('pdf_original_name', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('products', 'pdf_original_name')
