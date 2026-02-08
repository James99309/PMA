#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Python脚本导入的7条批价单的 created_by 字段

问题：2026-02-08 Python脚本导入时，所有 created_by 被设为 5（管理员），
     应该根据 Excel "销售归属"列设置为对应的销售人员。
"""
import sys
import os
import argparse

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
from app.models.pricing_order import PricingOrder, SettlementOrder

# ============================================================
# PO ID → 正确的 created_by (User ID)
# ============================================================
CORRECTIONS = {
    163: 15,  # 阿里达摩院增补改建项目 → 李华伟
    164: 16,  # 合肥瑶海区增补 → 范敬
    165: 13,  # 康桥二期(防爆天线) → 郭小会
    166: 13,  # 康桥二期(硬件+软件-软件) → 郭小会
    167: 13,  # 康桥二期(硬件+软件-硬件) → 郭小会
    168: 16,  # 无锡奥林匹克(硬件) → 范敬
    169: 16,  # 无锡奥林匹克(软件) → 范敬
}

WRONG_CREATED_BY = 5  # 错误值：管理员


def execute_fix(dry_run=True):
    """执行修复"""
    print(f"\n{'=' * 70}")
    print(f"  批价单/结算单 created_by 修复 ({'DRY RUN' if dry_run else '正式执行'})")
    print(f"{'=' * 70}")
    print(f"  待修复记录: {len(CORRECTIONS)} 条")
    print(f"  错误值: created_by = {WRONG_CREATED_BY}")
    print()

    updated_po = 0
    updated_so = 0
    errors = []

    for po_id, correct_user_id in sorted(CORRECTIONS.items()):
        po = db.session.get(PricingOrder, po_id)
        if not po:
            msg = f"  [错误] PO ID {po_id} 不存在!"
            print(msg)
            errors.append(msg)
            continue

        # 验证当前值确实是错误的
        if po.created_by != WRONG_CREATED_BY:
            msg = f"  [跳过] PO #{po_id} created_by = {po.created_by} (不是 {WRONG_CREATED_BY}，可能已修复)"
            print(msg)
            continue

        print(f"  PO #{po_id} ({po.order_number}): created_by {po.created_by} → {correct_user_id}")

        if not dry_run:
            po.created_by = correct_user_id
            updated_po += 1

        # 查找关联的 SettlementOrder
        so = SettlementOrder.query.filter_by(pricing_order_id=po_id).first()
        if so:
            if so.created_by != WRONG_CREATED_BY:
                print(f"    SO #{so.id} ({so.order_number}): created_by = {so.created_by} (不是 {WRONG_CREATED_BY}，跳过)")
            else:
                print(f"    SO #{so.id} ({so.order_number}): created_by {so.created_by} → {correct_user_id}")
                if not dry_run:
                    so.created_by = correct_user_id
                    updated_so += 1
        else:
            print(f"    [警告] PO #{po_id} 没有关联的结算单")

    # 提交
    if not dry_run:
        db.session.commit()
        print(f"\n{'=' * 70}")
        print(f"  ✅ 修复完成!")
        print(f"     更新 PricingOrder: {updated_po} 条")
        print(f"     更新 SettlementOrder: {updated_so} 条")
    else:
        print(f"\n{'=' * 70}")
        print(f"  📋 DRY RUN 完成 - 未做任何修改")

    if errors:
        print(f"\n  ⚠️ 错误 ({len(errors)}):")
        for e in errors:
            print(f"    {e}")

    print(f"{'=' * 70}\n")


def main():
    parser = argparse.ArgumentParser(description='修复Python导入批价单的 created_by 字段')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='仅预览变更，不实际修改数据库')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        execute_fix(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
