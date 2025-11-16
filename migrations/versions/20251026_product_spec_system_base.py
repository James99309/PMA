"""产品规格筛选系统基础表结构

Revision ID: 20251026_product_spec_base
Revises: unify_performance_targets_constraints_20250818
Create Date: 2025-10-26 14:46:03

说明：
- 创建 product_specs 表（产品规格值存储）
- 创建 product_relations 表（产品关联关系）
- 扩展 products 表（添加分类关联字段）
- 扩展 quotation_items 表（待定状态和附加产品支持）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251026_product_spec_base'
down_revision = 'add_quotation_currency_20251031'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建 product_specs 表（产品规格值存储）
    op.create_table('product_specs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('field_value', sa.String(length=255), nullable=False),
        sa.Column('field_code', sa.String(length=10), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建 product_specs 索引
    op.create_index('idx_product_specs_product', 'product_specs', ['product_id'])
    op.create_index('idx_product_specs_field_name', 'product_specs', ['field_name'])
    op.create_index('idx_product_specs_field_value', 'product_specs', ['field_value'])
    op.create_index('idx_product_specs_name_value', 'product_specs', ['field_name', 'field_value'])

    # 2. 创建 product_relations 表（产品关联关系）
    op.create_table('product_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('main_product_type', sa.String(length=20), nullable=False),
        sa.Column('main_product_id', sa.Integer(), nullable=False),
        sa.Column('related_product_id', sa.Integer(), nullable=False),
        sa.Column('relation_type', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('default_quantity', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('is_required', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['related_product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建 product_relations 索引
    op.create_index('idx_product_relations_main', 'product_relations', ['main_product_type', 'main_product_id'])
    op.create_index('idx_product_relations_related', 'product_relations', ['related_product_id'])

    # 3. 扩展 products 表
    op.add_column('products', sa.Column('category_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('subcategory_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('region_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('source_type', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('source_dev_product_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('productized_at', sa.DateTime(), nullable=True))

    # 创建 products 外键约束
    op.create_foreign_key('fk_products_category', 'products', 'product_categories', ['category_id'], ['id'])
    op.create_foreign_key('fk_products_subcategory', 'products', 'product_subcategories', ['subcategory_id'], ['id'])
    op.create_foreign_key('fk_products_region', 'products', 'product_regions', ['region_id'], ['id'])
    op.create_foreign_key('fk_products_source_dev', 'products', 'dev_products', ['source_dev_product_id'], ['id'])

    # 创建 products 索引
    op.create_index('idx_products_category', 'products', ['category_id'])
    op.create_index('idx_products_subcategory', 'products', ['subcategory_id'])
    op.create_index('idx_products_region', 'products', ['region_id'])

    # 4. 扩展 quotation_details 表（实际表名）
    op.add_column('quotation_details', sa.Column('pending_specs', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('quotation_details', sa.Column('parent_item_id', sa.Integer(), nullable=True))
    op.add_column('quotation_details', sa.Column('is_accessory', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('quotation_details', sa.Column('is_editable', sa.Boolean(), nullable=True, server_default='true'))

    # 创建 quotation_details 外键约束
    op.create_foreign_key('fk_quotation_details_parent', 'quotation_details', 'quotation_details', ['parent_item_id'], ['id'], ondelete='CASCADE')

    # 创建 quotation_details 索引
    op.create_index('idx_quotation_details_parent', 'quotation_details', ['parent_item_id'])


def downgrade():
    # 删除 quotation_details 的修改
    op.drop_index('idx_quotation_details_parent', table_name='quotation_details')
    op.drop_constraint('fk_quotation_details_parent', 'quotation_details', type_='foreignkey')
    op.drop_column('quotation_details', 'is_editable')
    op.drop_column('quotation_details', 'is_accessory')
    op.drop_column('quotation_details', 'parent_item_id')
    op.drop_column('quotation_details', 'pending_specs')

    # 删除 products 的修改
    op.drop_index('idx_products_region', table_name='products')
    op.drop_index('idx_products_subcategory', table_name='products')
    op.drop_index('idx_products_category', table_name='products')
    op.drop_constraint('fk_products_source_dev', 'products', type_='foreignkey')
    op.drop_constraint('fk_products_region', 'products', type_='foreignkey')
    op.drop_constraint('fk_products_subcategory', 'products', type_='foreignkey')
    op.drop_constraint('fk_products_category', 'products', type_='foreignkey')
    op.drop_column('products', 'productized_at')
    op.drop_column('products', 'source_dev_product_id')
    op.drop_column('products', 'source_type')
    op.drop_column('products', 'region_id')
    op.drop_column('products', 'subcategory_id')
    op.drop_column('products', 'category_id')

    # 删除 product_relations 表
    op.drop_index('idx_product_relations_related', table_name='product_relations')
    op.drop_index('idx_product_relations_main', table_name='product_relations')
    op.drop_table('product_relations')

    # 删除 product_specs 表
    op.drop_index('idx_product_specs_name_value', table_name='product_specs')
    op.drop_index('idx_product_specs_field_value', table_name='product_specs')
    op.drop_index('idx_product_specs_field_name', table_name='product_specs')
    op.drop_index('idx_product_specs_product', table_name='product_specs')
    op.drop_table('product_specs')
