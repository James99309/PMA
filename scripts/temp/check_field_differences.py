#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查本地数据库和云端SP8D数据库的字段差异
只读操作，不修改任何数据
"""
import sys
import os
from datetime import datetime
import json

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

import psycopg2
from dotenv import load_dotenv

# 加载环境变量
env_file = os.path.join(get_project_root(), '.env')
load_dotenv(env_file)

# 加载SP8D配置
sp8d_env_file = os.path.join(get_project_root(), '.env.sp8d.backup')
sp8d_config = {}
if os.path.exists(sp8d_env_file):
    with open(sp8d_env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                sp8d_config[key] = value.strip().strip('"').strip("'")


def get_table_columns(conn, schema='public'):
    """获取数据库所有表的字段信息"""
    cursor = conn.cursor()

    query = """
    SELECT
        c.table_name,
        c.column_name,
        c.data_type,
        c.character_maximum_length,
        c.is_nullable,
        c.column_default
    FROM information_schema.columns c
    WHERE c.table_schema = %s
        AND c.table_name NOT LIKE 'alembic%%'
    ORDER BY c.table_name, c.ordinal_position
    """

    cursor.execute(query, (schema,))
    rows = cursor.fetchall()

    # 按表组织数据
    tables = {}
    for row in rows:
        table_name = row[0]
        column_info = {
            'column_name': row[1],
            'data_type': row[2],
            'char_max_length': row[3],
            'is_nullable': row[4],
            'column_default': row[5]
        }

        if table_name not in tables:
            tables[table_name] = []
        tables[table_name].append(column_info)

    cursor.close()
    return tables


def connect_local_db():
    """连接本地数据库"""
    db_host = os.getenv('DATABASE_HOST', 'localhost')
    db_port = os.getenv('DATABASE_PORT', '5432')
    db_name = os.getenv('DATABASE_NAME', 'pma_local')
    db_user = os.getenv('DATABASE_USER', 'nijie')
    db_password = os.getenv('DATABASE_PASSWORD', '')

    print(f"正在连接本地数据库: {db_host}:{db_port}/{db_name}")

    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    return conn


def connect_sp8d_db():
    """连接云端SP8D数据库"""
    db_url = sp8d_config.get('DATABASE_URL', '')

    if not db_url:
        raise ValueError("未找到SP8D数据库配置（DATABASE_URL）")

    # 解析DATABASE_URL
    # postgresql://user:password@host:port/database
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^\?]+)', db_url)
    if not match:
        raise ValueError(f"无法解析DATABASE_URL: {db_url}")

    user, password, host, port, database = match.groups()

    print(f"正在连接云端SP8D数据库: {host}:{port}/{database}")

    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    return conn


def compare_databases():
    """对比两个数据库的字段差异"""
    print("\n" + "="*80)
    print("开始检查本地数据库和云端SP8D数据库的字段差异")
    print("="*80 + "\n")

    # 连接数据库
    try:
        local_conn = connect_local_db()
        print("✅ 本地数据库连接成功\n")
    except Exception as e:
        print(f"❌ 本地数据库连接失败: {str(e)}")
        return

    try:
        sp8d_conn = connect_sp8d_db()
        print("✅ 云端SP8D数据库连接成功\n")
    except Exception as e:
        print(f"❌ 云端SP8D数据库连接失败: {str(e)}")
        local_conn.close()
        return

    # 获取表字段信息
    print("正在获取本地数据库表结构...")
    local_tables = get_table_columns(local_conn)
    print(f"✅ 本地数据库共 {len(local_tables)} 个表\n")

    print("正在获取云端SP8D数据库表结构...")
    sp8d_tables = get_table_columns(sp8d_conn)
    print(f"✅ 云端数据库共 {len(sp8d_tables)} 个表\n")

    # 关闭数据库连接
    local_conn.close()
    sp8d_conn.close()

    # 对比字段差异
    print("\n" + "="*80)
    print("字段差异分析结果")
    print("="*80 + "\n")

    differences = []
    total_missing_fields = 0

    for table_name in sorted(local_tables.keys()):
        local_columns = {col['column_name']: col for col in local_tables[table_name]}

        if table_name not in sp8d_tables:
            print(f"⚠️  表 [{table_name}] 在云端不存在（本地新表）")
            differences.append({
                'table': table_name,
                'status': 'table_missing',
                'columns': list(local_columns.keys())
            })
            continue

        sp8d_columns = {col['column_name']: col for col in sp8d_tables[table_name]}

        # 找出本地有但云端没有的字段
        missing_columns = []
        for col_name, col_info in local_columns.items():
            if col_name not in sp8d_columns:
                missing_columns.append({
                    'name': col_name,
                    'type': col_info['data_type'],
                    'length': col_info['char_max_length'],
                    'nullable': col_info['is_nullable'],
                    'default': col_info['column_default']
                })

        if missing_columns:
            total_missing_fields += len(missing_columns)
            differences.append({
                'table': table_name,
                'status': 'fields_missing',
                'missing_columns': missing_columns
            })

            print(f"📋 表 [{table_name}] - 云端缺少 {len(missing_columns)} 个字段：")
            for col in missing_columns:
                type_str = col['type']
                if col['length']:
                    type_str += f"({col['length']})"

                nullable_str = "NULL" if col['nullable'] == 'YES' else "NOT NULL"
                default_str = f", DEFAULT {col['default']}" if col['default'] else ""

                print(f"   - {col['name']:<30} {type_str:<20} {nullable_str}{default_str}")
            print()

    # 汇总报告
    print("\n" + "="*80)
    print("汇总报告")
    print("="*80 + "\n")

    tables_with_differences = len([d for d in differences if d['status'] == 'fields_missing'])
    new_tables = len([d for d in differences if d['status'] == 'table_missing'])

    print(f"📊 总共检查了 {len(local_tables)} 个表")
    print(f"📊 发现 {tables_with_differences} 个表存在字段差异")
    print(f"📊 发现 {new_tables} 个本地新表在云端不存在")
    print(f"📊 云端总共缺少 {total_missing_fields} 个字段")

    if total_missing_fields == 0 and new_tables == 0:
        print("\n✅ 恭喜！本地和云端数据库结构完全一致，无需迁移。")
    else:
        print(f"\n⚠️  需要迁移 {total_missing_fields} 个字段到云端SP8D数据库")
        if new_tables > 0:
            print(f"⚠️  需要创建 {new_tables} 个新表到云端SP8D数据库")

    # 保存详细报告到JSON文件
    report_file = os.path.join(get_project_root(), 'field_differences_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tables': len(local_tables),
                'tables_with_differences': tables_with_differences,
                'new_tables': new_tables,
                'total_missing_fields': total_missing_fields
            },
            'differences': differences
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📄 详细报告已保存到: {report_file}")
    print("\n" + "="*80)


if __name__ == '__main__':
    try:
        compare_databases()
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
