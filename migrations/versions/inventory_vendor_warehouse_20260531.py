"""inventory 加 is_vendor_warehouse + company_id nullable + partial unique index

Revision ID: inventory_vendor_warehouse_20260531
Revises: lockable_po_so_pricing_20260529
Create Date: 2026-05-31

厂商系统级仓库改造:
- company_id 从 NOT NULL 改成 nullable (厂商仓库时为 NULL)
- 新增 is_vendor_warehouse Boolean (default false)
- 原唯一约束 (company_id, product_id) 删除,改为两条 partial unique index:
  · 厂商仓:(is_vendor_warehouse, product_id) WHERE is_vendor_warehouse=true
  · 客户仓:(company_id, product_id) WHERE company_id IS NOT NULL
"""
from alembic import op
import sqlalchemy as sa


revision = 'inventory_vendor_warehouse_20260531'
down_revision = 'lockable_po_so_pricing_20260529'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 加 is_vendor_warehouse 字段
    with op.batch_alter_table('inventory') as batch_op:
        batch_op.add_column(sa.Column(
            'is_vendor_warehouse', sa.Boolean(),
            nullable=False, server_default=sa.false()
        ))

    # 2. company_id 改 nullable
    op.alter_column('inventory', 'company_id', nullable=True)

    # 3. 删除老的唯一约束,改为两条 partial unique index
    op.drop_constraint('unique_company_product_inventory', 'inventory', type_='unique')

    op.execute("""
        CREATE UNIQUE INDEX uniq_inventory_customer_product
        ON inventory (company_id, product_id)
        WHERE company_id IS NOT NULL
    """)

    op.execute("""
        CREATE UNIQUE INDEX uniq_inventory_vendor_product
        ON inventory (product_id)
        WHERE is_vendor_warehouse = true
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS uniq_inventory_vendor_product")
    op.execute("DROP INDEX IF EXISTS uniq_inventory_customer_product")

    # 删除厂商仓库记录(否则 NOT NULL 约束会失败)
    op.execute("DELETE FROM inventory WHERE is_vendor_warehouse = true OR company_id IS NULL")

    op.create_unique_constraint(
        'unique_company_product_inventory', 'inventory',
        ['company_id', 'product_id']
    )
    op.alter_column('inventory', 'company_id', nullable=False)

    with op.batch_alter_table('inventory') as batch_op:
        batch_op.drop_column('is_vendor_warehouse')
