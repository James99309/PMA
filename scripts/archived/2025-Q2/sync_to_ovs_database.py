#!/usr/bin/env python3
"""
将本地数据库结构同步到 pma_db_ovs 数据库
先备份目标数据库，然后安全地同步结构

Created: 2025-06-27
Author: Assistant
Purpose: 安全地将本地数据库结构同步到pma_db_ovs数据库
"""

import os
import sys
import psycopg2
import json
from datetime import datetime
from urllib.parse import urlparse

# 数据库连接配置
LOCAL_DB_URL = os.getenv('DATABASE_URL', 'postgresql://nijie:@localhost:5432/pma_local')
OVS_DB_URL = 'postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs'

def parse_db_url(db_url):
    """解析数据库URL"""
    parsed = urlparse(db_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password
    }

def get_db_connection(db_url):
    """获取数据库连接"""
    db_config = parse_db_url(db_url)
    return psycopg2.connect(**db_config)

def backup_ovs_database():
    """备份OVS数据库"""
    print("=== 备份pma_db_ovs数据库 ===")
    
    # 创建备份目录
    backup_dir = "ovs_db_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/pma_db_ovs_backup_{timestamp}.sql"
    
    # 解析数据库配置
    db_config = parse_db_url(OVS_DB_URL)
    
    # 使用pg_dump备份
    dump_cmd = [
        'pg_dump',
        f"--host={db_config['host']}",
        f"--port={db_config['port']}",
        f"--username={db_config['user']}",
        f"--dbname={db_config['database']}",
        '--verbose',
        '--clean',
        '--no-owner',
        '--no-privileges',
        '--format=plain',
        f"--file={backup_file}"
    ]
    
    # 设置密码环境变量
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    try:
        import subprocess
        print(f"正在备份pma_db_ovs数据库到: {backup_file}")
        result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ pma_db_ovs数据库备份成功: {backup_file}")
            
            # 创建备份信息文件
            info_file = f"{backup_dir}/pma_db_ovs_backup_info_{timestamp}.md"
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"# pma_db_ovs数据库备份信息\n\n")
                f.write(f"**备份时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**源数据库**: {db_config['host']}:{db_config['port']}/{db_config['database']}\n")
                f.write(f"**备份文件**: {backup_file}\n")
                f.write(f"**备份大小**: {os.path.getsize(backup_file)} 字节\n\n")
                f.write("## 备份说明\n")
                f.write("- 这是在数据库结构同步前的完整备份\n")
                f.write("- 包含所有表结构和数据\n")
                f.write("- 可用于紧急恢复\n")
            
            return backup_file
        else:
            print(f"❌ 备份失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 备份过程出错: {str(e)}")
        return None

def get_table_columns(db_url):
    """获取数据库表的列信息"""
    conn = get_db_connection(db_url)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.is_nullable,
            c.column_default,
            c.ordinal_position
        FROM information_schema.tables t
        JOIN information_schema.columns c ON t.table_name = c.table_name
        WHERE t.table_schema = 'public' AND c.table_schema = 'public'
        ORDER BY t.table_name, c.ordinal_position;
    """)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # 按表组织数据
    tables = {}
    for row in results:
        table_name = row[0]
        if table_name not in tables:
            tables[table_name] = []
        tables[table_name].append({
            'column_name': row[1],
            'data_type': row[2],
            'character_maximum_length': row[3],
            'numeric_precision': row[4],
            'numeric_scale': row[5],
            'is_nullable': row[6],
            'column_default': row[7],
            'ordinal_position': row[8]
        })
    
    return tables

def get_table_constraints(db_url):
    """获取表的约束信息"""
    conn = get_db_connection(db_url)
    cursor = conn.cursor()
    
    # 获取主键信息
    cursor.execute("""
        SELECT 
            tc.table_name,
            kcu.column_name,
            tc.constraint_type
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_schema = 'public'
          AND tc.constraint_type = 'PRIMARY KEY'
        ORDER BY tc.table_name, kcu.ordinal_position;
    """)
    
    primary_keys = {}
    for row in cursor.fetchall():
        table_name, column_name, constraint_type = row
        if table_name not in primary_keys:
            primary_keys[table_name] = []
        primary_keys[table_name].append(column_name)
    
    # 获取外键信息
    cursor.execute("""
        SELECT 
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu 
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'public'
          AND tc.constraint_type = 'FOREIGN KEY';
    """)
    
    foreign_keys = {}
    for row in cursor.fetchall():
        table_name, column_name, foreign_table, foreign_column = row
        if table_name not in foreign_keys:
            foreign_keys[table_name] = []
        foreign_keys[table_name].append({
            'column': column_name,
            'foreign_table': foreign_table,
            'foreign_column': foreign_column
        })
    
    cursor.close()
    conn.close()
    
    return primary_keys, foreign_keys

def analyze_database_differences():
    """分析本地和OVS数据库的差异"""
    print("=== 分析数据库结构差异 ===")
    
    # 获取本地数据库结构
    print("正在获取本地数据库结构...")
    local_tables = get_table_columns(LOCAL_DB_URL)
    local_pk, local_fk = get_table_constraints(LOCAL_DB_URL)
    print(f"✅ 本地数据库: {len(local_tables)} 个表")
    
    # 获取OVS数据库结构
    print("正在获取pma_db_ovs数据库结构...")
    try:
        ovs_tables = get_table_columns(OVS_DB_URL)
        ovs_pk, ovs_fk = get_table_constraints(OVS_DB_URL)
        print(f"✅ pma_db_ovs数据库: {len(ovs_tables)} 个表")
    except Exception as e:
        print(f"❌ 无法连接pma_db_ovs数据库: {str(e)}")
        return None
    
    # 分析差异
    differences = {
        'missing_tables': [],      # OVS缺失的表
        'extra_tables': [],        # OVS多出的表
        'table_differences': {}    # 表结构差异
    }
    
    local_table_names = set(local_tables.keys())
    ovs_table_names = set(ovs_tables.keys())
    
    # 找出缺失和多余的表
    differences['missing_tables'] = list(local_table_names - ovs_table_names)
    differences['extra_tables'] = list(ovs_table_names - local_table_names)
    
    print(f"\n📊 差异分析结果:")
    print(f"  - OVS缺失表: {len(differences['missing_tables'])} 个")
    print(f"  - OVS多余表: {len(differences['extra_tables'])} 个")
    
    if differences['missing_tables']:
        print(f"  缺失的表: {', '.join(differences['missing_tables'])}")
    
    # 对比共同表的列差异
    common_tables = local_table_names & ovs_table_names
    for table_name in common_tables:
        local_columns = {col['column_name']: col for col in local_tables[table_name]}
        ovs_columns = {col['column_name']: col for col in ovs_tables[table_name]}
        
        table_diff = {
            'missing_columns': [],
            'extra_columns': [],
            'column_differences': []
        }
        
        # 找出缺失和多余的列
        local_col_names = set(local_columns.keys())
        ovs_col_names = set(ovs_columns.keys())
        
        table_diff['missing_columns'] = list(local_col_names - ovs_col_names)
        table_diff['extra_columns'] = list(ovs_col_names - local_col_names)
        
        # 对比相同列的属性差异
        common_columns = local_col_names & ovs_col_names
        for col_name in common_columns:
            local_col = local_columns[col_name]
            ovs_col = ovs_columns[col_name]
            
            # 比较关键属性
            if (local_col['data_type'] != ovs_col['data_type'] or
                local_col['is_nullable'] != ovs_col['is_nullable'] or
                local_col['character_maximum_length'] != ovs_col['character_maximum_length']):
                table_diff['column_differences'].append({
                    'column': col_name,
                    'local': local_col,
                    'ovs': ovs_col
                })
        
        # 只有存在差异时才记录
        if (table_diff['missing_columns'] or 
            table_diff['extra_columns'] or 
            table_diff['column_differences']):
            differences['table_differences'][table_name] = table_diff
    
    if differences['table_differences']:
        print(f"  - 表结构差异: {len(differences['table_differences'])} 个表")
    
    return differences, local_tables, local_pk, local_fk

def generate_create_table_sql(table_name, columns, primary_keys):
    """生成创建表的SQL"""
    col_definitions = []
    
    for col in columns:
        col_name = col['column_name']
        data_type = col['data_type']
        
        # 处理数据类型
        if col['character_maximum_length']:
            data_type += f"({col['character_maximum_length']})"
        elif col['numeric_precision'] and col['numeric_scale'] is not None:
            data_type += f"({col['numeric_precision']},{col['numeric_scale']})"
        elif col['numeric_precision']:
            data_type += f"({col['numeric_precision']})"
        
        # 处理可空性
        nullable = "" if col['is_nullable'] == 'YES' else " NOT NULL"
        
        # 处理默认值
        default = ""
        if col['column_default']:
            default = f" DEFAULT {col['column_default']}"
        
        col_definitions.append(f"  {col_name} {data_type}{nullable}{default}")
    
    # 添加主键
    if table_name in primary_keys and primary_keys[table_name]:
        pk_cols = ', '.join(primary_keys[table_name])
        col_definitions.append(f"  PRIMARY KEY ({pk_cols})")
    
    return f"CREATE TABLE {table_name} (\n" + ",\n".join(col_definitions) + "\n);"

def generate_sync_sql(differences, local_tables, local_pk, local_fk):
    """生成同步SQL语句"""
    print("\n=== 生成同步SQL ===")
    
    sql_statements = []
    
    # 1. 创建缺失的表
    for table_name in differences['missing_tables']:
        print(f"  生成创建表SQL: {table_name}")
        columns = local_tables[table_name]
        create_sql = generate_create_table_sql(table_name, columns, local_pk)
        sql_statements.append(create_sql)
    
    # 2. 添加缺失的列
    for table_name, table_diff in differences['table_differences'].items():
        for col_name in table_diff['missing_columns']:
            print(f"  生成添加列SQL: {table_name}.{col_name}")
            # 从本地结构中找到列定义
            local_columns = {col['column_name']: col for col in local_tables[table_name]}
            col_info = local_columns[col_name]
            
            data_type = col_info['data_type']
            if col_info['character_maximum_length']:
                data_type += f"({col_info['character_maximum_length']})"
            elif col_info['numeric_precision'] and col_info['numeric_scale'] is not None:
                data_type += f"({col_info['numeric_precision']},{col_info['numeric_scale']})"
            elif col_info['numeric_precision']:
                data_type += f"({col_info['numeric_precision']})"
            
            nullable = "" if col_info['is_nullable'] == 'YES' else " NOT NULL"
            default = f" DEFAULT {col_info['column_default']}" if col_info['column_default'] else ""
            
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {data_type}{nullable}{default};"
            sql_statements.append(alter_sql)
    
    return sql_statements

def execute_sync_sql(sql_statements):
    """执行同步SQL"""
    if not sql_statements:
        print("✅ 无需执行同步SQL")
        return True
    
    print(f"\n=== 准备执行 {len(sql_statements)} 条同步SQL ===")
    
    # 显示SQL预览
    print("\n将要执行的SQL语句:")
    for i, sql in enumerate(sql_statements, 1):
        # 只显示前几行，避免输出过长
        if i <= 10:
            print(f"{i:2d}. {sql[:100]}{'...' if len(sql) > 100 else ''}")
        elif i == 11:
            print(f"    ... 还有 {len(sql_statements) - 10} 条SQL语句")
    
    # 确认执行
    print(f"\n⚠️ 注意：这些操作将修改pma_db_ovs数据库结构")
    print("这会添加缺失的表和列，不会删除现有数据")
    
    confirm = input(f"\n是否执行以上 {len(sql_statements)} 条SQL语句？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 用户取消执行")
        return False
    
    try:
        print("\n正在连接pma_db_ovs数据库...")
        conn = get_db_connection(OVS_DB_URL)
        cursor = conn.cursor()
        
        print("开始执行同步SQL...")
        success_count = 0
        
        for i, sql in enumerate(sql_statements, 1):
            try:
                print(f"执行第 {i:2d} 条SQL: ", end="", flush=True)
                cursor.execute(sql)
                conn.commit()
                print("✅ 成功")
                success_count += 1
            except Exception as e:
                print(f"❌ 失败: {str(e)}")
                conn.rollback()
                # 继续执行其他SQL
        
        cursor.close()
        conn.close()
        
        print(f"\n📊 执行结果: {success_count}/{len(sql_statements)} 条SQL成功执行")
        
        if success_count == len(sql_statements):
            print("🎉 所有同步SQL执行成功！")
            return True
        else:
            print("⚠️ 部分同步SQL执行失败，请检查错误信息")
            return False
        
    except Exception as e:
        print(f"❌ 连接数据库失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=== 本地数据库结构同步到pma_db_ovs ===")
    print(f"源数据库: {LOCAL_DB_URL}")
    print(f"目标数据库: {OVS_DB_URL.replace(OVS_DB_URL.split('@')[0].split(':')[-1], '***')}")
    print()
    
    try:
        # 1. 备份OVS数据库
        backup_file = backup_ovs_database()
        if not backup_file:
            print("❌ 备份失败，建议修复备份问题后再同步")
            confirm = input("是否跳过备份继续同步？(y/N): ")
            if confirm.lower() != 'y':
                return
        print()
        
        # 2. 分析数据库差异
        analysis_result = analyze_database_differences()
        if analysis_result is None:
            return
        
        differences, local_tables, local_pk, local_fk = analysis_result
        
        # 3. 检查是否需要同步
        total_changes = (len(differences['missing_tables']) + 
                        sum(len(td['missing_columns']) for td in differences['table_differences'].values()))
        
        if total_changes == 0:
            print("\n✅ pma_db_ovs数据库结构已经是最新的，无需同步")
            return
        
        print(f"\n📋 需要同步 {total_changes} 项更改")
        
        # 4. 生成同步SQL
        sql_statements = generate_sync_sql(differences, local_tables, local_pk, local_fk)
        
        # 5. 保存SQL到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sql_file = f"pma_db_ovs_sync_{timestamp}.sql"
        
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write("-- pma_db_ovs数据库结构同步SQL\n")
            f.write(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- 源数据库: {LOCAL_DB_URL}\n")
            f.write(f"-- 目标数据库: pma_db_ovs\n\n")
            
            for sql in sql_statements:
                f.write(sql + "\n\n")
        
        print(f"\n📄 同步SQL已保存到: {sql_file}")
        
        # 6. 执行同步
        success = execute_sync_sql(sql_statements)
        
        if success:
            print(f"\n🎉 数据库结构同步完成！")
            if backup_file:
                print(f"📁 备份文件: {backup_file}")
            print(f"📄 同步SQL: {sql_file}")
        else:
            print(f"\n⚠️ 数据库同步未完全成功")
            if backup_file:
                print(f"📁 备份文件: {backup_file}")
            print(f"📄 同步SQL: {sql_file}")
    
    except Exception as e:
        print(f"❌ 执行过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 
"""
将本地数据库结构同步到 pma_db_ovs 数据库
先备份目标数据库，然后安全地同步结构

Created: 2025-06-27
Author: Assistant
Purpose: 安全地将本地数据库结构同步到pma_db_ovs数据库
"""

import os
import sys
import psycopg2
import json
from datetime import datetime
from urllib.parse import urlparse

# 数据库连接配置
LOCAL_DB_URL = os.getenv('DATABASE_URL', 'postgresql://nijie:@localhost:5432/pma_local')
OVS_DB_URL = 'postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs'

def parse_db_url(db_url):
    """解析数据库URL"""
    parsed = urlparse(db_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password
    }

def get_db_connection(db_url):
    """获取数据库连接"""
    db_config = parse_db_url(db_url)
    return psycopg2.connect(**db_config)

def backup_ovs_database():
    """备份OVS数据库"""
    print("=== 备份pma_db_ovs数据库 ===")
    
    # 创建备份目录
    backup_dir = "ovs_db_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/pma_db_ovs_backup_{timestamp}.sql"
    
    # 解析数据库配置
    db_config = parse_db_url(OVS_DB_URL)
    
    # 使用pg_dump备份
    dump_cmd = [
        'pg_dump',
        f"--host={db_config['host']}",
        f"--port={db_config['port']}",
        f"--username={db_config['user']}",
        f"--dbname={db_config['database']}",
        '--verbose',
        '--clean',
        '--no-owner',
        '--no-privileges',
        '--format=plain',
        f"--file={backup_file}"
    ]
    
    # 设置密码环境变量
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    try:
        import subprocess
        print(f"正在备份pma_db_ovs数据库到: {backup_file}")
        result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ pma_db_ovs数据库备份成功: {backup_file}")
            
            # 创建备份信息文件
            info_file = f"{backup_dir}/pma_db_ovs_backup_info_{timestamp}.md"
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"# pma_db_ovs数据库备份信息\n\n")
                f.write(f"**备份时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**源数据库**: {db_config['host']}:{db_config['port']}/{db_config['database']}\n")
                f.write(f"**备份文件**: {backup_file}\n")
                f.write(f"**备份大小**: {os.path.getsize(backup_file)} 字节\n\n")
                f.write("## 备份说明\n")
                f.write("- 这是在数据库结构同步前的完整备份\n")
                f.write("- 包含所有表结构和数据\n")
                f.write("- 可用于紧急恢复\n")
            
            return backup_file
        else:
            print(f"❌ 备份失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 备份过程出错: {str(e)}")
        return None

def get_table_columns(db_url):
    """获取数据库表的列信息"""
    conn = get_db_connection(db_url)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.is_nullable,
            c.column_default,
            c.ordinal_position
        FROM information_schema.tables t
        JOIN information_schema.columns c ON t.table_name = c.table_name
        WHERE t.table_schema = 'public' AND c.table_schema = 'public'
        ORDER BY t.table_name, c.ordinal_position;
    """)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # 按表组织数据
    tables = {}
    for row in results:
        table_name = row[0]
        if table_name not in tables:
            tables[table_name] = []
        tables[table_name].append({
            'column_name': row[1],
            'data_type': row[2],
            'character_maximum_length': row[3],
            'numeric_precision': row[4],
            'numeric_scale': row[5],
            'is_nullable': row[6],
            'column_default': row[7],
            'ordinal_position': row[8]
        })
    
    return tables

def get_table_constraints(db_url):
    """获取表的约束信息"""
    conn = get_db_connection(db_url)
    cursor = conn.cursor()
    
    # 获取主键信息
    cursor.execute("""
        SELECT 
            tc.table_name,
            kcu.column_name,
            tc.constraint_type
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_schema = 'public'
          AND tc.constraint_type = 'PRIMARY KEY'
        ORDER BY tc.table_name, kcu.ordinal_position;
    """)
    
    primary_keys = {}
    for row in cursor.fetchall():
        table_name, column_name, constraint_type = row
        if table_name not in primary_keys:
            primary_keys[table_name] = []
        primary_keys[table_name].append(column_name)
    
    # 获取外键信息
    cursor.execute("""
        SELECT 
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu 
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'public'
          AND tc.constraint_type = 'FOREIGN KEY';
    """)
    
    foreign_keys = {}
    for row in cursor.fetchall():
        table_name, column_name, foreign_table, foreign_column = row
        if table_name not in foreign_keys:
            foreign_keys[table_name] = []
        foreign_keys[table_name].append({
            'column': column_name,
            'foreign_table': foreign_table,
            'foreign_column': foreign_column
        })
    
    cursor.close()
    conn.close()
    
    return primary_keys, foreign_keys

def analyze_database_differences():
    """分析本地和OVS数据库的差异"""
    print("=== 分析数据库结构差异 ===")
    
    # 获取本地数据库结构
    print("正在获取本地数据库结构...")
    local_tables = get_table_columns(LOCAL_DB_URL)
    local_pk, local_fk = get_table_constraints(LOCAL_DB_URL)
    print(f"✅ 本地数据库: {len(local_tables)} 个表")
    
    # 获取OVS数据库结构
    print("正在获取pma_db_ovs数据库结构...")
    try:
        ovs_tables = get_table_columns(OVS_DB_URL)
        ovs_pk, ovs_fk = get_table_constraints(OVS_DB_URL)
        print(f"✅ pma_db_ovs数据库: {len(ovs_tables)} 个表")
    except Exception as e:
        print(f"❌ 无法连接pma_db_ovs数据库: {str(e)}")
        return None
    
    # 分析差异
    differences = {
        'missing_tables': [],      # OVS缺失的表
        'extra_tables': [],        # OVS多出的表
        'table_differences': {}    # 表结构差异
    }
    
    local_table_names = set(local_tables.keys())
    ovs_table_names = set(ovs_tables.keys())
    
    # 找出缺失和多余的表
    differences['missing_tables'] = list(local_table_names - ovs_table_names)
    differences['extra_tables'] = list(ovs_table_names - local_table_names)
    
    print(f"\n📊 差异分析结果:")
    print(f"  - OVS缺失表: {len(differences['missing_tables'])} 个")
    print(f"  - OVS多余表: {len(differences['extra_tables'])} 个")
    
    if differences['missing_tables']:
        print(f"  缺失的表: {', '.join(differences['missing_tables'])}")
    
    # 对比共同表的列差异
    common_tables = local_table_names & ovs_table_names
    for table_name in common_tables:
        local_columns = {col['column_name']: col for col in local_tables[table_name]}
        ovs_columns = {col['column_name']: col for col in ovs_tables[table_name]}
        
        table_diff = {
            'missing_columns': [],
            'extra_columns': [],
            'column_differences': []
        }
        
        # 找出缺失和多余的列
        local_col_names = set(local_columns.keys())
        ovs_col_names = set(ovs_columns.keys())
        
        table_diff['missing_columns'] = list(local_col_names - ovs_col_names)
        table_diff['extra_columns'] = list(ovs_col_names - local_col_names)
        
        # 对比相同列的属性差异
        common_columns = local_col_names & ovs_col_names
        for col_name in common_columns:
            local_col = local_columns[col_name]
            ovs_col = ovs_columns[col_name]
            
            # 比较关键属性
            if (local_col['data_type'] != ovs_col['data_type'] or
                local_col['is_nullable'] != ovs_col['is_nullable'] or
                local_col['character_maximum_length'] != ovs_col['character_maximum_length']):
                table_diff['column_differences'].append({
                    'column': col_name,
                    'local': local_col,
                    'ovs': ovs_col
                })
        
        # 只有存在差异时才记录
        if (table_diff['missing_columns'] or 
            table_diff['extra_columns'] or 
            table_diff['column_differences']):
            differences['table_differences'][table_name] = table_diff
    
    if differences['table_differences']:
        print(f"  - 表结构差异: {len(differences['table_differences'])} 个表")
    
    return differences, local_tables, local_pk, local_fk

def generate_create_table_sql(table_name, columns, primary_keys):
    """生成创建表的SQL"""
    col_definitions = []
    
    for col in columns:
        col_name = col['column_name']
        data_type = col['data_type']
        
        # 处理数据类型
        if col['character_maximum_length']:
            data_type += f"({col['character_maximum_length']})"
        elif col['numeric_precision'] and col['numeric_scale'] is not None:
            data_type += f"({col['numeric_precision']},{col['numeric_scale']})"
        elif col['numeric_precision']:
            data_type += f"({col['numeric_precision']})"
        
        # 处理可空性
        nullable = "" if col['is_nullable'] == 'YES' else " NOT NULL"
        
        # 处理默认值
        default = ""
        if col['column_default']:
            default = f" DEFAULT {col['column_default']}"
        
        col_definitions.append(f"  {col_name} {data_type}{nullable}{default}")
    
    # 添加主键
    if table_name in primary_keys and primary_keys[table_name]:
        pk_cols = ', '.join(primary_keys[table_name])
        col_definitions.append(f"  PRIMARY KEY ({pk_cols})")
    
    return f"CREATE TABLE {table_name} (\n" + ",\n".join(col_definitions) + "\n);"

def generate_sync_sql(differences, local_tables, local_pk, local_fk):
    """生成同步SQL语句"""
    print("\n=== 生成同步SQL ===")
    
    sql_statements = []
    
    # 1. 创建缺失的表
    for table_name in differences['missing_tables']:
        print(f"  生成创建表SQL: {table_name}")
        columns = local_tables[table_name]
        create_sql = generate_create_table_sql(table_name, columns, local_pk)
        sql_statements.append(create_sql)
    
    # 2. 添加缺失的列
    for table_name, table_diff in differences['table_differences'].items():
        for col_name in table_diff['missing_columns']:
            print(f"  生成添加列SQL: {table_name}.{col_name}")
            # 从本地结构中找到列定义
            local_columns = {col['column_name']: col for col in local_tables[table_name]}
            col_info = local_columns[col_name]
            
            data_type = col_info['data_type']
            if col_info['character_maximum_length']:
                data_type += f"({col_info['character_maximum_length']})"
            elif col_info['numeric_precision'] and col_info['numeric_scale'] is not None:
                data_type += f"({col_info['numeric_precision']},{col_info['numeric_scale']})"
            elif col_info['numeric_precision']:
                data_type += f"({col_info['numeric_precision']})"
            
            nullable = "" if col_info['is_nullable'] == 'YES' else " NOT NULL"
            default = f" DEFAULT {col_info['column_default']}" if col_info['column_default'] else ""
            
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {data_type}{nullable}{default};"
            sql_statements.append(alter_sql)
    
    return sql_statements

def execute_sync_sql(sql_statements):
    """执行同步SQL"""
    if not sql_statements:
        print("✅ 无需执行同步SQL")
        return True
    
    print(f"\n=== 准备执行 {len(sql_statements)} 条同步SQL ===")
    
    # 显示SQL预览
    print("\n将要执行的SQL语句:")
    for i, sql in enumerate(sql_statements, 1):
        # 只显示前几行，避免输出过长
        if i <= 10:
            print(f"{i:2d}. {sql[:100]}{'...' if len(sql) > 100 else ''}")
        elif i == 11:
            print(f"    ... 还有 {len(sql_statements) - 10} 条SQL语句")
    
    # 确认执行
    print(f"\n⚠️ 注意：这些操作将修改pma_db_ovs数据库结构")
    print("这会添加缺失的表和列，不会删除现有数据")
    
    confirm = input(f"\n是否执行以上 {len(sql_statements)} 条SQL语句？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 用户取消执行")
        return False
    
    try:
        print("\n正在连接pma_db_ovs数据库...")
        conn = get_db_connection(OVS_DB_URL)
        cursor = conn.cursor()
        
        print("开始执行同步SQL...")
        success_count = 0
        
        for i, sql in enumerate(sql_statements, 1):
            try:
                print(f"执行第 {i:2d} 条SQL: ", end="", flush=True)
                cursor.execute(sql)
                conn.commit()
                print("✅ 成功")
                success_count += 1
            except Exception as e:
                print(f"❌ 失败: {str(e)}")
                conn.rollback()
                # 继续执行其他SQL
        
        cursor.close()
        conn.close()
        
        print(f"\n📊 执行结果: {success_count}/{len(sql_statements)} 条SQL成功执行")
        
        if success_count == len(sql_statements):
            print("🎉 所有同步SQL执行成功！")
            return True
        else:
            print("⚠️ 部分同步SQL执行失败，请检查错误信息")
            return False
        
    except Exception as e:
        print(f"❌ 连接数据库失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=== 本地数据库结构同步到pma_db_ovs ===")
    print(f"源数据库: {LOCAL_DB_URL}")
    print(f"目标数据库: {OVS_DB_URL.replace(OVS_DB_URL.split('@')[0].split(':')[-1], '***')}")
    print()
    
    try:
        # 1. 备份OVS数据库
        backup_file = backup_ovs_database()
        if not backup_file:
            print("❌ 备份失败，建议修复备份问题后再同步")
            confirm = input("是否跳过备份继续同步？(y/N): ")
            if confirm.lower() != 'y':
                return
        print()
        
        # 2. 分析数据库差异
        analysis_result = analyze_database_differences()
        if analysis_result is None:
            return
        
        differences, local_tables, local_pk, local_fk = analysis_result
        
        # 3. 检查是否需要同步
        total_changes = (len(differences['missing_tables']) + 
                        sum(len(td['missing_columns']) for td in differences['table_differences'].values()))
        
        if total_changes == 0:
            print("\n✅ pma_db_ovs数据库结构已经是最新的，无需同步")
            return
        
        print(f"\n📋 需要同步 {total_changes} 项更改")
        
        # 4. 生成同步SQL
        sql_statements = generate_sync_sql(differences, local_tables, local_pk, local_fk)
        
        # 5. 保存SQL到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sql_file = f"pma_db_ovs_sync_{timestamp}.sql"
        
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write("-- pma_db_ovs数据库结构同步SQL\n")
            f.write(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- 源数据库: {LOCAL_DB_URL}\n")
            f.write(f"-- 目标数据库: pma_db_ovs\n\n")
            
            for sql in sql_statements:
                f.write(sql + "\n\n")
        
        print(f"\n📄 同步SQL已保存到: {sql_file}")
        
        # 6. 执行同步
        success = execute_sync_sql(sql_statements)
        
        if success:
            print(f"\n🎉 数据库结构同步完成！")
            if backup_file:
                print(f"📁 备份文件: {backup_file}")
            print(f"📄 同步SQL: {sql_file}")
        else:
            print(f"\n⚠️ 数据库同步未完全成功")
            if backup_file:
                print(f"📁 备份文件: {backup_file}")
            print(f"📄 同步SQL: {sql_file}")
    
    except Exception as e:
        print(f"❌ 执行过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 