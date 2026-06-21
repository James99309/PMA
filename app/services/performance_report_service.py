# -*- coding: utf-8 -*-
"""季度绩效评估报告 · 取数服务（WeasyPrint 导出用）

build_report_context(user_id, year, quarter) → 渲染模板所需的完整上下文 dict。

数据全部来自系统统一口径，与仪表盘「我的 KPI」/绩效页同源：
- 明细表/得分：复用 PerformanceDashboardService.get_quarterly_scores（含合格采集 + 币种换算 + scoring_modes）
- 证据明细：按合格口径直查（新增客户/项目按 qualified_at 落季；销售=已批价单；植入=报价单明细）
- 口径文案：METRIC_CRITERIA（每指标"纳入/计量/时间归属"）
- 改进意见：达成率 < 100% 的项规则化提示（后续可换 AI 草稿）

CN/SG 通过 lang 切换（zh/en）；金额按本实例 Config（¥/万 或 $/K）显示。
"""
from datetime import datetime, date


# 金额类指标 code（显示加货币前缀 + 单位；其余按计数/百分比）
_AMOUNT_CODES = {
    'sales_amount', 'implant_amount', 'pm_implant_amount', 'pm_sales_amount',
    'se_implant_amount', 'se_sales_amount', 'team_sales_amount', 'team_implant_amount',
    'channel_sales_amount', 'channel_implant_amount',
}
_RATE_CODES = {
    'customer_activity_rate', 'project_activity_rate', 'team_customer_activity_rate',
    'team_project_activity_rate', 'channel_customer_activity_rate', 'channel_project_activity_rate',
    'se_response_rate', 'se_satisfaction', 'fail_rate', 'team_fail_rate', 'channel_fail_rate',
    'team_pass_rate',
}
_REVERSE_CODES = {'fail_rate', 'team_fail_rate', 'channel_fail_rate'}


def _qrange(year, quarter):
    sm = (quarter - 1) * 3 + 1
    s = datetime(year, sm, 1)
    e = datetime(year + 1, 1, 1) if quarter == 4 else datetime(year, sm + 3, 1)
    return s, e


def _fmt_amount(value_base, sym, divisor, unit):
    """基础币种金额 → 显示单位（¥万 / $K）。value_base 为元/美元。"""
    v = (value_base or 0) / float(divisor or 1)
    return f"{sym}{v:,.1f}{unit}"


def build_report_context(user_id, year, quarter, lang='zh'):
    from app.models.user import User
    from app.services.performance_dashboard_service import PerformanceDashboardService as P
    from config import Config

    user = User.query.get(user_id)
    if not user:
        return None
    sym = getattr(Config, 'CURRENCY_SYMBOL', '¥')
    divisor = float(getattr(Config, 'AMOUNT_DIVISOR', 10000))
    amt_unit = getattr(Config, 'AMOUNT_UNIT', '万')
    currency = getattr(Config, 'DEFAULT_CURRENCY', 'CNY')
    count_unit = ' 个' if lang == 'zh' else ''

    s, e = _qrange(year, quarter)
    today = date.today()

    # ── 明细表 + 总分（复用绩效页同源算法）──
    qs = (P.get_quarterly_scores(user_id, year) or {}).get(f'Q{quarter}', {}) or {}
    raw_items = qs.get('items', []) or []
    total_weight = qs.get('total_weight', 0) or 0
    # 归一到 0-100（按已考核权重），与卡片口径一致
    raw_score = qs.get('total_score', 0) or 0
    total_score = round(raw_score / total_weight * 100, 1) if total_weight else None

    def _disp(code, val, is_target=False):
        if code in _AMOUNT_CODES:
            return _fmt_amount(val, sym, divisor, amt_unit)
        if code in _RATE_CODES:
            return f"{round(val or 0, 0):.0f}%"
        return f"{round(val or 0)}{count_unit}"

    items = []
    for i, it in enumerate(raw_items, 1):
        code = it.get('code')
        rev = code in _REVERSE_CODES
        rate = it.get('achievement_rate', 0) or 0
        items.append({
            'idx': i,
            'name': it.get('name') or code,
            'weight': f"{round(it.get('weight', 0) or 0)}%",
            'target': _disp(code, it.get('target'), True),
            'actual': _disp(code, it.get('actual')),
            'rate': '满分' if rev and rate >= 100 else f"{round(rate)}%",
            'score': '—' if (it.get('weight', 0) or 0) == 0 else f"{round(it.get('weighted_score', 0) or 0, 1)}",
            'reverse': rev,
        })

    # ── 改进意见（规则化；后续可换 AI 草稿）──
    improvements = []
    for it in items:
        try:
            r = float(str(it['rate']).rstrip('%')) if it['rate'] not in ('满分',) else 100
        except ValueError:
            r = 100
        if it['rate'] != '满分' and r < 100:
            improvements.append(f"{it['name']}（{it['rate']}）：未达本季目标，建议针对性补强。")
    if not improvements:
        improvements.append("各考核项均达标，保持当前节奏。" if lang == 'zh' else "All items met target — keep up the pace.")

    ctx = {
        'lang': lang,
        'user_name': user.real_name or user.username,
        'role_name': _role_label(user.role, lang),
        'dept_name': user.department or '—',
        'company_name': user.company_name or '—',
        'year': year, 'quarter': quarter,
        'q_start': s.strftime('%Y-%m-%d'),
        'q_end': (e.replace(day=1) if False else e).strftime('%Y-%m-%d'),
        'currency': currency, 'amount_unit': f"{sym}/{amt_unit}",
        'generated_at': today.strftime('%Y-%m-%d'),
        'settlement_status': _settlement_status(user_id, year, quarter, lang),
        'items': items,
        'total_score': total_score if total_score is not None else '—',
        'assessed_weight': round(total_weight),
        'criteria': _criteria_for(raw_items, lang),
        'evidence': _build_evidence(user, s, e, sym, divisor, amt_unit),
        'improvements': improvements,
        'manager_name': _manager_name(user),
        'ceo_name': '',
        'reviewer': '主管' if lang == 'zh' else 'the reviewer',
        'manager_comment': '',
    }
    return ctx


def _role_label(role, lang):
    from app.helpers.metric_i18n import _lang  # noqa
    # 简化:直接返回 role（前端已有角色显示名映射,此处兜底）
    return role or '—'


def _settlement_status(user_id, year, quarter, lang):
    try:
        from app.models.performance_settlement import PerformanceSettlement as _PS
        st = _PS.query.filter_by(user_id=user_id, year=year, quarter=quarter).first()
        if not st:
            return '草稿 / 未发起' if lang == 'zh' else 'Draft / Not initiated'
        m = {'pending': ('待审批', 'Pending'), 'approved': ('已通过 · 锁定', 'Approved · Locked'),
             'rejected': ('已驳回', 'Rejected')}
        return m.get(st.status, (st.status, st.status))[0 if lang == 'zh' else 1]
    except Exception:
        return '—'


def _manager_name(user):
    try:
        from app.models.affiliation import Affiliation
        from app.models.user import User
        aff = Affiliation.query.filter_by(user_id=user.id).first()
        if aff and aff.owner_id:
            mgr = User.query.get(aff.owner_id)
            if mgr:
                return mgr.real_name or mgr.username
    except Exception:
        pass
    return ''


# 每指标"纳入/计量/时间归属"口径文案（与 kpi_actual_service 实际一致）
METRIC_CRITERIA = {
    'sales_amount': {'zh': ('销售额（已批价）',
        ['纳入：本人创建、状态为「已批价通过」的批价单。',
         '计量：批价总额，多币种折算本位币。',
         '时间归属：按批准时间落入本季。',
         '不纳入：草稿 / 审批中 / 已驳回；他人创建。'])},
    'implant_amount': {'zh': ('植入价值',
        ['纳入：本人 owner 报价单中厂商产品的植入额。',
         '计量：植入小计合计，多币种折算本位币。',
         '时间归属：按报价单创建时间落入本季。'])},
    'new_projects': {'zh': ('新增项目（合格）',
        ['纳入（须全部满足）：① 未删除 ② 报备通过（授权编号） ③ ≥1 跟进 ④ 有关联客户 ⑤ ≥1 报价单。',
         '时间归属：按首次达标时间落季，盖戳后永不重算；补资料只计入达标当季。',
         '归属人：项目负责人（owner）。'])},
    'new_customers': {'zh': ('新增客户（合格）',
        ['纳入（须全部满足）：① 未删除 ② 名称/地址/类型齐全 ③ ≥1 联系人 ④ ≥1 跟进。',
         '时间归属：按首次达标时间落季，盖戳后永不重算。归属人为客户负责人（owner）。'])},
    'customer_activity_rate': {'zh': ('客户活跃率（水平 · 快照）',
        ['计量：名下未删除客户中「高度活跃/活跃/正常」占比；状态由每日跑批维护。',
         '特性：快照型，反映当前水平，与季度窗口无关。'])},
    'project_activity_rate': {'zh': ('项目活跃率（水平 · 快照）',
        ['计量：本人负责、未处于 签约/暂停/失败 的项目中，最近一次跟进 ≤20 天 的占比。'])},
    'fail_rate': {'zh': ('个人丢单率（反向 · 水平）',
        ['计量：本人负责项目中，本年「个人因素为主」失败项目占比。',
         '方向：越低越好，实际 ≤ 目标即满分。'])},
}


def _criteria_for(raw_items, lang):
    out = []
    for it in raw_items:
        code = it.get('code')
        spec = METRIC_CRITERIA.get(code)
        if spec and 'zh' in spec:
            name, lines = spec['zh']
            out.append({'name': name, 'lines': lines})
    return out


def _build_evidence(user, s, e, sym, divisor, amt_unit):
    """证据明细（附录）：新增客户/项目清单、销售批价单、植入明细、活跃率分子分母。"""
    from app import db
    from sqlalchemy import func, text
    ev = {'new_customers': [], 'new_projects': [], 'sales_orders': [],
          'implant_details': [], 'activity': {}}

    # 新增客户（按 qualified_at 落季）
    from app.models.customer import Company, Contact
    from app.models.action import Action
    cust = db.session.query(Company).filter(
        Company.owner_id == user.id, Company.is_deleted == False,
        Company.qualified_at.isnot(None), Company.qualified_at >= s, Company.qualified_at < e
    ).all()
    for c in cust:
        nc = db.session.query(func.count(Contact.id)).filter(Contact.company_id == c.id).scalar() or 0
        na = db.session.query(func.count(Action.id)).filter(Action.company_id == c.id).scalar() or 0
        ev['new_customers'].append({
            'name': c.company_name, 'type': c.company_type or '—',
            'contacts': nc, 'actions': na,
            'qualified_at': c.qualified_at.strftime('%Y-%m-%d') if c.qualified_at else '—'})

    # 新增项目（按 qualified_at 落季）
    from app.models.project import Project
    from app.models.quotation import Quotation
    from app.models.project_customer_association import ProjectCustomerAssociation as _PCA
    projs = db.session.query(Project).filter(
        Project.owner_id == user.id, Project.is_deleted == False,
        Project.qualified_at.isnot(None), Project.qualified_at >= s, Project.qualified_at < e
    ).all()
    for p in projs:
        na = db.session.query(func.count(Action.id)).filter(Action.project_id == p.id).scalar() or 0
        nq = db.session.query(func.count(Quotation.id)).filter(Quotation.project_id == p.id).scalar() or 0
        cust_row = db.session.query(_PCA).filter(_PCA.project_id == p.id).first()
        ev['new_projects'].append({
            'name': p.project_name, 'auth_code': p.authorization_code or '—',
            'customer': '—', 'actions': na, 'quotations': nq,
            'qualified_at': p.qualified_at.strftime('%Y-%m-%d') if p.qualified_at else '—'})

    # 销售（已批价单）
    from app.models.pricing_order import PricingOrder
    from app.services.multi_currency_aggregation import MultiCurrencyAggregationService as _MC
    pos = db.session.query(PricingOrder).filter(
        PricingOrder.created_by == user.id, PricingOrder.status == 'approved',
        PricingOrder.approved_at >= s, PricingOrder.approved_at < e
    ).all()
    for po in pos:
        conv = _MC.convert_single(po.pricing_total_amount or 0, po.currency)
        ev['sales_orders'].append({
            'no': po.order_number or f'PO-{po.id}', 'amount': po.pricing_total_amount or 0,
            'cur': po.currency or currency_default(), 'converted': _fmt_amount(conv, sym, divisor, amt_unit),
            'approved_at': po.approved_at.strftime('%Y-%m-%d') if po.approved_at else '—'})

    # 活跃率分子分母（客户）
    rows = dict(db.session.query(Company.status, func.count(Company.id))
                .filter(Company.owner_id == user.id, Company.is_deleted == False)
                .group_by(Company.status).all())
    total = sum(rows.values())
    active = sum(v for k, v in rows.items() if k in ('highly_active', 'active', 'normal'))
    ev['activity']['customer'] = {'num': active, 'den': total,
                                  'rate': round(active / total * 100, 1) if total else 0}
    return ev


def currency_default():
    from config import Config
    return getattr(Config, 'DEFAULT_CURRENCY', 'CNY')
