"""
添加产品厂商标记字段

Revision ID: add_vendor_product_field
Revises: 
Create Date: 2025-01-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_vendor_product_field'
down_revision = None
depends_on = None

def upgrade():
    """添加is_vendor_product字段到products表"""
    # 添加厂商产品标记字段
    op.add_column('products', sa.Column('is_vendor_product', sa.Boolean(), nullable=True, default=False))
    
    # 将现有的和源通信品牌产品标记为厂商产品
    op.execute("UPDATE products SET is_vendor_product = true WHERE brand = '和源通信'")
    
    # 设置字段为非空
    op.alter_column('products', 'is_vendor_product', nullable=False, server_default=sa.false())

def downgrade():
    """移除is_vendor_product字段"""
    op.drop_column('products', 'is_vendor_product') 