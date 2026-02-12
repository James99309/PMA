
"""add product points coefficient fields

Revision ID: 6831979cdbe4
Revises: add_tasks_tables_20260210
Create Date: 2026-02-11 23:30:01.822073

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6831979cdbe4'
down_revision = 'add_tasks_tables_20260210'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('points_coefficient_override', sa.Numeric(precision=3, scale=1), nullable=True, comment='手动积分系数起始值(Admin设置,NULL=按created_at自动)'))
    op.add_column('products', sa.Column('points_coefficient_override_at', sa.DateTime(), nullable=True, comment='手动系数设置时间(衰减起点)'))


def downgrade():
    op.drop_column('products', 'points_coefficient_override_at')
    op.drop_column('products', 'points_coefficient_override')
