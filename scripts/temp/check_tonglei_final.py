#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查tonglei对项目277的访问权限 - 最终版"""
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    tonglei_id = 18
    lihuawei_id = 15

    # 1. 检查role_permissions表结构
    print("=== 1. role_permissions表结构 ===")
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'role_permissions' ORDER BY ordinal_position
    """)
    cols = [c[0] for c in cursor.fetchall()]
    print(f"  列: {cols}")

    # 2. 查看tonglei的权限配置
    print("\n=== 2. tonglei角色(business_admin)的权限 ===")
    cursor.execute("""
        SELECT * FROM role_permissions WHERE role = 'business_admin'
    """)
    perms = cursor.fetchall()
    for perm in perms:
        print(f"  {dict(zip(cols, perm))}")

    # 3. 查看user_permissions表
    print("\n=== 3. user_permissions表结构 ===")
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'user_permissions' ORDER BY ordinal_position
    """)
    user_perm_cols = [c[0] for c in cursor.fetchall()]
    print(f"  列: {user_perm_cols}")

    # 4. 检查tonglei的用户权限
    print("\n=== 4. tonglei的用户级权限 ===")
    cursor.execute("""
        SELECT * FROM user_permissions WHERE user_id = %s
    """, (tonglei_id,))
    user_perms = cursor.fetchall()
    if user_perms:
        for perm in user_perms:
            print(f"  {dict(zip(user_perm_cols, perm))}")
    else:
        print("  无用户级权限配置")

    # 5. 计算可查看用户ID
    print("\n=== 5. tonglei可查看的用户ID ===")
    viewable_ids = [tonglei_id]
    cursor.execute("SELECT owner_id FROM affiliations WHERE viewer_id = %s", (tonglei_id,))
    viewable_ids.extend([row[0] for row in cursor.fetchall()])
    viewable_ids = list(set(viewable_ids))
    print(f"  ID列表: {viewable_ids}")
    print(f"  包含lihuawei(15): {lihuawei_id in viewable_ids}")

    # 6. 直接查询项目277
    print("\n=== 6. 直接SQL查询项目277 ===")
    viewable_ids_str = ','.join(str(x) for x in viewable_ids)
    query = f"""
        SELECT id, project_name, owner_id
        FROM projects
        WHERE owner_id IN ({viewable_ids_str})
          AND id = 277
    """
    print(f"  SQL: {query}")
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        print(f"  ✓ 找到项目277: {result}")
    else:
        print(f"  ✗ 未找到项目277")

    # 7. 检查项目277是否被删除
    print("\n=== 7. 项目277的详细状态 ===")
    cursor.execute("""
        SELECT id, project_name, owner_id, is_active, is_locked
        FROM projects WHERE id = 277
    """)
    project = cursor.fetchone()
    if project:
        print(f"  ID: {project[0]}")
        print(f"  名称: {project[1]}")
        print(f"  所有者ID: {project[2]}")
        print(f"  是否活跃: {project[3]}")
        print(f"  是否锁定: {project[4]}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
