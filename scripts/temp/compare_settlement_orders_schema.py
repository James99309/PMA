#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比本地和云端的settlement_orders表结构"""
import psycopg2
from psycopg2.extras import RealDictCursor

# 云端SP8D数据库
CLOUD_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

# 本地数据库
LOCAL_URL = "postgresql://nijie:@localhost:5432/pma_local"

def get_table_columns(db_url, db_name):
    """获取表的列信息"""
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'settlement_orders'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        cursor.close()
        conn.close()

        return {col['column_name']: col for col in columns}

    except Exception as e:
        print(f"❌ 连接{db_name}失败: {str(e)}")
        return {}

print("=" * 80)
print("对比 settlement_orders 表结构")
print("=" * 80)

# 获取云端和本地的表结构
print("\n正在获取云端数据库表结构...")
cloud_columns = get_table_columns(CLOUD_URL, "云端SP8D")

print("正在获取本地数据库表结构...")
local_columns = get_table_columns(LOCAL_URL, "本地")

if not cloud_columns and not local_columns:
    print("\n❌ 无法获取任何数据库的表结构")
    exit(1)

# 对比
print(f"\n{'='*80}")
print(f"对比结果:")
print(f"{'='*80}")

print(f"\n云端列数: {len(cloud_columns)}")
print(f"本地列数: {len(local_columns)}")

# 找出只在本地存在的列
only_local = set(local_columns.keys()) - set(cloud_columns.keys())
if only_local:
    print(f"\n⚠️  只在本地存在的列 ({len(only_local)} 个):")
    for col in sorted(only_local):
        col_info = local_columns[col]
        print(f"  - {col:30} {col_info['data_type']:20} (默认值: {col_info['column_default']})")

# 找出只在云端存在的列
only_cloud = set(cloud_columns.keys()) - set(local_columns.keys())
if only_cloud:
    print(f"\n⚠️  只在云端存在的列 ({len(only_cloud)} 个):")
    for col in sorted(only_cloud):
        col_info = cloud_columns[col]
        print(f"  - {col:30} {col_info['data_type']:20}")

# 共同的列
common = set(cloud_columns.keys()) & set(local_columns.keys())
print(f"\n✅ 共同的列: {len(common)} 个")

# 检查currency字段
print(f"\n{'='*80}")
print("currency 字段检查:")
print(f"{'='*80}")

if 'currency' in local_columns:
    print("✅ 本地数据库有 currency 字段")
    print(f"   类型: {local_columns['currency']['data_type']}")
    print(f"   默认值: {local_columns['currency']['column_default']}")
else:
    print("❌ 本地数据库没有 currency 字段")

if 'currency' in cloud_columns:
    print("✅ 云端数据库有 currency 字段")
    print(f"   类型: {cloud_columns['currency']['data_type']}")
    print(f"   默认值: {cloud_columns['currency']['column_default']}")
else:
    print("❌ 云端数据库没有 currency 字段")

# 结论
print(f"\n{'='*80}")
print("结论:")
print(f"{'='*80}")

if 'currency' in local_columns and 'currency' not in cloud_columns:
    print("⚠️  确认：云端数据库缺少 currency 字段！")
    print("   需要在云端数据库添加此字段。")
elif 'currency' in cloud_columns and 'currency' not in local_columns:
    print("⚠️  本地数据库缺少 currency 字段")
elif 'currency' in local_columns and 'currency' in cloud_columns:
    print("✅ 两个数据库都有 currency 字段")
else:
    print("❌ 两个数据库都没有 currency 字段")
