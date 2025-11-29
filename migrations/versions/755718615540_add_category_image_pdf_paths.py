"""add category image_path and pdf_path fields

Revision ID: 755718615540
Revises: None
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '755718615540'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """为product_categories表添加共享图片和PDF路径字段"""
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('product_categories')]

    if 'image_path' not in columns:
        op.add_column('product_categories', sa.Column('image_path', sa.String(500), nullable=True))

    if 'pdf_path' not in columns:
        op.add_column('product_categories', sa.Column('pdf_path', sa.String(500), nullable=True))


def downgrade():
    """移除添加的字段"""
    op.drop_column('product_categories', 'pdf_path')
    op.drop_column('product_categories', 'image_path')
