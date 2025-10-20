#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查project_customer_associations表结构差异"""
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

# 本地数据库配置
LOCAL_DB_URL = "postgresql://nijie:nijie20240729@localhost:5432/pma_db_sp8d"

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

local_engine = create_engine(LOCAL_DB_URL)
cloud_engine = create_engine(CLOUD_DB_URL)

print("=" * 80)
print("本地 project_customer_associations 表结构")
print("=" * 80)

local_inspector = inspect(local_engine)
local_cols = {col['name']: col for col in local_inspector.get_columns('project_customer_associations')}

for name, col in sorted(local_cols.items()):
    nullable = "NULL" if col['nullable'] else "NOT NULL"
    default = f"DEFAULT {col.get('default', 'N/A')}" if col.get('default') else ""
    print(f"{name:25} {str(col['type']):20} {nullable:10} {default}")

print("\n" + "=" * 80)
print("云端 project_customer_associations 表结构")
print("=" * 80)

cloud_inspector = inspect(cloud_engine)
cloud_cols = {col['name']: col for col in cloud_inspector.get_columns('project_customer_associations')}

for name, col in sorted(cloud_cols.items()):
    nullable = "NULL" if col['nullable'] else "NOT NULL"
    default = f"DEFAULT {col.get('default', 'N/A')}" if col.get('default') else ""
    print(f"{name:25} {str(col['type']):20} {nullable:10} {default}")

print("\n" + "=" * 80)
print("字段差异分析")
print("=" * 80)

# 找出云端缺失的字段
missing_in_cloud = set(local_cols.keys()) - set(cloud_cols.keys())
if missing_in_cloud:
    print(f"\n云端缺失的字段:")
    for field in sorted(missing_in_cloud):
        col = local_cols[field]
        print(f"  - {field}: {col['type']}")

# 找出本地缺失的字段
missing_in_local = set(cloud_cols.keys()) - set(local_cols.keys())
if missing_in_local:
    print(f"\n本地缺失的字段:")
    for field in sorted(missing_in_local):
        col = cloud_cols[field]
        print(f"  - {field}: {col['type']}")

# 找出类型或约束不同的字段
print(f"\n字段约束差异:")
for field in set(local_cols.keys()) & set(cloud_cols.keys()):
    local_col = local_cols[field]
    cloud_col = cloud_cols[field]

    differences = []

    # 比较可空性
    if local_col['nullable'] != cloud_col['nullable']:
        local_null = "NULL" if local_col['nullable'] else "NOT NULL"
        cloud_null = "NULL" if cloud_col['nullable'] else "NOT NULL"
        differences.append(f"可空性: 本地={local_null}, 云端={cloud_null}")

    # 比较默认值
    local_default = local_col.get('default')
    cloud_default = cloud_col.get('default')
    if str(local_default) != str(cloud_default):
        differences.append(f"默认值: 本地={local_default}, 云端={cloud_default}")

    if differences:
        print(f"\n  {field}:")
        for diff in differences:
            print(f"    - {diff}")

# 检查云端customer_type字段的详细信息
print("\n" + "=" * 80)
print("customer_type 字段详细信息")
print("=" * 80)

if 'customer_type' in cloud_cols:
    col = cloud_cols['customer_type']
    print(f"云端 customer_type:")
    print(f"  类型: {col['type']}")
    print(f"  可空: {col['nullable']}")
    print(f"  默认值: {col.get('default', 'N/A')}")

# 查询云端现有数据的customer_type分布
with cloud_engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            customer_type,
            COUNT(*) as count
        FROM project_customer_associations
        GROUP BY customer_type
        ORDER BY count DESC
    """))

    print(f"\n云端现有数据的customer_type分布:")
    for row in result:
        print(f"  {row[0] or '(NULL)'}: {row[1]}")
