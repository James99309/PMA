"""add_vendor_sales_manager_id_to_projects

Revision ID: 302d37d8a408
Revises: 88977b2d1103
Create Date: 2025-05-25 16:06:50.978485

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '302d37d8a408'
down_revision = '88977b2d1103'
branch_labels = None
depends_on = None


def upgrade():
    # 添加厂商销售负责人字段
    with op.batch_alter_table('projects', schema=None) as batch_op:
        # 添加vendor_sales_manager_id字段
        batch_op.add_column(sa.Column('vendor_sales_manager_id', sa.INTEGER(), nullable=True))
        
        # 创建外键约束
        batch_op.create_foreign_key('projects_vendor_sales_manager_id_fkey', 'users', ['vendor_sales_manager_id'], ['id'])


def downgrade():
    # 删除厂商销售负责人字段
    with op.batch_alter_table('projects', schema=None) as batch_op:
        # 删除外键约束
        batch_op.drop_constraint('projects_vendor_sales_manager_id_fkey', type_='foreignkey')
        
        # 删除vendor_sales_manager_id字段
        batch_op.drop_column('vendor_sales_manager_id') 