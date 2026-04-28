
"""add geo monitor tables

Revision ID: 3db17b0942a6
Revises: quotation_excel_editor_20260428
Create Date: 2026-04-28 13:34:52.310109

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3db17b0942a6'
down_revision = 'quotation_excel_editor_20260428'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('geo_intent',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('frequency', sa.String(length=20), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('geo_query',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('intent_id', sa.Integer(), nullable=False),
        sa.Column('market', sa.String(length=10), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('excluded', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['intent_id'], ['geo_intent.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('geo_result',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=False),
        sa.Column('run_at', sa.DateTime(), nullable=True),
        sa.Column('mentioned', sa.String(length=20), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('ai_response', sa.Text(), nullable=True),
        sa.Column('cited_urls', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['query_id'], ['geo_query.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('geo_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )


def downgrade():
    op.drop_table('geo_settings')
    op.drop_table('geo_result')
    op.drop_table('geo_query')
    op.drop_table('geo_intent')
