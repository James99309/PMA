#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查报价单 QU202311-067 的客户关联问题 - 直接SQL版本"""

from sqlalchemy import create_engine, text

# SP8D数据库连接
DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
engine = create_engine(DB_URL)

with engine.connect() as conn:
    # 查找报价单
    result = conn.execute(text("""
        SELECT q.id, q.quotation_number, q.project_id, q.customer_id, q.amount, q.currency
        FROM quotations q
        WHERE q.quotation_number = 'QU202311-067'
    """))
    quotation = result.fetchone()

    if quotation:
        print("=" * 70)
        print("报价单信息:")
        print("=" * 70)
        print(f"ID: {quotation[0]}")
        print(f"报价单号: {quotation[1]}")
        print(f"项目ID: {quotation[2]}")
        print(f"客户ID: {quotation[3]}")
        print(f"金额: {quotation[4]}")
        print(f"货币: {quotation[5]}")

        # 查看关联的客户
        if quotation[3]:  # customer_id
            customer_result = conn.execute(text("""
                SELECT id, company_name FROM companies WHERE id = :cid
            """), {"cid": quotation[3]})
            customer = customer_result.fetchone()
            if customer:
                print(f"\n当前关联客户:")
                print(f"  客户ID: {customer[0]}")
                print(f"  客户名称: {customer[1]}")
        else:
            print(f"\n当前关联客户: 无 (customer_id 为空)")

        # 查看关联的项目
        if quotation[2]:  # project_id
            project_result = conn.execute(text("""
                SELECT id, project_name FROM projects WHERE id = :pid
            """), {"pid": quotation[2]})
            project = project_result.fetchone()
            if project:
                print(f"\n关联项目信息:")
                print(f"  项目ID: {project[0]}")
                print(f"  项目名称: {project[1]}")

        print("\n" + "=" * 70)

    # 检查有多少报价单关联了客户382
    print("\n检查关联客户ID 382 的所有报价单:")
    result382 = conn.execute(text("""
        SELECT q.id, q.quotation_number, q.project_id, p.project_name
        FROM quotations q
        LEFT JOIN projects p ON q.project_id = p.id
        WHERE q.customer_id = 382
        ORDER BY q.quotation_number
    """))
    count = 0
    for r in result382:
        count += 1
        print(f"  {r[1]} - 项目: {r[3] or '无'}")
    print(f"\n总计: {count} 个报价单关联了客户382（深圳达实智能股份有限公司成都分公司）")

    # 搜索南京建宁相关客户
    print("\n" + "=" * 70)
    print("搜索可能正确的客户（南京/建宁/隧道相关）:")
    print("=" * 70)
    search_result = conn.execute(text("""
        SELECT id, company_name FROM companies
        WHERE (company_name ILIKE '%南京%' OR company_name ILIKE '%建宁%'
               OR company_name ILIKE '%隧道%' OR company_name ILIKE '%过江%')
        AND is_deleted = false
        ORDER BY company_name
        LIMIT 30
    """))
    for c in search_result:
        print(f"  ID: {c[0]}, 名称: {c[1]}")
