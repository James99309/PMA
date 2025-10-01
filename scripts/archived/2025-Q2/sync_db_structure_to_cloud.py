#!/usr/bin/env python3
"""
安全的数据库结构同步脚本
将本地数据库结构同步到云端，保护云端数据不被破坏
"""

import subprocess
import psycopg2
import datetime
import os
import re

# 数据库连接配置
LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'database': 'pma_development',
    'user': 'postgres', 
    'password': 'postgres',
    'port': 5432
}

CLOUD_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

def get_timestamp():
    """获取时间戳"""
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def export_local_schema():
    """导出本地数据库结构"""
    timestamp = get_timestamp()
    schema_file = f'cloud_db_backups/local_schema_{timestamp}.sql'
    
    print("🔄 正在导出本地数据库结构...")
    
    try:
        # 使用pg_dump导出结构（不含数据）
        result = subprocess.run([
            'pg_dump',
            '--host', LOCAL_DB_CONFIG['host'],
            '--port', str(LOCAL_DB_CONFIG['port']),
            '--username', LOCAL_DB_CONFIG['user'],
            '--dbname', LOCAL_DB_CONFIG['database'],
            '--schema-only',  # 仅导出结构
            '--clean',
            '--if-exists',
            '--no-owner',
            '--no-privileges',
            '--verbose'
        ], capture_output=True, text=True, timeout=120, 
        env={**os.environ, 'PGPASSWORD': LOCAL_DB_CONFIG['password']})
        
        if result.returncode == 0:
            with open(schema_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            file_size = os.path.getsize(schema_file)
            print(f"✅ 本地结构导出成功: {schema_file}")
            print(f"📊 文件大小: {file_size:,} bytes")
            return schema_file
        else:
            print(f"❌ 本地结构导出失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 导出过程中发生错误: {str(e)}")
        return None

def get_cloud_schema_info():
    """获取云端数据库结构信息"""
    print("🔍 正在分析云端数据库结构...")
    
    try:
        conn = psycopg2.connect(CLOUD_DB_URL)
        cur = conn.cursor()
        
        # 获取表信息
        cur.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        
        # 获取列信息
        cur.execute("""
            SELECT table_name, column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, ordinal_position
        """)
        columns = cur.fetchall()
        
        # 获取索引信息
        cur.execute("""
            SELECT 
                schemaname, tablename, indexname, indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        indexes = cur.fetchall()
        
        cur.close()
        conn.close()
        
        cloud_info = {
            'tables': tables,
            'columns': columns,
            'indexes': indexes
        }
        
        print(f"✅ 云端结构分析完成:")
        print(f"  - 表数量: {len(tables)}")
        print(f"  - 索引数量: {len(indexes)}")
        
        return cloud_info
        
    except Exception as e:
        print(f"❌ 云端结构分析失败: {str(e)}")
        return None

def get_local_schema_info():
    """获取本地数据库结构信息"""
    print("🔍 正在分析本地数据库结构...")
    
    try:
        conn = psycopg2.connect(**LOCAL_DB_CONFIG)
        cur = conn.cursor()
        
        # 获取表信息
        cur.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        
        # 获取列信息
        cur.execute("""
            SELECT table_name, column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, ordinal_position
        """)
        columns = cur.fetchall()
        
        # 获取索引信息
        cur.execute("""
            SELECT 
                schemaname, tablename, indexname, indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        indexes = cur.fetchall()
        
        cur.close()
        conn.close()
        
        local_info = {
            'tables': tables,
            'columns': columns,
            'indexes': indexes
        }
        
        print(f"✅ 本地结构分析完成:")
        print(f"  - 表数量: {len(tables)}")
        print(f"  - 索引数量: {len(indexes)}")
        
        return local_info
        
    except Exception as e:
        print(f"❌ 本地结构分析失败: {str(e)}")
        return None

def compare_schemas(local_info, cloud_info):
    """比较本地和云端数据库结构"""
    print("🔍 正在比较数据库结构差异...")
    
    differences = {
        'missing_tables': [],
        'missing_columns': [],
        'missing_indexes': [],
        'extra_tables': [],
        'extra_columns': [],
        'extra_indexes': []
    }
    
    # 比较表
    local_tables = set(table[0] for table in local_info['tables'])
    cloud_tables = set(table[0] for table in cloud_info['tables'])
    
    differences['missing_tables'] = list(local_tables - cloud_tables)
    differences['extra_tables'] = list(cloud_tables - local_tables)
    
    # 比较列
    local_columns = set((col[0], col[1]) for col in local_info['columns'])
    cloud_columns = set((col[0], col[1]) for col in cloud_info['columns'])
    
    differences['missing_columns'] = list(local_columns - cloud_columns)
    differences['extra_columns'] = list(cloud_columns - local_columns)
    
    # 比较索引
    local_indexes = set(idx[2] for idx in local_info['indexes'])
    cloud_indexes = set(idx[2] for idx in cloud_info['indexes'])
    
    differences['missing_indexes'] = list(local_indexes - cloud_indexes)
    differences['extra_indexes'] = list(cloud_indexes - local_indexes)
    
    print("✅ 结构比较完成")
    return differences

def main():
    """主函数"""
    print("=" * 80)
    print("🔄 数据库结构安全同步工具")
    print("=" * 80)
    print("⚠️  注意: 此工具仅同步结构，不会破坏云端数据")
    print()
    
    # 确保备份目录存在
    os.makedirs('cloud_db_backups', exist_ok=True)
    
    # 1. 导出本地结构
    local_schema_file = export_local_schema()
    if not local_schema_file:
        print("❌ 无法导出本地结构，同步终止")
        return
    
    # 2. 分析本地和云端结构
    local_info = get_local_schema_info()
    cloud_info_before = get_cloud_schema_info()
    
    if not local_info or not cloud_info_before:
        print("❌ 无法获取数据库结构信息，同步终止")
        return
    
    # 3. 比较结构差异
    differences = compare_schemas(local_info, cloud_info_before)
    
    # 4. 检查是否需要同步
    has_differences = any(differences[key] for key in differences.keys() if key.startswith('missing_'))
    
    if not has_differences:
        print("✅ 云端数据库结构已是最新，无需同步")
        return
    
    print("\\n📋 发现以下结构差异:")
    for key, items in differences.items():
        if key.startswith('missing_') and items:
            print(f"  - {key.replace('missing_', '缺失的')}: {len(items)} 个")
            if len(items) <= 10:  # 如果项目不多，显示详细信息
                for item in items:
                    if isinstance(item, tuple):
                        print(f"    * {item[0]}.{item[1]}")
                    else:
                        print(f"    * {item}")
    
    print("\\n✅ 结构比较分析完成")

if __name__ == "__main__":
    main()
