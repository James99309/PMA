# -*- coding: utf-8 -*-
"""项目失败/搁置审核 (object_type='project_hold')。

设计要点(见对话设计稿):
  - gated(闸门式):仅当审批链全部通过后,才把 project.current_stage 改为 lost/paused
    (真正写库在 approval_helpers._update_business_object_approval_status 的
     'project_hold' 分支)。提交到通过之间项目阶段值不变,前端显示"审核中"。
  - 审批链(顺序):部门经理(项目 owner 所在部门 is_department_manager=True)
                → 总经理(role='ceo')。
  - 复用通用审批框架(代办/流程时间轴/驳回/召回/通知全免费),用一个独立的
    object_type='project_hold' 与报备审批('project')隔离,可并存。
  - 强制理由:发起人理由存入实例快照 hold_reason;审批人意见的强制由
    approve 端点对 project_hold 校验 comment 非空保证。
  - 恢复正常免审:不走本模块,见 at_view 的 atProjRecover → update_stage。
"""

HOLD_OBJECT_TYPE = 'project_hold'
HOLD_TARGETS = {'lost': '失败', 'paused': '搁置'}


def resolve_hold_approvers(project):
    """解析项目失败/搁置审核的两级审批人。

    Returns: (dept_manager_or_None, ceo, error_msg)
      - 总经理(ceo)是终审,必需;缺失则 error。
      - 部门经理可为 None(该部门未设经理),由调用方跳过部门经理这级。
        发起人本身就是部门经理的情况也由调用方处理(自动跳过,不能自审)。
    """
    from app.models.user import User

    owner = project.owner
    if not owner:
        return None, None, '项目没有负责人，无法发起审核'

    # 部门经理 = owner 同部门同公司、is_department_manager=True 的用户
    dept_mgr = (User.query
                .filter_by(department=owner.department,
                           company_name=owner.company_name,
                           is_department_manager=True)
                .first())

    # 总经理 = role='ceo'（优先同公司，其次全局）
    ceo = (User.query.filter_by(role='ceo', company_name=owner.company_name).first()
           or User.query.filter_by(role='ceo').first())

    if not ceo:
        return None, None, '未找到总经理(ceo)，请联系管理员配置后再发起'
    return dept_mgr, ceo, None


def get_or_create_hold_template(created_by=None):
    """幂等确保 project_hold 审批模板 + 两个 submitter_designate 步骤存在。

    用按需创建(get-or-create)代替 DB 迁移,避免 CN/SG 两台 NAS 的迁移协调。
    created_by: 建模板的 created_by(用发起人或首个管理员,避免 FK 违例)。
    Returns: (template, step1, step2)
    """
    from app import db
    from app.models.approval import ApprovalProcessTemplate, ApprovalStep
    from app.models.user import User

    tpl = ApprovalProcessTemplate.query.filter_by(object_type=HOLD_OBJECT_TYPE).first()
    if not tpl:
        creator_id = created_by
        if not creator_id or not User.query.get(creator_id):
            admin = User.query.filter_by(role='admin').first() or User.query.first()
            creator_id = admin.id if admin else None
        tpl = ApprovalProcessTemplate(
            name='项目失败/搁置审核',
            object_type=HOLD_OBJECT_TYPE,
            is_active=True,
            created_by=creator_id,
            lock_object_on_start=False,   # 不硬锁项目编辑;阶段推进的锁由前端处理
            lock_reason='失败/搁置审核进行中',
        )
        db.session.add(tpl)
        db.session.flush()

    steps = (ApprovalStep.query.filter_by(process_id=tpl.id)
             .order_by(ApprovalStep.step_order).all())
    if len(steps) < 2:
        for s in steps:
            db.session.delete(s)
        db.session.flush()
        step1 = ApprovalStep(process_id=tpl.id, step_order=1, step_name='部门经理审批',
                             approver_type='submitter_designate', send_email=True)
        step2 = ApprovalStep(process_id=tpl.id, step_order=2, step_name='总经理审批',
                             approver_type='submitter_designate', send_email=True)
        db.session.add_all([step1, step2])
        db.session.flush()
        steps = [step1, step2]
        # 立即提交:模板是一次性独立配置,必须落库,否则 start_approval_process 内部
        # get_object_approval_instance 的强制 rollback 会把未提交的模板冲掉。
        db.session.commit()
    return tpl, steps[0], steps[1]


def get_pending_hold_instance(project_id):
    """返回该项目进行中的 project_hold 审批实例(PENDING),无则 None。"""
    from app.helpers.approval_helpers import get_object_approval_instance
    from app.models.approval import ApprovalStatus
    inst = get_object_approval_instance(HOLD_OBJECT_TYPE, project_id, include_rejected=False)
    if inst and inst.status == ApprovalStatus.PENDING:
        return inst
    return None


def submit_project_hold(project, target, reason, user_id):
    """发起项目失败/搁置审核。

    Args:
        project: Project 对象
        target: 'lost' | 'paused'
        reason: 发起人理由(强制)
        user_id: 发起人
    Returns: (instance, error_msg)
    """
    from app import db
    from sqlalchemy.orm.attributes import flag_modified
    from app.helpers.approval_helpers import start_approval_process

    if target not in HOLD_TARGETS:
        return None, '无效的目标状态'
    reason = (reason or '').strip()
    if not reason:
        return None, '请填写理由（必填）'
    if project.current_stage in ('lost', 'paused'):
        return None, '项目已处于失败/搁置状态'
    if get_pending_hold_instance(project.id):
        return None, '已有进行中的失败/搁置审核，请勿重复发起'

    dept_mgr, ceo, err = resolve_hold_approvers(project)
    if err:
        return None, err
    if ceo.id == user_id:
        # 发起人本人即总经理(终审人),无法自审
        return None, '您是终审人(总经理)，无法对自己发起的项目自审，请由他人操作'

    tpl, step1, step2 = get_or_create_hold_template(created_by=user_id)

    # 部门经理这级是否有效:存在、且不是发起人、且不与总经理重复 —— 否则跳过该级
    step1_approver = dept_mgr if (dept_mgr and dept_mgr.id != user_id and dept_mgr.id != ceo.id) else None
    designated = {str(step2.id): ceo.id}
    if step1_approver:
        designated[str(step1.id)] = step1_approver.id

    instance = start_approval_process(
        HOLD_OBJECT_TYPE, project.id, tpl.id, user_id,
        auto_commit=False, designated_approvers=designated)
    if not instance:
        return None, '发起审核失败（可能已存在审核流程）'

    # 把目标阶段 + 发起人理由注入实例快照(供通过时回调读取 + flow 展示发起节点)
    snap = instance.template_snapshot or {}
    snap['hold_target'] = target
    snap['hold_reason'] = reason
    snap['hold_initiator_id'] = user_id
    instance.template_snapshot = snap
    flag_modified(instance, 'template_snapshot')

    # 发起人即部门经理(或该部门无经理) → 跳过部门经理这级,直接从总经理开始
    if not step1_approver:
        from app.models.approval import ApprovalRecord
        db.session.add(ApprovalRecord(
            instance_id=instance.id, step_id=step1.id, approver_id=user_id,
            action='skipped',
            comment='发起人即部门经理或该部门未设经理，自动跳过部门经理审批'))
        instance.current_step = step2.step_order  # 直接进入总经理审批
        # 通知总经理(start_approval_process 通知的是被跳过的首步,这里补发)
        try:
            from app.services.approval_message_service import ApprovalMessageService
            ApprovalMessageService.send_approval_notification(instance, step2)
        except Exception as _notify_err:
            from flask import current_app
            current_app.logger.warning(f"补发总经理审核通知失败: {_notify_err}")

    db.session.commit()
    return instance, None
