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


def _fmt_user(u):
    if not u:
        return '—'
    return getattr(u, 'real_name', None) or getattr(u, 'username', None) or '—'


def _ago(dt):
    if not dt:
        return '—'
    sec = (datetime.now() - dt).total_seconds()
    if sec < 3600:  return f'{int(sec/60)} 分钟前'
    if sec < 86400: return f'{int(sec/3600)} 小时前'
    days = int(sec / 86400)
    return f'{days} 天前' if days < 30 else dt.strftime('%m-%d')


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
    mine = {'key': 'mine', 'label': '我的'}
    levels = [_user_level(user, m) for m in ('project', 'quotation', 'expense')]
    top = max(levels, key=lambda l: _DASH_LEVEL_RANK.get(l, 0))
    secondary = None
    if _DASH_LEVEL_RANK.get(top, 0) > 0:
        secondary = {'key': 'team', 'label': _DASH_LEVEL_LABELS.get(top, '团队')}
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
        'expense': '报销单', 'purchase_order': '采购订单',
        'project': '项目立项', 'pricing_order': '批价单',
        'quotation': '报价单', 'sales_order': '客户订单',
        'customer': '客户',
    }

    # 1) 待审批 — 复用 get_user_pending_approvals
    # AT 详情页 URL 映射 — 点击跳转到对应 AT 详情 + #approval hash 自动展开 chip dropdown
    at_url_map = {
        'expense':         lambda i: f'/expense/{i}/at_view#approval',
        'project':         lambda i: f'/project/{i}/at_view#approval',
        'quotation':       lambda i: f'/quotation/{i}/at_view#approval',
        'purchase_order':  lambda i: f'/purchase-order/{i}#approval',
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
            out.append({
                'id': f'AI{ai.id}', 'type': 'approval', 'typeLabel': '待审批', 'tone': 'warn',
                'title': f'{obj_label} #{ai.object_id}',
                'meta': '我作为当前节点审批人',
                'who': _fmt_user(submitter),
                'when': _ago(ai.started_at),
                'route': route_url, 'urgent': urgent,
            })
    except Exception as e:
        import logging; logging.warning(f'todos approval err: {e}')

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
            'worklog_mention': '日志 @ 我',
            'task_reply':      '任务回复',
            'task_assigned':   '任务指派',
        }
        for m in msgs:
            from app.models.user import User
            sender = User.query.get(m.sender_id) if m.sender_id else None
            out.append({
                'id': f'M{m.id}', 'type': 'mention', 'typeLabel': type_label_map.get(m.message_type, '@我'),
                'tone': 'info',
                'title': (m.title or '')[:60],
                'meta': (m.content or '')[:60],
                'who': _fmt_user(sender),
                'when': _ago(m.created_at),
                'route': '#', 'urgent': False,
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

        # 4a) 中标(awarded)项目:owner 或 销售负责人 == 我;关联该项目最近一条 Action.date
        #     >30 天;若从无跟进 → 用进入中标阶段时间(阶段历史),兜底项目创建时间
        from app.models.project import Project
        from app.models.action import Action
        from app.models.projectpm_stage_history import ProjectStageHistory
        projs = Project.query.filter(
            Project.is_deleted == False,
            Project.current_stage == 'awarded',
            _or(Project.owner_id == user.id, Project.vendor_sales_manager_id == user.id),
        ).all()
        proj_ids = [p.id for p in projs]
        # 批量:每项目最近 Action.date(一次 group by,替代逐项目查询)
        last_action = {}
        if proj_ids:
            last_action = dict(db.session.query(Action.project_id, _f.max(Action.date))
                               .filter(Action.project_id.in_(proj_ids))
                               .group_by(Action.project_id).all())
        # 批量:从无 Action 的项目 → 进入中标阶段时间(一次 group by)
        no_act_ids = [pid for pid in proj_ids if pid not in last_action]
        awarded_since = {}
        if no_act_ids:
            awarded_since = dict(db.session.query(ProjectStageHistory.project_id, _f.max(ProjectStageHistory.change_date))
                                 .filter(ProjectStageHistory.project_id.in_(no_act_ids),
                                         ProjectStageHistory.to_stage == 'awarded')
                                 .group_by(ProjectStageHistory.project_id).all())
        for p in projs:
            last_date = last_action.get(p.id)
            if last_date:
                days = (today - last_date).days
            else:
                base = awarded_since.get(p.id) or p.created_at
                days = (now - base).days if base else None
            if days is not None and days > 30:
                fu.append({
                    'id': f'P{p.id}', 'type': 'action', 'typeLabel': '项目跟进', 'tone': 'danger',
                    'title': f'{p.project_name} · {days} 天未跟进', 'meta': '中标',
                    'who': '—', 'when': f'{days}天',
                    'route': f'/project/{p.id}/at_view', 'urgent': days > 60, '_d': days,
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
                    'id': f'T{t.id}', 'type': 'action', 'typeLabel': '任务跟进', 'tone': 'danger',
                    'title': f'{t.title} · {days} 天未更新', 'meta': '任务',
                    'who': '—', 'when': f'{days}天',
                    'route': f'/task/management?task={t.id}', 'urgent': days > 20, '_d': days,
                })

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
        return ('—' if current == 0 else '新增', 'success' if current > 0 else 'neutral')
    pct = round((float(current) - float(previous)) / float(previous) * 100)
    if pct == 0:
        return ('持平', 'neutral')
    sign = '+' if pct > 0 else ''
    return (f'{sign}{pct}%', 'success' if pct > 0 else 'warn')


def _kpi_item(label, value, target, unit, prev, tone, delta=None):
    """构造一个 KPI 指标项(列表契约)。delta=('文案','tone') 可显式覆盖(快照型指标用)。"""
    if delta is None:
        d, dt = _kpi_delta(value, prev)
    else:
        d, dt = delta
    return {'data': {'label': label, 'value': int(value), 'target': int(target), 'unit': unit},
            'tone': tone, 'delta': d, 'deltaTone': dt}


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

    # Target 累加(从 performance_targets 表本周期所含月份)
    sales_t = implant_t = proj_t = cust_t = 0
    try:
        from app.models.performance import PerformanceTarget
        rows = PerformanceTarget.query.filter(
            PerformanceTarget.user_id == user.id,
            PerformanceTarget.year == start.year,
            PerformanceTarget.month.in_(list(target_months)),
        ).all()
        for r in rows:
            sales_t   += float(r.sales_amount_target   or 0)
            implant_t += float(r.implant_amount_target or 0)
            proj_t    += int(r.new_projects_target     or 0)
            cust_t    += int(r.new_customers_target    or 0)
    except Exception:
        pass

    def _delta(current, previous):
        if previous <= 0:
            return ('—' if current == 0 else '新增', 'success' if current > 0 else 'neutral')
        pct = round((float(current) - float(previous)) / float(previous) * 100)
        if pct == 0:
            return ('持平', 'neutral')
        sign = '+' if pct > 0 else ''
        return (f'{sign}{pct}%', 'success' if pct > 0 else 'warn')

    sd, sdt = _delta(sales_a, sales_p)
    id_, idt = _delta(implant_a, implant_p)
    pd, pdt = _delta(proj_a, proj_p)
    cd, cdt = _delta(cust_a, cust_p)

    # target=0 表示"未设目标",模板灰色显示;不再 fallback 到 1
    # 列表契约:每项 {data:{label,value,target,unit}, tone, delta, deltaTone}(模板通用循环)
    return [
        {'data': {'label': f'{label_prefix}销售额', 'value': int(sales_a), 'target': int(sales_t), 'unit': currency_symbol},
         'tone': 'var(--accent)', 'delta': sd, 'deltaTone': sdt},
        {'data': {'label': f'{label_prefix}植入额', 'value': int(implant_a), 'target': int(implant_t), 'unit': currency_symbol},
         'tone': 'var(--success)', 'delta': id_, 'deltaTone': idt},
        {'data': {'label': f'{label_prefix}新项目', 'value': int(proj_a), 'target': int(proj_t), 'unit': ' 个'},
         'tone': 'var(--info)', 'delta': pd, 'deltaTone': pdt},
        {'data': {'label': f'{label_prefix}新客户', 'value': int(cust_a), 'target': int(cust_t), 'unit': ' 户'},
         'tone': 'var(--warn)', 'delta': cd, 'deltaTone': cdt},
    ]


def _kpi_task_items(user, start, end, prev_start, prev_end, label_prefix):
    """任务数 / 任务完成数(解决方案 + 产品经理共用)。"""
    from sqlalchemy import func
    from app import db
    from app.models.task import Task

    def _new(s, e):
        return db.session.query(func.count(Task.id)).filter(
            Task.assignee_id == user.id, Task.is_deleted == False,
            Task.created_at >= s, Task.created_at < e).scalar() or 0

    def _done(s, e):
        return db.session.query(func.count(Task.id)).filter(
            Task.assignee_id == user.id, Task.is_deleted == False,
            Task.status == 'completed', Task.completed_at >= s, Task.completed_at < e).scalar() or 0

    tn, tnp = _new(start, end), _new(prev_start, prev_end)
    td, tdp = _done(start, end), _done(prev_start, prev_end)
    return [
        _kpi_item(f'{label_prefix}任务', tn, 0, ' 个', tnp, 'var(--accent)'),
        _kpi_item(f'{label_prefix}任务完成', td, 0, ' 个', tdp, 'var(--success)'),
    ]


def _kpi_metrics_solution(user, start, end, prev_start, prev_end, label_prefix, target_months, cur):
    """解决方案经理:任务 + 植入额(我创建∪我确认,去重) + 项目参与度(确认/图纸/报价/跟进)。"""
    from sqlalchemy import func
    from app import db
    from app.models.quotation import Quotation
    from app.models.quotation_confirmation_task import QuotationConfirmationTask
    from app.models.system_diagram import SystemDiagram
    from app.models.action import Action

    confirmed_q = db.session.query(QuotationConfirmationTask.quotation_id).filter(
        QuotationConfirmationTask.assignee_id == user.id,
        QuotationConfirmationTask.status == 'confirmed')

    def _implant(s, e):  # 报价级:owner==我 OR 我确认过(单行天然去重)
        return db.session.query(func.coalesce(func.sum(Quotation.implant_total_amount), 0)).filter(
            db.or_(Quotation.owner_id == user.id, Quotation.id.in_(confirmed_q)),
            Quotation.created_at >= s, Quotation.created_at < e).scalar() or 0

    def _confirm(s, e):
        return db.session.query(func.count(QuotationConfirmationTask.id)).filter(
            QuotationConfirmationTask.assignee_id == user.id,
            QuotationConfirmationTask.status == 'confirmed',
            QuotationConfirmationTask.confirmed_at >= s, QuotationConfirmationTask.confirmed_at < e).scalar() or 0

    def _diagram(s, e):
        return db.session.query(func.count(SystemDiagram.id)).filter(
            SystemDiagram.owner_id == user.id,
            SystemDiagram.created_at >= s, SystemDiagram.created_at < e).scalar() or 0

    def _quote(s, e):
        return db.session.query(func.count(Quotation.id)).filter(
            Quotation.owner_id == user.id,
            Quotation.created_at >= s, Quotation.created_at < e).scalar() or 0

    def _action(s, e):
        return db.session.query(func.count(Action.id)).filter(
            Action.owner_id == user.id,
            Action.created_at >= s, Action.created_at < e).scalar() or 0

    im, imp = _implant(start, end), _implant(prev_start, prev_end)
    cf, cfp = _confirm(start, end), _confirm(prev_start, prev_end)
    dg, dgp = _diagram(start, end), _diagram(prev_start, prev_end)
    qc, qcp = _quote(start, end), _quote(prev_start, prev_end)
    ac, acp = _action(start, end), _action(prev_start, prev_end)
    items = _kpi_task_items(user, start, end, prev_start, prev_end, label_prefix)
    items += [
        _kpi_item(f'{label_prefix}植入额', im, 0, cur, imp, 'var(--info)'),
        _kpi_item(f'{label_prefix}报价确认', cf, 0, ' 个', cfp, 'var(--accent)'),
        _kpi_item(f'{label_prefix}图纸绘制', dg, 0, ' 张', dgp, 'var(--info)'),
        _kpi_item(f'{label_prefix}报价制作', qc, 0, ' 份', qcp, 'var(--success)'),
        _kpi_item(f'{label_prefix}项目跟进', ac, 0, ' 条', acp, 'var(--warn)'),
    ]
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
    items.append(_kpi_item(f'{label_prefix}负责产品植入额', im, 0, cur, imp, 'var(--info)'))
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
        _kpi_item('待审批报销', pending_cnt, 0, ' 单', 0, 'var(--accent)', delta=('—', 'neutral')),
        _kpi_item(f'{label_prefix}报销总额', cl, 0, cur, clp, 'var(--info)'),
        _kpi_item(f'{label_prefix}已支付', pd_, 0, cur, pdp, 'var(--success)'),
        _kpi_item('待支付', unpaid, 0, cur, 0, 'var(--warn)', delta=('—', 'neutral')),
    ]


_KPI_VARIANT_FUNC = {
    'default':  _kpi_one_period,
    'overview': _kpi_one_period,
    'solution': _kpi_metrics_solution,
    'product':  _kpi_metrics_product,
    'finance':  _kpi_metrics_finance,
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

    fn = _KPI_VARIANT_FUNC.get(variant, _kpi_one_period)
    return {
        'month':   fn(user, month_start, month_end, prev_m_start, prev_m_end,
                      f'{m}月', [m], currency_symbol),
        'quarter': fn(user, quarter_start, quarter_end, prev_q_start, prev_q_end,
                      f'Q{q} ', quarter_months, currency_symbol),
        'year':    fn(user, year_start, year_end, prev_y_start, prev_y_end,
                      f'{y}年 ', list(range(1, 13)), currency_symbol),
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

    # 漏斗顺序:植入 → 标前 → 标中 → 中标 → 签约
    # (PMA 业务阶段:embed/植入是早期"方案植入"阶段,不是终态)
    # discover/quoted 不进漏斗;lost/paused 算流失
    STAGES = [
        ('embed',      '植入'),
        ('pre_tender', '标前'),
        ('tendering',  '标中'),
        ('awarded',    '中标'),
        ('signed',     '签约'),
    ]
    funnel = []
    for key, label in STAGES:
        d = stage_data.get(key, {'count': 0, 'amount': 0})
        funnel.append({'stage': label, 'count': d['count'], 'amount': int(d['amount'])})

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
    'signed':     {'label': '签约', 'tone': 'success', 'pct': 90},
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
                'stage': meta['label'],
                'stageT': meta['tone'],
                'progress': meta['pct'],
                'dueIn': due_in if due_in is not None else 0,
                'dueRed': due_red,
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
            'none':      ('待审批', 'warn'),
            'pending':   ('待确认', 'warn'),
            'confirmed': ('已成交', 'success'),
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
                'draft': ('草稿', 'neutral'), 'pending': ('待审批', 'warn'),
                'approved': ('已通过', 'success'), 'paid': ('已支付', 'success'),
                'rejected': ('已驳回', 'danger'),
            }
            status_lbl, tone = stat_map.get(e.status, (e.status or '—', 'neutral'))
            recent.append({
                'id': f'EXP-{e.id}',
                'title': (e.expense_subject or e.notes or '报销单')[:24],
                'amount': float(e.total_amount or 0),
                'status': status_lbl,
                'tone': tone,
            })
    except Exception:
        pass

    return {
        'yearTotal': year_total,
        'yearTotalLast': year_total_last,  # 去年 1月→当前月 累计(真实同比基数)
        'monthly': monthly_stats,
        'months': ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
        'recent': recent,
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
            type_lbl = _WORKITEM_TYPE_LABEL.get(w.work_type, w.work_type or '')
            is_mine  = (w.owner_id == user.id)
            # 状态徽章:planned + 过期日 → 逾期(danger);planned → 计划(neutral);
            #          in_progress → 进行中(info);completed → 不标
            status_tag = None
            if w.status == 'in_progress':
                status_tag = {'label': '进行中', 'tone': 'info'}
            elif w.status == 'planned':
                if d and d < today:
                    status_tag = {'label': '逾期', 'tone': 'danger'}
                else:
                    status_tag = {'label': '计划', 'tone': 'neutral'}
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


def _build_tasks(user):
    """「任务」卡:我的任务(assignee==user),状态计数 + 前 6 项(未完成优先、按截止升序)。"""
    from app.models.task import Task
    tasks = Task.query.filter(Task.assignee_id == user.id, Task.is_deleted == False,
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
               (t.customer.company_name if t.customer else '—'))
        items.append({
            'id': t.id, 'title': t.title, 'project': rel,
            'due': t.due_date.strftime('%m-%d') if t.due_date else '—',
            'status': es, 'statusLabel': _TASK_STATUS_LABELS.get(es, es),
            'tone': _TASK_STATUS_TONE.get(es, 'neutral'), 'progress': prog,
            'route': f'/task/management?task={t.id}',
        })
    return {'items': items, 'counts': counts}


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
        return {'variant': 'product', 'sub': '我负责分类的产品', 'periods': periods}

    # solution:我创建 ∪ 我确认的报价,按报价明细产品聚合(同产品经理前端)
    from app.models.quotation_confirmation_task import QuotationConfirmationTask
    confirmed_q = db.session.query(QuotationConfirmationTask.quotation_id).filter(
        QuotationConfirmationTask.assignee_id == user.id,
        QuotationConfirmationTask.status == 'confirmed')
    for pk, (s, e) in _dash_periods().items():
        rows = db.session.query(
            QuotationDetail.product_name,
            func.count(QuotationDetail.id),
            func.coalesce(func.sum(QuotationDetail.implant_subtotal), 0),
        ).join(Quotation, Quotation.id == QuotationDetail.quotation_id)\
         .filter(db.or_(Quotation.owner_id == user.id, Quotation.id.in_(confirmed_q)),
                 QuotationDetail.implant_subtotal > 0,
                 Quotation.created_at >= s, Quotation.created_at < e)\
         .group_by(QuotationDetail.product_name)\
         .order_by(func.sum(QuotationDetail.implant_subtotal).desc()).all()
        total = sum(float(r[2]) for r in rows)
        items = [{'name': n or '—', 'count': int(c), 'amount': float(a)} for n, c, a in rows[:6]]
        periods[pk] = {'total': total, 'items': items}
    return {'variant': 'solution', 'sub': '我创建 / 确认的报价', 'periods': periods}


def role_layout(user):
    """角色 → 仪表盘卡片集合 + KPI 变体(唯一事实源)。

    返回 {'cards': [...卡片 key 按渲染顺序...], 'kpi_variant': '...'}。
    模板按 cards 决定显隐;build_dashboard 按 cards 决定算什么(只算要显示的)。
    卡片 key:todo / kpi / funnel / projects / quotes / expense / task / implant / worklog
    KPI 变体:default(销售) / solution / product / finance / overview
    """
    role = (user.role or '').lower()
    if role in ('ceo', 'admin'):
        return {'cards': ['todo', 'kpi', 'funnel', 'projects', 'quotes', 'expense', 'worklog'],
                'kpi_variant': 'overview'}
    if role in ('finance', 'finance_director', 'finace_director', 'finance_supervisor'):
        return {'cards': ['todo', 'kpi', 'expense', 'worklog'], 'kpi_variant': 'finance'}
    if role == 'solution_manager':
        return {'cards': ['todo', 'kpi', 'task', 'implant', 'expense', 'worklog'], 'kpi_variant': 'solution'}
    if role == 'product_manager':
        return {'cards': ['todo', 'kpi', 'task', 'implant', 'expense', 'worklog'], 'kpi_variant': 'product'}
    # 默认:销售及其余角色
    return {'cards': ['todo', 'kpi', 'funnel', 'projects', 'quotes', 'expense', 'worklog'],
            'kpi_variant': 'default'}


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
