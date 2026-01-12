"""Add supplier confirmation file fields to purchase_orders

Revision ID: add_supplier_confirmation_file_20260111
Revises: add_order_module_tables_20260110
Create Date: 2026-01-11 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_supplier_confirmation_file_20260111'
down_revision = 'add_order_module_tables_20260110'
branch_labels = None
depends_on = None


def upgrade():
    # 添加供应商确认回执文件和备注字段
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('purchase_orders')]

    if 'supplier_confirmation_file' not in existing_columns:
        op.add_column('purchase_orders',
            sa.Column('supplier_confirmation_file', sa.String(500), nullable=True))

    if 'supplier_confirmation_notes' not in existing_columns:
        op.add_column('purchase_orders',
            sa.Column('supplier_confirmation_notes', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('purchase_orders', 'supplier_confirmation_notes')
    op.drop_column('purchase_orders', 'supplier_confirmation_file')
