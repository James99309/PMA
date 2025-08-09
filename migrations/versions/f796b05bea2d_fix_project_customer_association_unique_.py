
"""Fix project customer association unique constraint for soft delete

Revision ID: f796b05bea2d
Revises: 06dd883f89fa
Create Date: 2025-08-09 10:03:57.568616

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f796b05bea2d'
down_revision = '06dd883f89fa'
branch_labels = None
depends_on = None


def upgrade():
    """
    修复项目客户关联表的唯一约束问题
    将原有的唯一约束替换为部分唯一索引，只对未删除的记录生效
    """
    # 删除原有的唯一约束
    op.drop_constraint('unique_project_company_type', 'project_customer_associations', type_='unique')
    
    # 创建部分唯一索引，只对未删除的记录生效
    op.execute('''
        CREATE UNIQUE INDEX unique_project_company_type_active 
        ON project_customer_associations (project_id, company_id, customer_type) 
        WHERE is_deleted = false
    ''')


def downgrade():
    """
    恢复原来的唯一约束
    """
    # 删除部分唯一索引
    op.drop_index('unique_project_company_type_active', table_name='project_customer_associations')
    
    # 恢复原有的唯一约束
    op.create_unique_constraint('unique_project_company_type', 'project_customer_associations', ['project_id', 'company_id', 'customer_type'])