"""Add order module tables: product_tests, sales_orders, shipments, product_serial_numbers

Revision ID: add_order_module_tables_20260110
Revises: add_worklog_reactions_20260110
Create Date: 2026-01-10 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_order_module_tables_20260110'
down_revision = 'add_worklog_reactions_20260110'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 扩展 purchase_orders 表（仅添加新字段）
    # 检查字段是否存在，不存在则添加
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('purchase_orders')]

    new_columns = [
        ('revision', sa.String(20)),
        ('incoterms', sa.String(20)),
        ('order_category', sa.String(20)),
        ('supplier_confirmed', sa.Boolean()),
        ('supplier_confirmed_date', sa.DateTime()),
        ('supplier_confirmed_by', sa.String(100)),
        ('required_date', sa.DateTime()),
        ('confirmed_date', sa.DateTime()),
        ('ship_to', sa.Text()),
        ('shipping_method', sa.String(50)),
        ('freight_terms', sa.String(20)),
        ('verification_test_type', sa.String(20)),
        ('factory_test_status', sa.String(20)),
        ('verification_test_status', sa.String(20)),
        ('project_id', sa.Integer()),
        ('sales_order_id', sa.Integer()),
        ('production_status', sa.String(20)),
        ('production_progress', sa.Integer()),
        ('production_notes', sa.Text()),
        ('estimated_completion_date', sa.DateTime()),
        ('carrier', sa.String(100)),
        ('tracking_number', sa.String(100)),
        ('ship_date', sa.DateTime()),
        ('arrival_date', sa.DateTime()),
        ('actual_arrival_date', sa.DateTime()),
        ('acceptance_status', sa.String(20)),
        ('acceptance_date', sa.DateTime()),
        ('acceptance_by_id', sa.Integer()),
        ('acceptance_notes', sa.Text()),
        ('acceptance_documents', sa.Text()),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            op.add_column('purchase_orders', sa.Column(col_name, col_type, nullable=True))

    # 添加外键（如果不存在）
    if 'project_id' not in existing_columns:
        op.create_foreign_key('fk_purchase_orders_project_id', 'purchase_orders', 'projects', ['project_id'], ['id'])
    if 'acceptance_by_id' not in existing_columns:
        op.create_foreign_key('fk_purchase_orders_acceptance_by_id', 'purchase_orders', 'users', ['acceptance_by_id'], ['id'])

    # 2. 创建 product_tests 表
    if 'product_tests' not in inspector.get_table_names():
        op.create_table('product_tests',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('purchase_order_id', sa.Integer(), sa.ForeignKey('purchase_orders.id'), nullable=False),
            sa.Column('purchase_detail_id', sa.Integer(), sa.ForeignKey('purchase_order_details.id'), nullable=True),
            sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=True),
            sa.Column('serial_number_id', sa.Integer(), nullable=True),
            sa.Column('test_category', sa.String(20), nullable=False),
            sa.Column('test_type', sa.String(20), nullable=False),
            sa.Column('test_items', sa.Text(), nullable=True),
            sa.Column('test_date', sa.DateTime(), nullable=True),
            sa.Column('test_location', sa.String(200), nullable=True),
            sa.Column('tester_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('supplier_tester', sa.String(100), nullable=True),
            sa.Column('result', sa.String(20), server_default='pending'),
            sa.Column('issues', sa.Text(), nullable=True),
            sa.Column('resolution', sa.Text(), nullable=True),
            sa.Column('documents', sa.Text(), nullable=True),
            sa.Column('report_file', sa.String(500), nullable=True),
            sa.Column('reviewed', sa.Boolean(), server_default='false'),
            sa.Column('reviewed_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('review_notes', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('idx_product_tests_purchase_order', 'product_tests', ['purchase_order_id'])
        op.create_index('idx_product_tests_test_type', 'product_tests', ['test_category', 'test_type'])

    # 3. 创建 sales_orders 表
    if 'sales_orders' not in inspector.get_table_names():
        op.create_table('sales_orders',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('order_number', sa.String(50), unique=True, nullable=False),
            sa.Column('pricing_order_id', sa.Integer(), sa.ForeignKey('pricing_orders.id'), nullable=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=True),
            sa.Column('customer_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
            sa.Column('delivery_date', sa.DateTime(), nullable=True),
            sa.Column('delivery_address', sa.Text(), nullable=True),
            sa.Column('delivery_contact', sa.String(100), nullable=True),
            sa.Column('delivery_phone', sa.String(50), nullable=True),
            sa.Column('delivery_email', sa.String(100), nullable=True),
            sa.Column('shipping_method', sa.String(50), nullable=True),
            sa.Column('freight_terms', sa.String(20), nullable=True),
            sa.Column('incoterms', sa.String(20), nullable=True),
            sa.Column('carrier', sa.String(100), nullable=True),
            sa.Column('tracking_number', sa.String(100), nullable=True),
            sa.Column('ship_date', sa.DateTime(), nullable=True),
            sa.Column('arrival_date', sa.DateTime(), nullable=True),
            sa.Column('actual_arrival_date', sa.DateTime(), nullable=True),
            sa.Column('received_by', sa.String(100), nullable=True),
            sa.Column('received_date', sa.DateTime(), nullable=True),
            sa.Column('received_documents', sa.Text(), nullable=True),
            sa.Column('total_amount', sa.Numeric(15, 2), server_default='0'),
            sa.Column('total_quantity', sa.Integer(), server_default='0'),
            sa.Column('currency', sa.String(10), server_default='CNY'),
            sa.Column('status', sa.String(20), server_default='draft'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('idx_sales_orders_customer', 'sales_orders', ['customer_id'])
        op.create_index('idx_sales_orders_status', 'sales_orders', ['status'])
        op.create_index('idx_sales_orders_order_number', 'sales_orders', ['order_number'])

    # 4. 创建 sales_order_details 表
    if 'sales_order_details' not in inspector.get_table_names():
        op.create_table('sales_order_details',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('sales_order_id', sa.Integer(), sa.ForeignKey('sales_orders.id'), nullable=False),
            sa.Column('pricing_detail_id', sa.Integer(), sa.ForeignKey('pricing_order_details.id'), nullable=True),
            sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
            sa.Column('product_name', sa.String(200), nullable=False),
            sa.Column('product_model', sa.String(100), nullable=True),
            sa.Column('specification', sa.Text(), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=False),
            sa.Column('unit', sa.String(20), nullable=True),
            sa.Column('unit_price', sa.Numeric(15, 2), server_default='0'),
            sa.Column('discount', sa.Numeric(5, 4), server_default='1.0000'),
            sa.Column('total_price', sa.Numeric(15, 2), server_default='0'),
            sa.Column('shipped_quantity', sa.Integer(), server_default='0'),
            sa.Column('received_quantity', sa.Integer(), server_default='0'),
            sa.Column('status', sa.String(20), server_default='pending'),
            sa.Column('notes', sa.Text(), nullable=True),
        )
        op.create_index('idx_sales_order_details_order', 'sales_order_details', ['sales_order_id'])

    # 5. 创建 shipments 表
    if 'shipments' not in inspector.get_table_names():
        op.create_table('shipments',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('shipment_number', sa.String(50), unique=True, nullable=False),
            sa.Column('sales_order_id', sa.Integer(), sa.ForeignKey('sales_orders.id'), nullable=False),
            sa.Column('carrier', sa.String(100), nullable=True),
            sa.Column('tracking_number', sa.String(100), nullable=True),
            sa.Column('shipping_method', sa.String(50), nullable=True),
            sa.Column('ship_date', sa.DateTime(), nullable=True),
            sa.Column('expected_arrival', sa.DateTime(), nullable=True),
            sa.Column('actual_arrival', sa.DateTime(), nullable=True),
            sa.Column('freight_cost', sa.Numeric(15, 2), nullable=True),
            sa.Column('freight_payer', sa.String(20), nullable=True),
            sa.Column('currency', sa.String(10), server_default='CNY'),
            sa.Column('ship_from', sa.Text(), nullable=True),
            sa.Column('ship_from_contact', sa.String(100), nullable=True),
            sa.Column('ship_from_phone', sa.String(50), nullable=True),
            sa.Column('ship_to', sa.Text(), nullable=True),
            sa.Column('contact_name', sa.String(100), nullable=True),
            sa.Column('contact_phone', sa.String(50), nullable=True),
            sa.Column('contact_email', sa.String(100), nullable=True),
            sa.Column('total_packages', sa.Integer(), server_default='1'),
            sa.Column('total_weight', sa.Numeric(10, 2), nullable=True),
            sa.Column('total_volume', sa.Numeric(10, 4), nullable=True),
            sa.Column('package_description', sa.Text(), nullable=True),
            sa.Column('documents', sa.Text(), nullable=True),
            sa.Column('delivery_proof', sa.Text(), nullable=True),
            sa.Column('received_by', sa.String(100), nullable=True),
            sa.Column('received_date', sa.DateTime(), nullable=True),
            sa.Column('received_notes', sa.Text(), nullable=True),
            sa.Column('status', sa.String(20), server_default='pending'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('idx_shipments_sales_order', 'shipments', ['sales_order_id'])
        op.create_index('idx_shipments_status', 'shipments', ['status'])

    # 6. 创建 shipment_details 表
    if 'shipment_details' not in inspector.get_table_names():
        op.create_table('shipment_details',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('shipment_id', sa.Integer(), sa.ForeignKey('shipments.id'), nullable=False),
            sa.Column('sales_order_detail_id', sa.Integer(), sa.ForeignKey('sales_order_details.id'), nullable=True),
            sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
            sa.Column('product_name', sa.String(200), nullable=False),
            sa.Column('product_model', sa.String(100), nullable=True),
            sa.Column('specification', sa.Text(), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=False),
            sa.Column('unit', sa.String(20), nullable=True),
            sa.Column('serial_numbers', sa.Text(), nullable=True),
            sa.Column('received_quantity', sa.Integer(), server_default='0'),
            sa.Column('status', sa.String(20), server_default='pending'),
            sa.Column('notes', sa.Text(), nullable=True),
        )
        op.create_index('idx_shipment_details_shipment', 'shipment_details', ['shipment_id'])

    # 7. 创建 product_serial_numbers 表
    if 'product_serial_numbers' not in inspector.get_table_names():
        op.create_table('product_serial_numbers',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('serial_number', sa.String(100), unique=True, nullable=False),
            sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
            sa.Column('purchase_order_id', sa.Integer(), sa.ForeignKey('purchase_orders.id'), nullable=True),
            sa.Column('purchase_detail_id', sa.Integer(), sa.ForeignKey('purchase_order_details.id'), nullable=True),
            sa.Column('batch_number', sa.String(100), nullable=True),
            sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
            sa.Column('warehouse_in_date', sa.DateTime(), nullable=True),
            sa.Column('warehouse_location', sa.String(100), nullable=True),
            sa.Column('inventory_id', sa.Integer(), sa.ForeignKey('inventory.id'), nullable=True),
            sa.Column('received_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('sales_order_id', sa.Integer(), sa.ForeignKey('sales_orders.id'), nullable=True),
            sa.Column('shipment_id', sa.Integer(), sa.ForeignKey('shipments.id'), nullable=True),
            sa.Column('ship_out_date', sa.DateTime(), nullable=True),
            sa.Column('destination', sa.String(200), nullable=True),
            sa.Column('shipped_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('customer_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=True),
            sa.Column('status', sa.String(20), server_default='registered'),
            sa.Column('test_passed', sa.Boolean(), nullable=True),
            sa.Column('test_date', sa.DateTime(), nullable=True),
            sa.Column('test_id', sa.Integer(), sa.ForeignKey('product_tests.id'), nullable=True),
            sa.Column('warranty_start_date', sa.DateTime(), nullable=True),
            sa.Column('warranty_end_date', sa.DateTime(), nullable=True),
            sa.Column('warranty_notes', sa.Text(), nullable=True),
            sa.Column('manufacture_date', sa.DateTime(), nullable=True),
            sa.Column('hardware_version', sa.String(50), nullable=True),
            sa.Column('firmware_version', sa.String(50), nullable=True),
            sa.Column('mac_address', sa.String(50), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('idx_serial_numbers_product', 'product_serial_numbers', ['product_id'])
        op.create_index('idx_serial_numbers_status', 'product_serial_numbers', ['status'])
        op.create_index('idx_serial_numbers_sn', 'product_serial_numbers', ['serial_number'])

    # 8. 创建 serial_number_histories 表
    if 'serial_number_histories' not in inspector.get_table_names():
        op.create_table('serial_number_histories',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('serial_number_id', sa.Integer(), sa.ForeignKey('product_serial_numbers.id'), nullable=False),
            sa.Column('action', sa.String(50), nullable=False),
            sa.Column('status_before', sa.String(20), nullable=True),
            sa.Column('status_after', sa.String(20), nullable=False),
            sa.Column('reference_type', sa.String(50), nullable=True),
            sa.Column('reference_id', sa.Integer(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('location', sa.String(100), nullable=True),
            sa.Column('operated_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('operated_at', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('idx_sn_history_serial_number', 'serial_number_histories', ['serial_number_id'])
        op.create_index('idx_sn_history_action', 'serial_number_histories', ['action'])


def downgrade():
    # 按创建的反序删除表
    op.drop_table('serial_number_histories')
    op.drop_table('product_serial_numbers')
    op.drop_table('shipment_details')
    op.drop_table('shipments')
    op.drop_table('sales_order_details')
    op.drop_table('sales_orders')
    op.drop_table('product_tests')

    # 删除 purchase_orders 表的新增字段
    columns_to_drop = [
        'revision', 'incoterms', 'order_category',
        'supplier_confirmed', 'supplier_confirmed_date', 'supplier_confirmed_by',
        'required_date', 'confirmed_date', 'ship_to', 'shipping_method', 'freight_terms',
        'verification_test_type', 'factory_test_status', 'verification_test_status',
        'project_id', 'sales_order_id',
        'production_status', 'production_progress', 'production_notes', 'estimated_completion_date',
        'carrier', 'tracking_number', 'ship_date', 'arrival_date', 'actual_arrival_date',
        'acceptance_status', 'acceptance_date', 'acceptance_by_id', 'acceptance_notes', 'acceptance_documents',
    ]

    op.drop_constraint('fk_purchase_orders_project_id', 'purchase_orders', type_='foreignkey')
    op.drop_constraint('fk_purchase_orders_acceptance_by_id', 'purchase_orders', type_='foreignkey')

    for col in columns_to_drop:
        op.drop_column('purchase_orders', col)
