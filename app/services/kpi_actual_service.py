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
    """植入额(2026-06-30 口径修正):
       ① 归属按【项目拥有人】(Project.owner_id),不看报价 owner(SE/他人代写报价不影响归属);
       ② 仅计【有确认过】的报价(confirmed_by 留痕),不看当前徽章状态('reconfirm' 仍算)。"""
    from app import db
    from app.models.quotation import Quotation
    from app.models.project import Project
    q = (db.session.query(Quotation)
         .join(Project, Project.id == Quotation.project_id)
         .filter(Project.owner_id == user.id,
                 Quotation.confirmed_by.isnot(None),
                 Quotation.created_at >= s, Quotation.created_at < e))
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
    """合格新项目:报备通过(有授权编号) + ≥1 跟进记录 + 有关联客户 + ≥1 报价单
    (2026-06-21 新增报价单条件:无报价单不算合格新项目)。"""
    from app import db
    from sqlalchemy import func
    from app.models.project import Project
    from app.models.action import Action
    from app.models.quotation import Quotation
    from app.models.project_customer_association import ProjectCustomerAssociation as _PCA
    act_exists = db.session.query(Action.id).filter(Action.project_id == Project.id).exists()
    cust_exists = db.session.query(_PCA.id).filter(_PCA.project_id == Project.id).exists()
    quo_exists = db.session.query(Quotation.id).filter(Quotation.project_id == Project.id).exists()
    return [
        Project.is_deleted == False,
        Project.authorization_code.isnot(None), func.trim(Project.authorization_code) != '',
        act_exists, cust_exists, quo_exists,
    ]


def _collect_affected(session):
    """在 before_flush 阶段(new/dirty 仍完整)收集受影响的 company_id/project_id;
    新建的 Company/Project 此时尚无 id → 暂存对象引用,留待 after_commit 取 id。
    结果累加进 session.info(同一事务多次 flush 累计)。"""
    from app.models.customer import Company, Contact
    from app.models.action import Action
    from app.models.project import Project
    from app.models.quotation import Quotation
    from app.models.project_customer_association import ProjectCustomerAssociation as _PCA
    cids = session.info.setdefault('_qa_c', set())
    pids = session.info.setdefault('_qa_p', set())
    objs = session.info.setdefault('_qa_objs', [])
    for obj in list(session.new) + list(session.dirty):
        if isinstance(obj, Company):
            if obj.id:
                cids.add(obj.id)
            else:
                objs.append(obj)   # 新建,flush 后才有 id
        elif isinstance(obj, Project):
            if obj.id:
                pids.add(obj.id)
            else:
                objs.append(obj)
        elif isinstance(obj, Contact):
            if getattr(obj, 'company_id', None): cids.add(obj.company_id)
        elif isinstance(obj, Action):
            if getattr(obj, 'company_id', None): cids.add(obj.company_id)
            if getattr(obj, 'project_id', None): pids.add(obj.project_id)
        elif isinstance(obj, Quotation):
            if getattr(obj, 'project_id', None): pids.add(obj.project_id)
        elif isinstance(obj, _PCA):
            if getattr(obj, 'project_id', None): pids.add(obj.project_id)


def _stamp_now_for(company_ids, project_ids):
    """对【受影响 + 现已达标 + 未盖戳】的客户/项目,写 qualified_at = now()(实时,真实达标时刻);
    定向到指定 id,仅写 NULL 的。条件口径同合格过滤(含项目≥1报价单)。
    用独立连接 db.engine.begin()(自带新事务):因本函数在 after_commit 内调用,
    此时原 session 处于 committed 态不能再发 SQL;独立连接也与 session 事件无关,天然无递归。"""
    from app import db
    from sqlalchemy import text, bindparam
    from datetime import datetime
    now = datetime.now()
    cust_stmt = text("""
        UPDATE companies c SET qualified_at = :now
        WHERE c.id IN :ids AND c.qualified_at IS NULL AND c.is_deleted = false
          AND c.company_name IS NOT NULL AND btrim(c.company_name) <> ''
          AND c.address      IS NOT NULL AND btrim(c.address)      <> ''
          AND c.company_type IS NOT NULL AND btrim(c.company_type) <> ''
          AND EXISTS (SELECT 1 FROM contacts ct WHERE ct.company_id=c.id)
          AND (SELECT count(*) FROM actions a WHERE a.company_id=c.id) >= 1
    """).bindparams(bindparam('ids', expanding=True))
    proj_stmt = text("""
        UPDATE projects p SET qualified_at = :now
        WHERE p.id IN :ids AND p.qualified_at IS NULL AND p.is_deleted = false
          AND p.authorization_code IS NOT NULL AND btrim(p.authorization_code) <> ''
          AND EXISTS (SELECT 1 FROM actions a   WHERE a.project_id=p.id)
          AND EXISTS (SELECT 1 FROM project_customer_associations pca WHERE pca.project_id=p.id)
          AND EXISTS (SELECT 1 FROM quotations q WHERE q.project_id=p.id)
    """).bindparams(bindparam('ids', expanding=True))
    with db.engine.begin() as conn:
        if company_ids:
            conn.execute(cust_stmt, {'now': now, 'ids': list(company_ids)})
        if project_ids:
            conn.execute(proj_stmt, {'now': now, 'ids': list(project_ids)})


_listeners_registered = False


def register_qualified_at_listeners():
    """注册会话事件:任意提交若触及 客户/联系人/跟进/项目/报价单/项目关联,
    提交后即对受影响记录实时判定并盖戳 qualified_at(真实达标时刻)。集中一处,不动业务代码。
    幂等注册;失败只记日志不影响主流程。每小时定时任务仍作兜底。"""
    global _listeners_registered
    if _listeners_registered:
        return
    import logging
    from sqlalchemy import event
    from sqlalchemy.orm import Session
    _log = logging.getLogger(__name__)

    @event.listens_for(Session, 'before_flush')
    def _qa_collect(session, ctx, instances):
        try:
            _collect_affected(session)
        except Exception:
            pass

    @event.listens_for(Session, 'after_commit')
    def _qa_after_commit(session):
        from app.models.customer import Company
        from app.models.project import Project
        cids = session.info.pop('_qa_c', None) or set()
        pids = session.info.pop('_qa_p', None) or set()
        for o in (session.info.pop('_qa_objs', None) or []):
            try:
                if isinstance(o, Company) and o.id:
                    cids.add(o.id)
                elif isinstance(o, Project) and o.id:
                    pids.add(o.id)
            except Exception:
                pass
        if not cids and not pids:
            return
        if session.info.get('_qa_busy'):   # 防自身盖戳 commit 递归
            return
        try:
            session.info['_qa_busy'] = True
            _stamp_now_for(cids, pids)
        except Exception as e:
            _log.warning(f"实时达标盖戳失败(兜底任务会补): {e}")
            try:
                from app import db
                db.session.rollback()
            except Exception:
                pass
        finally:
            session.info.pop('_qa_busy', None)

    _listeners_registered = True


def stamp_qualified_at():
    """给【已达标但未盖戳】的客户/项目写入 qualified_at = 推导的首次达标时刻,幂等(只动 NULL),
    永不重算已盖戳记录(达标后即便资料被删也保留 → 过去月份不变)。
    既用于一次性回填,也供周期任务调用。返回 (新增盖戳客户数, 新增盖戳项目数)。

    达标时刻 = 各合格条件满足时间的最大值(GREATEST):
      客户 = max(建档, 首个联系人, 第1条跟进);
      项目 = max(建档, 第1条跟进, 第1个关联客户, 第1张报价单)。
    条件口径与 _qualified_customer_filters / _qualified_project_filters 一致(此处用 SQL 直写以批量高效);
    统一 ::timestamp 规避 quotations.created_at(timestamptz)与其余 naive 时间混比。"""
    from app import db
    from sqlalchemy import text
    cust_sql = text("""
        UPDATE companies c SET qualified_at = sub.qa FROM (
          SELECT c2.id, GREATEST(
                   c2.created_at::timestamp,
                   (SELECT min(ct.created_at) FROM contacts ct WHERE ct.company_id=c2.id)::timestamp,
                   (SELECT min(a.created_at)  FROM actions  a  WHERE a.company_id=c2.id)::timestamp
                 ) AS qa
          FROM companies c2
          WHERE c2.qualified_at IS NULL AND c2.is_deleted = false
            AND c2.company_name IS NOT NULL AND btrim(c2.company_name) <> ''
            AND c2.address      IS NOT NULL AND btrim(c2.address)      <> ''
            AND c2.company_type IS NOT NULL AND btrim(c2.company_type) <> ''
            AND EXISTS (SELECT 1 FROM contacts ct WHERE ct.company_id=c2.id)
            AND (SELECT count(*) FROM actions a WHERE a.company_id=c2.id) >= 1
        ) sub WHERE c.id = sub.id
    """)
    proj_sql = text("""
        UPDATE projects p SET qualified_at = sub.qa FROM (
          SELECT p2.id, GREATEST(
                   p2.created_at::timestamp,
                   (SELECT min(a.created_at)   FROM actions a   WHERE a.project_id=p2.id)::timestamp,
                   (SELECT min(pca.created_at) FROM project_customer_associations pca WHERE pca.project_id=p2.id)::timestamp,
                   (SELECT min(q.created_at)   FROM quotations q WHERE q.project_id=p2.id)::timestamp
                 ) AS qa
          FROM projects p2
          WHERE p2.qualified_at IS NULL AND p2.is_deleted = false
            AND p2.authorization_code IS NOT NULL AND btrim(p2.authorization_code) <> ''
            AND EXISTS (SELECT 1 FROM actions a   WHERE a.project_id=p2.id)
            AND EXISTS (SELECT 1 FROM project_customer_associations pca WHERE pca.project_id=p2.id)
            AND EXISTS (SELECT 1 FROM quotations q WHERE q.project_id=p2.id)
        ) sub WHERE p.id = sub.id
    """)
    n_cust = db.session.execute(cust_sql).rowcount
    n_proj = db.session.execute(proj_sql).rowcount
    db.session.commit()
    return n_cust, n_proj


def _act_new_projects(user, s, e):
    """合格新项目(我名下 owner_id,按【达标时间】落窗口 — 冻结历史,补资料不改过去月份)。"""
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        Project.owner_id == user.id, Project.is_deleted == False,
        Project.qualified_at.isnot(None),
        Project.qualified_at >= s, Project.qualified_at < e,
    ).scalar() or 0

def _act_new_customers(user, s, e):
    """合格新客户(我名下 owner_id,按【达标时间】落窗口 — 冻结历史,补资料不改过去月份)。"""
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.owner_id == user.id, Company.is_deleted == False,
        Company.qualified_at.isnot(None),
        Company.qualified_at >= s, Company.qualified_at < e,
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
        -- quality_sum/quality_count 供「跨实例池化」用,合并均值=(ΣCN+ΣSG)除以(nCN+nSG),非两均值再平均。
        SELECT COALESCE(AVG(qs.qscore), 0) AS quality,
               COALESCE(SUM(qs.qscore), 0) AS quality_sum,
               COUNT(*) AS quality_count
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
    SELECT c.cnt, spt.sup AS sup, ql.quality, ql.quality_sum, ql.quality_count,
           im.by_cur AS implant, sa.by_cur AS sales
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
            'se_confirm_quality_sum': round(float(r.quality_sum or 0), 4),    # 跨实例池化分子(系数和)
            'se_confirm_quality_count': int(r.quality_count or 0),            # 跨实例池化分母(确认报价笔数)
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
        from datetime import timedelta   # 既有遗漏:本模块未 import timedelta,致手工指标一直 NameError→算0(2026-06-30 修)
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
    'se_training_count':  lambda u, s, e: _act_task_count_approved(u, s, e, 'se_tech_training'),  # 技术培训:审核通过任务计数(每条记1)
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
    """团队植入额(2026-06-30 口径修正):按【项目拥有人 ∈ 本部门成员】归属 + 仅计有确认过的报价。"""
    from app import db
    from app.models.quotation import Quotation
    from app.models.project import Project
    q = (db.session.query(Quotation)
         .join(Project, Project.id == Quotation.project_id)
         .filter(Project.owner_id.in_(_dept_member_ids(user)),
                 Quotation.confirmed_by.isnot(None),
                 Quotation.created_at >= s, Quotation.created_at < e))
    return _sum_money(q, Quotation.implant_total_amount, Quotation.currency)


def _act_team_new_projects(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        Project.owner_id.in_(_dept_member_ids(user)), Project.is_deleted == False,
        Project.qualified_at.isnot(None),
        Project.qualified_at >= s, Project.qualified_at < e,
    ).scalar() or 0


def _act_team_new_customers(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.owner_id.in_(_dept_member_ids(user)), Company.is_deleted == False,
        Company.qualified_at.isnot(None),
        Company.qualified_at >= s, Company.qualified_at < e,
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
    """渠道植入额(2026-06-30 补确认):渠道项目(report_source=channel,不限负责人)归属不变,
       仅补"有确认过的报价"(confirmed_by 留痕)条件,与销售/团队口径一致。"""
    from app import db
    from app.models.quotation import Quotation
    from app.models.project import Project
    q = (db.session.query(Quotation)
         .join(Project, Project.id == Quotation.project_id)
         .filter(*_channel_project_filter(),
                 Quotation.confirmed_by.isnot(None),
                 Quotation.created_at >= s, Quotation.created_at < e))
    return _sum_money(q, Quotation.implant_total_amount, Quotation.currency)


def _act_channel_new_projects(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        *_channel_project_filter(),
        Project.qualified_at.isnot(None),
        Project.qualified_at >= s, Project.qualified_at < e,
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
        Company.owner_id.in_(_dealer_user_ids()), Company.is_deleted == False,
        Company.qualified_at.isnot(None),
        Company.qualified_at >= s, Company.qualified_at < e,
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


def _act_task_count_approved(user, s, e, _task_type):
    """通用:本人(assignee)完成且审核通过的某类任务计数(每条记1,不加权)。
    与 _act_hr_task_count(完成即计)不同:要求 review_status='approved' 才计入。"""
    from app.models.task import Task
    return Task.query.filter(
        Task.assignee_id == user.id,
        Task.task_type == _task_type,
        Task.review_status == 'approved',
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


# ──────────────────────────────────────────────────────────────────────────
# 跨实例 KPI 合并(Phase 2):绑定 peer_user_id 的人,实际值 = 本端 + 对端(CN+SG)
#   amount  → 对端值换算到本端币种后相加
#   count   → 直接相加
#   tiered(植入品质)→ 池化:合并均值 = (ΣCN+ΣSG)/(nCN+nSG),套同一档
#   percentage(率)/ score-avg(满意度)→ 暂仅本端(TODO 2b:暴露分子分母/明细池化后合并)
# 对端不可达 → 静默降级为仅本端,绝不影响本端考核。
# ──────────────────────────────────────────────────────────────────────────
_MERGE_ALIAS = {'sales_target': 'sales_amount'}


def _local_currency():
    import os
    _self = os.environ.get('PMA_DB_TYPE', os.environ.get('SUPABASE_DB_TYPE', 'sp8d'))
    return 'CNY' if _self == 'sp8d' else 'USD'


def _peer_kpi_payload(peer_id, s, e):
    """拉取对端整份 KPI payload,按 (peer_id, 窗口) 请求内缓存(一次渲染算多指标只调一次)。"""
    from flask import g, has_request_context
    key = ('_peer_kpi', peer_id, s.isoformat() if hasattr(s, 'isoformat') else str(s),
           e.isoformat() if hasattr(e, 'isoformat') else str(e))
    cache = None
    if has_request_context():
        cache = getattr(g, '_peer_kpi_cache', None)
        if cache is None:
            cache = {}
            g._peer_kpi_cache = cache
        if key in cache:
            return cache[key]
    try:
        from app.services.cross_sync_service import fetch_peer_kpi_actuals
        payload = fetch_peer_kpi_actuals(peer_id, s.isoformat(), e.isoformat())
    except Exception:
        payload = None
    if cache is not None:
        cache[key] = payload
    return payload


def _merge_metric(code, local, pdata, payload, user, s, e):
    """按 data_type/scoring_mode 合并本端值 local 与对端 pdata。"""
    dtype = (pdata or {}).get('data_type')
    mode = (pdata or {}).get('scoring_mode')
    pval = float((pdata or {}).get('value') or 0)
    # 植入品质:池化系数均值(非两均值再平均)
    if mode == 'tiered' or code == 'se_confirm_quality':
        try:
            lw = _se_window(user, s, e)
            lsum = float(lw.get('se_confirm_quality_sum') or 0)
            lcnt = int(lw.get('se_confirm_quality_count') or 0)
        except Exception:
            lsum, lcnt = 0.0, 0
        psum = float((pdata or {}).get('quality_sum') or 0)
        pcnt = int((pdata or {}).get('quality_count') or 0)
        tot = lcnt + pcnt
        return round((lsum + psum) / tot, 2) if tot else local
    if dtype == 'amount':
        cur = (payload or {}).get('self_currency') or 'USD'
        tgt = _local_currency()
        conv = pval
        if cur != tgt and pval:
            try:
                from app.services.exchange_rate_service import exchange_rate_service
                conv = float(exchange_rate_service.convert_amount(pval, cur, tgt) or 0)
            except Exception:
                conv = pval
        return local + conv
    if dtype == 'count':
        return local + pval
    # 率 / 满意度均值:Phase 2b 再做(需分子分母/明细池化)→ 暂仅本端
    return local


def kpi_actual(user, code, s, e):
    """KPI 实际值唯一公共入口(2026-06-30):本端值 +(若绑定对端)跨实例合并。
       未绑定 / 对端不可达 → 返回纯本端值。调用方应改用本函数替代直接索引 _KPI_ACTUAL_FNS,
       以便合并口径统一(仪表盘卡 / 绩效页 / 个人配置实际值一致)。"""
    fn = _KPI_ACTUAL_FNS.get(_MERGE_ALIAS.get(code, code))
    local = 0.0
    if fn is not None:
        try:
            local = float(fn(user, s, e) or 0)
        except Exception:
            local = 0.0
    peer_id = getattr(user, 'peer_user_id', None)
    if not peer_id:
        return local
    payload = _peer_kpi_payload(peer_id, s, e)
    if not payload or not payload.get('data'):
        return local
    pdata = payload['data'].get(code) or payload['data'].get(_MERGE_ALIAS.get(code, code))
    if not pdata:
        return local
    return _merge_metric(code, local, pdata, payload, user, s, e)
