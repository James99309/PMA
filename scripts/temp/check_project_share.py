#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查项目共享设置是否有类似问题"""

from sqlalchemy import create_engine, text

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("=" * 70)
    print("检查项目共享设置问题")
    print("=" * 70)

    # 查找 share_enabled=false 但有 shared_with_users 的项目
    print("\n【share_enabled=false 但有共享用户的项目】")
    result = conn.execute(text("""
        SELECT
            p.id,
            p.project_name,
            p.share_enabled,
            p.shared_with_users,
            u.real_name as owner_name
        FROM projects p
        LEFT JOIN users u ON p.owner_id = u.id
        WHERE p.share_enabled = false
        AND p.shared_with_users IS NOT NULL
        AND jsonb_array_length(p.shared_with_users) > 0
                ORDER BY p.id
    """))

    rows = result.fetchall()
    if rows:
        print(f"  发现 {len(rows)} 个问题项目：")
        for row in rows:
            print(f"\n  ID: {row[0]}")
            print(f"  项目名: {row[1]}")
            print(f"  share_enabled: {row[2]}")
            print(f"  shared_with_users: {row[3]}")
            print(f"  负责人: {row[4]}")
    else:
        print("  ✓ 没有发现问题项目")

    # 统计总体情况
    print("\n" + "=" * 70)
    print("【项目共享统计】")
    result = conn.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE share_enabled = true) as enabled_count,
            COUNT(*) FILTER (WHERE share_enabled = false AND shared_with_users IS NOT NULL AND jsonb_array_length(shared_with_users) > 0) as disabled_but_has_users,
            COUNT(*) FILTER (WHERE shared_with_users IS NOT NULL AND jsonb_array_length(shared_with_users) > 0) as has_shared_users
        FROM projects
    """))
    row = result.fetchone()
    print(f"  已启用共享的项目: {row[0]}")
    print(f"  未启用但有共享用户: {row[1]} (问题项目)")
    print(f"  有共享用户的项目总数: {row[2]}")
