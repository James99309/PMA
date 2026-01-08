#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查tonglei对项目277的访问权限 v2"""
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    tonglei_id = 18
    lihuawei_id = 15

    print("=== 1. 用户信息 ===")
    print(f"tonglei: ID=18, 角色=business_admin")
    print(f"lihuawei: ID=15, 角色=sales_manager")

    # 检查affiliations表结构
    print("\n=== 2. affiliations表结构 ===")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'affiliations'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]}")

    # 查询tonglei的归属关系
    print("\n=== 3. tonglei的数据归属 ===")
    cursor.execute("""
        SELECT * FROM affiliations WHERE manager_id = %s OR user_id = %s
    """, (tonglei_id, tonglei_id))
    affs = cursor.fetchall()
    if affs:
        # 获取列名
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'affiliations' ORDER BY ordinal_position
        """)
        col_names = [c[0] for c in cursor.fetchall()]
        for aff in affs:
            print(f"归属记录: {dict(zip(col_names, aff))}")
    else:
        print("未找到tonglei相关的归属记录")

    # 查询lihuawei作为下属的归属关系
    print("\n=== 4. lihuawei的归属关系（作为被管理者）===")
    cursor.execute("""
        SELECT a.*, u.real_name as manager_name
        FROM affiliations a
        LEFT JOIN users u ON a.manager_id = u.id
        WHERE a.user_id = %s
    """, (lihuawei_id,))
    lihuawei_affs = cursor.fetchall()
    if lihuawei_affs:
        for aff in lihuawei_affs:
            print(f"归属记录: {aff}")
    else:
        print("lihuawei没有被管理的归属关系")

    # 查询tonglei管理的下属
    print("\n=== 5. tonglei管理的下属 ===")
    cursor.execute("""
        SELECT a.id, a.user_id, u.real_name, u.username
        FROM affiliations a
        JOIN users u ON a.user_id = u.id
        WHERE a.manager_id = %s
    """, (tonglei_id,))
    subordinates = cursor.fetchall()
    if subordinates:
        for sub in subordinates:
            is_target = " ← 李华伟" if sub[1] == lihuawei_id else ""
            print(f"下属: {sub[2]}({sub[3]}) ID={sub[1]}{is_target}")
    else:
        print("tonglei没有下属")

    # 检查项目277
    print("\n=== 6. 项目277详情 ===")
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
        print(f"共享用户: {project[4]}")
        print(f"共享启用: {project[5]}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
