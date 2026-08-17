#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证「报备模板两步→三步原地升级」不会打断在办审批单。

复刻 CN 生产现状:在办报备实例都是两步快照、current_step=2(等总经理)。
本脚本把模板退回两步 → 造一个同形态在办实例 → 跑升级 → 断言:
  · current_step 不变(仍=2)
  · get_current_step_info() 仍指向「总经理审批」(不会被退回业务线经理)
  · get_step_actual_approver() 仍解析出总经理(designated_approvers 按 step_id,不受重排影响)

跑法: export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
      python3 scripts/temp/check_report_flow_inflight.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app, Sandbox                  # noqa: E402

app = make_app()
LEGACY_NAMES = ('业务线经理审批', '总经理审批')

with app.app_context():
    from datetime import datetime
    from app import db
    from app.models.approval import (ApprovalProcessTemplate, ApprovalStep,
                                     ApprovalInstance, ApprovalStatus)
    from app.models.project import Project
    from app.models.user import User
    from app.helpers.project_hold_helpers import REPORT_TEMPLATE_NAME, get_or_create_report_template
    from app.helpers.approval_helpers import get_step_actual_approver

    sb = Sandbox()
    ok = False
    try:
        tpl = ApprovalProcessTemplate.query.filter_by(
            object_type='project', name=REPORT_TEMPLATE_NAME).first()

        # ── 1. 把模板退回「两步」形态,复刻升级前的生产状态 ──────────────────────
        for s in ApprovalStep.query.filter_by(process_id=tpl.id).all():
            if s.step_name not in LEGACY_NAMES:
                db.session.delete(s)
        db.session.flush()
        legacy = (ApprovalStep.query.filter_by(process_id=tpl.id)
                  .order_by(ApprovalStep.step_order).all())
        assert len(legacy) == 2, f"退回两步失败: {[(s.step_order, s.step_name) for s in legacy]}"
        legacy[0].step_order, legacy[1].step_order = 1, 2
        db.session.flush()
        biz_step, ceo_step = legacy
        print("\n=== 升级前(两步) ===")
        print(f"  step1 id={biz_step.id} {biz_step.step_name}")
        print(f"  step2 id={ceo_step.id} {ceo_step.step_name}")

        # ── 2. 造一个「已过业务线经理、停在总经理」的在办实例 ──────────────────
        ceo = User.query.filter(User.role == 'ceo', User._is_active.is_(True)).first()
        biz = User.query.filter(User.role == 'sales_director', User._is_active.is_(True)).first()
        proj = Project.query.filter(Project.is_deleted == False).first()          # noqa: E712
        snap = {
            'template_id': tpl.id, 'template_name': tpl.name, 'object_type': 'project',
            'created_at': datetime.now().isoformat(), 'biz_line_route': True,
            'steps': [
                {'step_id': biz_step.id, 'step_order': 1, 'step_name': biz_step.step_name,
                 'approver_type': 'submitter_designate', 'approver_user_id': None},
                {'step_id': ceo_step.id, 'step_order': 2, 'step_name': ceo_step.step_name,
                 'approver_type': 'submitter_designate', 'approver_user_id': None},
            ],
        }
        inst = ApprovalInstance(
            process_id=tpl.id, object_id=proj.id, object_type='project',
            current_step=2, status=ApprovalStatus.PENDING, started_at=datetime.now(),
            created_by=proj.owner_id or ceo.id, template_snapshot=snap,
            designated_approvers={str(biz_step.id): biz.id, str(ceo_step.id): ceo.id})
        db.session.add(inst)
        db.session.flush()
        before_cur = inst.current_step
        before_name = (inst.get_current_step_info() or {}).get('step_name')
        print(f"  在办实例 id={inst.id} current_step={before_cur} 当前步={before_name}")
        assert before_name == '总经理审批'

        # ── 3. 跑升级 ────────────────────────────────────────────────────────
        print("\n=== 执行升级 ===")
        tpl, s1, s2, s3 = get_or_create_report_template()
        for s in ApprovalStep.query.filter_by(process_id=tpl.id).order_by(ApprovalStep.step_order):
            print(f"  step_order={s.step_order} id={s.id} {s.step_name}")

        # ── 4. 断言在办实例不受影响 ──────────────────────────────────────────
        db.session.refresh(inst)
        after_cur = inst.current_step
        cur_info = inst.get_current_step_info() or {}
        actual = get_step_actual_approver(cur_info, inst)
        print("\n=== 在办实例升级后 ===")
        print(f"  current_step {before_cur} → {after_cur}")
        print(f"  当前步        {before_name} → {cur_info.get('step_name')}")
        print(f"  实际审批人     {(actual.real_name if actual else None)}")
        print(f"  快照步骤       {[(x['step_order'], x['step_name']) for x in inst.get_steps()]}")

        ok = (after_cur == before_cur
              and cur_info.get('step_name') == '总经理审批'
              and actual is not None and actual.id == ceo.id)
        print(f"\n  结论: {'✅ 在办单不受影响,仍停在总经理' if ok else '❌ 在办单被打断!'}")
    finally:
        sb.teardown()
        # teardown 里 rollback 会把「退回两步」也丢掉,但若已 commit 过则需补一次升级
        get_or_create_report_template()
        print("  (模板保持三步)\n")
    assert ok
