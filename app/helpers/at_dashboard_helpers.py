# -*- coding: utf-8 -*-
"""
AT 仪表盘数据聚合 helpers

  - build_dashboard(user) → 完整 dict,与 dashboard-data.js DASH schema 对齐
                            {todos, kpis, todayStats, funnel, funnelConversion, funnelYoY,
                             projects, projectCounts, quotes, quoteCounts,
                             expense, worklog, alerts, layout}

字段命名严格匹配设计稿(dashboard-cards-*.jsx),数据填充以真实 DB 为主、缺失时用合理默认。
"""
from datetime import datetime, timedelta
from flask import url_for
from flask_babel import gettext as _t


def _fmt_user(u):
    if not u:
        return '—'
    return getattr(u, 'real_name', None) or getattr(u, 'username', None) or '—'


def _ago(dt):
    if not dt:
        return '—'
    sec = (datetime.now() - dt).total_seconds()
    if sec < 3600:  return _t('%(n)s 分钟前', n=int(sec/60))
    if sec < 86400: return _t('%(n)s 小时前', n=int(sec/3600))
    days = int(sec / 86400)
    return _t('%(d)s 天前', d=days) if days < 30 else dt.strftime('%m-%d')


# ─── Scope(我的/团队/公司/系统)──────────────────────────
# 权限级别 → 仪表盘范围档位标签 / 排序
_DASH_LEVEL_LABELS = {'system': '系统', 'company': '公司', 'department': '团队'}
_DASH_LEVEL_RANK = {'personal': 0, 'department': 1, 'company': 2, 'system': 3}


def _user_level(user, module):
    try:
        return user.get_permission_level(module) or 'personal'
    except Exception:
        return 'personal'


def _viewable_id_clause(model, user):
    """返回 `model.id IN (get_viewable_data 可见 id 子查询)` 的过滤子句。

    get_viewable_data 已封装：权限级别 + 数据归属 + 共享 + content_filters(如渠道/project_type),
    与各列表页完全一致,绝不越权。
    """
    from app.utils.access_control import get_viewable_data
    from app import db
    vq = get_viewable_data(model, user)
    sub = vq.with_entities(model.id).subquery()
    return model.id.in_(db.session.query(sub.c.id))


def _get_dash_scope(user):
    """仪表盘范围档位元数据(供模板渲染"我的 / 次级" chip)。

    次级档位标签 = 用户在仪表盘相关模块(project/quotation/expense)中的**最高权限级别**:
      system→系统 / company→公司 / department→团队 / personal→无次级(只看"我的")。

    注意:这里只决定"档位标签 + 是否显示次级 chip";实际数据范围由 build_dashboard
    用 get_viewable_data 按各自模块取(权限级别+归属+共享+content_filters 全生效),绝不越权。
    """
    mine = {'key': 'mine', 'label': _t('我的')}
    levels = [_user_level(user, m) for m in ('project', 'quotation', 'expense')]
    top = max(levels, key=lambda l: _DASH_LEVEL_RANK.get(l, 0))
    secondary = None
    if _DASH_LEVEL_RANK.get(top, 0) > 0:
        secondary = {'key': 'team', 'label': _t(_DASH_LEVEL_LABELS.get(top, '团队'))}
    return {'mine': mine, 'secondary': secondary, 'top_level': top}


# ─── 待办 8 条 ─────────────────────────────────────────
def _build_todos(user):
    """
    待办列表 — 完全复用老 PMA 后端逻辑,不自造规则:
      1) 待审批:get_user_pending_approvals(user.id) — 已处理 dynamic approver
      2) 待确认产品:QuotationConfirmationTask(老消息面板的"待办任务"实体)
      3) @我提及:Message 表的 worklog_mention / task_reply / task_assigned(未读)
      4) 跟进提醒:中标项目 >30 天无跟进(Action) + 我的任务 >10 天无更新
         (按逾期天数倒序;计数取真实条数,不再 limit)
    """
    out = []
    obj_label_map = {
        'expense': _t('报销单'), 'purchase_order': _t('采购订单'),
        'project': _t('项目立项'), 'pricing_order': _t('批价单'),
        'quotation': _t('报价单'), 'sales_order': _t('客户订单'),
        'customer': _t('客户'), 'project_hold': _t('项目搁置/失败审核'),
        'dealer_apply': _t('渠道身份审批'), 'perf_settlement': _t('绩效结算'),
        'salary_run': _t('月度薪资审批'),
    }

    # 1) 待审批 — 复用 get_user_pending_approvals
    # AT 详情页 URL 映射 — 点击跳转到对应 AT 详情 + #approval hash 自动展开 chip dropdown
    at_url_map = {
        'expense':         lambda i: f'/expense/{i}/at_view#approval',
        'project':         lambda i: f'/project/{i}/at_view#approval',
        'project_hold':    lambda i: f'/project/{i}/at_view#approval-project_hold',
        'quotation':       lambda i: f'/quotation/{i}/at_view#approval',
        'purchase_order':  lambda i: f'/purchase-order/{i}#approval',
        'dealer_apply':    None,   # 占位:下面按实例跳审批中心
    }
    try:
        from app.helpers.approval_helpers import get_user_pending_approvals
        from app.models.user import User
        page = get_user_pending_approvals(user_id=user.id, per_page=3)
        for ai in page.items:
            urgent = (datetime.now() - (ai.started_at or datetime.now())).days >= 3
            obj_label = obj_label_map.get(ai.object_type, ai.object_type)
            submitter = User.query.get(ai.created_by) if ai.created_by else None
            url_builder = at_url_map.get(ai.object_type)
            route_url = url_builder(ai.object_id) if url_builder else '#'
            if ai.object_type in ('dealer_apply',):
                # 渠道身份审批:跳通用 AT 审批详情(流程图+审批操作)
                route_url = f'/approval/at-detail/{ai.id}'
            # 标题:审批流程名称 + 关联项目/对象名称(项目类带项目名;搁置/失败区分)
            title = f'{obj_label} #{ai.object_id}'
            if ai.object_type == 'perf_settlement':
                # 绩效结算:标题=姓名·年Q季 绩效结算;点击进个人绩效页并自动展开审批 chip
                from app.models.performance_settlement import PerformanceSettlement
                _st = PerformanceSettlement.query.get(ai.object_id)
                if _st:
                    _su = User.query.get(_st.user_id)
                    _sn = (_su.real_name or _su.username) if _su else ''
                    title = f'{_sn} · {_st.year} Q{_st.quarter} {_t("绩效结算")}'
                    route_url = f'/user/at-config/performance?user={_st.user_id}&settle_q={_st.quarter}'
            if ai.object_type in ('project', 'project_hold'):
                from app.models.project import Project
                _proj = Project.query.get(ai.object_id)
                _pname = _proj.project_name if _proj else None
                _label = obj_label
                if ai.object_type == 'project_hold':
                    _tgt = (ai.template_snapshot or {}).get('hold_target')
                    _label = _t('项目失败审核') if _tgt == 'lost' else (_t('项目搁置审核') if _tgt == 'paused' else obj_label)
                title = f'{_label} · {_pname}' if _pname else f'{_label} #{ai.object_id}'
            elif ai.object_type == 'pricing_order':
                # 批价单显示批价单号(order_number)而非内部 ID
                from app.models.pricing_order import PricingOrder
                _po = PricingOrder.query.get(ai.object_id)
                title = f'{obj_label} {_po.order_number}' if (_po and _po.order_number) else title
            out.append({
                'id': f'AI{ai.id}', 'type': 'approval', 'typeLabel': _t('待审批'), 'tone': 'warn',
                'title': title,
                # 待审批 tab 已表明身份,"我作为当前节点审批人"冗余 → 换成提交人账户名
                'meta': _fmt_user(submitter),
                'who': '—',
                'when': _ago(ai.started_at),
                'route': route_url, 'urgent': urgent,
            })
    except Exception as e:
        import logging; logging.warning(f'todos approval err: {e}')

    # 1b) 待我审核的任务(任务审计:TaskReviewer 为单一事实源,归入「待审批」)
    try:
        from app import db
        from app.models.task import Task, TaskReviewer
        from app.models.user import User
        rows = db.session.query(Task, TaskReviewer).join(
            TaskReviewer, TaskReviewer.task_id == Task.id).filter(
            TaskReviewer.reviewer_id == user.id,
            TaskReviewer.status == 'pending',
            Task.review_status == 'pending_review',
            Task.is_deleted == False,
        ).order_by(Task.updated_at.desc()).all()
        for t, tr in rows:
            submitter = User.query.get(t.assignee_id) if t.assignee_id else None
            out.append({
                'id': f'TR{t.id}', 'type': 'approval', 'typeLabel': _t('待审核'), 'tone': 'warn',
                'title': f'{_t("任务审核")} · {t.title}',
                'meta': _fmt_user(submitter), 'who': '—',
                'when': _ago(t.updated_at),
                'route': f'/task/management?task_id={t.id}', 'urgent': False,
            })
    except Exception as e:
        import logging; logging.warning(f'todos task-review err: {e}')

    # 2) 待确认产品 — SM 老任务,已废弃(报价单标准审批已并入「待我审批」列表)
    # 旧 QuotationConfirmationTask 数据保留在 DB,但仪表盘不再显示其 todo
    # 报价单的标准 ApprovalInstance 待审批,通过上面 get_user_pending_approvals 同款入口处理

    # 3) @我提及 — Message 表未读 mention 类
    try:
        from app.models.message import Message
        msgs = Message.query.filter(
            Message.recipient_id == user.id,
            Message.message_type.in_(['worklog_mention', 'task_reply', 'task_assigned']),
            Message.is_read == False,
        ).order_by(Message.created_at.desc()).limit(2).all()
        type_label_map = {
            'worklog_mention': _t('日志 @ 我'),
            'task_reply':      _t('任务回复'),
            'task_assigned':   _t('任务指派'),
        }
        for m in msgs:
            from app.models.user import User
            sender = User.query.get(m.sender_id) if m.sender_id else None
            # 可点击跳转:任务类 → 任务管理页并打开该任务
            _route = '#'
            if m.related_object_type == 'task' and m.related_object_id:
                _route = f'/task/management?task_id={m.related_object_id}'
            out.append({
                'id': f'M{m.id}', 'type': 'mention', 'typeLabel': type_label_map.get(m.message_type, _t('@我')),
                'tone': 'info',
                'title': (m.title or '')[:60],
                'meta': (m.content or '')[:60],
                'who': _fmt_user(sender),
                'when': _ago(m.created_at),
                'route': _route, 'urgent': False,
            })
    except Exception as e:
        import logging; logging.warning(f'todos mention err: {e}')

    # 4) 跟进提醒 — 中标项目 >30 天无跟进 + 我的任务 >10 天无更新(按逾期天数倒序)
    try:
        from sqlalchemy import func as _f, or_ as _or
        from app import db
        now = datetime.now()
        today = now.date()
        fu = []

        # 4a) 项目跟进分级提醒(排除 签约/暂停/失败):
        #     ≥20 天未跟进 → 当事人(负责人/厂商销售);≥30 天 → 部门经理(部门成员的项目);
        #     ≥35 天 → 总经理(ceo,全部项目)。同一项目命中多个视角取最低阈值。
        #     口径:最近 Action.date;无跟进 → 进入当前阶段时间(阶段历史),兜底创建时间。
        from app.models.project import Project
        from app.models.action import Action
        from app.models.projectpm_stage_history import ProjectStageHistory
        from app.models.user import User as _U
        _EXCLUDE_STAGES = ('signed', 'paused', 'lost')
        _base_f = [Project.is_deleted == False, ~Project.current_stage.in_(_EXCLUDE_STAGES)]

        cand = {}   # pid → (project, threshold, meta_suffix)
        # 视角1:当事人(20 天)
        for p in Project.query.filter(*_base_f, _or(Project.owner_id == user.id,
                                                    Project.vendor_sales_manager_id == user.id)).all():
            cand[p.id] = (p, 20, '')
        # 视角2:部门经理(30 天,部门成员的项目;同公司)
        if user.is_department_manager and user.department:
            _dept_ids = [u.id for u in _U.query.filter(
                _U.department == user.department,
                _U.company_name == user.company_name).all()]
            if _dept_ids:
                for p in Project.query.filter(*_base_f, Project.owner_id.in_(_dept_ids)).all():
                    if p.id not in cand:
                        cand[p.id] = (p, 30, '')
        # 视角3:总经理(35 天,全部)
        if user.role == 'ceo':
            for p in Project.query.filter(*_base_f).all():
                if p.id not in cand:
                    cand[p.id] = (p, 35, '')

        proj_ids = list(cand.keys())
        # 批量:每项目最近 Action.date(一次 group by)
        last_action = {}
        if proj_ids:
            last_action = dict(db.session.query(Action.project_id, _f.max(Action.date))
                               .filter(Action.project_id.in_(proj_ids))
                               .group_by(Action.project_id).all())
        # 批量:无跟进项目 → 进入当前阶段时间(最近一次阶段变更)
        no_act_ids = [pid for pid in proj_ids if pid not in last_action]
        stage_since = {}
        if no_act_ids:
            stage_since = dict(db.session.query(ProjectStageHistory.project_id,
                                                _f.max(ProjectStageHistory.change_date))
                               .filter(ProjectStageHistory.project_id.in_(no_act_ids))
                               .group_by(ProjectStageHistory.project_id).all())
        _stage_zh = {'discover': _t('发现'), 'embed': _t('植入'), 'pre_tender': _t('标前'),
                     'tendering': _t('标中'), 'awarded': _t('中标'), 'quoted': _t('批价')}
        for pid, (p, threshold, _suffix) in cand.items():
            last_date = last_action.get(pid)
            if last_date:
                days = (today - last_date).days
            else:
                base = stage_since.get(pid) or p.created_at
                days = (now - base).days if base else None
            if days is not None and days >= threshold:
                _meta = _stage_zh.get(p.current_stage, p.current_stage or '')
                if threshold >= 30 and p.owner_id != user.id:
                    _own = _U.query.get(p.owner_id) if p.owner_id else None
                    if _own:
                        _meta += f' · {_own.real_name or _own.username}'
                fu.append({
                    'id': f'P{pid}', 'type': 'action', 'typeLabel': _t('项目跟进'), 'tone': 'danger',
                    'title': f'{p.project_name} · {_t("%(d)s 天未跟进", d=days)}', 'meta': _meta,
                    'who': '—', 'when': _t('%(d)s天', d=days),
                    'route': f'/project/{pid}/at_view', 'urgent': days >= threshold + 15, '_d': days,
                })

        # 4b) 我的任务:指派给我 或 我创建;非已完成;最近一次交互
        #     (max(updated_at, 最近未删除回复)) >10 天
        from app.models.task import Task, TaskReply
        tasks = Task.query.filter(
            Task.is_deleted == False,
            Task.status != 'completed',
            _or(Task.assignee_id == user.id, Task.creator_id == user.id),
        ).all()
        task_ids = [t.id for t in tasks]
        # 批量:每任务最近未删除回复时间(一次 group by)
        last_reply_map = {}
        if task_ids:
            last_reply_map = dict(db.session.query(TaskReply.task_id, _f.max(TaskReply.created_at))
                                  .filter(TaskReply.task_id.in_(task_ids), TaskReply.is_deleted == False)
                                  .group_by(TaskReply.task_id).all())
        for t in tasks:
            last_reply = last_reply_map.get(t.id)
            cands = [d for d in (t.updated_at, last_reply, t.created_at) if d]
            last_act = max(cands) if cands else None
            days = (now - last_act).days if last_act else None
            if days is not None and days > 10:
                fu.append({
                    'id': f'T{t.id}', 'type': 'action', 'typeLabel': _t('任务跟进'), 'tone': 'danger',
                    'title': f'{t.title} · {_t("%(d)s 天未更新", d=days)}', 'meta': _t('任务'),
                    'who': '—', 'when': _t('%(d)s天', d=days),
                    'route': f'/task/management?task={t.id}', 'urgent': days > 20, '_d': days,
                })

        # 4c) 锁定成功提醒 — 给「项目负责人的部门经理 / 总经理(ceo)/ 管理员」的跟进提醒
        try:
            from app.models.user import User as _User
            wl_q = None
            if user.role in ('admin', 'ceo'):
                wl_q = Project.query.filter(Project.is_deleted == False,
                                            Project.win_locked.is_(True),
                                            Project.current_stage != 'signed')
            elif user.is_department_manager and user.department:
                # 我部门成员名下被锁定的项目
                dept_ids = [u.id for u in _User.query.filter(
                    _User.department == user.department,
                    _User.company_name == user.company_name).all()]
                if dept_ids:
                    wl_q = Project.query.filter(Project.is_deleted == False,
                                                Project.win_locked.is_(True),
                                                Project.current_stage != 'signed',
                                                Project.owner_id.in_(dept_ids))
            if wl_q is not None:
                for p_ in wl_q.order_by(Project.win_locked_at.desc()).limit(10).all():
                    locker = _User.query.get(p_.win_locked_by) if p_.win_locked_by else None
                    days_ = (now - p_.win_locked_at).days if p_.win_locked_at else 0
                    fu.append({
                        'id': f'WL{p_.id}', 'type': 'action', 'typeLabel': _t('锁定成功'), 'tone': 'warn',
                        'title': f'{p_.project_name}',
                        'meta': (p_.win_lock_reason or '')[:50],
                        'who': _fmt_user(locker), 'when': _ago(p_.win_locked_at),
                        'route': f'/project/{p_.id}/at_view', 'urgent': False, '_d': days_,
                    })
        except Exception as _we:
            import logging; logging.warning(f'todos winlock err: {_we}')

        fu.sort(key=lambda x: x['_d'], reverse=True)
        for it in fu[:50]:        # 安全上限;列表只展示 top 5,其余进"显示其余 N 项"
            it.pop('_d', None)
            out.append(it)
    except Exception as e:
        import logging; logging.warning(f'todos followup err: {e}')

    return out


# ─── KPI ─── 直查业务表实时聚合(避开 PMA 内置 KPI 配置的字段名 bug)
#            返回 3 套粒度:本月 / 本季 / 本年,前端 tab 切换显示
def _kpi_delta(current, previous):
    """同比一周期 → (文案, tone)。"""
    if previous <= 0:
        return ('—' if current == 0 else _t('新增'), 'success' if current > 0 else 'neutral')
    pct = round((float(current) - float(previous)) / float(previous) * 100)
    if pct == 0:
        return (_t('持平'), 'neutral')
    sign = '+' if pct > 0 else ''
    return (f'{sign}{pct}%', 'success' if pct > 0 else 'warn')


def _kpi_item(label, value, target, unit, prev, tone, delta=None, as_float=False, data_extra=None):
    """构造一个 KPI 指标项(列表契约)。delta=('文案','tone') 可显式覆盖(快照型指标用)。
    as_float=True 时 value/target 保留 1 位小数(品质分等水平值);data_extra 合并进 data
    (如固定档位项的 tier 等级 / pct 达成率)。"""
    if delta is None:
        d, dt = _kpi_delta(value, prev)
    else:
        d, dt = delta
    if as_float:
        v, t = round(float(value), 1), round(float(target), 1)
        if v == int(v):
            v = int(v)        # 整数值去掉 .0(0.0→0, 5.0→5),保留 1.3
        if t == int(t):
            t = int(t)
    else:
        v, t = int(value), int(target)
    data = {'label': label, 'value': v, 'target': t, 'unit': unit}
    if data_extra:
        data.update(data_extra)
    return {'data': data, 'tone': tone, 'delta': d, 'deltaTone': dt}


def _framework_targets(user, year, target_months):
    """从新绩效配置框架取目标(个人覆盖 > 角色默认;金额已转元)。

    返回 {target_key: 本期累加值};完全未配置(无角色默认也无个人覆盖)返回 None,
    调用方据此显示「KPI 未设定」空状态。仪表盘与绩效达成视图自此同一目标来源。
    注意:跨月累加只对金额/数量类正确;比率类(如 se_confirm_quality)是水平目标,
    累加无意义 — 消费方仅取金额/数量 key,新增消费时勿直接累加率类。
    """
    try:
        from app.services.performance_dashboard_service import PerformanceDashboardService
        tmap = PerformanceDashboardService.get_user_kpi_targets(user.id, year)
    except Exception:
        return None
    if not tmap:
        return None
    out = {}
    for m in target_months:
        for k, v in (tmap.get(m) or {}).items():
            out[k] = out.get(k, 0) + float(v or 0)
    return out


def _kpi_one_period(user, start, end, prev_start, prev_end, label_prefix,
                    target_months, currency_symbol='¥'):
    """对一个时间窗口算 4 项 KPI(actual + 上一周期 actual + 累加 target)"""
    from sqlalchemy import func
    from app import db
    from app.models.pricing_order import PricingOrder
    from app.models.quotation import Quotation
    from app.models.customer import Company
    from app.models.project import Project

    # 销售额:PricingOrder 审批通过(created_by 限定)
    def _sales(s, e):
        return db.session.query(func.coalesce(func.sum(PricingOrder.pricing_total_amount), 0)).filter(
            PricingOrder.status == 'approved',
            PricingOrder.created_by == user.id,
            PricingOrder.approved_at >= s, PricingOrder.approved_at < e,
        ).scalar() or 0

    # 植入额:Quotation.implant_total_amount(owner_id 归属)
    def _implant(s, e):
        return db.session.query(func.coalesce(func.sum(Quotation.implant_total_amount), 0)).filter(
            Quotation.owner_id == user.id,
            Quotation.created_at >= s, Quotation.created_at < e,
        ).scalar() or 0

    # 新项目:owner_id 归属
    def _projects(s, e):
        return db.session.query(func.count(Project.id)).filter(
            Project.owner_id == user.id,
            Project.created_at >= s, Project.created_at < e,
        ).scalar() or 0

    # 新客户:owner_id + company_type=customer
    def _customers(s, e):
        return db.session.query(func.count(Company.id)).filter(
            Company.owner_id == user.id,
            Company.company_type == 'customer',
            Company.created_at >= s, Company.created_at < e,
        ).scalar() or 0

    sales_a, sales_p     = _sales(start, end),    _sales(prev_start, prev_end)
    implant_a, implant_p = _implant(start, end),  _implant(prev_start, prev_end)
    proj_a, proj_p       = _projects(start, end), _projects(prev_start, prev_end)
    cust_a, cust_p       = _customers(start, end),_customers(prev_start, prev_end)

    # Target:新绩效配置框架(个人覆盖>角色默认),与绩效达成视图同源;
    # 完全未配置 → 返回空列表,模板显示「KPI 未设定」
    ft = _framework_targets(user, start.year, target_months)
    if ft is None:
        return []
    sales_t   = ft.get('sales_amount_target', 0)
    implant_t = ft.get('implant_amount_target', 0)
    proj_t    = ft.get('new_projects_target', 0)
    cust_t    = ft.get('new_customers_target', 0)

    def _delta(current, previous):
        if previous <= 0:
            return ('—' if current == 0 else _t('新增'), 'success' if current > 0 else 'neutral')
        pct = round((float(current) - float(previous)) / float(previous) * 100)
        if pct == 0:
            return (_t('持平'), 'neutral')
        sign = '+' if pct > 0 else ''
        return (f'{sign}{pct}%', 'success' if pct > 0 else 'warn')

    sd, sdt = _delta(sales_a, sales_p)
    id_, idt = _delta(implant_a, implant_p)
    pd, pdt = _delta(proj_a, proj_p)
    cd, cdt = _delta(cust_a, cust_p)

    # target=0 表示"未设目标",模板灰色显示;不再 fallback 到 1
    # 列表契约:每项 {data:{label,value,target,unit}, tone, delta, deltaTone}(模板通用循环)
    return [
        {'data': {'label': f'{label_prefix}{_t("销售额")}', 'value': int(sales_a), 'target': int(sales_t), 'unit': currency_symbol},
         'tone': 'var(--accent)', 'delta': sd, 'deltaTone': sdt},
        {'data': {'label': f'{label_prefix}{_t("植入额")}', 'value': int(implant_a), 'target': int(implant_t), 'unit': currency_symbol},
         'tone': 'var(--success)', 'delta': id_, 'deltaTone': idt},
        {'data': {'label': f'{label_prefix}{_t("新项目")}', 'value': int(proj_a), 'target': int(proj_t), 'unit': ' 个'},
         'tone': 'var(--info)', 'delta': pd, 'deltaTone': pdt},
        {'data': {'label': f'{label_prefix}{_t("新客户")}', 'value': int(cust_a), 'target': int(cust_t), 'unit': ' 户'},
         'tone': 'var(--warn)', 'delta': cd, 'deltaTone': cdt},
    ]


def _kpi_task_items(user, start, end, prev_start, prev_end, label_prefix):
    """任务:完成 / 目标(本期指派) 合成一个指标(完成率),解决方案 + 产品经理共用。"""
    from sqlalchemy import func
    from app import db
    from app.models.task import Task

    # 「我的任务」口径:指派给我 OR 我协助(与任务模块一致)
    _mine = _my_task_filter(user)

    def _total(s, e):  # 目标=本期我的任务(非取消)
        return db.session.query(func.count(Task.id)).filter(
            _mine, Task.is_deleted == False, Task.status != 'cancelled',
            Task.created_at >= s, Task.created_at < e).scalar() or 0

    def _done(s, e):  # 完成=本期完成的我的任务
        return db.session.query(func.count(Task.id)).filter(
            _mine, Task.is_deleted == False,
            Task.status == 'completed', Task.completed_at >= s, Task.completed_at < e).scalar() or 0

    total = _total(start, end)
    done, done_p = _done(start, end), _done(prev_start, prev_end)
    # value=完成数, target=目标(总数) → 进度条显示完成率
    return [_kpi_item(f'{label_prefix}{_t("任务")}', done, total, ' 个', done_p, 'var(--accent)')]


def _kpi_metrics_solution(user, start, end, prev_start, prev_end, label_prefix, target_months, cur):
    """解决方案经理:按岗位方案五项渲染(与绩效配置同源)——
    报价确认 / 植入额 / 确认质量 / 销售支持 / 销售额;
    actual 口径照抄 performance_service 的 SE 统计 CTE(窗口参数化),
    target 来自新绩效配置框架(个人覆盖>角色默认)。未配置 → 空列表(KPI 未设定)。"""
    from sqlalchemy import text
    from app import db

    # 目标:金额/数量按窗口月份累加;质量(%)为水平目标取单月值
    try:
        from app.services.performance_dashboard_service import PerformanceDashboardService
        tmap = PerformanceDashboardService.get_user_kpi_targets(user.id, start.year)
    except Exception:
        tmap = {}
    if not tmap:
        return []
    tsum = {}
    for m in target_months:
        for k, v in (tmap.get(m) or {}).items():
            tsum[k] = tsum.get(k, 0) + float(v or 0)
    first_m = list(target_months)[0]
    quality_t = float((tmap.get(first_m) or {}).get('se_confirm_quality_target', 0) or 0)

    _SE_SQL = text("""
        WITH se_users AS (
            SELECT id FROM users WHERE role = 'solution_manager'
        ),
        collab AS (
            -- 每个 (项目, SE) 的确认数与总配合量(确认+系统设计+工作项+行动)
            SELECT project_id, se_id, SUM(cf) AS confirms, COUNT(*) AS vol
            FROM (
                SELECT project_id, confirmed_by AS se_id, 1 AS cf FROM quotations
                    WHERE confirmed_by IN (SELECT id FROM se_users)
                      AND project_id IS NOT NULL AND confirmed_at IS NOT NULL
                UNION ALL
                SELECT project_id, owner_id, 0 FROM system_diagrams
                    WHERE owner_id IN (SELECT id FROM se_users)
                      AND is_deleted = false AND project_id IS NOT NULL
                UNION ALL
                SELECT project_id, owner_id, 0 FROM work_items
                    WHERE owner_id IN (SELECT id FROM se_users) AND project_id IS NOT NULL
                UNION ALL
                SELECT project_id, owner_id, 0 FROM actions
                    WHERE owner_id IN (SELECT id FROM se_users) AND project_id IS NOT NULL
            ) parts
            GROUP BY project_id, se_id
        ),
        primary_se AS (
            -- 配合主方:确认数优先,其次总配合量,再次 se_id 最小(稳定唯一)
            SELECT DISTINCT ON (project_id) project_id, se_id
            FROM collab
            ORDER BY project_id, confirms DESC, vol DESC, se_id ASC
        ),
        se_projects AS (
            -- 仅「我作为配合主方」的项目计入植入额/批价额,避免共享项目重复计入
            SELECT project_id FROM primary_se WHERE se_id = :uid
        ),
        c AS (
            SELECT COUNT(*) AS cnt
            FROM quotations
            WHERE confirmed_by = :uid AND confirmed_at >= :s AND confirmed_at < :e
        ),
        spt AS (
            SELECT COUNT(DISTINCT pr.owner_id) AS sup
            FROM (
                SELECT sd.project_id FROM system_diagrams sd
                    WHERE sd.owner_id = :uid AND sd.is_deleted = false
                      AND sd.updated_at >= :s AND sd.updated_at < :e
                UNION
                SELECT q.project_id FROM quotations q
                    WHERE q.project_id IS NOT NULL
                      AND ( (q.owner_id = :uid AND q.created_at >= :s AND q.created_at < :e)
                         OR (q.confirmed_by = :uid AND q.confirmed_at >= :s AND q.confirmed_at < :e) )
            ) pp
            JOIN projects pr ON pp.project_id = pr.id
            WHERE pr.owner_id IS NOT NULL
        ),
        ql AS (
            -- 植入品质:本期确认报价单的"推荐产品系数和"平均(去重不看数量;无推荐产品=0)
            SELECT COALESCE(AVG(qs.qscore), 0) AS quality
            FROM (
                SELECT q.id, COALESCE(SUM(p.citation_coefficient), 0) AS qscore
                FROM quotations q
                LEFT JOIN (SELECT DISTINCT quotation_id, product_mn FROM quotation_details) dp ON dp.quotation_id = q.id
                LEFT JOIN products p ON p.product_mn = dp.product_mn AND p.citation_coefficient > 0
                WHERE q.confirmed_by = :uid AND q.confirmed_at >= :s AND q.confirmed_at < :e
                GROUP BY q.id
            ) qs
        ),
        im AS (
            SELECT COALESCE(SUM(qd.quantity * qd.market_price), 0) AS amt
            FROM quotation_details qd
            JOIN quotations q ON qd.quotation_id = q.id
            JOIN se_projects sp ON q.project_id = sp.project_id
            JOIN products p ON qd.product_mn = p.product_mn
            WHERE p.is_vendor_product = true AND q.created_at >= :s AND q.created_at < :e
        ),
        sa AS (
            SELECT COALESCE(SUM(po.pricing_total_amount), 0) AS amt
            FROM pricing_orders po
            JOIN se_projects sp ON po.project_id = sp.project_id
            WHERE po.status = 'approved' AND po.approved_at >= :s AND po.approved_at < :e
        )
        SELECT c.cnt, spt.sup AS sup, ql.quality, im.amt AS implant, sa.amt AS sales
        FROM c, spt, ql, im, sa
    """)

    def _win(s, e):
        r = db.session.execute(_SE_SQL, {'uid': user.id, 's': s, 'e': e}).fetchone()
        quality = round(float(r.quality or 0), 2)  # 植入品质(推荐系数加权均值)
        training = _act_hr_task_count(user, s, e, 'se_tech_training')  # 技术培训任务完成数
        return {'support': int(r.sup or 0), 'quality': quality,
                'implant': float(r.implant or 0), 'training': int(training or 0)}

    a, p = _win(start, end), _win(prev_start, prev_end)

    # 方案四项(顺序与岗位方案一致);target=0 视为该项未配置
    spec = [
        ('se_implant_amount_target',  f'{label_prefix}{_t("植入额")}',       a['implant'],  p['implant'],  cur,   'var(--success)'),
        ('se_confirm_quality_target', f'{label_prefix}{_t("植入品质")}',     a['quality'],  p['quality'],  ' 分', 'var(--info)'),
        ('se_sales_support_target',   f'{label_prefix}{_t("销售配合广度")}', a['support'],  p['support'],  ' 人', 'var(--warn)'),
        ('se_training_count_target',  f'{label_prefix}{_t("技术培训")}',     a['training'], p['training'], ' 次', 'var(--accent)'),
    ]
    from app.helpers.scoring_modes import tiered_achievement, TIERED_PASS, TIERED_GOOD
    items = []
    for key, label, val, prev, unit, tone in spec:
        if key == 'se_confirm_quality_target':
            # 植入品质:固定档位制,无数字目标;按均值给等级 + 达成率(及格3/良好5/优秀7)
            tier = (_t('优秀') if val >= 7 else _t('良好') if val >= TIERED_GOOD
                    else _t('及格') if val >= TIERED_PASS else _t('待提升'))
            t_tone = ('var(--success)' if val >= TIERED_GOOD
                      else 'var(--info)' if val >= TIERED_PASS else 'var(--warn)')
            items.append(_kpi_item(label, val, 0, unit, prev, t_tone, as_float=True,
                                   data_extra={'tier': tier, 'pct': round(tiered_achievement(val)),
                                               'pass': int(TIERED_PASS), 'good': int(TIERED_GOOD), 'excellent': 7}))
            continue
        target = tsum.get(key, 0)
        _keep_float = unit == '%'   # 率类保留小数,其余取整
        items.append(_kpi_item(label, val if _keep_float else int(val),
                               target if _keep_float else int(target), unit, prev, tone))
    return items


def _kpi_metrics_product(user, start, end, prev_start, prev_end, label_prefix, target_months, cur):
    """产品经理:任务 + 负责产品植入额(我管理分类下产品,按报价明细 implant_subtotal)。"""
    from sqlalchemy import func
    from app import db
    from app.models.quotation import Quotation, QuotationDetail
    from app.models.product import Product

    my_cat_ids = [c.id for c in getattr(user, 'managed_categories', [])]

    def _pm_implant(s, e):
        if not my_cat_ids:
            return 0
        return db.session.query(func.coalesce(func.sum(QuotationDetail.implant_subtotal), 0)).join(
            Quotation, Quotation.id == QuotationDetail.quotation_id).join(
            Product, Product.product_mn == QuotationDetail.product_mn).filter(
            Product.category_id.in_(my_cat_ids),
            Quotation.created_at >= s, Quotation.created_at < e).scalar() or 0

    im, imp = _pm_implant(start, end), _pm_implant(prev_start, prev_end)
    items = _kpi_task_items(user, start, end, prev_start, prev_end, label_prefix)
    items.append(_kpi_item(f'{label_prefix}{_t("负责产品植入额")}', im, 0, cur, imp, 'var(--info)'))
    return items


def _kpi_metrics_finance(user, start, end, prev_start, prev_end, label_prefix, target_months, cur):
    """财务:待审批报销数 + 本期报销总额 + 已支付 + 待支付(全公司)。"""
    from sqlalchemy import func
    from app import db
    from app.models.expense import Expense

    pending_cnt = db.session.query(func.count(Expense.id)).filter(
        Expense.is_deleted == False, Expense.status == 'pending').scalar() or 0

    def _claimed(s, e):  # 本期报销总额(非草稿,按创建期)
        return db.session.query(func.coalesce(func.sum(Expense.total_amount), 0)).filter(
            Expense.is_deleted == False, Expense.status != 'draft',
            Expense.created_at >= s, Expense.created_at < e).scalar() or 0

    def _paid(s, e):  # 本期已支付(按支付日期)
        return db.session.query(func.coalesce(
            func.sum(func.coalesce(Expense.payment_amount, Expense.total_amount)), 0)).filter(
            Expense.is_deleted == False, Expense.payment_status == 'paid',
            Expense.payment_date >= s, Expense.payment_date < e).scalar() or 0

    unpaid = db.session.query(func.coalesce(func.sum(Expense.total_amount), 0)).filter(
        Expense.is_deleted == False, Expense.status == 'approved',
        Expense.payment_status != 'paid').scalar() or 0

    cl, clp = _claimed(start, end), _claimed(prev_start, prev_end)
    pd_, pdp = _paid(start, end), _paid(prev_start, prev_end)
    return [
        _kpi_item(_t('待审批报销'), pending_cnt, 0, ' 单', 0, 'var(--accent)', delta=('—', 'neutral')),
        _kpi_item(f'{label_prefix}{_t("报销总额")}', cl, 0, cur, clp, 'var(--info)'),
        _kpi_item(f'{label_prefix}{_t("已支付")}', pd_, 0, cur, pdp, 'var(--success)'),
        _kpi_item(_t('待支付'), unpaid, 0, cur, 0, 'var(--warn)', delta=('—', 'neutral')),
    ]


# ─── 配置驱动 KPI 引擎 ───────────────────────────────────
# KPI 卡完全跟随绩效配置:有效考核项(岗位方案 > 个人配置行 > 角色默认行)有什么就渲染什么,
# 一项都没有 → 空列表 → 模板「KPI 未设定」占位。目标来自新框架(个人覆盖>角色默认)。

_KPI_TONES = ['var(--accent)', 'var(--success)', 'var(--info)', 'var(--warn)']

# metric_code → 实际值窗口查询;未注册的指标(快照/未定义口径)actual 显示 0 灰显
def _act_sales(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.pricing_order import PricingOrder
    return float(db.session.query(func.coalesce(func.sum(PricingOrder.pricing_total_amount), 0)).filter(
        PricingOrder.status == 'approved', PricingOrder.created_by == user.id,
        PricingOrder.approved_at >= s, PricingOrder.approved_at < e).scalar() or 0)

def _act_implant(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.quotation import Quotation
    return float(db.session.query(func.coalesce(func.sum(Quotation.implant_total_amount), 0)).filter(
        Quotation.owner_id == user.id,
        Quotation.created_at >= s, Quotation.created_at < e).scalar() or 0)

def _act_new_projects(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        Project.owner_id == user.id,
        Project.created_at >= s, Project.created_at < e).scalar() or 0

def _act_new_customers(user, s, e):
    # 新增客户 = 我名下(owner_id)本期新建的公司,不过滤类型
    # (companies 表无 created_by 列;旧口径 company_type=='customer' 在库里无此值恒为 0)
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.owner_id == user.id,
        Company.created_at >= s, Company.created_at < e).scalar() or 0

def _act_quotation_count(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.quotation import Quotation
    return db.session.query(func.count(Quotation.id)).filter(
        Quotation.owner_id == user.id,
        Quotation.created_at >= s, Quotation.created_at < e).scalar() or 0

def _act_pm_implant(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.quotation import Quotation, QuotationDetail
    from app.models.product import Product
    cat_ids = [c.id for c in getattr(user, 'managed_categories', [])]
    if not cat_ids:
        return 0
    return float(db.session.query(func.coalesce(func.sum(QuotationDetail.implant_subtotal), 0)).join(
        Quotation, Quotation.id == QuotationDetail.quotation_id).join(
        Product, Product.product_mn == QuotationDetail.product_mn).filter(
        Product.category_id.in_(cat_ids),
        Quotation.created_at >= s, Quotation.created_at < e).scalar() or 0)

# SE 五项:一次 SQL 出全窗口(口径照抄 performance_service SE CTE)
_SE_WINDOW_SQL = """
    WITH se_users AS (
        SELECT id FROM users WHERE role = 'solution_manager'
    ),
    collab AS (
        SELECT project_id, se_id, SUM(cf) AS confirms, COUNT(*) AS vol
        FROM (
            SELECT project_id, confirmed_by AS se_id, 1 AS cf FROM quotations
                WHERE confirmed_by IN (SELECT id FROM se_users)
                  AND project_id IS NOT NULL AND confirmed_at IS NOT NULL
            UNION ALL
            SELECT project_id, owner_id, 0 FROM system_diagrams
                WHERE owner_id IN (SELECT id FROM se_users)
                  AND is_deleted = false AND project_id IS NOT NULL
            UNION ALL
            SELECT project_id, owner_id, 0 FROM work_items
                WHERE owner_id IN (SELECT id FROM se_users) AND project_id IS NOT NULL
            UNION ALL
            SELECT project_id, owner_id, 0 FROM actions
                WHERE owner_id IN (SELECT id FROM se_users) AND project_id IS NOT NULL
        ) parts
        GROUP BY project_id, se_id
    ),
    primary_se AS (
        SELECT DISTINCT ON (project_id) project_id, se_id
        FROM collab
        ORDER BY project_id, confirms DESC, vol DESC, se_id ASC
    ),
    se_projects AS (
        -- 仅「我作为配合主方」的项目计入植入额/批价额,避免共享项目重复计入
        SELECT project_id FROM primary_se WHERE se_id = :uid
    ),
    c AS (
        SELECT COUNT(*) AS cnt
        FROM quotations
        WHERE confirmed_by = :uid AND confirmed_at >= :s AND confirmed_at < :e
    ),
    spt AS (
        -- 销售配合广度 项目参与=系统设计 + 报价制作/确认 触达的项目,项目 owner 去重
        SELECT COUNT(DISTINCT pr.owner_id) AS sup
        FROM (
            SELECT sd.project_id FROM system_diagrams sd
                WHERE sd.owner_id = :uid AND sd.is_deleted = false
                  AND sd.updated_at >= :s AND sd.updated_at < :e
            UNION
            SELECT q.project_id FROM quotations q
                WHERE q.project_id IS NOT NULL
                  AND ( (q.owner_id = :uid AND q.created_at >= :s AND q.created_at < :e)
                     OR (q.confirmed_by = :uid AND q.confirmed_at >= :s AND q.confirmed_at < :e) )
        ) pp
        JOIN projects pr ON pp.project_id = pr.id
        WHERE pr.owner_id IS NOT NULL
    ),
    ql AS (
        -- 植入品质:本期该 SE 确认的报价单,每单 = 出现过的"推荐产品"系数之和(去重,不看数量),
        -- 取所有确认报价的平均(无推荐产品的单计 0)。citation_coefficient>0 才计。
        SELECT COALESCE(AVG(qs.qscore), 0) AS quality
        FROM (
            SELECT q.id, COALESCE(SUM(p.citation_coefficient), 0) AS qscore
            FROM quotations q
            LEFT JOIN (SELECT DISTINCT quotation_id, product_mn FROM quotation_details) dp ON dp.quotation_id = q.id
            LEFT JOIN products p ON p.product_mn = dp.product_mn AND p.citation_coefficient > 0
            WHERE q.confirmed_by = :uid AND q.confirmed_at >= :s AND q.confirmed_at < :e
            GROUP BY q.id
        ) qs
    ),
    im AS (
        SELECT COALESCE(SUM(qd.quantity * qd.market_price), 0) AS amt
        FROM quotation_details qd
        JOIN quotations q ON qd.quotation_id = q.id
        JOIN se_projects sp ON q.project_id = sp.project_id
        JOIN products p ON qd.product_mn = p.product_mn
        WHERE p.is_vendor_product = true AND q.created_at >= :s AND q.created_at < :e
    ),
    sa AS (
        SELECT COALESCE(SUM(po.pricing_total_amount), 0) AS amt
        FROM pricing_orders po
        JOIN se_projects sp ON po.project_id = sp.project_id
        WHERE po.status = 'approved' AND po.approved_at >= :s AND po.approved_at < :e
    )
    SELECT c.cnt, spt.sup AS sup, ql.quality, im.amt AS implant, sa.amt AS sales
    FROM c, spt, ql, im, sa
"""

def _se_window(user, s, e, _cache={}):
    from sqlalchemy import text
    from app import db
    key = (user.id, s, e)
    if key not in _cache:
        r = db.session.execute(text(_SE_WINDOW_SQL), {'uid': user.id, 's': s, 'e': e}).fetchone()
        _cache.clear() if len(_cache) > 64 else None
        _cache[key] = {
            'se_confirm_count': int(r.cnt or 0),
            'se_sales_support': int(r.sup or 0),
            'se_confirm_quality': round(float(r.quality or 0), 2),  # 植入品质(推荐系数加权均值)
            'se_implant_amount': float(r.implant or 0),
            'se_sales_amount': float(r.sales or 0),
        }
    return _cache[key]

def _act_se(code):
    return lambda user, s, e: _se_window(user, s, e)[code]

def _act_manual(code, agg='sum'):
    """手工录入指标(培训次数/内容产出/研发达成/批次质量等):窗口内按月聚合。
    月度记录优先;该季度无任何月度记录时回退季度记录(sum 按 1/3 折算到月,avg 取原值),
    与录入侧「季考行存季度记录、月考行存月记录」对应。"""
    def fn(user, s, e):
        from app.models.performance_manual_entry import PerformanceManualEntry
        years = {s.year, (e - timedelta(days=1)).year}
        ents = PerformanceManualEntry.query.filter(
            PerformanceManualEntry.user_id == user.id,
            PerformanceManualEntry.metric_code == code,
            PerformanceManualEntry.year.in_(years),
        ).all()
        monthly = {(x.year, x.period): float(x.value)
                   for x in ents if x.period_type == 'monthly' and x.value is not None}
        quarterly = {(x.year, x.period): float(x.value)
                     for x in ents if x.period_type == 'quarterly' and x.value is not None}
        q_has_monthly = {(y, (m - 1) // 3 + 1) for (y, m) in monthly}
        vals = []
        d = s
        while d < e:
            q = (d.month - 1) // 3 + 1
            if (d.year, d.month) in monthly:
                vals.append(monthly[(d.year, d.month)])
            elif (d.year, q) in quarterly and (d.year, q) not in q_has_monthly:
                qv = quarterly[(d.year, q)]
                vals.append(qv if agg == 'avg' else qv / 3.0)
            d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        if not vals:
            return 0
        return round(sum(vals) / len(vals), 1) if agg == 'avg' else round(sum(vals), 2)
    return fn

def _act_project_activity(team=False):
    """项目活跃度%(快照型,窗口无关):
    负责(owner/厂商销售)的项目,排除 签约/暂停/失败,跟进未超 20 天的占比。
    team=True(营销总监):范围扩为本部门成员(含本人)负责的项目。
    口径与待办分级跟进提醒/列表未跟进标识完全一致。"""
    def fn(user, s, e):
        from sqlalchemy import func, or_
        from datetime import datetime as _dt, date as _date
        from app import db
        from app.models.project import Project
        from app.models.action import Action
        from app.models.projectpm_stage_history import ProjectStageHistory
        from app.models.user import User as _U
        _EXCL = ('signed', 'paused', 'lost')
        if team and user.department:
            ids = [u.id for u in _U.query.filter(
                _U.department == user.department,
                _U.company_name == user.company_name).all()] or [user.id]
        else:
            ids = [user.id]
        projs = Project.query.filter(
            Project.is_deleted == False,
            ~Project.current_stage.in_(_EXCL),
            or_(Project.owner_id.in_(ids),
                Project.vendor_sales_manager_id.in_(ids))).all()
        if not projs:
            return 100.0
        pids = [p.id for p in projs]
        last_act = dict(db.session.query(Action.project_id, func.max(Action.date))
                        .filter(Action.project_id.in_(pids)).group_by(Action.project_id).all())
        no_act = [pid for pid in pids if pid not in last_act]
        since = {}
        if no_act:
            since = dict(db.session.query(ProjectStageHistory.project_id,
                                          func.max(ProjectStageHistory.change_date))
                         .filter(ProjectStageHistory.project_id.in_(no_act))
                         .group_by(ProjectStageHistory.project_id).all())
        today, now = _date.today(), _dt.now()
        overdue = 0
        for p_ in projs:
            ld = last_act.get(p_.id)
            if ld:
                days = (today - ld).days
            else:
                b = since.get(p_.id) or p_.created_at
                days = (now - b).days if b else 0
            if days >= 20:
                overdue += 1
        return round((1 - overdue / len(projs)) * 100, 1)
    return fn


_KPI_ACTUAL_FNS = {
    'sales_amount':       _act_sales,
    'implant_amount':     _act_implant,
    'new_projects':       _act_new_projects,
    'new_customers':      _act_new_customers,
    'quotation_count':    _act_quotation_count,
    'pm_implant_amount':  _act_pm_implant,
    'se_confirm_count':   _act_se('se_confirm_count'),
    'se_sales_support':   _act_se('se_sales_support'),
    'se_confirm_quality': _act_se('se_confirm_quality'),
    'se_implant_amount':  _act_se('se_implant_amount'),
    'se_sales_amount':    _act_se('se_sales_amount'),
    'se_training_count':  lambda u, s, e: _act_hr_task_count(u, s, e, 'se_tech_training'),  # 技术培训:任务完成计数
    'se_content_output':  _act_manual('se_content_output'),
    'se_response_rate':   _act_manual('se_response_rate', agg='avg'),
    'se_satisfaction':    _act_manual('se_satisfaction', agg='avg'),
    'customer_activity_rate':     None,   # 下方注册(快照型)
    'project_activity_rate':      _act_project_activity(team=False),
    'team_project_activity_rate': _act_project_activity(team=True),
    # 研发计划达成/质量处理:完成且审核通过的研发/质量任务计数(达成率=完成÷目标)
    'pm_dev_rate':        lambda u, s, e: _act_task_count_reviewed(u, s, e, 'pm_rd'),
    'pm_quality_rate':    lambda u, s, e: _act_task_count_reviewed(u, s, e, 'pm_quality'),
    # 上市支持:完成且审核通过的上市支持任务,按三档评价加权求和
    'pm_support_count':   lambda u, s, e: _act_task_count_reviewed(u, s, e, 'pm_launch_support'),
    'pm_new_launch':      None,   # 下方注册(自动)
    'pm_sales_amount':    None,   # 占位,下方注册(需 SQL)
    # 未注册(快照/口径未定):customer_activity_rate / high_price_amount → actual 0
}

def _act_pm_sales(user, s, e):
    """产品批价额:我(产品 owner 或分类负责人)名下厂商产品的已批价明细金额
    —— 口径照抄 performance_service.calculate_pm_yearly_statistics_batch 的 pm_sales CTE"""
    from sqlalchemy import text
    from app import db
    r = db.session.execute(text("""
        WITH product_pm AS (
            SELECT p.product_mn,
                   CASE WHEN u_owner.role = 'product_manager' THEN p.owner_id
                        WHEN u_cat_mgr.role = 'product_manager' THEN pc.manager_id
                        ELSE NULL END AS pm_id
            FROM products p
            LEFT JOIN users u_owner ON p.owner_id = u_owner.id
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN users u_cat_mgr ON pc.manager_id = u_cat_mgr.id
            WHERE p.is_vendor_product = true
        )
        SELECT COALESCE(SUM(pod.total_price), 0) AS amt
        FROM pricing_order_details pod
        JOIN pricing_orders po ON pod.pricing_order_id = po.id
        JOIN product_pm pp ON pod.product_mn = pp.product_mn
        WHERE pp.pm_id = :uid AND po.status = 'approved'
          AND po.approved_at >= :s AND po.approved_at < :e
    """), {'uid': user.id, 's': s, 'e': e}).fetchone()
    return float(r.amt or 0)

_KPI_ACTUAL_FNS['pm_sales_amount'] = _act_pm_sales


def _act_pm_new_launch(user, s, e):
    """新品上市:负责范围(产品归属人/分类负责人)本期新建的在产厂商产品数"""
    from sqlalchemy import func, or_, text
    from app import db
    r = db.session.execute(text("""
        SELECT COUNT(*) FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE p.is_vendor_product = true AND p.status = 'active'
          AND p.created_at >= :s AND p.created_at < :e
          AND (p.owner_id = :uid OR pc.manager_id = :uid)
    """), {'uid': user.id, 's': s, 'e': e}).scalar()
    return int(r or 0)


_KPI_ACTUAL_FNS['pm_new_launch'] = _act_pm_new_launch


def _act_customer_activity(user, s, e):
    """客户活跃度%(快照型,窗口无关):
    我名下未删除客户中,状态为 高度活跃/活跃/正常 的占比
    (companies.status 由每日 01:00 活跃度跑批维护;待跟进/沉睡/流失 计为不活跃)"""
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    rows = dict(db.session.query(Company.status, func.count(Company.id))
                .filter(Company.owner_id == user.id, Company.is_deleted == False)
                .group_by(Company.status).all())
    total = sum(rows.values())
    if not total:
        return 100.0
    active = sum(v for k, v in rows.items() if k in ('highly_active', 'active', 'normal'))
    return round(active / total * 100, 1)


_KPI_ACTUAL_FNS['customer_activity_rate'] = _act_customer_activity


def _dept_member_ids(user):
    """团队 = 本部门成员(含本人,同公司)"""
    from app.models.user import User as _U
    if not user.department:
        return [user.id]
    return [u.id for u in _U.query.filter(
        _U.department == user.department,
        _U.company_name == user.company_name).all()] or [user.id]


def _act_team_sales(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.pricing_order import PricingOrder
    return float(db.session.query(func.coalesce(func.sum(PricingOrder.pricing_total_amount), 0)).filter(
        PricingOrder.status == 'approved',
        PricingOrder.created_by.in_(_dept_member_ids(user)),
        PricingOrder.approved_at >= s, PricingOrder.approved_at < e).scalar() or 0)


def _act_team_implant(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.quotation import Quotation
    return float(db.session.query(func.coalesce(func.sum(Quotation.implant_total_amount), 0)).filter(
        Quotation.owner_id.in_(_dept_member_ids(user)),
        Quotation.created_at >= s, Quotation.created_at < e).scalar() or 0)


def _act_team_new_projects(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        Project.owner_id.in_(_dept_member_ids(user)),
        Project.created_at >= s, Project.created_at < e).scalar() or 0


def _act_team_new_customers(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.owner_id.in_(_dept_member_ids(user)),
        Company.created_at >= s, Company.created_at < e).scalar() or 0


def _act_team_customer_activity(user, s, e):
    """团队客户活跃度%(快照):部门成员名下客户中 高活/活跃/正常 占比"""
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    rows = dict(db.session.query(Company.status, func.count(Company.id))
                .filter(Company.owner_id.in_(_dept_member_ids(user)), Company.is_deleted == False)
                .group_by(Company.status).all())
    total = sum(rows.values())
    if not total:
        return 100.0
    active = sum(v for k, v in rows.items() if k in ('highly_active', 'active', 'normal'))
    return round(active / total * 100, 1)


def _lost_this_year_ids(year):
    """当年进入失败阶段的项目 id 集合(阶段历史 to_stage='lost' 当年)"""
    from sqlalchemy import extract
    from app import db
    from app.models.projectpm_stage_history import ProjectStageHistory
    rows = db.session.query(ProjectStageHistory.project_id).filter(
        ProjectStageHistory.to_stage == 'lost',
        extract('year', ProjectStageHistory.change_date) == year).distinct().all()
    return {r[0] for r in rows}


def _act_fail_rate(user, s, e):
    """个人失败率%(反向,≤目标达标):
    当年被认定「个人因素为主」的失败项目数 ÷ 本人负责(负责人/厂商销售)的项目总数"""
    from sqlalchemy import or_
    from app.models.project import Project
    mine = Project.query.filter(
        Project.is_deleted == False,
        or_(Project.owner_id == user.id, Project.vendor_sales_manager_id == user.id)).all()
    if not mine:
        return 0.0
    lost_ids = _lost_this_year_ids(s.year)
    fault = sum(1 for p_ in mine
                if p_.id in lost_ids and getattr(p_, 'fail_owner_fault', False))
    return round(fault / len(mine) * 100, 1)


def _act_team_fail_rate(user, s, e):
    """团队失败率%(反向,≤目标达标):
    当年被认定「团队管理失责」的失败数 ÷ 本部门当年失败项目总数"""
    from sqlalchemy import or_
    from app.models.project import Project
    ids = _dept_member_ids(user)
    lost_ids = _lost_this_year_ids(s.year)
    if not lost_ids:
        return 0.0
    dept_lost = Project.query.filter(
        Project.id.in_(list(lost_ids)),
        or_(Project.owner_id.in_(ids), Project.vendor_sales_manager_id.in_(ids))).all()
    if not dept_lost:
        return 0.0
    fault = sum(1 for p_ in dept_lost if getattr(p_, 'fail_mgmt_fault', False))
    return round(fault / len(dept_lost) * 100, 1)


# ── 渠道口径(全量 report_source/source='channel',不限负责人)──
def _channel_project_filter():
    from app.models.project import Project
    return [Project.is_deleted == False, Project.report_source == 'channel']


def _act_channel_sales(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.pricing_order import PricingOrder
    from app.models.project import Project
    return float(db.session.query(func.coalesce(func.sum(PricingOrder.pricing_total_amount), 0))
                 .join(Project, Project.id == PricingOrder.project_id)
                 .filter(*_channel_project_filter(),
                         PricingOrder.status == 'approved',
                         PricingOrder.approved_at >= s, PricingOrder.approved_at < e).scalar() or 0)


def _act_channel_implant(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.quotation import Quotation
    from app.models.project import Project
    return float(db.session.query(func.coalesce(func.sum(Quotation.implant_total_amount), 0))
                 .join(Project, Project.id == Quotation.project_id)
                 .filter(*_channel_project_filter(),
                         Quotation.created_at >= s, Quotation.created_at < e).scalar() or 0)


def _act_channel_new_projects(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        *_channel_project_filter(),
        Project.created_at >= s, Project.created_at < e).scalar() or 0


def _dealer_user_ids():
    """渠道客户维度的口径主体:代理商(dealer)账户"""
    from app.models.user import User as _U
    return [u.id for u in _U.query.filter(_U.role == 'dealer').all()] or [0]


def _act_channel_new_customers(user, s, e):
    # 渠道新增客户 = 代理商账户名下本期新建的客户(客户不分渠道,按创建账户归属)
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.is_deleted == False, Company.owner_id.in_(_dealer_user_ids()),
        Company.created_at >= s, Company.created_at < e).scalar() or 0


def _act_channel_customer_activity(user, s, e):
    # 渠道客户活跃度 = 代理商账户名下客户中 高活/活跃/正常 占比(快照)
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    rows = dict(db.session.query(Company.status, func.count(Company.id))
                .filter(Company.is_deleted == False, Company.owner_id.in_(_dealer_user_ids()))
                .group_by(Company.status).all())
    total = sum(rows.values())
    if not total:
        return 100.0
    active = sum(v for k, v in rows.items() if k in ('highly_active', 'active', 'normal'))
    return round(active / total * 100, 1)


def _act_channel_project_activity(user, s, e):
    """渠道项目活跃度%(快照):渠道项目(排除签约/暂停/失败)跟进未超 20 天占比"""
    from sqlalchemy import func
    from datetime import datetime as _dt, date as _date
    from app import db
    from app.models.project import Project
    from app.models.action import Action
    from app.models.projectpm_stage_history import ProjectStageHistory
    projs = Project.query.filter(*_channel_project_filter(),
                                 ~Project.current_stage.in_(('signed', 'paused', 'lost'))).all()
    if not projs:
        return 100.0
    pids = [p_.id for p_ in projs]
    last_act = dict(db.session.query(Action.project_id, func.max(Action.date))
                    .filter(Action.project_id.in_(pids)).group_by(Action.project_id).all())
    no_act = [pid for pid in pids if pid not in last_act]
    since = {}
    if no_act:
        since = dict(db.session.query(ProjectStageHistory.project_id,
                                      func.max(ProjectStageHistory.change_date))
                     .filter(ProjectStageHistory.project_id.in_(no_act))
                     .group_by(ProjectStageHistory.project_id).all())
    today, now = _date.today(), _dt.now()
    overdue = 0
    for p_ in projs:
        ld = last_act.get(p_.id)
        days = (today - ld).days if ld else ((now - (since.get(p_.id) or p_.created_at)).days
                                             if (since.get(p_.id) or p_.created_at) else 0)
        if days >= 20:
            overdue += 1
    return round((1 - overdue / len(projs)) * 100, 1)


def _act_channel_fail_rate(user, s, e):
    """渠道失败率%(反向):当年失败的渠道项目 ÷ 渠道项目总数"""
    from app.models.project import Project
    total = Project.query.filter(*_channel_project_filter()).count()
    if not total:
        return 0.0
    lost_ids = _lost_this_year_ids(s.year)
    if not lost_ids:
        return 0.0
    lost_channel = Project.query.filter(*_channel_project_filter(),
                                        Project.id.in_(list(lost_ids))).count()
    return round(lost_channel / total * 100, 1)


def _act_channel_new_dealers(user, s, e):
    """渠道发展:本期新增的代理商/分销商客户数(company_type=dealer/distributor)"""
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.is_deleted == False,
        Company.company_type.in_(('dealer', 'distributor')),
        Company.created_at >= s, Company.created_at < e).scalar() or 0


def _act_team_pass_rate(user, s, e):
    """团队绩效合格率%(正向):HRBP(user)负责部门中【有考核成员】当季绩效得分 ≥ 60 的占比。
    成员得分复用 PerformanceDashboardService.get_quarterly_scores;按请求(flask.g)缓存避免重复计算。"""
    from flask import g
    from app.helpers.hrbp_helpers import hrbp_department_keys
    from app.models.user import User as _U
    from app.services.performance_dashboard_service import PerformanceDashboardService as _PDS
    PASS_LINE = 60.0
    year = s.year
    try:
        cache = g._team_pass_cache
    except Exception:
        cache = {}
        try:
            g._team_pass_cache = cache
        except Exception:
            pass
    key = (user.id, year)
    if key not in cache:
        member_ids = set()
        for name, comp in hrbp_department_keys(user):
            for m in _U.query.filter(_U.department == name, _U.company_name == comp,
                                     _U._is_active.is_(True), _U.id != user.id).all():
                member_ids.add(m.id)
        num = {1: 0, 2: 0, 3: 0, 4: 0}
        den = {1: 0, 2: 0, 3: 0, 4: 0}
        for mid in member_ids:
            sc = _PDS.get_quarterly_scores(mid, year) or {}
            for q in (1, 2, 3, 4):
                qd = sc.get('Q%d' % q)
                tw = (qd.get('total_weight') or 0) if qd else 0
                if tw <= 0:
                    continue   # 无考核(无计入权重)→ 不计入分母
                den[q] += 1
                # 按计入权重归一为 0-100(与前端口径一致),再判合格线
                score = (qd.get('total_score') or 0) / tw * 100
                if score >= PASS_LINE:
                    num[q] += 1
        rates = {q: (round(num[q] / den[q] * 100, 1) if den[q] else 0.0) for q in (1, 2, 3, 4)}
        valid = [rates[q] for q in (1, 2, 3, 4) if den[q]]
        rates['y'] = round(sum(valid) / len(valid), 1) if valid else 0.0
        cache[key] = rates
    rates = cache[key]
    span = (e.year - s.year) * 12 + (e.month - s.month)
    if span >= 12:
        return rates['y']
    return rates[(s.month - 1) // 3 + 1]


def _act_hr_recruit_count(user, s, e):
    """招聘到岗:本人(assignee)审核通过的 hr_recruit 任务,按三档评价加权求和。"""
    return _act_task_count_reviewed(user, s, e, 'hr_recruit')


def _act_hr_training_count(user, s, e):
    """培训组织次数:本人(assignee)已完成的 hr_training 任务,按 completed_at 落窗口(不需审核)。"""
    from app.models.task import Task
    return Task.query.filter(
        Task.assignee_id == user.id,
        Task.task_type == 'hr_training',
        Task.status == 'completed',
        Task.is_deleted == False,
        Task.completed_at.isnot(None),
        Task.completed_at >= s,
        Task.completed_at < e,
    ).count()


def _act_hr_task_count(user, s, e, _task_type):
    """通用:本人(assignee)已完成的某类任务计数(完成即计)。"""
    from app.models.task import Task
    return Task.query.filter(
        Task.assignee_id == user.id,
        Task.task_type == _task_type,
        Task.status == 'completed',
        Task.is_deleted == False,
        Task.completed_at.isnot(None),
        Task.completed_at >= s,
        Task.completed_at < e,
    ).count()


def _act_task_count_reviewed(user, s, e, _task_type):
    """通用:本人(assignee)完成且审核通过的某类任务,按三档评价加权求和。
    review_score: 低于预期0.5/符合1/超出1.5;旧数据无评价兜底 1.0。"""
    from sqlalchemy import func
    from app.models.task import Task
    total = Task.query.with_entities(
        func.coalesce(func.sum(func.coalesce(Task.review_score, 1.0)), 0.0)
    ).filter(
        Task.assignee_id == user.id,
        Task.task_type == _task_type,
        Task.review_status == 'approved',
        Task.is_deleted == False,
        Task.completed_at.isnot(None),
        Task.completed_at >= s,
        Task.completed_at < e,
    ).scalar()
    return round(float(total or 0), 2)


def _act_hr_team_build_count(user, s, e):
    """团队建设次数:hr_team_build 任务完成数。"""
    return _act_hr_task_count(user, s, e, 'hr_team_build')


def _act_hr_admin_count(user, s, e):
    """行政/合规事务次数:hr_admin 任务完成数。"""
    return _act_hr_task_count(user, s, e, 'hr_admin')


_KPI_ACTUAL_FNS.update({
    'team_pass_rate':                 _act_team_pass_rate,
    'hr_recruit_count':               _act_hr_recruit_count,
    'hr_training_count':              _act_hr_training_count,
    'hr_team_build_count':            _act_hr_team_build_count,
    'hr_admin_count':                 _act_hr_admin_count,
    'channel_new_dealers':            _act_channel_new_dealers,
    'channel_sales_amount':           _act_channel_sales,
    'channel_implant_amount':         _act_channel_implant,
    'channel_new_projects':           _act_channel_new_projects,
    'channel_new_customers':          _act_channel_new_customers,
    'channel_customer_activity_rate': _act_channel_customer_activity,
    'channel_project_activity_rate':  _act_channel_project_activity,
    'channel_fail_rate':              _act_channel_fail_rate,
    'fail_rate':                   _act_fail_rate,
    'team_fail_rate':              _act_team_fail_rate,
    'team_sales_amount':           _act_team_sales,
    'team_implant_amount':         _act_team_implant,
    'team_new_projects':           _act_team_new_projects,
    'team_new_customers':          _act_team_new_customers,
    'team_customer_activity_rate': _act_team_customer_activity,
})

# 率/评分类:目标为水平值(取单月,不累加);actual 同理由查询口径保证
_KPI_RATE_CODES = {'customer_activity_rate', 'se_response_rate', 'se_confirm_quality', 'se_satisfaction',
                   'project_activity_rate', 'team_project_activity_rate', 'team_customer_activity_rate',
                   'team_pass_rate',
                   'fail_rate', 'team_fail_rate',
                   'channel_customer_activity_rate', 'channel_project_activity_rate', 'channel_fail_rate'}


def _kpi_config_driven(user, start, end, prev_start, prev_end, label_prefix, target_months, cur):
    """配置驱动 KPI:渲染该用户有效考核项(方案>个人行>角色默认行),目标走新框架。"""
    from app.services.performance_dashboard_service import PerformanceDashboardService

    year = start.year
    # 1) 考核项集合(方案角色=方案;否则个人配置行;再否则回退角色默认行)
    try:
        codes = PerformanceDashboardService._get_configured_performance_items(user.id, year) or []
    except Exception:
        codes = []
    if not codes and user.role:
        try:
            from app.models.performance_config import RolePerformanceTarget
            rows = RolePerformanceTarget.query.filter_by(role_code=user.role, year=year).all()
            mapping = {'sales_target': 'sales_amount'}
            codes = [mapping.get(r.item_code, r.item_code) for r in rows
                     if getattr(r, 'enabled', True) is not False]
        except Exception:
            pass
    if not codes:
        return []          # → 模板「KPI 未设定」

    # 2) 目标(个人覆盖>角色默认;金额已转元)
    try:
        tmap = PerformanceDashboardService.get_user_kpi_targets(user.id, year) or {}
    except Exception:
        tmap = {}
    first_m = list(target_months)[0]

    # 非方案角色:只认「目标有值」的项 — 勾了项但目标全空的遗留行不算配置;
    # 全部无值 → 占位「KPI 未设定」(方案角色考核项写死,始终全显)
    try:
        from app.services.role_kpi_schemes import get_role_scheme_codes
        is_scheme = bool(get_role_scheme_codes(user.role)) if user.role else False
    except Exception:
        is_scheme = False
    if not is_scheme:
        def _has_target(code):
            tkey = f'{code}_target'
            return any(float((tmap.get(m) or {}).get(tkey, 0) or 0) > 0 for m in range(1, 13))
        codes = [c for c in codes if _has_target(c)]
        if not codes:
            return []

    # 3) 指标定义(名称/单位/计分方式)
    name_map, unit_map, dtype_map, smode_map = {}, {}, {}, {}
    _ALIAS = {'sales_target': 'sales_amount'}   # 定义表 code → 看板 code
    try:
        from app.models.performance_config import PerformanceMetricsDefinition
        for m in PerformanceMetricsDefinition.query.all():
            for key in {m.metric_code, _ALIAS.get(m.metric_code, m.metric_code)}:
                name_map[key] = m.metric_name
                unit_map[key] = m.default_unit or ''
                dtype_map[key] = m.data_type or ''
                smode_map[key] = getattr(m, 'scoring_mode', None)
    except Exception:
        pass
    from app.helpers.scoring_modes import (
        default_scoring_mode as _dsmode, tiered_achievement as _tach,
        TIERED_PASS as _TP, TIERED_GOOD as _TG)
    _UNIT_DISPLAY = {'%': '%', '个': ' 个', '人': ' 人', '次': ' 次', '份': ' 份',
                     '分': ' 分', '单': ' 单', '户': ' 户'}

    items = []
    for idx, code in enumerate(codes):
        tkey = f'{code}_target'
        if code in _KPI_RATE_CODES:
            target = float((tmap.get(first_m) or {}).get(tkey, 0) or 0)
        else:
            target = sum(float((tmap.get(m) or {}).get(tkey, 0) or 0) for m in target_months)

        fn = _KPI_ACTUAL_FNS.get(code)
        val = fn(user, start, end) if fn else 0
        prev = fn(user, prev_start, prev_end) if fn else 0

        raw_unit = unit_map.get(code, '')
        dtype = dtype_map.get(code, '')
        if raw_unit in _UNIT_DISPLAY:
            unit = _UNIT_DISPLAY[raw_unit]
        elif dtype == 'amount':
            unit = cur
        elif dtype == 'percentage':
            unit = '%'
        elif dtype == 'count':
            unit = ' 个'
        elif dtype == 'score':
            unit = ' 分'
        else:
            unit = cur if raw_unit in ('', '元', '万元') else f' {raw_unit}'
        label = f"{label_prefix}{name_map.get(code, code)}"
        # 固定档位制(植入品质):无数字目标,按均值给等级 + 档位达成率(及格3/良好5/优秀7)
        smode = smode_map.get(code) or _dsmode(code)
        if smode == 'tiered':
            tier = (_t('优秀') if val >= 7 else _t('良好') if val >= _TG
                    else _t('及格') if val >= _TP else _t('待提升'))
            t_tone = ('var(--success)' if val >= _TG
                      else 'var(--info)' if val >= _TP else 'var(--warn)')
            items.append(_kpi_item(label, val, 0, unit, prev, t_tone, as_float=True,
                                   data_extra={'tier': tier, 'pct': round(_tach(val)),
                                               'pass': int(_TP), 'good': int(_TG), 'excellent': 7}))
            continue
        is_pct = (unit == '%')
        items.append(_kpi_item(label,
                               val if is_pct else int(val),
                               target if is_pct else int(target),
                               unit, prev, _KPI_TONES[idx % len(_KPI_TONES)]))
    return items


_KPI_VARIANT_FUNC = {
    'default':  _kpi_config_driven,
    'overview': _kpi_config_driven,
    'solution': _kpi_config_driven,
    'product':  _kpi_config_driven,
    'finance':  _kpi_config_driven,     # 财务同样配置驱动:未配置 → KPI 未设定
}


def _build_kpis(user, currency_symbol='¥', variant='default'):
    """返回 3 套粒度: month / quarter / year(前端 tab 切换),按 variant 分流指标集。"""
    from datetime import datetime
    now = datetime.now()
    y, m = now.year, now.month

    # ── 月 ──
    month_start = datetime(y, m, 1)
    if m == 12: month_end = datetime(y + 1, 1, 1)
    else:       month_end = datetime(y, m + 1, 1)
    if m > 1:   prev_m_start, prev_m_end = datetime(y, m - 1, 1), month_start
    else:       prev_m_start, prev_m_end = datetime(y - 1, 12, 1), month_start

    # ── 季 ──
    q = (m - 1) // 3 + 1
    q_start_m = (q - 1) * 3 + 1
    q_end_m   = q_start_m + 3   # 3 个月后,可能 > 12
    quarter_start = datetime(y, q_start_m, 1)
    if q_end_m > 12: quarter_end = datetime(y + 1, q_end_m - 12, 1)
    else:            quarter_end = datetime(y, q_end_m, 1)
    if q > 1:
        prev_q_start = datetime(y, q_start_m - 3, 1)
        prev_q_end   = quarter_start
    else:
        prev_q_start = datetime(y - 1, 10, 1)
        prev_q_end   = quarter_start
    quarter_months = list(range(q_start_m, q_end_m if q_end_m <= 12 else 13))

    # ── 年 ──
    year_start = datetime(y, 1, 1)
    year_end   = datetime(y + 1, 1, 1)
    prev_y_start = datetime(y - 1, 1, 1)
    prev_y_end   = year_start

    fn = _KPI_VARIANT_FUNC.get(variant, _kpi_config_driven)
    return {
        'month':   fn(user, month_start, month_end, prev_m_start, prev_m_end,
                      _t('%(m)s月', m=m), [m], currency_symbol),
        'quarter': fn(user, quarter_start, quarter_end, prev_q_start, prev_q_end,
                      'Q%s ' % q, quarter_months, currency_symbol),
        'year':    fn(user, year_start, year_end, prev_y_start, prev_y_end,
                      _t('%(y)s年 ', y=y), list(range(1, 13)), currency_symbol),
    }


def _build_today_stats(user):
    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    out = {'newCust': 0, 'newQuote': 0, 'newAction': 0, 'newOrder': 0}
    try:
        from app.models.company import Company
        out['newCust'] = Company.query.filter(Company.is_deleted == False, Company.created_at >= today_start).count()
    except Exception: pass
    try:
        from app.models.quotation import Quotation
        out['newQuote'] = Quotation.query.filter(Quotation.created_at >= today_start).count()
    except Exception: pass
    try:
        from app.models.action import Action
        out['newAction'] = Action.query.filter(Action.owner_id == user.id, Action.created_at >= today_start).count()
    except Exception: pass
    try:
        from app.models.sales_order import SalesOrder
        out['newOrder'] = SalesOrder.query.filter(SalesOrder.created_at >= today_start).count()
    except Exception: pass
    return out


# ─── 销售漏斗 ─── 我的项目(近 12 月)5 阶段聚合 + 流失统计
def _build_funnel(user, scope_filter=None):
    """
    数据源:Project + 关联 Quotation 植入额,近 12 个月。
    scope_filter: SQLAlchemy 过滤子句,由 build_dashboard 按"我的/可见范围"传入
                  (我的=owner==user;可见=get_viewable_data 的 id 集合,含权限级别+归属+共享+content_filters)
    """
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from app import db
    from app.models.project import Project
    from app.models.quotation import Quotation

    cutoff = datetime.now() - timedelta(days=365)

    # 我的项目按 stage 分组 + 关联报价植入额聚合
    q = db.session.query(
        Project.current_stage,
        func.count(Project.id.distinct()).label('cnt'),
        func.coalesce(func.sum(Quotation.implant_total_amount), 0).label('amt'),
    ).outerjoin(
        Quotation, Quotation.project_id == Project.id
    ).filter(
        Project.created_at >= cutoff,
    )
    if scope_filter is not None:
        q = q.filter(scope_filter)
    rows = q.group_by(Project.current_stage).all()

    stage_data = {r.current_stage: {'count': int(r.cnt or 0), 'amount': float(r.amt or 0)} for r in rows}

    # 锁定成功(锁单预判)按阶段计数 — 同 scope,签约阶段已自动解除不会出现
    lq = db.session.query(Project.current_stage, func.count(Project.id)).filter(
        Project.created_at >= cutoff, Project.win_locked.is_(True))
    if scope_filter is not None:
        lq = lq.filter(scope_filter)
    locked_by_stage = {st: int(c or 0) for st, c in lq.group_by(Project.current_stage).all()}

    # 漏斗顺序:植入 → 标前 → 标中 → 中标 → 签约
    # (PMA 业务阶段:embed/植入是早期"方案植入"阶段,不是终态)
    # discover/quoted 不进漏斗;lost/paused 算流失
    STAGES = [
        ('embed',      _t('植入')),
        ('pre_tender', _t('标前')),
        ('tendering',  _t('标中')),
        ('awarded',    _t('中标')),
        ('signed',     _t('签约')),
    ]
    funnel = []
    for key, label in STAGES:
        d = stage_data.get(key, {'count': 0, 'amount': 0})
        funnel.append({'stage': label, 'count': d['count'], 'amount': int(d['amount']),
                       'locked': locked_by_stage.get(key, 0)})

    # 流失统计(lost + paused)
    lost   = stage_data.get('lost',   {'count': 0, 'amount': 0})
    paused = stage_data.get('paused', {'count': 0, 'amount': 0})
    loss_count  = lost['count'] + paused['count']
    loss_amount = int(lost['amount'] + paused['amount'])

    # 总项目数 = 5 阶段 + lost + paused(分母,用于转化率和流失率)
    total = sum(s['count'] for s in funnel) + loss_count
    tail = funnel[-1]['count']   # 签约
    conv = round((tail / total) * 100) if total > 0 else 0
    loss_rate = round((loss_count / total) * 100) if total > 0 else 0

    return funnel, conv, 0, {
        'count': loss_count, 'amount': loss_amount, 'rate': loss_rate,
        'lost': lost, 'paused': paused,
    }


# ─── 我的项目 ────────────────────────────────────────────
# DB current_stage(英文 key)→ 中文 label / pill tone / 进度百分比
_PROJ_STAGE_MAP = {
    'discover':   {'label': '发现', 'tone': 'neutral', 'pct': 10},
    'embed':      {'label': '植入', 'tone': 'accent',  'pct': 25},
    'pre_tender': {'label': '标前', 'tone': 'warn',    'pct': 40},
    'tendering':  {'label': '标中', 'tone': 'info',    'pct': 55},
    'awarded':    {'label': '中标', 'tone': 'success', 'pct': 70},
    'quoted':     {'label': '批价', 'tone': 'success', 'pct': 85},
    'signed':     {'label': '签约', 'tone': 'success', 'pct': 100},
    'lost':       {'label': '失败', 'tone': 'danger',  'pct': 0},
    'paused':     {'label': '暂停', 'tone': 'neutral', 'pct': 50},
}


def _build_projects(user, scope_filter=None):
    """scope_filter: SQLAlchemy 过滤子句(我的=owner==user;可见=get_viewable_data id 集合)"""
    from datetime import date
    items = []
    due_soon_count = 0
    today = date.today()
    try:
        from app.models.project import Project
        q = Project.query
        if scope_filter is not None:
            q = q.filter(scope_filter)
        rows = q.order_by(Project.updated_at.desc()).limit(6).all()
        for p in rows:
            stage_key = getattr(p, 'current_stage', None) or 'discover'
            meta = _PROJ_STAGE_MAP.get(stage_key, {'label': stage_key, 'tone': 'neutral', 'pct': 0})

            # 到期算法:delivery_forecast - today
            due_in = None
            due_red = False
            if p.delivery_forecast:
                due_in = (p.delivery_forecast - today).days
                due_red = (0 <= due_in <= 7)
                if due_red:
                    due_soon_count += 1

            items.append({
                'id': p.id,
                'name': (p.project_name or '')[:40],
                'stage': _t(meta['label']),
                'stageT': meta['tone'],
                'progress': meta['pct'],
                'dueIn': due_in if due_in is not None else 0,
                'dueRed': due_red,
                'winLocked': bool(getattr(p, 'win_locked', False)) and p.current_stage != 'signed',
                'winReason': getattr(p, 'win_lock_reason', None) or '',
            })
    except Exception as e:
        import logging; logging.warning(f'projects err: {e}')
    return items, {'active': len(items), 'dueSoon': due_soon_count}


# ─── 我的报价 ────────────────────────────────────────────
def _build_quotes(user, scope_filter=None):
    """scope_filter: SQLAlchemy 过滤子句(我的=owner==user;可见=get_viewable_data id 集合)"""
    quotes, counts = [], {'newThisMonth': 0, 'awaitConfirm': 0, 'wonThisMonth': 0}
    try:
        from app.models.quotation import Quotation
        base = Quotation.query
        if scope_filter is not None:
            base = base.filter(scope_filter)
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        counts['newThisMonth'] = base.filter(Quotation.created_at >= month_start).count()
        counts['awaitConfirm'] = base.filter(Quotation.confirmation_badge_status == 'pending').count()
        counts['wonThisMonth'] = base.filter(
            Quotation.confirmation_badge_status == 'confirmed',
            Quotation.confirmed_at >= month_start,
        ).count()

        # 列表 5 条(按 confirmation_badge_status 显示状态;字段名:amount 不是 total_amount)
        stat_map = {
            'none':      (_t('待审批'), 'warn'),
            'pending':   (_t('待确认'), 'warn'),
            'confirmed': (_t('已成交'), 'success'),
        }
        for q in base.order_by(Quotation.updated_at.desc()).limit(5).all():
            badge = q.confirmation_badge_status or 'none'
            status_lbl, tone = stat_map.get(badge, (badge, 'neutral'))
            quotes.append({
                'id': q.quotation_number,
                'db_id': q.id,  # 用于跳转 AT 详情 URL
                'title': (q.customer.company_name if q.customer else '—')[:24],
                'amount': float(q.amount or 0),
                'status': status_lbl,
                'tone': tone,
            })
    except Exception as e:
        import logging; logging.warning(f'quotes err: {e}')
    return quotes, counts


# ─── 报销(年度 + 12 月折线 + 最近 3 笔) ────────────
def _build_expense(user, monthly_stats, year_total, currency_symbol, scope_filter=None, mine=True):
    """报销:scope_filter 控制范围(我的=owner==user;可见=get_viewable_data,含权限级别+归属+content_filters)。
       mine=True 用 main.py 传入的 monthly/year_total;非 mine 态(可见范围)重算。
    """
    from app.models.expense import Expense
    from sqlalchemy import func, extract
    from app import db

    now = datetime.now()

    # 可见范围态:重算 monthly + year_total(我的态用 main.py 传入的)
    if not mine:
        q = db.session.query(Expense).filter(Expense.is_deleted == False)
        if scope_filter is not None:
            q = q.filter(scope_filter)
        rows = q.filter(extract('year', Expense.created_at) == now.year).all()
        monthly_stats = [0] * 12
        year_total = 0
        for e in rows:
            m = e.created_at.month - 1
            amt = float(e.total_amount or 0)
            monthly_stats[m] += amt
            year_total += amt

    # 去年同期(1月 → 当前月)累计,用于真实同比
    year_total_last = 0
    try:
        q_last = db.session.query(func.coalesce(func.sum(Expense.total_amount), 0)).filter(
            Expense.is_deleted == False,
            extract('year', Expense.created_at) == now.year - 1,
            extract('month', Expense.created_at) <= now.month,
        )
        if scope_filter is not None:
            q_last = q_last.filter(scope_filter)
        year_total_last = float(q_last.scalar() or 0)
    except Exception:
        pass

    recent = []
    try:
        rq = Expense.query.filter(Expense.is_deleted == False)
        if scope_filter is not None:
            rq = rq.filter(scope_filter)
        for e in rq.order_by(Expense.updated_at.desc()).limit(3).all():
            stat_map = {
                'draft': (_t('草稿'), 'neutral'), 'pending': (_t('待审批'), 'warn'),
                'approved': (_t('已通过'), 'success'), 'paid': (_t('已支付'), 'success'),
                'rejected': (_t('已驳回'), 'danger'),
            }
            status_lbl, tone = stat_map.get(e.status, (e.status or '—', 'neutral'))
            recent.append({
                'id': f'EXP-{e.id}',
                'title': (e.expense_subject or e.notes or _t('报销单'))[:24],
                'amount': float(e.total_amount or 0),
                'status': status_lbl,
                'tone': tone,
            })
    except Exception:
        pass

    # 科目分类(本年,跟随 scope_filter);标签+配色对齐报销单表单
    _CAT_META = {
        'entertainment':        (_t('招待费'),   '#ff6b6b'),
        'local_transport':      (_t('市内交通'), '#4ecdc4'),
        'travel_accommodation': (_t('差旅住宿'), '#45b7d1'),
        'office_supplies':      (_t('办公用品'), '#96ceb4'),
        'communication':        (_t('通讯费'),   '#ffeaa7'),
        'fuel':                 (_t('油费'),     '#dda0dd'),
        'parking':              (_t('停车费'),   '#98d8c8'),
        'meals':                (_t('餐费'),     '#f7dc6f'),
        'other':                (_t('其他'),     '#aab7b8'),
    }
    categories = []
    try:
        from app.models.expense import ExpenseDetail
        cq = db.session.query(
            ExpenseDetail.expense_category,
            func.coalesce(func.sum(ExpenseDetail.current_amount), 0),
        ).join(Expense, Expense.id == ExpenseDetail.expense_id).filter(
            Expense.is_deleted == False,
            Expense.status != 'draft',
            extract('year', Expense.created_at) == now.year,
        )
        if scope_filter is not None:
            cq = cq.filter(scope_filter)
        crows = cq.group_by(ExpenseDetail.expense_category).all()
        _ctot = sum(float(a or 0) for _, a in crows) or 0
        for code, amt in crows:
            amt = float(amt or 0)
            if amt <= 0:
                continue
            lbl, color = _CAT_META.get(code, (code or _t('其他'), '#aab7b8'))
            categories.append({'label': lbl, 'color': color, 'amount': amt,
                               'pct': round(amt / _ctot * 100) if _ctot else 0})
        categories.sort(key=lambda x: x['amount'], reverse=True)
    except Exception:
        pass

    return {
        'yearTotal': year_total,
        'yearTotalLast': year_total_last,  # 去年 1月→当前月 累计(真实同比基数)
        'monthly': monthly_stats,
        'months': [_t('%(m)s月', m=i) for i in range(1, 13)],
        'recent': recent,
        'categories': categories,
        'currency': currency_symbol,
    }


# ─── 工作记录流 ─── WorkItem(日历行程,Action 自动同步过来)
_WORKITEM_TYPE_LABEL = {
    'customer_visit':       '客户拜访',
    'customer_maintenance': '客户维护',
    'presales_support':     '售前支持',
    'business_negotiation': '商务洽谈',
    'meeting':              '会议',
    'finance_work':         '财务',
    'procurement':          '采购',
    'product_planning':     '产品规划',
    'recruitment':          '招聘',
    'other':                '其它',
}


def _build_worklog(user):
    """工作记录 = WorkItem(日历行程级别),已自动同步 Action / 报价/批价 等业务事件
       权限:按 worklog 模块 permission_level(system/company/department/personal)+ affiliations 归属,
            每条标 is_mine 供 chip 过滤
    """
    items = []
    try:
        from app.models.worklog import WorkItem
        from app.utils.access_control import (
            get_company_user_ids, get_department_user_ids, get_personal_viewable_user_ids,
        )

        # 按 PMA 权限系统 + 归属授权决定可见 owner_id 范围
        if user.role == 'admin' or user.get_permission_level('worklog') == 'system':
            base_q = WorkItem.query
        else:
            level = user.get_permission_level('worklog') or 'personal'
            if level == 'company':
                owner_ids = get_company_user_ids(user, include_affiliations=True)
            elif level == 'department':
                owner_ids = get_department_user_ids(user, include_affiliations=True)
            else:
                owner_ids = get_personal_viewable_user_ids(user)
            base_q = WorkItem.query.filter(WorkItem.owner_id.in_(owner_ids))

        rows = base_q.filter(WorkItem.is_deleted == False).order_by(
            WorkItem.created_at.desc(),
        ).limit(50).all()

        from datetime import date as _date
        today = _date.today()
        for w in rows:
            d = w.planned_date
            customer = (w.customer.company_name[:14] if w.customer else '—')
            project  = (w.project.project_name[:18]  if w.project  else '—')
            text     = (w.title or '') + (' · ' + (w.description or '')[:80] if w.description else '')
            _raw_type = _WORKITEM_TYPE_LABEL.get(w.work_type, w.work_type or '')
            type_lbl = _t(_raw_type) if _raw_type else ''
            is_mine  = (w.owner_id == user.id)
            # 状态徽章:planned + 过期日 → 逾期(danger);planned → 计划(neutral);
            #          in_progress → 进行中(info);completed → 不标
            status_tag = None
            if w.status == 'in_progress':
                status_tag = {'label': _t('进行中'), 'tone': 'info'}
            elif w.status == 'planned':
                if d and d < today:
                    status_tag = {'label': _t('逾期'), 'tone': 'danger'}
                else:
                    status_tag = {'label': _t('计划'), 'tone': 'neutral'}
            items.append({
                'id': w.id,
                'project_id': w.project_id,
                'customer_id': w.customer_id,
                'who': _fmt_user(getattr(w, 'owner', None)),
                'customer': customer,
                'project': project,
                'time': _ago(w.created_at),
                'date': d.isoformat() if d else '',
                'text': text[:220],
                'type_label': type_lbl,
                'status_tag': status_tag,
                'replies': 0,
                'mentioned': False,  # WorkItem 本身无 @,日报 Worklog 才有
                'is_mine': is_mine,
            })
    except Exception as e:
        import logging; logging.warning(f'worklog err: {e}')
    return items


# ─── 角色化布局 ──────────────────────────────────────────
_TASK_STATUS_LABELS = {'pending': '待开始', 'in_progress': '进行中', 'paused': '已暂停',
                       'pending_review': '待审核', 'completed': '已完成'}
_TASK_STATUS_TONE = {'pending': 'neutral', 'in_progress': 'info', 'paused': 'warn',
                     'pending_review': 'warn', 'completed': 'success'}


def _team_scope(user):
    """「团队」范围:基于**组织管理关系**(部门负责人 / 归属上级 / admin),
    不是数据查看权限级别 —— 看得到很多数据 ≠ 带团队。
    get_viewable_user_ids() 已编码:admin=全员、部门负责人=本部门成员、归属链=下属。
    只能看到自己 → has_team=False,不显示「我的/团队」开关。"""
    try:
        ids = [i for i in (user.get_viewable_user_ids() or []) if i]
    except Exception:
        ids = [user.id]
    if user.id not in ids:
        ids.append(user.id)
    has_team = len(set(ids) - {user.id}) > 0
    label = _t('系统') if user.role == 'admin' else _t('团队')
    return {'has_team': has_team, 'ids': ids, 'label': label}


def _my_task_filter(user):
    """「我的任务」过滤:指派给我 OR 我在协助人(shared_with_users)里。
    shared_with_users 为 JSON 列,用 JSONB @> 做数组包含(同 access_control 口径)。"""
    from sqlalchemy import cast, text
    from sqlalchemy.dialects.postgresql import JSONB
    from app import db
    from app.models.task import Task
    return db.or_(
        Task.assignee_id == user.id,
        cast(Task.shared_with_users, JSONB).op('@>')(text(f"'[{int(user.id)}]'::jsonb")),
    )


def _tasks_payload(user, task_filter, with_assignee=False):
    """按过滤条件取任务:状态计数 + 前 6 项(未完成优先、按截止升序)。"""
    from app.models.task import Task
    if task_filter is None:
        return {'counts': {'all': 0, 'in_progress': 0, 'pending': 0, 'pending_review': 0, 'completed': 0},
                'items': []}
    tasks = Task.query.filter(task_filter, Task.is_deleted == False,
                              Task.status != 'cancelled').all()
    counts = {'all': len(tasks), 'in_progress': 0, 'pending': 0, 'pending_review': 0, 'completed': 0}
    for t in tasks:
        es = t.effective_status
        if es in counts:
            counts[es] += 1

    def _key(t):
        return (t.effective_status == 'completed', t.due_date or datetime.max)

    items = []
    for t in sorted(tasks, key=_key)[:6]:
        try:
            total = t.subtasks.filter_by(is_deleted=False).count()
            done = t.subtasks.filter_by(is_deleted=False, status='completed').count()
        except Exception:
            total = done = 0
        es = t.effective_status
        prog = 100 if es == 'completed' else (int(done / total * 100) if total else 0)
        rel = (t.project.project_name if t.project else
               (t.customer.company_name if t.customer else ''))
        # 最近进展:最新一条回复;无回复则用任务描述
        try:
            from app.models.task import TaskReply
            lr = t.replies.filter_by(is_deleted=False).order_by(TaskReply.created_at.desc()).first()
            raw = lr.content if lr else (t.description or '')
        except Exception:
            raw = t.description or ''
        note = ' '.join((raw or '').split())[:40]
        items.append({
            'id': t.id, 'title': t.title, 'project': rel,
            'note': note,
            'due': t.due_date.strftime('%m-%d') if t.due_date else '—',
            'status': es, 'statusLabel': _t(_TASK_STATUS_LABELS.get(es, es)),
            'tone': _TASK_STATUS_TONE.get(es, 'neutral'), 'progress': prog,
            'assignee': _fmt_user(t.assignee) if with_assignee else '',
            'route': f'/task/management?task={t.id}',
        })
    return {'counts': counts, 'items': items}


def _build_tasks(user):
    """「任务」卡:我的任务(被指派 ∪ 我协助)+ (部门负责人额外)团队任务(成员被指派)。
    管理员 → 全局任务(所有任务,无开关)。"""
    from app import db
    from app.models.task import Task
    if user.role == 'admin':
        return {'has_team': False, 'title': _t('全局任务'),
                'mine': _tasks_payload(user, Task.id.isnot(None), with_assignee=True)}
    ts = _team_scope(user)
    out = {'has_team': ts['has_team'], 'teamLabel': ts['label'], 'title': _t('我的任务'),
           'mine': _tasks_payload(user, _my_task_filter(user))}
    if ts['has_team']:
        out['team'] = _tasks_payload(user, Task.assignee_id.in_(ts['ids']), with_assignee=True)
    return out


def _dash_periods():
    """月 / 季 / 年 三个时间窗口 (start, end),与 KPI 同口径。"""
    now = datetime.now()
    y, m = now.year, now.month
    month_start = datetime(y, m, 1)
    month_end = datetime(y + 1, 1, 1) if m == 12 else datetime(y, m + 1, 1)
    q = (m - 1) // 3 + 1
    qs_m = (q - 1) * 3 + 1
    qe_m = qs_m + 3
    quarter_start = datetime(y, qs_m, 1)
    quarter_end = datetime(y + 1, qe_m - 12, 1) if qe_m > 12 else datetime(y, qe_m, 1)
    year_start = datetime(y, 1, 1)
    year_end = datetime(y + 1, 1, 1)
    return {'month': (month_start, month_end),
            'quarter': (quarter_start, quarter_end),
            'year': (year_start, year_end)}


def _build_implant(user, variant='solution'):
    """「植入产值」卡(月/季/年切换,按产品聚合 implant_subtotal,solution/product 同前端):
       product = 我管理分类下产品;solution = 我创建 ∪ 我确认的报价里的产品。"""
    from sqlalchemy import func
    from app import db
    from app.models.quotation import Quotation, QuotationDetail
    from app.utils.access_control import get_viewable_data

    periods = {}

    if variant == 'product':
        from app.models.product import Product
        my_cat_ids = [c.id for c in getattr(user, 'managed_categories', [])]
        for pk, (s, e) in _dash_periods().items():
            items, total = [], 0
            if my_cat_ids:
                rows = db.session.query(
                    Product.product_name,
                    func.count(QuotationDetail.id),
                    func.coalesce(func.sum(QuotationDetail.implant_subtotal), 0),
                ).join(QuotationDetail, QuotationDetail.product_mn == Product.product_mn)\
                 .join(Quotation, Quotation.id == QuotationDetail.quotation_id)\
                 .filter(Product.category_id.in_(my_cat_ids),
                         QuotationDetail.implant_subtotal > 0,
                         Quotation.created_at >= s, Quotation.created_at < e)\
                 .group_by(Product.product_name)\
                 .order_by(func.sum(QuotationDetail.implant_subtotal).desc()).all()
                total = sum(float(r[2]) for r in rows)
                items = [{'name': n or '—', 'count': int(c), 'amount': float(a)} for n, c, a in rows[:6]]
            periods[pk] = {'total': total, 'items': items}
        return {'variant': 'product', 'sub': _t('我负责分类的产品'),
                'has_team': False, 'mine': {'periods': periods}}

    # solution:按报价明细产品聚合;我的=我创建∪我确认,团队=我可见范围的报价(部门负责人)
    from app.models.quotation_confirmation_task import QuotationConfirmationTask

    def _solution_periods(quote_filter):
        out = {}
        for pk, (s, e) in _dash_periods().items():
            rows = db.session.query(
                QuotationDetail.product_name,
                func.count(QuotationDetail.id),
                func.coalesce(func.sum(QuotationDetail.implant_subtotal), 0),
            ).join(Quotation, Quotation.id == QuotationDetail.quotation_id)\
             .filter(quote_filter,
                     QuotationDetail.implant_subtotal > 0,
                     Quotation.created_at >= s, Quotation.created_at < e)\
             .group_by(QuotationDetail.product_name)\
             .order_by(func.sum(QuotationDetail.implant_subtotal).desc()).all()
            total = sum(float(r[2]) for r in rows)
            items = [{'name': n or '—', 'count': int(c), 'amount': float(a)} for n, c, a in rows[:6]]
            out[pk] = {'total': total, 'items': items}
        return out

    if variant == 'admin':
        # 管理员:全局植入产值(全公司所有报价),无开关
        return {'variant': 'admin', 'sub': _t('全公司报价'), 'has_team': False,
                'mine': {'periods': _solution_periods(Quotation.id.isnot(None))}}

    confirmed_q = db.session.query(QuotationConfirmationTask.quotation_id).filter(
        QuotationConfirmationTask.assignee_id == user.id,
        QuotationConfirmationTask.status == 'confirmed')
    ts = _team_scope(user)
    res = {'variant': 'solution', 'sub': _t('我创建 / 确认的报价'),
           'has_team': ts['has_team'], 'teamLabel': ts['label'],
           'mine': {'periods': _solution_periods(
               db.or_(Quotation.owner_id == user.id, Quotation.id.in_(confirmed_q)))}}
    if ts['has_team']:
        team_q = get_viewable_data(Quotation, user).with_entities(Quotation.id).subquery()
        res['team'] = {'periods': _solution_periods(
            Quotation.id.in_(db.session.query(team_q.c.id)))}
    return res


def _role_base_layout(user):
    """角色 → 基础卡片集合 + KPI 变体(KPI 卡是否出现由 role_layout 统一裁决)。

    返回 {'cards': [...卡片 key 按渲染顺序...], 'kpi_variant': '...'}。
    卡片 key:todo / kpi / funnel / projects / quotes / expense / task / implant / worklog
    KPI 变体:default(销售) / solution / product / finance / overview / minimal
    注意:除 CEO 外,各分支不再写死 'kpi';是否显示由 role_layout 按「是否配置绩效项」决定。
    """
    role = (user.role or '').lower()
    if role == 'admin':
        # 管理员:全局视角 — 去 KPI/项目/报价,加 全局任务 + 全局植入产值
        return {'cards': ['todo', 'funnel', 'task', 'implant', 'expense', 'worklog'],
                'kpi_variant': 'admin'}
    if role == 'ceo':
        # CEO 维持现状:保留总览 KPI(此分支的 'kpi' 不受配置裁决影响)
        return {'cards': ['todo', 'kpi', 'funnel', 'projects', 'quotes', 'expense', 'worklog'],
                'kpi_variant': 'overview'}
    # 财务 + 出纳:全公司报销进度
    if role in ('finance', 'finance_director', 'finace_director', 'finance_supervisor', 'treasurer'):
        return {'cards': ['todo', 'expense', 'worklog'], 'kpi_variant': 'finance'}
    if role == 'solution_manager':
        return {'cards': ['todo', 'task', 'implant', 'expense', 'worklog'], 'kpi_variant': 'solution'}
    if role == 'product_manager':
        return {'cards': ['todo', 'task', 'implant', 'expense', 'worklog'], 'kpi_variant': 'product'}
    # 工程师:对齐解决方案,但去掉植入卡(任务/图纸为主)
    if role == 'engineer':
        return {'cards': ['todo', 'task', 'expense', 'worklog'], 'kpi_variant': 'solution'}
    # 商务助理:对齐销售
    if role == 'business_admin':
        return {'cards': ['todo', 'funnel', 'projects', 'quotes', 'expense', 'worklog'], 'kpi_variant': 'default'}
    # 市场 / 人事 / 采购供应链:留 待办·报销·工作记录(KPI 卡按配置自动出现)
    if role in ('marketing_manager', 'marketingplan', 'hr_manager', 'hrdp_manager',
                'supplychain_manager', 'buyer'):
        return {'cards': ['todo', 'expense', 'worklog'], 'kpi_variant': 'default'}
    # 默认:销售家族 + 服务经理 + 外部(代理商/普通用户)对齐销售
    return {'cards': ['todo', 'funnel', 'projects', 'quotes', 'expense', 'worklog'],
            'kpi_variant': 'default'}


def role_layout(user):
    """角色 → 仪表盘卡片 + KPI 变体(唯一事实源)。

    KPI 卡是否显示 = PerformanceDashboardService.has_kpi_config(user)(配置驱动):
    有角色绩效方案 或 配了带目标的考核项 → 显示;否则不显示。新增角色无需改本函数。
    例外:CEO 维持现状(总览 KPI 始终保留)。
    """
    lay = _role_base_layout(user)
    role = (user.role or '').lower()
    if role == 'ceo':
        return lay   # CEO 不受配置裁决,保持原样
    cards = list(lay['cards'])
    try:
        from app.services.performance_dashboard_service import PerformanceDashboardService
        has_kpi = PerformanceDashboardService.has_kpi_config(user)
    except Exception:
        has_kpi = False
    if has_kpi and 'kpi' not in cards:
        i = (cards.index('todo') + 1) if 'todo' in cards else 0
        cards.insert(i, 'kpi')         # 统一插在「待办」之后
    elif not has_kpi and 'kpi' in cards:
        cards.remove('kpi')
    lay['cards'] = cards
    return lay


# ─── 主入口 ────────────────────────────────────────────
def build_dashboard(user, monthly_stats=None, year_total=None,
                    db_currency_symbol='¥', expense_currency_symbol=None,
                    currency_symbol=None):
    """聚合一次性返回全部数据。

    Args:
        user: current_user
        monthly_stats / year_total: 复用 main.index 已算好的报销月度数据
        db_currency_symbol: 数据库底层货币(统计用 — KPI/漏斗/项目/报价)
        expense_currency_symbol: 用户结算货币(报销用,显示报销最终金额)
        currency_symbol: 兼容旧调用方,等价于 db_currency_symbol
    """
    # 兼容旧签名
    if currency_symbol is not None and db_currency_symbol == '¥':
        db_currency_symbol = currency_symbol
    if expense_currency_symbol is None:
        expense_currency_symbol = db_currency_symbol
    from app.models.project import Project
    from app.models.quotation import Quotation
    from app.models.expense import Expense

    layout = role_layout(user)
    cards = set(layout['cards'])
    variant = layout['kpi_variant']
    scope = _get_dash_scope(user)

    # 所有角色共有:待办 / KPI / 工作日志(KPI 变体按角色,P2 起分流)
    out = {
        'currency': db_currency_symbol,  # 顶层货币 — 统计用,跟 PMA_DB_TYPE 走
        'layout': layout,
        'scope': scope,
        'todos': _build_todos(user) if 'todo' in cards else [],
        'kpis':  _build_kpis(user, db_currency_symbol, variant) if 'kpi' in cards else None,
        'todayStats': _build_today_stats(user) if 'kpi' in cards else None,
        'worklog': _build_worklog(user) if 'worklog' in cards else None,
    }

    sales_trio = cards & {'funnel', 'projects', 'quotes'}
    if variant == 'finance' and 'expense' in cards:
        # —— 财务:全公司报销进度(可见范围),单视图(无"我的/团队"切换)——
        expense_fin = _build_expense(user, None, None, expense_currency_symbol,
                                     _viewable_id_clause(Expense, user), mine=False)
        out['expense'] = expense_fin
        out['scope'] = {'mine': scope['mine'], 'secondary': None, 'top_level': scope.get('top_level')}
        out['scopeData'] = {'mine': {'expense': expense_fin}, 'secondary': None}

    elif variant == 'admin':
        # —— 管理员:漏斗=全局(可见全部,单视图无开关);报销=个人 ——
        fg, cg, yg, lg = _build_funnel(user, _viewable_id_clause(Project, user))
        eg = _build_expense(user, monthly_stats or [0]*12, year_total or 0,
                            expense_currency_symbol, Expense.owner_id == user.id, mine=True)
        out['scope'] = {'mine': scope['mine'], 'secondary': None, 'top_level': scope.get('top_level')}
        out.update({'funnel': fg, 'funnelConversion': cg, 'funnelLoss': lg, 'funnelYoY': yg,
                    'expense': eg})
        out['scopeData'] = {'mine': {'funnel': fg, 'funnelConversion': cg, 'funnelLoss': lg,
                                     'expense': eg}, 'secondary': None}

    elif sales_trio:
        # —— 销售 / 总览:漏斗/项目/报价/报销全量(保留 mine + secondary 双套,绝不越权)——
        funnel_m, conv_m, yoy_m, loss_m = _build_funnel(user, Project.owner_id == user.id)
        projects_m, proj_counts_m = _build_projects(user, Project.owner_id == user.id)
        quotes_m, quote_counts_m = _build_quotes(user, Quotation.owner_id == user.id)
        expense_m = _build_expense(user, monthly_stats or [0]*12, year_total or 0,
                                   expense_currency_symbol, Expense.owner_id == user.id, mine=True)
        funnel_s = projects_s = quotes_s = expense_s = None
        conv_s = yoy_s = 0
        loss_s = None
        proj_counts_s = quote_counts_s = None
        if scope['secondary']:
            funnel_s, conv_s, yoy_s, loss_s = _build_funnel(user, _viewable_id_clause(Project, user))
            projects_s, proj_counts_s = _build_projects(user, _viewable_id_clause(Project, user))
            quotes_s, quote_counts_s = _build_quotes(user, _viewable_id_clause(Quotation, user))
            expense_s = _build_expense(user, None, None, expense_currency_symbol,
                                       _viewable_id_clause(Expense, user), mine=False)
        out.update({
            'funnel': funnel_m, 'funnelConversion': conv_m, 'funnelLoss': loss_m, 'funnelYoY': yoy_m,
            'projects': projects_m, 'projectCounts': proj_counts_m,
            'quotes': quotes_m, 'quoteCounts': quote_counts_m,
            'expense': expense_m,
            'scopeData': {
                'mine': {
                    'funnel': funnel_m, 'funnelConversion': conv_m, 'funnelLoss': loss_m,
                    'projects': projects_m, 'projectCounts': proj_counts_m,
                    'quotes': quotes_m, 'quoteCounts': quote_counts_m,
                    'expense': expense_m,
                },
                'secondary': None if not scope['secondary'] else {
                    'funnel': funnel_s, 'funnelConversion': conv_s, 'funnelLoss': loss_s,
                    'projects': projects_s, 'projectCounts': proj_counts_s,
                    'quotes': quotes_s, 'quoteCounts': quote_counts_s,
                    'expense': expense_s,
                },
            },
        })

    elif 'expense' in cards:
        # —— 解决方案/产品经理:仅「我的报销」个人面板(单视图,不算销售卡)——
        expense_m = _build_expense(user, monthly_stats or [0]*12, year_total or 0,
                                   expense_currency_symbol, Expense.owner_id == user.id, mine=True)
        out['expense'] = expense_m
        out['scope'] = {'mine': scope['mine'], 'secondary': None, 'top_level': scope.get('top_level')}
        out['scopeData'] = {'mine': {'expense': expense_m}, 'secondary': None}

    # —— 经理新卡(P3 实现 builder;此处按需调用)——
    if 'task' in cards:
        out['task'] = _build_tasks(user)
    if 'implant' in cards:
        out['implant'] = _build_implant(user, variant)

    return out
