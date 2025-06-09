#!/usr/bin/env python3
"""
数据库结构同步脚本
将本地PostgreSQL数据库的最新结构同步到云端数据库
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
    'password': ''  # 本地通常使用信任连接
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

def get_table_structure(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
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
    cursor.close()
    return columns

def get_table_constraints(conn, table_name):
    """获取表约束"""
    cursor = conn.cursor()
    query = """
    SELECT 
        conname,
        contype,
        pg_get_constraintdef(oid) as definition
    FROM pg_constraint 
    WHERE conrelid = (
        SELECT oid FROM pg_class WHERE relname = %s
    )
    ORDER BY conname;
    """
    
    cursor.execute(query, (table_name,))
    constraints = cursor.fetchall()
    cursor.close()
    return constraints

def get_table_indexes(conn, table_name):
    """获取表索引"""
    cursor = conn.cursor()
    query = """
    SELECT 
        indexname,
        indexdef
    FROM pg_indexes 
    WHERE tablename = %s 
    AND schemaname = 'public'
    ORDER BY indexname;
    """
    
    cursor.execute(query, (table_name,))
    indexes = cursor.fetchall()
    cursor.close()
    return indexes

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

def compare_table_structures(local_conn, cloud_conn, table_name):
    """比较两个数据库中表的结构"""
    print(f"\n检查表: {table_name}")
    
    # 比较列结构
    local_columns = get_table_structure(local_conn, table_name)
    cloud_columns = get_table_structure(cloud_conn, table_name)
    
    differences = []
    
    if local_columns != cloud_columns:
        differences.append("列结构不同")
        print(f"  ⚠ 列结构存在差异")
        
        # 详细比较
        local_col_dict = {col[0]: col for col in local_columns}
        cloud_col_dict = {col[0]: col for col in cloud_columns}
        
        # 检查新增的列
        for col_name in local_col_dict:
            if col_name not in cloud_col_dict:
                print(f"    + 本地新增列: {col_name}")
        
        # 检查删除的列
        for col_name in cloud_col_dict:
            if col_name not in local_col_dict:
                print(f"    - 云端多余列: {col_name}")
        
        # 检查修改的列
        for col_name in local_col_dict:
            if col_name in cloud_col_dict:
                if local_col_dict[col_name] != cloud_col_dict[col_name]:
                    print(f"    ~ 列定义差异: {col_name}")
                    print(f"      本地: {local_col_dict[col_name]}")
                    print(f"      云端: {cloud_col_dict[col_name]}")
    
    # 比较约束
    local_constraints = get_table_constraints(local_conn, table_name)
    cloud_constraints = get_table_constraints(cloud_conn, table_name)
    
    if local_constraints != cloud_constraints:
        differences.append("约束不同")
        print(f"  ⚠ 约束存在差异")
    
    # 比较索引
    local_indexes = get_table_indexes(local_conn, table_name)
    cloud_indexes = get_table_indexes(cloud_conn, table_name)
    
    if local_indexes != cloud_indexes:
        differences.append("索引不同")
        print(f"  ⚠ 索引存在差异")
    
    if not differences:
        print(f"  ✓ 表结构一致")
    
    return differences

def dump_schema(conn, db_name):
    """导出数据库结构"""
    print(f"\n正在导出{db_name}结构...")
    
    tables = get_all_tables(conn)
    schema_info = {}
    
    for table in tables:
        schema_info[table] = {
            'columns': get_table_structure(conn, table),
            'constraints': get_table_constraints(conn, table),
            'indexes': get_table_indexes(conn, table)
        }
    
    return schema_info

def generate_sync_sql(local_schema, cloud_schema):
    """生成同步SQL语句"""
    sync_statements = []
    
    for table_name in local_schema:
        if table_name not in cloud_schema:
            # 新表 - 需要完整创建
            sync_statements.append(f"-- 需要创建新表: {table_name}")
            continue
        
        local_cols = {col[0]: col for col in local_schema[table_name]['columns']}
        cloud_cols = {col[0]: col for col in cloud_schema[table_name]['columns']}
        
        # 检查新增列
        for col_name, col_def in local_cols.items():
            if col_name not in cloud_cols:
                data_type = col_def[1]
                if col_def[2]:  # character_maximum_length
                    data_type += f"({col_def[2]})"
                
                nullable = "NULL" if col_def[3] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col_def[4]}" if col_def[4] else ""
                
                sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {data_type} {nullable}{default};"
                sync_statements.append(sql)
        
        # 检查列类型变更
        for col_name, col_def in local_cols.items():
            if col_name in cloud_cols and col_def != cloud_cols[col_name]:
                data_type = col_def[1]
                if col_def[2]:
                    data_type += f"({col_def[2]})"
                
                sql = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {data_type};"
                sync_statements.append(sql)
    
    return sync_statements

def main():
    print("=== PostgreSQL 数据库结构同步工具 ===")
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
        # 获取表列表
        print("\n2. 获取表列表...")
        local_tables = get_all_tables(local_conn)
        cloud_tables = get_all_tables(cloud_conn)
        
        print(f"本地数据库表数量: {len(local_tables)}")
        print(f"云端数据库表数量: {len(cloud_tables)}")
        
        # 比较表列表
        missing_tables = set(local_tables) - set(cloud_tables)
        extra_tables = set(cloud_tables) - set(local_tables)
        
        if missing_tables:
            print(f"云端缺失的表: {missing_tables}")
        if extra_tables:
            print(f"云端多余的表: {extra_tables}")
        
        # 比较共同表的结构
        print("\n3. 比较表结构...")
        common_tables = set(local_tables) & set(cloud_tables)
        tables_with_differences = []
        
        for table in sorted(common_tables):
            differences = compare_table_structures(local_conn, cloud_conn, table)
            if differences:
                tables_with_differences.append((table, differences))
        
        # 生成同步方案
        print("\n4. 生成同步方案...")
        if tables_with_differences:
            print(f"发现 {len(tables_with_differences)} 个表需要同步:")
            for table, diffs in tables_with_differences:
                print(f"  - {table}: {', '.join(diffs)}")
            
            # 导出完整结构
            print("\n5. 导出数据库结构...")
            local_schema = dump_schema(local_conn, "本地数据库")
            cloud_schema = dump_schema(cloud_conn, "云端数据库")
            
            # 生成同步SQL
            sync_sql = generate_sync_sql(local_schema, cloud_schema)
            
            if sync_sql:
                print(f"\n6. 生成同步SQL语句 ({len(sync_sql)} 条):")
                sql_file = f"sync_statements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
                with open(sql_file, 'w', encoding='utf-8') as f:
                    f.write("-- PostgreSQL 数据库结构同步语句\n")
                    f.write(f"-- 生成时间: {datetime.now()}\n")
                    f.write("-- 从本地数据库同步到云端数据库\n\n")
                    for sql in sync_sql:
                        f.write(sql + "\n")
                        print(f"  {sql}")
                
                print(f"\nSQL语句已保存到文件: {sql_file}")
                
                # 询问是否执行同步
                response = input("\n是否立即执行同步? (y/N): ").strip().lower()
                if response == 'y':
                    print("\n7. 执行同步...")
                    cloud_cursor = cloud_conn.cursor()
                    
                    for sql in sync_sql:
                        try:
                            print(f"执行: {sql}")
                            cloud_cursor.execute(sql)
                            cloud_conn.commit()
                            print("  ✓ 成功")
                        except psycopg2.Error as e:
                            print(f"  ✗ 失败: {e}")
                            cloud_conn.rollback()
                    
                    cloud_cursor.close()
                    print("\n同步完成!")
            else:
                print("没有需要执行的SQL语句")
        else:
            print("✓ 所有表结构均一致，无需同步!")
    
    finally:
        # 关闭连接
        local_conn.close()
        cloud_conn.close()
        print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 