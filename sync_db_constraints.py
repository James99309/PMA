#!/usr/bin/env python3
"""
数据库约束和索引同步脚本
同步本地数据库的约束和索引到云端数据库
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

def get_table_defaults(conn, table_name):
    """获取表的默认值约束"""
    cursor = conn.cursor()
    query = """
    SELECT 
        column_name,
        column_default
    FROM information_schema.columns 
    WHERE table_name = %s 
    AND table_schema = 'public'
    AND column_default IS NOT NULL
    ORDER BY ordinal_position;
    """
    
    cursor.execute(query, (table_name,))
    defaults = cursor.fetchall()
    cursor.close()
    return defaults

def set_column_defaults(conn, table_name, column_defaults):
    """设置列的默认值"""
    cursor = conn.cursor()
    
    for column_name, default_value in column_defaults:
        try:
            sql = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET DEFAULT {default_value};"
            print(f"设置默认值: {sql}")
            cursor.execute(sql)
            conn.commit()
            print("  ✓ 成功")
        except psycopg2.Error as e:
            print(f"  ✗ 失败: {e}")
            conn.rollback()
    
    cursor.close()

def main():
    print("=== PostgreSQL 约束和默认值同步工具 ===")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
        # 需要同步默认值的表
        tables_to_sync = [
            'approval_process_template',
            'pricing_orders', 
            'project_rating_records',
            'project_scoring_config',
            'project_scoring_records', 
            'project_total_scores',
            'quotations'
        ]
        
        print("\n2. 同步默认值...")
        for table_name in tables_to_sync:
            print(f"\n处理表: {table_name}")
            
            # 获取本地表的默认值
            local_defaults = get_table_defaults(local_conn, table_name)
            cloud_defaults = get_table_defaults(cloud_conn, table_name)
            
            # 找出需要设置的默认值
            local_defaults_dict = {col: default for col, default in local_defaults}
            cloud_defaults_dict = {col: default for col, default in cloud_defaults}
            
            missing_defaults = []
            for col, default in local_defaults_dict.items():
                if col not in cloud_defaults_dict or cloud_defaults_dict[col] != default:
                    missing_defaults.append((col, default))
            
            if missing_defaults:
                print(f"需要设置 {len(missing_defaults)} 个默认值")
                set_column_defaults(cloud_conn, table_name, missing_defaults)
            else:
                print("默认值已同步")
        
        print("\n3. 验证同步结果...")
        for table_name in tables_to_sync:
            local_defaults = get_table_defaults(local_conn, table_name)
            cloud_defaults = get_table_defaults(cloud_conn, table_name)
            
            if local_defaults == cloud_defaults:
                print(f"✓ {table_name}: 默认值同步成功")
            else:
                print(f"⚠ {table_name}: 默认值仍有差异")
    
    finally:
        # 关闭连接
        local_conn.close()
        cloud_conn.close()
        print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 