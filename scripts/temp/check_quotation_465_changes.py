#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查询报价单465的客户变更历史"""
import sys, os

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

from dotenv import load_dotenv
dotenv_path = os.path.join(project_root, '.env.sp8d.backup')
load_dotenv(dotenv_path, override=True)

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 80)
    print("报价单 QU202405-022 (ID: 465) 的客户变更历史")
    print("=" * 80)

    # 1. 查询所有与客户相关的变更记录
    print("\n🔍 查询客户字段的变更记录:")
    changes = db.session.execute(text("""
        SELECT
            id,
            operation_type,
            field_name,
            old_value,
            new_value,
            user_id,
            user_name,
            created_at,
            ip_address
        FROM change_logs
        WHERE table_name = 'quotations'
        AND record_id = 465
        AND (field_name = 'customer_id' OR field_name LIKE '%customer%')
        ORDER BY created_at ASC
    """))

    rows = changes.fetchall()
    if rows:
        print(f"\n✅ 找到 {len(rows)} 条客户相关变更:")
        for i, row in enumerate(rows, 1):
            print(f"\n[变更 {i}]")
            print(f"  时间: {row[7]}")
            print(f"  操作类型: {row[1]}")
            print(f"  字段: {row[2]}")
            print(f"  旧值: {row[3]}")
            print(f"  新值: {row[4]}")
            print(f"  操作人: {row[6]} (ID: {row[5]})")
            print(f"  IP地址: {row[8]}")
    else:
        print("  ⚠️ 未找到客户字段的直接变更记录")

    # 2. 查询7月11日前后的所有变更
    print("\n\n📅 查询 2025-07-11 前后的所有变更:")
    all_changes = db.session.execute(text("""
        SELECT
            id,
            operation_type,
            field_name,
            old_value,
            new_value,
            user_id,
            user_name,
            created_at
        FROM change_logs
        WHERE table_name = 'quotations'
        AND record_id = 465
        AND created_at >= '2025-07-01'
        AND created_at <= '2025-07-20'
        ORDER BY created_at ASC
    """))

    july_rows = all_changes.fetchall()
    if july_rows:
        print(f"\n✅ 7月1-20日期间找到 {len(july_rows)} 条变更:")
        for i, row in enumerate(july_rows, 1):
            print(f"\n[{i}] {row[7]}")
            print(f"  字段: {row[2]}")
            print(f"  {row[3]} → {row[4]}")
            print(f"  操作人: {row[6]}")
    else:
        print("  ⚠️ 7月1-20日期间未找到变更记录")

    # 3. 查询所有变更记录（按时间排序）
    print("\n\n📜 查询报价单465的所有历史变更（最近20条）:")
    all_history = db.session.execute(text("""
        SELECT
            id,
            operation_type,
            field_name,
            old_value,
            new_value,
            user_name,
            created_at
        FROM change_logs
        WHERE table_name = 'quotations'
        AND record_id = 465
        ORDER BY created_at DESC
        LIMIT 20
    """))

    history_rows = all_history.fetchall()
    if history_rows:
        print(f"\n✅ 找到 {len(history_rows)} 条历史变更:")
        for i, row in enumerate(history_rows, 1):
            print(f"\n[{i}] {row[6]} | {row[1]} | {row[2]}")
            if row[2] == 'customer_id':
                print(f"  ⚠️ 客户变更: {row[3]} → {row[4]}")
            if len(str(row[3])) < 100 and len(str(row[4])) < 100:
                print(f"  {row[3]} → {row[4]}")
    else:
        print("  ⚠️ 未找到历史变更记录")

    # 4. 检查项目180的客户关联
    print("\n\n📊 项目 180 (湖州西凤漾智创湾) 的客户关联:")
    project_customers = db.session.execute(text("""
        SELECT
            pca.id,
            pca.company_id,
            c.company_name,
            pca.created_at
        FROM project_customer_associations pca
        LEFT JOIN companies c ON c.id = pca.company_id
        WHERE pca.project_id = 180
        ORDER BY pca.created_at ASC
    """))

    pc_rows = project_customers.fetchall()
    if pc_rows:
        print(f"\n✅ 项目关联了 {len(pc_rows)} 个客户:")
        for row in pc_rows:
            print(f"\n  客户ID: {row[1]}")
            print(f"  客户名称: {row[2]}")
            print(f"  关联时间: {row[3]}")

            # 如果是客户4，特别标注
            if row[1] == 4:
                print(f"  ✅ 这是当前报价单的客户!")
    else:
        print("  ⚠️ 项目未关联客户")

    # 5. 查询客户4 (SK海力士) 何时成为项目180的客户
    print("\n\n🔍 查询客户4何时与项目180产生关联:")
    customer_4_assoc = db.session.execute(text("""
        SELECT
            id,
            created_at
        FROM project_customer_associations
        WHERE project_id = 180
        AND company_id = 4
    """))

    c4_row = customer_4_assoc.fetchone()
    if c4_row:
        print(f"\n  ⚠️ 客户4 (SK海力士) 在 {c4_row[1]} 被关联到项目180")
        print(f"  关联记录ID: {c4_row[0]}")
    else:
        print("\n  ❌ 客户4从未被关联到项目180!")
        print("  这解释了为什么报价单客户不在项目客户列表中")

    print("\n" + "=" * 80)
    print("调查完成")
    print("=" * 80)

    # 总结
    print("\n📋 问题总结:")
    print("  1. 报价单 QU202405-022 创建于 2024-05-10")
    print("  2. 报价单最后更新于 2025-07-11 04:50:20")
    print("  3. 当前客户: SK海力士（无锡）产业发展有限公司 (ID: 4)")
    print("  4. 项目关联客户: [319, 323]")
    print("  5. 报价单客户 ≠ 项目客户，存在数据不一致")
