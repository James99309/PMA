"""add quantity_synced to quotation_details

Revision ID: add_quantity_synced_20251122
Create Date: 2025-11-22

添加 quantity_synced 字段到 quotation_details 表
用于记录配置产品是否同步主产品数量
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # 添加 quantity_synced 字段，默认值为 True（同步）
    op.add_column('quotation_details',
        sa.Column('quantity_synced', sa.Boolean(),
                  nullable=False, server_default='1'))
    print('✅ 成功添加 quantity_synced 字段到 quotation_details 表')


def downgrade():
    # 回滚：删除 quantity_synced 字段
    op.drop_column('quotation_details', 'quantity_synced')
    print('✅ 成功删除 quantity_synced 字段从 quotation_details 表')
