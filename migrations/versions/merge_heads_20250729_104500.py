"""合并多头版本迁移

解决多数据库迁移导致的多头版本冲突问题

Revision ID: merge_heads_20250729_104500
Revises: sync_local_to_cloud_20250728, ovs_sync_to_latest_20250729
Create Date: 2025-07-29 10:45:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads_20250729_104500'
down_revision = ('sync_local_to_cloud_20250728', 'ovs_sync_to_latest_20250729')
branch_labels = None
depends_on = None


def upgrade():
    """合并多头版本，无需额外操作"""
    print("🔄 执行多头版本合并...")
    
    # 🔒 安全检查: 验证当前数据库环境
    connection = op.get_bind()
    
    try:
        result = connection.execute(sa.text("SELECT current_database()"))
        db_name = result.fetchone()[0]
        print(f"✅ 当前数据库: {db_name}")
        
        # 验证alembic版本状态
        result = connection.execute(sa.text("SELECT version_num FROM alembic_version"))
        versions = result.fetchall()
        
        if versions:
            current_version = versions[0][0]
            print(f"✅ 当前迁移版本: {current_version}")
        
        print("✅ 多头版本合并完成")
        
    except Exception as e:
        print(f"⚠️ 合并过程警告: {e}")


def downgrade():
    """回滚合并操作"""
    print("⚠️ 多头版本合并回滚")
    print("建议使用数据库备份恢复而不是自动回滚")
    pass