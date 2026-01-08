#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查tonglei对项目277的访问权限"""
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    # 1. 查找tonglei和lihuawei的用户信息
    print("=== 1. 用户信息 ===")
    cursor.execute("""
        SELECT id, username, real_name, role
        FROM users
        WHERE username IN ('tonglei', 'lihuawei')
        ORDER BY username
    """)
    users = cursor.fetchall()
    tonglei_id = None
    lihuawei_id = None
    for u in users:
        print(f"用户ID: {u[0]}, 用户名: {u[1]}, 真实姓名: {u[2]}, 角色: {u[3]}")
        if u[1] == 'tonglei':
            tonglei_id = u[0]
        elif u[1] == 'lihuawei':
            lihuawei_id = u[0]

    # 2. 检查数据归属关系 (Affiliation表)
    print(f"\n=== 2. 数据归属关系 (tonglei ID={tonglei_id} 的下属) ===")
    cursor.execute("""
        SELECT a.id, a.superior_id, a.subordinate_id,
               u1.real_name as superior_name,
               u2.real_name as subordinate_name,
               a.created_at
        FROM affiliations a
        JOIN users u1 ON a.superior_id = u1.id
        JOIN users u2 ON a.subordinate_id = u2.id
        WHERE a.superior_id = %s
        ORDER BY a.subordinate_id
    """, (tonglei_id,))
    affiliations = cursor.fetchall()
    if affiliations:
        for aff in affiliations:
            is_lihuawei = " ← 李华伟" if aff[2] == lihuawei_id else ""
            print(f"关系ID: {aff[0]} | 上级: {aff[3]}(ID={aff[1]}) -> 下属: {aff[4]}(ID={aff[2]}){is_lihuawei}")
    else:
        print("tonglei没有配置下属归属关系")

    # 3. 检查项目277的信息
    print(f"\n=== 3. 项目277详情 ===")
    cursor.execute("""
        SELECT p.id, p.project_name, p.owner_id, p.created_by,
               u1.real_name as owner_name,
               p.shared_with_users, p.share_enabled,
               p.is_deleted
        FROM projects p
        LEFT JOIN users u1 ON p.owner_id = u1.id
        WHERE p.id = 277
    """)
    project = cursor.fetchone()
    if project:
        print(f"项目ID: {project[0]}")
        print(f"项目名称: {project[1]}")
        print(f"所有者: {project[4]} (owner_id={project[2]})")
        print(f"创建人ID: {project[3]}")
        print(f"共享用户列表: {project[5]}")
        print(f"共享启用: {project[6]}")
        print(f"是否删除: {project[7]}")

    # 4. 检查tonglei的权限级别
    print(f"\n=== 4. tonglei的权限配置 ===")
    cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.role,
               u.permission_level, u.company_id
        FROM users u
        WHERE u.id = %s
    """, (tonglei_id,))
    tonglei_info = cursor.fetchone()
    if tonglei_info:
        print(f"用户ID: {tonglei_info[0]}")
        print(f"用户名: {tonglei_info[1]}")
        print(f"真实姓名: {tonglei_info[2]}")
        print(f"角色: {tonglei_info[3]}")
        print(f"权限级别: {tonglei_info[4]}")
        print(f"公司ID: {tonglei_info[5]}")

    # 5. 检查lihuawei的信息
    print(f"\n=== 5. lihuawei的信息 ===")
    cursor.execute("""
        SELECT u.id, u.username, u.real_name, u.role,
               u.permission_level, u.company_id
        FROM users u
        WHERE u.id = %s
    """, (lihuawei_id,))
    lihuawei_info = cursor.fetchone()
    if lihuawei_info:
        print(f"用户ID: {lihuawei_info[0]}")
        print(f"用户名: {lihuawei_info[1]}")
        print(f"真实姓名: {lihuawei_info[2]}")
        print(f"角色: {lihuawei_info[3]}")
        print(f"权限级别: {lihuawei_info[4]}")
        print(f"公司ID: {lihuawei_info[5]}")

    # 6. 检查是否是同一公司
    print(f"\n=== 6. 公司信息对比 ===")
    if tonglei_info and lihuawei_info:
        if tonglei_info[5] == lihuawei_info[5]:
            print(f"✓ tonglei和lihuawei属于同一公司 (company_id={tonglei_info[5]})")
        else:
            print(f"✗ tonglei(公司{tonglei_info[5]})和lihuawei(公司{lihuawei_info[5]})不在同一公司")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
