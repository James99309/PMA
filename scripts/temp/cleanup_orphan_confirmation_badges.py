#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理老确认机制遗留的孤儿状态(让确认徽章=审批结果,列表/详情一致)。

老机制(create_confirmation_tasks)会把 confirmation_badge_status 设 pending 并锁定报价单,
但从不建 ApprovalInstance,导致:列表读徽章显示「待确认」、详情读审批实例显示「草稿」、且锁定卡死。

清理规则(幂等,可重复跑):
  对 confirmation_badge_status ∈ (pending, reconfirm) 且【无 active(PENDING/APPROVED)审批实例】的报价单:
    - confirmation_badge_status → none(clear)
    - 若被锁定(均为老机制 '产品确认中' 残留,因无 active 审批) → 解锁
  保留 confirmed(老 SM 真实确认过的,不动)。

用法: docker exec pma-app python3 /app/cleanup_orphan.py [--apply]
  默认 dry-run(只统计不改);加 --apply 才落库。
"""
import sys
import os


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
from app.models.quotation import Quotation
from app.models.approval import ApprovalInstance, ApprovalStatus


def main():
    apply = '--apply' in sys.argv
    app = create_app()
    with app.app_context():
        targets = Quotation.query.filter(
            Quotation.confirmation_badge_status.in_(['pending', 'reconfirm'])
        ).all()
        total = len(targets)
        reset = 0
        unlocked = 0
        skipped_active = 0
        samples = []
        for q in targets:
            active = ApprovalInstance.query.filter_by(
                object_type='quotation', object_id=q.id
            ).filter(ApprovalInstance.status.in_(
                [ApprovalStatus.PENDING, ApprovalStatus.APPROVED]
            )).first()
            if active:
                skipped_active += 1
                continue  # 有真实进行中/已通过审批 → 不动
            if len(samples) < 8:
                samples.append((q.quotation_number, q.confirmation_badge_status, q.is_locked))
            if apply:
                q.clear_confirmation_badge()
                if q.is_locked:
                    if hasattr(q, 'unlock'):
                        q.unlock(None)
                    else:
                        q.is_locked = False
                        q.lock_reason = None
                        q.locked_by = None
                        q.locked_at = None
            else:
                if q.is_locked:
                    pass
            reset += 1
            if q.is_locked:
                unlocked += 1
        # ── Step B:badge 同步审批实例(让列表=详情) ──
        #   有 PENDING 实例 → badge=pending;有 APPROVED 实例(无pending) → badge=confirmed
        sync_pending = 0
        sync_confirmed = 0
        for q in Quotation.query.all():
            pend = ApprovalInstance.query.filter_by(
                object_type='quotation', object_id=q.id
            ).filter(ApprovalInstance.status == ApprovalStatus.PENDING).first()
            appr = ApprovalInstance.query.filter_by(
                object_type='quotation', object_id=q.id
            ).filter(ApprovalInstance.status == ApprovalStatus.APPROVED).first()
            cur = q.confirmation_badge_status or 'none'
            if pend and cur != 'pending':
                if apply:
                    q.set_pending_confirmation_badge() if cur == 'none' else None
                    q.confirmation_badge_status = 'pending'
                    q.confirmation_badge_color = '#f97316'
                sync_pending += 1
            elif appr and not pend and cur != 'confirmed':
                if apply:
                    q.set_confirmation_badge('#28a745', appr.created_by)
                sync_confirmed += 1
        if apply:
            db.session.commit()
        print(f"== {'已落库 APPLY' if apply else 'DRY-RUN(未改)'} ==")
        print(f"[A] badge∈(pending,reconfirm) 总数: {total}")
        print(f"    跳过(有 active 审批实例,不动): {skipped_active}")
        print(f"    归位为 none 的孤儿: {reset}  其中解锁: {unlocked}")
        print(f"[B] 同步: pending实例→pending: {sync_pending}  approved实例→confirmed: {sync_confirmed}")
        print("  样例(A):")
        for n, b, lk in samples:
            print(f"    {n}  badge={b}  locked={lk}")


if __name__ == '__main__':
    main()
