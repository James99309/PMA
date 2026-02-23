"""add is_template to system_diagrams

Revision ID: i3c4d5e6f7g8
Revises: h2b3c4d5e6f7
Create Date: 2026-02-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i3c4d5e6f7g8'
down_revision = 'h2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('system_diagrams',
        sa.Column('is_template', sa.Boolean(), server_default='false', nullable=False))
    op.create_index('ix_system_diagrams_is_template', 'system_diagrams', ['is_template'])


def downgrade():
    op.drop_index('ix_system_diagrams_is_template', table_name='system_diagrams')
    op.drop_column('system_diagrams', 'is_template')
