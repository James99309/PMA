"""remove_dealer_manager_field_from_projects

Revision ID: 88977b2d1103
Revises: 2dd8f9f53975
Create Date: 2025-05-25 15:48:40.488054

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '88977b2d1103'
down_revision = '2dd8f9f53975'
branch_labels = None
depends_on = None


def upgrade():
    # 删除代理商负责人字段相关的外键约束和字段
    connection = op.get_bind()
    
    # 检查外键约束是否存在
    constraint_exists = connection.execute(text("""
        SELECT COUNT(*) 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'projects_dealer_manager_id_fkey' 
        AND table_name = 'projects'
    """)).scalar()
    
    with op.batch_alter_table('projects', schema=None) as batch_op:
        # 如果外键约束存在，则删除它
        if constraint_exists > 0:
            batch_op.drop_constraint('projects_dealer_manager_id_fkey', type_='foreignkey')
        
        # 检查字段是否存在，如果存在则删除
        column_exists = connection.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'projects' 
            AND column_name = 'dealer_manager_id'
        """)).scalar()
        
        if column_exists > 0:
            batch_op.drop_column('dealer_manager_id')


def downgrade():
    # 恢复代理商负责人字段
    connection = op.get_bind()
    
    # 检查字段是否已存在
    column_exists = connection.execute(text("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = 'projects' 
        AND column_name = 'dealer_manager_id'
    """)).scalar()
    
    with op.batch_alter_table('projects', schema=None) as batch_op:
        # 如果字段不存在，则添加它
        if column_exists == 0:
            batch_op.add_column(sa.Column('dealer_manager_id', sa.INTEGER(), nullable=True))
            
            # 重新创建外键约束
            batch_op.create_foreign_key('projects_dealer_manager_id_fkey', 'users', ['dealer_manager_id'], ['id'])