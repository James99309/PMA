#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复已导入批价单状态：设置审批通过 + 项目签约锁定

已导入7个批价单+7个结算单状态为draft，需修复为approved。
同时更新关联项目状态为signed并锁定。
"""
import sys
import os
import argparse

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
from app.models.pricing_order import PricingOrder, SettlementOrder, PricingOrderApprovalRecord
from app.models.project import Project
from app.models.projectpm_stage_history import ProjectStageHistory
from datetime import datetime

# ========== 配置 ==========

ADMIN_USER_ID = 5  # admin 用户

# 需要修复的批价单ID列表
PRICING_ORDER_IDS = [163, 164, 165, 166, 167, 168, 169]

# 对应的结算单ID列表
SETTLEMENT_ORDER_IDS = [156, 157, 158, 159, 160, 161, 162]

# 需要更新项目状态的项目ID（排除已签约的63）
PROJECT_IDS_TO_UPDATE = [601, 675, 100]

# 已经是signed状态的项目ID（跳过）
PROJECT_IDS_SKIP = [63]


def fix_pricing_orders(dry_run=True):
    """修复批价单和结算单状态"""
    app = create_app()
    with app.app_context():
        now = datetime.utcnow()
        errors = []

        print("=" * 60)
        print(f"{'[DRY RUN] ' if dry_run else ''}修复已导入批价单状态")
        print("=" * 60)

        # ===== 1. 更新批价单状态 =====
        print("\n--- 步骤1: 更新批价单状态 ---")
        for po_id in PRICING_ORDER_IDS:
            po = PricingOrder.query.get(po_id)
            if not po:
                errors.append(f"批价单 ID={po_id} 不存在")
                print(f"  ❌ 批价单 ID={po_id} 不存在!")
                continue

            print(f"  批价单 {po.order_number} (ID={po.id})")
            print(f"    当前状态: {po.status}")

            if po.status == 'approved':
                print(f"    ⏭ 已是 approved，跳过")
                continue

            if not dry_run:
                po.status = 'approved'
                po.approved_by = ADMIN_USER_ID
                po.approved_at = po.created_at  # 使用批价日期作为审批时间

            print(f"    → status=approved, approved_by={ADMIN_USER_ID}, approved_at={po.created_at}")

        # ===== 2. 更新结算单状态 =====
        print("\n--- 步骤2: 更新结算单状态 ---")
        for so_id in SETTLEMENT_ORDER_IDS:
            so = SettlementOrder.query.get(so_id)
            if not so:
                errors.append(f"结算单 ID={so_id} 不存在")
                print(f"  ❌ 结算单 ID={so_id} 不存在!")
                continue

            print(f"  结算单 {so.order_number} (ID={so.id})")
            print(f"    当前状态: {so.status}")

            if so.status == 'approved':
                print(f"    ⏭ 已是 approved，跳过")
                continue

            if not dry_run:
                so.status = 'approved'
                so.approved_by = ADMIN_USER_ID
                so.approved_at = so.created_at

            print(f"    → status=approved, approved_by={ADMIN_USER_ID}, approved_at={so.created_at}")

        # ===== 3. 创建审批记录 =====
        print("\n--- 步骤3: 创建审批记录 ---")
        for po_id in PRICING_ORDER_IDS:
            po = PricingOrder.query.get(po_id)
            if not po:
                continue

            # 检查是否已有审批记录
            existing = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=po_id,
                action='approve'
            ).first()

            if existing:
                print(f"  ⏭ 批价单 {po.order_number} 已有审批记录，跳过")
                continue

            record = PricingOrderApprovalRecord(
                pricing_order_id=po_id,
                step_order=1,
                step_name='审批',
                approver_role='approver',
                approver_id=ADMIN_USER_ID,
                action='approve',
                comment='线下已审批，系统批量导入补录',
                approved_at=po.created_at,
                is_fast_approval=False
            )

            if not dry_run:
                db.session.add(record)

            print(f"  ✅ 批价单 {po.order_number}: 创建审批记录 (approved_at={po.created_at})")

        # ===== 4. 更新项目状态 =====
        print("\n--- 步骤4: 更新项目状态 ---")
        for pid in PROJECT_IDS_SKIP:
            proj = Project.query.get(pid)
            if proj:
                print(f"  ⏭ 项目 {proj.project_name} (ID={pid}): 已是 {proj.current_stage}/{proj.activity_status}，跳过")

        for pid in PROJECT_IDS_TO_UPDATE:
            proj = Project.query.get(pid)
            if not proj:
                errors.append(f"项目 ID={pid} 不存在")
                print(f"  ❌ 项目 ID={pid} 不存在!")
                continue

            old_stage = proj.current_stage
            print(f"  项目 {proj.project_name} (ID={pid})")
            print(f"    当前: stage={old_stage}, locked={proj.is_locked}, activity={proj.activity_status}")

            if proj.current_stage == 'signed' and proj.is_locked:
                print(f"    ⏭ 已是 signed + locked，跳过")
                continue

            if not dry_run:
                proj.current_stage = 'signed'
                proj.is_locked = True
                proj.locked_reason = '项目已签约，自动锁定'
                proj.locked_by = ADMIN_USER_ID
                proj.locked_at = now
                proj.is_active = False
                proj.activity_status = 'frozen'
                proj.activity_reason = '项目已签约，活跃度已冻结'

            print(f"    → stage=signed, locked=True, activity=frozen")

        # ===== 5. 创建项目阶段历史 =====
        print("\n--- 步骤5: 创建项目阶段历史 ---")
        for pid in PROJECT_IDS_TO_UPDATE:
            proj = Project.query.get(pid)
            if not proj:
                continue

            # 注意：如果是 dry_run，proj.current_stage 仍是原值
            from_stage = proj.current_stage if dry_run else 'quoted'  # 执行时原值已被改，用硬编码

            if not dry_run:
                ProjectStageHistory.add_history_record(
                    project_id=pid,
                    from_stage='quoted',
                    to_stage='signed',
                    change_date=now,
                    remarks='批价单审批通过自动推进（批量导入补录）',
                    commit=False
                )

            print(f"  ✅ 项目 {proj.project_name} (ID={pid}): quoted → signed")

        # ===== 提交或回滚 =====
        if errors:
            print(f"\n⚠️ 发现 {len(errors)} 个错误:")
            for e in errors:
                print(f"  - {e}")

        if dry_run:
            print(f"\n{'=' * 60}")
            print("[DRY RUN] 以上为预览，未实际修改数据库")
            print(f"{'=' * 60}")
            db.session.rollback()
        else:
            try:
                db.session.commit()
                print(f"\n{'=' * 60}")
                print("✅ 所有修改已提交!")
                print(f"{'=' * 60}")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ 提交失败，已回滚: {e}")
                raise

        # ===== 验证 =====
        print("\n--- 验证结果 ---")
        print("\n批价单状态:")
        for po_id in PRICING_ORDER_IDS:
            po = PricingOrder.query.get(po_id)
            if po:
                print(f"  {po.order_number}: status={po.status}, approved_by={po.approved_by}")

        print("\n结算单状态:")
        for so_id in SETTLEMENT_ORDER_IDS:
            so = SettlementOrder.query.get(so_id)
            if so:
                print(f"  {so.order_number}: status={so.status}, approved_by={so.approved_by}")

        print("\n审批记录:")
        for po_id in PRICING_ORDER_IDS:
            count = PricingOrderApprovalRecord.query.filter_by(pricing_order_id=po_id).count()
            print(f"  批价单 ID={po_id}: {count} 条审批记录")

        print("\n项目状态:")
        for pid in PROJECT_IDS_TO_UPDATE + PROJECT_IDS_SKIP:
            proj = Project.query.get(pid)
            if proj:
                print(f"  {proj.project_name} (ID={pid}): stage={proj.current_stage}, locked={proj.is_locked}, activity={proj.activity_status}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='修复已导入批价单状态')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改')
    args = parser.parse_args()

    fix_pricing_orders(dry_run=args.dry_run)
