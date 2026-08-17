#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端验证「中间级失效」不卡流程:业务线经理本人发起报备 →
商务初审(童蕾)通过 → 应自动跳过业务线经理这级 → 直达总经理。

这是三级化后新出现的失效形态:submitter_designate 步没指定审批人时引擎默认不跳,
若不处理会卡在「无人可审」。对照组:常规发起 → 初审通过后应正常落到业务线经理。

跑法: export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
      python3 scripts/temp/check_report_flow_midskip.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app, Sandbox                  # noqa: E402

app = make_app()
results = []

with app.app_context():
    from app import db
    from app.models.approval import ApprovalInstance, ApprovalRecord
    from app.models.project import Project
    from app.models.user import User
    from app.helpers.project_hold_helpers import (
        submit_project_report_approval, resolve_report_approvers)
    from app.helpers.approval_helpers import process_approval

    sb = Sandbox()
    try:
        def _name(u):
            return (u.real_name or u.username) if u else None

        used = set()

        def fresh_channel_project():
            for p in Project.query.filter(Project.project_type == 'channel_follow',
                                          Project.is_deleted == False).all():      # noqa: E712
                if p.id in used:
                    continue
                if not ApprovalInstance.query.filter_by(object_type='project',
                                                        object_id=p.id).first():
                    used.add(p.id)
                    return sb.watch(p)
            return None

        base = fresh_channel_project()
        pre, biz, ceo, _ = resolve_report_approvers(base)
        print(f"基准: 初审={_name(pre)} 业务线={_name(biz)}({biz.role}) 总经理={_name(ceo)}\n")

        def case(label, submitter_id, expect_after_first_approval):
            p = fresh_channel_project()
            inst, err = submit_project_report_approval(p, submitter_id)
            if err or not inst:
                print(f"【{label}】发起失败: {err}")
                return
            db.session.flush()
            print(f"【{label}】发起人={_name(db.session.get(User, submitter_id))} "
                  f"项目#{p.id} 实例{inst.id}")
            cur = inst.get_current_step_info() or {}
            print(f"  发起后当前步 = {cur.get('step_name')} (order={inst.current_step})")
            marks = [(s['step_order'], s['step_name'], s.get('auto_skip', False))
                     for s in inst.get_steps()]
            print(f"  快照 auto_skip 标记: {marks}")

            approver_id = (inst.designated_approvers or {}).get(str(cur.get('step_id')))
            process_approval(inst.id, 'approve', comment='测试通过', user_id=approver_id)
            db.session.flush()
            db.session.refresh(inst)
            cur2 = inst.get_current_step_info() or {}
            got = (cur2.get('step_name') if inst.status.name == 'PENDING'
                   else f"流程结束({inst.status.name})")
            print(f"  {_name(db.session.get(User, approver_id))} 通过 → "
                  f"当前步 = {got} (order={inst.current_step})")
            for r in ApprovalRecord.query.filter_by(instance_id=inst.id).order_by(ApprovalRecord.id):
                print(f"    记录 step_id={r.step_id} {r.action}: {r.comment}")
            passed = got == expect_after_first_approval
            print(f"  期望 = {expect_after_first_approval} → {'✅' if passed else '❌'}\n")
            results.append((label, passed))

        case("A 常规发起", base.owner_id, '业务线经理审批')
        case("C 业务线经理本人发起", biz.id, '总经理审批')
    finally:
        sb.teardown()

print("=" * 50)
for label, passed in results:
    print(f"  {'✅' if passed else '❌'} {label}")
assert results and all(p for _, p in results), "存在失败用例"
print("  全部通过")
