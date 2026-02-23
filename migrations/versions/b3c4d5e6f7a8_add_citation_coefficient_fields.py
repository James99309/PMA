
"""Add citation_coefficient and citation_count to products table

Revision ID: b3c4d5e6f7a8
Revises: ca8d42e860a8
Create Date: 2026-02-20 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7a8'
down_revision = 'ca8d42e860a8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('citation_coefficient', sa.Numeric(4, 2), nullable=True, comment='引用频率积分系数'))
    op.add_column('products', sa.Column('citation_count', sa.Integer(), nullable=True, comment='过去12个月引用次数'))


def downgrade():
    op.drop_column('products', 'citation_count')
    op.drop_column('products', 'citation_coefficient')
