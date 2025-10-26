#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 PO202510-004 批价单的审批流程详情"""
import sys, os

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

from app import create_app, db
from sqlalchemy import text
import json

def main():
    app = create_app()

    with app.app_context():
        print("\n=== 检查 PO202510-004 批价单审批流程 ===\n")

        # 1. 查找批价单
        po_result = db.session.execute(text("""
            SELECT id, order_number, status, created_at, updated_at,
                   pricing_total_discount_rate, settlement_total_discount_rate
            FROM pricing_orders
            WHERE order_number = 'PO202510-004'
        """)).fetchone()

        if not po_result:
            print("❌ 未找到批价单 PO202510-004")
            return

        po_id = po_result[0]
        print(f"批价单ID: {po_id}")
        print(f"订单号: {po_result[1]}")
        print(f"状态: {po_result[2]}")
        print(f"创建时间: {po_result[3]}")
        print(f"更新时间: {po_result[4]}")
        print(f"批价折扣率: {po_result[5]} ({po_result[5]*100:.1f}%)")
        print(f"结算折扣率: {po_result[6]} ({po_result[6]*100:.1f}%)")

        # 2. 查找审批实例
        print(f"\n=== 审批实例信息 ===\n")

        instance_result = db.session.execute(text("""
            SELECT ai.id, ai.status, ai.current_step, ai.started_at, ai.ended_at,
                   ai.template_snapshot, u.real_name as submitter
            FROM approval_instance ai
            JOIN users u ON ai.created_by = u.id
            WHERE ai.object_type = 'pricing_order' AND ai.object_id = :po_id
            ORDER BY ai.started_at DESC
            LIMIT 1
        """), {'po_id': po_id}).fetchone()

        if not instance_result:
            print("❌ 未找到审批实例")
            return

        instance_id = instance_result[0]
        instance_status = instance_result[1]
        current_step = instance_result[2]
        template_snapshot = instance_result[5]

        print(f"实例ID: {instance_id}")
        print(f"提交人: {instance_result[6]}")
        print(f"实例状态: {instance_status}")
        print(f"当前步骤ID: {current_step}")
        print(f"开始时间: {instance_result[3]}")
        print(f"结束时间: {instance_result[4]}")

        # 3. 解析模板快照中的步骤
        print(f"\n=== 流程步骤配置（模板快照）===\n")

        if template_snapshot:
            if isinstance(template_snapshot, str):
                import json
                template_snapshot = json.loads(template_snapshot)

            steps = template_snapshot.get('steps', [])
            print(f"总共 {len(steps)} 个步骤:\n")

            for i, step in enumerate(steps):
                step_id = step.get('step_id')
                step_name = step.get('step_name')
                step_type = step.get('step_type')
                action_type = step.get('action_type')
                approver_name = step.get('approver_real_name') or step.get('approver_username')

                marker = "👉" if step_id == current_step else "  "
                print(f"{marker} 步骤{i+1} (ID:{step_id}): {step_name}")
                print(f"     - 类型: {step_type}")
                print(f"     - 审批人: {approver_name or '分支决策'}")
                print(f"     - 动作: {action_type}")

                if step_id == current_step:
                    print(f"     ⚠️ 当前停留在此步骤")

                print()

        # 4. 查找所有审批记录
        print(f"\n=== 审批记录详情 ===\n")

        records = db.session.execute(text("""
            SELECT ar.id, ar.step_id, u.real_name, ar.action, ar.status, ar.timestamp, ar.comment
            FROM approval_record ar
            JOIN users u ON ar.approver_id = u.id
            WHERE ar.instance_id = :instance_id
            ORDER BY ar.timestamp ASC
        """), {'instance_id': instance_id}).fetchall()

        print(f"总共 {len(records)} 条审批记录:\n")

        for rec in records:
            record_id = rec[0]
            step_id = rec[1]
            approver = rec[2]
            action = rec[3]
            status = rec[4]
            timestamp = rec[5]
            comment = rec[6]

            marker = "👉" if approver == "郭小会" else "  "
            status_icon = "✓" if status == "approved" else "⏳" if status == "pending" else "❌"

            print(f"{marker} 记录{record_id}: 步骤{step_id} - {approver:10}")
            print(f"     {status_icon} action={action:10} status={status:10}")
            print(f"     时间: {timestamp}")
            if comment:
                print(f"     备注: {comment}")
            print()

        # 5. 分析问题
        print(f"\n=== 问题分析 ===\n")

        gxh_record = None
        for rec in records:
            if rec[2] == "郭小会":
                gxh_record = rec
                break

        if gxh_record:
            gxh_status = gxh_record[4]
            gxh_step_id = gxh_record[1]

            print(f"gxh的审批记录:")
            print(f"  - 步骤ID: {gxh_step_id}")
            print(f"  - action: {gxh_record[3]}")
            print(f"  - status: {gxh_status}")
            print(f"  - 时间: {gxh_record[5]}")

            if gxh_status == "approved":
                print(f"\n  ✓ gxh的记录状态正确（approved）")
                print(f"  → 如果前端仍显示等待，可能是前端缓存问题")
                print(f"  → 建议：强制刷新页面（Ctrl+Shift+R）")
            else:
                print(f"\n  ❌ gxh的记录状态异常: {gxh_status}")
                print(f"  → 需要手动更新状态")

            # 检查是否是分支步骤
            if template_snapshot:
                steps = template_snapshot.get('steps', [])
                for step in steps:
                    if step.get('step_id') == gxh_step_id:
                        if step.get('step_type') == 'branch':
                            print(f"\n  ℹ️  这是一个分支决策步骤")
                            branch_condition = step.get('branch_condition')
                            if branch_condition:
                                conditions = branch_condition.get('conditions', [])
                                print(f"  → 分支条件数: {len(conditions)}")
                                for cond in conditions:
                                    if cond.get('approver_id') == 13:  # gxh的ID
                                        print(f"  → gxh负责的条件: {cond.get('value')}")
                                        print(f"  → 执行的动作: {cond.get('action')}")

        print("\n=== 检查完成 ===\n")

if __name__ == '__main__':
    main()
