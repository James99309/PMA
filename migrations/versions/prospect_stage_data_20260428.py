"""add stage_data column to prospect_projects

Revision ID: prospect_stage_data_20260428
Revises: quotation_extra_fields_20260428
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'prospect_stage_data_20260428'
down_revision = 'quotation_extra_fields_20260428'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('prospect_projects',
        sa.Column('stage_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )


def downgrade():
    op.drop_column('prospect_projects', 'stage_data')
