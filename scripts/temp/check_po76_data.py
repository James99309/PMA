#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查批价单76的数据是否保存成功"""
import psycopg2
from psycopg2.extras import RealDictCursor

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n" + "="*80)
    print("检查批价单76的数据".center(80))
    print("="*80 + "\n")

    conn = psycopg2.connect(CLOUD_DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. 查询批价单的折扣率
        print("1. 批价单折扣率:")
        cursor.execute("""
            SELECT id, order_number,
                   pricing_total_discount_rate,
                   settlement_total_discount_rate
            FROM pricing_orders
            WHERE id = 76
        """)
        po = cursor.fetchone()

        if po:
            print(f"   订单号: {po['order_number']}")
            print(f"   批价折扣率: {po['pricing_total_discount_rate']}")
            print(f"   结算折扣率: {po['settlement_total_discount_rate']}")

            if po['settlement_total_discount_rate'] == 0.5:
                print(f"   ✓ gxh修改的折扣率(0.5)已保存")
            else:
                print(f"   ❌ 折扣率没有保存或不是0.5")
        else:
            print("   ❌ 未找到批价单76")
            return

        # 2. 查询实例390的状态
        print(f"\n2. 审批实例390状态:")
        cursor.execute("""
            SELECT id, current_step, status
            FROM approval_instance
            WHERE id = 390
        """)
        instance = cursor.fetchone()

        if instance:
            print(f"   实例ID: {instance['id']}")
            print(f"   当前步骤: {instance['current_step']}")
            print(f"   状态: {instance['status']}")

            if instance['current_step'] == 14:
                print(f"   ✓ 已转到下一步（步骤14，admin）")
            elif instance['current_step'] == 13:
                print(f"   ❌ 仍在步骤13，审批可能失败")
        else:
            print("   ❌ 未找到实例390")

        # 3. 查询审批记录
        print(f"\n3. 审批记录:")
        cursor.execute("""
            SELECT ar.id, ar.step_id, u.real_name, ar.action, ar.timestamp
            FROM approval_record ar
            JOIN users u ON ar.approver_id = u.id
            WHERE ar.instance_id = 390
            ORDER BY ar.timestamp
        """)
        records = cursor.fetchall()

        for rec in records:
            print(f"   记录{rec['id']}: 步骤{rec['step_id']}, {rec['real_name']}, {rec['action']}, {rec['timestamp']}")

        # 4. 查询结算单明细
        print(f"\n4. 结算单明细:")
        cursor.execute("""
            SELECT id, product_name, discount_rate, pricing_detail_id
            FROM settlement_order_details
            WHERE pricing_order_id = 76
        """)
        details = cursor.fetchall()

        if details:
            print(f"   找到 {len(details)} 条明细:")
            for detail in details:
                pricing_detail_status = "✓" if detail['pricing_detail_id'] else "❌ NULL"
                print(f"     明细{detail['id']}: {detail['product_name']}, "
                      f"折扣率={detail['discount_rate']}, "
                      f"pricing_detail_id={detail['pricing_detail_id']} {pricing_detail_status}")
        else:
            print("   ❌ 没有结算单明细（保存失败）")

        # 5. 分析结果
        print(f"\n" + "="*80)
        print("分析结果".center(80))
        print("="*80 + "\n")

        has_gxh_record = any(r['step_id'] == 13 for r in records)

        if has_gxh_record:
            print("✓ gxh的审批记录已创建")
        else:
            print("❌ gxh的审批记录未创建")

        if instance and instance['current_step'] == 14:
            print("✓ 流程已转到下一步")
        else:
            print("❌ 流程未转到下一步")

        if po and po['settlement_total_discount_rate'] == 0.5:
            print("✓ 折扣率已保存")
        else:
            print("❌ 折扣率未保存")

        if details:
            has_null_pricing_detail = any(d['pricing_detail_id'] is None for d in details)
            if has_null_pricing_detail:
                print("❌ 结算单明细的pricing_detail_id为NULL（数据不完整）")
            else:
                print("✓ 结算单明细正常")
        else:
            print("❌ 结算单明细未创建")

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
