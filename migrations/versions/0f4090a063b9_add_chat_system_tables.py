
"""add chat system tables

Revision ID: 0f4090a063b9
Revises: d2269307de93
Create Date: 2026-02-14 09:34:46.488355

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0f4090a063b9'
down_revision = 'd2269307de93'
branch_labels = None
depends_on = None


def upgrade():
    # 创建聊天对话表
    op.create_table('chat_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_conv_type', 'chat_conversations', ['type'], unique=False)
    op.create_index('ix_chat_conv_created_by', 'chat_conversations', ['created_by'], unique=False)

    # 创建聊天参与者表
    op.create_table('chat_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'user_id', name='uq_chat_participant_conv_user')
    )
    op.create_index('ix_chat_participant_user_id', 'chat_participants', ['user_id'], unique=False)

    # 创建聊天消息表
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_language', sa.String(length=10), nullable=True),
        sa.Column('is_ai_response', sa.Boolean(), nullable=True),
        sa.Column('ai_model', sa.String(length=50), nullable=True),
        sa.Column('ai_prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('ai_completion_tokens', sa.Integer(), nullable=True),
        sa.Column('reply_to_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reply_to_id'], ['chat_messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_msg_conv_created', 'chat_messages', ['conversation_id', 'created_at'], unique=False)
    op.create_index('ix_chat_msg_sender_id', 'chat_messages', ['sender_id'], unique=False)

    # 创建聊天翻译表
    op.create_table('chat_translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('translated_content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'target_language', name='uq_chat_translation_msg_lang')
    )


def downgrade():
    op.drop_table('chat_translations')
    op.drop_table('chat_messages')
    op.drop_table('chat_participants')
    op.drop_table('chat_conversations')
