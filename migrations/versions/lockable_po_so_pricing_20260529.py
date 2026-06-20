"""Add lockable fields to purchase_orders / sales_orders / pricing_orders

Revision ID: lockable_po_so_pricing_20260529
Revises: so_detail_product_mn_20260529
Create Date: 2026-05-29

Phase 2 of approval-lock unification: 给 PO/SO/PricingOrder 加 LockableMixin
对应的 4 个字段(is_locked, locked_reason, locked_by, locked_at),让审批
模板配置 lock_object_on_start=true 时对这 3 类对象生效。
"""
from alembic import op
import sqlalchemy as sa


revision = 'lockable_po_so_pricing_20260529'
down_revision = 'so_detail_product_mn_20260529'
branch_labels = None
depends_on = None


_TABLES = ('purchase_orders', 'sales_orders', 'pricing_orders')


def upgrade():
    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(sa.Column('is_locked', sa.Boolean(), nullable=False, server_default=sa.false()))
            batch_op.add_column(sa.Column('locked_reason', sa.String(length=200), nullable=True))
            batch_op.add_column(sa.Column('locked_by', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('locked_at', sa.DateTime(), nullable=True))
            batch_op.create_foreign_key(
                f'fk_{table}_locked_by_users',
                'users',
                ['locked_by'], ['id']
            )


def downgrade():
    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(f'fk_{table}_locked_by_users', type_='foreignkey')
            batch_op.drop_column('locked_at')
            batch_op.drop_column('locked_by')
            batch_op.drop_column('locked_reason')
            batch_op.drop_column('is_locked')
