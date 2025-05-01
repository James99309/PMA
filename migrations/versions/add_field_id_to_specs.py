"""add field_id to specs

Revision ID: add_field_id_to_specs
Revises: 
Create Date: 2025-04-24 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_field_id_to_specs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加 field_id 字段到 dev_product_specs 表
    op.add_column('dev_product_specs', sa.Column('field_id', sa.Integer(), nullable=True))
    
    # 添加外键（如果需要）
    op.create_foreign_key(
        'fk_dev_product_specs_field_id', 
        'dev_product_specs', 
        'product_code_fields', 
        ['field_id'], 
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # 删除外键
    op.drop_constraint('fk_dev_product_specs_field_id', 'dev_product_specs', type_='foreignkey')
    
    # 删除字段
    op.drop_column('dev_product_specs', 'field_id') 