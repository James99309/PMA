"""Add invoice_images field to expense_details table

Revision ID: add_expense_invoice_images
Revises: 
Create Date: 2025-08-03 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_expense_invoice_images'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add invoice_images field to expense_details table"""
    try:
        # 添加发票图片字段
        op.add_column('expense_details', 
                     sa.Column('invoice_images', sa.Text(), nullable=True))
        
        print("成功添加 invoice_images 字段到 expense_details 表")
        
    except Exception as e:
        print(f"迁移执行失败: {str(e)}")
        raise

def downgrade():
    """Remove invoice_images field from expense_details table"""
    try:
        # 删除发票图片字段
        op.drop_column('expense_details', 'invoice_images')
        
        print("成功删除 invoice_images 字段")
        
    except Exception as e:
        print(f"回滚失败: {str(e)}")
        raise