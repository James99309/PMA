"""add development_purpose to dev_products

Revision ID: add_development_purpose_20251124
Revises: 20251115_add_spec_dict_display_order
Create Date: 2025-11-24

添加 development_purpose 字段到 dev_products 表
用于记录研发产品的研发用途说明
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_development_purpose_20251124'
down_revision = 'add_quantity_synced_20251122'
branch_labels = None
depends_on = None


def upgrade():
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('dev_products')]

    # 添加 development_purpose 字段
    if 'development_purpose' not in columns:
        op.add_column('dev_products',
            sa.Column('development_purpose', sa.Text(), nullable=True))
        print('✅ 成功添加 development_purpose 字段到 dev_products 表')
    else:
        print('⏭️ development_purpose 字段已存在，跳过')


def downgrade():
    # 回滚：删除 development_purpose 字段
    op.drop_column('dev_products', 'development_purpose')
    print('✅ 成功删除 development_purpose 字段从 dev_products 表')
