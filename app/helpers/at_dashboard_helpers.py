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
def _get_dash_scope(user):
    """决定仪表盘第二个 scope chip 的元数据。

    返回 {
      'mine':       {'key':'mine','label':'我的','owner_ids':[user.id]},
      'secondary':  {'key':'team|company|system','label':'团队|公司|系统','owner_ids':[...] or None} | None
    }

    规则(按优先级):
      - admin                                  → 系统(owner_ids=None,代表全平台)
      - quotation 权限级别 = 'company' / CEO角色 → 公司
      - is_department_manager=True             → 团队(部门内)
      - 其他                                   → 无 secondary(普通员工只看我的)
    """
    mine = {'key': 'mine', 'label': '我的', 'owner_ids': [user.id]}
    secondary = None
    try:
        role = (getattr(user, 'role', '') or '').lower()
        if role == 'admin':
            secondary = {'key': 'system', 'label': '系统', 'owner_ids': None}
        else:
            # 走 PMA 权限系统(quotation 模块做主键判断,3 卡常用)
            level = None
            try:
                level = user.get_permission_level('quotation')
            except Exception:
                pass
            if role == 'ceo' or level == 'company':
                from app.utils.access_control import get_company_user_ids
                secondary = {
                    'key': 'company', 'label': '公司',
                    'owner_ids': get_company_user_ids(user, include_affiliations=True),
                }
            elif getattr(user, 'is_department_manager', False):
                from app.utils.access_control import get_department_user_ids
                secondary = {
                    'key': 'team', 'label': '团队',
                    'owner_ids': get_department_user_ids(user, include_affiliations=True),
                }
    except Exception as e:
        import logging; logging.warning(f'_get_dash_scope err: {e}')
    return {'mine': mine, 'secondary': secondary}


# ─── 待办 8 条 ─────────────────────────────────────────
def _build_todos(user):
    """
    待办列表 — 完全复用老 PMA 后端逻辑,不自造规则:
      1) 待审批:get_user_pending_approvals(user.id) — 已处理 dynamic approver
      2) 待确认产品:QuotationConfirmationTask(老消息面板的"待办任务"实体)
      3) @我提及:Message 表的 worklog_mention / task_reply / task_assigned(未读)
      4) 客户跟进:Action 我 owner 超 30 天(MVP 规则,无对应老后端)
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

    try:
        from app.models.action import Action
        cutoff = datetime.now() - timedelta(days=30)
        for a in Action.query.filter(
            Action.owner_id == user.id, Action.created_at < cutoff
        ).order_by(Action.created_at.asc()).limit(2).all():
            days = (datetime.now() - a.created_at).days if a.created_at else 0
            out.append({
                'id': f'A{a.id}', 'type': 'action', 'typeLabel': '客户跟进', 'tone': 'danger',
                'title': f'{(a.company.company_name if a.company else "客户")} · {days} 天未沟通',
                'meta': f'上次:{a.created_at.strftime("%m-%d") if a.created_at else "—"}',
                'who': '—', 'when': '—', 'route': '#', 'urgent': False,
            })
    except Exception:
        pass

    return out


# ─── KPI ─── 直查业务表实时聚合(避开 PMA 内置 KPI 配置的字段名 bug)
#            返回 3 套粒度:本月 / 本季 / 本年,前端 tab 切换显示
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
    return {
        'salesGoal':  {'label': f'{label_prefix}销售额',
                       'value': int(sales_a), 'target': int(sales_t), 'unit': currency_symbol,
                       'delta': sd, 'deltaTone': sdt, 'tone': 'var(--accent)'},
        'quoteWin':   {'label': f'{label_prefix}植入额',
                       'value': int(implant_a), 'target': int(implant_t), 'unit': currency_symbol,
                       'delta': id_, 'deltaTone': idt, 'tone': 'var(--success)'},
        'activeCust': {'label': f'{label_prefix}新项目',
                       'value': int(proj_a), 'target': int(proj_t), 'unit': ' 个',
                       'delta': pd, 'deltaTone': pdt, 'tone': 'var(--info)'},
        'budget':     {'label': f'{label_prefix}新客户',
                       'value': int(cust_a), 'target': int(cust_t), 'unit': ' 户',
                       'delta': cd, 'deltaTone': cdt, 'tone': 'var(--warn)'},
    }


def _build_kpis(user, currency_symbol='¥'):
    """返回 3 套粒度: month / quarter / year(前端 tab 切换)"""
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

    return {
        'month':   _kpi_one_period(user, month_start, month_end, prev_m_start, prev_m_end,
                                    f'{m}月', [m], currency_symbol),
        'quarter': _kpi_one_period(user, quarter_start, quarter_end, prev_q_start, prev_q_end,
                                    f'Q{q} ', quarter_months, currency_symbol),
        'year':    _kpi_one_period(user, year_start, year_end, prev_y_start, prev_y_end,
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
def _build_funnel(user, owner_ids=None):
    """
    数据源:Project.owner_id IN owner_ids (默认 [user.id])
            Project.created_at >= 今天 - 12 个月
    owner_ids=None → 全平台(admin/系统态)
    """
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from app import db
    from app.models.project import Project
    from app.models.quotation import Quotation

    if owner_ids is None and (getattr(user, 'role', '') or '').lower() != 'admin':
        owner_ids = [user.id]

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
    if owner_ids is not None:
        q = q.filter(Project.owner_id.in_(owner_ids))
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


def _build_projects(user, owner_ids=None):
    """owner_ids 控制范围;None+非admin → [user.id];admin/系统态可传 None=全部"""
    from datetime import date
    items = []
    due_soon_count = 0
    today = date.today()
    if owner_ids is None and (getattr(user, 'role', '') or '').lower() != 'admin':
        owner_ids = [user.id]
    try:
        from app.models.project import Project
        q = Project.query
        if owner_ids is not None:
            q = q.filter(Project.owner_id.in_(owner_ids))
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
def _build_quotes(user, owner_ids=None):
    """owner_ids 控制范围;None+非admin → [user.id]"""
    quotes, counts = [], {'newThisMonth': 0, 'awaitConfirm': 0, 'wonThisMonth': 0}
    if owner_ids is None and (getattr(user, 'role', '') or '').lower() != 'admin':
        owner_ids = [user.id]
    try:
        from app.models.quotation import Quotation
        base = Quotation.query
        if owner_ids is not None:
            base = base.filter(Quotation.owner_id.in_(owner_ids))
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
def _build_expense(user, monthly_stats, year_total, currency_symbol, owner_ids=None):
    """报销:owner_ids 控制范围;None+非admin → [user.id]
       注意:报销默认权限规则是个人财务隔离,但仪表盘"团队"chip 是显式仪表盘聚合视角,
       由调用方(build_dashboard)按 scope 显式传入 owner_ids。
       monthly_stats/year_total 由 main.py 算好,只用于"我的";"团队"态需要重算。
    """
    from app.models.expense import Expense
    from sqlalchemy import func, extract
    from app import db

    if owner_ids is None and (getattr(user, 'role', '') or '').lower() != 'admin':
        owner_ids = [user.id]
    is_mine_scope = (owner_ids == [user.id])

    now = datetime.now()

    # 团队/公司/系统态:重算 monthly + year_total(我的态用 main.py 传入的)
    if not is_mine_scope:
        q = db.session.query(Expense).filter(Expense.is_deleted == False)
        if owner_ids is not None:
            q = q.filter(Expense.owner_id.in_(owner_ids))
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
        if owner_ids is not None:
            q_last = q_last.filter(Expense.owner_id.in_(owner_ids))
        year_total_last = float(q_last.scalar() or 0)
    except Exception:
        pass

    recent = []
    try:
        rq = Expense.query.filter(Expense.is_deleted == False)
        if owner_ids is not None:
            rq = rq.filter(Expense.owner_id.in_(owner_ids))
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
def role_layout(user):
    role = (user.role or '').lower()
    if role == 'ceo':
        return {'row1': ['funnel', 'kpi', 'todo'], 'row2': ['projects', 'quotes', 'expense'], 'row3': ['worklog']}
    if role in ('finance_director', 'finace_director', 'finance'):
        return {'row1': ['todo', 'expense', 'kpi'], 'row2': ['quotes', 'projects', 'funnel'], 'row3': ['worklog']}
    if role in ('sm', 'sales_manager'):
        return {'row1': ['todo', 'quotes', 'funnel'], 'row2': ['kpi', 'projects', 'expense'], 'row3': ['worklog']}
    return {'row1': ['todo', 'kpi', 'funnel'], 'row2': ['projects', 'quotes', 'expense'], 'row3': ['worklog']}


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
    scope = _get_dash_scope(user)

    # 我的(默认)
    mine_owner_ids = scope['mine']['owner_ids']
    funnel_m, conv_m, yoy_m, loss_m = _build_funnel(user, mine_owner_ids)
    projects_m, proj_counts_m = _build_projects(user, mine_owner_ids)
    quotes_m, quote_counts_m = _build_quotes(user, mine_owner_ids)
    expense_m = _build_expense(user, monthly_stats or [0]*12, year_total or 0, expense_currency_symbol, mine_owner_ids)

    # 团队/公司/系统(若用户有权限)
    funnel_s = projects_s = quotes_s = expense_s = None
    conv_s = yoy_s = 0
    loss_s = None
    proj_counts_s = quote_counts_s = None
    if scope['secondary']:
        sec_ids = scope['secondary']['owner_ids']
        funnel_s, conv_s, yoy_s, loss_s = _build_funnel(user, sec_ids)
        projects_s, proj_counts_s = _build_projects(user, sec_ids)
        quotes_s, quote_counts_s = _build_quotes(user, sec_ids)
        expense_s = _build_expense(user, monthly_stats or [0]*12, year_total or 0, expense_currency_symbol, sec_ids)

    return {
        'currency': db_currency_symbol,  # 顶层货币 — 用于所有统计(漏斗/项目/报价/KPI),跟 PMA_DB_TYPE 走
        'todos': _build_todos(user),
        'kpis':  _build_kpis(user, db_currency_symbol),
        'todayStats': _build_today_stats(user),
        # 默认填 mine,兼容旧模板
        'funnel': funnel_m,
        'funnelConversion': conv_m,
        'funnelLoss': loss_m,
        'funnelYoY': yoy_m,
        'projects': projects_m,
        'projectCounts': proj_counts_m,
        'quotes': quotes_m,
        'quoteCounts': quote_counts_m,
        'expense': expense_m,
        # 新:scope 元数据 + 两套数据(secondary 可为 None)
        'scope': scope,
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
        'worklog': _build_worklog(user),
    }
