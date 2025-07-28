#!/usr/bin/env python3
"""
云端数据库迁移同步脚本
安全地将本地迁移同步到云端数据库
"""

import psycopg2
import os
import sys
import subprocess
from datetime import datetime

# 云端数据库连接信息
CLOUD_DB_URL = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"

def backup_cloud_database():
    """备份云端数据库"""
    print("☁️  开始备份云端数据库...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"cloud_db_backups/cloud_sp8d_backup_before_migration_{timestamp}.sql"
    
    cmd = [
        "pg_dump",
        "--verbose",
        "--clean",
        "--no-acl",
        "--no-owner", 
        "--format=plain",
        "--file", backup_file,
        CLOUD_DB_URL
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            print(f"✅ 云端数据库备份完成: {backup_file}")
            return backup_file
        else:
            print(f"❌ 备份失败: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ 备份异常: {str(e)}")
        return None

def check_cloud_status():
    """检查云端数据库当前状态"""
    print("🔍 检查云端数据库状态...")
    
    try:
        conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = conn.cursor()
        
        # 获取当前版本
        cursor.execute("SELECT version_num FROM alembic_version;")
        current_version = cursor.fetchone()[0]
        
        # 获取表数量
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ 云端当前版本: {current_version}")
        print(f"✅ 云端表数量: {table_count}")
        
        return current_version
        
    except Exception as e:
        print(f"❌ 检查云端状态失败: {str(e)}")
        return None

def main():
    print("🚀 云端数据库迁移同步工具")
    print("=" * 50)
    
    # 1. 检查云端当前状态
    current_version = check_cloud_status()
    if not current_version:
        print("❌ 无法获取云端状态，停止同步")
        return False
    
    # 2. 备份云端数据库
    backup_file = backup_cloud_database()
    if not backup_file:
        print("❌ 云端备份失败，停止同步") 
        return False
    
    print("✅ 云端数据库已安全备份，可以开始迁移")
    print("📋 下一步:")
    print("   1. 在云端环境中执行标准迁移流程")
    print("   2. 使用 alembic upgrade head 或等效命令")
    print("   3. 验证迁移结果")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
