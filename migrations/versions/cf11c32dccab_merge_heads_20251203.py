
"""merge_heads_20251203

Revision ID: cf11c32dccab
Revises: add_quotation_spec_config_20251201, add_subcategory_field_options
Create Date: 2025-12-03 20:53:17.776967

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf11c32dccab'
down_revision = ('add_quotation_spec_config_20251201', 'add_subcategory_field_options')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass