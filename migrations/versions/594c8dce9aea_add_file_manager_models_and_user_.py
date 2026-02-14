
"""Add file manager models and user storage quota

Revision ID: 594c8dce9aea
Revises: d2269307de93
Create Date: 2026-02-14 11:53:08.284901

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '594c8dce9aea'
down_revision = 'd2269307de93'
branch_labels = None
depends_on = None


def upgrade():
    # 创建物理文件库表
    op.create_table('file_library',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('storage_path', sa.String(length=1000), nullable=False),
        sa.Column('storage_type', sa.String(length=20), nullable=True),
        sa.Column('ref_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sha256_hash')
    )
    op.create_index(op.f('ix_file_library_sha256_hash'), 'file_library', ['sha256_hash'], unique=True)

    # 创建用户文件夹表
    op.create_table('user_folders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['user_folders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_folders_user_id'), 'user_folders', ['user_id'], unique=False)
    op.create_index('ix_user_folders_user_parent', 'user_folders', ['user_id', 'parent_id'], unique=False)

    # 创建用户文件引用表
    op.create_table('user_file_refs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('folder_id', sa.Integer(), nullable=True),
        sa.Column('file_library_id', sa.Integer(), nullable=False),
        sa.Column('display_name', sa.String(length=500), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['file_library_id'], ['file_library.id'], ),
        sa.ForeignKeyConstraint(['folder_id'], ['user_folders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_file_refs_user_id'), 'user_file_refs', ['user_id'], unique=False)
    op.create_index('ix_user_file_refs_user_folder', 'user_file_refs', ['user_id', 'folder_id'], unique=False)
    op.create_index('ix_user_file_refs_user_deleted', 'user_file_refs', ['user_id', 'is_deleted'], unique=False)

    # 给 users 表添加存储配额字段
    op.add_column('users', sa.Column('storage_quota', sa.BigInteger(), nullable=True))
    op.add_column('users', sa.Column('storage_used', sa.BigInteger(), nullable=True))


def downgrade():
    op.drop_column('users', 'storage_used')
    op.drop_column('users', 'storage_quota')
    op.drop_index('ix_user_file_refs_user_deleted', table_name='user_file_refs')
    op.drop_index('ix_user_file_refs_user_folder', table_name='user_file_refs')
    op.drop_index(op.f('ix_user_file_refs_user_id'), table_name='user_file_refs')
    op.drop_table('user_file_refs')
    op.drop_index('ix_user_folders_user_parent', table_name='user_folders')
    op.drop_index(op.f('ix_user_folders_user_id'), table_name='user_folders')
    op.drop_table('user_folders')
    op.drop_index(op.f('ix_file_library_sha256_hash'), table_name='file_library')
    op.drop_table('file_library')
