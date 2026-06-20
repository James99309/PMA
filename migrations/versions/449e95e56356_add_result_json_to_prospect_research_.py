
"""add result_json to prospect_research_logs

Revision ID: 449e95e56356
Revises: prospect_stage_data_20260428
Create Date: 2026-04-29 20:29:35.620043

"""
from alembic import op
import sqlalchemy as sa

revision = '449e95e56356'
down_revision = 'prospect_stage_data_20260428'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('prospect_research_logs',
        sa.Column('result_json', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('prospect_research_logs', 'result_json')
