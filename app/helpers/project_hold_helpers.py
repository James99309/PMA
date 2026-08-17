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
    import os
    from app.models.user import User

    owner = project.owner
    if not owner:
        return None, None, '项目没有负责人，无法发起审核'

    def _active_role(role):
        """在职激活的该角色用户(优先同公司,其次全局)"""
        q = User.query.filter(User.role == role, User._is_active.is_(True))
        return (q.filter(User.company_name == owner.company_name).first() or q.first())

    # 总经理 = role='ceo'(终审,必需)
    ceo = _active_role('ceo')
    if not ceo:
        return None, None, '未找到总经理(ceo)，请联系管理员配置后再发起'

    # SG(ovs):组织结构扁平,无业务线经理层,报备/失败/搁置一律跳过第一步直达总经理(ceo)。
    # 与 resolve_win_lock_candidates 的 ovs 逻辑保持一致(SG 任何类型 → ceo)。
    _db_type = os.environ.get('PMA_DB_TYPE', os.environ.get('SUPABASE_DB_TYPE', 'sp8d'))
    if _db_type == 'ovs':
        return None, ceo, None

    # 第一步按业务线分流 —— 判据收口到 biz_line_routing(只看项目类型,不看报备来源)。
    # 2026-07-14:这里原先是 `pt == 'channel_follow' or report_source == 'channel'`,
    # 于是「国航股份浙江分公司新园区」(类型=销售重点、报备来源=渠道)被派给了渠道经理。
    from app.helpers.biz_line_routing import approver_role_chain

    first = None
    for role in approver_role_chain(project, owner):
        first = _active_role(role)
        if first:
            break
    return first, ceo, None


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
        step1 = ApprovalStep(process_id=tpl.id, step_order=1, step_name='业务线经理审批',
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

    # 业务线经理这级是否有效:存在、且不是发起人、且不与总经理重复 —— 否则跳过该级
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

    # 业务线经理缺位/重复 → 跳过该级,直接从总经理开始
    if not step1_approver:
        from app.models.approval import ApprovalRecord
        db.session.add(ApprovalRecord(
            instance_id=instance.id, step_id=step1.id, approver_id=user_id,
            action='skipped',
            comment='业务线经理缺位或与发起人/终审人重复，自动跳过该级审批'))
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


# ─────────────────────────────────────────────────────────────────────────────
# 项目报备审批(object_type='project')业务线路由 —— 2026-06-13 与用户确认:
# 与失败审核同款分流(渠道→渠道经理[缺位营销总监代理]/服务→服务经理/其余→营销总监,
# 缺位直达)→ 总经理终审;授权编号在整条通过时按项目类型自动生成
# (channel_follow→CPJ / sales_focus→SPJ / business_opportunity→APJ),
# 取代旧 branch 步骤的人工选择。旧模板停用,进行中的旧实例按各自快照走完。
#
# 2026-08-17 用户确认:报备升为**三级** —— 所有业务线(渠道/销售/服务)先过「商务初审」
# (商务助理 business_admin,当前 CN 唯一在职者=童蕾),再到业务线经理,最后总经理。
# 只改报备:失败/搁置审核(resolve_hold_approvers)与成功锁定审核不变,仍是两级/单级。
# ─────────────────────────────────────────────────────────────────────────────

REPORT_TEMPLATE_NAME = '项目报备审批(业务线)'

# 商务初审角色链(与业务线无关,所有报备统一先过这一级);按序找在职用户,缺位则跳过该级
REPORT_PRE_REVIEW_ROLES = ('business_admin',)

# 三级步骤名(顺序即 step_order 1/2/3)
REPORT_STEP_NAMES = ('商务初审', '业务线经理审批', '总经理审批')


def resolve_report_approvers(project):
    """解析报备审批三级审批人。

    Returns: (pre_reviewer_or_None, biz_manager_or_None, ceo, error_msg)
      - 商务初审/业务线经理都可为 None(缺位),由调用方跳过该级;总经理必需。
      - SG(ovs) 组织扁平:无商务/业务线经理层,直达总经理
        (与 resolve_hold_approvers 的 ovs 分支一致)。
    """
    import os
    from app.models.user import User

    biz_mgr, ceo, err = resolve_hold_approvers(project)   # 业务线分流复用同一规则
    if err:
        return None, None, None, err

    _db_type = os.environ.get('PMA_DB_TYPE', os.environ.get('SUPABASE_DB_TYPE', 'sp8d'))
    if _db_type == 'ovs':
        return None, None, ceo, None

    owner = project.owner
    pre = None
    for role in REPORT_PRE_REVIEW_ROLES:
        q = User.query.filter(User.role == role, User._is_active.is_(True))
        pre = ((q.filter(User.company_name == owner.company_name).first() if owner else None)
               or q.first())
        if pre:
            break
    return pre, biz_mgr, ceo, None


def get_or_create_report_template(created_by=None):
    """幂等确保业务线报备模板 + 三步 submitter_designate 存在。

    Returns: (template, step1商务初审, step2业务线经理, step3总经理)

    2026-08-17 从两步(业务线经理→总经理)升级为三步。旧模板**原地升级**:原两步
    step_order 后移一位,新增「商务初审」为第 1 步。进行中的实例不受影响 ——
    ApprovalInstance.get_steps() 优先读 template_snapshot(发起时的两步定义),
    current_step 也是对快照里的 step_order 取值,所以在办单按旧两步走完;它们都停在
    总经理这一级,与新流程的末级一致,不会被"退回"业务线经理。
    """
    from app import db
    from app.models.approval import ApprovalProcessTemplate, ApprovalStep
    from app.models.user import User

    tpl = ApprovalProcessTemplate.query.filter_by(
        object_type='project', name=REPORT_TEMPLATE_NAME).first()
    if not tpl:
        creator_id = created_by
        if not creator_id or not User.query.get(creator_id):
            admin = User.query.filter_by(role='admin').first() or User.query.first()
            creator_id = admin.id if admin else None
        tpl = ApprovalProcessTemplate(
            name=REPORT_TEMPLATE_NAME, object_type='project',
            created_by=creator_id, is_active=True)
        db.session.add(tpl)
        db.session.flush()

    def _mk(order, name):
        s = ApprovalStep(process_id=tpl.id, step_order=order, step_name=name,
                         approver_type='submitter_designate', send_email=True)
        db.session.add(s)
        return s

    steps = (ApprovalStep.query.filter_by(process_id=tpl.id)
             .order_by(ApprovalStep.step_order).all())
    if len(steps) == 2:
        # 旧两步模板原地升级:不删旧步(其 id 被历史 approval_record 引用),只后移顺序
        steps[0].step_order, steps[0].step_name = 2, REPORT_STEP_NAMES[1]
        steps[1].step_order, steps[1].step_name = 3, REPORT_STEP_NAMES[2]
        steps = [_mk(1, REPORT_STEP_NAMES[0])] + steps
        db.session.flush()
        db.session.commit()   # 模板独立落库,防内部 rollback 冲掉
    elif len(steps) != 3:
        for s in steps:
            db.session.delete(s)
        db.session.flush()
        steps = [_mk(i + 1, n) for i, n in enumerate(REPORT_STEP_NAMES)]
        db.session.flush()
        db.session.commit()
    return tpl, steps[0], steps[1], steps[2]


def submit_project_report_approval(project, user_id):
    """发起报备审批(三级:商务初审 → 业务线经理 → 总经理)。Returns (instance, err)。"""
    from app import db
    from sqlalchemy.orm.attributes import flag_modified
    from app.helpers.approval_helpers import start_approval_process
    from app.models.approval import ApprovalRecord

    pre, biz, ceo, err = resolve_report_approvers(project)
    if err:
        return None, err

    tpl, step1, step2, step3 = get_or_create_report_template(created_by=user_id)

    # 逐级有效性:存在、不是发起人、不与后面各级重复 —— 否则该级自动跳过(不能自审/重复审)
    taken = {ceo.id}
    biz_ok = bool(biz) and biz.id != user_id and biz.id not in taken
    if biz_ok:
        taken.add(biz.id)
    pre_ok = bool(pre) and pre.id != user_id and pre.id not in taken

    designated = {str(step3.id): ceo.id}
    if biz_ok:
        designated[str(step2.id)] = biz.id
    if pre_ok:
        designated[str(step1.id)] = pre.id

    instance = start_approval_process(
        'project', project.id, tpl.id, user_id,
        auto_commit=False, designated_approvers=designated)
    if not instance:
        return None, '发起审批失败(可能已存在审批流程)'

    SKIP_REASON = {
        step1.id: '商务初审人缺位或与发起人/后续审批人重复，自动跳过该级审批',
        step2.id: '业务线经理缺位或与发起人/终审人重复，自动跳过该级审批',
    }
    chain = [(step1, pre if pre_ok else None), (step2, biz if biz_ok else None), (step3, ceo)]
    invalid_ids = {st.id: SKIP_REASON[st.id] for st, approver in chain if not approver}

    # 无效级在**本实例快照**里显式标记 auto_skip:引擎推进时才会跳过它。
    # (submitter_designate 步没指定审批人时引擎默认不跳 → 会卡在"无人可审"。
    #  中间级失效就是这种情况,例如业务线经理本人发起报备。)
    snap = instance.template_snapshot or {}
    snap['biz_line_route'] = True
    for st_data in snap.get('steps', []):
        _reason = invalid_ids.get(st_data.get('step_id'))
        if _reason:
            st_data['auto_skip'] = True
            st_data['skip_reason'] = _reason
    instance.template_snapshot = snap
    flag_modified(instance, 'template_snapshot')

    # 开头连续的无效级:start_approval_process 已把 current_step 定成 1 并通知了首步,
    # 标记来不及生效(标记发生在它返回之后),所以这里手工记 skipped + 推进 + 补发通知。
    # 中间级的无效由上面的 auto_skip 标记在推进时由引擎处理。
    start_step = None
    for st, approver in chain:
        if approver:
            start_step = st
            break
        db.session.add(ApprovalRecord(
            instance_id=instance.id, step_id=st.id, approver_id=user_id,
            action='skipped', comment=SKIP_REASON[st.id]))

    if start_step is not step1:
        instance.current_step = start_step.step_order
        try:
            from app.services.approval_message_service import ApprovalMessageService
            ApprovalMessageService.send_approval_notification(instance, start_step)
        except Exception:
            pass
    return instance, None


# ─────────────────────────────────────────────────────────────────────────────
# 项目成功锁定审核 (object_type='project_win_lock') —— 2026-06-16 用户确认:
# 单级审核;审核人由提交人弹窗强制指定。
#   CN(sp8d) 业务线路由: 渠道→渠道经理(缺位营销总监) / 服务→服务经理 / 其余→营销总监
#   SG(ovs) 任何类型 → 总经理(ceo)
# 提交→进行中(徽章橙「锁定审核中」);通过→真正 win_locked(徽章绿,打金额/报价/交期快照);
# 驳回→不锁定(无徽章)。徽章=审批结果显示。
# ─────────────────────────────────────────────────────────────────────────────

WIN_LOCK_OBJECT_TYPE = 'project_win_lock'


def resolve_win_lock_candidates(project, exclude_user_id=None):
    """成功锁定审核人候选(供提交人指定弹窗)。Returns (candidates[list[User]], err)。

    逐级排除提交人(exclude_user_id):某级在职人员只剩提交人本人 → 视为该级无效,自动升上一级
    (避免自审 + 满足"该级不存在则上一级")。最终兜底到总经理(ceo)。
    """
    import os
    from app.models.user import User

    def _role_users(role):
        q = User.query.filter(User.role == role, User._is_active.is_(True))
        if exclude_user_id:
            q = q.filter(User.id != exclude_user_id)
        return q.order_by(User.real_name.asc(), User.username.asc()).all()

    db_type = os.environ.get('PMA_DB_TYPE', os.environ.get('SUPABASE_DB_TYPE', 'sp8d'))
    if db_type == 'ovs':
        cands = _role_users('ceo')
        return (cands, None) if cands else (None, '未找到总经理(ceo)，请联系管理员')
    owner = project.owner
    # 业务线主审 → 缺位/仅自己 逐级兜底,最终到总经理(ceo)。仅取在职(_is_active),离职自动跳过。
    # 判据收口到 biz_line_routing:原先这里**只看 report_source、完全没看项目类型**,
    # 渠道来源的销售项目会被派给渠道线;现统一为「只看项目类型」。
    from app.helpers.biz_line_routing import approver_role_chain

    cands = []
    for role in approver_role_chain(project, owner):
        cands = _role_users(role)
        if cands:
            break
    cands = cands or _role_users('ceo')
    return (cands, None) if cands else (None, '未找到审核人(营销总监/总经理均缺),请联系管理员')


def get_or_create_win_lock_template(created_by=None):
    """幂等确保 project_win_lock 模板 + 单步 submitter_designate。Returns (template, step1)。"""
    from app import db
    from app.models.approval import ApprovalProcessTemplate, ApprovalStep
    from app.models.user import User

    tpl = ApprovalProcessTemplate.query.filter_by(object_type=WIN_LOCK_OBJECT_TYPE).first()
    if not tpl:
        creator_id = created_by
        if not creator_id or not User.query.get(creator_id):
            admin = User.query.filter_by(role='admin').first() or User.query.first()
            creator_id = admin.id if admin else None
        tpl = ApprovalProcessTemplate(
            name='项目成功锁定审核', object_type=WIN_LOCK_OBJECT_TYPE, is_active=True,
            created_by=creator_id, lock_object_on_start=False,
            lock_reason='成功锁定审核进行中')
        db.session.add(tpl)
        db.session.flush()
    steps = ApprovalStep.query.filter_by(process_id=tpl.id).order_by(ApprovalStep.step_order).all()
    if len(steps) < 1:
        step1 = ApprovalStep(process_id=tpl.id, step_order=1, step_name='成功锁定审核',
                             approver_type='submitter_designate', send_email=True)
        db.session.add(step1)
        db.session.flush()
        steps = [step1]
        db.session.commit()
    return tpl, steps[0]


def get_pending_win_lock_instance(project_id):
    """该项目进行中的成功锁定审核实例(PENDING),无则 None。"""
    from app.helpers.approval_helpers import get_object_approval_instance
    from app.models.approval import ApprovalStatus
    inst = get_object_approval_instance(WIN_LOCK_OBJECT_TYPE, project_id, include_rejected=False)
    if inst and inst.status == ApprovalStatus.PENDING:
        return inst
    return None


def submit_win_lock(project, reason, user_id, approver_id, quotation_id, delivery_date):
    """发起成功锁定审核。不立即锁定;通过回调才锁。Returns (instance, err)。"""
    from app import db
    from sqlalchemy.orm.attributes import flag_modified
    from app.helpers.approval_helpers import start_approval_process
    from app.models.user import User

    reason = (reason or '').strip()
    if not reason:
        return None, '请填写锁定理由（必填）'
    if not approver_id or not User.query.get(int(approver_id)):
        return None, '请选择审核人'
    if int(approver_id) == int(user_id):
        return None, '不能指定自己为审核人，请由他人审核'
    if get_pending_win_lock_instance(project.id):
        return None, '已有进行中的成功锁定审核，请勿重复发起'

    tpl, step1 = get_or_create_win_lock_template(created_by=user_id)
    instance = start_approval_process(
        WIN_LOCK_OBJECT_TYPE, project.id, tpl.id, user_id,
        auto_commit=False, designated_approvers={str(step1.id): int(approver_id)})
    if not instance:
        return None, '发起审核失败（可能已存在审核流程）'
    snap = instance.template_snapshot or {}
    snap.update({
        'wl_reason': reason,
        'wl_quotation_id': quotation_id,
        'wl_delivery': delivery_date.isoformat() if delivery_date else None,
        'wl_initiator_id': user_id,
    })
    instance.template_snapshot = snap
    flag_modified(instance, 'template_snapshot')
    db.session.commit()
    return instance, None
