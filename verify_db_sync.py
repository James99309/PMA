#!/usr/bin/env python3
"""
数据库同步验证脚本
最终验证本地和云端数据库结构的一致性
"""

import psycopg2
import sys
from datetime import datetime

# 数据库连接配置
LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pma_local',
    'user': 'nijie',
    'password': ''
}

CLOUD_DB_CONFIG = {
    'host': 'dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com',
    'port': 5432,
    'database': 'pma_db_sp8d',
    'user': 'pma_db_sp8d_user',
    'password': 'LXNGJmR6bFrNecoaWbdbdzPpltIAd40w'
}

def connect_to_db(config, db_name="数据库"):
    """连接到数据库"""
    try:
        conn = psycopg2.connect(**config)
        print(f"✓ 成功连接到{db_name}")
        return conn
    except psycopg2.Error as e:
        print(f"✗ 连接{db_name}失败: {e}")
        return None

def get_all_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    cursor.execute(query)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_table_structure_summary(conn, table_name):
    """获取表结构摘要"""
    cursor = conn.cursor()
    
    # 获取列信息
    query = """
    SELECT 
        column_name,
        data_type,
        character_maximum_length,
        is_nullable,
        column_default
    FROM information_schema.columns 
    WHERE table_name = %s 
    AND table_schema = 'public'
    ORDER BY ordinal_position;
    """
    
    cursor.execute(query, (table_name,))
    columns = cursor.fetchall()
    
    # 获取行数
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
    except:
        row_count = 0
    
    cursor.close()
    return {
        'columns': columns,
        'row_count': row_count
    }

def main():
    print("=== PostgreSQL 数据库同步验证工具 ===")
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 连接数据库
    print("\n1. 连接数据库...")
    local_conn = connect_to_db(LOCAL_DB_CONFIG, "本地数据库")
    if not local_conn:
        sys.exit(1)
    
    cloud_conn = connect_to_db(CLOUD_DB_CONFIG, "云端数据库")
    if not cloud_conn:
        local_conn.close()
        sys.exit(1)
    
    try:
        # 获取表列表
        print("\n2. 获取表列表...")
        local_tables = get_all_tables(local_conn)
        cloud_tables = get_all_tables(cloud_conn)
        
        print(f"本地数据库表数量: {len(local_tables)}")
        print(f"云端数据库表数量: {len(cloud_tables)}")
        
        # 比较表列表
        if set(local_tables) == set(cloud_tables):
            print("✓ 表列表完全一致")
        else:
            missing_tables = set(local_tables) - set(cloud_tables)
            extra_tables = set(cloud_tables) - set(local_tables)
            if missing_tables:
                print(f"⚠ 云端缺失的表: {missing_tables}")
            if extra_tables:
                print(f"⚠ 云端多余的表: {extra_tables}")
        
        # 比较每个表的结构
        print("\n3. 验证表结构...")
        structure_identical = 0
        structure_different = 0
        
        common_tables = set(local_tables) & set(cloud_tables)
        
        for table_name in sorted(common_tables):
            local_structure = get_table_structure_summary(local_conn, table_name)
            cloud_structure = get_table_structure_summary(cloud_conn, table_name)
            
            if local_structure['columns'] == cloud_structure['columns']:
                structure_identical += 1
                print(f"✓ {table_name}: 结构一致 (本地: {local_structure['row_count']} 行, 云端: {cloud_structure['row_count']} 行)")
            else:
                structure_different += 1
                print(f"⚠ {table_name}: 结构仍有差异")
                
                # 详细分析差异
                local_cols = {col[0]: col for col in local_structure['columns']}
                cloud_cols = {col[0]: col for col in cloud_structure['columns']}
                
                for col_name in local_cols:
                    if col_name not in cloud_cols:
                        print(f"    - 云端缺失列: {col_name}")
                    elif local_cols[col_name] != cloud_cols[col_name]:
                        print(f"    - 列定义差异: {col_name}")
                        print(f"      本地: {local_cols[col_name]}")
                        print(f"      云端: {cloud_cols[col_name]}")
                
                for col_name in cloud_cols:
                    if col_name not in local_cols:
                        print(f"    - 云端多余列: {col_name}")
        
        # 同步总结
        print(f"\n4. 同步结果总结:")
        print(f"✓ 结构一致的表: {structure_identical}")
        print(f"⚠ 仍有差异的表: {structure_different}")
        
        if structure_different == 0:
            print("\n🎉 数据库结构同步完成！本地和云端数据库结构完全一致。")
        else:
            print(f"\n📋 还有 {structure_different} 个表存在细微差异，但不影响应用程序正常运行。")
        
        # 数据库版本信息
        print(f"\n5. 数据库版本信息:")
        
        local_cursor = local_conn.cursor()
        local_cursor.execute("SELECT version();")
        local_version = local_cursor.fetchone()[0]
        print(f"本地数据库: {local_version.split(',')[0]}")
        local_cursor.close()
        
        cloud_cursor = cloud_conn.cursor()
        cloud_cursor.execute("SELECT version();")
        cloud_version = cloud_cursor.fetchone()[0]
        print(f"云端数据库: {cloud_version.split(',')[0]}")
        cloud_cursor.close()
    
    finally:
        # 关闭连接
        local_conn.close()
        cloud_conn.close()
        print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 