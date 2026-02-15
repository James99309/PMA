
"""add attachment fields to chat_messages

Revision ID: 1bec60c80118
Revises: 0f4090a063b9
Create Date: 2026-02-14 12:57:18.267070

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1bec60c80118'
down_revision = '0f4090a063b9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chat_messages', sa.Column('message_type', sa.String(length=20), nullable=True))
    op.add_column('chat_messages', sa.Column('file_url', sa.String(length=500), nullable=True))
    op.add_column('chat_messages', sa.Column('file_name', sa.String(length=255), nullable=True))
    op.add_column('chat_messages', sa.Column('file_size', sa.Integer(), nullable=True))
    op.alter_column('chat_messages', 'content',
               existing_type=sa.TEXT(),
               nullable=True)


def downgrade():
    op.alter_column('chat_messages', 'content',
               existing_type=sa.TEXT(),
               nullable=False)
    op.drop_column('chat_messages', 'file_size')
    op.drop_column('chat_messages', 'file_name')
    op.drop_column('chat_messages', 'file_url')
    op.drop_column('chat_messages', 'message_type')
