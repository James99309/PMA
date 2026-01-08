#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比OVS和本地的permission_modules表"""
import psycopg2

OVS_DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
LOCAL_DB_URL = 'postgresql://nijie@localhost:5432/pma_local'

def get_permission_modules(conn, db_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT module_id, name, supports_content_filter
        FROM permission_modules
        WHERE module_id IN ('project', 'quotation', 'customer', 'pricing_order', 'order')
        ORDER BY module_id
    """)
    results = {row[0]: row[2] for row in cursor.fetchall()}
    cursor.close()
    return results

print("="*60)
print("对比 permission_modules.supports_content_filter")
print("="*60)

local_conn = psycopg2.connect(LOCAL_DB_URL)
ovs_conn = psycopg2.connect(OVS_DB_URL)

local_data = get_permission_modules(local_conn, "本地")
ovs_data = get_permission_modules(ovs_conn, "OVS")

print(f"\n{'模块':<20} | {'本地':^10} | {'OVS':^10} | 状态")
print("-"*60)

for module in sorted(set(local_data.keys()) | set(ovs_data.keys())):
    local_val = local_data.get(module, None)
    ovs_val = ovs_data.get(module, None)

    if local_val == ovs_val:
        status = "✓ 相同"
    else:
        status = "⚠️ 不同"

    local_str = "True" if local_val else "False"
    ovs_str = "True" if ovs_val else "False"

    print(f"{module:<20} | {local_str:^10} | {ovs_str:^10} | {status}")

local_conn.close()
ovs_conn.close()
