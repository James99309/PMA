"""修复缺失的linked_company_id等字段

由于多分支迁移合并问题，6eef2ad2bfd0迁移可能未被执行。
此迁移确保以下字段存在：
1. users.linked_company_id
2. companies.supplier_code
3. products.serial_code

Revision ID: fix_missing_linked_company_id_20260112
Revises: merge_all_heads_20260111
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_missing_linked_company_id_20260112'
down_revision = 'merge_all_heads_20260111'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 获取现有列信息
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    companies_columns = [col['name'] for col in inspector.get_columns('companies')]
    products_columns = [col['name'] for col in inspector.get_columns('products')]

    # 1. 添加 users.linked_company_id 字段
    if 'linked_company_id' not in users_columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('linked_company_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                'fk_users_linked_company_id',
                'companies',
                ['linked_company_id'],
                ['id']
            )
        print("  ✓ 添加字段 users.linked_company_id")
    else:
        print("  - users.linked_company_id 字段已存在，跳过")

    # 2. 添加 companies.supplier_code 字段
    if 'supplier_code' not in companies_columns:
        with op.batch_alter_table('companies', schema=None) as batch_op:
            batch_op.add_column(sa.Column('supplier_code', sa.String(10), nullable=True))
            batch_op.create_unique_constraint('uq_companies_supplier_code', ['supplier_code'])
        print("  ✓ 添加字段 companies.supplier_code")
    else:
        print("  - companies.supplier_code 字段已存在，跳过")

    # 3. 添加 products.serial_code 字段
    if 'serial_code' not in products_columns:
        with op.batch_alter_table('products', schema=None) as batch_op:
            batch_op.add_column(sa.Column('serial_code', sa.String(10), nullable=True))
            batch_op.create_unique_constraint('uq_products_serial_code', ['serial_code'])
        print("  ✓ 添加字段 products.serial_code")
    else:
        print("  - products.serial_code 字段已存在，跳过")


def downgrade():
    # 这是修复性迁移，降级时不做任何操作
    # 因为字段可能是由 6eef2ad2bfd0 创建的
    pass
