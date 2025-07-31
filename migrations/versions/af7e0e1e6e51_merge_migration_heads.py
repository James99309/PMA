
"""merge_migration_heads

Revision ID: af7e0e1e6e51
Revises: ovs_sync_fix_20250729, sync_local_to_cloud_20250728
Create Date: 2025-07-30 08:17:43.467304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af7e0e1e6e51'
down_revision = ('ovs_sync_fix_20250729', 'sync_local_to_cloud_20250728')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass