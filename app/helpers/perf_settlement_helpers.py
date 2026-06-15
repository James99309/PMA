# -*- coding: utf-8 -*-
"""季度绩效结算审批 helpers(P2)。

流程:HR 发起 → 当事人直属上级 → 总经理(ceo)。通过后(P3,dispatch 回调)
按「绩效基数 × 得分%」折算绩效薪资写入个人薪资该季末月并锁定。
设计:docs/plans/2026-06-13-quarterly-perf-settlement-design.md
"""
from sqlalchemy.orm.attributes import flag_modified

SETTLEMENT_OBJECT_TYPE = 'perf_settlement'
_Q_END_MONTH = {1: 3, 2: 6, 3: 9, 4: 12}
_CYC_PERIODS = {'monthly': 3, 'quarterly': 1, 'yearly': 1}   # 每季度内的发放期数(年发仅 Q4 计 1)


def resolve_settlement_approvers(user, initiator_id):
    """解析 (直属上级, 总经理ceo, err)。上级缺位→跳级直达总经理;ceo 必需。"""
    from app.models.user import User, Affiliation

    company_name = user.company_name or ''

    def _active_ceo():
        q = User.query.filter(User.role == 'ceo', User._is_active.is_(True))
        return q.filter(User.company_name == company_name).first() or q.first()

    ceo = _active_ceo()
    if not ceo:
        return None, None, '未找到总经理(ceo),请联系管理员配置后再发起'

    # 直属上级:归属关系(owner=当事人 → viewer=上级),优先部门负责人
    viewer_ids = [a.viewer_id for a in Affiliation.query.filter_by(owner_id=user.id).all()]
    sup = None
    if viewer_ids:
        sups = User.query.filter(User.id.in_(viewer_ids), User._is_active.is_(True)).all()
        sup = next((s for s in sups if s.is_department_manager), None) or (sups[0] if sups else None)
    # 回退:同部门同公司的部门负责人
    if not sup and user.department:
        sup = User.query.filter(
            User.department == user.department, User.company_name == company_name,
            User.is_department_manager.is_(True), User._is_active.is_(True)).first()
    # 与发起人/终审重复则视为缺位(跳级)
    if sup and (sup.id == initiator_id or sup.id == ceo.id):
        sup = None
    return sup, ceo, None


def get_or_create_settlement_template(created_by=None):
    """幂等确保 perf_settlement 模板 + 两个 submitter_designate 步骤(上级 / 总经理)。"""
    from app import db
    from app.models.approval import ApprovalProcessTemplate, ApprovalStep
    from app.models.user import User

    tpl = ApprovalProcessTemplate.query.filter_by(object_type=SETTLEMENT_OBJECT_TYPE).first()
    if not tpl:
        creator_id = created_by
        if not creator_id or not User.query.get(creator_id):
            admin = User.query.filter_by(role='admin').first() or User.query.first()
            creator_id = admin.id if admin else None
        tpl = ApprovalProcessTemplate(
            name='季度绩效结算审批', object_type=SETTLEMENT_OBJECT_TYPE,
            created_by=creator_id, is_active=True)
        db.session.add(tpl)
        db.session.flush()

    steps = (ApprovalStep.query.filter_by(process_id=tpl.id)
             .order_by(ApprovalStep.step_order).all())
    if len(steps) < 2:
        for s in steps:
            db.session.delete(s)
        db.session.flush()
        step1 = ApprovalStep(process_id=tpl.id, step_order=1, step_name='直属上级确认',
                             approver_type='submitter_designate', send_email=True)
        step2 = ApprovalStep(process_id=tpl.id, step_order=2, step_name='总经理审批',
                             approver_type='submitter_designate', send_email=True)
        db.session.add_all([step1, step2])
        db.session.flush()
        steps = [step1, step2]
        db.session.commit()
    return tpl, steps[0], steps[1]


def perf_base_amount(user_id, year, quarter):
    """季度绩效基数(元)= 绩效薪资标准金额 × 该季度发放期数(月发×3/季发×1/年发仅Q4×1)。"""
    from app.models.salary_structure import UserSalaryItem
    row = UserSalaryItem.query.filter_by(
        user_id=user_id, year=year, item_code='performance_salary', is_personal=False).first()
    if not row or row.amount is None:
        return 0.0
    cyc = row.pay_cycle or 'monthly'
    periods = _CYC_PERIODS.get(cyc, 3)
    if cyc == 'yearly' and quarter != 4:
        periods = 0
    return round(float(row.amount) * periods, 2)


def get_settlement(user_id, year, quarter):
    from app.models.performance_settlement import PerformanceSettlement
    return PerformanceSettlement.query.filter_by(
        user_id=user_id, year=year, quarter=quarter).first()


def submit_settlement(user_id, year, quarter, score, snapshot, initiator_id):
    """HR 发起季度绩效结算审批。score/snapshot 由前端(当季显示得分)传入并快照。
    Returns (settlement, instance, err)。"""
    from app import db
    from app.models.user import User
    from app.models.performance_settlement import PerformanceSettlement
    from app.helpers.approval_helpers import start_approval_process
    from app.models.approval import ApprovalRecord

    if quarter not in (1, 2, 3, 4):
        return None, None, '无效季度'
    user = User.query.get(user_id)
    if not user:
        return None, None, '用户不存在'

    existing = get_settlement(user_id, year, quarter)
    if existing and existing.status in ('pending', 'approved'):
        return None, None, f'{year}Q{quarter} 已有进行中或已结算的绩效结算,请勿重复发起'

    sup, ceo, err = resolve_settlement_approvers(user, initiator_id)
    if err:
        return None, None, err
    if ceo.id == initiator_id:
        return None, None, '您是终审人(总经理),请由他人发起'

    base = perf_base_amount(user_id, year, quarter)
    sc = float(score or 0)
    settled = round(base * sc / 100.0, 2)

    # upsert 结算单(覆盖之前被驳回的)。先提交持久化:
    # start_approval_process 假设业务对象已存在于库中(同 dealer_apply/project_hold),
    # 新建未提交的结算单会被流程内部 flush 弄成游离态丢失,故此处先 commit。
    st = existing or PerformanceSettlement(user_id=user_id, year=year, quarter=quarter)
    st.score = sc
    st.base_amount = base
    st.settled_amount = settled
    st.score_snapshot = snapshot or []
    st.status = 'pending'
    st.is_locked = False
    st.initiated_by = initiator_id
    st.settled_at = None
    if not existing:
        db.session.add(st)
    db.session.commit()

    tpl, step1, step2 = get_or_create_settlement_template(created_by=initiator_id)
    designated = {str(step2.id): ceo.id}
    if sup:
        designated[str(step1.id)] = sup.id

    instance = start_approval_process(
        SETTLEMENT_OBJECT_TYPE, st.id, tpl.id, initiator_id,
        auto_commit=False, designated_approvers=designated)
    if not instance:
        return None, None, '发起审批失败(可能已存在审批流程)'

    snap = instance.template_snapshot or {}
    snap['settlement_id'] = st.id
    snap['perf_year'] = year
    snap['perf_quarter'] = quarter
    instance.template_snapshot = snap
    flag_modified(instance, 'template_snapshot')

    # 上级缺位 → 跳级直达总经理
    if not sup:
        db.session.add(ApprovalRecord(
            instance_id=instance.id, step_id=step1.id, approver_id=initiator_id,
            action='skipped', comment='直属上级缺位或与发起人/总经理重复,自动跳过'))
        instance.current_step = 2
        try:
            from app.services.approval_message_service import ApprovalMessageService
            ApprovalMessageService.send_approval_notification(instance, step2)
        except Exception:
            pass

    st.approval_instance_id = instance.id
    db.session.commit()
    return st, instance, None


def build_settlement_flow(settlement_id, current_user_id):
    """绩效结算审批流数据(对齐 at_approval_dropdown / 项目 flow 形态)。"""
    from app.models.performance_settlement import PerformanceSettlement
    from app.models.approval import ApprovalInstance, ApprovalStatus, ApprovalStep, ApprovalRecord
    from app.models.user import User

    st = PerformanceSettlement.query.get(settlement_id)
    if not st:
        return {'success': False, 'message': '结算单不存在'}
    if not st.approval_instance_id:
        return {'success': True, 'has_approval': False, 'message': '暂无审批流程'}
    inst = ApprovalInstance.query.get(st.approval_instance_id)
    if not inst:
        return {'success': True, 'has_approval': False, 'message': '暂无审批流程'}

    steps = ApprovalStep.query.filter_by(process_id=inst.process_id).order_by(ApprovalStep.step_order).all()
    records = ApprovalRecord.query.filter_by(instance_id=inst.id).order_by(ApprovalRecord.id).all()
    rec_by_step = {}
    for r in records:
        rec_by_step[r.step_id] = r
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
    return {
        'success': True, 'has_approval': True,
        'approval_flow': {
            'instance_id': inst.id, 'stages': stages, 'status': status_str,
            'can_approve': can_approve, 'can_recall': False, 'can_resubmit': False,
        },
        'control_info': {'can_approve': can_approve, 'can_recall': False,
                         'can_resubmit': False, 'can_submit': False},
    }


def is_settlement_approver_of(approver_id, target_user_id, year=None):
    """approver_id 是否为 target_user_id 某进行中绩效结算的当前审批人(用于只读放行)。"""
    from app.models.performance_settlement import PerformanceSettlement
    from app.helpers.approval_helpers import is_current_approver
    q = PerformanceSettlement.query.filter_by(user_id=target_user_id, status='pending')
    if year:
        q = q.filter_by(year=year)
    for st in q.all():
        if st.approval_instance_id and is_current_approver('perf_settlement', st.id, approver_id):
            return True
    return False


def is_supervisor_of(viewer_id, target_user_id):
    """viewer 是否为 target 的上级(可看下属绩效):归属上级 / 同部门负责人 / 总经理。"""
    if viewer_id == target_user_id:
        return False
    from app.models.user import User, Affiliation
    target = User.query.get(target_user_id)
    viewer = User.query.get(viewer_id)
    if not target or not viewer:
        return False
    # 1) 归属关系:owner=下属 → viewer=上级
    if Affiliation.query.filter_by(owner_id=target_user_id, viewer_id=viewer_id).first():
        return True
    # 2) 同部门同公司的部门负责人
    if (viewer.is_department_manager and target.department and viewer.department == target.department
            and (viewer.company_name or '') == (target.company_name or '')):
        return True
    # 3) 总经理(ceo)可看本公司下属
    if viewer.role == 'ceo' and (viewer.company_name or '') == (target.company_name or ''):
        return True
    return False
