"""添加产品MN锁定字段

Revision ID: add_product_mn_locked
Revises: 20251026_product_spec_base
Create Date: 2025-10-26 16:30:00.000000

说明：
- 为products表添加is_mn_locked字段，用于控制产品MN编码是否可编辑
- 将所有现有产品的MN设置为锁定状态（保护已有产品）
- 新创建的产品默认不锁定，可编辑MN
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_product_mn_locked'
down_revision = '20251026_product_spec_base'
branch_labels = None
depends_on = None


def upgrade():
    """添加MN锁定字段"""
    # 为products表添加is_mn_locked字段
    # 默认值为False（新产品不锁定）
    op.add_column('products', sa.Column('is_mn_locked', sa.Boolean(), nullable=True, server_default='0'))

    # 将所有现有产品的MN设置为锁定状态（保护已有产品）
    # 这样可以防止意外修改已有产品的MN编码
    op.execute("UPDATE products SET is_mn_locked = TRUE")

    print("✅ 已为products表添加is_mn_locked字段")
    print("✅ 已将所有现有产品的MN编码设置为锁定状态")


def downgrade():
    """移除MN锁定字段"""
    op.drop_column('products', 'is_mn_locked')
    print("✅ 已移除products表的is_mn_locked字段")
