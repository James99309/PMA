"""add subcategory display order field

Revision ID: add_subcategory_display_order
Revises: 
Create Date: 2024-04-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_subcategory_display_order'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加display_order列
    op.add_column('product_subcategories', sa.Column('display_order', sa.Integer(), nullable=True))
    
    # 获取数据库连接
    connection = op.get_bind()
    
    # 获取所有分类
    categories = connection.execute("SELECT id FROM product_categories").fetchall()
    
    # 为每个分类下的子分类设置display_order，按照id顺序，从1开始计数
    for category in categories:
        category_id = category[0]
        subcategories = connection.execute(
            f"SELECT id FROM product_subcategories WHERE category_id = {category_id} ORDER BY id"
        ).fetchall()
        
        # 设置display_order从1开始
        for i, subcategory in enumerate(subcategories, 1):
            subcategory_id = subcategory[0]
            connection.execute(
                f"UPDATE product_subcategories SET display_order = {i} WHERE id = {subcategory_id}"
            )
    
    # 设置非空约束
    op.alter_column('product_subcategories', 'display_order', nullable=False, 
                    server_default=sa.text('0'),  # 默认值为0
                    existing_type=sa.Integer())


def downgrade():
    # 删除display_order列
    op.drop_column('product_subcategories', 'display_order') 