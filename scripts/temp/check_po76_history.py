#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查批价单76的修改历史"""
import psycopg2
from psycopg2.extras import RealDictCursor

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n" + "="*80)
    print("检查批价单76的修改历史".center(80))
    print("="*80 + "\n")

    conn = psycopg2.connect(CLOUD_DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. 批价单的创建和更新时间
        print("1. 批价单76的时间戳:")
        cursor.execute("""
            SELECT id, order_number, created_at, updated_at,
                   pricing_total_discount_rate,
                   settlement_total_discount_rate
            FROM pricing_orders
            WHERE id = 76
        """)
        po = cursor.fetchone()

        if po:
            print(f"   创建时间: {po['created_at']}")
            print(f"   更新时间: {po['updated_at']}")
            print(f"   批价折扣率: {po['pricing_total_discount_rate']}")
            print(f"   结算折扣率: {po['settlement_total_discount_rate']}")

        # 2. 结算单明细的创建时间
        print(f"\n2. 结算单明细的创建时间:")
        cursor.execute("""
            SELECT sod.id, sod.product_name, sod.discount_rate
            FROM settlement_order_details sod
            WHERE sod.pricing_order_id = 76
            ORDER BY sod.id
        """)
        details = cursor.fetchall()

        for detail in details:
            print(f"   明细{detail['id']}: {detail['product_name']}, 折扣率={detail['discount_rate']}")

        # 3. 关键时间点对比
        print(f"\n3. 关键时间点对比:")
        print(f"   童蕾审批(步骤12): 2025-10-25 14:24:02.636721")
        print(f"   gxh审批失败日志: 2025-10-25 14:26:59（根据HTTP请求日志）")
        print(f"   批价单更新时间: {po['updated_at']}")

        # 4. 检查是否有其他审批记录在gxh之后
        print(f"\n4. 检查gxh审批失败之后是否有其他操作:")
        cursor.execute("""
            SELECT ar.id, ar.step_id, u.real_name, ar.action, ar.timestamp
            FROM approval_record ar
            JOIN users u ON ar.approver_id = u.id
            WHERE ar.instance_id = 390 AND ar.timestamp > '2025-10-25 14:24:02'
            ORDER BY ar.timestamp
        """)
        later_records = cursor.fetchall()

        if later_records:
            print(f"   找到 {len(later_records)} 条之后的记录:")
            for rec in later_records:
                print(f"     记录{rec['id']}: 步骤{rec['step_id']}, {rec['real_name']}, {rec['action']}, {rec['timestamp']}")
        else:
            print("   ❌ 没有找到之后的审批记录")

        # 5. 检查结算单状态
        print(f"\n5. 结算单信息:")
        cursor.execute("""
            SELECT id, settlement_number, status, created_at
            FROM settlement_orders
            WHERE pricing_order_id = 76
            ORDER BY id DESC
            LIMIT 1
        """)
        settlement = cursor.fetchone()

        if settlement:
            print(f"   结算单ID: {settlement['id']}")
            print(f"   结算单号: {settlement['settlement_number']}")
            print(f"   状态: {settlement['status']}")
            print(f"   创建时间: {settlement['created_at']}")
        else:
            print("   ❌ 没有结算单")

        # 6. 分析
        print(f"\n" + "="*80)
        print("时间线分析".center(80))
        print("="*80 + "\n")

        print("时间顺序:")
        print("1. 14:24:02 - 童蕾批准步骤12")
        print("2. 14:26:59 - gxh尝试批准步骤13")
        print("   → 保存数据失败（ID 942插入失败）")
        print("   → 审批记录未创建")
        print("   → 但流程转到步骤14？")
        print(f"3. {po['updated_at']} - 批价单最后更新时间")

        if po['updated_at'] and '2025-10-25 14:26' in str(po['updated_at']):
            print("\n✓ 批价单更新时间与gxh审批时间接近")
            print("→ 说明某些数据在gxh审批时被保存了")
        else:
            print("\n⚠️ 批价单更新时间与gxh审批时间不匹配")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

    print("\n" + "="*80)
    print("检查完成".center(80))
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
