"""新增action_reply表用于行动记录多级回复

Revision ID: 20240511_action_reply
Revises: 20240510_action_nullable
Create Date: 2024-05-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240511_action_reply'
down_revision = '20240510_action_nullable'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'action_reply',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('action_id', sa.Integer(), sa.ForeignKey('actions.id'), nullable=False),
        sa.Column('parent_reply_id', sa.Integer(), sa.ForeignKey('action_reply.id'), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table('action_reply') 