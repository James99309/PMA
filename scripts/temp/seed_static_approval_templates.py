#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""幂等创建「报价单技术确认」+「采购订单」审批模板(随数据库环境配公司池)。

这两个是纯静态模板(无 get_or_create helper),需手动种到各环境。
其余流程(薪资/绩效/渠道/项目报备/失败搁置)由各自 helper 首次使用时自动生成。

环境区分(PMA_DB_TYPE):
  - ovs(SG): 报价单 pool=solution_manager@evertacsolutions;采购 审批人=财务总监@evertacsolutions
  - sp8d(CN)及默认: 报价单 pool=solution_manager@和源通信(上海);采购 审批人=供应链主管@和源通信(上海)

幂等:对应 object_type 已有模板则跳过,可安全重复运行。
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
from app.models.approval import ApprovalProcessTemplate, ApprovalStep
from app.models.user import User

LOCK_REASON = '审批流程进行中，暂时锁定编辑'


def ensure(object_type, name, step_name, pool, creator_id, lock_on_start=True):
    tpl = ApprovalProcessTemplate.query.filter_by(object_type=object_type).first()
    if tpl:
        # 幂等纠正:lock_object_on_start 若与期望不符则更正(技术确认不锁定)
        if tpl.lock_object_on_start != lock_on_start:
            tpl.lock_object_on_start = lock_on_start
            db.session.commit()
            print(f'[update] {object_type} 模板 id={tpl.id} lock_object_on_start→{lock_on_start}')
        else:
            print(f'[skip] {object_type} 模板已存在 id={tpl.id} name={tpl.name}')
        return tpl
    tpl = ApprovalProcessTemplate(
        name=name, object_type=object_type, is_active=True,
        created_by=creator_id, lock_object_on_start=lock_on_start,
        lock_reason=LOCK_REASON, required_fields=[])
    db.session.add(tpl)
    db.session.flush()
    st = ApprovalStep(
        process_id=tpl.id, step_order=1, step_name=step_name,
        approver_type='submitter_designate', send_email=True,
        designate_pool=pool)
    db.session.add(st)
    db.session.commit()
    print(f'[created] {object_type} 模板 id={tpl.id} step="{step_name}" pool={pool}')
    return tpl


def main():
    app = create_app()
    with app.app_context():
        db_type = os.environ.get('PMA_DB_TYPE', os.environ.get('SUPABASE_DB_TYPE', 'sp8d'))
        is_ovs = db_type == 'ovs'
        company = 'evertacsolutions' if is_ovs else '和源通信（上海）股份有限公司'
        print(f'== 环境 db_type={db_type} company={company} ==')

        admin = User.query.filter_by(role='admin').first() or User.query.first()
        creator_id = admin.id if admin else None

        # 1) 报价单技术确认 —— 只是确认"状态",不锁定报价单(锁了就无法编辑触发 reconfirm)
        ensure('quotation', '报价单技术确认', '技术确认',
               {'roles': ['solution_manager'], 'companies': [company]}, creator_id,
               lock_on_start=False)

        # 2) 采购订单
        if is_ovs:
            po_step = '财务总监审核'
            po_pool = {'roles': ['finance_director', 'finace_director'], 'companies': [company]}
        else:
            po_step = '供应链主管审核'
            po_pool = {'roles': ['supplychain_manager'], 'companies': [company]}
        ensure('purchase_order', '采购订单', po_step, po_pool, creator_id)

        # 验证候选(只列在职用户)
        from app.helpers.approval_helpers import get_designate_steps_info
        print('-- 候选校验 --')
        for ot in ('quotation', 'purchase_order'):
            t = ApprovalProcessTemplate.query.filter_by(object_type=ot).first()
            if not t:
                continue
            for s in get_designate_steps_info(t.id):
                cands = [f"{c['name']}({c['role']})" for c in s['candidates']]
                print(f'  {ot} 步骤「{s["step_name"]}」候选: {cands or "⚠️ 空!"}')


if __name__ == '__main__':
    main()
