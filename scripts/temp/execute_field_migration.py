#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行SP8D云端数据库字段迁移
"""
import sys
import os
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

import psycopg2
from dotenv import load_dotenv

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


def connect_sp8d_db():
    """连接云端SP8D数据库"""
    db_url = sp8d_config.get('DATABASE_URL', '')

    if not db_url:
        raise ValueError("未找到SP8D数据库配置（DATABASE_URL）")

    # 解析DATABASE_URL
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


def execute_migration():
    """执行字段迁移"""
    print("\n" + "="*80)
    print("开始执行SP8D云端数据库字段迁移")
    print("="*80 + "\n")

    # 读取SQL文件
    sql_file = os.path.join(get_project_root(), 'scripts/temp/field_migration_sp8d.sql')
    print(f"读取SQL文件: {sql_file}")

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 解析SQL语句
    statements = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            statements.append(line)

    sql_statements = ' '.join(statements).split(';')
    sql_statements = [s.strip() for s in sql_statements if s.strip()]

    print(f"✅ 共解析出 {len(sql_statements)} 条SQL语句\n")

    # 连接数据库
    try:
        conn = connect_sp8d_db()
        print("✅ 数据库连接成功\n")
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False

    cursor = conn.cursor()
    success_count = 0
    failed_count = 0

    print("="*80)
    print("执行SQL语句")
    print("="*80 + "\n")

    # 执行每条SQL语句
    for i, sql in enumerate(sql_statements, 1):
        print(f"[{i}/{len(sql_statements)}] 执行: {sql[:60]}...")

        try:
            cursor.execute(sql)
            conn.commit()
            print(f"     ✅ 成功\n")
            success_count += 1
        except Exception as e:
            conn.rollback()
            print(f"     ❌ 失败: {str(e)}\n")
            failed_count += 1

    cursor.close()
    conn.close()

    # 汇总报告
    print("\n" + "="*80)
    print("迁移执行完成")
    print("="*80 + "\n")

    print(f"📊 总共执行 {len(sql_statements)} 条SQL语句")
    print(f"✅ 成功: {success_count} 条")
    print(f"❌ 失败: {failed_count} 条")

    if failed_count == 0:
        print("\n🎉 恭喜！所有字段迁移成功！")
        return True
    else:
        print(f"\n⚠️  有 {failed_count} 条语句执行失败，请检查日志")
        return False


if __name__ == '__main__':
    try:
        success = execute_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
