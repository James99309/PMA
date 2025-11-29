
"""add_category_id_to_product_code_fields

Revision ID: 3358cee70c59
Revises: 77cc9d8fabcc
Create Date: 2025-11-29 12:28:12.789997

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3358cee70c59'
down_revision = '77cc9d8fabcc'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 category_id 列
    op.add_column('product_code_fields',
        sa.Column('category_id', sa.Integer(), nullable=True)
    )
    # 添加外键约束
    op.create_foreign_key(
        'fk_product_code_fields_category_id',
        'product_code_fields', 'product_categories',
        ['category_id'], ['id']
    )


def downgrade():
    # 删除外键约束
    op.drop_constraint('fk_product_code_fields_category_id', 'product_code_fields', type_='foreignkey')
    # 删除列
    op.drop_column('product_code_fields', 'category_id')