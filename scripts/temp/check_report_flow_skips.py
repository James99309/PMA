#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证报备三级流程的跳级分支:发起人=商务初审人 / 发起人=业务线经理 / SG(ovs) 扁平。

跑法: export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
      python3 scripts/temp/check_report_flow_skips.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app, Sandbox                  # noqa: E402

app = make_app()

with app.app_context():
    from app import db
    from app.models.approval import ApprovalInstance, ApprovalRecord
    from app.models.project import Project
    from app.models.user import User
    from app.helpers.project_hold_helpers import (
        submit_project_report_approval, resolve_report_approvers)

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

        def run_case(label, submitter_id):
            p = fresh_channel_project()
            if not p:
                print(f"\n【{label}】无可用项目,跳过")
                return
            inst, err = submit_project_report_approval(p, submitter_id)
            print(f"\n【{label}】发起人={_name(db.session.get(User, submitter_id))} 项目#{p.id}")
            if err or not inst:
                print(f"  失败: {err}")
                return
            db.session.flush()
            print(f"  current_step={inst.current_step} (流程实际从这一步开始)")
            for st in inst.get_steps():
                uid = (inst.designated_approvers or {}).get(str(st['step_id']))
                who = _name(db.session.get(User, uid)) if uid else '—'
                print(f"    step{st['step_order']} {st['step_name']:<10} 指定={who}")
            for r in ApprovalRecord.query.filter_by(instance_id=inst.id).all():
                print(f"    skipped: step_id={r.step_id} {r.comment}")

        base = fresh_channel_project()
        pre, biz, ceo, _ = resolve_report_approvers(base)
        print(f"基准: 初审={_name(pre)} 业务线={_name(biz)} 总经理={_name(ceo)}")

        run_case("A 常规发起", base.owner_id)
        run_case("B 商务初审人本人发起", pre.id)
        run_case("C 业务线经理本人发起", biz.id)
        run_case("D 总经理本人发起", ceo.id)

        # E. SG(ovs):组织扁平 → 前两级都无人,直达总经理
        os.environ['PMA_DB_TYPE'] = 'ovs'
        p = fresh_channel_project()
        pre2, biz2, ceo2, err2 = resolve_report_approvers(p)
        print(f"\n【E SG(ovs) 解析】初审={_name(pre2)} 业务线={_name(biz2)} "
              f"总经理={_name(ceo2)} err={err2}")
        used.discard(p.id)
        run_case("E SG(ovs) 发起", p.owner_id)
        os.environ['PMA_DB_TYPE'] = 'sp8d'
        print()
    finally:
        sb.teardown()
