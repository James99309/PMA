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
    
    print("🚀 开始SP8D数据库迁移安全检查...")
    
    # 🔒 安全检查: 验证当前数据库是否为SP8D
    connection = op.get_bind()
    
    try:
        result = connection.execute(sa.text("SELECT current_database()"))
        db_name = result.fetchone()[0]
        
        if 'sp8d' not in db_name.lower():
            print(f"❌ 安全检查失败: 当前数据库 '{db_name}' 不是SP8D数据库")
            print("   此迁移仅适用于SP8D数据库 (数据库名应包含'sp8d')")
            print("   请检查 DATABASE_URL 环境变量")
            raise Exception("数据库安全检查失败 - 非SP8D数据库")
            
        print(f"✅ 安全检查通过: 当前数据库 '{db_name}' 是SP8D数据库")
    except Exception as e:
        if "数据库安全检查失败" in str(e):
            raise
        print(f"⚠️ 无法确定数据库名称，继续执行: {e}")
    
    # 验证前置版本
    try:
        result = connection.execute(sa.text("SELECT version_num FROM alembic_version"))
        versions = result.fetchall()
        
        if not versions or versions[0][0] != 'c8d3eaeaf234':
            current_version = versions[0][0] if versions else "无版本"
            print(f"⚠️ 版本检查: 当前版本 '{current_version}'，期望版本 'c8d3eaeaf234'")
            print("   如果确认要强制执行，请继续...")
        else:
            print("✅ 版本检查通过: 当前版本匹配期望的前置版本")
    except Exception as e:
        print(f"⚠️ 版本检查警告: {e}")
    
    print("🎉 开始执行SP8D数据库迁移...")
    
    # 使用标准的Alembic方法创建索引（不使用CONCURRENTLY避免事务问题）
    
    # 1. 报价单性能索引
    try:
        op.create_index('idx_quotations_project_id', 'quotations', ['project_id'], if_not_exists=True)
    except Exception:
        pass  # 索引可能已存在
    
    try:
        op.create_index('idx_quotations_owner_id', 'quotations', ['owner_id'], if_not_exists=True)
    except Exception:
        pass
    
    try:
        op.create_index('idx_quotations_created_at', 'quotations', ['created_at'], if_not_exists=True)
    except Exception:
        pass
    
    try:
        op.create_index('idx_quotations_updated_at', 'quotations', ['updated_at'], if_not_exists=True)
    except Exception:
        pass
    
    try:
        op.create_index('idx_quotations_amount', 'quotations', ['amount'], if_not_exists=True)
    except Exception:
        pass
    
    try:
        op.create_index('idx_quotations_project_owner', 'quotations', ['project_id', 'owner_id'], if_not_exists=True)
    except Exception:
        pass
    
    # 2. 项目性能索引
    try:
        op.create_index('idx_projects_project_type', 'projects', ['project_type'], if_not_exists=True)
    except Exception:
        pass
    
    try:
        op.create_index('idx_projects_current_stage', 'projects', ['current_stage'], if_not_exists=True)
    except Exception:
        pass
    
    try:
        op.create_index('idx_projects_type_stage', 'projects', ['project_type', 'current_stage'], if_not_exists=True)
    except Exception:
        pass
    
    try:
        op.create_index('idx_projects_owner_id', 'projects', ['owner_id'], if_not_exists=True)
    except Exception:
        pass
    
    try:
        op.create_index('idx_projects_vendor_sales_manager', 'projects', ['vendor_sales_manager_id'], if_not_exists=True)
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