#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步本地数据库结构到云端数据库
1. 备份云端数据库内容
2. 导出本地数据库结构
3. 同步结构到云端数据库（不包含数据）
"""

import os
import sys
import psycopg2
import subprocess
import logging
from datetime import datetime
from urllib.parse import urlparse
import tempfile

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
LOCAL_DB_URL = "postgresql://nijie@localhost:5432/pma_local"
CLOUD_DB_URL = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"

def parse_database_url(db_url):
    """解析数据库URL"""
    parsed = urlparse(db_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'username': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/')
    }

def test_database_connection(db_url, db_name):
    """测试数据库连接"""
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        logger.info(f"✅ {db_name}数据库连接成功")
        logger.info(f"   版本: {version[:50]}...")
        return True
    except Exception as e:
        logger.error(f"❌ {db_name}数据库连接失败: {e}")
        return False

def backup_cloud_database():
    """备份云端数据库"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"cloud_backup_pma_db_ovs_{timestamp}.sql"
    backup_path = os.path.join('backups', backup_filename)
    
    # 确保备份目录存在
    os.makedirs('backups', exist_ok=True)
    
    try:
        logger.info("🔄 开始备份云端数据库...")
        
        cloud_config = parse_database_url(CLOUD_DB_URL)
        
        # 构建pg_dump命令
        cmd = [
            'pg_dump',
            '--host', cloud_config['host'],
            '--port', str(cloud_config['port']),
            '--username', cloud_config['username'],
            '--no-password',
            '--format', 'plain',
            '--clean',
            '--create',
            '--encoding', 'UTF8',
            '--verbose',
            cloud_config['database']
        ]
        
        # 设置环境变量
        env = os.environ.copy()
        env['PGPASSWORD'] = cloud_config['password']
        
        # 执行备份命令
        with open(backup_path, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
        
        if result.returncode == 0:
            file_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
            logger.info(f"✅ 云端数据库备份成功: {backup_filename}")
            logger.info(f"   文件大小: {file_size:.2f} MB")
            logger.info(f"   备份路径: {backup_path}")
            return backup_path
        else:
            logger.error(f"❌ 云端数据库备份失败: {result.stderr}")
            if os.path.exists(backup_path):
                os.remove(backup_path)
            return None
            
    except Exception as e:
        logger.error(f"❌ 备份过程中发生错误: {str(e)}")
        if os.path.exists(backup_path):
            os.remove(backup_path)
        return None

def export_local_schema():
    """导出本地数据库结构"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    schema_filename = f"local_schema_{timestamp}.sql"
    schema_path = os.path.join('backups', schema_filename)
    
    try:
        logger.info("🔄 导出本地数据库结构...")
        
        local_config = parse_database_url(LOCAL_DB_URL)
        
        # 构建pg_dump命令（只导出结构）
        cmd = [
            'pg_dump',
            '--host', local_config['host'],
            '--port', str(local_config['port']),
            '--username', local_config['username'],
            '--no-password',
            '--format', 'plain',
            '--schema-only',  # 只导出结构
            '--clean',
            '--no-owner',
            '--no-privileges',
            '--encoding', 'UTF8',
            '--verbose',
            local_config['database']
        ]
        
        # 设置环境变量
        env = os.environ.copy()
        if local_config['password']:
            env['PGPASSWORD'] = local_config['password']
        
        # 执行导出命令
        with open(schema_path, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
        
        if result.returncode == 0:
            file_size = os.path.getsize(schema_path) / 1024  # KB
            logger.info(f"✅ 本地数据库结构导出成功: {schema_filename}")
            logger.info(f"   文件大小: {file_size:.2f} KB")
            logger.info(f"   导出路径: {schema_path}")
            return schema_path
        else:
            logger.error(f"❌ 本地数据库结构导出失败: {result.stderr}")
            if os.path.exists(schema_path):
                os.remove(schema_path)
            return None
            
    except Exception as e:
        logger.error(f"❌ 导出过程中发生错误: {str(e)}")
        if os.path.exists(schema_path):
            os.remove(schema_path)
        return None

def sync_schema_to_cloud(schema_path):
    """同步结构到云端数据库"""
    try:
        logger.info("🔄 开始同步结构到云端数据库...")
        
        cloud_config = parse_database_url(CLOUD_DB_URL)
        
        # 构建psql命令
        cmd = [
            'psql',
            '--host', cloud_config['host'],
            '--port', str(cloud_config['port']),
            '--username', cloud_config['username'],
            '--dbname', cloud_config['database'],
            '--no-password',
            '--file', schema_path,
            '--echo-errors',
            '--set', 'ON_ERROR_STOP=1'
        ]
        
        # 设置环境变量
        env = os.environ.copy()
        env['PGPASSWORD'] = cloud_config['password']
        
        # 执行同步命令
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("✅ 数据库结构同步成功")
            logger.info("   所有表结构已更新到云端数据库")
            return True
        else:
            logger.error(f"❌ 数据库结构同步失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 同步过程中发生错误: {str(e)}")
        return False

def verify_sync_result():
    """验证同步结果"""
    try:
        logger.info("🔄 验证同步结果...")
        
        # 连接云端数据库
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cloud_cursor = cloud_conn.cursor()
        
        # 获取表数量
        cloud_cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        cloud_table_count = cloud_cursor.fetchone()[0]
        
        # 获取序列数量
        cloud_cursor.execute("""
            SELECT COUNT(*) FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        cloud_sequence_count = cloud_cursor.fetchone()[0]
        
        # 检查关键表是否存在
        key_tables = ['users', 'projects', 'quotations', 'products', 'companies']
        existing_tables = []
        
        for table in key_tables:
            cloud_cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            if cloud_cursor.fetchone()[0] > 0:
                existing_tables.append(table)
        
        cloud_cursor.close()
        cloud_conn.close()
        
        logger.info("📊 同步结果验证:")
        logger.info(f"   - 云端表数量: {cloud_table_count}")
        logger.info(f"   - 云端序列数量: {cloud_sequence_count}")
        logger.info(f"   - 关键表存在: {len(existing_tables)}/{len(key_tables)}")
        logger.info(f"   - 存在的关键表: {', '.join(existing_tables)}")
        
        if len(existing_tables) == len(key_tables):
            logger.info("✅ 同步验证成功 - 所有关键表都存在")
            return True
        else:
            missing_tables = set(key_tables) - set(existing_tables)
            logger.warning(f"⚠️ 部分关键表缺失: {', '.join(missing_tables)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 验证过程中发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 同步本地数据库结构到云端数据库")
    print("=" * 80)
    print("📋 任务说明:")
    print("   1. 备份云端数据库内容")
    print("   2. 导出本地数据库结构")
    print("   3. 同步结构到云端数据库（不包含数据）")
    print("=" * 80)
    
    # 1. 测试数据库连接
    print("\n📋 步骤1: 测试数据库连接")
    if not test_database_connection(LOCAL_DB_URL, "本地"):
        print("❌ 本地数据库连接失败，无法继续")
        return False
    
    if not test_database_connection(CLOUD_DB_URL, "云端"):
        print("❌ 云端数据库连接失败，无法继续")
        return False
    
    # 2. 备份云端数据库
    print("\n📋 步骤2: 备份云端数据库")
    backup_path = backup_cloud_database()
    if not backup_path:
        print("❌ 云端数据库备份失败，无法继续")
        return False
    
    # 3. 导出本地数据库结构
    print("\n📋 步骤3: 导出本地数据库结构")
    schema_path = export_local_schema()
    if not schema_path:
        print("❌ 本地数据库结构导出失败，无法继续")
        return False
    
    # 4. 确认同步操作
    print("\n📋 步骤4: 确认同步操作")
    print("⚠️ 警告：即将覆盖云端数据库结构！")
    print(f"   - 云端数据库: pma_db_ovs")
    print(f"   - 备份文件: {backup_path}")
    print(f"   - 结构文件: {schema_path}")
    
    confirm = input("\n是否继续同步？(输入 'YES' 确认): ")
    if confirm != 'YES':
        print("❌ 用户取消操作")
        return False
    
    # 5. 同步结构到云端
    print("\n📋 步骤5: 同步结构到云端数据库")
    if not sync_schema_to_cloud(schema_path):
        print("❌ 数据库结构同步失败")
        return False
    
    # 6. 验证同步结果
    print("\n📋 步骤6: 验证同步结果")
    if not verify_sync_result():
        print("⚠️ 同步验证有警告，请检查")
    
    print("\n🎉 数据库结构同步完成！")
    print(f"📁 备份文件保存在: {backup_path}")
    print(f"📁 结构文件保存在: {schema_path}")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 任务完成")
            sys.exit(0)
        else:
            print("\n❌ 任务失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 