"""幂等基线同步迁移

此迁移确保所有表和字段存在，可安全重复执行。
用于修复因 db.create_all() 导致的迁移状态不一致问题。

所有操作都使用 IF NOT EXISTS 检查，不会破坏现有数据。

Revision ID: baseline_sync_20260112
Revises: fix_missing_linked_company_id_20260112
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'baseline_sync_20260112'
down_revision = 'fix_missing_linked_company_id_20260112'
branch_labels = None
depends_on = None


def table_exists(conn, table_name):
    """检查表是否存在"""
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(conn, table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(conn)
    if table_name not in inspector.get_table_names():
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_column_if_not_exists(conn, table_name, column):
    """安全添加列（如果不存在）"""
    if not column_exists(conn, table_name, column.name):
        op.add_column(table_name, column)
        print(f"  ✓ 添加列 {table_name}.{column.name}")
        return True
    else:
        print(f"  - {table_name}.{column.name} 已存在，跳过")
        return False


def upgrade():
    conn = op.get_bind()
    print("\n" + "=" * 60)
    print("幂等基线同步迁移 - 确保所有表和字段存在")
    print("=" * 60)

    # ========================================
    # 1. 创建可能缺失的表
    # ========================================
    print("\n[1/4] 检查并创建缺失的表...")

    # data_affiliation 表
    if not table_exists(conn, 'data_affiliation'):
        op.create_table('data_affiliation',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('owner_id', sa.Integer(), nullable=False),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('depth', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['parent_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        print("  ✓ 创建表 data_affiliation")
    else:
        print("  - data_affiliation 已存在，跳过")

    # product_test_samplings 表
    if not table_exists(conn, 'product_test_samplings'):
        op.create_table('product_test_samplings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('test_id', sa.Integer(), nullable=False),
            sa.Column('total_population', sa.Integer(), nullable=False),
            sa.Column('sample_size', sa.Integer(), nullable=False),
            sa.Column('random_seed', sa.String(100), nullable=True),
            sa.Column('sampled_at', sa.DateTime(), nullable=True),
            sa.Column('sampled_by_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['sampled_by_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['test_id'], ['product_tests.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        print("  ✓ 创建表 product_test_samplings")
    else:
        print("  - product_test_samplings 已存在，跳过")

    # ========================================
    # 2. users 表字段
    # ========================================
    print("\n[2/4] 检查 users 表字段...")
    add_column_if_not_exists(conn, 'users',
        sa.Column('linked_company_id', sa.Integer(), nullable=True))

    # ========================================
    # 3. companies 表字段
    # ========================================
    print("\n[3/4] 检查 companies 表字段...")
    add_column_if_not_exists(conn, 'companies',
        sa.Column('supplier_code', sa.String(10), nullable=True))

    # ========================================
    # 4. products 表字段
    # ========================================
    print("\n[4/4] 检查 products 表字段...")
    add_column_if_not_exists(conn, 'products',
        sa.Column('serial_code', sa.String(10), nullable=True))

    # ========================================
    # 5. projects 表字段
    # ========================================
    print("\n[5/4] 检查 projects 表字段...")
    add_column_if_not_exists(conn, 'projects',
        sa.Column('address', sa.Text(), nullable=True))
    add_column_if_not_exists(conn, 'projects',
        sa.Column('city', sa.String(100), nullable=True))
    add_column_if_not_exists(conn, 'projects',
        sa.Column('country', sa.String(100), nullable=True))
    add_column_if_not_exists(conn, 'projects',
        sa.Column('region', sa.String(100), nullable=True))

    # ========================================
    # 6. worklogs 表字段
    # ========================================
    print("\n[6/4] 检查 worklogs 表字段...")
    add_column_if_not_exists(conn, 'worklogs',
        sa.Column('quality_issues', sa.Text(), nullable=True))
    add_column_if_not_exists(conn, 'worklogs',
        sa.Column('reflection', sa.Text(), nullable=True))
    add_column_if_not_exists(conn, 'worklogs',
        sa.Column('difficulties', sa.Text(), nullable=True))
    add_column_if_not_exists(conn, 'worklogs',
        sa.Column('tomorrow_plan', sa.Text(), nullable=True))
    add_column_if_not_exists(conn, 'worklogs',
        sa.Column('is_deleted', sa.Boolean(), nullable=True))
    add_column_if_not_exists(conn, 'worklogs',
        sa.Column('quality_score', sa.Integer(), nullable=True))

    # ========================================
    # 7. work_items 表字段
    # ========================================
    print("\n[7/4] 检查 work_items 表字段...")
    add_column_if_not_exists(conn, 'work_items',
        sa.Column('priority', sa.Integer(), nullable=True))
    add_column_if_not_exists(conn, 'work_items',
        sa.Column('actual_date', sa.Date(), nullable=True))
    add_column_if_not_exists(conn, 'work_items',
        sa.Column('duration', sa.Integer(), nullable=True))
    add_column_if_not_exists(conn, 'work_items',
        sa.Column('notes', sa.Text(), nullable=True))

    # ========================================
    # 8. purchase_orders 表字段（大量字段）
    # ========================================
    print("\n[8/4] 检查 purchase_orders 表字段...")

    # 基础字段
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('project_id', sa.Integer(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('sales_order_id', sa.Integer(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('order_category', sa.String(20), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('revision', sa.String(20), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('approval_notes', sa.Text(), nullable=True))

    # 供应商确认相关
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('supplier_confirmed', sa.Boolean(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('supplier_confirmed_by', sa.String(100), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('supplier_confirmed_date', sa.DateTime(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('supplier_confirmation_notes', sa.Text(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('supplier_confirmation_file', sa.String(500), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('supplier_signature_url', sa.String(500), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('confirmed_date', sa.DateTime(), nullable=True))

    # 生产相关
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('production_status', sa.String(20), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('production_progress', sa.Integer(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('production_notes', sa.Text(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('estimated_completion_date', sa.DateTime(), nullable=True))

    # 测试相关
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('factory_test_status', sa.String(20), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('verification_test_status', sa.String(20), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('verification_test_type', sa.String(20), nullable=True))

    # 物流相关
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('ship_to', sa.Text(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('incoterms', sa.String(20), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('freight_terms', sa.String(20), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('shipping_method', sa.String(50), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('carrier', sa.String(100), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('tracking_number', sa.String(100), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('ship_date', sa.DateTime(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('arrival_date', sa.DateTime(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('actual_arrival_date', sa.DateTime(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('required_date', sa.DateTime(), nullable=True))

    # 验收相关
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('acceptance_status', sa.String(20), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('acceptance_date', sa.DateTime(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('acceptance_by_id', sa.Integer(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('acceptance_notes', sa.Text(), nullable=True))
    add_column_if_not_exists(conn, 'purchase_orders',
        sa.Column('acceptance_documents', sa.Text(), nullable=True))

    # ========================================
    # 9. 其他可能缺失的字段
    # ========================================
    print("\n[9/4] 检查其他表字段...")

    # approval_external_token 表相关
    if table_exists(conn, 'approval_external_token'):
        add_column_if_not_exists(conn, 'approval_external_token',
            sa.Column('action_taken', sa.String(20), nullable=True))
        add_column_if_not_exists(conn, 'approval_external_token',
            sa.Column('action_comment', sa.Text(), nullable=True))
        add_column_if_not_exists(conn, 'approval_external_token',
            sa.Column('action_at', sa.DateTime(), nullable=True))

    print("\n" + "=" * 60)
    print("✅ 幂等基线同步迁移完成")
    print("=" * 60 + "\n")


def downgrade():
    """
    降级操作 - 此迁移是修复性质的，降级时不做任何操作。

    原因：
    1. 这些字段可能已被其他迁移创建
    2. 删除字段可能导致数据丢失
    3. 保持向前兼容性
    """
    print("\n⚠️ baseline_sync 是修复性迁移，downgrade 不执行任何操作")
    print("如需删除字段，请创建专门的迁移文件\n")
    pass
