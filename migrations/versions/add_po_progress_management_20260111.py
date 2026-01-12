"""Add purchase order progress management fields

添加采购订单进度管理相关字段：
- 交期计划字段（milestone_test_complete_date, milestone_ship_date等）
- 超期状态字段（is_overdue, overdue_days, overdue_milestone）
- 阶段推进记录字段
- 测试条件扩展字段
- 新增 purchase_order_stage_history 表
- 新增 purchase_order_delivery_changes 表

Revision ID: add_po_progress_mgmt
Revises:
Create Date: 2026-01-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_po_progress_mgmt'
down_revision = 'add_order_module_tables_20260110'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    existing_columns = [col['name'] for col in inspector.get_columns('purchase_orders')] if 'purchase_orders' in existing_tables else []

    # ========== PurchaseOrder 新增字段 ==========
    columns_to_add = [
        ('milestone_test_complete_date', sa.DateTime(), None),
        ('milestone_ship_date', sa.DateTime(), None),
        ('delivery_schedule_locked', sa.Boolean(), 'false'),
        ('delivery_schedule_locked_at', sa.DateTime(), None),
        ('is_overdue', sa.Boolean(), 'false'),
        ('overdue_days', sa.Integer(), '0'),
        ('overdue_milestone', sa.String(50), None),
        ('current_stage_started_at', sa.DateTime(), None),
        ('last_stage_change_at', sa.DateTime(), None),
        ('factory_test_report_url', sa.String(500), None),
        ('factory_test_signed_at', sa.DateTime(), None),
        ('fat_completed', sa.Boolean(), 'false'),
        ('fat_completed_at', sa.DateTime(), None),
        ('fat_completed_by', sa.String(100), None),
    ]

    for col_name, col_type, default in columns_to_add:
        if col_name not in existing_columns:
            if default:
                op.add_column('purchase_orders', sa.Column(col_name, col_type, server_default=default, nullable=True))
            else:
                op.add_column('purchase_orders', sa.Column(col_name, col_type, nullable=True))
            print(f"  ✓ 添加字段 {col_name}")

    # 特殊处理带外键的字段
    if 'last_stage_change_by_id' not in existing_columns:
        op.add_column('purchase_orders', sa.Column('last_stage_change_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
        print("  ✓ 添加字段 last_stage_change_by_id")

    # ========== 创建 purchase_order_stage_history 表 ==========
    if 'purchase_order_stage_history' not in existing_tables:
        op.create_table(
            'purchase_order_stage_history',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('order_id', sa.Integer(), sa.ForeignKey('purchase_orders.id'), nullable=False),
            sa.Column('from_stage', sa.String(30), nullable=True),
            sa.Column('to_stage', sa.String(30), nullable=False),
            sa.Column('from_progress', sa.Integer(), nullable=True),
            sa.Column('to_progress', sa.Integer(), nullable=False),
            sa.Column('changed_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('changed_by_external_name', sa.String(100), nullable=True),
            sa.Column('changed_by_external_token', sa.String(64), nullable=True),
            sa.Column('change_type', sa.String(30), nullable=False),
            sa.Column('change_reason', sa.Text(), nullable=True),
            sa.Column('change_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('ix_po_stage_history_order_id', 'purchase_order_stage_history', ['order_id'])
        print("  ✓ 创建表 purchase_order_stage_history")
    else:
        print("  - 表 purchase_order_stage_history 已存在，跳过")

    # ========== 创建 purchase_order_delivery_changes 表 ==========
    if 'purchase_order_delivery_changes' not in existing_tables:
        op.create_table(
            'purchase_order_delivery_changes',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('order_id', sa.Integer(), sa.ForeignKey('purchase_orders.id'), nullable=False),
            sa.Column('field_name', sa.String(50), nullable=False),
            sa.Column('old_value', sa.String(100), nullable=True),
            sa.Column('new_value', sa.String(100), nullable=False),
            sa.Column('change_reason', sa.Text(), nullable=True),
            sa.Column('changed_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('ix_po_delivery_changes_order_id', 'purchase_order_delivery_changes', ['order_id'])
        print("  ✓ 创建表 purchase_order_delivery_changes")
    else:
        print("  - 表 purchase_order_delivery_changes 已存在，跳过")


def downgrade():
    # 删除新表
    op.drop_index('ix_po_delivery_changes_order_id', table_name='purchase_order_delivery_changes')
    op.drop_table('purchase_order_delivery_changes')

    op.drop_index('ix_po_stage_history_order_id', table_name='purchase_order_stage_history')
    op.drop_table('purchase_order_stage_history')

    # 删除 PurchaseOrder 新增字段
    op.drop_column('purchase_orders', 'fat_completed_by')
    op.drop_column('purchase_orders', 'fat_completed_at')
    op.drop_column('purchase_orders', 'fat_completed')
    op.drop_column('purchase_orders', 'factory_test_signed_at')
    op.drop_column('purchase_orders', 'factory_test_report_url')
    op.drop_column('purchase_orders', 'last_stage_change_by_id')
    op.drop_column('purchase_orders', 'last_stage_change_at')
    op.drop_column('purchase_orders', 'current_stage_started_at')
    op.drop_column('purchase_orders', 'overdue_milestone')
    op.drop_column('purchase_orders', 'overdue_days')
    op.drop_column('purchase_orders', 'is_overdue')
    op.drop_column('purchase_orders', 'delivery_schedule_locked_at')
    op.drop_column('purchase_orders', 'delivery_schedule_locked')
    op.drop_column('purchase_orders', 'milestone_ship_date')
    op.drop_column('purchase_orders', 'milestone_test_complete_date')
