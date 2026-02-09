"""add manager_id to product_categories

Revision ID: a1b2c3d4e501
Revises: ded5068735f0
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers
revision = 'a1b2c3d4e501'
down_revision = 'ded5068735f0'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('product_categories')]

    if 'manager_id' not in columns:
        op.add_column('product_categories',
                       sa.Column('manager_id', sa.Integer(),
                                 sa.ForeignKey('users.id'), nullable=True,
                                 comment='产品经理ID'))


def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('product_categories')]

    if 'manager_id' in columns:
        op.drop_column('product_categories', 'manager_id')
