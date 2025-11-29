
"""merge_heads

Revision ID: 77cc9d8fabcc
Revises: add_product_mn_locked, add_development_purpose_20251124, bccffbe037d7
Create Date: 2025-11-29 12:28:07.272361

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77cc9d8fabcc'
down_revision = ('add_product_mn_locked', 'add_development_purpose_20251124', 'bccffbe037d7')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass