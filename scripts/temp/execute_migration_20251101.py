#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""专用迁移执行脚本 - 绕过完整应用加载"""

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

os.chdir(get_project_root())
sys.path.insert(0, get_project_root())

# 直接执行迁移SQL，不加载应用
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# 加载 .env 文件
env_path = os.path.join(get_project_root(), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ 已加载环境配置: {env_path}")
else:
    print("⚠️  未找到 .env 文件")

# 从环境变量获取数据库URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ 未找到DATABASE_URL环境变量")
    sys.exit(1)

# 解析数据库URL
url = urlparse(database_url)
db_name = url.path[1:]  # 去掉开头的 /
db_user = url.username
db_password = url.password
db_host = url.hostname
db_port = url.port or 5432

print("=" * 60)
print("🔧 执行数据库迁移")
print("=" * 60)
print(f"数据库主机: {db_host}")
print(f"数据库端口: {db_port}")
print(f"数据库名称: {db_name}")
print(f"用户名: {db_user}")
print("=" * 60)

try:
    # 连接数据库
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    conn.autocommit = False
    cursor = conn.cursor()

    # 检查字段是否已存在
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='products' AND column_name='code_definition_snapshot'
    """)
    exists = cursor.fetchone()

    if exists:
        print("⚠️  字段 code_definition_snapshot 已存在，跳过迁移")
    else:
        # 执行迁移：添加字段
        print("📝 添加 code_definition_snapshot 字段到 products 表...")
        cursor.execute("""
            ALTER TABLE products
            ADD COLUMN code_definition_snapshot JSON
        """)

        # 检查 alembic_version 表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alembic_version'
            )
        """)
        version_table_exists = cursor.fetchone()[0]

        if version_table_exists:
            # 更新 alembic_version 表
            print("📝 更新 alembic_version 记录...")
            cursor.execute("""
                UPDATE alembic_version
                SET version_num = '20251101_add_code_snapshot'
            """)
        else:
            print("⚠️  alembic_version 表不存在，无法记录版本号")
            print("   建议稍后手动创建该表")

        conn.commit()
        print("✅ 迁移执行成功！")

        # 验证字段已添加
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name='products' AND column_name='code_definition_snapshot'
        """)
        result = cursor.fetchone()
        if result:
            print(f"✅ 验证成功：字段 {result[0]} (类型: {result[1]}) 已添加")

    cursor.close()
    conn.close()
    print("=" * 60)

except Exception as e:
    print(f"❌ 迁移执行失败: {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    sys.exit(1)
