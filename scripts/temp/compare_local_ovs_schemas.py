#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地数据库与云端OVS数据库Schema对比脚本
对比本地数据库和云端pma_db_ovs数据库的schema差异，识别需要迁移的变更
"""
import sys, os
import re
from collections import defaultdict
from datetime import datetime

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

from app import create_app, db
from sqlalchemy import create_engine, inspect
import psycopg2

# OVS数据库连接信息
OVS_URL = "postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"


def extract_local_schema():
    """提取本地数据库完整schema"""
    print("=" * 80)
    print("📊 提取本地数据库Schema")
    print("=" * 80)

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    schema = {}
    for table_name in tables:
        columns = inspector.get_columns(table_name)
        schema[table_name] = {
            col['name']: {
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': str(col['default']) if col['default'] is not None else None
            }
            for col in columns
        }

    print(f"✅ 本地数据库共有 {len(tables)} 个表")
    return schema


def extract_ovs_schema():
    """提取云端OVS数据库schema"""
    print("\n" + "=" * 80)
    print("☁️  提取云端OVS数据库Schema")
    print("=" * 80)

    try:
        ovs_engine = create_engine(OVS_URL)
        inspector = inspect(ovs_engine)
        tables = inspector.get_table_names()

        schema = {}
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            schema[table_name] = {
                col['name']: {
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': str(col['default']) if col['default'] is not None else None
                }
                for col in columns
            }

        print(f"✅ 云端OVS数据库共有 {len(tables)} 个表")
        ovs_engine.dispose()
        return schema

    except Exception as e:
        print(f"❌ 提取OVS Schema失败: {e}")
        return None


def compare_schemas(local_schema, ovs_schema):
    """对比本地和OVS数据库schema"""
    print("\n" + "=" * 80)
    print("🔍 Schema对比分析")
    print("=" * 80)

    differences = {
        'new_tables': [],        # 本地有但OVS没有的表
        'missing_tables': [],    # OVS有但本地没有的表
        'new_columns': defaultdict(list),     # 本地新增的字段
        'missing_columns': defaultdict(list), # OVS有但本地没有的字段
        'type_changes': defaultdict(list)     # 字段类型变更
    }

    local_tables = set(local_schema.keys())
    ovs_tables = set(ovs_schema.keys())

    # 检查表级别差异
    differences['new_tables'] = sorted(local_tables - ovs_tables)
    differences['missing_tables'] = sorted(ovs_tables - local_tables)

    # 检查字段级别差异
    common_tables = local_tables & ovs_tables

    for table in common_tables:
        local_cols = set(local_schema[table].keys())
        ovs_cols = set(ovs_schema[table].keys())

        # 新增字段
        new_cols = local_cols - ovs_cols
        if new_cols:
            for col in sorted(new_cols):
                differences['new_columns'][table].append({
                    'name': col,
                    'type': local_schema[table][col]['type'],
                    'nullable': local_schema[table][col]['nullable']
                })

        # 缺失字段
        missing_cols = ovs_cols - local_cols
        if missing_cols:
            for col in sorted(missing_cols):
                differences['missing_columns'][table].append({
                    'name': col,
                    'type': ovs_schema[table][col]['type'],
                    'nullable': ovs_schema[table][col]['nullable']
                })

        # 字段类型变更
        common_cols = local_cols & ovs_cols
        for col in common_cols:
            local_type = local_schema[table][col]['type']
            ovs_type = ovs_schema[table][col]['type']

            # 规范化类型字符串进行比较
            local_type_normalized = re.sub(r'\(\d+\)', '', local_type).upper()
            ovs_type_normalized = re.sub(r'\(\d+\)', '', ovs_type).upper()

            if local_type_normalized != ovs_type_normalized:
                differences['type_changes'][table].append({
                    'column': col,
                    'local_type': local_type,
                    'ovs_type': ovs_type
                })

    return differences


def print_differences(differences):
    """打印schema差异报告"""
    print("\n" + "=" * 80)
    print("📋 Schema差异报告")
    print("=" * 80)

    has_differences = False

    # 新增的表
    if differences['new_tables']:
        has_differences = True
        print(f"\n🆕 本地新增的表 ({len(differences['new_tables'])}个):")
        for table in differences['new_tables']:
            print(f"   - {table}")

    # 缺失的表
    if differences['missing_tables']:
        has_differences = True
        print(f"\n⚠️  OVS有但本地没有的表 ({len(differences['missing_tables'])}个):")
        for table in differences['missing_tables']:
            print(f"   - {table}")

    # 新增的字段
    if differences['new_columns']:
        has_differences = True
        print(f"\n🆕 本地新增的字段:")
        for table, columns in sorted(differences['new_columns'].items()):
            print(f"\n   表: {table}")
            for col in columns:
                nullable_str = "NULL" if col['nullable'] else "NOT NULL"
                print(f"      - {col['name']}: {col['type']} {nullable_str}")

    # 缺失的字段
    if differences['missing_columns']:
        has_differences = True
        print(f"\n⚠️  OVS有但本地没有的字段:")
        for table, columns in sorted(differences['missing_columns'].items()):
            print(f"\n   表: {table}")
            for col in columns:
                nullable_str = "NULL" if col['nullable'] else "NOT NULL"
                print(f"      - {col['name']}: {col['type']} {nullable_str}")

    # 类型变更
    if differences['type_changes']:
        has_differences = True
        print(f"\n🔄 字段类型变更:")
        for table, changes in sorted(differences['type_changes'].items()):
            print(f"\n   表: {table}")
            for change in changes:
                print(f"      - {change['column']}: {change['ovs_type']} → {change['local_type']}")

    if not has_differences:
        print("\n✅ 本地数据库与OVS数据库Schema完全一致！")
        return False

    return True


def generate_migration_suggestions(differences):
    """根据差异生成迁移建议"""
    print("\n" + "=" * 80)
    print("💡 迁移建议")
    print("=" * 80)

    total_changes = (
        len(differences['new_tables']) +
        len(differences['new_columns']) +
        len(differences['type_changes'])
    )

    if total_changes == 0:
        print("\n✅ 无需迁移！")
        return

    print(f"\n检测到 {total_changes} 项需要同步到OVS的变更")

    # 建议策略
    if len(differences['new_tables']) > 0 or len(differences['type_changes']) > 0:
        print("\n⚠️  检测到表结构重大变更（新表或字段类型变更）")
        print("   建议策略：")
        print("   1. 先检查迁移历史状态（运行 check_ovs_migration_status.py）")
        print("   2. 使用Flask-Migrate标准升级流程")
        print("   3. 如失败，考虑手动SQL迁移")
    else:
        print("\n✓ 仅有字段新增，变更相对安全")
        print("   建议策略：")
        print("   1. 检查迁移历史状态")
        print("   2. 优先使用Flask-Migrate标准升级")

    # 生成简单的SQL预览
    if differences['new_columns']:
        print("\n📝 新增字段的SQL预览（仅供参考）:")
        for table, columns in sorted(differences['new_columns'].items()):
            for col in columns:
                nullable_str = "NULL" if col['nullable'] else "NOT NULL"
                default_str = f" DEFAULT {col.get('default')}" if col.get('default') else ""
                print(f"   ALTER TABLE {table} ADD COLUMN {col['name']} {col['type']} {nullable_str}{default_str};")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🔍 本地数据库 vs 云端OVS数据库 Schema对比")
    print("=" * 80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建Flask应用上下文
    app = create_app()
    with app.app_context():
        # 提取本地schema
        local_schema = extract_local_schema()

        # 提取OVS schema
        ovs_schema = extract_ovs_schema()

        if ovs_schema is None:
            print("\n❌ 无法连接到OVS数据库，对比终止")
            return

        # 对比schema
        differences = compare_schemas(local_schema, ovs_schema)

        # 打印差异
        has_diff = print_differences(differences)

        # 生成迁移建议
        if has_diff:
            generate_migration_suggestions(differences)

    print("\n" + "=" * 80)
    print("✅ Schema对比完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
