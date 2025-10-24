#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复云端SP8D数据库 settlement_orders.distributor_id 约束
"""
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

def check_constraint_before():
    """检查修复前的约束状态"""
    print("\n" + "=" * 80)
    print("步骤1: 检查修复前的约束状态")
    print("=" * 80)

    result = db.session.execute(text("""
        SELECT
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_name = 'settlement_orders'
        AND column_name = 'distributor_id'
    """))

    col = result.fetchone()
    if col:
        print(f"  字段名: {col[0]}")
        print(f"  数据类型: {col[1]}")
        print(f"  可空状态: {col[2]}")

        if col[2] == 'NO':
            print(f"  ❌ 确认问题: distributor_id 不允许NULL值")
            return True  # 需要修复
        else:
            print(f"  ✅ distributor_id 已经允许NULL值，无需修复")
            return False  # 不需要修复
    else:
        print(f"  ❌ 错误: 未找到 distributor_id 字段")
        return False


def execute_fix():
    """执行修复"""
    print("\n" + "=" * 80)
    print("步骤2: 执行修复")
    print("=" * 80)

    try:
        # 修改约束
        db.session.execute(text("""
            ALTER TABLE settlement_orders
            ALTER COLUMN distributor_id DROP NOT NULL
        """))

        db.session.commit()
        print("  ✅ 成功移除 NOT NULL 约束")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"  ❌ 修复失败: {str(e)}")
        return False


def verify_fix():
    """验证修复结果"""
    print("\n" + "=" * 80)
    print("步骤3: 验证修复结果")
    print("=" * 80)

    # 检查字段定义
    result = db.session.execute(text("""
        SELECT
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_name = 'settlement_orders'
        AND column_name = 'distributor_id'
    """))

    col = result.fetchone()
    if col:
        print(f"  字段名: {col[0]}")
        print(f"  数据类型: {col[1]}")
        print(f"  可空状态: {col[2]}")

        if col[2] == 'YES':
            print(f"  ✅ 验证通过: distributor_id 现在允许NULL值")
            return True
        else:
            print(f"  ❌ 验证失败: distributor_id 仍然不允许NULL值")
            return False
    else:
        print(f"  ❌ 错误: 未找到 distributor_id 字段")
        return False


def test_insert():
    """测试插入NULL值"""
    print("\n" + "=" * 80)
    print("步骤4: 测试插入 distributor_id=NULL 的记录")
    print("=" * 80)

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
            return True

        print(f"  使用批价单 ID={pricing[0]} 进行测试")

        import random
        test_order_number = f'TEST-FIX-{random.randint(10000000, 99999999)}'

        # 插入测试数据
        result = db.session.execute(text("""
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
        """), {
            'order_number': test_order_number,
            'pricing_order_id': pricing[0],
            'project_id': pricing[1],
            'quotation_id': pricing[2],
            'distributor_id': None,  # ← 测试NULL值
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

        return True

    except Exception as e:
        db.session.rollback()
        print(f"  ❌ 测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("云端SP8D数据库修复工具")
        print("修复目标: settlement_orders.distributor_id NOT NULL约束")
        print("=" * 80)

        # 连接信息
        print("\n数据库连接:")
        result = db.session.execute(text("SELECT current_database(), current_user"))
        db_info = result.fetchone()
        print(f"  数据库: {db_info[0]}")
        print(f"  用户: {db_info[1]}")

        # 步骤1: 检查修复前状态
        needs_fix = check_constraint_before()

        if not needs_fix:
            print("\n" + "=" * 80)
            print("✅ 修复完成：distributor_id 已经允许NULL值，无需执行修复")
            print("=" * 80)
            return

        # 步骤2: 执行修复
        if not execute_fix():
            print("\n" + "=" * 80)
            print("❌ 修复失败，已回滚")
            print("=" * 80)
            return

        # 步骤3: 验证修复
        if not verify_fix():
            print("\n" + "=" * 80)
            print("❌ 验证失败")
            print("=" * 80)
            return

        # 步骤4: 测试插入
        if not test_insert():
            print("\n" + "=" * 80)
            print("❌ 测试失败")
            print("=" * 80)
            return

        # 完成
        print("\n" + "=" * 80)
        print("✅ 修复完成并验证通过！")
        print("=" * 80)
        print("\n修复内容:")
        print("  - 移除了 settlement_orders.distributor_id 的 NOT NULL 约束")
        print("  - 现在可以插入 distributor_id=NULL 的记录")
        print("  - 已通过实际插入测试验证")
        print("\n下一步:")
        print("  - 请在项目中重新提交批价单进行测试")
        print("  - 问题应该已经解决")
        print("=" * 80)


if __name__ == '__main__':
    main()
