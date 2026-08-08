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
            'name': _metric_name(code, it.get('name') or code, lang),
            'weight': f"{round(it.get('weight', 0) or 0)}%",
            'target': _disp(code, it.get('target'), True),
            'actual': _disp(code, it.get('actual')),
            'rate': (('满分' if lang == 'zh' else 'Full') if rev and rate >= 100 else f"{round(rate)}%"),
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
        if it['rate'] not in ('满分', 'Full') and r < 100:
            if lang == 'en':
                improvements.append(f"{it['name']} ({it['rate']}): below this quarter's target — targeted improvement suggested.")
            else:
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
        'diagnostics': None,   # 下方填充
        'improvements': improvements,
        'ai_analysis': None,   # 下方填充(AI 解读;无 key 回退规则版)
        'manager_name': _manager_name(user),
        'ceo_name': '',
        'reviewer': '主管' if lang == 'zh' else 'the reviewer',
        'manager_comment': '',
    }
    # 诊断明细(表格用) + AI 分析(基于诊断数据,无 key 回退规则版)
    ctx['diagnostics'] = _build_diagnostics(user, s, e, [it.get('code') for it in raw_items], lang)
    ctx['ai_analysis'] = _ai_analysis(ctx, lang)
    return ctx


def _ai_analysis(ctx, lang):
    """基于诊断明细让 AI 写"为何分低 + 怎么改"分析段(数字来自代码,AI 只解读)。
    无 ANTHROPIC_API_KEY 或调用失败 → 回退规则版要点。返回段落列表。"""
    L = (lambda zh, en: en if lang == 'en' else zh)
    items = ctx.get('items') or []
    diag = ctx.get('diagnostics') or {}
    under = [it for it in items
             if it.get('rate') not in ('满分', 'Full') and str(it.get('rate', '')).rstrip('%').replace('.', '', 1).isdigit()
             and float(str(it['rate']).rstrip('%')) < 100]

    # —— 规则版要点(回退/兜底) ——
    def _rule():
        out = []
        nc = diag.get('new_customers')
        if nc and nc['total'] > nc['qualified']:
            bad = nc['total'] - nc['qualified']
            out.append(L('新增客户：本季建档 %d 个，仅 %d 个合格；%d 个不合格——补齐联系人与跟进记录即可计入。'
                         % (nc['total'], nc['qualified'], bad),
                         'New customers: %d created, only %d qualified; %d short — add contacts and follow-ups to count.'
                         % (nc['total'], nc['qualified'], bad)))
        npj = diag.get('new_projects')
        if npj and npj['total'] > npj['qualified']:
            bad = npj['total'] - npj['qualified']
            out.append(L('新增项目：本季 %d 个，仅 %d 个合格；%d 个缺报备/跟进/关联客户/报价单。'
                         % (npj['total'], npj['qualified'], bad),
                         'New projects: %d this quarter, only %d qualified; %d missing approval/follow-up/customer/quotation.'
                         % (npj['total'], npj['qualified'], bad)))
        pa = diag.get('project_activity')
        if pa and pa['stale']:
            out.append(L('项目活跃度：在跟 %d 个，%d 个超 20 天未跟进，建议优先回访。'
                         % (pa['total'], pa['stale']),
                         'Project activity: %d ongoing, %d untouched >20 days — prioritise re-engagement.'
                         % (pa['total'], pa['stale'])))
        ca = diag.get('customer_activity')
        if ca and ca['total']:
            inactive = ca['total'] - ca['active']
            if inactive:
                out.append(L('客户活跃度：名下 %d 个客户中 %d 个不活跃(待跟进/沉睡/流失)，激活可提升活跃率。'
                             % (ca['total'], inactive),
                             'Customer activity: %d of %d customers inactive — re-activating lifts the rate.'
                             % (inactive, ca['total'])))
        if not out:
            out.append(L('各考核项均达标，保持当前节奏。', 'All items met target — keep up the pace.'))
        return out

    if not under:
        return _rule()

    # —— AI 版 ——
    try:
        import os, json
        if not os.environ.get('ANTHROPIC_API_KEY'):
            return _rule()
        from app.services.claude_vision_ocr import get_client, first_text
        # 精简喂给 AI 的事实(只给诊断结论,不给原始库)
        facts = {'score': ctx.get('total_score'),
                 'under_target': [{'name': it['name'], 'target': it['target'], 'actual': it['actual'], 'rate': it['rate']} for it in under],
                 'diagnostics': _diag_brief(diag)}
        sys_zh = ('你是绩效分析助理。基于给定的【真实诊断数据】解读该季度为何未达标、缺口在哪、如何改进。'
                  '严格只用提供的数字，不得编造或臆测其它数据。输出 3-5 条中文要点，每条一句话，聚焦"哪项缺什么、怎么补"，'
                  '务实、对人不苛刻。只输出 JSON 数组(字符串列表)，不要额外文字。')
        sys_en = ('You are a performance-analysis assistant. Using ONLY the given real diagnostic data, explain why targets '
                  'were missed, where the gaps are, and how to improve. Never invent numbers. Output 3-5 concise English bullet '
                  'points, each one sentence, focused on "which item lacks what, how to fix". Output ONLY a JSON array of strings.')
        msg = get_client().messages.create(
            model=os.environ.get('PERF_ANALYSIS_MODEL', 'claude-haiku-4-5-20251001'),
            max_tokens=600,
            system=(sys_en if lang == 'en' else sys_zh),
            messages=[{'role': 'user', 'content': json.dumps(facts, ensure_ascii=False)}],
        )
        raw = first_text(msg).strip()
        raw = raw.strip('`').lstrip('json').strip()
        arr = json.loads(raw)
        pts = [str(x).strip() for x in arr if str(x).strip()]
        return pts[:5] if pts else _rule()
    except Exception:
        return _rule()


def _diag_brief(diag):
    """把诊断明细压成 AI 可读的精简结构(含不合格记录的缺失原因,便于 AI 解读)。"""
    out = {}
    if diag.get('new_customers'):
        nc = diag['new_customers']
        out['new_customers'] = {'total': nc['total'], 'qualified': nc['qualified'],
                                'unqualified_reasons': [r['missing'] for r in nc['rows'] if not r['qualified']][:15]}
    if diag.get('new_projects'):
        npj = diag['new_projects']
        out['new_projects'] = {'total': npj['total'], 'qualified': npj['qualified'],
                               'unqualified_reasons': [r['missing'] for r in npj['rows'] if not r['qualified']][:15]}
    if diag.get('customer_activity'):
        ca = diag['customer_activity']
        out['customer_activity'] = {'total': ca['total'], 'active': ca['active'],
                                    'distribution': {x['label']: x['count'] for x in ca['dist']}}
    if diag.get('project_activity'):
        pa = diag['project_activity']
        out['project_activity'] = {'ongoing': pa['total'], 'stale_over_20d': pa['stale'],
                                   'most_stale': [(r['name'], r['days']) for r in pa['rows'][:8]]}
    return out


def _metric_name(code, fallback, lang):
    try:
        from app.helpers.metric_i18n import METRIC_I18N
        n = (METRIC_I18N.get(code) or {}).get('name') or {}
        return n.get(lang) or n.get('zh') or fallback
    except Exception:
        return fallback


def _role_label(role, lang):
    if not role:
        return '—'
    try:
        from app.utils.dictionary_helpers import get_role_display_name
        return get_role_display_name(role) or role
    except Exception:
        return role


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

# 英文口径（与中文一一对应）
METRIC_CRITERIA_EN = {
    'sales_amount': ('Sales (approved pricing)',
        ['Counted: pricing orders created by you with status "approved".',
         'Measure: total approved amount, mixed currencies converted to base currency.',
         'Attribution: falls in the quarter of the approval date.',
         'Excluded: draft / pending / rejected; orders created by others.']),
    'implant_amount': ('Implant value',
        ['Counted: vendor-product implant amount in quotations you own.',
         'Measure: sum of implant subtotals, converted to base currency.',
         'Attribution: falls in the quarter of the quotation creation date.']),
    'new_projects': ('New projects (qualified)',
        ['Counted (all required): ① not deleted ② approved registration (authorization code) ③ ≥1 follow-up ④ has linked customer ⑤ ≥1 quotation.',
         'Attribution: by first-qualified time (stamped once, never recomputed); later data only counts in the quarter it qualified.',
         'Owner: the project owner.']),
    'new_customers': ('New customers (qualified)',
        ['Counted (all required): ① not deleted ② name / address / type complete ③ ≥1 contact ④ ≥1 follow-up.',
         'Attribution: by first-qualified time, stamped once and never recomputed. Owner: the customer owner.']),
    'customer_activity_rate': ('Customer activity rate (level · snapshot)',
        ['Measure: share of your non-deleted customers in "highly active / active / normal"; maintained by a daily batch.',
         'Nature: snapshot — reflects the current level, independent of the quarter window.']),
    'project_activity_rate': ('Project activity rate (level · snapshot)',
        ['Measure: among your projects not in signed / paused / lost, the share followed up within the last 20 days.']),
    'fail_rate': ('Personal loss rate (reverse · level)',
        ['Measure: share of your projects lost this year mainly due to personal factors.',
         'Direction: lower is better — actual ≤ target scores full.']),
}


def _criteria_for(raw_items, lang):
    out = []
    src = METRIC_CRITERIA_EN if lang == 'en' else None
    for it in raw_items:
        code = it.get('code')
        if src and code in src:
            name, lines = src[code]
            out.append({'name': name, 'lines': lines})
            continue
        spec = METRIC_CRITERIA.get(code)
        if spec and 'zh' in spec:
            name, lines = spec['zh']
            out.append({'name': name, 'lines': lines})
    return out


_STATUS_LABEL = {
    'highly_active': ('高度活跃', 'Highly active'), 'active': ('活跃', 'Active'),
    'normal': ('正常', 'Normal'), 'to_follow': ('待跟进', 'To follow'),
    'pending': ('待跟进', 'To follow'), 'dormant': ('沉睡', 'Dormant'),
    'sleeping': ('沉睡', 'Dormant'), 'lost': ('流失', 'Churned'), 'churned': ('流失', 'Churned'),
    'inactive': ('不活跃', 'Inactive'),
}
_ACTIVE_STATUSES = ('highly_active', 'active', 'normal')


def _build_diagnostics(user, s, e, codes, lang):
    """诊断明细:对关键未达标项查"全量记录 + 合格判定 + 缺啥",既供报告表格也喂 AI。
    数字全部代码直查(准),AI 只在其上做解读。"""
    from app import db
    from sqlalchemy import func
    codes = set(codes or [])
    diag = {}
    L = (lambda zh, en: en if lang == 'en' else zh)

    # 新增客户诊断:本季 created_at 落入的、本人名下客户,逐条判定合格与缺失
    if 'new_customers' in codes:
        from app.models.customer import Company, Contact
        from app.models.action import Action
        rows = db.session.query(Company).filter(
            Company.owner_id == user.id, Company.is_deleted == False,
            Company.created_at >= s, Company.created_at < e).all()
        items = []
        for c in rows:
            nc = db.session.query(func.count(Contact.id)).filter(Contact.company_id == c.id).scalar() or 0
            na = db.session.query(func.count(Action.id)).filter(Action.company_id == c.id).scalar() or 0
            info_ok = bool((c.company_name or '').strip() and (c.address or '').strip() and (c.company_type or '').strip())
            miss = []
            if not info_ok: miss.append(L('资料不全', 'incomplete info'))
            if nc < 1: miss.append(L('缺联系人', 'no contact'))
            if na < 1: miss.append(L('缺跟进', 'no follow-up'))
            items.append({'name': c.company_name or L('(未命名)', '(unnamed)'),
                          'info_ok': info_ok, 'contacts': nc, 'actions': na,
                          'qualified': not miss, 'missing': '、'.join(miss) if miss else L('合格', 'qualified')})
        diag['new_customers'] = {
            'total': len(items), 'qualified': sum(1 for x in items if x['qualified']), 'rows': items}

    # 新增项目诊断
    if 'new_projects' in codes:
        from app.models.project import Project
        from app.models.action import Action
        from app.models.quotation import Quotation
        from app.models.project_customer_association import ProjectCustomerAssociation as _PCA
        rows = db.session.query(Project).filter(
            Project.owner_id == user.id, Project.is_deleted == False,
            Project.created_at >= s, Project.created_at < e).all()
        items = []
        for p in rows:
            na = db.session.query(func.count(Action.id)).filter(Action.project_id == p.id).scalar() or 0
            nq = db.session.query(func.count(Quotation.id)).filter(Quotation.project_id == p.id).scalar() or 0
            nassoc = db.session.query(func.count(_PCA.id)).filter(_PCA.project_id == p.id).scalar() or 0
            auth_ok = bool((p.authorization_code or '').strip())
            miss = []
            if not auth_ok: miss.append(L('未报备通过', 'not approved'))
            if na < 1: miss.append(L('缺跟进', 'no follow-up'))
            if nassoc < 1: miss.append(L('无关联客户', 'no linked customer'))
            if nq < 1: miss.append(L('缺报价单', 'no quotation'))
            items.append({'name': p.project_name or L('(未命名)', '(unnamed)'),
                          'auth_ok': auth_ok, 'actions': na, 'assoc': nassoc, 'quotes': nq,
                          'qualified': not miss, 'missing': '、'.join(miss) if miss else L('合格', 'qualified')})
        diag['new_projects'] = {
            'total': len(items), 'qualified': sum(1 for x in items if x['qualified']), 'rows': items}

    # 客户活跃度分布(快照)
    if 'customer_activity_rate' in codes:
        from app.models.customer import Company
        rows = dict(db.session.query(Company.status, func.count(Company.id))
                    .filter(Company.owner_id == user.id, Company.is_deleted == False)
                    .group_by(Company.status).all())
        total = sum(rows.values())
        dist = [{'label': _STATUS_LABEL.get(k, (k, k))[1 if lang == 'en' else 0],
                 'count': v, 'active': k in _ACTIVE_STATUSES}
                for k, v in sorted(rows.items(), key=lambda x: -x[1])]
        diag['customer_activity'] = {'total': total, 'active': sum(v for k, v in rows.items() if k in _ACTIVE_STATUSES), 'dist': dist}

    # 项目活跃度:在跟项目最近跟进距今天数(>20天为不活跃)
    if 'project_activity_rate' in codes:
        from app.models.project import Project
        from app.models.action import Action
        from sqlalchemy import or_
        _EXCL = ('signed', 'paused', 'lost')
        projs = Project.query.filter(
            Project.is_deleted == False, ~Project.current_stage.in_(_EXCL),
            or_(Project.owner_id == user.id, Project.vendor_sales_manager_id == user.id)).all()
        last = dict(db.session.query(Action.project_id, func.max(Action.date))
                    .filter(Action.project_id.in_([p.id for p in projs] or [0]))
                    .group_by(Action.project_id).all()) if projs else {}
        today = date.today()
        stale = []
        for p in projs:
            d = last.get(p.id)
            days = (today - d).days if d else None
            if days is None or days > 20:
                stale.append({'name': p.project_name or L('(未命名)', '(unnamed)'),
                              'days': days if days is not None else L('从无跟进', 'never')})
        stale.sort(key=lambda x: (x['days'] if isinstance(x['days'], int) else 99999), reverse=True)
        diag['project_activity'] = {'total': len(projs), 'stale': len(stale), 'rows': stale}

    return diag


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
