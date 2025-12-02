"""在 ProductCodeFieldOption 表增加 subcategory_id 字段

将可配置字段选项从分类级别下沉到子分类级别：
- 新增 subcategory_id 字段：区分子分类级选项
- 新增 allow_quotation_config 字段：控制是否允许报价配置

Revision ID: add_subcategory_field_options
Revises:
Create Date: 2025-12-02
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_subcategory_field_options'
down_revision = '20251129_fix_region_fk'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 在 ProductCodeFieldOption 表增加 subcategory_id 字段
    # NULL 表示分类级选项（用于产品编码），有值表示子分类级选项（用于报价可配置）
    op.add_column('product_code_field_options',
        sa.Column('subcategory_id', sa.Integer(), nullable=True)
    )

    # 创建外键约束
    op.create_foreign_key(
        'fk_field_options_subcategory',
        'product_code_field_options',
        'product_subcategories',
        ['subcategory_id'],
        ['id']
    )

    # 创建索引以提高查询性能
    op.create_index(
        'ix_product_code_field_options_subcategory_id',
        'product_code_field_options',
        ['subcategory_id']
    )

    # 2. 在 ProductCodeFieldOption 表增加 allow_quotation_config 字段
    # 仅子分类级选项使用，控制是否允许在报价单中配置
    op.add_column('product_code_field_options',
        sa.Column('allow_quotation_config', sa.Boolean(), server_default='false', nullable=True)
    )


def downgrade():
    # 移除 allow_quotation_config 字段
    op.drop_column('product_code_field_options', 'allow_quotation_config')

    # 移除索引
    op.drop_index('ix_product_code_field_options_subcategory_id', table_name='product_code_field_options')

    # 移除外键约束
    op.drop_constraint('fk_field_options_subcategory', 'product_code_field_options', type_='foreignkey')

    # 移除 subcategory_id 字段
    op.drop_column('product_code_field_options', 'subcategory_id')
