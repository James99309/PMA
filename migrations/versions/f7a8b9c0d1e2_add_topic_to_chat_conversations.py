"""add topic to chat_conversations

Revision ID: f7a8b9c0d1e2
Revises: e5e82350daec
Create Date: 2026-02-16 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f7a8b9c0d1e2'
down_revision = 'e5e82350daec'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chat_conversations', sa.Column('topic', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('chat_conversations', 'topic')
