"""add project ai research fields

Revision ID: f2a3b4c5d6e7
Revises: e6f7a8b9c0d1
Create Date: 2026-02-21 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = 'f2a3b4c5d6e7'
down_revision = 'e6f7a8b9c0d1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('ai_research_data', JSON, nullable=True))
    op.add_column('projects', sa.Column('ai_research_updated_at', sa.DateTime(), nullable=True))
    op.add_column('projects', sa.Column('ai_research_status', sa.String(20), server_default='none'))
    op.add_column('projects', sa.Column('ai_research_error', sa.String(500), nullable=True))


def downgrade():
    op.drop_column('projects', 'ai_research_error')
    op.drop_column('projects', 'ai_research_status')
    op.drop_column('projects', 'ai_research_updated_at')
    op.drop_column('projects', 'ai_research_data')
