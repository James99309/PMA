"""add admin_locked fields to user_file_refs

Revision ID: 27b5f37f1c30
Revises: 5286a32c3d63
Create Date: 2026-05-05 06:26:23.171448

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27b5f37f1c30'
down_revision = '5286a32c3d63'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_file_refs', sa.Column('is_admin_locked', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('user_file_refs', sa.Column('admin_locked_at', sa.DateTime(), nullable=True))
    op.add_column('user_file_refs', sa.Column('admin_locked_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.create_index('ix_user_file_refs_is_admin_locked', 'user_file_refs', ['is_admin_locked'])


def downgrade():
    op.drop_index('ix_user_file_refs_is_admin_locked', table_name='user_file_refs')
    op.drop_column('user_file_refs', 'admin_locked_by')
    op.drop_column('user_file_refs', 'admin_locked_at')
    op.drop_column('user_file_refs', 'is_admin_locked')
