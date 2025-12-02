"""添加报价单动态规格配置相关字段

新增字段：
1. ProductCodeField.allow_quotation_config - 允许报价配置标记
2. ProductCodeFieldOption.price_adjustment - 价格增量（分）
3. QuotationDetail.configured_specs - 配置规格快照
4. QuotationDetail.configured_mn - 配置后的MN编码
5. QuotationDetail.price_adjustment_total - 总价格增量
6. QuotationDetail.pending_product_creation - 待创建产品标记

Revision ID: add_quotation_spec_config_20251201
Revises:
Create Date: 2025-12-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_quotation_spec_config_20251201'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. ProductCodeField 添加 allow_quotation_config 字段
    try:
        op.add_column('product_code_fields',
            sa.Column('allow_quotation_config', sa.Boolean(), nullable=True, server_default='false'))
        print("✓ 添加 product_code_fields.allow_quotation_config 字段成功")
    except Exception as e:
        print(f"⚠ product_code_fields.allow_quotation_config 字段可能已存在: {e}")

    # 2. ProductCodeFieldOption 添加 price_adjustment 字段
    try:
        op.add_column('product_code_field_options',
            sa.Column('price_adjustment', sa.Integer(), nullable=True, server_default='0'))
        print("✓ 添加 product_code_field_options.price_adjustment 字段成功")
    except Exception as e:
        print(f"⚠ product_code_field_options.price_adjustment 字段可能已存在: {e}")

    # 3. QuotationDetail 添加 configured_specs 字段 (JSON)
    try:
        op.add_column('quotation_details',
            sa.Column('configured_specs', sa.JSON(), nullable=True))
        print("✓ 添加 quotation_details.configured_specs 字段成功")
    except Exception as e:
        print(f"⚠ quotation_details.configured_specs 字段可能已存在: {e}")

    # 4. QuotationDetail 添加 configured_mn 字段
    try:
        op.add_column('quotation_details',
            sa.Column('configured_mn', sa.String(50), nullable=True))
        print("✓ 添加 quotation_details.configured_mn 字段成功")
    except Exception as e:
        print(f"⚠ quotation_details.configured_mn 字段可能已存在: {e}")

    # 5. QuotationDetail 添加 price_adjustment_total 字段
    try:
        op.add_column('quotation_details',
            sa.Column('price_adjustment_total', sa.Integer(), nullable=True, server_default='0'))
        print("✓ 添加 quotation_details.price_adjustment_total 字段成功")
    except Exception as e:
        print(f"⚠ quotation_details.price_adjustment_total 字段可能已存在: {e}")

    # 6. QuotationDetail 添加 pending_product_creation 字段
    try:
        op.add_column('quotation_details',
            sa.Column('pending_product_creation', sa.Boolean(), nullable=True, server_default='false'))
        print("✓ 添加 quotation_details.pending_product_creation 字段成功")
    except Exception as e:
        print(f"⚠ quotation_details.pending_product_creation 字段可能已存在: {e}")


def downgrade():
    # 按添加的逆序删除字段
    try:
        op.drop_column('quotation_details', 'pending_product_creation')
    except Exception:
        pass

    try:
        op.drop_column('quotation_details', 'price_adjustment_total')
    except Exception:
        pass

    try:
        op.drop_column('quotation_details', 'configured_mn')
    except Exception:
        pass

    try:
        op.drop_column('quotation_details', 'configured_specs')
    except Exception:
        pass

    try:
        op.drop_column('product_code_field_options', 'price_adjustment')
    except Exception:
        pass

    try:
        op.drop_column('product_code_fields', 'allow_quotation_config')
    except Exception:
        pass
