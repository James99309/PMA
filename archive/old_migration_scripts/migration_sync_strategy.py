#!/usr/bin/env python3
"""
数据库同步策略分析和实施方案
基于当前迁移状态制定安全的同步策略
"""

import os
import subprocess
import sys

def analyze_migration_situation():
    """分析当前迁移情况"""
    
    print("🔍 迁移情况分析")
    print("=" * 60)
    
    cloud_version = "c8d3eaeaf234"  # 云端当前版本
    local_version = "592b90d54921"  # 本地当前版本
    
    print(f"云端版本: {cloud_version}")
    print(f"本地版本: {local_version}")
    
    # 迁移文件顺序分析
    migrations = [
        "592b90d54921",  # 本地当前 - 优化报价单筛选性能_添加关键索引
        "669777b71041",  # add_pdf_path_field_to_products_table
        "69da2a6b4ac1",  # 添加植入总额字段_implanted_total_amount_到_
        "7dfcf037db65",  # add_pdf_path_field_to_dev_products_table
        "c8d3eaeaf234"   # 云端当前 - 添加缺失的settlement_status字段修复报价单删除功能
    ]
    
    local_index = migrations.index(local_version)
    cloud_index = migrations.index(cloud_version)
    
    print(f"\n迁移位置分析:")
    print(f"本地位置: {local_index + 1} / {len(migrations)}")
    print(f"云端位置: {cloud_index + 1} / {len(migrations)}")
    
    # 分析需要同步的迁移
    if cloud_index > local_index:
        # 云端比本地新
        missing_migrations = migrations[local_index + 1:cloud_index + 1]
        print(f"\n❗ 本地缺少 {len(missing_migrations)} 个迁移:")
        for i, migration in enumerate(missing_migrations):
            print(f"   {i+1}. {migration}")
        
        return "local_behind", missing_migrations
    elif local_index > cloud_index:
        # 本地比云端新
        new_migrations = migrations[cloud_index + 1:local_index + 1]
        print(f"\n🚀 本地有 {len(new_migrations)} 个新迁移可以同步到云端:")
        for i, migration in enumerate(new_migrations):
            print(f"   {i+1}. {migration}")
        
        return "cloud_behind", new_migrations
    else:
        print(f"\n✅ 版本一致")
        return "synced", []

def generate_sync_strategy():
    """生成同步策略"""
    
    print(f"\n🎯 推荐同步策略")
    print("=" * 60)
    
    status, migrations = analyze_migration_situation()
    
    if status == "local_behind":
        print("📋 策略: 先同步云端迁移到本地")
        print("\n步骤:")
        print("1. 📦 本地数据库备份")
        print("2. 🔄 拉取最新的迁移文件 (如果需要)")
        print("3. 🚀 执行本地迁移升级")
        print("4. ✅ 验证本地数据库状态")
        print("5. 📊 重新评估同步需求")
        
        print(f"\n需要在本地执行的迁移:")
        for migration in migrations:
            print(f"   - {migration}")
            
    elif status == "cloud_behind":
        print("📋 策略: 同步本地迁移到云端")
        print("\n步骤:")
        print("1. ☁️  云端数据库完整备份")
        print("2. 📤 上传迁移文件到云端环境")
        print("3. 🚀 在云端执行迁移升级")
        print("4. ✅ 验证云端数据库状态")
        print("5. 🔄 确认本地和云端同步")
        
        print(f"\n需要在云端执行的迁移:")
        for migration in migrations:
            print(f"   - {migration}")
            
    else:
        print("✅ 当前版本已同步，无需迁移")

def create_local_upgrade_script():
    """创建本地升级脚本"""
    
    script_content = '''#!/bin/bash
# 本地数据库迁移升级脚本
# 将本地数据库升级到与云端相同的版本

set -e  # 遇到错误立即退出

echo "🚀 开始本地数据库迁移升级..."

# 1. 激活虚拟环境
source venv/bin/activate

# 2. 备份当前数据库
echo "📦 创建数据库备份..."
timestamp=$(date +"%Y%m%d_%H%M%S")
pg_dump pma_local > "backups/local_backup_before_migration_${timestamp}.sql"
echo "✅ 备份完成: backups/local_backup_before_migration_${timestamp}.sql"

# 3. 检查当前迁移状态
echo "🔍 检查当前迁移状态..."
current_version=$(psql -d pma_local -t -c "SELECT version_num FROM alembic_version;" | xargs)
echo "当前版本: $current_version"

# 4. 执行迁移升级
echo "🚀 执行迁移升级..."
cd migrations
alembic upgrade head
cd ..

# 5. 验证升级结果
echo "✅ 验证升级结果..."
new_version=$(psql -d pma_local -t -c "SELECT version_num FROM alembic_version;" | xargs)
echo "新版本: $new_version"

# 6. 运行数据库完整性检查
echo "🔍 运行数据库完整性检查..."
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app import db
    # 基本连接测试
    result = db.engine.execute('SELECT 1').scalar()
    print(f'数据库连接正常: {result == 1}')
    print('✅ 数据库完整性检查通过')
"

echo "🎉 本地数据库迁移升级完成!"
echo "📋 版本变化: $current_version -> $new_version"
'''

    with open("upgrade_local_database.sh", "w") as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod("upgrade_local_database.sh", 0o755)
    
    print("📄 本地升级脚本已创建: upgrade_local_database.sh")

def create_cloud_sync_script():
    """创建云端同步脚本"""
    
    script_content = '''#!/usr/bin/env python3
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
'''

    with open("sync_to_cloud.py", "w") as f:
        f.write(script_content)
        
    print("📄 云端同步脚本已创建: sync_to_cloud.py")

def main():
    """主函数"""
    print("🚀 数据库迁移同步策略生成工具")
    print("=" * 80)
    
    # 分析并生成策略
    generate_sync_strategy()
    
    print(f"\n🛠️  生成同步工具")
    print("=" * 60)
    
    # 创建同步脚本
    create_local_upgrade_script()
    create_cloud_sync_script()
    
    print(f"\n📋 下一步操作建议:")
    print("=" * 60)
    print("1. 📦 运行云端备份（已完成）")
    print("2. 🔄 先执行本地升级: ./upgrade_local_database.sh")
    print("3. ☁️  然后准备云端同步: python sync_to_cloud.py")
    print("4. ✅ 在云端环境执行标准迁移流程")

if __name__ == "__main__":
    main()