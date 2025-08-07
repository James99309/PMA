"""添加通用共享字段并修改客户共享默认行为

Revision ID: add_sharing_support_20250807
Revises: 13ba9dc7b8d8
Create Date: 2025-08-07 07:59:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_sharing_support_20250807'
down_revision = '13ba9dc7b8d8'
branch_labels = None
depends_on = None

def upgrade():
    """升级数据库结构"""
    
    # 获取数据库连接检查字段是否存在
    conn = op.get_bind()
    
    # 1. 为项目表添加共享字段（如果不存在）
    # 检查 shared_with_users 字段是否存在
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'projects' AND column_name = 'shared_with_users'
    """))
    if not result.fetchone():
        op.add_column('projects', sa.Column('shared_with_users', postgresql.JSONB(), nullable=True, default='[]'))
    
    # 检查 projects.share_enabled 字段是否存在
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'projects' AND column_name = 'share_enabled'
    """))
    if not result.fetchone():
        # 先添加可为空的字段
        op.add_column('projects', sa.Column('share_enabled', sa.Boolean(), nullable=True, default=False))
        # 更新所有NULL值为False
        op.execute("UPDATE projects SET share_enabled = false WHERE share_enabled IS NULL")
        # 然后修改为NOT NULL
        op.alter_column('projects', 'share_enabled',
                       existing_type=sa.Boolean(),
                       nullable=False)
    
    # 2. 为公司表添加共享使能字段（如果不存在）
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'share_enabled'
    """))
    if not result.fetchone():
        # 先添加可为空的字段
        op.add_column('companies', sa.Column('share_enabled', sa.Boolean(), nullable=True, default=False))
        # 更新所有NULL值为False
        op.execute("UPDATE companies SET share_enabled = false WHERE share_enabled IS NULL")
        # 然后修改为NOT NULL
        op.alter_column('companies', 'share_enabled',
                       existing_type=sa.Boolean(),
                       nullable=False)
    
    # 3. 修改客户表的默认共享行为
    # 将现有的 share_related_projects 字段默认值改为 False
    op.alter_column('companies', 'share_related_projects',
                   existing_type=sa.Boolean(),
                   nullable=False,
                   default=False)
    
    # 3. 数据迁移：将现有项目的共享设置初始化
    op.execute("""
        UPDATE projects 
        SET shared_with_users = '[]', share_enabled = false 
        WHERE shared_with_users IS NULL
    """)
    
    # 4. 关闭所有客户的项目自动共享（解决权限异常问题）
    op.execute("""
        UPDATE companies 
        SET share_related_projects = false 
        WHERE share_related_projects = true
    """)
    
    print("✅ 共享字段迁移完成：")
    print("  - 项目表添加了 shared_with_users 和 share_enabled 字段") 
    print("  - 公司表添加了 share_enabled 字段")
    print("  - 修改了客户表的默认共享行为")
    print("  - 关闭了所有客户的项目自动共享功能")

def downgrade():
    """降级数据库结构"""
    
    # 恢复客户表默认值
    op.alter_column('companies', 'share_related_projects',
                   existing_type=sa.Boolean(),
                   nullable=True,
                   default=True)
    
    # 删除公司表的共享使能字段
    op.drop_column('companies', 'share_enabled')
    
    # 删除项目表的共享字段
    op.drop_column('projects', 'share_enabled')
    op.drop_column('projects', 'shared_with_users')
    
    print("⚠️  降级完成：已移除通用共享字段")