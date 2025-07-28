#!/usr/bin/env python3
'''
云端数据库增量迁移部署脚本
安全地将本地最新结构同步到云端
'''

import psycopg2
import sys
from datetime import datetime

CLOUD_DB_URL = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"

def execute_migration():
    '''执行增量迁移'''
    print("🚀 开始执行云端增量迁移...")
    
    try:
        # 读取迁移脚本
        with open('migrations/local_to_cloud_incremental_20250728_231123.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # 连接云端数据库
        conn = psycopg2.connect(CLOUD_DB_URL)
        conn.autocommit = False  # 使用事务
        
        cursor = conn.cursor()
        
        print("✅ 云端数据库连接成功")
        
        # 执行迁移
        print("🔄 执行迁移脚本...")
        cursor.execute(migration_sql)
        
        # 验证迁移结果
        cursor.execute("SELECT version_num FROM alembic_version;")
        new_version = cursor.fetchone()[0]
        
        # 提交事务
        conn.commit()
        
        print(f"✅ 迁移成功完成！新版本: {new_version}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        try:
            conn.rollback()
            print("✅ 事务已回滚")
        except:
            pass
        return False

def main():
    print("🚀 云端数据库增量迁移工具")
    print("=" * 50)
    
    success = execute_migration()
    
    if success:
        print("\n🎉 云端数据库迁移成功完成！")
        print("📋 已应用本地最新的数据库结构")
    else:
        print("\n💥 云端数据库迁移失败")
        print("📋 数据库状态已回滚，请检查错误信息")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
