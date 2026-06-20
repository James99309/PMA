
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
    op.execute("CREATE INDEX IF NOT EXISTS idx_quotations_project_id ON quotations (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_quotations_owner_id ON quotations (owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_quotations_created_at ON quotations (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_quotations_updated_at ON quotations (updated_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_quotations_amount ON quotations (amount)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_quotations_project_owner ON quotations (project_id, owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_project_type ON projects (project_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_current_stage ON projects (current_stage)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_type_stage ON projects (project_type, current_stage)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects (owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_vendor_sales_manager ON projects (vendor_sales_manager_id)")


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