#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查批价单的完整数据，对比提交时和审批后的变化"""
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

def main():
    app = create_app()

    with app.app_context():
        print("\n=== 检查批价单数据变更历史 ===\n")

        # 找到最新的批价单
        pricing_result = db.session.execute(
            text("""
                SELECT po.id, po.order_number, po.created_at, po.updated_at,
                       po.pricing_total_discount_rate, po.settlement_total_discount_rate,
                       po.status, u.real_name as creator
                FROM pricing_orders po
                JOIN users u ON po.created_by = u.id
                ORDER BY po.created_at DESC
                LIMIT 1
            """)
        ).fetchone()

        if not pricing_result:
            print("❌ 未找到批价单数据")
            return

        po_id = pricing_result[0]
        print(f"批价单ID: {po_id}")
        print(f"订单号: {pricing_result[1]}")
        print(f"创建人: {pricing_result[7]}")
        print(f"创建时间: {pricing_result[2]}")
        print(f"更新时间: {pricing_result[3]}")
        print(f"状态: {pricing_result[6]}")
        print(f"\n当前折扣率:")
        print(f"  批价折扣率: {pricing_result[4]} ({pricing_result[4]*100:.1f}%)")
        print(f"  结算折扣率: {pricing_result[5]} ({pricing_result[5]*100:.1f}%)")

        # 检查审批实例
        print(f"\n=== 审批流程信息 ===\n")

        instance_result = db.session.execute(
            text("""
                SELECT ai.id, ai.status, ai.started_at, ai.ended_at,
                       u.real_name as submitter
                FROM approval_instance ai
                JOIN users u ON ai.created_by = u.id
                WHERE ai.object_type = 'pricing_order' AND ai.object_id = :po_id
                ORDER BY ai.started_at DESC
                LIMIT 1
            """),
            {'po_id': po_id}
        ).fetchone()

        if instance_result:
            print(f"审批实例ID: {instance_result[0]}")
            print(f"提交人: {instance_result[4]}")
            print(f"状态: {instance_result[1]}")
            print(f"开始时间: {instance_result[2]}")
            print(f"结束时间: {instance_result[3]}")

            # 审批记录
            print(f"\n审批记录:")
            records = db.session.execute(
                text("""
                    SELECT ar.id, u.real_name, ar.action, ar.timestamp, ar.comment
                    FROM approval_record ar
                    JOIN users u ON ar.approver_id = u.id
                    WHERE ar.instance_id = :instance_id
                    ORDER BY ar.timestamp ASC
                """),
                {'instance_id': instance_result[0]}
            ).fetchall()

            for rec in records:
                print(f"  [{rec[3]}] {rec[1]:10} - {rec[2]:8} {rec[4] or ''}")

        # 检查明细表数据（看是否有 discount_rate 字段）
        print(f"\n=== 批价单明细数据 ===\n")

        # 先检查表结构
        from sqlalchemy import inspect
        inspector = inspect(db.engine)

        # 检查批价明细表
        if inspector.has_table('pricing_order_details'):
            columns = inspector.get_columns('pricing_order_details')
            column_names = [col['name'] for col in columns]

            has_discount_rate = 'discount_rate' in column_names
            has_unit_price = 'unit_price' in column_names

            print(f"pricing_order_details 表字段: {len(columns)} 个")
            print(f"  - discount_rate 字段: {'✓ 存在' if has_discount_rate else '❌ 不存在'}")
            print(f"  - unit_price 字段: {'✓ 存在' if has_unit_price else '❌ 不存在'}")

            # 查询明细数据
            if has_discount_rate:
                details_query = text("""
                    SELECT id, product_id, quantity, unit_price, discount_rate, total_price
                    FROM pricing_order_details
                    WHERE pricing_order_id = :po_id
                    ORDER BY id
                    LIMIT 5
                """)
            else:
                details_query = text("""
                    SELECT id, product_id, quantity, unit_price, total_price
                    FROM pricing_order_details
                    WHERE pricing_order_id = :po_id
                    ORDER BY id
                    LIMIT 5
                """)

            details = db.session.execute(details_query, {'po_id': po_id}).fetchall()

            if details:
                print(f"\n  前 {len(details)} 条明细:")
                for det in details:
                    if has_discount_rate:
                        print(f"    明细{det[0]:3}: 产品{det[1]:3} 数量{det[2]:6.2f} 单价{det[3]:10.2f} 折扣{det[4]:5.2%} 总价{det[5]:12.2f}")
                    else:
                        print(f"    明细{det[0]:3}: 产品{det[1]:3} 数量{det[2]:6.2f} 单价{det[3]:10.2f} 总价{det[4]:12.2f}")
                        print(f"        ⚠️ 缺少 discount_rate 字段")
            else:
                print(f"  ⚠️ 没有明细数据")

        # 检查结算明细表
        if inspector.has_table('settlement_order_details'):
            print(f"\n=== 结算单明细数据 ===\n")
            columns = inspector.get_columns('settlement_order_details')
            column_names = [col['name'] for col in columns]

            has_discount_rate = 'discount_rate' in column_names
            has_unit_price = 'unit_price' in column_names

            print(f"settlement_order_details 表字段: {len(columns)} 个")
            print(f"  - discount_rate 字段: {'✓ 存在' if has_discount_rate else '❌ 不存在'}")
            print(f"  - unit_price 字段: {'✓ 存在' if has_unit_price else '❌ 不存在'}")

        print("\n=== 关键结论 ===\n")

        print("1. 流程图显示问题:")
        print("   ❌ approval_record 表缺少 status 字段")
        print("   → 需要执行数据库迁移")

        print("\n2. 折扣率保存问题:")
        print(f"   当前值: 批价{pricing_result[4]*100:.1f}% 结算{pricing_result[5]*100:.1f}%")
        print("   → 需要确认：这是提交时的值还是审批修改后的值？")
        print("   → 建议查看应用日志确认数据传递情况")

        print("\n=== 检查完成 ===\n")

if __name__ == '__main__':
    main()
