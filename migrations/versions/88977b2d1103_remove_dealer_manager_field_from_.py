"""remove_dealer_manager_field_from_projects

Revision ID: 88977b2d1103
Revises: 2dd8f9f53975
Create Date: 2025-05-25 15:48:40.488054

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88977b2d1103'
down_revision = '2dd8f9f53975'
branch_labels = None
depends_on = None


def upgrade():
    # 删除代理商负责人字段相关的外键约束和字段
    with op.batch_alter_table('projects', schema=None) as batch_op:
        # 首先删除外键约束（如果存在）
        try:
            batch_op.drop_constraint('projects_dealer_manager_id_fkey', type_='foreignkey')
        except:
            # 如果约束不存在，忽略错误
            pass
        
        # 删除dealer_manager_id字段
        batch_op.drop_column('dealer_manager_id')


def downgrade():
    # 恢复代理商负责人字段
    with op.batch_alter_table('projects', schema=None) as batch_op:
        # 添加dealer_manager_id字段
        batch_op.add_column(sa.Column('dealer_manager_id', sa.INTEGER(), nullable=True))
        
        # 重新创建外键约束
        batch_op.create_foreign_key('projects_dealer_manager_id_fkey', 'users', ['dealer_manager_id'], ['id'])