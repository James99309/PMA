#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查PO202510-004的步骤转换逻辑"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n" + "="*80)
    print("检查步骤转换逻辑".center(80))
    print("="*80 + "\n")

    conn = psycopg2.connect(CLOUD_DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 获取实例385的完整信息
        cursor.execute("""
            SELECT id, current_step, status, template_snapshot
            FROM approval_instance
            WHERE id = 385
        """)
        instance = cursor.fetchone()

        if not instance:
            print("❌ 未找到实例385")
            return

        print(f"实例ID: {instance['id']}")
        print(f"当前步骤ID: {instance['current_step']}")
        print(f"状态: {instance['status']}")

        # 解析模板快照中的所有步骤
        template_snapshot = instance['template_snapshot']
        steps = template_snapshot.get('steps', [])

        print(f"\n模板快照中的所有步骤:")
        print(f"{'步骤ID':<10} {'顺序':<8} {'步骤名':<20} {'类型':<12} {'审批人类型':<15} {'动作类型':<30}")
        print("-" * 110)

        for step in steps:
            step_id = step.get('step_id') or 'N/A'
            step_order = step.get('step_order') or 0
            step_name = step.get('step_name') or ''
            step_type = step.get('step_type') or 'normal'
            approver_type = step.get('approver_type') or 'user'
            action_type = step.get('action_type') or ''

            marker = "👉" if step.get('step_id') == instance['current_step'] else "  "
            print(f"{marker} {str(step_id):<10} {str(step_order):<8} {step_name:<20} {step_type:<12} {approver_type:<15} {action_type:<30}")

        # 查找步骤12和步骤13
        step_12 = None
        step_13 = None
        step_14 = None

        for step in steps:
            if step.get('step_id') == 12:
                step_12 = step
            elif step.get('step_id') == 13:
                step_13 = step
            elif step.get('step_id') == 14:
                step_14 = step

        print(f"\n" + "="*80)
        print("关键步骤分析".center(80))
        print("="*80 + "\n")

        if step_12:
            print(f"步骤12（童蕾的步骤）:")
            print(f"  step_order: {step_12.get('step_order')}")
            print(f"  step_name: {step_12.get('step_name')}")
            print(f"  approver_type: {step_12.get('approver_type')}")

        if step_13:
            print(f"\n步骤13（应该是gxh的步骤）:")
            print(f"  step_order: {step_13.get('step_order')}")
            print(f"  step_name: {step_13.get('step_name')}")
            print(f"  step_type: {step_13.get('step_type')}")
            print(f"  approver_type: {step_13.get('approver_type')}")
            print(f"  action_type: {step_13.get('action_type')}")

            if step_13.get('branch_condition'):
                print(f"\n  分支条件:")
                bc = step_13.get('branch_condition')
                print(f"    field: {bc.get('field')}")
                print(f"    conditions: {len(bc.get('conditions', []))} 个")
                for i, cond in enumerate(bc.get('conditions', [])):
                    print(f"      {i+1}. value={cond.get('value')}, approver_id={cond.get('approver_id')}, action={cond.get('action')}")

        if step_14:
            print(f"\n步骤14（当前步骤）:")
            print(f"  step_order: {step_14.get('step_order')}")
            print(f"  step_name: {step_14.get('step_name')}")
            print(f"  approver_type: {step_14.get('approver_type')}")

        # 检查审批记录
        print(f"\n" + "="*80)
        print("审批记录".center(80))
        print("="*80 + "\n")

        cursor.execute("""
            SELECT ar.id, ar.step_id, u.real_name, ar.action, ar.timestamp
            FROM approval_record ar
            JOIN users u ON ar.approver_id = u.id
            WHERE ar.instance_id = 385
            ORDER BY ar.timestamp
        """)
        records = cursor.fetchall()

        if records:
            print(f"找到 {len(records)} 条审批记录:")
            for rec in records:
                print(f"  记录{rec['id']}: 步骤{rec['step_id']}, {rec['real_name']}, {rec['action']}, {rec['timestamp']}")
        else:
            print("  ❌ 没有审批记录")

        # 分析问题
        print(f"\n" + "="*80)
        print("问题分析".center(80))
        print("="*80 + "\n")

        if step_12 and step_13 and step_14:
            step_12_order = step_12.get('step_order')
            step_13_order = step_13.get('step_order')
            step_14_order = step_14.get('step_order')

            print(f"步骤顺序:")
            print(f"  步骤12 step_order: {step_12_order}")
            print(f"  步骤13 step_order: {step_13_order}")
            print(f"  步骤14 step_order: {step_14_order}")
            print()

            if step_12_order and step_13_order:
                next_order = step_12_order + 1
                print(f"童蕾批准步骤12后，系统会查找 step_order={next_order} 的步骤")

                if step_13_order == next_order:
                    print(f"✓ 步骤13的 step_order 正确")
                    print(f"\n❓ 但为什么当前步骤是14而不是13？")
                    print(f"\n可能原因:")
                    print(f"  1. 步骤13被某种逻辑自动跳过了")
                    print(f"  2. 童蕾批准后的步骤转换逻辑有bug")
                    print(f"  3. 步骤13的分支条件没有匹配任何审批人，系统跳过了")
                    print(f"  4. gxh尝试审批步骤13失败，但系统错误地转到了步骤14")
                else:
                    print(f"❌ 步骤13的 step_order 不是 {next_order}")
                    print(f"   这会导致童蕾批准后找不到下一步，可能跳过了步骤13")

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
