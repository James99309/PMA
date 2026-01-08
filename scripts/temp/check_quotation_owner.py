#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查报价单 QU202408-022 的所有者和客户关联问题"""
import psycopg2

# SP8D 云端数据库连接
DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    # 查找报价单
    cursor.execute("""
        SELECT q.id, q.quotation_number, q.customer_id, q.project_id, q.owner_id,
               q.created_at, q.updated_at
        FROM quotations q
        WHERE LOWER(q.quotation_number) = 'qu202408-022'
    """)
    quotation = cursor.fetchone()

    if not quotation:
        print("未找到报价单 QU202408-022")
        return

    q_id, q_number, q_customer_id, q_project_id, q_owner_id, created_at, updated_at = quotation

    print(f"=== 报价单基本信息 ===")
    print(f"报价单号: {q_number}")
    print(f"报价单ID: {q_id}")
    print(f"创建时间: {created_at}")
    print(f"更新时间: {updated_at}")

    # 查看报价单所有者
    print(f"\n=== 报价单所有者 (owner_id={q_owner_id}) ===")
    if q_owner_id:
        cursor.execute("SELECT id, username, real_name FROM users WHERE id = %s", (q_owner_id,))
        owner = cursor.fetchone()
        if owner:
            print(f"用户ID: {owner[0]}")
            print(f"用户名: {owner[1]}")
            print(f"真实姓名: {owner[2]}")
        else:
            print(f"⚠️ owner_id={q_owner_id} 对应的用户不存在！")
    else:
        print("报价单没有所有者 (owner_id 为空)")

    # 查看报价单关联的客户
    print(f"\n=== 报价单关联的客户 (customer_id={q_customer_id}) ===")
    if q_customer_id:
        cursor.execute("""
            SELECT c.id, c.company_name, c.company_code, c.owner_id,
                   u.real_name as owner_name
            FROM companies c
            LEFT JOIN users u ON c.owner_id = u.id
            WHERE c.id = %s
        """, (q_customer_id,))
        customer = cursor.fetchone()
        if customer:
            print(f"客户ID: {customer[0]}")
            print(f"客户名称: {customer[1]}")
            print(f"客户代码: {customer[2]}")
            print(f"客户所有者ID: {customer[3]}")
            print(f"客户所有者姓名: {customer[4]}")

    # 查看项目信息和所有者
    print(f"\n=== 关联项目 (project_id={q_project_id}) ===")
    if q_project_id:
        cursor.execute("""
            SELECT p.id, p.project_name, p.owner_id, p.created_by,
                   u1.real_name as owner_name,
                   u2.real_name as creator_name
            FROM projects p
            LEFT JOIN users u1 ON p.owner_id = u1.id
            LEFT JOIN users u2 ON p.created_by = u2.id
            WHERE p.id = %s
        """, (q_project_id,))
        project = cursor.fetchone()
        if project:
            print(f"项目ID: {project[0]}")
            print(f"项目名称: {project[1]}")
            print(f"项目所有者ID: {project[2]}, 姓名: {project[4]}")
            print(f"项目创建人ID: {project[3]}, 姓名: {project[5]}")

    # 查找杨俊杰和周裔锦的用户信息
    print(f"\n=== 用户查询 ===")
    cursor.execute("""
        SELECT id, username, real_name
        FROM users
        WHERE real_name LIKE '%杨俊杰%' OR real_name LIKE '%周裔锦%'
        ORDER BY real_name
    """)
    users = cursor.fetchall()
    for u in users:
        print(f"用户ID: {u[0]}, 用户名: {u[1]}, 真实姓名: {u[2]}")

    # 查看项目关联的客户及其所有者
    print(f"\n=== 项目关联的客户详情 ===")
    cursor.execute("""
        SELECT pca.id, pca.company_id,
               c.company_name, c.owner_id,
               u.real_name as customer_owner_name
        FROM project_customer_associations pca
        JOIN companies c ON pca.company_id = c.id
        LEFT JOIN users u ON c.owner_id = u.id
        WHERE pca.project_id = %s
        ORDER BY pca.id
    """, (q_project_id,))
    associations = cursor.fetchall()
    for assoc in associations:
        print(f"关联ID: {assoc[0]}, 客户ID: {assoc[1]}")
        print(f"  客户名称: {assoc[2]}")
        print(f"  客户所有者: {assoc[4]} (ID={assoc[3]})")
        print()

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
