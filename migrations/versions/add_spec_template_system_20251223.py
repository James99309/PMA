"""Add spec template system for R&D product configuration

This migration creates 9 new tables for the specification template system:
- test_method_dictionary: Test method dictionary
- test_condition_dictionary: Test condition dictionary
- spec_categories: Specification categories (8 categories)
- spec_definitions: Global specification dictionary
- spec_templates: Model-level specification templates
- spec_template_items: Template specification items
- product_configurations: Product configuration versions
- product_config_values: Configuration version values
- spec_attachments: Specification attachments

And adds 3 new fields:
- dev_products.spec_template_id
- dev_products.primary_config_id
- products.source_configuration_id

Revision ID: spec_template_001
Revises: be0fcb982e76
Create Date: 2025-12-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'spec_template_001'
down_revision = 'be0fcb982e76'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建测试方法字典表
    op.create_table(
        'test_method_dictionary',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 2. 创建测试条件字典表
    op.create_table(
        'test_condition_dictionary',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 3. 创建规格分类表
    op.create_table(
        'spec_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    # 4. 创建全局规格字典表
    op.create_table(
        'spec_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=True),
        sa.Column('unit', sa.String(length=30), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(length=20), nullable=True, server_default='text'),
        sa.Column('default_options', sa.JSON(), nullable=True),
        sa.Column('default_test_condition_id', sa.Integer(), nullable=True),
        sa.Column('default_test_method_id', sa.Integer(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['category_id'], ['spec_categories.id'], ),
        sa.ForeignKeyConstraint(['default_test_condition_id'], ['test_condition_dictionary.id'], ),
        sa.ForeignKeyConstraint(['default_test_method_id'], ['test_method_dictionary.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_id', 'name', name='uq_spec_definitions_category_name')
    )

    # 5. 创建规格模板表
    op.create_table(
        'spec_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True, server_default='V1.0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model')
    )

    # 6. 创建模板规格项定义表
    op.create_table(
        'spec_template_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('definition_id', sa.Integer(), nullable=True),
        sa.Column('general_value', sa.String(length=255), nullable=True),
        sa.Column('test_condition_id', sa.Integer(), nullable=True),
        sa.Column('test_condition_text', sa.String(length=200), nullable=True),
        sa.Column('test_method_id', sa.Integer(), nullable=True),
        sa.Column('test_method_text', sa.String(length=200), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_required', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['definition_id'], ['spec_definitions.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['spec_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_condition_id'], ['test_condition_dictionary.id'], ),
        sa.ForeignKeyConstraint(['test_method_id'], ['test_method_dictionary.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_id', 'definition_id', name='uq_spec_template_items_template_definition')
    )

    # 7. 创建产品配置版本表
    op.create_table(
        'product_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('dev_product_id', sa.Integer(), nullable=True),
        sa.Column('config_code', sa.String(length=50), nullable=False),
        sa.Column('region', sa.String(length=50), nullable=True),
        sa.Column('region_name', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='development'),
        sa.Column('mn_code', sa.String(length=50), nullable=True),
        sa.Column('power_spec', sa.String(length=50), nullable=True),
        sa.Column('power_cord_type', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['dev_product_id'], ['dev_products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['template_id'], ['spec_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_id', 'config_code', name='uq_product_configurations_template_config_code')
    )

    # 8. 创建配置版本规格值表
    op.create_table(
        'product_config_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('configuration_id', sa.Integer(), nullable=True),
        sa.Column('template_item_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['configuration_id'], ['product_configurations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_item_id'], ['spec_template_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('configuration_id', 'template_item_id', name='uq_product_config_values_config_item')
    )

    # 9. 创建规格附件表
    op.create_table(
        'spec_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_item_id', sa.Integer(), nullable=True),
        sa.Column('config_value_id', sa.Integer(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['config_value_id'], ['product_config_values.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_item_id'], ['spec_template_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            '(template_item_id IS NOT NULL AND config_value_id IS NULL) OR '
            '(template_item_id IS NULL AND config_value_id IS NOT NULL)',
            name='chk_spec_attachments_ref'
        )
    )

    # 10. 为dev_products表添加新字段
    op.add_column('dev_products', sa.Column('spec_template_id', sa.Integer(), nullable=True))
    op.add_column('dev_products', sa.Column('primary_config_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_dev_products_spec_template',
        'dev_products', 'spec_templates',
        ['spec_template_id'], ['id']
    )
    op.create_foreign_key(
        'fk_dev_products_primary_config',
        'dev_products', 'product_configurations',
        ['primary_config_id'], ['id']
    )

    # 11. 为products表添加新字段
    op.add_column('products', sa.Column('source_configuration_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_products_source_configuration',
        'products', 'product_configurations',
        ['source_configuration_id'], ['id']
    )

    # 12. 创建索引优化查询性能
    op.create_index('idx_spec_definitions_category', 'spec_definitions', ['category_id'])
    op.create_index('idx_spec_template_items_template', 'spec_template_items', ['template_id'])
    op.create_index('idx_spec_template_items_definition', 'spec_template_items', ['definition_id'])
    op.create_index('idx_product_configurations_template', 'product_configurations', ['template_id'])
    op.create_index('idx_product_configurations_dev_product', 'product_configurations', ['dev_product_id'])
    op.create_index('idx_product_config_values_configuration', 'product_config_values', ['configuration_id'])
    op.create_index('idx_spec_attachments_template_item', 'spec_attachments', ['template_item_id'])
    op.create_index('idx_spec_attachments_config_value', 'spec_attachments', ['config_value_id'])


def downgrade():
    # 删除索引
    op.drop_index('idx_spec_attachments_config_value', table_name='spec_attachments')
    op.drop_index('idx_spec_attachments_template_item', table_name='spec_attachments')
    op.drop_index('idx_product_config_values_configuration', table_name='product_config_values')
    op.drop_index('idx_product_configurations_dev_product', table_name='product_configurations')
    op.drop_index('idx_product_configurations_template', table_name='product_configurations')
    op.drop_index('idx_spec_template_items_definition', table_name='spec_template_items')
    op.drop_index('idx_spec_template_items_template', table_name='spec_template_items')
    op.drop_index('idx_spec_definitions_category', table_name='spec_definitions')

    # 删除products表的新增字段
    op.drop_constraint('fk_products_source_configuration', 'products', type_='foreignkey')
    op.drop_column('products', 'source_configuration_id')

    # 删除dev_products表的新增字段
    op.drop_constraint('fk_dev_products_primary_config', 'dev_products', type_='foreignkey')
    op.drop_constraint('fk_dev_products_spec_template', 'dev_products', type_='foreignkey')
    op.drop_column('dev_products', 'primary_config_id')
    op.drop_column('dev_products', 'spec_template_id')

    # 删除新建的表（按依赖顺序逆序删除）
    op.drop_table('spec_attachments')
    op.drop_table('product_config_values')
    op.drop_table('product_configurations')
    op.drop_table('spec_template_items')
    op.drop_table('spec_templates')
    op.drop_table('spec_definitions')
    op.drop_table('spec_categories')
    op.drop_table('test_condition_dictionary')
    op.drop_table('test_method_dictionary')
