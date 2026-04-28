"""add quotations.extra_fields JSON for non-structured fields

Revision ID: quotation_extra_fields_20260428
Revises: company_entities_20260428
Create Date: 2026-04-28 15:30:00.000000

新增 quotations.extra_fields JSON 字段，存放编辑器中"非结构化"字段：
- payment_terms / shipping_terms / validity / ref_no
- 以后再加新字段不需要再改 schema
"""
from alembic import op


revision = 'quotation_extra_fields_20260428'
down_revision = 'company_entities_20260428'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE quotations ADD COLUMN IF NOT EXISTS extra_fields JSONB
    """)


def downgrade():
    op.execute("ALTER TABLE quotations DROP COLUMN IF EXISTS extra_fields")
