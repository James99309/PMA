"""添加采购模块编码相关字段

新增字段:
1. users.linked_company_id - 关联外部用户(供应商/代理商/客户)到Company表
2. companies.supplier_code - 供应商编码(3-4字符)用于序列号生成
3. products.serial_code - 序列号编码(5字符)用于产品序列号生成

Revision ID: 6eef2ad2bfd0
Revises:
Create Date: 2026-01-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6eef2ad2bfd0'
down_revision = 'add_order_module_tables_20260110'
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
    # 用于关联外部用户(供应商、代理商、客户联系人)到Company表
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
    # 供应商编码，用于生成产品序列号，格式：3-4位字母
    if 'supplier_code' not in companies_columns:
        with op.batch_alter_table('companies', schema=None) as batch_op:
            batch_op.add_column(sa.Column('supplier_code', sa.String(10), nullable=True))
            batch_op.create_unique_constraint('uq_companies_supplier_code', ['supplier_code'])
        print("  ✓ 添加字段 companies.supplier_code")
    else:
        print("  - companies.supplier_code 字段已存在，跳过")

    # 3. 添加 products.serial_code 字段
    # 序列号编码，用于生成产品序列号，格式：5位字母数字
    if 'serial_code' not in products_columns:
        with op.batch_alter_table('products', schema=None) as batch_op:
            batch_op.add_column(sa.Column('serial_code', sa.String(10), nullable=True))
            batch_op.create_unique_constraint('uq_products_serial_code', ['serial_code'])
        print("  ✓ 添加字段 products.serial_code")
    else:
        print("  - products.serial_code 字段已存在，跳过")


def downgrade():
    # 3. 移除 products.serial_code 字段
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('uq_products_serial_code', type_='unique')
        batch_op.drop_column('serial_code')

    # 2. 移除 companies.supplier_code 字段
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.drop_constraint('uq_companies_supplier_code', type_='unique')
        batch_op.drop_column('supplier_code')

    # 1. 移除 users.linked_company_id 字段
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_linked_company_id', type_='foreignkey')
        batch_op.drop_column('linked_company_id')
