
"""add procurement shipment linkage fields

Revision ID: ecc58026c4eb
Revises: 240f1150d812
Create Date: 2026-03-24 00:18:55.432473

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ecc58026c4eb'
down_revision = '240f1150d812'
branch_labels = None
depends_on = None


# ── 幂等守卫:订单-发货链路曾以 cherry-pick 方式直接加列上生产(未走迁移),
#    此处升级时列/外键可能已存在 → 存在则跳过,保证多血缘对账可重复执行 ──
def _has_col(table, col):
    insp = sa.inspect(op.get_bind())
    return col in [c['name'] for c in insp.get_columns(table)]

def _has_fk(table, name):
    insp = sa.inspect(op.get_bind())
    return name in [fk['name'] for fk in insp.get_foreign_keys(table)]


def upgrade():
    # SalesOrderDetail: 新增采购跟踪字段
    if not _has_col('sales_order_details', 'procured_quantity'):
        op.add_column('sales_order_details', sa.Column('procured_quantity', sa.Integer(), nullable=True, server_default='0'))

    # PurchaseOrderDetail: 新增客户需求关联和发货跟踪字段
    if not _has_col('purchase_order_details', 'sales_order_detail_id'):
        op.add_column('purchase_order_details', sa.Column('sales_order_detail_id', sa.Integer(), nullable=True))
    if not _has_col('purchase_order_details', 'dispatched_quantity'):
        op.add_column('purchase_order_details', sa.Column('dispatched_quantity', sa.Integer(), nullable=True, server_default='0'))
    if not _has_fk('purchase_order_details', 'fk_po_detail_so_detail'):
        op.create_foreign_key('fk_po_detail_so_detail', 'purchase_order_details', 'sales_order_details', ['sales_order_detail_id'], ['id'])

    # Shipment: 新增采购订单来源关联，sales_order_id 改为 nullable
    if not _has_col('shipments', 'purchase_order_id'):
        op.add_column('shipments', sa.Column('purchase_order_id', sa.Integer(), nullable=True))
    if not _has_fk('shipments', 'fk_shipment_purchase_order'):
        op.create_foreign_key('fk_shipment_purchase_order', 'shipments', 'purchase_orders', ['purchase_order_id'], ['id'])
    op.alter_column('shipments', 'sales_order_id', existing_type=sa.Integer(), nullable=True)

    # ShipmentDetail: 新增采购订单明细关联
    if not _has_col('shipment_details', 'purchase_order_detail_id'):
        op.add_column('shipment_details', sa.Column('purchase_order_detail_id', sa.Integer(), nullable=True))
    if not _has_fk('shipment_details', 'fk_shipment_detail_po_detail'):
        op.create_foreign_key('fk_shipment_detail_po_detail', 'shipment_details', 'purchase_order_details', ['purchase_order_detail_id'], ['id'])


def downgrade():
    # ShipmentDetail
    op.drop_constraint('fk_shipment_detail_po_detail', 'shipment_details', type_='foreignkey')
    op.drop_column('shipment_details', 'purchase_order_detail_id')

    # Shipment
    op.alter_column('shipments', 'sales_order_id', existing_type=sa.Integer(), nullable=False)
    op.drop_constraint('fk_shipment_purchase_order', 'shipments', type_='foreignkey')
    op.drop_column('shipments', 'purchase_order_id')

    # PurchaseOrderDetail
    op.drop_constraint('fk_po_detail_so_detail', 'purchase_order_details', type_='foreignkey')
    op.drop_column('purchase_order_details', 'dispatched_quantity')
    op.drop_column('purchase_order_details', 'sales_order_detail_id')

    # SalesOrderDetail
    op.drop_column('sales_order_details', 'procured_quantity')
