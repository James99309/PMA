"""add development_purpose to dev_products

Revision ID: add_development_purpose_20251124
Create Date: 2025-11-24

添加 development_purpose 字段到 dev_products 表
用于记录研发产品的研发用途说明
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # 添加 development_purpose 字段
    op.add_column('dev_products',
        sa.Column('development_purpose', sa.Text(), nullable=True))
    print('✅ 成功添加 development_purpose 字段到 dev_products 表')


def downgrade():
    # 回滚：删除 development_purpose 字段
    op.drop_column('dev_products', 'development_purpose')
    print('✅ 成功删除 development_purpose 字段从 dev_products 表')
