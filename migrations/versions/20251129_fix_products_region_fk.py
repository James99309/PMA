"""Fix products region_id foreign key constraint

Revision ID: 20251129_fix_region_fk
Revises: 20251129_move_subcategory
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251129_fix_region_fk'
down_revision = '20251129_move_subcategory'
branch_labels = None
depends_on = None


def upgrade():
    """修复 products 表 region_id 外键约束，从 product_regions 改为 product_code_fields"""
    conn = op.get_bind()

    # 检查旧约束是否存在
    result = conn.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'products'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name = 'fk_products_region'
    """))
    old_constraint_exists = result.fetchone() is not None

    if old_constraint_exists:
        # 删除旧的外键约束（指向 product_regions）
        op.drop_constraint('fk_products_region', 'products', type_='foreignkey')

    # 检查新约束是否已存在
    result = conn.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'products'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name = 'fk_products_region_code_fields'
    """))
    new_constraint_exists = result.fetchone() is not None

    if not new_constraint_exists:
        # 创建新的外键约束（指向 product_code_fields）
        op.create_foreign_key(
            'fk_products_region_code_fields',
            'products',
            'product_code_fields',
            ['region_id'],
            ['id']
        )


def downgrade():
    """回滚：恢复旧的外键约束"""
    conn = op.get_bind()

    # 检查新约束是否存在
    result = conn.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'products'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name = 'fk_products_region_code_fields'
    """))
    new_constraint_exists = result.fetchone() is not None

    if new_constraint_exists:
        op.drop_constraint('fk_products_region_code_fields', 'products', type_='foreignkey')

    # 检查旧约束是否已存在
    result = conn.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'products'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name = 'fk_products_region'
    """))
    old_constraint_exists = result.fetchone() is not None

    if not old_constraint_exists:
        op.create_foreign_key(
            'fk_products_region',
            'products',
            'product_regions',
            ['region_id'],
            ['id']
        )
