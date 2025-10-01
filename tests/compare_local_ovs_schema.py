#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比本地数据库和云端OVS数据库的schema差异"""
import sys
import os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from collections import defaultdict

# 数据库连接
LOCAL_DB = 'postgresql://nijie@localhost:5432/pma_local'
OVS_DB = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

def get_table_columns(engine, table_name):
    """获取表的所有列信息"""
    query = text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = :table_name
        AND table_schema = 'public'
        ORDER BY ordinal_position
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {'table_name': table_name})
        return {row[0]: {'type': row[1], 'nullable': row[2], 'default': row[3]}
                for row in result}

def get_all_tables(engine):
    """获取所有表名"""
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        return [row[0] for row in result]

print("=" * 100)
print("  本地数据库 vs 云端OVS数据库 Schema对比")
print("=" * 100)

# 连接数据库
print("\n【1】连接数据库...")
local_engine = create_engine(LOCAL_DB)
ovs_engine = create_engine(OVS_DB)
print("  ✅ 本地数据库连接成功")
print("  ✅ 云端OVS数据库连接成功")

# 获取所有表
print("\n【2】获取表列表...")
local_tables = set(get_all_tables(local_engine))
ovs_tables = set(get_all_tables(ovs_engine))

print(f"  本地数据库: {len(local_tables)} 个表")
print(f"  云端OVS: {len(ovs_tables)} 个表")

# 表差异
tables_only_local = local_tables - ovs_tables
tables_only_ovs = ovs_tables - local_tables
common_tables = local_tables & ovs_tables

if tables_only_local:
    print(f"\n  ⚠️  仅存在于本地的表 ({len(tables_only_local)}):")
    for table in sorted(tables_only_local):
        print(f"    - {table}")

if tables_only_ovs:
    print(f"\n  ⚠️  仅存在于OVS的表 ({len(tables_only_ovs)}):")
    for table in sorted(tables_only_ovs):
        print(f"    - {table}")

# 重点检查审批相关表
approval_tables = [
    'approval_instance',
    'approval_steps',
    'approval_record',
    'approval_process_template',
    'approval_branch_condition'
]

print("\n" + "=" * 100)
print("  【3】审批相关表详细对比")
print("=" * 100)

critical_issues = []

for table in approval_tables:
    if table not in common_tables:
        print(f"\n⚠️  表 {table} 不在两个数据库中都存在")
        continue

    print(f"\n📋 表: {table}")
    print("-" * 100)

    local_cols = get_table_columns(local_engine, table)
    ovs_cols = get_table_columns(ovs_engine, table)

    local_col_names = set(local_cols.keys())
    ovs_col_names = set(ovs_cols.keys())

    # 本地有但OVS没有的列
    cols_only_local = local_col_names - ovs_col_names
    if cols_only_local:
        print(f"\n  ❌ 云端OVS缺失的字段 ({len(cols_only_local)}):")
        for col in sorted(cols_only_local):
            col_info = local_cols[col]
            print(f"    - {col} ({col_info['type']}, nullable={col_info['nullable']})")
            critical_issues.append({
                'table': table,
                'column': col,
                'issue': 'OVS数据库缺失此字段',
                'type': col_info['type']
            })

    # OVS有但本地没有的列
    cols_only_ovs = ovs_col_names - local_col_names
    if cols_only_ovs:
        print(f"\n  ⚠️  OVS有但本地没有的字段 ({len(cols_only_ovs)}):")
        for col in sorted(cols_only_ovs):
            col_info = ovs_cols[col]
            print(f"    - {col} ({col_info['type']}, nullable={col_info['nullable']})")

    # 共同字段的类型差异
    common_cols = local_col_names & ovs_col_names
    type_diffs = []
    for col in common_cols:
        if local_cols[col]['type'] != ovs_cols[col]['type']:
            type_diffs.append(col)

    if type_diffs:
        print(f"\n  ⚠️  字段类型不一致 ({len(type_diffs)}):")
        for col in type_diffs:
            print(f"    - {col}:")
            print(f"        本地: {local_cols[col]['type']}")
            print(f"        OVS: {ovs_cols[col]['type']}")

    if not cols_only_local and not cols_only_ovs and not type_diffs:
        print(f"  ✅ 字段完全一致")

# 检查其他重要表
print("\n" + "=" * 100)
print("  【4】其他重要表检查")
print("=" * 100)

important_tables = [
    'expenses',
    'expense_details',
    'users',
    'projects',
    'quotations',
    'companies',
    'pricing_orders',
    'purchase_orders'
]

for table in important_tables:
    if table not in common_tables:
        continue

    local_cols = get_table_columns(local_engine, table)
    ovs_cols = get_table_columns(ovs_engine, table)

    cols_only_local = set(local_cols.keys()) - set(ovs_cols.keys())
    cols_only_ovs = set(ovs_cols.keys()) - set(local_cols.keys())

    if cols_only_local or cols_only_ovs:
        print(f"\n📋 表: {table}")

        if cols_only_local:
            print(f"  ❌ OVS缺失字段: {', '.join(sorted(cols_only_local))}")
            for col in cols_only_local:
                critical_issues.append({
                    'table': table,
                    'column': col,
                    'issue': 'OVS数据库缺失此字段',
                    'type': local_cols[col]['type']
                })

        if cols_only_ovs:
            print(f"  ⚠️  本地缺失字段: {', '.join(sorted(cols_only_ovs))}")

# 输出关键问题汇总
print("\n" + "=" * 100)
print("  【5】关键问题汇总")
print("=" * 100)

if critical_issues:
    print(f"\n❌ 发现 {len(critical_issues)} 个云端OVS数据库缺失字段的问题:\n")

    # 按表分组
    issues_by_table = defaultdict(list)
    for issue in critical_issues:
        issues_by_table[issue['table']].append(issue)

    for table, issues in sorted(issues_by_table.items()):
        print(f"表: {table}")
        for issue in issues:
            print(f"  ❌ 缺失字段: {issue['column']} ({issue['type']})")
        print()
else:
    print("\n✅ 没有发现云端OVS数据库缺失字段的问题")

# 生成修复SQL
if critical_issues:
    print("\n" + "=" * 100)
    print("  【6】修复SQL脚本")
    print("=" * 100)
    print("\n-- 在云端OVS数据库执行以下SQL添加缺失字段:\n")

    for table, issues in sorted(issues_by_table.items()):
        print(f"-- 表: {table}")
        for issue in issues:
            col = issue['column']
            col_info = None

            # 从本地数据库获取完整字段信息
            if table in approval_tables or table in important_tables:
                local_cols = get_table_columns(local_engine, table)
                col_info = local_cols.get(col)

            if col_info:
                nullable = "NULL" if col_info['nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col_info['default']}" if col_info['default'] else ""
                print(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_info['type'].upper()} {nullable} {default};")
            else:
                print(f"-- ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} <TYPE>; -- 需要手动指定类型")
        print()

print("\n" + "=" * 100)
print("  对比完成")
print("=" * 100)

# 关闭连接
local_engine.dispose()
ovs_engine.dispose()
