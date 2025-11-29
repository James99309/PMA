
"""Merge migration heads

Revision ID: 528dc1c41c03
Revises: 20251129_spec_options, 755718615540
Create Date: 2025-11-29 21:06:05.670537

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '528dc1c41c03'
down_revision = ('20251129_spec_options', '755718615540')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass