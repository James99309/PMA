#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复SQL批量导入的35个批价单/结算单的单号和日期

问题：2026-02-07 SQL导入时，所有单号使用导入时间生成（PO202602-xxx），
     created_at/approved_at 也都是 2026-02-07。
修复：根据实际批价月份重新分配单号和日期。
"""
import sys
import os
import argparse
from datetime import datetime

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    # Docker 环境下可能直接在 /app
    if os.path.exists('/app/app') and os.path.exists('/app/run.py'):
        return '/app'
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())
from app import create_app, db
from app.models.pricing_order import PricingOrder, SettlementOrder, PricingOrderApprovalRecord

# ============================================================
# PO ID → 正确的批价年月 (YYYYMM)
# ============================================================
CORRECTIONS = {
    # 2025年3月 (9条)
    129: '202503', 130: '202503', 131: '202503', 136: '202503',
    144: '202503', 146: '202503', 157: '202503', 158: '202503', 161: '202503',
    # 2025年4月 (8条)
    128: '202504', 138: '202504', 142: '202504', 145: '202504',
    151: '202504', 153: '202504', 156: '202504', 162: '202504',
    # 2025年5月 (7条)
    134: '202505', 135: '202505', 148: '202505', 152: '202505',
    154: '202505', 155: '202505', 159: '202505',
    # 2025年6月 (1条)
    137: '202506',
    # 2025年9月 (9条)
    132: '202509', 133: '202509', 139: '202509', 140: '202509',
    141: '202509', 143: '202509', 147: '202509', 149: '202509', 160: '202509',
    # 2025年11月 (1条)
    150: '202511',
}


def get_existing_max_numbers():
    """查询各月份现有的最大编号"""
    months = sorted(set(CORRECTIONS.values()))
    max_numbers = {}

    for month in months:
        po_prefix = f"PO{month}"
        latest_po = PricingOrder.query.filter(
            PricingOrder.order_number.like(f"{po_prefix}-%"),
            ~PricingOrder.id.in_(CORRECTIONS.keys())  # 排除待修复的记录
        ).order_by(PricingOrder.order_number.desc()).first()

        if latest_po:
            max_numbers[month] = int(latest_po.order_number[-3:])
        else:
            max_numbers[month] = 0

    return max_numbers


def build_correction_plan(max_numbers):
    """构建修正计划：为每个PO分配新编号"""
    # 按月分组，月内按PO ID排序（保持稳定顺序）
    by_month = {}
    for po_id, month in CORRECTIONS.items():
        by_month.setdefault(month, []).append(po_id)

    for month in by_month:
        by_month[month].sort()

    plan = {}  # po_id -> {month, po_number, so_number, created_at}
    counters = dict(max_numbers)  # 复制一份计数器

    for month in sorted(by_month.keys()):
        year = int(month[:4])
        mon = int(month[4:])
        target_date = datetime(year, mon, 15)

        for po_id in by_month[month]:
            counters[month] += 1
            seq = counters[month]
            po_number = f"PO{month}-{seq:03d}"
            so_number = f"SO{month}-{seq:03d}"

            plan[po_id] = {
                'month': month,
                'po_number': po_number,
                'so_number': so_number,
                'created_at': target_date,
            }

    return plan


def execute_fix(plan, dry_run=True):
    """执行修复"""
    print(f"\n{'=' * 70}")
    print(f"  批价单/结算单 单号和日期修复 ({'DRY RUN' if dry_run else '正式执行'})")
    print(f"{'=' * 70}")
    print(f"  待修复记录: {len(plan)} 条")
    print()

    # 按月分组显示
    by_month = {}
    for po_id, info in plan.items():
        by_month.setdefault(info['month'], []).append((po_id, info))

    updated_po = 0
    updated_so = 0
    updated_ar = 0
    errors = []

    for month in sorted(by_month.keys()):
        items = by_month[month]
        print(f"\n--- {month[:4]}年{int(month[4:])}月 ({len(items)}条) ---")

        for po_id, info in items:
            po = db.session.get(PricingOrder, po_id)
            if not po:
                msg = f"  [错误] PO ID {po_id} 不存在!"
                print(msg)
                errors.append(msg)
                continue

            old_po_number = po.order_number
            old_created = po.created_at
            new_po_number = info['po_number']
            new_so_number = info['so_number']
            target_date = info['created_at']

            # 显示变更
            print(f"  PO #{po_id}: {old_po_number} → {new_po_number}  |  "
                  f"{old_created.strftime('%Y-%m-%d') if old_created else 'None'} → {target_date.strftime('%Y-%m-%d')}")

            if not dry_run:
                # 更新 PricingOrder
                po.order_number = new_po_number
                po.created_at = target_date
                po.updated_at = target_date
                if po.approved_at:
                    po.approved_at = target_date
                updated_po += 1

            # 查找关联的 SettlementOrder
            so = SettlementOrder.query.filter_by(pricing_order_id=po_id).first()
            if so:
                old_so_number = so.order_number
                print(f"    SO #{so.id}: {old_so_number} → {new_so_number}")

                if not dry_run:
                    so.order_number = new_so_number
                    so.created_at = target_date
                    so.updated_at = target_date
                    if so.approved_at:
                        so.approved_at = target_date
                    updated_so += 1
            else:
                print(f"    [警告] PO #{po_id} 没有关联的结算单")

            # 查找关联的审批记录
            approval_records = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=po_id
            ).all()
            for ar in approval_records:
                if ar.approved_at:
                    if not dry_run:
                        ar.approved_at = target_date
                        updated_ar += 1
                    else:
                        print(f"    AR #{ar.id}: approved_at → {target_date.strftime('%Y-%m-%d')}")

    # 提交
    if not dry_run:
        db.session.commit()
        print(f"\n{'=' * 70}")
        print(f"  ✅ 修复完成!")
        print(f"     更新 PricingOrder: {updated_po} 条")
        print(f"     更新 SettlementOrder: {updated_so} 条")
        print(f"     更新 ApprovalRecord: {updated_ar} 条")
    else:
        print(f"\n{'=' * 70}")
        print(f"  📋 DRY RUN 完成 - 未做任何修改")
        print(f"     将更新 PricingOrder: {len(plan)} 条")

    if errors:
        print(f"\n  ⚠️ 错误 ({len(errors)}):")
        for e in errors:
            print(f"    {e}")

    # 验证唯一性
    print(f"\n--- 编号唯一性验证 ---")
    all_po_numbers = [info['po_number'] for info in plan.values()]
    all_so_numbers = [info['so_number'] for info in plan.values()]

    # 检查新编号之间是否重复
    if len(all_po_numbers) != len(set(all_po_numbers)):
        print("  ❌ 新PO编号有重复!")
    else:
        print(f"  ✅ 新PO编号唯一 ({len(all_po_numbers)}条)")

    if len(all_so_numbers) != len(set(all_so_numbers)):
        print("  ❌ 新SO编号有重复!")
    else:
        print(f"  ✅ 新SO编号唯一 ({len(all_so_numbers)}条)")

    # 检查与数据库中已有编号是否冲突
    for po_num in all_po_numbers:
        existing = PricingOrder.query.filter(
            PricingOrder.order_number == po_num,
            ~PricingOrder.id.in_(CORRECTIONS.keys())
        ).first()
        if existing:
            print(f"  ❌ PO编号冲突: {po_num} 已被 PO #{existing.id} 使用!")

    for so_num in all_so_numbers:
        existing = SettlementOrder.query.filter(
            SettlementOrder.order_number == so_num,
            ~SettlementOrder.pricing_order_id.in_(CORRECTIONS.keys())
        ).first()
        if existing:
            print(f"  ❌ SO编号冲突: {so_num} 已被 SO #{existing.id} 使用!")

    print(f"{'=' * 70}\n")


def main():
    parser = argparse.ArgumentParser(description='修复SQL导入的批价单单号和日期')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='仅预览变更，不实际修改数据库')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print("正在查询各月份现有最大编号...")
        max_numbers = get_existing_max_numbers()
        for month, max_num in sorted(max_numbers.items()):
            prefix = f"PO{month}"
            if max_num > 0:
                print(f"  {prefix}: 最大编号 {prefix}-{max_num:03d}")
            else:
                print(f"  {prefix}: 无现有编号")

        plan = build_correction_plan(max_numbers)
        execute_fix(plan, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
