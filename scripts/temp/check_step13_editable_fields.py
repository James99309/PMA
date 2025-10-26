#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端步骤13的editable_fields配置"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n" + "="*80)
    print("检查步骤13的editable_fields配置".center(80))
    print("="*80 + "\n")

    conn = psycopg2.connect(CLOUD_DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 从实例390的template_snapshot中获取步骤13的配置
        cursor.execute("""
            SELECT id, template_snapshot
            FROM approval_instance
            WHERE id = 390
        """)
        instance = cursor.fetchone()

        if not instance:
            print("❌ 未找到实例390")
            return

        snapshot = instance['template_snapshot']
        steps = snapshot.get('steps', [])

        # 找到步骤13
        step_13 = None
        for step in steps:
            if step.get('step_id') == 13:
                step_13 = step
                break

        if not step_13:
            print("❌ 未找到步骤13")
            return

        print("步骤13配置:")
        print(f"  step_id: {step_13.get('step_id')}")
        print(f"  step_name: {step_13.get('step_name')}")
        print(f"  step_type: {step_13.get('step_type')}")
        print(f"  approver_type: {step_13.get('approver_type')}")
        print(f"  action_type: {step_13.get('action_type')}")
        print()

        # 关键：editable_fields
        editable_fields = step_13.get('editable_fields', [])
        print(f"  editable_fields: {editable_fields}")
        print()

        if not editable_fields:
            print("❌ editable_fields 为空！")
            print()
            print("影响:")
            print("  → can_edit_pricing = False")
            print("  → can_edit_discount_price = False")
            print("  → 明细字段渲染为普通文本，不是input")
            print("  → collectPricingDetails() 找不到input元素")
            print("  → pricing_details = []")
            print("  → 保存失败！")
        else:
            print(f"✓ editable_fields 有 {len(editable_fields)} 个字段:")
            for field in editable_fields:
                print(f"    - {field}")
            print()
            print("这些字段会影响:")
            print("  → can_edit_pricing (如果包含明细相关字段)")
            print("  → can_edit_discount_price (如果包含折扣率或单价)")

        # 检查branch_condition
        print(f"\n分支条件配置:")
        branch_condition = step_13.get('branch_condition')
        if branch_condition:
            conditions = branch_condition.get('conditions', [])
            for i, cond in enumerate(conditions):
                if cond.get('value') == 'channel_follow':
                    print(f"  匹配 channel_follow 的条件:")
                    print(f"    approver_id: {cond.get('approver_id')}")
                    print(f"    action: {cond.get('action')}")  # 应该是 pricing_settlement_approval

                    # 关键：检查这个action对应的editable_fields
                    action_type = cond.get('action')
                    print(f"\n  action '{action_type}' 应该允许编辑哪些字段？")
                    print(f"    理论上应该包括: pricing_total_discount_rate, settlement_total_discount_rate")

        # 对比：检查本地应该有什么配置
        print(f"\n" + "="*80)
        print("本地 vs 云端对比".center(80))
        print("="*80 + "\n")

        print("如果本地正常工作，editable_fields 应该包含:")
        print("  [ ]")
        print("  或者")
        print("  ['pricing_total_discount_rate', 'settlement_total_discount_rate']")
        print()
        print(f"云端当前配置: {editable_fields}")
        print()

        if not editable_fields:
            print("❌ 这就是问题！云端的步骤13没有配置editable_fields")
            print()
            print("修复方案:")
            print("1. 更新云端审批流程模板，为步骤13添加editable_fields")
            print("2. 或者修改代码逻辑，即使editable_fields为空也能收集明细数据")

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
