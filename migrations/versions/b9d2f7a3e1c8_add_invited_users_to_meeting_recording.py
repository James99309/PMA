"""add invited_user_ids to meeting_recordings

Revision ID: b9d2f7a3e1c8
Revises: a8c1d2e3f4b5
Create Date: 2026-05-12 16:00:00

让发起人在录音时可以邀请 PMA 同事旁听，权限层据此放行被邀请人。
"""
from alembic import op
import sqlalchemy as sa


revision = 'b9d2f7a3e1c8'
down_revision = 'a8c1d2e3f4b5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('meeting_recordings', sa.Column('invited_user_ids', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('meeting_recordings', 'invited_user_ids')
