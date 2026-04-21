
"""add sync_metadata to chat_conversations

Revision ID: ef4820999291
Revises: 24791f1cc747
Create Date: 2026-04-21 16:29:10.364019

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef4820999291'
down_revision = '24791f1cc747'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chat_conversations', sa.Column('sync_metadata', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('chat_conversations', 'sync_metadata')
