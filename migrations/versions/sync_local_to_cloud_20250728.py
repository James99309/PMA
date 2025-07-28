"""同步本地数据库结构到云端

Revision ID: sync_local_to_cloud_20250728
Revises: c8d3eaeaf234
Create Date: 2025-07-28 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'sync_local_to_cloud_20250728'
down_revision = 'c8d3eaeaf234'
branch_labels = None
depends_on = None


def upgrade():
    """将本地最新结构同步到云端"""
    
    # 使用原生SQL执行索引创建，避免Alembic事务问题
    connection = op.get_bind()
    
    # 定义要创建的索引列表
    indexes = [
        # 报价单性能索引
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_project_id ON quotations(project_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_owner_id ON quotations(owner_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_created_at ON quotations(created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_updated_at ON quotations(updated_at)", 
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_amount ON quotations(amount)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_project_owner ON quotations(project_id, owner_id)",
        
        # 项目性能索引
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_type ON projects(project_type)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_current_stage ON projects(current_stage)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_type_stage ON projects(project_type, current_stage)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_owner_id ON projects(owner_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_vendor_sales_manager ON projects(vendor_sales_manager_id)"
    ]
    
    # 设置autocommit模式以支持CONCURRENTLY
    connection.execution_options(autocommit=True)
    
    for index_sql in indexes:
        try:
            connection.execute(sa.text(index_sql))
            print(f"✅ 索引创建成功: {index_sql.split()[-1]}")
        except Exception as e:
            print(f"⚠️ 索引可能已存在或创建失败: {str(e)[:100]}")
            continue


def downgrade():
    """回滚同步的变更"""
    
    # 移除添加的索引
    try:
        op.drop_index('idx_quotations_project_id', 'quotations')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_quotations_owner_id', 'quotations')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_quotations_created_at', 'quotations')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_quotations_updated_at', 'quotations')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_quotations_amount', 'quotations')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_quotations_project_owner', 'quotations')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_projects_project_type', 'projects')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_projects_current_stage', 'projects')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_projects_type_stage', 'projects')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_projects_owner_id', 'projects')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_projects_vendor_sales_manager', 'projects')
    except Exception:
        pass