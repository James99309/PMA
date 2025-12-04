#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证OVS约束同步结果
"""
import os
import sys

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

PROJECT_ROOT = get_project_root()
sys.path.insert(0, PROJECT_ROOT)

import psycopg2

# 数据库配置
LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pma_dev',
    'user': 'postgres',
    'password': 'postgres'
}

# 正确的OVS数据库配置（根据CLAUDE-DATABASE.md）
OVS_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.pqzviljbpfoqvyfulakl',
    'password': 'nyjrIc-gubcu4-rukhoc',
    'sslmode': 'require'
}

def get_column_info(cursor, schema='public'):
    """获取所有列的约束信息"""
    query = """
        SELECT
            c.table_name,
            c.column_name,
            c.is_nullable,
            c.column_default
        FROM information_schema.columns c
        JOIN information_schema.tables t
            ON c.table_name = t.table_name
            AND c.table_schema = t.table_schema
        WHERE c.table_schema = %s
            AND t.table_type = 'BASE TABLE'
            AND c.table_name NOT LIKE 'pg_%%'
            AND c.table_name NOT IN ('alembic_version', 'spatial_ref_sys')
        ORDER BY c.table_name, c.ordinal_position
    """
    cursor.execute(query, (schema,))
    return {(row[0], row[1]): {'nullable': row[2], 'default': row[3]} for row in cursor.fetchall()}


def main():
    print("="*60)
    print("OVS 约束同步验证")
    print("="*60)

    # 连接数据库
    local_conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    ovs_conn = psycopg2.connect(**OVS_DB_CONFIG)

    local_cursor = local_conn.cursor()
    ovs_cursor = ovs_conn.cursor()

    # 获取列信息
    print("\n获取本地数据库列信息...")
    local_cols = get_column_info(local_cursor)
    print(f"  共 {len(local_cols)} 列")

    print("获取OVS数据库列信息...")
    ovs_cols = get_column_info(ovs_cursor)
    print(f"  共 {len(ovs_cols)} 列")

    # 对比关键表的约束
    key_tables = [
        'companies', 'dev_products', 'expense_details', 'expenses',
        'permissions', 'product_categories', 'product_code_field_options',
        'product_code_fields', 'product_relations', 'product_specs',
        'projects', 'quotation_details', 'quotations', 'settlement_orders',
        'specification_dictionary', 'approval_branch_condition',
        'approval_record', 'approval_step', 'dev_product_milestones',
        'stage_attachments', 'stage_dependencies', 'stage_reviews'
    ]

    nullable_diff = []
    default_diff = []

    for table in key_tables:
        for (t, col), local_info in local_cols.items():
            if t != table:
                continue
            ovs_info = ovs_cols.get((t, col))
            if not ovs_info:
                continue

            # 检查nullable
            if local_info['nullable'] != ovs_info['nullable']:
                nullable_diff.append({
                    'table': t,
                    'column': col,
                    'local': local_info['nullable'],
                    'ovs': ovs_info['nullable']
                })

            # 检查default (简化比较)
            local_def = local_info['default']
            ovs_def = ovs_info['default']

            # 标准化比较
            def normalize_default(val):
                if val is None:
                    return None
                val = str(val).strip()
                # 移除类型转换
                if '::' in val:
                    val = val.split('::')[0]
                # 移除引号
                val = val.strip("'\"")
                return val

            local_norm = normalize_default(local_def)
            ovs_norm = normalize_default(ovs_def)

            if local_norm != ovs_norm:
                default_diff.append({
                    'table': t,
                    'column': col,
                    'local': local_def,
                    'ovs': ovs_def
                })

    # 输出结果
    print("\n" + "="*60)
    print("验证结果")
    print("="*60)

    if nullable_diff:
        print(f"\n⚠️ nullable 差异: {len(nullable_diff)} 处")
        for d in nullable_diff[:10]:
            print(f"  {d['table']}.{d['column']}: 本地={d['local']}, OVS={d['ovs']}")
        if len(nullable_diff) > 10:
            print(f"  ... 还有 {len(nullable_diff) - 10} 处")
    else:
        print("\n✅ nullable 约束完全一致")

    if default_diff:
        print(f"\n⚠️ default 差异: {len(default_diff)} 处")
        for d in default_diff[:10]:
            print(f"  {d['table']}.{d['column']}")
            print(f"    本地: {d['local']}")
            print(f"    OVS:  {d['ovs']}")
        if len(default_diff) > 10:
            print(f"  ... 还有 {len(default_diff) - 10} 处")
    else:
        print("\n✅ default 值约束完全一致")

    total_diff = len(nullable_diff) + len(default_diff)
    print(f"\n总计差异: {total_diff} 处")

    if total_diff == 0:
        print("\n🎉 所有关键表的约束已完全同步！")
    else:
        print("\n⚠️ 仍存在部分差异，可能需要进一步检查")

    # 关闭连接
    local_cursor.close()
    ovs_cursor.close()
    local_conn.close()
    ovs_conn.close()


if __name__ == '__main__':
    main()
