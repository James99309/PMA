"""merge heads

Revision ID: 7ca40c445fb1
Revises: add_field_id_to_specs, add_product_specs
Create Date: 2025-04-24 12:21:18.920906

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ca40c445fb1'
down_revision = ('add_field_id_to_specs', 'add_product_specs')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
