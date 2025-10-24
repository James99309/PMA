#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端SP8D数据库 settlement_orders 表约束"""
import sys
import os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

# 设置云端SP8D数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
os.environ['USE_SUPABASE'] = 'true'
os.environ['SUPABASE_DB_TYPE'] = 'sp8d'

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    print("=" * 80)
    print("检查云端SP8D数据库 settlement_orders 表")
    print("=" * 80)

    # 1. 检查数据库连接
    print("\n1. 数据库连接信息:")
    try:
        result = db.session.execute(text("SELECT current_database(), current_user"))
        db_info = result.fetchone()
        print(f"  数据库: {db_info[0]}")
        print(f"  用户: {db_info[1]}")
    except Exception as e:
        print(f"  错误: {e}")

    # 2. 检查迁移版本
    print("\n2. 数据库迁移版本:")
    try:
        result = db.session.execute(text("SELECT version_num FROM alembic_version"))
        versions = [v[0] for v in result.fetchall()]
        print(f"  当前版本数: {len(versions)}")
        if versions:
            print(f"  版本列表:")
            for v in versions:
                print(f"    - {v}")

        # 检查特定迁移
        if 'add_settlement_business_type_20251014' in versions:
            print(f"\n  ✅ 迁移 'add_settlement_business_type_20251014' 已运行")
        else:
            print(f"\n  ❌ 迁移 'add_settlement_business_type_20251014' 未运行")
    except Exception as e:
        print(f"  错误: {e}")

    # 3. 检查settlement_orders表的字段定义
    print("\n3. settlement_orders 表的关键字段:")
    try:
        result = db.session.execute(text("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'settlement_orders'
            AND column_name IN ('distributor_id', 'dealer_id', 'is_direct_contract', 'is_factory_pickup')
            ORDER BY column_name
        """))
        rows = result.fetchall()
        if rows:
            print(f"  {'字段名':<25} {'类型':<15} {'可空':<10} {'默认值'}")
            print(f"  {'-'*70}")
            for row in rows:
                print(f"  {row[0]:<25} {row[1]:<15} {row[2]:<10} {row[3]}")
        else:
            print("  ❌ 未找到settlement_orders表或相关字段")
    except Exception as e:
        print(f"  错误: {e}")

    # 4. 检查表约束
    print("\n4. settlement_orders 表的约束:")
    try:
        result = db.session.execute(text("""
            SELECT
                conname AS constraint_name,
                contype AS constraint_type,
                pg_get_constraintdef(oid) AS constraint_def
            FROM pg_constraint
            WHERE conrelid = 'settlement_orders'::regclass
            ORDER BY contype, conname
        """))
        constraints = result.fetchall()
        if constraints:
            print(f"  {'约束名':<40} {'类型':<8} {'定义'}")
            print(f"  {'-'*80}")
            for row in constraints:
                constraint_type_map = {
                    'p': 'PRIMARY',
                    'f': 'FOREIGN',
                    'c': 'CHECK',
                    'u': 'UNIQUE',
                    'n': 'NOT NULL'
                }
                ctype = constraint_type_map.get(row[1], row[1])
                print(f"  {row[0]:<40} {ctype:<8} {row[2][:60]}")
        else:
            print("  未找到约束")
    except Exception as e:
        print(f"  错误: {e}")

    # 5. 检查是否有NOT NULL约束在distributor_id上
    print("\n5. distributor_id 字段的NOT NULL约束检查:")
    try:
        result = db.session.execute(text("""
            SELECT
                attname,
                attnotnull,
                format_type(atttypid, atttypmod) as data_type
            FROM pg_attribute
            WHERE attrelid = 'settlement_orders'::regclass
            AND attname = 'distributor_id'
        """))
        col = result.fetchone()
        if col:
            print(f"  字段名: {col[0]}")
            print(f"  数据类型: {col[2]}")
            if col[1]:
                print(f"  ❌ 有NOT NULL约束 (attnotnull = true)")
            else:
                print(f"  ✅ 无NOT NULL约束 (attnotnull = false)")
        else:
            print(f"  未找到distributor_id字段")
    except Exception as e:
        print(f"  错误: {e}")

    # 6. 测试插入NULL值
    print("\n6. 测试插入 distributor_id=NULL 的记录:")
    try:
        # 查找一个批价单用于测试
        result = db.session.execute(text("""
            SELECT id, project_id, quotation_id, created_by
            FROM pricing_orders
            WHERE created_by IS NOT NULL
            ORDER BY id DESC
            LIMIT 1
        """))
        pricing = result.fetchone()

        if not pricing:
            print("  ⚠️ 数据库中没有批价单数据，跳过测试")
        else:
            print(f"  使用批价单 ID={pricing[0]} 进行测试")

            import random
            test_order_number = f'TEST-{random.randint(10000000, 99999999)}'

            insert_sql = text("""
                INSERT INTO settlement_orders (
                    order_number, pricing_order_id, project_id, quotation_id,
                    distributor_id, dealer_id,
                    is_direct_contract, is_factory_pickup,
                    total_amount, total_discount_rate,
                    status, settlement_status,
                    created_by
                ) VALUES (
                    :order_number, :pricing_order_id, :project_id, :quotation_id,
                    :distributor_id, :dealer_id,
                    :is_direct_contract, :is_factory_pickup,
                    :total_amount, :total_discount_rate,
                    :status, :settlement_status,
                    :created_by
                )
                RETURNING id
            """)

            result = db.session.execute(insert_sql, {
                'order_number': test_order_number,
                'pricing_order_id': pricing[0],
                'project_id': pricing[1],
                'quotation_id': pricing[2],
                'distributor_id': None,  # ← 关键测试点
                'dealer_id': None,
                'is_direct_contract': False,
                'is_factory_pickup': False,
                'total_amount': 0.0,
                'total_discount_rate': 1.0,
                'status': 'draft',
                'settlement_status': 'pending',
                'created_by': pricing[3]
            })

            new_id = result.scalar()
            print(f"  ✅ 成功插入测试记录，ID={new_id}")

            # 立即删除测试数据
            db.session.execute(text(f"DELETE FROM settlement_orders WHERE id = {new_id}"))
            db.session.commit()
            print(f"  ✅ 已删除测试记录")

    except Exception as e:
        db.session.rollback()
        print(f"  ❌ 插入失败:")
        print(f"     错误类型: {type(e).__name__}")
        print(f"     错误信息: {str(e)}")

        # 检查是否是NOT NULL约束错误
        if 'not-null constraint' in str(e).lower() or 'violates not-null constraint' in str(e).lower():
            print(f"\n  🔥 确认问题: distributor_id字段有NOT NULL约束！")

    print("\n" + "=" * 80)
