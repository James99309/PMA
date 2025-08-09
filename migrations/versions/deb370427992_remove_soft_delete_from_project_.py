
"""Remove soft delete from project customer associations

Revision ID: deb370427992
Revises: f796b05bea2d
Create Date: 2025-08-09 10:06:24.651203

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'deb370427992'
down_revision = 'f796b05bea2d'
branch_labels = None
depends_on = None


def upgrade():
    """
    移除项目客户关联表的软删除机制
    1. 删除所有已标记为deleted的记录
    2. 删除部分唯一索引
    3. 创建标准唯一约束
    4. 删除is_deleted字段
    """
    # 删除所有已标记为deleted的记录
    op.execute("DELETE FROM project_customer_associations WHERE is_deleted = true")
    
    # 删除部分唯一索引
    op.drop_index('unique_project_company_type_active', table_name='project_customer_associations')
    
    # 创建标准唯一约束
    op.create_unique_constraint('unique_project_company_type', 'project_customer_associations', ['project_id', 'company_id', 'customer_type'])
    
    # 删除is_deleted字段
    op.drop_column('project_customer_associations', 'is_deleted')


def downgrade():
    """
    恢复软删除机制
    """
    # 添加is_deleted字段
    op.add_column('project_customer_associations', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    
    # 删除标准唯一约束
    op.drop_constraint('unique_project_company_type', 'project_customer_associations', type_='unique')
    
    # 创建部分唯一索引
    op.execute('''
        CREATE UNIQUE INDEX unique_project_company_type_active 
        ON project_customer_associations (project_id, company_id, customer_type) 
        WHERE is_deleted = false
    ''')