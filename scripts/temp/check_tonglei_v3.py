#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查tonglei对项目277的访问权限 v3"""
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    tonglei_id = 18
    lihuawei_id = 15

    print("=== 1. 用户信息 ===")
    print(f"tonglei: ID=18, 角色=business_admin (童蕾)")
    print(f"lihuawei: ID=15, 角色=sales_manager (李华伟)")

    # affiliations表结构: id, owner_id, viewer_id, created_at
    # owner_id = 数据所有者, viewer_id = 可以查看的人

    # 查询tonglei可以查看谁的数据 (tonglei是viewer)
    print("\n=== 2. tonglei可以查看的数据归属 (tonglei作为viewer) ===")
    cursor.execute("""
        SELECT a.id, a.owner_id, u.real_name as owner_name, a.created_at
        FROM affiliations a
        JOIN users u ON a.owner_id = u.id
        WHERE a.viewer_id = %s
        ORDER BY a.owner_id
    """, (tonglei_id,))
    can_view = cursor.fetchall()
    if can_view:
        found_lihuawei = False
        for aff in can_view:
            is_target = " ← 李华伟" if aff[1] == lihuawei_id else ""
            if aff[1] == lihuawei_id:
                found_lihuawei = True
            print(f"  可查看: {aff[2]} (owner_id={aff[1]}){is_target}")
        if found_lihuawei:
            print("\n✓ 李华伟在tonglei的数据归属中")
        else:
            print("\n✗ 李华伟不在tonglei的数据归属中")
    else:
        print("tonglei没有配置任何数据归属")

    # 查询lihuawei的数据可以被谁查看
    print("\n=== 3. 谁可以查看lihuawei的数据 ===")
    cursor.execute("""
        SELECT a.id, a.viewer_id, u.real_name as viewer_name
        FROM affiliations a
        JOIN users u ON a.viewer_id = u.id
        WHERE a.owner_id = %s
    """, (lihuawei_id,))
    viewers = cursor.fetchall()
    if viewers:
        for v in viewers:
            is_tonglei = " ← tonglei" if v[1] == tonglei_id else ""
            print(f"  可查看者: {v[2]} (viewer_id={v[1]}){is_tonglei}")
    else:
        print("没有人被配置可以查看lihuawei的数据")

    # 检查项目277
    print("\n=== 4. 项目277详情 ===")
    cursor.execute("""
        SELECT p.id, p.project_name, p.owner_id,
               u.real_name as owner_name,
               p.shared_with_users, p.share_enabled
        FROM projects p
        LEFT JOIN users u ON p.owner_id = u.id
        WHERE p.id = 277
    """)
    project = cursor.fetchone()
    if project:
        print(f"项目ID: {project[0]}")
        print(f"项目名称: {project[1]}")
        print(f"所有者: {project[3]} (owner_id={project[2]})")
        print(f"共享用户列表: {project[4]}")
        print(f"共享启用: {project[5]}")

        # 检查tonglei是否在共享列表中
        shared_users = project[4] or []
        if tonglei_id in shared_users:
            print(f"\n✓ tonglei (ID={tonglei_id}) 在项目共享列表中")
        else:
            print(f"\n✗ tonglei (ID={tonglei_id}) 不在项目共享列表中")

    # 检查tonglei的权限级别
    print("\n=== 5. tonglei的权限配置 ===")
    cursor.execute("""
        SELECT id, username, real_name, role, company_id
        FROM users WHERE id = %s
    """, (tonglei_id,))
    tonglei_info = cursor.fetchone()
    if tonglei_info:
        print(f"用户ID: {tonglei_info[0]}")
        print(f"用户名: {tonglei_info[1]}")
        print(f"角色: {tonglei_info[3]}")
        print(f"公司ID: {tonglei_info[4]}")

    # 检查role_permissions表中business_admin对project的权限
    print("\n=== 6. business_admin角色对project的权限配置 ===")
    cursor.execute("""
        SELECT * FROM role_permissions
        WHERE role_name = 'business_admin' AND module_name = 'project'
    """)
    perms = cursor.fetchall()
    if perms:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'role_permissions' ORDER BY ordinal_position
        """)
        col_names = [c[0] for c in cursor.fetchall()]
        for perm in perms:
            print(f"  {dict(zip(col_names, perm))}")
    else:
        print("未找到business_admin对project的权限配置")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
