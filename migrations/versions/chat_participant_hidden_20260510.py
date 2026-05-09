"""add is_hidden to chat_participants

Revision ID: chat_participant_hidden_20260510
Revises: approval_delegate_20260509
Create Date: 2026-05-10 00:30:00.000000

聊天对话"删除"语义改为"从列表移出"(仅自己列表隐藏, 收消息自动 unhide)。
原 chat_conversations.is_deleted 保留给"解散群"破坏性操作 + 群主权限。
"""
from alembic import op
import sqlalchemy as sa


revision = 'chat_participant_hidden_20260510'
down_revision = 'approval_delegate_20260509'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('chat_participants') as batch_op:
        batch_op.add_column(sa.Column(
            'is_hidden', sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ))


def downgrade():
    with op.batch_alter_table('chat_participants') as batch_op:
        batch_op.drop_column('is_hidden')
