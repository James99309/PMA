"""add announcement tables

Revision ID: add_announcements_20260105
Revises:
Create Date: 2026-01-05

创建公告系统表：announcements(公告), announcement_reads(阅读记录), announcement_attachments(附件)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_announcements_20260105'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建公告系统表"""
    # 1. 创建公告主表
    op.create_table('announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('announcement_type', sa.String(length=20), nullable=False, server_default='system'),
        sa.Column('target_users', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('scheduled_time', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_announcements_announcement_type', 'announcements', ['announcement_type'], unique=False)
    op.create_index('ix_announcements_status', 'announcements', ['status'], unique=False)
    op.create_index('ix_announcements_created_at', 'announcements', ['created_at'], unique=False)
    op.create_index('ix_announcements_status_published', 'announcements', ['status', 'published_at'], unique=False)

    # 2. 创建阅读记录表
    op.create_table('announcement_reads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('announcement_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['announcement_id'], ['announcements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('announcement_id', 'user_id', name='uq_announcement_user')
    )
    op.create_index('ix_announcement_reads_announcement_id', 'announcement_reads', ['announcement_id'], unique=False)
    op.create_index('ix_announcement_reads_user_id', 'announcement_reads', ['user_id'], unique=False)
    op.create_index('ix_announcement_reads_is_read', 'announcement_reads', ['is_read'], unique=False)
    op.create_index('ix_announcement_reads_user_unread', 'announcement_reads', ['user_id', 'is_read'], unique=False)

    # 3. 创建附件表
    op.create_table('announcement_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('announcement_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['announcement_id'], ['announcements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_announcement_attachments_announcement_id', 'announcement_attachments', ['announcement_id'], unique=False)


def downgrade():
    """删除公告系统表"""
    op.drop_index('ix_announcement_attachments_announcement_id', table_name='announcement_attachments')
    op.drop_table('announcement_attachments')

    op.drop_index('ix_announcement_reads_user_unread', table_name='announcement_reads')
    op.drop_index('ix_announcement_reads_is_read', table_name='announcement_reads')
    op.drop_index('ix_announcement_reads_user_id', table_name='announcement_reads')
    op.drop_index('ix_announcement_reads_announcement_id', table_name='announcement_reads')
    op.drop_table('announcement_reads')

    op.drop_index('ix_announcements_status_published', table_name='announcements')
    op.drop_index('ix_announcements_created_at', table_name='announcements')
    op.drop_index('ix_announcements_status', table_name='announcements')
    op.drop_index('ix_announcements_announcement_type', table_name='announcements')
    op.drop_table('announcements')
