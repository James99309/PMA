"""add user_folder_shares table for folder sharing

Revision ID: folder_shares_20260520
Revises: merge_mobile_api_20260515
Create Date: 2026-05-20

"""
from alembic import op
import sqlalchemy as sa


revision = 'folder_shares_20260520'
down_revision = 'merge_mobile_api_20260515'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_folder_shares',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('folder_id', sa.Integer(),
                  sa.ForeignKey('user_folders.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('shared_with_user_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('shared_by_user_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('permission', sa.String(10), nullable=False, server_default='read'),
        sa.Column('message', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_user_folder_shares_folder_id',
                    'user_folder_shares', ['folder_id'])
    op.create_index('ix_user_folder_shares_shared_with_user_id',
                    'user_folder_shares', ['shared_with_user_id'])
    op.create_index('ix_user_folder_shares_folder_user',
                    'user_folder_shares', ['folder_id', 'shared_with_user_id'],
                    unique=True)
    op.create_index('ix_user_folder_shares_user_active',
                    'user_folder_shares', ['shared_with_user_id', 'is_active'])


def downgrade():
    op.drop_index('ix_user_folder_shares_user_active', table_name='user_folder_shares')
    op.drop_index('ix_user_folder_shares_folder_user', table_name='user_folder_shares')
    op.drop_index('ix_user_folder_shares_shared_with_user_id', table_name='user_folder_shares')
    op.drop_index('ix_user_folder_shares_folder_id', table_name='user_folder_shares')
    op.drop_table('user_folder_shares')
