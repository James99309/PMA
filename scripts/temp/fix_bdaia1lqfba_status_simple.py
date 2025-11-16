#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复产品BDAIA1LQFBA的状态（从已入库改回申请入库）- 简化版"""

import sys, os
import json
from datetime import datetime

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
print("修复产品BDAIA1LQFBA状态")
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

    # 查找产品
    cursor.execute("""
        SELECT id, mn_code, model, status, stage_history
        FROM dev_products
        WHERE mn_code = 'BDAIA1LQFBA'
    """)
    result = cursor.fetchone()

    if not result:
        print("\n❌ 未找到产品BDAIA1LQFBA")
        cursor.close()
        conn.close()
        sys.exit(1)

    dev_product_id, mn_code, model, status, stage_history = result

    print(f"\n📋 当前产品信息:")
    print(f"   ID: {dev_product_id}")
    print(f"   MN编号: {mn_code}")
    print(f"   型号: {model}")
    print(f"   当前状态: {status}")

    # 检查是否已实际入库
    cursor.execute("""
        SELECT id
        FROM products
        WHERE source_dev_product_id = %s
    """, (dev_product_id,))
    warehoused = cursor.fetchone()

    if warehoused:
        print(f"\n⚠️  警告：该产品已经实际入库到产品库（Product#{warehoused[0]}）")
        print(f"   修复状态后需要检查数据一致性")
        response = input("\n是否继续修复状态？(y/N): ")
        if response.lower() != 'y':
            print("已取消")
            cursor.close()
            conn.close()
            sys.exit(0)

    # 修复状态和阶段历史
    old_status = status

    # 清理阶段历史
    if stage_history:
        # 移除已入库阶段的记录
        stage_history = [
            record for record in stage_history
            if record.get('stage') != 'stored'
        ]

        # 清除申请入库阶段的结束日期
        for record in reversed(stage_history):
            if record.get('stage') == 'apply_storage' and record.get('endDate'):
                record['endDate'] = None
                break

    print(f"\n✅ 修复操作:")
    print(f"   状态: {old_status} → 申请入库")
    print(f"   阶段历史: 已清理'已入库'记录，移除'申请入库'的结束日期")

    # 执行更新
    cursor.execute("""
        UPDATE dev_products
        SET status = '申请入库',
            stage_history = %s,
            updated_at = %s
        WHERE id = %s
    """, (json.dumps(stage_history), datetime.now(), dev_product_id))

    conn.commit()

    print("\n✅ 状态修复成功！")
    print("\n📝 现在可以从产品详情页提交入库审批了")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)

except Exception as e:
    print(f"\n❌ 修复失败: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    sys.exit(1)
