#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查2025年7月11日的变更记录"""
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

project_root = get_project_root()
sys.path.insert(0, project_root)

# 加载云端数据库配置
from dotenv import load_dotenv
dotenv_path = os.path.join(project_root, '.env.sp8d.backup')
if os.path.exists(dotenv_path):
    print(f"✅ 加载云端数据库配置: {dotenv_path}")
    load_dotenv(dotenv_path, override=True)

from app import create_app, db
from sqlalchemy import text
from datetime import datetime

def check_july11_changes():
    """检查2025年7月11日的变更"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("检查 2025-07-11 的数据变更")
        print("=" * 80)

        # 1. 查询报价单 QU202405-022 在7月11日的变更
        print("\n📋 查询报价单 QU202405-022 在 2025-07-11 的状态变化:")

        # 检查是否有 change_logs 表
        try:
            result = db.session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'change_logs'
            """))

            if result.fetchone():
                print("\n  ✅ 找到 change_logs 表，查询相关记录:")

                # 查询7月11日的变更日志
                logs = db.session.execute(text("""
                    SELECT
                        id,
                        table_name,
                        record_id,
                        operation,
                        changes,
                        user_id,
                        created_at
                    FROM change_logs
                    WHERE table_name = 'quotations'
                    AND record_id = 465
                    AND DATE(created_at) = '2025-07-11'
                    ORDER BY created_at DESC
                """)).fetchall()

                if logs:
                    print(f"\n  找到 {len(logs)} 条变更记录:")
                    for log in logs:
                        print(f"\n  [变更 {log[0]}]")
                        print(f"    表名: {log[1]}")
                        print(f"    记录ID: {log[2]}")
                        print(f"    操作: {log[3]}")
                        print(f"    变更内容: {log[4][:500] if log[4] else 'N/A'}...")
                        print(f"    用户ID: {log[5]}")
                        print(f"    时间: {log[6]}")
                else:
                    print("  ⚠️ 未找到 2025-07-11 的变更记录")

                # 查询前后时间的变更记录
                print("\n  查询前后时间的变更记录:")
                logs_around = db.session.execute(text("""
                    SELECT
                        id,
                        operation,
                        changes,
                        user_id,
                        created_at
                    FROM change_logs
                    WHERE table_name = 'quotations'
                    AND record_id = 465
                    AND created_at >= '2025-07-01'
                    AND created_at <= '2025-07-20'
                    ORDER BY created_at DESC
                """)).fetchall()

                if logs_around:
                    print(f"\n  7月份的变更记录:")
                    for log in logs_around:
                        print(f"\n  时间: {log[4]} | 操作: {log[1]} | 用户ID: {log[3]}")
                        if log[2] and 'customer_id' in str(log[2]):
                            print(f"  ⚠️ 发现客户ID变更: {log[2][:300]}")
                else:
                    print("  ⚠️ 7月份未找到相关变更记录")

            else:
                print("  ⚠️ 系统中无 change_logs 表")
        except Exception as e:
            print(f"  ❌ 查询 change_logs 失败: {e}")

        # 2. 查询项目ID 180 关联的客户变化
        print("\n\n📊 查询项目 180 (湖州西凤漾智创湾) 的客户关联:")

        try:
            # 查询项目客户关联表
            associations = db.session.execute(text("""
                SELECT
                    id,
                    project_id,
                    company_id,
                    created_at
                FROM project_customer_associations
                WHERE project_id = 180
                ORDER BY created_at DESC
            """)).fetchall()

            if associations:
                print(f"\n  找到 {len(associations)} 条客户关联记录:")
                for assoc in associations:
                    # 查询客户名称
                    company_result = db.session.execute(text("""
                        SELECT company_name FROM companies WHERE id = :company_id
                    """), {"company_id": assoc[2]})
                    company_row = company_result.fetchone()
                    company_name = company_row[0] if company_row else 'Unknown'

                    print(f"\n  客户ID: {assoc[2]} | 客户名称: {company_name}")
                    print(f"  关联时间: {assoc[3]}")
            else:
                print("  ⚠️ 未找到项目客户关联记录")
        except Exception as e:
            print(f"  ❌ 查询项目客户关联失败: {e}")

        # 3. 查询客户319和323的信息
        print("\n\n🏢 查询项目关联的客户信息:")
        for customer_id in [319, 323]:
            try:
                customer = db.session.execute(text("""
                    SELECT id, company_name, created_at, updated_at
                    FROM companies
                    WHERE id = :customer_id
                """), {"customer_id": customer_id}).fetchone()

                if customer:
                    print(f"\n  [客户 {customer[0]}]")
                    print(f"    名称: {customer[1]}")
                    print(f"    创建时间: {customer[2]}")
                    print(f"    更新时间: {customer[3]}")

                    # 查询这个客户的报价单数量
                    count_result = db.session.execute(text("""
                        SELECT COUNT(*) FROM quotations WHERE customer_id = :customer_id
                    """), {"customer_id": customer_id})
                    count = count_result.scalar()
                    print(f"    关联报价单数: {count}")
            except Exception as e:
                print(f"  ❌ 查询客户{customer_id}失败: {e}")

        # 4. 查询报价单在7月11日前后的所有变更
        print("\n\n🔍 查询报价单 465 的历史变更（所有时间）:")
        try:
            all_changes = db.session.execute(text("""
                SELECT
                    operation,
                    changes,
                    user_id,
                    created_at
                FROM change_logs
                WHERE table_name = 'quotations'
                AND record_id = 465
                ORDER BY created_at ASC
                LIMIT 20
            """)).fetchall()

            if all_changes:
                print(f"\n  找到 {len(all_changes)} 条历史变更:")
                for i, change in enumerate(all_changes, 1):
                    print(f"\n  [{i}] {change[3]} | 操作: {change[0]} | 用户: {change[2]}")
                    if change[1]:
                        changes_str = str(change[1])
                        if 'customer' in changes_str.lower():
                            print(f"  ⚠️ 涉及客户变更: {changes_str[:400]}")
            else:
                print("  ⚠️ 未找到历史变更记录")
        except Exception as e:
            print(f"  ❌ 查询历史变更失败: {e}")

        print("\n" + "=" * 80)
        print("调查完成")
        print("=" * 80)

if __name__ == '__main__':
    check_july11_changes()
