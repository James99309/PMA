"""add archive fields to file_library

Revision ID: 429349b8805f
Revises: 594c8dce9aea
Create Date: 2026-02-14 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '429349b8805f'
down_revision = '594c8dce9aea'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('file_library', sa.Column('is_archived', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('file_library', sa.Column('archived_at', sa.DateTime(), nullable=True))
    op.add_column('file_library', sa.Column('archive_reason', sa.String(length=20), nullable=True))
    op.add_column('file_library', sa.Column('original_size', sa.BigInteger(), nullable=True))
    op.add_column('file_library', sa.Column('last_accessed_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_file_library_is_archived'), 'file_library', ['is_archived'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_file_library_is_archived'), table_name='file_library')
    op.drop_column('file_library', 'last_accessed_at')
    op.drop_column('file_library', 'original_size')
    op.drop_column('file_library', 'archive_reason')
    op.drop_column('file_library', 'archived_at')
    op.drop_column('file_library', 'is_archived')
