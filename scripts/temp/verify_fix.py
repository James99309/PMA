#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证审批流程修复结果"""
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 60)
    print("✅ 验证修复结果")
    print("=" * 60)

    # 查找项目
    cursor.execute("""
        SELECT id, project_name, status, owner_id
        FROM projects
        WHERE id = 713
    """)
    project = cursor.fetchone()

    print(f"\n项目: {project['project_name']} (ID: {project['id']})")
    print(f"  状态: {project['status']}")
    print(f"  所有者ID: {project['owner_id']}")

    if project['status'] == 'draft':
        print("  ✅ 项目状态已正确设置为 draft")
    else:
        print(f"  ⚠️  项目状态不是 draft，而是 {project['status']}")

    # 查找审批实例
    cursor.execute("""
        SELECT id, status, started_at, current_step
        FROM approval_instance
        WHERE object_type = 'project' AND object_id = 713
        ORDER BY started_at DESC
        LIMIT 1
    """)
    instance = cursor.fetchone()

    if instance:
        print(f"\n审批实例 ID: {instance['id']}")
        print(f"  状态: {instance['status']}")
        print(f"  创建时间: {instance['started_at']}")

        if instance['status'] == 'RECALLED':
            print("  ✅ 审批实例已正确召回")
        else:
            print(f"  ⚠️  审批实例状态不是 RECALLED，而是 {instance['status']}")

    print(f"\n{'='*60}")
    print("结论:")
    if project['status'] == 'draft' and instance and instance['status'] == 'RECALLED':
        print("✅ 修复成功！用户 lihuawei 现在可以重新提交项目报备。")
    else:
        print("⚠️  可能存在问题，请检查上述信息。")
    print("=" * 60)

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
