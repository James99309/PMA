#!/usr/bin/env python3
"""
检查云端sp8d数据库的当前迁移状态
与本地迁移状态进行对比，确定需要同步的迁移
"""

import psycopg2
import os
import sys
from urllib.parse import urlparse

def check_cloud_migration_status():
    """检查云端数据库的迁移状态"""
    
    # 云端数据库连接信息
    cloud_db_url = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
    
    print("🔍 检查云端sp8d数据库迁移状态...")
    print("=" * 60)
    
    try:
        # 连接云端数据库
        conn = psycopg2.connect(cloud_db_url)
        cursor = conn.cursor()
        
        print("✅ 云端数据库连接成功")
        
        # 检查是否存在alembic_version表
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'alembic_version'
            );
        """)
        
        has_alembic_table = cursor.fetchone()[0]
        
        if not has_alembic_table:
            print("❌ 云端数据库未找到 alembic_version 表")
            print("💡 这意味着云端数据库可能未使用标准迁移管理")
            return None
            
        print("✅ 找到 alembic_version 表")
        
        # 获取当前迁移版本
        cursor.execute("SELECT version_num FROM alembic_version ORDER BY version_num DESC;")
        versions = cursor.fetchall()
        
        if not versions:
            print("❌ alembic_version 表为空")
            return None
            
        current_version = versions[0][0]
        print(f"📋 云端当前迁移版本: {current_version}")
        
        # 显示所有版本（如果有多个）
        if len(versions) > 1:
            print("⚠️  发现多个迁移版本记录:")
            for i, (version,) in enumerate(versions):
                print(f"   {i+1}. {version}")
        
        cursor.close()
        conn.close()
        
        return current_version
        
    except Exception as e:
        print(f"❌ 检查云端数据库迁移状态失败: {str(e)}")
        return None

def check_local_migration_status():
    """检查本地数据库的迁移状态"""
    
    print(f"\n🔍 检查本地数据库迁移状态...")
    print("=" * 60)
    
    try:
        # 连接本地数据库
        import subprocess
        result = subprocess.run(['psql', '-d', 'pma_local', '-t', '-c', 
                               'SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;'],
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 查询本地数据库失败: {result.stderr}")
            return None
            
        local_version = result.stdout.strip()
        if local_version:
            print(f"📋 本地当前迁移版本: {local_version}")
            return local_version
        else:
            print("❌ 本地数据库未找到迁移版本")
            return None
            
    except Exception as e:
        print(f"❌ 检查本地数据库迁移状态失败: {str(e)}")
        return None

def find_migration_path(local_version, cloud_version):
    """查找从云端版本到本地版本的迁移路径"""
    
    print(f"\n🔍 分析迁移路径...")
    print("=" * 60)
    
    if not local_version or not cloud_version:
        print("❌ 缺少版本信息，无法分析迁移路径")
        return []
    
    if local_version == cloud_version:
        print("✅ 云端和本地版本一致，无需迁移")
        return []
    
    print(f"📊 版本对比:")
    print(f"   云端版本: {cloud_version}")
    print(f"   本地版本: {local_version}")
    
    # 读取migrations目录下的版本文件
    migrations_dir = "migrations/versions"
    if not os.path.exists(migrations_dir):
        print(f"❌ 迁移目录不存在: {migrations_dir}")
        return []
    
    # 获取所有迁移文件
    migration_files = []
    for filename in os.listdir(migrations_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            version_id = filename.split('_')[0]
            migration_files.append((version_id, filename))
    
    migration_files.sort()
    
    print(f"\n📁 找到 {len(migration_files)} 个迁移文件")
    
    # 查找云端版本的位置
    cloud_index = -1
    local_index = -1
    
    for i, (version_id, filename) in enumerate(migration_files):
        if version_id == cloud_version:
            cloud_index = i
        if version_id == local_version:
            local_index = i
            
        # 显示迁移文件信息
        status = ""
        if version_id == cloud_version:
            status += "☁️ 云端当前"
        if version_id == local_version:
            status += "🏠 本地当前"
        
        print(f"   {i+1:2d}. {version_id} - {filename} {status}")
    
    if cloud_index == -1:
        print(f"❌ 在迁移文件中未找到云端版本: {cloud_version}")
        return []
        
    if local_index == -1:
        print(f"❌ 在迁移文件中未找到本地版本: {local_version}")
        return []
    
    # 确定需要执行的迁移
    if local_index > cloud_index:
        # 本地版本更新，需要将云端升级到本地版本
        needed_migrations = migration_files[cloud_index + 1:local_index + 1]
        print(f"\n🚀 需要在云端执行 {len(needed_migrations)} 个升级迁移:")
        for i, (version_id, filename) in enumerate(needed_migrations):
            print(f"   {i+1}. {version_id} - {filename}")
        return needed_migrations
    elif local_index < cloud_index:
        # 云端版本更新，本地需要升级
        print(f"\n⚠️  云端版本比本地新，建议先将本地升级到云端版本")
        return []
    else:
        print(f"\n✅ 版本一致，无需迁移")
        return []

def main():
    """主函数"""
    print("🚀 数据库迁移状态检查工具")
    print("=" * 80)
    
    # 检查云端迁移状态
    cloud_version = check_cloud_migration_status()
    
    # 检查本地迁移状态
    local_version = check_local_migration_status()
    
    # 分析迁移路径
    needed_migrations = find_migration_path(local_version, cloud_version)
    
    print(f"\n📋 迁移分析总结:")
    print("=" * 80)
    print(f"云端版本: {cloud_version or '未知'}")
    print(f"本地版本: {local_version or '未知'}")
    
    if needed_migrations:
        print(f"需要执行迁移: {len(needed_migrations)} 个")
        print("\n下一步操作建议:")
        print("1. 确保云端数据库已备份")
        print("2. 创建迁移脚本同步到云端")
        print("3. 在云端执行标准迁移流程")
    else:
        if local_version and cloud_version and local_version == cloud_version:
            print("状态: ✅ 无需迁移")
        else:
            print("状态: ⚠️  需要手动处理")

if __name__ == "__main__":
    main()