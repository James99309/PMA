#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接使用psycopg2检查和修复卡住的项目报备审批流程"""
import psycopg2
from psycopg2.extras import RealDictCursor

# 云端SP8D数据库连接信息
DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

try:
    # 连接数据库
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 60)
    print("检查卡住的项目报备审批流程")
    print("=" * 60)

    # 查找lihuawei用户
    cursor.execute("SELECT id, username, email FROM users WHERE username = %s", ('lihuawei',))
    user = cursor.fetchone()

    if not user:
        print("❌ 未找到用户 lihuawei")
        exit(1)

    print(f"\n✅ 找到用户: {user['username']} (ID: {user['id']})")

    # 查找上海证大广场改造项目
    cursor.execute("""
        SELECT id, project_name, status, created_at, owner_id
        FROM projects
        WHERE project_name LIKE %s AND owner_id = %s
        ORDER BY created_at DESC
    """, ('%上海证大广场改造%', user['id']))

    project = cursor.fetchone()

    if not project:
        # 列出该用户的所有项目
        print(f"\n❌ 未找到名称包含'上海证大广场改造'的项目")
        cursor.execute("""
            SELECT id, project_name, status, created_at
            FROM projects
            WHERE owner_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (user['id'],))

        user_projects = cursor.fetchall()
        print(f"\n该用户最近的10个项目：")
        for p in user_projects:
            print(f"  - {p['project_name']} (ID: {p['id']}, 状态: {p['status']}, 创建时间: {p['created_at']})")
        exit(1)

    print(f"\n✅ 找到项目: {project['project_name']} (ID: {project['id']})")
    print(f"   状态: {project['status']}")
    print(f"   创建时间: {project['created_at']}")

    # 查找该项目的审批实例
    cursor.execute("""
        SELECT id, process_id, status, started_at, current_step, created_by
        FROM approval_instance
        WHERE object_type = %s AND object_id = %s
        ORDER BY started_at DESC
    """, ('project', project['id']))

    approval_instances = cursor.fetchall()

    if not approval_instances:
        print("\n❌ 未找到该项目的审批实例")
        exit(1)

    print(f"\n✅ 找到 {len(approval_instances)} 个审批实例：")

    for idx, instance in enumerate(approval_instances, 1):
        print(f"\n{'='*50}")
        print(f"审批实例 #{idx}")
        print(f"{'='*50}")
        print(f"  ID: {instance['id']}")
        print(f"  状态: {instance['status']}")
        print(f"  创建时间: {instance['started_at']}")
        print(f"  当前步骤: {instance['current_step']}")

        # 查找审批记录
        cursor.execute("""
            SELECT ar.id, ar.approver_id, ar.action, ar.comment, ar.timestamp,
                   u.username as approver_name
            FROM approval_record ar
            LEFT JOIN users u ON ar.approver_id = u.id
            WHERE ar.instance_id = %s
            ORDER BY ar.timestamp
        """, (instance['id'],))

        records = cursor.fetchall()

        if records:
            print(f"\n  审批记录 ({len(records)} 条):")
            for record in records:
                print(f"    {record['approver_name']}: {record['action']} - {record['timestamp']}")
                if record['comment']:
                    print(f"      意见: {record['comment']}")
        else:
            print(f"\n  ⚠️  没有审批记录")

    # 询问是否需要重置
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

    if approval_instances:
        latest = approval_instances[0]
        status_lower = latest['status'].lower() if isinstance(latest['status'], str) else latest['status']
        if status_lower in ['pending', 'in_progress']:
            print(f"\n⚠️  最新的审批实例状态为: {latest['status']}")
            print("   可以执行以下操作：")
            print("   1. 删除该审批实例（让用户重新提交）")
            print("   2. 重置项目状态为草稿（draft）并召回审批流程")

            # 自动选择方案2
            response = '2'
            print(f"\n自动选择方案2：召回审批流程并重置项目状态")

            if response == '1':
                print(f"\n删除审批实例 {latest['id']}...")
                # 先删除所有审批记录
                cursor.execute("DELETE FROM approval_record WHERE instance_id = %s", (latest['id'],))
                # 删除审批实例
                cursor.execute("DELETE FROM approval_instance WHERE id = %s", (latest['id'],))
                # 重置项目状态为草稿
                cursor.execute("UPDATE projects SET status = %s WHERE id = %s", ('draft', project['id']))
                conn.commit()
                print("✅ 已删除审批实例并重置项目状态为草稿")
                print("   用户现在可以重新提交项目报备")

            elif response == '2':
                print(f"\n重置项目状态为草稿...")
                # 重置项目状态为草稿
                cursor.execute("UPDATE projects SET status = %s WHERE id = %s", ('draft', project['id']))
                # 同时召回审批实例（使用大写枚举值）
                cursor.execute("UPDATE approval_instance SET status = %s WHERE id = %s", ('RECALLED', latest['id']))
                conn.commit()
                print("✅ 已重置项目状态为草稿，并召回审批流程")
                print("   用户现在可以重新提交项目报备")
            else:
                print("\n❌ 取消操作")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
