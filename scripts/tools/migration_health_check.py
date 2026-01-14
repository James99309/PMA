#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移健康检查工具
对比本地 SQLAlchemy 模型与目标数据库结构，输出差异报告

使用方法：
    python3 scripts/tools/migration_health_check.py --target=ovs
    python3 scripts/tools/migration_health_check.py --target=sp8d --fix --dry-run
    python3 scripts/tools/migration_health_check.py --target=ovs --fix
    python3 scripts/tools/migration_health_check.py --list-targets

功能：
    - 检查缺失的表
    - 检查缺失的字段
    - 生成修复 SQL
    - 可选执行修复
"""

import os
import sys
import argparse
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

PROJECT_ROOT = get_project_root()
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# 设置环境变量避免 WeasyPrint 问题
os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib'

import psycopg2
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine


# SQLAlchemy 类型到 PostgreSQL 类型的映射
TYPE_MAPPING = {
    'INTEGER': 'INTEGER',
    'BIGINT': 'BIGINT',
    'SMALLINT': 'SMALLINT',
    'VARCHAR': 'VARCHAR',
    'TEXT': 'TEXT',
    'BOOLEAN': 'BOOLEAN',
    'DATE': 'DATE',
    'DATETIME': 'TIMESTAMP',
    'TIMESTAMP': 'TIMESTAMP',
    'FLOAT': 'DOUBLE PRECISION',
    'NUMERIC': 'NUMERIC',
    'JSON': 'JSON',
    'JSONB': 'JSONB',
}


def get_sqlalchemy_type_str(col_type):
    """将 SQLAlchemy 列类型转换为 PostgreSQL 类型字符串"""
    type_name = type(col_type).__name__.upper()

    if type_name == 'VARCHAR' or type_name == 'STRING':
        length = getattr(col_type, 'length', None)
        if length:
            return f'VARCHAR({length})'
        return 'VARCHAR'
    elif type_name == 'NUMERIC':
        precision = getattr(col_type, 'precision', None)
        scale = getattr(col_type, 'scale', None)
        if precision and scale:
            return f'NUMERIC({precision},{scale})'
        return 'NUMERIC'
    elif type_name in TYPE_MAPPING:
        return TYPE_MAPPING[type_name]
    else:
        return type_name


def load_models():
    """加载所有 SQLAlchemy 模型"""
    print("加载模型定义...")

    # 导入 Flask 应用以获取模型
    from app import create_app, db
    app = create_app()

    with app.app_context():
        # 获取所有已注册的模型
        models = {}
        for mapper in db.Model.registry.mappers:
            model_class = mapper.class_
            table_name = model_class.__tablename__ if hasattr(model_class, '__tablename__') else None
            if table_name:
                models[table_name] = {
                    'class': model_class,
                    'columns': {}
                }

                # 获取列信息
                for column in mapper.columns:
                    col_name = column.name
                    col_type = get_sqlalchemy_type_str(column.type)
                    col_nullable = column.nullable
                    col_default = column.default
                    col_fk = None

                    # 获取外键信息
                    if column.foreign_keys:
                        fk = list(column.foreign_keys)[0]
                        col_fk = str(fk.target_fullname)

                    models[table_name]['columns'][col_name] = {
                        'type': col_type,
                        'nullable': col_nullable,
                        'default': col_default,
                        'foreign_key': col_fk
                    }

        return models


def get_db_schema(db_url):
    """获取数据库实际结构"""
    print("连接目标数据库...")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    tables = {row[0] for row in cursor.fetchall()}

    # 获取所有列
    schema = {}
    for table in tables:
        cursor.execute(f"""
            SELECT column_name, data_type, character_maximum_length,
                   numeric_precision, numeric_scale, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table}'
        """)

        schema[table] = {}
        for row in cursor.fetchall():
            col_name, data_type, char_len, num_prec, num_scale, nullable, default = row

            # 构建类型字符串
            if data_type == 'character varying':
                type_str = f'VARCHAR({char_len})' if char_len else 'VARCHAR'
            elif data_type == 'numeric' and num_prec and num_scale:
                type_str = f'NUMERIC({num_prec},{num_scale})'
            elif data_type == 'timestamp without time zone':
                type_str = 'TIMESTAMP'
            elif data_type == 'double precision':
                type_str = 'DOUBLE PRECISION'
            else:
                type_str = data_type.upper()

            schema[table][col_name] = {
                'type': type_str,
                'nullable': nullable == 'YES'
            }

    # 获取 alembic 版本
    try:
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()
        alembic_version = version[0] if version else 'N/A'
    except:
        alembic_version = 'N/A'

    cursor.close()
    conn.close()

    return schema, alembic_version, len(tables)


def compare_schemas(models, db_schema):
    """对比模型和数据库结构"""
    differences = {
        'missing_tables': [],
        'missing_columns': [],
        'extra_tables': [],
        'type_mismatches': []
    }

    model_tables = set(models.keys())
    db_tables = set(db_schema.keys())

    # 忽略的系统表
    ignore_tables = {'alembic_version', 'spatial_ref_sys'}

    # 检查缺失的表
    for table in model_tables:
        if table not in db_tables and table not in ignore_tables:
            differences['missing_tables'].append(table)

    # 检查多余的表（在数据库中但不在模型中）
    for table in db_tables:
        if table not in model_tables and table not in ignore_tables:
            # 只报告，不作为问题
            differences['extra_tables'].append(table)

    # 检查缺失的列
    for table, model_info in models.items():
        if table in db_schema:
            db_columns = set(db_schema[table].keys())
            model_columns = set(model_info['columns'].keys())

            for col in model_columns:
                if col not in db_columns:
                    col_info = model_info['columns'][col]
                    differences['missing_columns'].append({
                        'table': table,
                        'column': col,
                        'type': col_info['type'],
                        'nullable': col_info['nullable'],
                        'foreign_key': col_info['foreign_key']
                    })

    return differences


def generate_fix_sql(differences, models):
    """生成修复 SQL"""
    sql_statements = []

    # 生成创建表的 SQL（简化版，实际需要完整定义）
    for table in differences['missing_tables']:
        if table in models:
            columns_sql = []
            for col_name, col_info in models[table]['columns'].items():
                col_def = f"{col_name} {col_info['type']}"
                if not col_info['nullable']:
                    col_def += " NOT NULL"
                if col_info['foreign_key']:
                    ref_table = col_info['foreign_key'].split('.')[0]
                    col_def += f" REFERENCES {ref_table}(id)"
                columns_sql.append(col_def)

            # 添加主键
            sql = f"CREATE TABLE IF NOT EXISTS {table} (\n    "
            sql += ",\n    ".join(columns_sql)
            sql += "\n);"
            sql_statements.append(sql)

    # 生成添加列的 SQL
    for col_diff in differences['missing_columns']:
        table = col_diff['table']
        column = col_diff['column']
        col_type = col_diff['type']
        nullable = col_diff['nullable']
        fk = col_diff['foreign_key']

        sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
        if not nullable:
            sql += " NOT NULL"
        if fk:
            ref_table = fk.split('.')[0]
            sql += f" REFERENCES {ref_table}(id)"
        sql += ";"
        sql_statements.append(sql)

    return sql_statements


def execute_fixes(db_url, sql_statements, dry_run=True):
    """执行修复 SQL"""
    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN - 以下 SQL 将被执行（实际未执行）:")
        print("=" * 60)
        for sql in sql_statements:
            print(f"\n{sql}")
        return True

    print("\n" + "=" * 60)
    print("执行修复 SQL...")
    print("=" * 60)

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    conn.autocommit = True

    success_count = 0
    error_count = 0

    for sql in sql_statements:
        try:
            print(f"\n执行: {sql[:80]}...")
            cursor.execute(sql)
            print("  ✅ 成功")
            success_count += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            error_count += 1

    cursor.close()
    conn.close()

    print(f"\n完成: {success_count} 成功, {error_count} 失败")
    return error_count == 0


def print_report(target_name, target_info, db_schema, alembic_version, table_count, differences):
    """打印检查报告"""
    print("\n")
    print("🔍 迁移健康检查报告")
    print("━" * 60)
    print(f"目标: {target_info['name']}")
    print(f"描述: {target_info['description']}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("📊 数据库状态")
    print(f"   迁移版本: {alembic_version}")
    print(f"   表数量: {table_count}")
    print()

    # 统计问题数量
    total_issues = len(differences['missing_tables']) + len(differences['missing_columns'])

    if total_issues == 0:
        print("✅ 数据库结构与模型完全一致!")
        return

    print(f"⚠️ 发现 {total_issues} 个差异:")
    print()

    # 缺失的表
    if differences['missing_tables']:
        print("❌ 缺失的表:")
        for table in sorted(differences['missing_tables']):
            print(f"   - {table}")
        print()

    # 缺失的列
    if differences['missing_columns']:
        print("❌ 缺失的字段:")
        for col in differences['missing_columns']:
            fk_info = f" (FK -> {col['foreign_key']})" if col['foreign_key'] else ""
            print(f"   - {col['table']}.{col['column']} ({col['type']}{fk_info})")
        print()

    # 多余的表（仅供参考）
    if differences['extra_tables']:
        print("ℹ️ 数据库中额外的表（可能是旧表或备份）:")
        for table in sorted(differences['extra_tables'])[:10]:  # 只显示前10个
            print(f"   - {table}")
        if len(differences['extra_tables']) > 10:
            print(f"   ... 还有 {len(differences['extra_tables']) - 10} 个")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='迁移健康检查工具 - 对比模型与数据库结构',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --target=ovs              检查 OVS 数据库
  %(prog)s --target=sp8d --fix       检查并生成修复 SQL
  %(prog)s --target=ovs --fix --execute  检查并执行修复
  %(prog)s --list-targets            列出所有可用目标
        """
    )

    parser.add_argument('--target', '-t',
                        help='目标数据库 (ovs, sp8d, synology, local)')
    parser.add_argument('--list-targets', '-l', action='store_true',
                        help='列出所有可用的目标数据库')
    parser.add_argument('--fix', '-f', action='store_true',
                        help='生成修复 SQL')
    parser.add_argument('--execute', '-e', action='store_true',
                        help='执行修复 SQL（需要与 --fix 一起使用）')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='仅显示将要执行的 SQL（默认）')

    args = parser.parse_args()

    # 导入目标配置
    from db_targets import TARGETS, get_target, list_targets

    if args.list_targets:
        list_targets()
        return

    if not args.target:
        print("错误: 请指定目标数据库 (--target)")
        list_targets()
        return

    try:
        target_info = get_target(args.target)
    except ValueError as e:
        print(f"错误: {e}")
        list_targets()
        return

    # 加载模型
    models = load_models()
    print(f"已加载 {len(models)} 个模型")

    # 获取数据库结构
    db_schema, alembic_version, table_count = get_db_schema(target_info['url'])
    print(f"已获取数据库结构: {table_count} 个表")

    # 对比
    differences = compare_schemas(models, db_schema)

    # 打印报告
    print_report(args.target, target_info, db_schema, alembic_version, table_count, differences)

    # 生成修复 SQL
    if args.fix:
        sql_statements = generate_fix_sql(differences, models)

        if not sql_statements:
            print("无需修复，数据库结构完整。")
            return

        if args.execute and not args.dry_run:
            # 确认执行
            print("\n" + "=" * 60)
            print("⚠️  警告: 即将执行以下修复操作")
            print("=" * 60)
            for sql in sql_statements:
                print(f"  {sql[:70]}...")

            confirm = input("\n确认执行? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                execute_fixes(target_info['url'], sql_statements, dry_run=False)
            else:
                print("已取消执行")
        else:
            execute_fixes(target_info['url'], sql_statements, dry_run=True)


if __name__ == '__main__':
    main()
