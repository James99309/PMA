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
    
    # 添加本地新增的性能索引（来自592b90d54921迁移）
    # 这些索引在本地存在但云端可能缺失
    
    # 1. 报价单性能索引
    try:
        op.create_index('idx_quotations_project_id', 'quotations', ['project_id'])
    except Exception:
        pass  # 索引可能已存在
    
    try:
        op.create_index('idx_quotations_owner_id', 'quotations', ['owner_id'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_quotations_created_at', 'quotations', ['created_at'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_quotations_updated_at', 'quotations', ['updated_at'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_quotations_amount', 'quotations', ['amount'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_quotations_project_owner', 'quotations', ['project_id', 'owner_id'])
    except Exception:
        pass
    
    # 2. 项目性能索引
    try:
        op.create_index('idx_projects_project_type', 'projects', ['project_type'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_projects_current_stage', 'projects', ['current_stage'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_projects_type_stage', 'projects', ['project_type', 'current_stage'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_projects_owner_id', 'projects', ['owner_id'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_projects_vendor_sales_manager', 'projects', ['vendor_sales_manager_id'])
    except Exception:
        pass


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