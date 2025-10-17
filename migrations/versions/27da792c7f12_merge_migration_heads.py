
"""Merge migration heads

Revision ID: 27da792c7f12
Revises: add_project_created_by_field, add_settlement_business_type_20251014
Create Date: 2025-10-15 17:45:22.337154

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27da792c7f12'
down_revision = ('add_project_created_by_field', 'add_settlement_business_type_20251014')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass