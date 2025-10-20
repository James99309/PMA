#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库Schema对比脚本
对比本地数据库和云端sp8d数据库的schema差异，识别本地新增但未同步到云端的字段
"""
import sys, os
import re
from collections import defaultdict

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
from sqlalchemy import inspect


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


def parse_cloud_schema_from_sql(sql_file_path):
    """从SQL备份文件解析云端数据库schema"""
    print("\n" + "=" * 80)
    print("☁️  解析云端数据库Schema")
    print("=" * 80)

    if not os.path.exists(sql_file_path):
        print(f"❌ SQL备份文件不存在: {sql_file_path}")
        return {}

    print(f"📄 读取文件: {sql_file_path}")

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    schema = {}

    # 匹配CREATE TABLE语句
    # 正则表达式匹配: CREATE TABLE table_name ( ... );
    create_table_pattern = re.compile(
        r'CREATE TABLE (?:public\.)?(\w+)\s*\((.*?)\);',
        re.DOTALL | re.IGNORECASE
    )

    for match in create_table_pattern.finditer(sql_content):
        table_name = match.group(1)
        columns_text = match.group(2)

        # 解析列定义
        columns = {}

        # 按逗号分割列定义（忽略括号内的逗号）
        column_lines = []
        current_line = ""
        paren_depth = 0

        for char in columns_text:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                column_lines.append(current_line.strip())
                current_line = ""
                continue
            current_line += char

        if current_line.strip():
            column_lines.append(current_line.strip())

        # 解析每一列
        for line in column_lines:
            line = line.strip()

            # 跳过约束定义（CONSTRAINT, PRIMARY KEY, FOREIGN KEY等）
            if any(keyword in line.upper() for keyword in ['CONSTRAINT', 'PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE (', 'CHECK (']):
                continue

            # 解析列定义: column_name column_type [NOT NULL] [DEFAULT ...]
            parts = line.split(None, 2)  # 最多分割成3部分
            if len(parts) < 2:
                continue

            col_name = parts[0].strip('"')
            col_type = parts[1]

            # 提取完整类型定义（包括长度、精度等）
            type_match = re.match(r'(\w+)(\([^)]+\))?', col_type)
            if type_match:
                col_type = type_match.group(0)

            # 检查nullable和default
            nullable = 'NOT NULL' not in line.upper()

            default_match = re.search(r'DEFAULT\s+(.+?)(?:\s|$)', line, re.IGNORECASE)
            default_value = default_match.group(1) if default_match else None

            columns[col_name] = {
                'type': col_type,
                'nullable': nullable,
                'default': default_value
            }

        schema[table_name] = columns

    print(f"✅ 云端数据库共有 {len(schema)} 个表")
    return schema


def compare_schemas(local_schema, cloud_schema):
    """对比本地和云端schema"""
    print("\n" + "=" * 80)
    print("🔍 对比Schema差异")
    print("=" * 80)

    # 1. 表级别对比
    local_tables = set(local_schema.keys())
    cloud_tables = set(cloud_schema.keys())

    tables_only_local = local_tables - cloud_tables
    tables_only_cloud = cloud_tables - local_tables
    common_tables = local_tables & cloud_tables

    print(f"\n📋 表级别对比:")
    print(f"   - 共同表: {len(common_tables)}")
    print(f"   - 仅本地有: {len(tables_only_local)}")
    print(f"   - 仅云端有: {len(tables_only_cloud)}")

    if tables_only_local:
        print(f"\n⚠️  本地新增的表（未同步到云端）:")
        for table in sorted(tables_only_local):
            print(f"   - {table} ({len(local_schema[table])} 列)")

    if tables_only_cloud:
        print(f"\n⚠️  云端独有的表（本地已删除）:")
        for table in sorted(tables_only_cloud):
            print(f"   - {table}")

    # 2. 列级别对比
    print(f"\n📊 列级别对比（共同表）:")

    columns_diff = defaultdict(lambda: {
        'only_local': [],
        'only_cloud': [],
        'type_diff': []
    })

    for table in sorted(common_tables):
        local_cols = set(local_schema[table].keys())
        cloud_cols = set(cloud_schema[table].keys())

        cols_only_local = local_cols - cloud_cols
        cols_only_cloud = cloud_cols - local_cols
        common_cols = local_cols & cloud_cols

        if cols_only_local:
            columns_diff[table]['only_local'] = sorted(cols_only_local)

        if cols_only_cloud:
            columns_diff[table]['only_cloud'] = sorted(cols_only_cloud)

        # 检查类型差异
        for col in common_cols:
            local_type = local_schema[table][col]['type']
            cloud_type = cloud_schema[table][col]['type']

            # 规范化类型比较（忽略大小写和某些细微差异）
            local_type_norm = local_type.upper().replace('DOUBLE_PRECISION', 'DOUBLE PRECISION')
            cloud_type_norm = cloud_type.upper().replace('DOUBLE_PRECISION', 'DOUBLE PRECISION')

            if local_type_norm != cloud_type_norm:
                columns_diff[table]['type_diff'].append({
                    'column': col,
                    'local_type': local_type,
                    'cloud_type': cloud_type
                })

    # 输出列差异
    has_diff = False

    for table in sorted(columns_diff.keys()):
        diff = columns_diff[table]
        if diff['only_local'] or diff['only_cloud'] or diff['type_diff']:
            if not has_diff:
                has_diff = True

            print(f"\n🔧 表 {table}:")

            if diff['only_local']:
                print(f"   ⚠️  本地新增的列（未同步到云端）:")
                for col in diff['only_local']:
                    col_info = local_schema[table][col]
                    nullable_str = "NULL" if col_info['nullable'] else "NOT NULL"
                    default_str = f" DEFAULT {col_info['default']}" if col_info['default'] else ""
                    print(f"      - {col}: {col_info['type']} {nullable_str}{default_str}")

            if diff['only_cloud']:
                print(f"   ⚠️  云端独有的列（本地已删除）:")
                for col in diff['only_cloud']:
                    print(f"      - {col}")

            if diff['type_diff']:
                print(f"   ⚠️  类型差异:")
                for item in diff['type_diff']:
                    print(f"      - {item['column']}: 本地={item['local_type']}, 云端={item['cloud_type']}")

    if not has_diff:
        print("   ✅ 所有共同表的列定义完全一致")

    return {
        'tables_only_local': tables_only_local,
        'tables_only_cloud': tables_only_cloud,
        'columns_diff': dict(columns_diff)
    }


def generate_sync_suggestions(diff_results, local_schema):
    """生成同步建议SQL"""
    print("\n" + "=" * 80)
    print("💡 同步建议")
    print("=" * 80)

    suggestions = []

    # 1. 新增表的建议
    if diff_results['tables_only_local']:
        print(f"\n📝 需要在云端创建的表:")
        for table in sorted(diff_results['tables_only_local']):
            print(f"   - {table}")
            suggestions.append(f"-- 需要手动导出表 {table} 的CREATE TABLE语句")

    # 2. 新增列的建议
    columns_diff = diff_results['columns_diff']

    print(f"\n📝 需要在云端添加的列:")
    has_columns = False

    for table in sorted(columns_diff.keys()):
        only_local = columns_diff[table].get('only_local', [])
        if only_local:
            has_columns = True
            print(f"\n   表 {table}:")
            for col in only_local:
                col_info = local_schema[table][col]
                nullable_str = "" if col_info['nullable'] else " NOT NULL"
                default_str = f" DEFAULT {col_info['default']}" if col_info['default'] else ""

                sql = f"ALTER TABLE {table} ADD COLUMN {col} {col_info['type']}{nullable_str}{default_str};"
                print(f"      {sql}")
                suggestions.append(sql)

    if not has_columns:
        print("   ✅ 无需添加新列")

    return suggestions


def main():
    """主函数"""
    app = create_app()

    with app.app_context():
        # 1. 提取本地schema
        local_schema = extract_local_schema()

        # 2. 解析云端schema
        project_root = get_project_root()
        cloud_sql_file = os.path.join(
            project_root,
            'cloud_db_backups',
            'pma_db_sp8d_backup_20251017_123426.sql'
        )
        cloud_schema = parse_cloud_schema_from_sql(cloud_sql_file)

        # 3. 对比schema
        diff_results = compare_schemas(local_schema, cloud_schema)

        # 4. 生成同步建议
        suggestions = generate_sync_suggestions(diff_results, local_schema)

        # 5. 总结
        print("\n" + "=" * 80)
        print("📊 对比总结")
        print("=" * 80)
        print(f"✅ 本地数据库: {len(local_schema)} 个表")
        print(f"✅ 云端数据库: {len(cloud_schema)} 个表")
        print(f"⚠️  本地新增表: {len(diff_results['tables_only_local'])} 个")
        print(f"⚠️  本地删除表: {len(diff_results['tables_only_cloud'])} 个")

        total_new_columns = sum(
            len(diff.get('only_local', []))
            for diff in diff_results['columns_diff'].values()
        )
        print(f"⚠️  本地新增列: {total_new_columns} 个")

        print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
