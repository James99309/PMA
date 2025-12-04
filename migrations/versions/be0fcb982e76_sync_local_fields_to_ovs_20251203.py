"""sync_local_fields_to_ovs_20251203

同步本地数据库新字段到 OVS 云端

新增字段：
1. approval_record.status - 审批记录状态
2. product_code_field_options.allow_quotation_config - 允许报价配置
3. product_code_field_options.price_adjustment - 价格调整
4. product_code_field_options.spec_option_id - 规格选项ID
5. product_code_field_options.subcategory_id - 子分类ID
6. product_code_fields.allow_quotation_config - 允许报价配置
7. product_subcategories.image_path - 图片路径
8. product_subcategories.pdf_path - PDF路径
9. quotation_details.configured_mn - 配置MN编码
10. quotation_details.configured_specs - 配置规格快照
11. quotation_details.pending_product_creation - 待创建产品标记
12. quotation_details.price_adjustment_total - 价格调整总额
13. settlement_orders.currency - 货币类型

Revision ID: be0fcb982e76
Revises: cf11c32dccab
Create Date: 2025-12-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'be0fcb982e76'
down_revision = 'cf11c32dccab'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """检查字段是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def safe_add_column(table, column_name, column_type):
    """安全添加字段，如果已存在则跳过"""
    if column_exists(table, column_name):
        print(f"⚠ {table}.{column_name} 字段已存在，跳过")
        return

    op.add_column(table, column_type)
    print(f"✓ 添加 {table}.{column_name} 字段成功")


def upgrade():
    # 1. approval_record 添加 status 字段
    safe_add_column('approval_record', 'status',
        sa.Column('status', sa.String(20), nullable=True))

    # 2. product_code_field_options 添加字段
    safe_add_column('product_code_field_options', 'allow_quotation_config',
        sa.Column('allow_quotation_config', sa.Boolean(), nullable=True, server_default='false'))
    safe_add_column('product_code_field_options', 'price_adjustment',
        sa.Column('price_adjustment', sa.Integer(), nullable=True, server_default='0'))
    safe_add_column('product_code_field_options', 'spec_option_id',
        sa.Column('spec_option_id', sa.Integer(), nullable=True))
    safe_add_column('product_code_field_options', 'subcategory_id',
        sa.Column('subcategory_id', sa.Integer(), nullable=True))

    # 3. product_code_fields 添加字段
    safe_add_column('product_code_fields', 'allow_quotation_config',
        sa.Column('allow_quotation_config', sa.Boolean(), nullable=True, server_default='false'))

    # 4. product_subcategories 添加字段
    safe_add_column('product_subcategories', 'image_path',
        sa.Column('image_path', sa.String(500), nullable=True))
    safe_add_column('product_subcategories', 'pdf_path',
        sa.Column('pdf_path', sa.String(500), nullable=True))

    # 5. quotation_details 添加字段
    safe_add_column('quotation_details', 'configured_mn',
        sa.Column('configured_mn', sa.String(50), nullable=True))
    safe_add_column('quotation_details', 'configured_specs',
        sa.Column('configured_specs', sa.JSON(), nullable=True))
    safe_add_column('quotation_details', 'pending_product_creation',
        sa.Column('pending_product_creation', sa.Boolean(), nullable=True, server_default='false'))
    safe_add_column('quotation_details', 'price_adjustment_total',
        sa.Column('price_adjustment_total', sa.Integer(), nullable=True, server_default='0'))

    # 6. settlement_orders 添加字段
    safe_add_column('settlement_orders', 'currency',
        sa.Column('currency', sa.String(10), nullable=True, server_default="'CNY'"))


def downgrade():
    # 按添加的逆序删除字段
    columns_to_drop = [
        ('settlement_orders', 'currency'),
        ('quotation_details', 'price_adjustment_total'),
        ('quotation_details', 'pending_product_creation'),
        ('quotation_details', 'configured_specs'),
        ('quotation_details', 'configured_mn'),
        ('product_subcategories', 'pdf_path'),
        ('product_subcategories', 'image_path'),
        ('product_code_fields', 'allow_quotation_config'),
        ('product_code_field_options', 'subcategory_id'),
        ('product_code_field_options', 'spec_option_id'),
        ('product_code_field_options', 'price_adjustment'),
        ('product_code_field_options', 'allow_quotation_config'),
        ('approval_record', 'status'),
    ]

    for table, column in columns_to_drop:
        if column_exists(table, column):
            op.drop_column(table, column)
            print(f"✓ 删除 {table}.{column} 字段成功")
        else:
            print(f"⚠ {table}.{column} 不存在，跳过")
