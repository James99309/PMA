
"""优化报价单筛选性能_添加关键索引

Revision ID: 592b90d54921
Revises: 38b3e335f251
Create Date: 2025-07-12 13:46:45.429778

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '592b90d54921'
down_revision = '38b3e335f251'
branch_labels = None
depends_on = None


def upgrade():
    # 为报价单表添加关键索引以优化筛选性能
    
    # 1. 报价单项目ID索引 - 优化JOIN查询
    try:
        op.create_index('idx_quotations_project_id', 'quotations', ['project_id'])
    except Exception:
        pass  # 索引可能已存在
    
    # 2. 报价单拥有者ID索引 - 优化权限过滤
    try:
        op.create_index('idx_quotations_owner_id', 'quotations', ['owner_id'])
    except Exception:
        pass
    
    # 3. 报价单创建时间索引 - 优化排序
    try:
        op.create_index('idx_quotations_created_at', 'quotations', ['created_at'])
    except Exception:
        pass
    
    # 4. 报价单更新时间索引 - 优化排序
    try:
        op.create_index('idx_quotations_updated_at', 'quotations', ['updated_at'])
    except Exception:
        pass
    
    # 5. 报价单金额索引 - 优化金额排序
    try:
        op.create_index('idx_quotations_amount', 'quotations', ['amount'])
    except Exception:
        pass
    
    # 6. 复合索引：项目ID + 拥有者ID - 优化权限查询
    try:
        op.create_index('idx_quotations_project_owner', 'quotations', ['project_id', 'owner_id'])
    except Exception:
        pass
    
    # 7. 项目类型索引 - 优化项目类型筛选
    try:
        op.create_index('idx_projects_project_type', 'projects', ['project_type'])
    except Exception:
        pass
    
    # 8. 项目阶段索引 - 优化项目阶段筛选
    try:
        op.create_index('idx_projects_current_stage', 'projects', ['current_stage'])
    except Exception:
        pass
    
    # 9. 复合索引：项目类型 + 阶段 - 优化复合筛选
    try:
        op.create_index('idx_projects_type_stage', 'projects', ['project_type', 'current_stage'])
    except Exception:
        pass
    
    # 10. 项目拥有者ID索引 - 优化权限查询
    try:
        op.create_index('idx_projects_owner_id', 'projects', ['owner_id'])
    except Exception:
        pass
    
    # 11. 项目厂商销售负责人索引 - 优化特殊权限查询
    try:
        op.create_index('idx_projects_vendor_sales_manager', 'projects', ['vendor_sales_manager_id'])
    except Exception:
        pass


def downgrade():
    # 移除所有添加的索引
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