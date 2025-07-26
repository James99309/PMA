
"""merge_heads_for_sp8d_migration

Revision ID: e069ac4907d0
Revises: 592b90d54921, sp8d001_tables
Create Date: 2025-07-26 14:36:19.020772

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e069ac4907d0'
down_revision = ('592b90d54921', 'sp8d001_tables')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass