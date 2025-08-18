
"""合并多个迁移头以支持项目status字段

Revision ID: 818231a27ec4
Revises: 2ce622455809, 979d4f8aa17e, add_approval_branch_support, add_approval_branch_support_v2, add_data_source_config, b7c12b709c29
Create Date: 2025-08-17 21:22:48.892200

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '818231a27ec4'
down_revision = ('2ce622455809', '979d4f8aa17e', 'add_approval_branch_support', 'add_approval_branch_support_v2', 'add_data_source_config', 'b7c12b709c29')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass