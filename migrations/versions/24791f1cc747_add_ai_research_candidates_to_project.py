"""add_ai_research_candidates_to_project

Revision ID: 24791f1cc747
Revises: cli_session_model_20260421
Create Date: 2026-04-21 07:40:23.446992

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '24791f1cc747'
down_revision = 'cli_session_model_20260421'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('ai_research_candidates', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    op.drop_column('projects', 'ai_research_candidates')
