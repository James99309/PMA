"""add product specs

Revision ID: add_product_specs
Revises: 
Create Date: 2025-04-24 11:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_product_specs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建 dev_product_specs 表（如果不存在）
    op.create_table('dev_product_specs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dev_product_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(length=128), nullable=False),
        sa.Column('field_value', sa.String(length=128), nullable=True),
        sa.Column('field_code', sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(['dev_product_id'], ['dev_products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # 删除表
    op.drop_table('dev_product_specs') 