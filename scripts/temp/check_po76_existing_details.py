#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查批价单76在gxh审批前是否已经有明细数据"""
import psycopg2
from psycopg2.extras import RealDictCursor

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n" + "="*80)
    print("检查批价单76在gxh审批时是否有明细数据".center(80))
    print("="*80 + "\n")

    conn = psycopg2.connect(CLOUD_DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. 检查pricing_order_details表
        print("1. 批价单明细(pricing_order_details):")
        cursor.execute("""
            SELECT id, product_name, product_model, product_mn,
                   unit_price, quantity, discount_rate, total_price
            FROM pricing_order_details
            WHERE pricing_order_id = 76
            ORDER BY id
        """)
        pricing_details = cursor.fetchall()

        if pricing_details:
            print(f"   找到 {len(pricing_details)} 条批价明细:")
            for detail in pricing_details:
                print(f"     ID {detail['id']}: {detail['product_name']} ({detail['product_model']}_{detail['product_mn']})")
                print(f"       单价={detail['unit_price']}, 数量={detail['quantity']}, 折扣={detail['discount_rate']}")
        else:
            print("   ❌ 没有批价明细")

        # 2. 检查settlement_order_details表（在gxh审批前）
        print(f"\n2. 结算单明细(settlement_order_details):")
        cursor.execute("""
            SELECT id, product_name, product_model, product_mn,
                   unit_price, quantity, discount_rate, pricing_detail_id
            FROM settlement_order_details
            WHERE pricing_order_id = 76
            ORDER BY id
        """)
        settlement_details = cursor.fetchall()

        if settlement_details:
            print(f"   找到 {len(settlement_details)} 条结算明细:")
            for detail in settlement_details:
                pd_status = f"✓ {detail['pricing_detail_id']}" if detail['pricing_detail_id'] else "❌ NULL"
                print(f"     ID {detail['id']}: {detail['product_name']} ({detail['product_model']}_{detail['product_mn']})")
                print(f"       pricing_detail_id={pd_status}")
        else:
            print("   ❌ 没有结算明细")

        # 3. 分析
        print(f"\n" + "="*80)
        print("分析结果".center(80))
        print("="*80 + "\n")

        print("时间线推测:")
        print("1. 童蕾审批时（14:24:02）:")
        print("   - 前端传递: pricing_details=[], settlement_details=[]")
        print("   - 不会创建明细（空数组）")
        print()
        print("2. gxh审批时（14:26:59）:")
        print("   - 前端传递: pricing_details=?, settlement_details=?")
        print("   - 尝试插入settlement_details（ID 942）")
        print("   - 但pricing_detail_id为NULL（找不到mapping）")
        print()

        if pricing_details:
            print(f"✓ 当前批价单有 {len(pricing_details)} 条批价明细")
            print(f"→ 这些明细是什么时候创建的？")

            # 检查最早的明细ID
            earliest_pricing_id = min(d['id'] for d in pricing_details)
            latest_pricing_id = max(d['id'] for d in pricing_details)
            print(f"  批价明细ID范围: {earliest_pricing_id} - {latest_pricing_id}")
        else:
            print(f"❌ 当前批价单没有批价明细")
            print(f"→ 说明童蕾审批后也没有创建明细")

        if settlement_details:
            print(f"\n✓ 当前结算单有 {len(settlement_details)} 条结算明细")
            earliest_settlement_id = min(d['id'] for d in settlement_details)
            latest_settlement_id = max(d['id'] for d in settlement_details)
            print(f"  结算明细ID范围: {earliest_settlement_id} - {latest_settlement_id}")

            # 检查是否有ID 942
            has_942 = any(d['id'] == 942 for d in settlement_details)
            if has_942:
                print(f"  ⚠️ 存在ID 942（日志中失败的那条）")
            else:
                print(f"  ❌ 不存在ID 942（说明插入失败并回滚）")

            # 检查是否有NULL的pricing_detail_id
            null_count = sum(1 for d in settlement_details if not d['pricing_detail_id'])
            if null_count > 0:
                print(f"  ❌ 有 {null_count} 条明细的pricing_detail_id为NULL")
            else:
                print(f"  ✓ 所有明细都有正确的pricing_detail_id")

        # 4. 关键问题
        print(f"\n" + "="*80)
        print("关键问题".center(80))
        print("="*80 + "\n")

        print("问题1: gxh审批时，前端为什么会传递settlement_details？")
        print("  可能的原因:")
        print("  A. collectSettlementDetails()从DOM读取了现有数据")
        print("  B. 页面上已经显示了结算明细（从数据库渲染）")
        print("  C. 但collectPricingDetails()没有读取到对应的批价明细")
        print()
        print("问题2: 为什么本地正常？")
        print("  可能的原因:")
        print("  A. 本地批价单已经有完整的pricing_details")
        print("  B. 本地的前端代码版本不同")
        print("  C. 本地的数据结构不同")

        # 5. 下一步调查方向
        print(f"\n下一步调查:")
        print("1. 检查collectPricingDetails()和collectSettlementDetails()函数")
        print("2. 确认这两个函数是从哪里读取数据的（DOM还是变量）")
        print("3. 检查edit_pricing_order.html模板是否渲染了明细数据")

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
