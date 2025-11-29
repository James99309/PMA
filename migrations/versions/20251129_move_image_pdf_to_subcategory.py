"""Move image_path and pdf_path from ProductCategory to ProductSubcategory

Revision ID: 20251129_move_subcategory
Revises: 528dc1c41c03
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251129_move_subcategory'
down_revision = '528dc1c41c03'
branch_labels = None
depends_on = None


def upgrade():
    """将共享图片和PDF路径字段从product_categories移动到product_subcategories"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 检查product_subcategories表中是否已有这些列
    subcategory_columns = [c['name'] for c in inspector.get_columns('product_subcategories')]

    if 'image_path' not in subcategory_columns:
        op.add_column('product_subcategories', sa.Column('image_path', sa.String(500), nullable=True))

    if 'pdf_path' not in subcategory_columns:
        op.add_column('product_subcategories', sa.Column('pdf_path', sa.String(500), nullable=True))

    # 检查product_categories表中是否有这些列，如果有则删除
    category_columns = [c['name'] for c in inspector.get_columns('product_categories')]

    if 'image_path' in category_columns:
        op.drop_column('product_categories', 'image_path')

    if 'pdf_path' in category_columns:
        op.drop_column('product_categories', 'pdf_path')


def downgrade():
    """回滚：将字段移回product_categories"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 检查product_categories表中是否已有这些列
    category_columns = [c['name'] for c in inspector.get_columns('product_categories')]

    if 'image_path' not in category_columns:
        op.add_column('product_categories', sa.Column('image_path', sa.String(500), nullable=True))

    if 'pdf_path' not in category_columns:
        op.add_column('product_categories', sa.Column('pdf_path', sa.String(500), nullable=True))

    # 从product_subcategories删除列
    subcategory_columns = [c['name'] for c in inspector.get_columns('product_subcategories')]

    if 'image_path' in subcategory_columns:
        op.drop_column('product_subcategories', 'image_path')

    if 'pdf_path' in subcategory_columns:
        op.drop_column('product_subcategories', 'pdf_path')
