#!/usr/bin/env python3
"""
检查SP8D云端数据库的迁移状态
确定是否存在alembic_version表和当前迁移版本
"""

import psycopg2
import os
from urllib.parse import urlparse

# SP8D数据库连接
SP8D_URL = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"

def check_sp8d_migration_status():
    """检查SP8D的迁移状态"""
    try:
        conn = psycopg2.connect(SP8D_URL)
        cursor = conn.cursor()
        
        print("🔍 SP8D数据库迁移状态检查")
        print("=" * 50)
        
        # 1. 检查是否存在alembic_version表
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            )
        """)
        
        has_alembic_table = cursor.fetchone()[0]
        print(f"📋 alembic_version表存在: {'✅ 是' if has_alembic_table else '❌ 否'}")
        
        if has_alembic_table:
            # 2. 获取当前迁移版本
            cursor.execute("SELECT version_num FROM alembic_version")
            result = cursor.fetchone()
            current_version = result[0] if result else "无版本"
            print(f"📌 当前迁移版本: {current_version}")
            
            # 3. 检查本地是否有这个版本
            local_migrations_dir = "migrations/versions"
            if os.path.exists(local_migrations_dir):
                local_files = [f for f in os.listdir(local_migrations_dir) if f.endswith('.py')]
                version_found = any(current_version in f for f in local_files)
                print(f"🔍 本地是否有此版本: {'✅ 有' if version_found else '❌ 无'}")
                
                if not version_found:
                    print("⚠️  版本冲突风险: SP8D版本在本地不存在")
            else:
                print("❌ 本地migrations目录不存在")
        else:
            print("✅ SP8D是全新数据库，无版本冲突")
        
        # 4. 检查表数量
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        print(f"📊 SP8D表数量: {table_count}")
        
        # 5. 检查是否已有我们要添加的表
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('company_assets', 'temp_products')
        """)
        existing_target_tables = [row[0] for row in cursor.fetchall()]
        
        if existing_target_tables:
            print(f"⚠️  目标表已存在: {existing_target_tables}")
        else:
            print("✅ 目标表不存在，可以安全添加")
        
        cursor.close()
        conn.close()
        
        # 6. 生成建议
        print("\n💡 建议方案:")
        if not has_alembic_table:
            print("   🎯 方案A: 初始化迁移历史 + 执行迁移 (推荐)")
            print("   🎯 方案B: 直接原生SQL (快速但无版本管理)")
        elif has_alembic_table and current_version:
            print("   🎯 方案A: 创建基于当前版本的新迁移 (推荐)")
            print("   🎯 方案B: 检查版本冲突后执行迁移")
        
        return has_alembic_table, current_version if has_alembic_table else None
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return None, None

if __name__ == "__main__":
    check_sp8d_migration_status()