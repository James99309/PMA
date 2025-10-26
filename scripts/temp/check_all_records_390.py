#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查实例390的所有相关记录，包括可能的事务回滚"""
import psycopg2
from psycopg2.extras import RealDictCursor

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n" + "="*80)
    print("详细检查实例390的所有记录".center(80))
    print("="*80 + "\n")

    conn = psycopg2.connect(CLOUD_DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. 所有审批记录（包括可能ID不连续的）
        print("1. 审批记录表中所有与批价单76相关的记录:")
        cursor.execute("""
            SELECT ar.id, ar.instance_id, ar.step_id, u.real_name, ar.action, ar.timestamp
            FROM approval_record ar
            JOIN users u ON ar.approver_id = u.id
            JOIN approval_instance ai ON ar.instance_id = ai.id
            WHERE ai.object_type = 'pricing_order' AND ai.object_id = 76
            ORDER BY ar.id
        """)
        all_records = cursor.fetchall()

        if all_records:
            print(f"   找到 {len(all_records)} 条记录:")
            for rec in all_records:
                marker = "👉" if rec['instance_id'] == 390 else "  "
                print(f"   {marker} 记录{rec['id']}: 实例{rec['instance_id']}, "
                      f"步骤{rec['step_id']}, {rec['real_name']}, "
                      f"{rec['action']}, {rec['timestamp']}")
        else:
            print("   ❌ 没有找到任何记录")

        # 2. approval_record表的ID序列情况
        print(f"\n2. 检查approval_record表最近的ID:")
        cursor.execute("""
            SELECT id, instance_id, step_id, timestamp
            FROM approval_record
            WHERE id >= 670 AND id <= 685
            ORDER BY id
        """)
        id_range = cursor.fetchall()

        if id_range:
            print(f"   ID范围 670-685:")
            for rec in id_range:
                print(f"     ID {rec['id']}: 实例{rec['instance_id']}, 步骤{rec['step_id']}, {rec['timestamp']}")
        else:
            print("   ❌ 该ID范围没有记录")

        # 3. 结算单明细的创建情况
        print(f"\n3. 结算单明细创建情况:")
        cursor.execute("""
            SELECT id, pricing_order_id, product_name, pricing_detail_id
            FROM settlement_order_details
            WHERE pricing_order_id = 76
            ORDER BY id
        """)
        settlement_details = cursor.fetchall()

        if settlement_details:
            print(f"   找到 {len(settlement_details)} 条明细:")
            for detail in settlement_details:
                print(f"     明细ID {detail['id']}: {detail['product_name']}, "
                      f"pricing_detail_id={detail['pricing_detail_id']}")
        else:
            print("   ❌ 没有结算单明细")

        # 4. 检查是否有ID 942（日志中失败的那条）
        print(f"\n4. 检查日志中提到的失败记录（ID 942）:")
        cursor.execute("""
            SELECT id, pricing_order_id, product_name, pricing_detail_id
            FROM settlement_order_details
            WHERE id = 942
        """)
        failed_record = cursor.fetchone()

        if failed_record:
            print(f"   ✓ 找到ID 942: {failed_record['product_name']}, pricing_detail_id={failed_record['pricing_detail_id']}")
        else:
            print(f"   ❌ 没有ID 942（说明插入失败并回滚了）")

        # 5. 分析
        print(f"\n" + "="*80)
        print("分析结果".center(80))
        print("="*80 + "\n")

        instance_390_records = [r for r in all_records if r['instance_id'] == 390]

        if len(instance_390_records) == 1 and instance_390_records[0]['step_id'] == 12:
            print("✓ 实例390只有1条记录（童蕾，步骤12）")
            print("❌ 没有gxh的审批记录（步骤13）")
            print()
            print("可能的原因:")
            print("1. 保存失败导致整个审批事务回滚")
            print("2. 审批记录在创建前失败了")
            print("3. 有异常处理机制阻止了记录创建")
        elif len(instance_390_records) == 2:
            print("✓ 实例390有2条记录")
            step_13_record = next((r for r in instance_390_records if r['step_id'] == 13), None)
            if step_13_record:
                print(f"✓ 找到gxh的记录: {step_13_record}")
            else:
                print("❌ 没有步骤13的记录")
        else:
            print(f"⚠️ 实例390有 {len(instance_390_records)} 条记录（异常）")

        # 检查批价单当前状态
        print(f"\n6. 批价单当前状态:")
        cursor.execute("""
            SELECT id, order_number, status,
                   pricing_total_discount_rate,
                   settlement_total_discount_rate
            FROM pricing_orders
            WHERE id = 76
        """)
        po = cursor.fetchone()

        if po:
            print(f"   状态: {po['status']}")
            print(f"   批价折扣率: {po['pricing_total_discount_rate']}")
            print(f"   结算折扣率: {po['settlement_total_discount_rate']}")

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
