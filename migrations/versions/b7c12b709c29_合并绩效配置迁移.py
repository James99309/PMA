
"""合并绩效配置迁移

Revision ID: b7c12b709c29
Revises: add_performance_config, deb370427992
Create Date: 2025-08-11 16:27:42.513331

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c12b709c29'
down_revision = ('add_performance_config', 'deb370427992')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass