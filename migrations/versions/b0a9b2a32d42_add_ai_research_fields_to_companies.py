"""add ai research fields to companies

Revision ID: b0a9b2a32d42
Revises: d5e6f7a8b9c0
Create Date: 2026-02-21 11:31:18.361220

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b0a9b2a32d42'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('companies', sa.Column('ai_research_data', sa.JSON(), nullable=True))
    op.add_column('companies', sa.Column('ai_research_updated_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('companies', 'ai_research_updated_at')
    op.drop_column('companies', 'ai_research_data')
