"""add ai research status fields to companies

Revision ID: e6f7a8b9c0d1
Revises: b0a9b2a32d42
Create Date: 2026-02-21 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e6f7a8b9c0d1'
down_revision = 'b0a9b2a32d42'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('companies', sa.Column('ai_research_status', sa.String(20), server_default='none'))
    op.add_column('companies', sa.Column('ai_research_error', sa.String(500), nullable=True))
    op.add_column('companies', sa.Column('ai_research_candidates', sa.JSON(), nullable=True))

    # 回填：已有调研数据的记录标记为 completed
    op.execute("""
        UPDATE companies
        SET ai_research_status = 'completed'
        WHERE ai_research_data IS NOT NULL
          AND ai_research_status = 'none'
    """)


def downgrade():
    op.drop_column('companies', 'ai_research_candidates')
    op.drop_column('companies', 'ai_research_error')
    op.drop_column('companies', 'ai_research_status')
