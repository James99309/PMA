#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查客户共享问题"""

from sqlalchemy import create_engine, text

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("=" * 70)
    print("检查客户共享问题")
    print("=" * 70)

    # 1. 查找yangjj用户
    print("\n【1. yangjj 用户信息】")
    result = conn.execute(text("""
        SELECT id, username, real_name, role, is_active
        FROM users
        WHERE username ILIKE '%yangjj%' OR real_name ILIKE '%yangjj%'
    """))
    users = result.fetchall()
    for u in users:
        print(f"  ID: {u[0]}, 用户名: {u[1]}, 姓名: {u[2]}, 角色: {u[3]}, 活跃: {u[4]}")

    # 2. 查找上海仪电鑫森科技发展有限公司
    print("\n【2. 客户信息】")
    result = conn.execute(text("""
        SELECT id, company_name, owner_id, share_enabled, shared_with_users, share_contacts
        FROM companies
        WHERE company_name ILIKE '%仪电鑫森%'
    """))
    companies = result.fetchall()
    for c in companies:
        print(f"  ID: {c[0]}")
        print(f"  名称: {c[1]}")
        print(f"  所有者ID: {c[2]}")
        print(f"  共享启用: {c[3]}")
        print(f"  共享用户列表: {c[4]}")
        print(f"  共享联系人: {c[5]}")

        # 查看所有者信息
        if c[2]:
            result2 = conn.execute(text("""
                SELECT username, real_name FROM users WHERE id = :uid
            """), {"uid": c[2]})
            owner = result2.fetchone()
            if owner:
                print(f"  所有者: {owner[1]} ({owner[0]})")

    # 3. 检查yangjj的权限级别
    print("\n【3. yangjj 权限检查】")
    if users:
        yangjj_id = users[0][0]
        print(f"  yangjj用户ID: {yangjj_id}")

        # 检查是否在共享列表中
        if companies:
            shared_users = companies[0][4]
            if shared_users:
                if yangjj_id in shared_users:
                    print(f"  ✓ yangjj (ID={yangjj_id}) 在共享用户列表中")
                else:
                    print(f"  ✗ yangjj (ID={yangjj_id}) 不在共享用户列表 {shared_users} 中")
            else:
                print(f"  ✗ 共享用户列表为空")

        # 检查yangjj的权限模块
        result = conn.execute(text("""
            SELECT pm.module_name, pm.permission_level
            FROM permission_modules pm
            WHERE pm.user_id = :uid AND pm.module_name = 'customer'
        """), {"uid": yangjj_id})
        perms = result.fetchall()
        if perms:
            for p in perms:
                print(f"  客户模块权限级别: {p[1]}")
        else:
            print("  未找到客户模块权限配置")

    # 4. 检查Affiliation关系
    print("\n【4. 归属关系检查】")
    if users and companies:
        yangjj_id = users[0][0]
        company_owner_id = companies[0][2]

        result = conn.execute(text("""
            SELECT id, manager_id, subordinate_id
            FROM affiliations
            WHERE manager_id = :yangjj OR subordinate_id = :yangjj
            OR manager_id = :owner OR subordinate_id = :owner
        """), {"yangjj": yangjj_id, "owner": company_owner_id})
        affs = result.fetchall()
        if affs:
            for a in affs:
                print(f"  归属ID: {a[0]}, 上级ID: {a[1]}, 下级ID: {a[2]}")
        else:
            print("  无相关归属关系")
