"""add messages table

Revision ID: add_messages_20260104
Revises:
Create Date: 2026-01-04

创建站内消息表，用于存储日志@消息等站内通知
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_messages_20260104'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建 messages 表"""
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('related_object_type', sa.String(length=50), nullable=True),
        sa.Column('related_object_id', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, default=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_messages_message_type', 'messages', ['message_type'], unique=False)
    op.create_index('ix_messages_recipient_id', 'messages', ['recipient_id'], unique=False)
    op.create_index('ix_messages_is_read', 'messages', ['is_read'], unique=False)
    op.create_index('ix_messages_created_at', 'messages', ['created_at'], unique=False)
    op.create_index('ix_messages_recipient_unread', 'messages', ['recipient_id', 'is_read'], unique=False)


def downgrade():
    """删除 messages 表"""
    op.drop_index('ix_messages_recipient_unread', table_name='messages')
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_is_read', table_name='messages')
    op.drop_index('ix_messages_recipient_id', table_name='messages')
    op.drop_index('ix_messages_message_type', table_name='messages')
    op.drop_table('messages')
