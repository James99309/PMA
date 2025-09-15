
"""Add stage_records column to dev_products table

Revision ID: cefa7a906d3f
Revises: 3236147db2f8
Create Date: 2025-09-07 23:17:55.177105

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cefa7a906d3f'
down_revision = '3236147db2f8'
branch_labels = None
depends_on = None


def upgrade():
    # Add stage_records column to dev_products table
    op.add_column('dev_products', sa.Column('stage_records', sa.JSON(), nullable=True))


def downgrade():
    # Remove stage_records column from dev_products table
    op.drop_column('dev_products', 'stage_records')