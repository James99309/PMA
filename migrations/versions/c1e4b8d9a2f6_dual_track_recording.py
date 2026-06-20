"""add system track storage to meeting_recordings (dual-track recording)

Revision ID: c1e4b8d9a2f6
Revises: b9d2f7a3e1c8
Create Date: 2026-05-12 17:30:00

录音改为双轨：
- storage_path: mixed 轨（mic+system 混音，用于回放）
- system_storage_path: system 轨（仅对方端，用于 pyannote 单边声纹分离）
"""
from alembic import op
import sqlalchemy as sa


revision = 'c1e4b8d9a2f6'
down_revision = 'b9d2f7a3e1c8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('meeting_recordings', sa.Column('system_storage_path', sa.String(500), nullable=True))
    op.add_column('meeting_recordings', sa.Column('system_storage_url', sa.String(1000), nullable=True))
    op.add_column('meeting_recordings', sa.Column('system_chunk_paths', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('meeting_recordings', 'system_chunk_paths')
    op.drop_column('meeting_recordings', 'system_storage_url')
    op.drop_column('meeting_recordings', 'system_storage_path')
