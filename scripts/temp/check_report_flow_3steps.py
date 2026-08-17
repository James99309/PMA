#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证报备审批三级化(商务初审→业务线经理→总经理)的模板升级与审批人解析。

跑法: export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
      python3 scripts/temp/check_report_flow_3steps.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app, Sandbox                  # noqa: E402

app = make_app()


def show(label, val):
    print(f"  {label:<28} {val}")


with app.app_context():
    from app import db
    from app.models.approval import (ApprovalProcessTemplate, ApprovalStep,
                                     ApprovalInstance, ApprovalStatus)
    from app.models.project import Project
    from app.helpers.project_hold_helpers import (
        REPORT_TEMPLATE_NAME, get_or_create_report_template,
        resolve_report_approvers, submit_project_report_approval)

    sb = Sandbox()
    try:
        tpl = ApprovalProcessTemplate.query.filter_by(
            object_type='project', name=REPORT_TEMPLATE_NAME).first()
        print(f"\n=== 1. 升级前模板 (id={tpl.id if tpl else None}) ===")
        for s in ApprovalStep.query.filter_by(process_id=tpl.id).order_by(ApprovalStep.step_order):
            show(f"step_order={s.step_order}", f"id={s.id} {s.step_name} ({s.approver_type})")

        pend_before = {i.id: i.current_step for i in ApprovalInstance.query.filter_by(
            object_type='project', process_id=tpl.id, status=ApprovalStatus.PENDING).all()}
        show("在办实例 current_step", pend_before or "(本地无在办单)")

        print("\n=== 2. 执行幂等升级 ===")
        tpl, s1, s2, s3 = get_or_create_report_template()
        for s in ApprovalStep.query.filter_by(process_id=tpl.id).order_by(ApprovalStep.step_order):
            show(f"step_order={s.step_order}", f"id={s.id} {s.step_name} ({s.approver_type})")
        print("  再跑一次(幂等性检查)...")
        tpl, s1, s2, s3 = get_or_create_report_template()
        n = ApprovalStep.query.filter_by(process_id=tpl.id).count()
        show("步骤总数(应为3)", n)
        assert n == 3, f"幂等失败: 步骤数={n}"

        pend_after = {i.id: i.current_step for i in ApprovalInstance.query.filter_by(
            object_type='project', process_id=tpl.id, status=ApprovalStatus.PENDING).all()}
        show("在办实例 current_step 未变", pend_after == pend_before)
        assert pend_after == pend_before, f"在办实例被改动: {pend_before} -> {pend_after}"

        print("\n=== 3. 三条业务线的审批人解析 ===")
        for ptype, label in (('channel_follow', '渠道跟进'), ('sales_focus', '销售重点'),
                             ('business_opportunity', '业务机会/服务')):
            p = Project.query.filter(Project.project_type == ptype,
                                     Project.is_deleted == False).first()          # noqa: E712
            if not p:
                show(label, "本地无该类型项目,跳过")
                continue
            pre, biz, ceo, err = resolve_report_approvers(p)
            show(label,
                 f"项目#{p.id} 负责人={(p.owner.real_name if p.owner else None)} → "
                 f"初审={(pre.real_name if pre else None)} / "
                 f"业务线={(biz.real_name if biz else None)}({biz.role if biz else '-'}) / "
                 f"总经理={(ceo.real_name if ceo else None)} err={err}")

        print("\n=== 4. 模拟发起(渠道项目) ===")
        target = None
        for p in Project.query.filter(Project.project_type == 'channel_follow',
                                      Project.is_deleted == False).all():          # noqa: E712
            if not ApprovalInstance.query.filter_by(object_type='project', object_id=p.id).first():
                target = sb.watch(p)
                break
        if not target:
            print("  本地没有【无历史审批实例】的渠道项目,跳过")
        else:
            from app.models.user import User
            from app.models.approval import ApprovalRecord
            inst, err = submit_project_report_approval(target, target.owner_id)
            if err or not inst:
                print(f"  发起失败: {err}")
            else:
                db.session.flush()
                show("实例", f"id={inst.id} current_step={inst.current_step}")
                for st in inst.get_steps():
                    uid = (inst.designated_approvers or {}).get(str(st['step_id']))
                    u = db.session.get(User, uid) if uid else None
                    show(f"  step{st['step_order']} {st['step_name']}",
                         f"指定={(u.real_name if u else '(未指定/跳过)')}")
                for r in ApprovalRecord.query.filter_by(instance_id=inst.id):
                    show("  记录", f"step_id={r.step_id} {r.action} {r.comment}")
        print()
    finally:
        sb.teardown()
    print("  (模板升级为独立 commit,保留)\n")
