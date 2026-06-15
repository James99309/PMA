# -*- coding: utf-8 -*-
"""月度薪资审批 helpers(2026-06-13 用户确认)。

流程:HR(或管理员)生成当月全员薪资表 → 提交审批 →
财务主管(finance_supervisor)→ 财务总监(finace_director)→ 总经理(ceo)。
- 提交即锁定该公司该月个人薪资(is_locked=True,status=pending),个人薪资页该月不可编辑;
- 召回 → 解锁(status=draft);驳回 → 解锁(status=rejected,可改后重提);
- 终审通过 → 永久锁定(status=approved),不可再编辑。
- snapshot 固化提交时各人各项当月应发,后续改标准额/结构/考核方法不影响已锁定月份。
"""
from sqlalchemy.orm.attributes import flag_modified

SALARY_RUN_OBJECT_TYPE = 'salary_run'

# 发放方式 → 当月是否有效(月发全月 / 季发 3·6·9·12 / 年发仅 12)
_EFF_MONTHS = {
    'monthly': set(range(1, 13)),
    'quarterly': {3, 6, 9, 12},
    'yearly': {12},
}


def _eff_months(cycle):
    return _EFF_MONTHS.get(cycle or 'monthly', _EFF_MONTHS['monthly'])


def get_run(company_name, year, month):
    from app.models.salary_structure import SalaryRun
    return SalaryRun.query.filter_by(
        company_name=company_name, year=year, month=month).first()


def is_month_locked(user_id, year, month):
    """该用户所属公司该年月是否已被薪资审批锁定(pending/approved)。"""
    from app.models.salary_structure import SalaryRun
    from app.models.user import User
    u = User.query.get(user_id)
    if not u or not u.company_name:
        return False
    run = SalaryRun.query.filter_by(
        company_name=u.company_name, year=year, month=month).first()
    return bool(run and run.is_locked and run.status in ('pending', 'approved'))


def locked_months(company_name, year):
    """该公司该年已锁定(pending/approved)的月份集合 → 供薪资页整年标只读。"""
    from app.models.salary_structure import SalaryRun
    rows = SalaryRun.query.filter_by(company_name=company_name, year=year).all()
    return sorted(r.month for r in rows if r.is_locked and r.status in ('pending', 'approved'))


def person_month_breakdown(user_id, year, month):
    """单人某月各薪资项应发(元):override(monthly_amounts[m])优先,否则有效月按标准额,否则 0。
    主项有子项 → 该项 = 子项之和;返回 {leaf_code: amount} + total。"""
    from app.models.salary_structure import SalaryStructureItem, UserSalaryItem

    struct = SalaryStructureItem.query.filter_by(is_active=True).all()
    child_codes = {r.parent_code for r in struct if r.parent_code}
    urows = UserSalaryItem.query.filter_by(user_id=user_id, year=year).all()
    amap = {x.item_code: x for x in urows if not x.is_personal}
    personal = [x for x in urows if x.is_personal]

    def _row_month(row, cyc):
        if not row:
            return 0.0
        m = (row.monthly_amounts or {})
        ov = m.get(str(month), m.get(month))
        if ov not in (None, ''):
            return float(ov)
        # 无 override → 有效月按标准额
        if month in _eff_months(cyc):
            return float(row.amount) if row.amount is not None else 0.0
        return 0.0

    items = {}
    # 叶子结构项(无子项的)
    for r in struct:
        if r.item_code in child_codes:
            continue   # 主项(汇总)不单列,由子项累计
        a = amap.get(r.item_code)
        cyc = (a.pay_cycle if (a and a.pay_cycle) else None) or (r.pay_cycle or 'monthly')
        if r.parent_code:   # 子项
            items[r.item_code] = _row_month(a, cyc)
        else:               # 无子项的主项 = 叶子
            items[r.item_code] = _row_month(a, cyc)
    # 个人专属项
    for x in personal:
        cyc = x.pay_cycle or 'monthly'
        code = x.item_code or f'personal_{x.id}'
        items[code] = _row_month(x, cyc)

    total = round(sum(items.values()), 2)
    return items, total


# 不计薪的外部/伙伴/系统角色(不进薪资表):代理商 + 系统管理员
SALARY_EXCLUDE_ROLES = ('dealer', 'admin')


def build_month_snapshot(company_name, year, month):
    """该公司该月全员薪资快照:[{user_id,name,department,role,items,total}] + 合计。
    纳入该公司全部在职员工(未配置标准额者显示 0,便于 HR 核对名单),排除外部伙伴角色。"""
    from app.models.user import User
    users = User.query.filter(
        User.company_name == company_name, User._is_active.is_(True),
        User.role.notin_(SALARY_EXCLUDE_ROLES)
    ).order_by(User.department, User.id).all()
    rows, total = [], 0.0
    for u in users:
        items, t = person_month_breakdown(u.id, year, month)
        rows.append({
            'user_id': u.id,
            'name': u.real_name or u.username,
            'department': u.department or '',
            'role': u.role or '',
            'items': items,
            'total': t,
        })
        total += t
    return rows, round(total, 2)


def resolve_salary_approvers(company_name, initiator_id):
    """按 SALARY_RUN_APPROVER_ROLES 顺序解析审批人(优先同公司,回退全局)。
    Returns (approvers[list[User]], err)。任一角色缺人 → err。"""
    from app.models.user import User
    from app.models.salary_structure import SALARY_RUN_APPROVER_ROLES

    approvers = []
    for role in SALARY_RUN_APPROVER_ROLES:
        q = User.query.filter(User.role == role, User._is_active.is_(True))
        u = q.filter(User.company_name == company_name).first() or q.first()
        if not u:
            try:
                from app.utils.role_mappings import get_role_display_name
                disp = get_role_display_name(role)
            except Exception:
                disp = role
            return None, f'未找到审批角色「{disp}」的在职用户,请先配置后再发起'
        approvers.append(u)
    return approvers, None


def get_or_create_salary_template(created_by=None):
    """幂等确保 salary_run 模板 + 三个 submitter_designate 步骤(财务主管/财务总监/总经理)。"""
    from app import db
    from app.models.approval import ApprovalProcessTemplate, ApprovalStep
    from app.models.user import User

    tpl = ApprovalProcessTemplate.query.filter_by(object_type=SALARY_RUN_OBJECT_TYPE).first()
    if not tpl:
        creator_id = created_by
        if not creator_id or not User.query.get(creator_id):
            admin = User.query.filter_by(role='admin').first() or User.query.first()
            creator_id = admin.id if admin else None
        tpl = ApprovalProcessTemplate(
            name='月度薪资审批', object_type=SALARY_RUN_OBJECT_TYPE,
            created_by=creator_id, is_active=True)
        db.session.add(tpl)
        db.session.flush()

    steps = (ApprovalStep.query.filter_by(process_id=tpl.id)
             .order_by(ApprovalStep.step_order).all())
    if len(steps) < 3:
        for s in steps:
            db.session.delete(s)
        db.session.flush()
        names = ['财务主管复核', '财务总监审批', '总经理审批']
        steps = []
        for i, nm in enumerate(names, start=1):
            st = ApprovalStep(process_id=tpl.id, step_order=i, step_name=nm,
                              approver_type='submitter_designate', send_email=True)
            db.session.add(st)
            steps.append(st)
        db.session.flush()
        db.session.commit()
    return tpl, steps


def submit_salary_run(company_name, year, month, initiator_id):
    """生成并提交当月薪资审批。提交即锁定该公司该月个人薪资。
    Returns (run, instance, err)。"""
    from app import db
    from app.models.salary_structure import SalaryRun
    from app.helpers.approval_helpers import start_approval_process
    from app.models.approval import ApprovalRecord

    if month not in range(1, 13):
        return None, None, '无效月份'

    existing = get_run(company_name, year, month)
    if existing and existing.status in ('pending', 'approved'):
        return None, None, f'{company_name} {year}年{month}月 薪资已在审批中或已通过,请勿重复发起'

    approvers, err = resolve_salary_approvers(company_name, initiator_id)
    if err:
        return None, None, err

    rows, total = build_month_snapshot(company_name, year, month)
    if not rows:
        return None, None, f'{year}年{month}月 该公司无可发放薪资的人员'

    run = existing or SalaryRun(company_name=company_name, year=year, month=month)
    run.snapshot = rows
    run.total_amount = total
    run.headcount = len(rows)
    run.status = 'pending'
    run.is_locked = True
    run.initiated_by = initiator_id
    run.settled_at = None
    if not existing:
        db.session.add(run)
    db.session.commit()   # 业务对象须先持久化(同绩效结算)

    tpl, steps = get_or_create_salary_template(created_by=initiator_id)
    designated = {str(steps[i].id): approvers[i].id for i in range(len(steps))}

    instance = start_approval_process(
        SALARY_RUN_OBJECT_TYPE, run.id, tpl.id, initiator_id,
        auto_commit=False, designated_approvers=designated)
    if not instance:
        return None, None, '发起审批失败(可能已存在审批流程)'

    snap = instance.template_snapshot or {}
    snap.update({'salary_run_id': run.id, 'sr_company': company_name,
                 'sr_year': year, 'sr_month': month})
    instance.template_snapshot = snap
    flag_modified(instance, 'template_snapshot')

    run.approval_instance_id = instance.id
    db.session.commit()
    return run, instance, None


def build_salary_run_flow(run_id, current_user_id):
    """供 at-approval-dropdown 徽章展开(对齐 build_settlement_flow 形态)。"""
    from app.models.salary_structure import SalaryRun
    from app.models.approval import ApprovalInstance, ApprovalStatus, ApprovalStep, ApprovalRecord
    from app.models.user import User

    run = SalaryRun.query.get(run_id)
    if not run:
        return {'success': False, 'message': '薪资批次不存在'}
    if not run.approval_instance_id:
        return {'success': True, 'has_approval': False, 'message': '暂无审批流程'}
    inst = ApprovalInstance.query.get(run.approval_instance_id)
    if not inst:
        return {'success': True, 'has_approval': False, 'message': '暂无审批流程'}

    steps = ApprovalStep.query.filter_by(process_id=inst.process_id).order_by(ApprovalStep.step_order).all()
    records = ApprovalRecord.query.filter_by(instance_id=inst.id).order_by(ApprovalRecord.id).all()
    rec_by_step = {r.step_id: r for r in records}
    designated = inst.designated_approvers or {}
    cur = inst.current_step
    is_pending = inst.status == ApprovalStatus.PENDING

    stages = []
    for step in steps:
        ap_id = designated.get(str(step.id)) or step.approver_user_id
        ap = User.query.get(ap_id) if ap_id else None
        rec = rec_by_step.get(step.id)
        sd = {
            'id': step.id, 'stage_name': step.step_name, 'stage_order': step.step_order,
            'approver_name': (ap.real_name or ap.username) if ap else '待确定',
            'approver_id': ap_id, 'status': 'pending', 'comment': None,
            'processed_at': None, 'can_approve': False,
        }
        if rec:
            if rec.action == 'skipped':
                continue
            sd['status'] = 'approved' if rec.action == 'approve' else ('rejected' if rec.action == 'reject' else rec.action)
            sd['comment'] = rec.comment
            sd['processed_at'] = rec.timestamp.isoformat() if getattr(rec, 'timestamp', None) else None
        elif is_pending and step.step_order == cur:
            sd['status'] = 'current'
            sd['can_approve'] = bool(ap_id and int(ap_id) == int(current_user_id))
        elif is_pending and step.step_order < cur:
            sd['status'] = 'approved'
        elif inst.status == ApprovalStatus.APPROVED:
            sd['status'] = 'approved'
        stages.append(sd)

    status_str = inst.status.value if hasattr(inst.status, 'value') else str(inst.status).lower()
    can_approve = any(s.get('can_approve') for s in stages)
    # 发起人(HR)在审批中可召回 → 解锁该月个人薪资
    can_recall = bool(is_pending and run.initiated_by and int(run.initiated_by) == int(current_user_id))
    return {
        'success': True, 'has_approval': True,
        'approval_flow': {
            'instance_id': inst.id, 'stages': stages, 'status': status_str,
            'can_approve': can_approve, 'can_recall': can_recall, 'can_resubmit': False,
        },
        'control_info': {'can_approve': can_approve, 'can_recall': can_recall,
                         'can_resubmit': False, 'can_submit': False},
    }
