
"""add permission field to diagram_share_tokens

Revision ID: 20d4b0658fcf
Revises: k5e6f7g8h9i0
Create Date: 2026-02-26 08:03:10.353100

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20d4b0658fcf'
down_revision = 'k5e6f7g8h9i0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('diagram_share_tokens',
                  sa.Column('permission', sa.String(length=10),
                            nullable=False, server_default='edit'))


def downgrade():
    op.drop_column('diagram_share_tokens', 'permission')
