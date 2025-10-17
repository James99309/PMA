#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""执行结算单业务类型字段迁移"""
import sys, os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from sqlalchemy import text

def execute_migration():
    """执行迁移"""
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("开始执行结算单业务类型字段迁移...")
        print("=" * 80)

        # 步骤0: 修改 distributor_id 约束为可空
        print("\n步骤0: 修改 distributor_id 约束为可空...")
        try:
            db.session.execute(text("""
                ALTER TABLE settlement_orders
                ALTER COLUMN distributor_id DROP NOT NULL
            """))
            db.session.commit()
            print("✓ distributor_id 约束已修改为可空")
        except Exception as e:
            print(f"修改约束失败或约束已是可空: {e}")
            db.session.rollback()

        # 步骤1: 添加新字段
        print("\n步骤1: 添加业务类型标记字段...")
        try:
            db.session.execute(text("""
                ALTER TABLE settlement_orders
                ADD COLUMN IF NOT EXISTS is_direct_contract BOOLEAN DEFAULT false NOT NULL
            """))
            db.session.execute(text("""
                ALTER TABLE settlement_orders
                ADD COLUMN IF NOT EXISTS is_factory_pickup BOOLEAN DEFAULT false NOT NULL
            """))
            db.session.commit()
            print("✓ 字段添加成功")
        except Exception as e:
            print(f"字段添加失败或字段已存在: {e}")
            db.session.rollback()

        # 步骤2: 从批价单同步业务类型标记
        print("\n" + "=" * 80)
        print("步骤2: 从批价单同步业务类型标记...")
        print("=" * 80)

        # 查询需要同步的结算单数量
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM settlement_orders
        """))
        total_count = result.scalar()
        print(f"\n总结算单数: {total_count}")

        # 同步标记字段
        db.session.execute(text("""
            UPDATE settlement_orders s
            SET
                is_direct_contract = p.is_direct_contract,
                is_factory_pickup = p.is_factory_pickup
            FROM pricing_orders p
            WHERE s.pricing_order_id = p.id
        """))
        db.session.commit()

        # 验证同步结果
        result = db.session.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE is_direct_contract = true) as direct_count,
                COUNT(*) FILTER (WHERE is_factory_pickup = true) as pickup_count,
                COUNT(*) FILTER (WHERE is_direct_contract = false AND is_factory_pickup = false) as channel_count
            FROM settlement_orders
        """))
        row = result.fetchone()
        print(f"\n同步结果:")
        print(f"  - 厂商直签: {row[0]} 条")
        print(f"  - 厂家提货: {row[1]} 条")
        print(f"  - 常规渠道: {row[2]} 条")

        # 步骤3: 清洗不合理的数据
        print("\n" + "=" * 80)
        print("步骤3: 清洗不合理的数据...")
        print("=" * 80)

        # 3.1: 厂商直签的结算单应该没有dealer_id和distributor_id
        result = db.session.execute(text("""
            SELECT COUNT(*)
            FROM settlement_orders
            WHERE is_direct_contract = true
            AND (dealer_id IS NOT NULL OR distributor_id IS NOT NULL)
        """))
        direct_dirty_count = result.scalar()

        if direct_dirty_count > 0:
            print(f"\n发现 {direct_dirty_count} 条厂商直签结算单有不合理的客户ID，清洗中...")

            # 显示详情
            result = db.session.execute(text("""
                SELECT id, order_number, dealer_id, distributor_id
                FROM settlement_orders
                WHERE is_direct_contract = true
                AND (dealer_id IS NOT NULL OR distributor_id IS NOT NULL)
                LIMIT 10
            """))

            print("\n示例记录（前10条）:")
            for row in result:
                print(f"  结算单 {row[1]}: dealer_id={row[2]}, distributor_id={row[3]}")

            # 清洗：将客户ID设置为NULL
            db.session.execute(text("""
                UPDATE settlement_orders
                SET dealer_id = NULL, distributor_id = NULL
                WHERE is_direct_contract = true
            """))
            db.session.commit()
            print(f"✓ 已清洗 {direct_dirty_count} 条厂商直签结算单的客户ID")
        else:
            print("\n✓ 所有厂商直签结算单的客户ID都正确")

        # 3.2: 厂家提货的结算单应该没有distributor_id
        result = db.session.execute(text("""
            SELECT COUNT(*)
            FROM settlement_orders
            WHERE is_factory_pickup = true
            AND distributor_id IS NOT NULL
        """))
        pickup_dirty_count = result.scalar()

        if pickup_dirty_count > 0:
            print(f"\n发现 {pickup_dirty_count} 条厂家提货结算单有不合理的distributor_id，清洗中...")

            # 清洗：将distributor_id设置为NULL
            db.session.execute(text("""
                UPDATE settlement_orders
                SET distributor_id = NULL
                WHERE is_factory_pickup = true
            """))
            db.session.commit()
            print(f"✓ 已清洗 {pickup_dirty_count} 条厂家提货结算单的distributor_id")
        else:
            print("\n✓ 所有厂家提货结算单的distributor_id都正确")

        # 步骤4: 最终验证
        print("\n" + "=" * 80)
        print("步骤4: 最终验证...")
        print("=" * 80)

        result = db.session.execute(text("""
            SELECT
                is_direct_contract,
                is_factory_pickup,
                COUNT(*) as count,
                COUNT(*) FILTER (WHERE dealer_id IS NULL) as dealer_null_count,
                COUNT(*) FILTER (WHERE distributor_id IS NULL) as distributor_null_count
            FROM settlement_orders
            GROUP BY is_direct_contract, is_factory_pickup
            ORDER BY is_direct_contract DESC, is_factory_pickup DESC
        """))

        print("\n结算单数据验证:")
        print(f"{'类型':15s} {'数量':8s} {'dealer=NULL':15s} {'distributor=NULL':20s}")
        print("-" * 65)
        for row in result:
            if row[0]:
                type_label = "厂商直签"
            elif row[1]:
                type_label = "厂家提货"
            else:
                type_label = "常规渠道"

            print(f"{type_label:15s} {row[2]:8d} {row[3]:15d} {row[4]:20d}")

        print("\n" + "=" * 80)
        print("✅ 迁移和清洗完成！")
        print("=" * 80)

        return True

if __name__ == '__main__':
    try:
        success = execute_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
