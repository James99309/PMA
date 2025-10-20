#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端project_customer_associations表的customer_type字段"""
import sys
import os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from sqlalchemy import create_engine, text, inspect

# 云端数据库配置
CLOUD_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': '6543',
    'database': 'postgres',
    'user': 'postgres.iqcyimnjtnmomvfuwjzw',
    'password': 'towsys-coGdoq-6gofdi'
}

CLOUD_DB_URL = f"postgresql://{CLOUD_DB_CONFIG['user']}:{CLOUD_DB_CONFIG['password']}@" \
               f"{CLOUD_DB_CONFIG['host']}:{CLOUD_DB_CONFIG['port']}/{CLOUD_DB_CONFIG['database']}"

cloud_engine = create_engine(CLOUD_DB_URL)

print("=" * 80)
print("云端 project_customer_associations 表结构")
print("=" * 80)

cloud_inspector = inspect(cloud_engine)
cloud_cols = cloud_inspector.get_columns('project_customer_associations')

for col in cloud_cols:
    nullable = "NULL" if col['nullable'] else "NOT NULL"
    default = f"DEFAULT {col.get('default')}" if col.get('default') else ""
    print(f"{col['name']:25} {str(col['type']):20} {nullable:10} {default}")

print("\n" + "=" * 80)
print("customer_type 字段详细检查")
print("=" * 80)

with cloud_engine.connect() as conn:
    # 检查约束信息
    result = conn.execute(text("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'project_customer_associations'
        AND column_name = 'customer_type'
    """))

    row = result.fetchone()
    if row:
        print(f"字段名: {row[0]}")
        print(f"数据类型: {row[1]}")
        print(f"可空: {row[2]}")
        print(f"默认值: {row[3]}")

    # 检查现有数据
    print(f"\n当前数据统计:")
    result = conn.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(customer_type) as with_type,
            COUNT(*) FILTER (WHERE customer_type IS NULL) as null_count
        FROM project_customer_associations
    """))

    row = result.fetchone()
    print(f"  总记录数: {row[0]}")
    print(f"  有customer_type的: {row[1]}")
    print(f"  NULL值数量: {row[2]}")

    # 显示customer_type值的分布
    print(f"\ncustomer_type 值分布:")
    result = conn.execute(text("""
        SELECT
            customer_type,
            COUNT(*) as count
        FROM project_customer_associations
        GROUP BY customer_type
        ORDER BY count DESC
        LIMIT 10
    """))

    for row in result:
        value = row[0] if row[0] is not None else "(NULL)"
        print(f"  {value}: {row[1]}")
