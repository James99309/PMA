#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证产品编码快照功能"""

import sys, os

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
print("🔍 验证产品编码快照功能")
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

    # 1. 验证数据库字段
    print("\n1️⃣  验证数据库字段...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name='products' AND column_name='code_definition_snapshot'
    """)
    field_info = cursor.fetchone()
    if field_info:
        print(f"   ✅ 字段存在: {field_info[0]} ({field_info[1]}, nullable={field_info[2]})")
    else:
        print("   ❌ 字段不存在！")

    # 2. 验证迁移版本
    print("\n2️⃣  验证迁移版本记录...")
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()
    if version:
        print(f"   ✅ 当前迁移版本: {version[0]}")
    else:
        print("   ⚠️  未找到迁移版本记录")

    # 3. 验证模型导入
    print("\n3️⃣  验证模型代码...")
    try:
        from app.models.product import Product
        from app.models.product_code import ProductCode

        # 检查Product模型是否有code_definition_snapshot字段
        if hasattr(Product, 'code_definition_snapshot'):
            print("   ✅ Product模型包含 code_definition_snapshot 字段")
        else:
            print("   ❌ Product模型缺少 code_definition_snapshot 字段")

        # 检查ProductCode模型是否有generate_snapshot方法
        if hasattr(ProductCode, 'generate_snapshot'):
            print("   ✅ ProductCode模型包含 generate_snapshot() 方法")
        else:
            print("   ❌ ProductCode模型缺少 generate_snapshot() 方法")

    except Exception as e:
        print(f"   ❌ 模型导入失败: {e}")

    # 4. 统计产品编码数据
    print("\n4️⃣  统计数据...")
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    print(f"   📊 产品总数: {product_count}")

    cursor.execute("SELECT COUNT(*) FROM products WHERE code_definition_snapshot IS NOT NULL")
    snapshot_count = cursor.fetchone()[0]
    print(f"   📊 有快照的产品: {snapshot_count}")
    print(f"   📊 无快照的产品: {product_count - snapshot_count}")

    if snapshot_count > 0:
        cursor.execute("""
            SELECT product_mn, code_definition_snapshot->>'full_code'
            FROM products
            WHERE code_definition_snapshot IS NOT NULL
            LIMIT 3
        """)
        examples = cursor.fetchall()
        print("\n   示例快照:")
        for ex in examples:
            print(f"      - 产品MN: {ex[0]}, 快照编码: {ex[1]}")

    print("\n" + "=" * 80)
    print("✅ 验证完成！")
    print("=" * 80)
    print("\n📝 下一步:")
    print("   1. 创建新产品编码，验证快照自动生成")
    print("   2. 访问产品详情页，查看编码分解展示")
    print("   3. 检查快照JSON结构是否完整")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
