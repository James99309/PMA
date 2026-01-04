"""add category_id and subcategory_id to spec_templates

Revision ID: add_category_to_spec_template_20251224
Revises:
Create Date: 2024-12-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_category_to_spec_template_20251224'
down_revision = 'spec_template_001'
branch_labels = None
depends_on = None


def upgrade():
    """添加 category_id 和 subcategory_id 字段到 spec_templates 表"""
    # 添加 category_id 字段
    op.add_column('spec_templates', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_spec_templates_category_id',
        'spec_templates', 'product_categories',
        ['category_id'], ['id']
    )

    # 添加 subcategory_id 字段
    op.add_column('spec_templates', sa.Column('subcategory_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_spec_templates_subcategory_id',
        'spec_templates', 'product_subcategories',
        ['subcategory_id'], ['id']
    )


def downgrade():
    """移除 category_id 和 subcategory_id 字段"""
    op.drop_constraint('fk_spec_templates_subcategory_id', 'spec_templates', type_='foreignkey')
    op.drop_column('spec_templates', 'subcategory_id')

    op.drop_constraint('fk_spec_templates_category_id', 'spec_templates', type_='foreignkey')
    op.drop_column('spec_templates', 'category_id')
