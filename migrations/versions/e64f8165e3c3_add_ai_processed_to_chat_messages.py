"""add ai_processed to chat_messages

Revision ID: e64f8165e3c3
Revises: wiki_tables_20260409
Create Date: 2026-04-12 10:27:55.215139

"""
from alembic import op
import sqlalchemy as sa

revision = 'e64f8165e3c3'
down_revision = 'wiki_tables_20260409'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chat_messages', sa.Column('ai_processed', sa.Boolean(), nullable=True, server_default='false'))


def downgrade():
    op.drop_column('chat_messages', 'ai_processed')
