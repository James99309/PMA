"""widen prospect_stakeholders phone and contact_person to varchar(200)

Revision ID: widen_stakeholder_fields_20260429
Revises: 449e95e56356
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa

revision = 'widen_stakeholder_fields_20260429'
down_revision = '449e95e56356'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('prospect_stakeholders', 'phone',
        existing_type=sa.String(50), type_=sa.String(200), existing_nullable=True)
    op.alter_column('prospect_stakeholders', 'contact_person',
        existing_type=sa.String(50), type_=sa.String(200), existing_nullable=True)


def downgrade():
    op.alter_column('prospect_stakeholders', 'phone',
        existing_type=sa.String(200), type_=sa.String(50), existing_nullable=True)
    op.alter_column('prospect_stakeholders', 'contact_person',
        existing_type=sa.String(200), type_=sa.String(50), existing_nullable=True)
