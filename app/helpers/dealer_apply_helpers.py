# -*- coding: utf-8 -*-
"""客户渠道身份(代理商/分销商)审批 helpers。

业务规则(2026-06-13 与用户确认):
  - 新建/编辑客户选择 company_type = dealer / distributor 时,不直接生效:
    目标类型暂存 companies.pending_company_type,并发起本审批。
  - 审批链:商务助理 → 渠道经理 → 总经理(ceo 终审必需);
    前两级岗位无人在职/与发起人重复时自动跳级(沿 project_hold 同款机制)。
  - 通过:company_type = 目标类型,清 pending;驳回/召回:仅清 pending(身份不变)。
  - 与 project_hold 一致采用 get-or-create 模板 + designated_approvers,免迁移协调。
"""
from sqlalchemy.orm.attributes import flag_modified

DEALER_OBJECT_TYPE = 'dealer_apply'
DEALER_TARGET_TYPES = ('dealer', 'distributor')


def resolve_dealer_approvers(company, initiator_id):
    """解析三级审批人:(business_admin, channel_manager, ceo), err。
    前两级可为 None(缺位/重复 → 跳级);ceo 必需。"""
    from app.models.user import User

    owner = User.query.get(company.owner_id) if company.owner_id else None
    company_name = (owner.company_name if owner else None) or ''

    def _active_role(role):
        q = User.query.filter(User.role == role, User._is_active.is_(True))
        return (q.filter(User.company_name == company_name).first() or q.first())

    ceo = _active_role('ceo')
    if not ceo:
        return None, None, None, '未找到总经理(ceo)，请联系管理员配置后再发起'
    ba = _active_role('business_admin')
    # 渠道线审批人 = 渠道总监优先,缺位退渠道经理(2026-07-14:渠道审批负责人已改为渠道总监)
    from app.helpers.biz_line_routing import CHANNEL_APPROVER_ROLES
    cm = next((u for u in (_active_role(r) for r in CHANNEL_APPROVER_ROLES) if u), None)

    # 与发起人/终审人重复的级跳过
    def _dedupe(u, taken):
        return None if (u and (u.id == initiator_id or u.id in taken)) else u
    taken = {ceo.id}
    ba = _dedupe(ba, taken)
    if ba:
        taken.add(ba.id)
    cm = _dedupe(cm, taken)
    return ba, cm, ceo, None


def get_or_create_dealer_template(created_by=None):
    """幂等确保 dealer_apply 审批模板 + 三个 submitter_designate 步骤存在。"""
    from app import db
    from app.models.approval import ApprovalProcessTemplate, ApprovalStep
    from app.models.user import User

    tpl = ApprovalProcessTemplate.query.filter_by(object_type=DEALER_OBJECT_TYPE).first()
    if not tpl:
        creator_id = created_by
        if not creator_id or not User.query.get(creator_id):
            admin = User.query.filter_by(role='admin').first() or User.query.first()
            creator_id = admin.id if admin else None
        tpl = ApprovalProcessTemplate(
            name='客户渠道身份审批',
            object_type=DEALER_OBJECT_TYPE,
            created_by=creator_id,
            is_active=True,
        )
        db.session.add(tpl)
        db.session.flush()

    steps = (ApprovalStep.query.filter_by(process_id=tpl.id)
             .order_by(ApprovalStep.step_order).all())
    if len(steps) < 3:
        for s in steps:
            db.session.delete(s)
        db.session.flush()
        step1 = ApprovalStep(process_id=tpl.id, step_order=1, step_name='商务助理审批',
                             approver_type='submitter_designate', send_email=True)
        step2 = ApprovalStep(process_id=tpl.id, step_order=2, step_name='渠道经理审批',
                             approver_type='submitter_designate', send_email=True)
        step3 = ApprovalStep(process_id=tpl.id, step_order=3, step_name='总经理审批',
                             approver_type='submitter_designate', send_email=True)
        db.session.add_all([step1, step2, step3])
        db.session.flush()
        steps = [step1, step2, step3]
        db.session.commit()   # 模板独立落库(同 project_hold:防内部 rollback 冲掉)
    return tpl, steps[0], steps[1], steps[2]


def get_pending_dealer_instance(company_id):
    """该客户进行中的渠道身份审批实例(PENDING),无则 None。"""
    from app.helpers.approval_helpers import get_object_approval_instance
    from app.models.approval import ApprovalStatus
    inst = get_object_approval_instance(DEALER_OBJECT_TYPE, company_id, include_rejected=False)
    if inst and inst.status == ApprovalStatus.PENDING:
        return inst
    return None


def submit_dealer_apply(company, target_type, user_id, reason=''):
    """发起客户渠道身份审批。Returns (instance, err)。"""
    from app import db
    from app.helpers.approval_helpers import start_approval_process
    from app.models.approval import ApprovalRecord

    if target_type not in DEALER_TARGET_TYPES:
        return None, '无效的目标身份(仅限 代理商/分销商)'
    if get_pending_dealer_instance(company.id):
        return None, '该客户已有进行中的渠道身份审批,请勿重复发起'

    ba, cm, ceo, err = resolve_dealer_approvers(company, user_id)
    if err:
        return None, err
    if ceo.id == user_id:
        return None, '您是终审人(总经理),请由他人发起后审批'

    tpl, step1, step2, step3 = get_or_create_dealer_template(created_by=user_id)
    designated = {str(step3.id): ceo.id}
    if ba:
        designated[str(step1.id)] = ba.id
    if cm:
        designated[str(step2.id)] = cm.id

    instance = start_approval_process(
        DEALER_OBJECT_TYPE, company.id, tpl.id, user_id,
        auto_commit=False, designated_approvers=designated)
    if not instance:
        return None, '发起审批失败(可能已存在审批流程)'

    snap = instance.template_snapshot or {}
    snap['dealer_target'] = target_type
    # 发起时的原身份要快照:通过后 company_type 就被改成目标身份了,事后回看
    # 若实时去读就会显示成「经销 → 经销商」这种自己变自己的废话
    snap['dealer_from_type'] = company.company_type or ''
    snap['dealer_reason'] = (reason or '').strip()
    snap['dealer_initiator_id'] = user_id
    instance.template_snapshot = snap
    flag_modified(instance, 'template_snapshot')

    # 缺位级跳过(skipped 记录 + current_step 前移)
    skipped_steps = []
    if not ba:
        skipped_steps.append((step1, '商务助理缺位或与发起人/审批人重复,自动跳过'))
    if not cm:
        skipped_steps.append((step2, '渠道经理缺位或与发起人/审批人重复,自动跳过'))
    first_live = step1 if ba else (step2 if cm else step3)
    for st, note in skipped_steps:
        db.session.add(ApprovalRecord(
            instance_id=instance.id, step_id=st.id, approver_id=user_id,
            action='skipped', comment=note))
    if first_live.step_order != 1:
        instance.current_step = first_live.step_order
        try:
            from app.services.approval_message_service import ApprovalMessageService
            ApprovalMessageService.send_approval_notification(instance, first_live)
        except Exception:
            pass

    db.session.commit()
    return instance, None
