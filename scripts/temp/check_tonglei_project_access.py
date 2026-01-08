#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查tonglei对项目277的具体访问权限"""
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    tonglei_id = 18
    lihuawei_id = 15

    # 1. 获取tonglei的权限配置
    print("=== 1. tonglei在project模块的权限配置 ===")
    cursor.execute("""
        SELECT rp.*
        FROM role_permissions rp
        WHERE rp.role_name = 'business_admin' AND rp.module_name = 'project'
    """)
    role_perms = cursor.fetchall()
    if role_perms:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'role_permissions' ORDER BY ordinal_position
        """)
        cols = [c[0] for c in cursor.fetchall()]
        for perm in role_perms:
            print(f"  {dict(zip(cols, perm))}")
    else:
        print("  未找到business_admin角色的project权限")

    # 2. 检查是否有user_permissions覆盖
    print("\n=== 2. tonglei的用户级权限覆盖 ===")
    cursor.execute("""
        SELECT * FROM user_permissions WHERE user_id = %s
    """, (tonglei_id,))
    user_perms = cursor.fetchall()
    if user_perms:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'user_permissions' ORDER BY ordinal_position
        """)
        cols = [c[0] for c in cursor.fetchall()]
        for perm in user_perms:
            print(f"  {dict(zip(cols, perm))}")
    else:
        print("  tonglei没有用户级权限覆盖配置")

    # 3. 计算tonglei的viewable_user_ids
    print("\n=== 3. tonglei的可查看用户ID列表 ===")
    viewable_ids = [tonglei_id]

    # 归属关系
    cursor.execute("""
        SELECT owner_id FROM affiliations WHERE viewer_id = %s
    """, (tonglei_id,))
    aff_ids = [row[0] for row in cursor.fetchall()]
    viewable_ids.extend(aff_ids)

    viewable_ids = list(set(viewable_ids))
    print(f"  可查看的用户ID: {viewable_ids}")
    print(f"  是否包含lihuawei(15): {lihuawei_id in viewable_ids}")

    # 4. 检查项目277是否满足条件
    print("\n=== 4. 检查项目277是否应该可见 ===")
    cursor.execute("""
        SELECT id, project_name, owner_id, vendor_sales_manager_id,
               shared_with_users, share_enabled
        FROM projects WHERE id = 277
    """)
    project = cursor.fetchone()
    if project:
        print(f"  项目owner_id: {project[2]}")
        print(f"  owner_id在可查看列表中: {project[2] in viewable_ids}")
        print(f"  vendor_sales_manager_id: {project[3]}")
        print(f"  是tonglei的vendor_sales_manager: {project[3] == tonglei_id}")

    # 5. 检查tonglei的company_name和department
    print("\n=== 5. tonglei的公司和部门信息 ===")
    cursor.execute("""
        SELECT id, username, real_name, role, company_name, department, is_department_manager
        FROM users WHERE id = %s
    """, (tonglei_id,))
    tonglei_info = cursor.fetchone()
    if tonglei_info:
        print(f"  用户ID: {tonglei_info[0]}")
        print(f"  用户名: {tonglei_info[1]}")
        print(f"  角色: {tonglei_info[3]}")
        print(f"  公司: {tonglei_info[4]}")
        print(f"  部门: {tonglei_info[5]}")
        print(f"  是否部门负责人: {tonglei_info[6]}")

    # 6. 测试SQL查询
    print("\n=== 6. 模拟项目查询（项目277是否在结果中）===")
    viewable_ids_str = ','.join(str(x) for x in viewable_ids)
    cursor.execute(f"""
        SELECT id, project_name, owner_id
        FROM projects
        WHERE (owner_id IN ({viewable_ids_str}) OR vendor_sales_manager_id = {tonglei_id})
          AND id = 277
    """)
    result = cursor.fetchone()
    if result:
        print(f"  ✓ 项目277在查询结果中: {result}")
    else:
        print(f"  ✗ 项目277不在查询结果中")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
