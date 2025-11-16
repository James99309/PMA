#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复错误的已入库状态（未实际入库但状态为已入库）"""

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
print("修复错误的已入库状态")
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

    # 查找状态为已入库但实际未入库的产品
    cursor.execute("""
        SELECT
            dp.id,
            dp.mn_code,
            dp.model,
            dp.status,
            dp.stage_history
        FROM dev_products dp
        LEFT JOIN products p ON p.source_dev_product_id = dp.id
        WHERE dp.status = '已入库' AND p.id IS NULL
    """)

    results = cursor.fetchall()

    if not results:
        print("\n✅ 未找到需要修复的产品（所有已入库产品均已实际入库）")
        cursor.close()
        conn.close()
        sys.exit(0)

    print(f"\n📋 找到 {len(results)} 个需要修复的产品:\n")

    for dev_product_id, mn_code, model, status, stage_history in results:
        print(f"   ID: {dev_product_id:<5} MN: {mn_code or '无':<20} 型号: {model:<20} 状态: {status}")

    response = input(f"\n是否修复这 {len(results)} 个产品的状态？(y/N): ")
    if response.lower() != 'y':
        print("已取消")
        cursor.close()
        conn.close()
        sys.exit(0)

    # 批量修复
    fixed_count = 0
    for dev_product_id, mn_code, model, status, stage_history in results:
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

        # 执行更新
        cursor.execute("""
            UPDATE dev_products
            SET status = '申请入库',
                stage_history = %s,
                updated_at = %s
            WHERE id = %s
        """, (json.dumps(stage_history) if stage_history else None, datetime.now(), dev_product_id))

        print(f"   ✅ 修复产品 {dev_product_id} ({mn_code or '无MN'}): 已入库 → 申请入库")
        fixed_count += 1

    conn.commit()

    print(f"\n✅ 共修复 {fixed_count} 个产品的状态！")
    print("\n📝 这些产品现在可以从产品详情页提交入库审批了")

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
