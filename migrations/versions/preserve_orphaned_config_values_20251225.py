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
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'preserve_orphaned_config_values_20251225'
down_revision = None
branch_labels = None
depends_on = None


def table_exists(table_name):
    """检查表是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """检查列是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def constraint_exists(table_name, constraint_name):
    """检查外键约束是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    fks = inspector.get_foreign_keys(table_name)
    return any(fk.get('name') == constraint_name for fk in fks)


def upgrade():
    # 检查表是否存在
    if not table_exists('product_config_values'):
        return

    # 1. 添加孤立项信息字段（只添加不存在的列）
    columns_to_add = [
        ('orphaned_spec_name', sa.String(200)),
        ('orphaned_spec_name_en', sa.String(200)),
        ('orphaned_spec_unit', sa.String(50)),
        ('orphaned_category_id', sa.Integer()),
    ]

    for col_name, col_type in columns_to_add:
        if not column_exists('product_config_values', col_name):
            op.add_column('product_config_values',
                sa.Column(col_name, col_type, nullable=True))

    # 2. 修改外键约束：从 CASCADE 改为 SET NULL
    # 只在外键存在时处理
    if constraint_exists('product_config_values', 'product_config_values_template_item_id_fkey'):
        try:
            op.drop_constraint('product_config_values_template_item_id_fkey', 'product_config_values', type_='foreignkey')
            op.create_foreign_key(
                'product_config_values_template_item_id_fkey',
                'product_config_values',
                'spec_template_items',
                ['template_item_id'],
                ['id'],
                ondelete='SET NULL'
            )
        except Exception:
            pass  # 忽略外键操作失败


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
