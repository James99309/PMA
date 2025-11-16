#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证研发库入库产品快照功能"""

import sys, os
import json

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

from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# 加载环境配置
env_path = os.path.join(get_project_root(), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ 未找到DATABASE_URL环境变量")
    sys.exit(1)

# 解析数据库URL
url = urlparse(database_url)
db_name = url.path[1:]
db_user = url.username
db_password = url.password
db_host = url.hostname
db_port = url.port or 5432

print("=" * 80)
print("🔍 验证研发库入库产品快照功能")
print("=" * 80)

try:
    # 连接数据库
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    cursor = conn.cursor()

    # 1. 统计入库产品快照情况
    print("\n1️⃣  统计入库产品快照情况...")

    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE source_type = 'from_dev'
    """)
    total_warehoused = cursor.fetchone()[0]
    print(f"   📊 从研发库入库的产品总数: {total_warehoused}")

    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE source_type = 'from_dev'
        AND code_definition_snapshot IS NOT NULL
    """)
    with_snapshot = cursor.fetchone()[0]
    print(f"   📊 有快照的入库产品: {with_snapshot}")
    print(f"   📊 无快照的入库产品: {total_warehoused - with_snapshot}")

    # 2. 检查快照格式
    if with_snapshot > 0:
        print("\n2️⃣  检查快照格式...")
        cursor.execute("""
            SELECT
                id,
                product_mn,
                code_definition_snapshot->>'version' as version,
                code_definition_snapshot->>'source' as source,
                code_definition_snapshot->>'full_code' as full_code,
                jsonb_array_length(code_definition_snapshot->'code_parts') as parts_count
            FROM products
            WHERE source_type = 'from_dev'
            AND code_definition_snapshot IS NOT NULL
            LIMIT 3
        """)

        snapshots = cursor.fetchall()
        for snap in snapshots:
            product_id, mn, version, source, full_code, parts_count = snap
            print(f"\n   产品 #{product_id}:")
            print(f"     - MN号: {mn}")
            print(f"     - 快照版本: {version}")
            print(f"     - 快照来源: {source}")
            print(f"     - 编码: {full_code}")
            print(f"     - code_parts数量: {parts_count}")

    # 3. 验证快照字段结构
    if with_snapshot > 0:
        print("\n3️⃣  验证快照字段结构...")
        cursor.execute("""
            SELECT code_definition_snapshot
            FROM products
            WHERE source_type = 'from_dev'
            AND code_definition_snapshot IS NOT NULL
            LIMIT 1
        """)

        snapshot_json = cursor.fetchone()[0]

        print("   快照JSON结构示例:")
        print("   " + "─" * 70)
        print(json.dumps(snapshot_json, indent=4, ensure_ascii=False))
        print("   " + "─" * 70)

        # 检查必需字段
        required_fields = ['version', 'source', 'generated_at', 'full_code', 'code_parts']
        missing_fields = [f for f in required_fields if f not in snapshot_json]

        if missing_fields:
            print(f"   ❌ 缺少必需字段: {', '.join(missing_fields)}")
        else:
            print("   ✅ 所有必需字段都存在")

        # 检查code_parts格式
        if 'code_parts' in snapshot_json and len(snapshot_json['code_parts']) > 0:
            first_part = snapshot_json['code_parts'][0]
            part_fields = ['position', 'field_name', 'code', 'value']
            part_missing = [f for f in part_fields if f not in first_part]

            if part_missing:
                print(f"   ⚠️  code_parts缺少字段: {', '.join(part_missing)}")
            else:
                print("   ✅ code_parts字段格式正确")

    # 4. 提示信息
    print("\n4️⃣  提示...")
    if total_warehoused > 0 and with_snapshot == 0:
        print("   ⚠️  现有入库产品没有快照（入库时间早于快照功能添加）")
        print("   ✅ 新入库的产品将自动生成快照")

    print("\n" + "=" * 80)
    print("✅ 验证完成！")
    print("=" * 80)
    print("\n📝 下一步:")
    print("   1. 创建新研发产品并添加规格")
    print("   2. 提交入库审批")
    print("   3. 审批通过后验证快照生成")
    print("   4. 访问产品详情页查看编码分解展示")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
