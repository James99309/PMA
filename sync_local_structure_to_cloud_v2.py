#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步本地数据库结构到云端数据库 (改进版本)
1. 备份云端数据库内容
2. 清理云端数据库结构
3. 导出本地数据库结构
4. 同步结构到云端数据库（不包含数据）
"""

import os
import sys
import psycopg2
import subprocess
import logging
from datetime import datetime
from urllib.parse import urlparse

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

def clean_cloud_database():
    """清理云端数据库结构"""
    try:
        logger.info("🔄 清理云端数据库结构...")
        
        conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # 获取所有序列名
        cursor.execute("""
            SELECT sequencename FROM pg_sequences 
            WHERE schemaname = 'public'
        """)
        sequences = [row[0] for row in cursor.fetchall()]
        
        # 获取所有视图名
        cursor.execute("""
            SELECT viewname FROM pg_views 
            WHERE schemaname = 'public'
        """)
        views = [row[0] for row in cursor.fetchall()]
        
        # 删除所有外键约束
        cursor.execute("""
            SELECT conname, conrelid::regclass 
            FROM pg_constraint 
            WHERE contype = 'f' AND connamespace = 'public'::regnamespace
        """)
        foreign_keys = cursor.fetchall()
        
        for fk_name, table_name in foreign_keys:
            try:
                cursor.execute(f'ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS "{fk_name}" CASCADE')
            except Exception as e:
                logger.warning(f"删除外键约束 {fk_name} 失败: {e}")
        
        # 删除所有视图
        for view in views:
            try:
                cursor.execute(f'DROP VIEW IF EXISTS "{view}" CASCADE')
            except Exception as e:
                logger.warning(f"删除视图 {view} 失败: {e}")
        
        # 删除所有表
        for table in tables:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
            except Exception as e:
                logger.warning(f"删除表 {table} 失败: {e}")
        
        # 删除所有序列
        for sequence in sequences:
            try:
                cursor.execute(f'DROP SEQUENCE IF EXISTS "{sequence}" CASCADE')
            except Exception as e:
                logger.warning(f"删除序列 {sequence} 失败: {e}")
        
        # 删除所有函数
        cursor.execute("""
            SELECT proname, oidvectortypes(proargtypes) 
            FROM pg_proc 
            WHERE pronamespace = 'public'::regnamespace
        """)
        functions = cursor.fetchall()
        
        for func_name, func_args in functions:
            try:
                cursor.execute(f'DROP FUNCTION IF EXISTS "{func_name}"({func_args}) CASCADE')
            except Exception as e:
                logger.warning(f"删除函数 {func_name} 失败: {e}")
        
        # 删除所有自定义类型
        cursor.execute("""
            SELECT typname FROM pg_type 
            WHERE typnamespace = 'public'::regnamespace 
            AND typtype = 'e'
        """)
        types = [row[0] for row in cursor.fetchall()]
        
        for type_name in types:
            try:
                cursor.execute(f'DROP TYPE IF EXISTS "{type_name}" CASCADE')
            except Exception as e:
                logger.warning(f"删除类型 {type_name} 失败: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ 云端数据库清理完成")
        logger.info(f"   - 删除表: {len(tables)} 个")
        logger.info(f"   - 删除序列: {len(sequences)} 个")
        logger.info(f"   - 删除视图: {len(views)} 个")
        logger.info(f"   - 删除外键约束: {len(foreign_keys)} 个")
        logger.info(f"   - 删除函数: {len(functions)} 个")
        logger.info(f"   - 删除自定义类型: {len(types)} 个")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 清理云端数据库失败: {str(e)}")
        return False

def export_local_schema():
    """导出本地数据库结构"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    schema_filename = f"local_schema_{timestamp}.sql"
    schema_path = os.path.join('backups', schema_filename)
    
    try:
        logger.info("🔄 导出本地数据库结构...")
        
        local_config = parse_database_url(LOCAL_DB_URL)
        
        # 构建pg_dump命令（只导出结构，不清理）
        cmd = [
            'pg_dump',
            '--host', local_config['host'],
            '--port', str(local_config['port']),
            '--username', local_config['username'],
            '--no-password',
            '--format', 'plain',
            '--schema-only',  # 只导出结构
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
        
        # 连接本地数据库
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        local_cursor = local_conn.cursor()
        
        # 连接云端数据库
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cloud_cursor = cloud_conn.cursor()
        
        # 获取本地表数量
        local_cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        local_table_count = local_cursor.fetchone()[0]
        
        # 获取云端表数量
        cloud_cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        cloud_table_count = cloud_cursor.fetchone()[0]
        
        # 获取本地序列数量
        local_cursor.execute("""
            SELECT COUNT(*) FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        local_sequence_count = local_cursor.fetchone()[0]
        
        # 获取云端序列数量
        cloud_cursor.execute("""
            SELECT COUNT(*) FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        cloud_sequence_count = cloud_cursor.fetchone()[0]
        
        # 检查关键表是否存在
        key_tables = ['users', 'projects', 'quotations', 'products', 'companies']
        local_existing_tables = []
        cloud_existing_tables = []
        
        for table in key_tables:
            # 检查本地
            local_cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            if local_cursor.fetchone()[0] > 0:
                local_existing_tables.append(table)
            
            # 检查云端
            cloud_cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            if cloud_cursor.fetchone()[0] > 0:
                cloud_existing_tables.append(table)
        
        local_cursor.close()
        local_conn.close()
        cloud_cursor.close()
        cloud_conn.close()
        
        logger.info("📊 同步结果验证:")
        logger.info(f"   - 本地表数量: {local_table_count}")
        logger.info(f"   - 云端表数量: {cloud_table_count}")
        logger.info(f"   - 本地序列数量: {local_sequence_count}")
        logger.info(f"   - 云端序列数量: {cloud_sequence_count}")
        logger.info(f"   - 本地关键表: {len(local_existing_tables)}/{len(key_tables)}")
        logger.info(f"   - 云端关键表: {len(cloud_existing_tables)}/{len(key_tables)}")
        
        # 检查同步是否成功
        tables_match = cloud_table_count == local_table_count
        sequences_match = cloud_sequence_count == local_sequence_count
        key_tables_match = len(cloud_existing_tables) == len(local_existing_tables)
        
        if tables_match and sequences_match and key_tables_match:
            logger.info("✅ 同步验证成功 - 结构完全匹配")
            return True
        else:
            if not tables_match:
                logger.warning(f"⚠️ 表数量不匹配: 本地{local_table_count} vs 云端{cloud_table_count}")
            if not sequences_match:
                logger.warning(f"⚠️ 序列数量不匹配: 本地{local_sequence_count} vs 云端{cloud_sequence_count}")
            if not key_tables_match:
                logger.warning(f"⚠️ 关键表不匹配: 本地{local_existing_tables} vs 云端{cloud_existing_tables}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 验证过程中发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 同步本地数据库结构到云端数据库 (改进版本)")
    print("=" * 80)
    print("📋 任务说明:")
    print("   1. 备份云端数据库内容")
    print("   2. 清理云端数据库结构")
    print("   3. 导出本地数据库结构")
    print("   4. 同步结构到云端数据库（不包含数据）")
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
    
    # 3. 确认清理操作
    print("\n📋 步骤3: 确认清理和同步操作")
    print("⚠️ 警告：即将清理并覆盖云端数据库结构！")
    print(f"   - 云端数据库: pma_db_ovs")
    print(f"   - 备份文件: {backup_path}")
    print("   - 将删除云端所有表、序列、视图、函数")
    print("   - 然后导入本地数据库结构")
    
    confirm = input("\n是否继续同步？(输入 'YES' 确认): ")
    if confirm != 'YES':
        print("❌ 用户取消操作")
        return False
    
    # 4. 清理云端数据库
    print("\n📋 步骤4: 清理云端数据库结构")
    if not clean_cloud_database():
        print("❌ 云端数据库清理失败，无法继续")
        return False
    
    # 5. 导出本地数据库结构
    print("\n📋 步骤5: 导出本地数据库结构")
    schema_path = export_local_schema()
    if not schema_path:
        print("❌ 本地数据库结构导出失败，无法继续")
        return False
    
    # 6. 同步结构到云端
    print("\n📋 步骤6: 同步结构到云端数据库")
    if not sync_schema_to_cloud(schema_path):
        print("❌ 数据库结构同步失败")
        return False
    
    # 7. 验证同步结果
    print("\n📋 步骤7: 验证同步结果")
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