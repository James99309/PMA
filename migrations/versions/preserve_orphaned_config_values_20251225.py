"""保留孤立配置值：修改外键策略和添加孤立项信息字段

当从模板中删除规格项时，锁定配置中保存的值需要保留。
- 修改 template_item_id 外键从 CASCADE 改为 SET NULL
- 添加字段保存孤立项的规格信息

Revision ID: preserve_orphaned_config_values_20251225
Revises:
Create Date: 2025-12-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'preserve_orphaned_config_values_20251225'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. 添加孤立项信息字段
    op.add_column('product_config_values',
        sa.Column('orphaned_spec_name', sa.String(200), nullable=True))
    op.add_column('product_config_values',
        sa.Column('orphaned_spec_name_en', sa.String(200), nullable=True))
    op.add_column('product_config_values',
        sa.Column('orphaned_spec_unit', sa.String(50), nullable=True))
    op.add_column('product_config_values',
        sa.Column('orphaned_category_id', sa.Integer(), nullable=True))

    # 2. 修改外键约束：从 CASCADE 改为 SET NULL
    # 先删除旧的外键约束
    op.drop_constraint('product_config_values_template_item_id_fkey', 'product_config_values', type_='foreignkey')

    # 创建新的外键约束，使用 SET NULL
    op.create_foreign_key(
        'product_config_values_template_item_id_fkey',
        'product_config_values',
        'spec_template_items',
        ['template_item_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # 1. 恢复外键约束为 CASCADE
    op.drop_constraint('product_config_values_template_item_id_fkey', 'product_config_values', type_='foreignkey')

    op.create_foreign_key(
        'product_config_values_template_item_id_fkey',
        'product_config_values',
        'spec_template_items',
        ['template_item_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # 2. 删除孤立项信息字段
    op.drop_column('product_config_values', 'orphaned_category_id')
    op.drop_column('product_config_values', 'orphaned_spec_unit')
    op.drop_column('product_config_values', 'orphaned_spec_name_en')
    op.drop_column('product_config_values', 'orphaned_spec_name')
