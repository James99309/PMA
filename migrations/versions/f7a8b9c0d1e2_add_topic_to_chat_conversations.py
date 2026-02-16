"""add topic to chat_conversations

Revision ID: f7a8b9c0d1e2
Revises: add_knowledge_config_20260215
Create Date: 2026-02-16 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f7a8b9c0d1e2'
down_revision = 'add_knowledge_config_20260215'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chat_conversations', sa.Column('topic', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('chat_conversations', 'topic')
