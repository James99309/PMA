#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端跑完渠道报备三级链:商务初审 → 业务线经理 → 总经理,验证整条通过后的副作用:
  · 项目 status=approved
  · 授权编号自动生成(渠道跟进→CPJ)——先把原编号清空并 commit,否则
    _handle_project_authorization 对已有编号幂等直接返回,这条断言就是空的
  · 厂商销售负责人回填为**在职渠道负责人**(与谁审批解耦,本次改动点)

跑法: export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
      python3 scripts/temp/check_report_flow_fullchain.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app, Sandbox                  # noqa: E402

app = make_app()

with app.app_context():
    from app import db
    from app.models.approval import ApprovalInstance, ApprovalStatus
    from app.models.project import Project
    from app.models.user import User
    from app.helpers.project_hold_helpers import submit_project_report_approval
    from app.helpers.approval_helpers import process_approval
    from app.helpers.biz_line_routing import CHANNEL_APPROVER_ROLES

    sb = Sandbox()
    checks = {}
    try:
        def _name(u):
            return (u.real_name or u.username) if u else None

        target = None
        for p in Project.query.filter(Project.project_type == 'channel_follow',
                                      Project.is_deleted == False).all():          # noqa: E712
            if not ApprovalInstance.query.filter_by(object_type='project',
                                                    object_id=p.id).first():
                target = sb.watch(p)
                break
        assert target, "本地没有可用的渠道项目(需无历史审批实例)"

        # 清空并**提交**:start_approval_process 内部有强制 rollback,只 flush 会被冲掉。
        # 原值已由 sb.watch 记下,teardown 会还原。
        target.authorization_code = None
        target.vendor_sales_manager_id = None
        db.session.commit()

        # 期望回填人:在职渠道总监(缺位退渠道经理)
        expect_vsm = None
        for r in CHANNEL_APPROVER_ROLES:
            q = User.query.filter(User.role == r, User._is_active.is_(True))
            expect_vsm = ((q.filter(User.company_name == target.owner.company_name).first()
                           if target.owner else None) or q.first())
            if expect_vsm:
                break

        inst, err = submit_project_report_approval(target, target.owner_id)
        assert inst, f"发起失败: {err}"
        db.session.flush()
        print(f"项目#{target.id} 实例{inst.id} 发起人={_name(target.owner)}")

        n = 0
        while inst.status == ApprovalStatus.PENDING and n < 6:
            n += 1
            cur = inst.get_current_step_info() or {}
            uid = (inst.designated_approvers or {}).get(str(cur.get('step_id')))
            print(f"  [{n}] 当前步={cur.get('step_name')} 审批人={_name(db.session.get(User, uid))}")
            process_approval(inst.id, 'approve', comment='测试通过', user_id=uid)
            db.session.flush()
            db.session.refresh(inst)

        db.session.refresh(target)
        print(f"\n  流程状态         {inst.status.name}")
        print(f"  项目 status      {target.status}")
        print(f"  授权编号         {target.authorization_code} (发起前已清空)")
        print(f"  厂商销售负责人    {_name(target.vendor_sales_manager)} "
              f"(期望={_name(expect_vsm)})")

        checks = {
            '流程通过': inst.status == ApprovalStatus.APPROVED,
            '项目 approved': target.status == 'approved',
            '授权编号新生成且为 CPJ': bool(target.authorization_code
                                           and 'CPJ' in target.authorization_code),
            '厂商销售负责人=在职渠道负责人': (expect_vsm is not None
                                            and target.vendor_sales_manager_id == expect_vsm.id),
        }
        print()
        for k, v in checks.items():
            print(f"  {'✅' if v else '❌'} {k}")
    finally:
        sb.teardown()
    assert checks and all(checks.values()), "存在失败断言"
    print("\n  全部通过\n")
