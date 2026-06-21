# -*- coding: utf-8 -*-
"""KPI 实际值采集 —— 全系统唯一后端事实源(2026-06-21 收口)。

原散落于 at_dashboard_helpers.py(前端仪表盘 helper),现收口为独立后端服务,
供 仪表盘卡 / 个人配置实际值 / 绩效页季度得分(get_quarterly_scores) / goal_achievement 共用,
杜绝「同一指标多套口径」(如新建客户合格过滤前端有后端无)。

_KPI_ACTUAL_FNS[code](user, start, end) -> float:本期窗口实际值;
  金额类已按各记录币种换算到本实例默认币种;率/快照类按窗口直算;
  新建客户/项目走合格过滤(_qualified_*_filters)。
所有依赖均函数内惰性 import,避免循环依赖。
"""

def _sum_money(query, amount_col, currency_col):
    """金额按各记录币种换算到本实例默认币种后求和(公共组件 MultiCurrencyAggregationService)。
    CN 同币种=无操作;SG 多币种(USD/MYR/...)→ 统一换算到 USD,使与 USD 目标可比。
    query: 已 filter/join、未聚合的 SQLAlchemy Query。"""
    from app.services.multi_currency_aggregation import MultiCurrencyAggregationService
    return float(MultiCurrencyAggregationService.sum_converted(query, amount_col, currency_col) or 0)


def _conv_money(amount, from_currency):
    """单笔金额换算到本实例默认币种(裸 SQL 采集器按币种分组后逐档调用)。"""
    from app.services.multi_currency_aggregation import MultiCurrencyAggregationService
    return float(MultiCurrencyAggregationService.convert_single(amount or 0, from_currency) or 0)



def _act_sales(user, s, e):
    from app import db
    from app.models.pricing_order import PricingOrder
    q = db.session.query(PricingOrder).filter(
        PricingOrder.status == 'approved', PricingOrder.created_by == user.id,
        PricingOrder.approved_at >= s, PricingOrder.approved_at < e)
    return _sum_money(q, PricingOrder.pricing_total_amount, PricingOrder.currency)

def _act_implant(user, s, e):
    from app import db
    from app.models.quotation import Quotation
    q = db.session.query(Quotation).filter(
        Quotation.owner_id == user.id,
        Quotation.created_at >= s, Quotation.created_at < e)
    return _sum_money(q, Quotation.implant_total_amount, Quotation.currency)

# ── 合格「新建客户/项目」统一口径(2026-06-21,个人/团队/渠道共用) ──
def _qualified_customer_filters():
    """合格新客户:名称/地址/公司类型齐全 + ≥1 联系人 + 客户下跟进(Action)≥1 条
    (2026-06-21 标准下调:跟进从 ≥2 改为 ≥1,代表至少接触过客户一次即可)。"""
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company, Contact
    from app.models.action import Action
    contact_exists = db.session.query(Contact.id).filter(Contact.company_id == Company.id).exists()
    action_cnt = (db.session.query(func.count(Action.id))
                  .filter(Action.company_id == Company.id)
                  .correlate(Company).scalar_subquery())
    return [
        Company.is_deleted == False,
        Company.company_name.isnot(None), func.trim(Company.company_name) != '',
        Company.address.isnot(None), func.trim(Company.address) != '',
        Company.company_type.isnot(None), func.trim(Company.company_type) != '',
        contact_exists, action_cnt >= 1,
    ]


def _qualified_project_filters():
    """合格新项目:报备通过(有授权编号) + ≥1 跟进记录 + 有关联客户。"""
    from app import db
    from sqlalchemy import func
    from app.models.project import Project
    from app.models.action import Action
    from app.models.project_customer_association import ProjectCustomerAssociation as _PCA
    act_exists = db.session.query(Action.id).filter(Action.project_id == Project.id).exists()
    cust_exists = db.session.query(_PCA.id).filter(_PCA.project_id == Project.id).exists()
    return [
        Project.is_deleted == False,
        Project.authorization_code.isnot(None), func.trim(Project.authorization_code) != '',
        act_exists, cust_exists,
    ]


def _act_new_projects(user, s, e):
    """合格新项目(我名下 owner_id 本期新建)。"""
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        Project.owner_id == user.id,
        Project.created_at >= s, Project.created_at < e,
        *_qualified_project_filters(),
    ).scalar() or 0

def _act_new_customers(user, s, e):
    """合格新客户(我名下 owner_id 本期新建)。"""
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.owner_id == user.id,
        Company.created_at >= s, Company.created_at < e,
        *_qualified_customer_filters(),
    ).scalar() or 0

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
    q = db.session.query(QuotationDetail).join(
        Quotation, Quotation.id == QuotationDetail.quotation_id).join(
        Product, Product.product_mn == QuotationDetail.product_mn).filter(
        Product.category_id.in_(cat_ids),
        Quotation.created_at >= s, Quotation.created_at < e)
    return _sum_money(q, QuotationDetail.implant_subtotal, Quotation.currency)

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
        -- 按币种分组(植入额),供 Python 换算到本实例币种
        SELECT COALESCE(jsonb_object_agg(cur, amt), '{}'::jsonb) AS by_cur FROM (
            SELECT q.currency AS cur, SUM(qd.quantity * qd.market_price) AS amt
            FROM quotation_details qd
            JOIN quotations q ON qd.quotation_id = q.id
            JOIN se_projects sp ON q.project_id = sp.project_id
            JOIN products p ON qd.product_mn = p.product_mn
            WHERE p.is_vendor_product = true AND q.created_at >= :s AND q.created_at < :e
            GROUP BY q.currency
        ) t
    ),
    sa AS (
        -- 按币种分组(批价额)
        SELECT COALESCE(jsonb_object_agg(cur, amt), '{}'::jsonb) AS by_cur FROM (
            SELECT po.currency AS cur, SUM(po.pricing_total_amount) AS amt
            FROM pricing_orders po
            JOIN se_projects sp ON po.project_id = sp.project_id
            WHERE po.status = 'approved' AND po.approved_at >= :s AND po.approved_at < :e
            GROUP BY po.currency
        ) t
    )
    SELECT c.cnt, spt.sup AS sup, ql.quality, im.by_cur AS implant, sa.by_cur AS sales
    FROM c, spt, ql, im, sa
"""

def _se_window(user, s, e, _cache={}):
    from sqlalchemy import text
    from app import db
    key = (user.id, s, e)
    if key not in _cache:
        r = db.session.execute(text(_SE_WINDOW_SQL), {'uid': user.id, 's': s, 'e': e}).fetchone()
        _cache.clear() if len(_cache) > 64 else None
        import json as _json
        def _cmap(v):
            """{币种:金额} jsonb → 换算到本实例币种后合计(CN 同币种=无操作;SG→USD)。"""
            d = v if isinstance(v, dict) else (_json.loads(v) if v else {})
            return sum(_conv_money(amt, cur) for cur, amt in d.items())
        _cache[key] = {
            'se_confirm_count': int(r.cnt or 0),
            'se_sales_support': int(r.sup or 0),
            'se_confirm_quality': round(float(r.quality or 0), 2),  # 植入品质(推荐系数加权均值)
            'se_implant_amount': _cmap(r.implant),
            'se_sales_amount': _cmap(r.sales),
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
        SELECT po.currency AS cur, COALESCE(SUM(pod.total_price), 0) AS amt
        FROM pricing_order_details pod
        JOIN pricing_orders po ON pod.pricing_order_id = po.id
        JOIN product_pm pp ON pod.product_mn = pp.product_mn
        WHERE pp.pm_id = :uid AND po.status = 'approved'
          AND po.approved_at >= :s AND po.approved_at < :e
        GROUP BY po.currency
    """), {'uid': user.id, 's': s, 'e': e}).fetchall()
    # 跨币种换算到本实例币种(CN 同币种=无操作;SG MYR→USD)
    return sum(_conv_money(row.amt, row.cur) for row in r)

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
    from app import db
    from app.models.pricing_order import PricingOrder
    q = db.session.query(PricingOrder).filter(
        PricingOrder.status == 'approved',
        PricingOrder.created_by.in_(_dept_member_ids(user)),
        PricingOrder.approved_at >= s, PricingOrder.approved_at < e)
    return _sum_money(q, PricingOrder.pricing_total_amount, PricingOrder.currency)


def _act_team_implant(user, s, e):
    from app import db
    from app.models.quotation import Quotation
    q = db.session.query(Quotation).filter(
        Quotation.owner_id.in_(_dept_member_ids(user)),
        Quotation.created_at >= s, Quotation.created_at < e)
    return _sum_money(q, Quotation.implant_total_amount, Quotation.currency)


def _act_team_new_projects(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        Project.owner_id.in_(_dept_member_ids(user)),
        Project.created_at >= s, Project.created_at < e,
        *_qualified_project_filters(),
    ).scalar() or 0


def _act_team_new_customers(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.owner_id.in_(_dept_member_ids(user)),
        Company.created_at >= s, Company.created_at < e,
        *_qualified_customer_filters(),
    ).scalar() or 0


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
    from app import db
    from app.models.pricing_order import PricingOrder
    from app.models.project import Project
    q = (db.session.query(PricingOrder)
         .join(Project, Project.id == PricingOrder.project_id)
         .filter(*_channel_project_filter(),
                 PricingOrder.status == 'approved',
                 PricingOrder.approved_at >= s, PricingOrder.approved_at < e))
    return _sum_money(q, PricingOrder.pricing_total_amount, PricingOrder.currency)


def _act_channel_implant(user, s, e):
    from app import db
    from app.models.quotation import Quotation
    from app.models.project import Project
    q = (db.session.query(Quotation)
         .join(Project, Project.id == Quotation.project_id)
         .filter(*_channel_project_filter(),
                 Quotation.created_at >= s, Quotation.created_at < e))
    return _sum_money(q, Quotation.implant_total_amount, Quotation.currency)


def _act_channel_new_projects(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        *_channel_project_filter(),
        Project.created_at >= s, Project.created_at < e,
        *_qualified_project_filters(),
    ).scalar() or 0


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
        Company.owner_id.in_(_dealer_user_ids()),
        Company.created_at >= s, Company.created_at < e,
        *_qualified_customer_filters(),
    ).scalar() or 0


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
