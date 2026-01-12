"""Add product test tables for factory and FAT testing

Revision ID: add_product_test_tables_20260111
Revises:
Create Date: 2026-01-11

新增表:
- product_tests: 产品测试记录表
- product_test_details: 测试明细表(每个序列号的测试结果)
- product_test_samplings: 采样测试记录表
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_product_test_tables_20260111'
down_revision = 'add_order_module_tables_20260110'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. 创建 product_tests 表
    if 'product_tests' not in existing_tables:
        op.create_table('product_tests',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('purchase_order_id', sa.Integer(), sa.ForeignKey('purchase_orders.id'), nullable=False),
            sa.Column('approval_step_id', sa.Integer(), sa.ForeignKey('approval_steps.id'), nullable=True),

            # 测试分类
            sa.Column('test_category', sa.String(20), nullable=False),  # factory/verification
            sa.Column('test_type', sa.String(20), nullable=True),  # site_fat/incoming

            # 测试模式
            sa.Column('test_mode', sa.String(20), default='full'),  # full/sampling
            sa.Column('total_quantity', sa.Integer(), default=0),
            sa.Column('sample_quantity', sa.Integer(), nullable=True),

            # 状态和结果
            sa.Column('status', sa.String(20), default='pending'),
            sa.Column('passed_count', sa.Integer(), default=0),
            sa.Column('failed_count', sa.Integer(), default=0),

            # 测试信息
            sa.Column('test_date', sa.DateTime(), nullable=True),
            sa.Column('tester_name', sa.String(100), nullable=True),
            sa.Column('tester_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('signature_url', sa.String(500), nullable=True),

            # 元数据
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
        )

    # 2. 创建 product_test_details 表
    if 'product_test_details' not in existing_tables:
        op.create_table('product_test_details',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('test_id', sa.Integer(), sa.ForeignKey('product_tests.id'), nullable=False),
            sa.Column('serial_number_id', sa.Integer(), sa.ForeignKey('product_serial_numbers.id'), nullable=False),

            # 测试顺序
            sa.Column('sequence', sa.Integer(), default=0),

            # 测试结果
            sa.Column('result', sa.String(20), nullable=True),  # passed/failed/null
            sa.Column('report_file_url', sa.String(500), nullable=True),
            sa.Column('report_file_name', sa.String(200), nullable=True),

            # 测试详情
            sa.Column('tested_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
        )

    # 3. 创建 product_test_samplings 表
    if 'product_test_samplings' not in existing_tables:
        op.create_table('product_test_samplings',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('test_id', sa.Integer(), sa.ForeignKey('product_tests.id'), nullable=False),

            # 采样信息
            sa.Column('total_population', sa.Integer(), nullable=False),
            sa.Column('sample_size', sa.Integer(), nullable=False),
            sa.Column('random_seed', sa.String(100), nullable=True),

            # 采样时间和操作人
            sa.Column('sampled_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('sampled_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        )


def downgrade():
    op.drop_table('product_test_samplings')
    op.drop_table('product_test_details')
    op.drop_table('product_tests')
