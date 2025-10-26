#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查数据库迁移历史"""
import sys, os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)

from dotenv import load_dotenv
dotenv_path = os.path.join(project_root, '.env.sp8d.backup')
load_dotenv(dotenv_path, override=True)

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 80)
    print("检查数据库迁移历史")
    print("=" * 80)

    # 1. 检查alembic_version表
    print("\n📋 当前数据库版本:")
    result = db.session.execute(text("SELECT version_num FROM alembic_version"))
    version = result.scalar()
    print(f"  当前版本: {version}")

    # 2. 检查quotations表是否有customer_id字段
    print("\n🔍 检查quotations表字段:")
    result = db.session.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'quotations'
        ORDER BY ordinal_position
    """))

    has_customer_id = False
    for row in result:
        if row[0] == 'customer_id':
            has_customer_id = True
            print(f"  ✅ 找到 customer_id 字段: {row[1]}, nullable={row[2]}")

    if not has_customer_id:
        print("  ❌ quotations表中没有customer_id字段！")

    # 3. 查询报价单465的customer_id（如果字段存在）
    if has_customer_id:
        print("\n📊 查询报价单465的customer_id:")
        result = db.session.execute(text("""
            SELECT
                id,
                quotation_number,
                customer_id,
                project_id,
                created_at
            FROM quotations
            WHERE id = 465
        """))

        row = result.fetchone()
        if row:
            print(f"  ID: {row[0]}")
            print(f"  报价单号: {row[1]}")
            print(f"  客户ID: {row[2]}")
            print(f"  项目ID: {row[3]}")
            print(f"  创建时间: {row[4]}")

    # 4. 查询所有报价单的customer_id分布
    if has_customer_id:
        print("\n📈 报价单customer_id统计:")
        result = db.session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(customer_id) as has_customer,
                COUNT(*) - COUNT(customer_id) as null_customer
            FROM quotations
        """))

        row = result.fetchone()
        print(f"  总报价单数: {row[0]}")
        print(f"  有客户ID: {row[1]} ({row[1]*100/row[0]:.1f}%)")
        print(f"  客户ID为空: {row[2]} ({row[2]*100/row[0]:.1f}%)")

        # 5. 统计各客户的报价单数量
        print("\n🏢 各客户的报价单数量（Top 10）:")
        result = db.session.execute(text("""
            SELECT
                q.customer_id,
                c.company_name,
                COUNT(*) as quote_count
            FROM quotations q
            LEFT JOIN companies c ON c.id = q.customer_id
            WHERE q.customer_id IS NOT NULL
            GROUP BY q.customer_id, c.company_name
            ORDER BY quote_count DESC
            LIMIT 10
        """))

        for i, row in enumerate(result, 1):
            print(f"  {i}. 客户ID {row[0]} ({row[1]}): {row[2]} 个报价单")

    print("\n" + "=" * 80)
