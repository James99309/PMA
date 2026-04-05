"""add quotation_details search indexes for autocomplete

Revision ID: 5ed9cf9a28eb
Revises: 4bd148e53cbe
Create Date: 2026-04-05 14:50:00.000000

为 quotation_details 表的 product_name 和 product_model 字段添加 btree 索引
用途：加速自建产品 autocomplete 的 ILIKE 模糊匹配查询

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '5ed9cf9a28eb'
down_revision = '4bd148e53cbe'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 product_name 索引（如果不存在）
    op.create_index(
        'idx_qd_product_name',
        'quotation_details',
        ['product_name'],
        unique=False,
        postgresql_using='btree',
        if_not_exists=True,
    )
    # 创建 product_model 索引（如果不存在）
    op.create_index(
        'idx_qd_product_model',
        'quotation_details',
        ['product_model'],
        unique=False,
        postgresql_using='btree',
        if_not_exists=True,
    )


def downgrade():
    op.drop_index('idx_qd_product_model', table_name='quotation_details', if_exists=True)
    op.drop_index('idx_qd_product_name', table_name='quotation_details', if_exists=True)
