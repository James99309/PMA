"""添加产品分类显示顺序字段

Revision ID: 20251115_add_category_display_order
Revises:
Create Date: 2025-11-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251115_add_category_display_order'
down_revision = '20251109_spec_dict'
branch_labels = None
depends_on = None


def upgrade():
    """添加 display_order 字段到 product_categories 表"""
    # 添加字段
    op.add_column('product_categories',
                  sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'))

    # 为现有记录初始化 display_order = id（保持当前顺序）
    op.execute('UPDATE product_categories SET display_order = id WHERE display_order IS NULL OR display_order = 0')

    # 设置字段为非空（在数据初始化后）
    op.alter_column('product_categories', 'display_order', nullable=False)


def downgrade():
    """移除 display_order 字段"""
    op.drop_column('product_categories', 'display_order')
