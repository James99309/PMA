#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接查询数据库检查报价单 qu202408-022 的客户关联问题"""
import psycopg2

# SP8D 云端数据库连接
DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    # 查找报价单（支持大小写）
    cursor.execute("""
        SELECT id, quotation_number, customer_id, project_id
        FROM quotations
        WHERE LOWER(quotation_number) = 'qu202408-022'
    """)
    quotation = cursor.fetchone()

    if not quotation:
        print("未找到报价单 qu202408-022")
        cursor.execute("""
            SELECT quotation_number FROM quotations
            WHERE quotation_number ILIKE '%202408%'
            ORDER BY quotation_number
        """)
        similar = cursor.fetchall()
        print(f"\n类似的报价单号：")
        for q in similar:
            print(f"  - {q[0]}")
        cursor.close()
        conn.close()
        return

    q_id, q_number, q_customer_id, q_project_id = quotation
    print(f"=== 报价单信息 ===")
    print(f"报价单号: {q_number}")
    print(f"报价单ID: {q_id}")
    print(f"customer_id: {q_customer_id}")
    print(f"project_id: {q_project_id}")

    # 1. 查看报价单直接关联的客户
    print(f"\n=== 1. 报价单直接关联的客户 ===")
    if q_customer_id:
        cursor.execute("SELECT id, company_name, company_code FROM companies WHERE id = %s", (q_customer_id,))
        customer = cursor.fetchone()
        if customer:
            print(f"客户ID: {customer[0]}")
            print(f"客户代码: {customer[2]}")
            print(f"客户名称: {customer[1]}")
        else:
            print(f"⚠️ customer_id={q_customer_id} 对应的客户不存在！")
    else:
        print("报价单的 customer_id 为空")

    # 2. 查看关联的项目信息
    print(f"\n=== 2. 关联的项目 ===")
    if q_project_id:
        cursor.execute("SELECT id, project_name, end_user FROM projects WHERE id = %s", (q_project_id,))
        project = cursor.fetchone()
        if project:
            p_id, p_name, p_end_user = project
            print(f"项目ID: {p_id}")
            print(f"项目名称: {p_name}")
            print(f"项目 end_user 字段: {p_end_user}")
        else:
            print(f"⚠️ project_id={q_project_id} 对应的项目不存在！")

    # 3. 查看项目关联的客户（通过 project_customer_associations 表）
    print(f"\n=== 3. 项目关联的客户（通过关联表）===")
    if q_project_id:
        cursor.execute("""
            SELECT pca.id, pca.company_id, pca.customer_type,
                   c.company_name, c.company_code, c.company_type as actual_type
            FROM project_customer_associations pca
            JOIN companies c ON pca.company_id = c.id
            WHERE pca.project_id = %s
            ORDER BY pca.id
        """, (q_project_id,))
        associations = cursor.fetchall()

        if associations:
            for idx, (assoc_id, company_id, cust_type, company_name, company_code, actual_type) in enumerate(associations, 1):
                print(f"\n关联 {idx}:")
                print(f"  关联ID: {assoc_id}")
                print(f"  客户ID: {company_id}")
                print(f"  客户代码: {company_code}")
                print(f"  客户名称: {company_name}")
                print(f"  客户实际类型: {actual_type}")
                print(f"  关联表中的类型(已废弃): {cust_type}")
        else:
            print("项目没有关联任何客户")

    # 4. 分析结论
    print(f"\n=== 4. 分析结论 ===")
    if q_customer_id:
        cursor.execute("SELECT company_name FROM companies WHERE id = %s", (q_customer_id,))
        q_cust = cursor.fetchone()
        q_cust_name = q_cust[0] if q_cust else "未知"

        # 检查报价单的 customer_id 是否在项目关联的客户中
        cursor.execute("""
            SELECT company_id FROM project_customer_associations
            WHERE project_id = %s AND company_id = %s
        """, (q_project_id, q_customer_id))
        is_in_project = cursor.fetchone()

        if is_in_project:
            print(f"✓ 报价单客户 '{q_cust_name}' (ID={q_customer_id}) 存在于项目关联客户中")
        else:
            print(f"✗ 报价单客户 '{q_cust_name}' (ID={q_customer_id}) 不在项目关联客户中！")
            print("  这可能导致前端显示不一致")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
