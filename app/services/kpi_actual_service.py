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
import logging

logger = logging.getLogger(__name__)


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



# ── 销售额 / 植入额 的基础查询(唯一定义)─────────────────────────────────
# 采集器(_act_*)与明细下钻(_detail_*)共用同一个 query builder,口径物理上不可分叉。
# scope: 'own'(本人) | 'team'(本部门成员) | 'channel'(渠道项目按厂商销售负责人)
# ⚠️ 改口径只改这两个函数;不要在别处另写一份 —— 见 memory「KPI实际采集唯一后端」。

def _q_sales(user, s, e, scope='own'):
    """已批准批价单。归属:批价单创建人(渠道口径除外,渠道看项目的厂商销售负责人)。"""
    from app import db
    from app.models.pricing_order import PricingOrder
    from app.models.project import Project
    q = db.session.query(PricingOrder)
    if scope == 'channel':
        q = (q.join(Project, Project.id == PricingOrder.project_id)
              .filter(*_channel_project_filter(user)))
    elif scope == 'team':
        q = q.filter(PricingOrder.created_by.in_(_dept_member_ids(user)))
    else:
        q = q.filter(PricingOrder.created_by == user.id)
    return q.filter(PricingOrder.status == 'approved',
                    PricingOrder.approved_at >= s, PricingOrder.approved_at < e)


def _q_implant(user, s, e, scope='own'):
    """植入额口径(2026-06-30 修正):
       ① 归属按【项目拥有人】(Project.owner_id),不看报价 owner(SE/他人代写报价不影响归属);
       ② 仅计【有确认过】的报价(confirmed_by 留痕),不看当前徽章状态('reconfirm' 仍算)。
       注意与 se_implant_amount 同名不同义 —— 后者按「项目配合主方 + 仅厂商产品 +
       市场价×数量」算,两者数值不可比,下钻的 basis 脚注会讲清楚。"""
    from app import db
    from app.models.quotation import Quotation
    from app.models.project import Project
    q = db.session.query(Quotation).join(Project, Project.id == Quotation.project_id)
    if scope == 'channel':
        q = q.filter(*_channel_project_filter(user))
    elif scope == 'team':
        q = q.filter(Project.owner_id.in_(_dept_member_ids(user)))
    else:
        q = q.filter(Project.owner_id == user.id)
    return q.filter(Quotation.confirmed_by.isnot(None),
                    Quotation.created_at >= s, Quotation.created_at < e)


def _act_sales(user, s, e):
    from app.models.pricing_order import PricingOrder
    return _sum_money(_q_sales(user, s, e, 'own'),
                      PricingOrder.pricing_total_amount, PricingOrder.currency)

def _act_implant(user, s, e):
    from app.models.quotation import Quotation
    return _sum_money(_q_implant(user, s, e, 'own'),
                      Quotation.implant_total_amount, Quotation.currency)

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

# ── PM 归属口径(唯一定义)────────────────────────────────────────────────
# 产品经理三个指标各有一套归属判定(既有实现,本次只抽取不改口径):
#   植入额     = 分类负责人(managed_categories)                    → _q_pm_implant
#   产品批价额 = 产品 owner 或分类负责人,且该人 role=product_manager → _PM_PRODUCT_PM_CTE
#   新品上市   = 产品 owner 或分类负责人(不看 role)                 → _PM_LAUNCH_WHERE
# 采集器(_act_pm_*)与明细下钻(_detail_pm_*)共用下面这三段,物理上不可能分叉。
# ⚠️ 三套口径不一致是既有事实(同一个人在三个指标里的归属范围不同),各自的
#    basis 文案会逐条写明,让差异在界面上可见。要统一口径另开一轮,别在这里顺手改。

def _q_pm_implant(user, s, e):
    """产品植入额的基础查询(已 join/filter、未聚合)。无分管分类时返回 None。

    ⚠️ **不要**补 is_vendor_product 过滤:implant_subtotal 对非厂商产品恒为 0,
    但对旧数据「品牌=和源通信、无 product_mn」的行是有值的
    (见 QuotationDetail.calculate_implant_subtotal_only 的兼容分支),
    补过滤会把这批旧数据漏掉,明细合计立刻对不上单元格。
    同理 quotations 表没有 is_deleted 列,不存在漏加软删除的问题。
    """
    from app import db
    from app.models.quotation import Quotation, QuotationDetail
    from app.models.product import Product
    cat_ids = [c.id for c in getattr(user, 'managed_categories', [])]
    if not cat_ids:
        return None
    return db.session.query(QuotationDetail).join(
        Quotation, Quotation.id == QuotationDetail.quotation_id).join(
        Product, Product.product_mn == QuotationDetail.product_mn).filter(
        Product.category_id.in_(cat_ids),
        Quotation.created_at >= s, Quotation.created_at < e)


def _act_pm_implant(user, s, e):
    from app.models.quotation import Quotation, QuotationDetail
    q = _q_pm_implant(user, s, e)
    if q is None:
        return 0
    return _sum_money(q, QuotationDetail.implant_subtotal, Quotation.currency)

# ── SE 归属口径(唯一定义)────────────────────────────────────────────────
# 「配合主方」的判定只此一份:总额(_SE_WINDOW_SQL)与明细下钻(_SE_IMPLANT_DETAIL_SQL)
# 都拼这段,物理上不可能分叉。改口径只改这里。
# ⚠️ 不要复制这段去别处写新统计 —— 见 memory「KPI实际采集唯一后端」。
_SE_SCOPE_CTE = """
    se_users AS (
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
    )
"""

# SE 五项:一次 SQL 出全窗口(口径照抄 performance_service SE CTE)
_SE_WINDOW_SQL = "WITH " + _SE_SCOPE_CTE + """,
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
        vals = _manual_vals(code, agg, user, s, e)
        if not vals:
            return 0
        return round(sum(vals) / len(vals), 1) if agg == 'avg' else round(sum(vals), 2)
    return fn


def _manual_vals(code, agg, user, s, e):
    """手工指标窗口内逐月取到的值列表(agg-aware:sum 模式季度回退按 /3 折月)。
    供 _act_manual 求 avg/sum,以及跨实例池化分子分母(metric_parts)单一来源。"""
    from app.models.performance_manual_entry import PerformanceManualEntry
    from datetime import timedelta
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
    return vals


# 手工录入指标 → 聚合方式(avg 类参与跨实例池化:合并均值=(ΣCN+ΣSG)/(nCN+nSG))
_MANUAL_AGG = {
    'se_content_output': 'sum',
    'se_response_rate': 'avg',
    'se_satisfaction': 'avg',
}


def metric_parts(code, user, s, e):
    """avg/档位类指标的跨实例池化分子分母 (sum, count);无法分解的(DB率类)→None。
    合并均值 = (ΣCN+ΣSG)/(nCN+nSG),而非两侧各自均值再平均。"""
    if code == 'se_confirm_quality':
        try:
            w = _se_window(user, s, e)
            return (float(w.get('se_confirm_quality_sum') or 0),
                    int(w.get('se_confirm_quality_count') or 0))
        except Exception:
            return None
    if _MANUAL_AGG.get(code) == 'avg':
        vals = _manual_vals(code, 'avg', user, s, e)
        return (float(sum(vals)), len(vals))
    return None

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

# 产品→产品经理的归属映射。总额(_act_pm_sales)与明细(_detail_pm_sales)拼同一段。
_PM_PRODUCT_PM_CTE = """
        product_pm AS (
            SELECT p.product_mn,
                   CASE WHEN u_owner.role = 'product_manager' THEN p.owner_id
                        WHEN u_cat_mgr.role = 'product_manager' THEN pc.manager_id
                        ELSE NULL END AS pm_id
            FROM products p
            LEFT JOIN users u_owner ON p.owner_id = u_owner.id
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN users u_cat_mgr ON pc.manager_id = u_cat_mgr.id
            WHERE p.is_vendor_product = true
        )"""

# 新品上市的归属条件(products 表别名 p、product_categories 别名 pc)。
# 注意与上面 product_pm 不同:这里不要求归属人的 role 是 product_manager。
_PM_LAUNCH_WHERE = "(p.owner_id = :uid OR pc.manager_id = :uid)"


def _act_pm_sales(user, s, e):
    """产品批价额:我(产品 owner 或分类负责人)名下厂商产品的已批价明细金额
    —— 口径照抄 performance_service.calculate_pm_yearly_statistics_batch 的 pm_sales CTE"""
    from sqlalchemy import text
    from app import db
    r = db.session.execute(text("WITH " + _PM_PRODUCT_PM_CTE + """
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
    from sqlalchemy import text
    from app import db
    r = db.session.execute(text(f"""
        SELECT COUNT(*) FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE p.is_vendor_product = true AND p.status = 'active'
          AND p.created_at >= :s AND p.created_at < :e
          AND {_PM_LAUNCH_WHERE}
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
    from app.models.pricing_order import PricingOrder
    return _sum_money(_q_sales(user, s, e, 'team'),
                      PricingOrder.pricing_total_amount, PricingOrder.currency)


def _act_team_implant(user, s, e):
    """团队植入额:按【项目拥有人 ∈ 本部门成员】归属 + 仅计有确认过的报价(口径见 _q_implant)。"""
    from app.models.quotation import Quotation
    return _sum_money(_q_implant(user, s, e, 'team'),
                      Quotation.implant_total_amount, Quotation.currency)


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
def _channel_project_filter(user):
    """渠道项目过滤:report_source=channel 且 厂商销售负责人(vendor_sales_manager)为本人。
    2026-07-03:由"全渠道不分人"改为按厂商负责人归属,避免多渠道经理互相串号
    (代理商上报的渠道项目 owner 常为代理商/他人,真正归属看 vendor_sales_manager)。"""
    from app.models.project import Project
    return [Project.is_deleted == False, Project.report_source == 'channel',
            Project.vendor_sales_manager_id == user.id]


def _act_channel_sales(user, s, e):
    from app.models.pricing_order import PricingOrder
    return _sum_money(_q_sales(user, s, e, 'channel'),
                      PricingOrder.pricing_total_amount, PricingOrder.currency)


def _act_channel_implant(user, s, e):
    """渠道植入额:渠道项目(report_source=channel + 厂商销售负责人为本人)中有确认过的报价
       的植入额之和(2026-07-03 归属口径由全渠道改为按厂商负责人;口径见 _q_implant)。"""
    from app.models.quotation import Quotation
    return _sum_money(_q_implant(user, s, e, 'channel'),
                      Quotation.implant_total_amount, Quotation.currency)


def _act_channel_new_projects(user, s, e):
    from sqlalchemy import func
    from app import db
    from app.models.project import Project
    return db.session.query(func.count(Project.id)).filter(
        *_channel_project_filter(user),
        Project.qualified_at.isnot(None),
        Project.qualified_at >= s, Project.qualified_at < e,
    ).scalar() or 0


def _dealer_user_ids():
    """渠道客户维度的口径主体:代理商(dealer)账户"""
    from app.models.user import User as _U
    return [u.id for u in _U.query.filter(_U.role == 'dealer').all()] or [0]


def _act_channel_new_customers(user, s, e):
    # 渠道新增客户 = 本人名下本期新建的客户(按创建账户归属)
    # 2026-07-03:由"全部代理商账户名下"改为"本人名下"(Company.owner_id == 本人),与渠道各项口径一致
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.owner_id == user.id, Company.is_deleted == False,
        Company.qualified_at.isnot(None),
        Company.qualified_at >= s, Company.qualified_at < e,
    ).scalar() or 0


def _act_channel_customer_activity(user, s, e):
    # 渠道客户活跃度 = 本人名下客户中 高活/活跃/正常 占比(快照)
    # 2026-07-03:由"全部代理商账户名下客户"改为"本人名下客户"(Company.owner_id == 本人)
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    rows = dict(db.session.query(Company.status, func.count(Company.id))
                .filter(Company.is_deleted == False, Company.owner_id == user.id)
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
    projs = Project.query.filter(*_channel_project_filter(user),
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
    total = Project.query.filter(*_channel_project_filter(user)).count()
    if not total:
        return 0.0
    lost_ids = _lost_this_year_ids(s.year)
    if not lost_ids:
        return 0.0
    lost_channel = Project.query.filter(*_channel_project_filter(user),
                                        Project.id.in_(list(lost_ids))).count()
    return round(lost_channel / total * 100, 1)


def _act_channel_new_dealers(user, s, e):
    """渠道发展:本人名下本期新建的代理商/分销商客户数(company_type=dealer/distributor)。
    2026-07-03:由全实例改为按创建账户归属(Company.owner_id == 本人),谁建的代理商算谁。"""
    from sqlalchemy import func
    from app import db
    from app.models.customer import Company
    return db.session.query(func.count(Company.id)).filter(
        Company.is_deleted == False,
        Company.owner_id == user.id,
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


def _local_meta():
    """本端全量指标元数据 {code:{data_type,scoring_mode}},请求内缓存。
       合并以本端 data_type 为权威(对端定义可能不全,如 SG 缺某指标 data_type)。"""
    from flask import g, has_request_context
    if has_request_context():
        m = getattr(g, '_kpi_local_meta', None)
        if m is not None:
            return m
    try:
        from app.helpers.scoring_modes import load_metric_meta
        m = load_metric_meta()
    except Exception:
        m = {}
    if has_request_context():
        g._kpi_local_meta = m
    return m


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


def _merge_metric(code, local, pdata, payload, user, s, e, local_info=None):
    """按 data_type/scoring_mode 合并本端值 local 与对端 pdata。
       data_type/scoring_mode 以本端(local_info)为权威,对端值仅兜底
       (对端 metrics 定义可能不全,如 SG 缺某指标 data_type 会致漏加)。"""
    li = local_info or {}
    dtype = li.get('data_type') or (pdata or {}).get('data_type')
    mode = li.get('scoring_mode') or (pdata or {}).get('scoring_mode')
    pval = float((pdata or {}).get('value') or 0)
    from app.helpers.scoring_modes import is_avg_aggregated
    # 均值/档位类(植入品质 tiered、率、满意度 avg):池化分子分母
    # 合并均值=(ΣCN+ΣSG)/(nCN+nSG);任一侧无 parts(如 DB 率类不可分解)→ 仅本端。
    if mode == 'tiered' or is_avg_aggregated(dtype):
        lp = metric_parts(code, user, s, e)
        pp = (pdata or {}).get('parts')
        if lp and pp:
            lsum, lcnt = lp
            psum, pcnt = float(pp.get('sum') or 0), int(pp.get('count') or 0)
            tot = lcnt + pcnt
            if tot:
                return round((lsum + psum) / tot, 2)
        return local
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
    meta = _local_meta()
    local_info = meta.get(code) or meta.get(_MERGE_ALIAS.get(code, code)) or {}
    return _merge_metric(code, local, pdata, payload, user, s, e, local_info)


def kpi_actual_breakdown(user, code, s, e):
    """合并值 + CN/SG 拆分,供仪表盘卡 hover tooltip 展示。
       返回 {'merged','local','has_peer'[,'peer','peer_converted','peer_currency']}。
       未绑定/对端不可达 → has_peer=False,merged=local。"""
    fn = _KPI_ACTUAL_FNS.get(_MERGE_ALIAS.get(code, code))
    local = 0.0
    if fn is not None:
        try:
            local = float(fn(user, s, e) or 0)
        except Exception:
            local = 0.0
    peer_id = getattr(user, 'peer_user_id', None)
    if not peer_id:
        return {'merged': local, 'local': local, 'has_peer': False}
    payload = _peer_kpi_payload(peer_id, s, e)
    pdata = (payload or {}).get('data', {}).get(code) if payload else None
    if not pdata:
        pdata = (payload or {}).get('data', {}).get(_MERGE_ALIAS.get(code, code)) if payload else None
    if not pdata:
        return {'merged': local, 'local': local, 'has_peer': False}
    meta = _local_meta()
    li = meta.get(code) or meta.get(_MERGE_ALIAS.get(code, code)) or {}
    merged = _merge_metric(code, local, pdata, payload, user, s, e, li)
    pval = float(pdata.get('value') or 0)
    dtype = li.get('data_type') or pdata.get('data_type')
    mode = li.get('scoring_mode') or pdata.get('scoring_mode')
    # 是否真正发生合并:amount/count 恒合并;tiered/avg 仅两侧都有 parts 才池化;
    # DB 率类(无 parts)实为仅本端 → 不算合并,卡片不显示 CN+SG 标签(避免误导)。
    from app.helpers.scoring_modes import is_avg_aggregated
    if dtype in ('amount', 'count'):
        applied = True
    elif mode == 'tiered' or is_avg_aggregated(dtype):
        applied = bool(metric_parts(code, user, s, e) and (pdata or {}).get('parts'))
    else:
        applied = False
    if not applied:
        return {'merged': merged, 'local': local, 'has_peer': False}
    peer_cur = (payload or {}).get('self_currency')
    peer_conv = pval
    if dtype == 'amount' and peer_cur and peer_cur != _local_currency() and pval:
        try:
            from app.services.exchange_rate_service import exchange_rate_service
            peer_conv = float(exchange_rate_service.convert_amount(pval, peer_cur, _local_currency()) or 0)
        except Exception:
            peer_conv = pval
    return {'merged': merged, 'local': local, 'has_peer': True,
            'peer': pval, 'peer_converted': peer_conv, 'peer_currency': peer_cur}


# ═══════════════════════════════════════════════════════════════════════════
# KPI 实际值「下钻明细」—— 回答 HR/审批人「这个数字是怎么来的」
#
# 铁律:明细与总额必须共用同一段归属 CTE(_SE_SCOPE_CTE),不允许另写一份 SQL。
# 另写一份的下场见 memory「工作项→跟进记录同步」:两套互不知情的实现并存半年,
# 数字对不上时无人能解释,最后只能靠考古 git 找根因。
#
# 新增一个 KPI 的下钻 = 加一个 provider + 在 _KPI_DETAIL_FNS 注册一行,
# 前端组件数据驱动、零改动。注册表里没有的 code,前端不显示下钻入口。
# ═══════════════════════════════════════════════════════════════════════════

# 明细:与 _SE_WINDOW_SQL 的 im CTE 同源,去掉 SUM/GROUP BY 摊到行
_SE_IMPLANT_DETAIL_SQL = "WITH " + _SE_SCOPE_CTE + """
    SELECT pj.id           AS project_id,
           pj.project_name AS project_name,
           q.id            AS quotation_id,
           q.quotation_number,
           q.currency      AS currency,
           qd.product_mn,
           qd.product_name,
           qd.product_model,
           qd.quantity     AS quantity,
           qd.market_price AS market_price
    FROM quotation_details qd
    JOIN quotations   q  ON qd.quotation_id = q.id
    JOIN se_projects  sp ON q.project_id = sp.project_id
    JOIN projects     pj ON pj.id = q.project_id
    JOIN products     p  ON qd.product_mn = p.product_mn
    WHERE p.is_vendor_product = true
      AND q.created_at >= :s AND q.created_at < :e
    ORDER BY pj.project_name, q.id, qd.id
"""


def _unit_display(kind='amount'):
    """与绩效表格「单位」列**逐字一致**的单位串。

    口径来源:app/views/performance_config.py:1458-1461(那里是表格的单位来源)——
      金额 = 币种符号 + 量级,CN「¥万」/ SG「$M」(带符号,去掉 CNY 的「元」冗余)
      计数 = Config.COUNT_UNIT「个」/「pcs」
    **与界面语言解耦**(绩效模块既定约定,见 get_performance_unit_config docstring)。
    早先误用 currency_helpers.get_amount_unit(),英文界面会返回「0K」;后来改用
    Config.AMOUNT_UNIT 得到「万元」,又与表格的「¥万」对不上 —— 现按表格为准。
    """
    from config import Config
    if kind == 'count':
        return Config.COUNT_UNIT
    mag = '万' if Config.DEFAULT_CURRENCY == 'CNY' else Config.AMOUNT_UNIT
    return f"{Config.CURRENCY_SYMBOL}{mag}"


def _fmt_amount(v):
    """缩放后的金额数字,**不带货币符号**(如「1,832.89」)。

    两条约束:
    ① **必须 2 位小数**:表格单元格用 fmt=Math.round(v*100)/100 显示(如 1832.89),
       下钻合计要能与用户刚点的数字逐位对上,否则会被当成两个数。
    ② **不带符号也不拼单位**:表格是「数字格 + 独立单位列」,单位串本身已含 ¥
       (「¥万」),这里再带符号会得到「¥1,832.89 ¥万」。
    """
    from config import Config
    return f"{v / float(Config.AMOUNT_DIVISOR):,.2f}"


def _fmt_amount_raw(v):
    """原始金额(不缩放),供交叉核对 —— 「¥1,832.89 万元」到底是多少钱一眼可见。"""
    from app.utils.currency_helpers import get_currency_symbol
    return f"{get_currency_symbol()}{v:,.0f}"


def _detail_se_implant(user, s, e):
    """方案植入额明细:项目 › 报价单 › 产品行。"""
    from sqlalchemy import text
    from app import db
    from flask_babel import gettext as _g

    rows = db.session.execute(
        text(_SE_IMPLANT_DETAIL_SQL), {'uid': user.id, 's': s, 'e': e}).fetchall()

    projects, total, n_quo, n_rows = {}, 0.0, set(), 0
    for r in rows:
        amt = _conv_money(float(r.quantity or 0) * float(r.market_price or 0), r.currency)
        total += amt
        n_quo.add(r.quotation_id)
        n_rows += 1
        pg = projects.setdefault(r.project_id, {
            'label': r.project_name or _g('(未命名项目)'), 'value': 0.0, '_q': {}})
        pg['value'] += amt
        qg = pg['_q'].setdefault(r.quotation_id, {
            'label': r.quotation_number or f'#{r.quotation_id}', 'value': 0.0, 'rows': []})
        qg['value'] += amt
        qg['rows'].append({
            'name': r.product_name or r.product_model or r.product_mn or '—',
            'sub': r.product_mn or '',
            'qty': float(r.quantity or 0),
            'value': amt,
            # 明细行用原始金额(元),不用万元:一行 1400 元缩成「¥0.14」会被读成一毛四,
            # 单位只在顶部标一次,下面全靠隐式继承 —— 必错。用元还能和报价单原始数字对上。
            'value_display': _fmt_amount_raw(amt),
        })

    groups = []
    for pg in sorted(projects.values(), key=lambda x: -x['value']):
        quos = sorted(pg['_q'].values(), key=lambda x: -x['value'])
        # 项目/报价单小计同样用元:与产品行同单位才能直接相加,且各项目之和 == 顶部的
        # total_raw_display(¥18,328,899),核对链条闭合。只有顶部合计用万元(与绩效单元格对齐)。
        g = {'label': pg['label'], 'value': pg['value'],
             'value_display': _fmt_amount_raw(pg['value'])}
        if len(quos) == 1:
            # 97% 的项目只有一张报价单(实测本地库 686 中 668) —— 这层不分叉时纯属噪音,
            # 多一次展开换不来任何信息。单号降为副标题,产品行直接挂项目下。
            g['sub'] = quos[0]['label']
            g['rows'] = quos[0]['rows']
        else:
            g['children'] = [{
                'label': qg['label'],
                'value': qg['value'],
                'value_display': _fmt_amount_raw(qg['value']),
                'rows': qg['rows'],
            } for qg in quos]
        groups.append(g)

    from config import Config
    return {
        'title': _g('方案植入额'),
        'kind': 'amount',
        'total': total,
        # 单位单独给,前端小字附在数字后。**必须用 Config.AMOUNT_UNIT,不能用
        # currency_helpers.get_amount_unit()** —— 后者会按界面语言把「万元」换成「0K」,
        # 而绩效模块的既定约定是「单位由数据库类型决定,与语言解耦」
        # (见 performance_config.get_performance_unit_config 的 docstring),
        # 表格的单位列走的就是 Config.AMOUNT_UNIT。用错会出现表格「万元」/弹层「0K」。
        'unit': _unit_display('amount'),
        'total_display': _fmt_amount(total),
        'total_raw_display': _fmt_amount_raw(total),
        'meta': _g('%(p)d 个项目 · %(q)d 张报价单 · %(r)d 行',
                   p=len(projects), q=len(n_quo), r=n_rows),
        # 这行不是装饰:植入额有 4 处反直觉口径,不写清楚 HR 拿去跟销售对账必吵
        'basis': _g('归属:项目配合主方 · 仅厂商产品 · 市场价 × 数量 · 期内全部报价单'),
        'groups': groups,
    }


# code → provider。没注册的 code 前端不显示下钻入口。
_KPI_DETAIL_FNS = {
    'se_implant_amount': _detail_se_implant,
}


def has_actual_detail(code):
    """该 KPI 是否支持下钻(供前端决定要不要给单元格加可点样式)。

    必须走 _MERGE_ALIAS 解析:绩效表格里「销售额」这一行的 item_code 是 **sales_target**
    (定义表口径),而采集器/明细注册用的是 sales_amount(看板口径)。不解析就会出现
    「注册表里有 sales_amount,李华伟的销售额却点不开」。
    """
    return _MERGE_ALIAS.get(code, code) in _KPI_DETAIL_FNS


def detail_supported_codes():
    """下发给前端的可下钻 code 清单 —— 含别名,使表格 item_code 能直接命中。"""
    codes = set(_KPI_DETAIL_FNS)
    codes |= {alias for alias, real in _MERGE_ALIAS.items() if real in _KPI_DETAIL_FNS}
    return sorted(codes)


def get_actual_detail(user, code, s, e):
    """取某人某期某 KPI 的实际值明细。不支持下钻的 code 返回 None。

    返回统一信封 {title,total,total_display,meta,basis,groups[]},
    groups 可递归含 children / rows,前端组件对结构无假设。
    """
    code = _MERGE_ALIAS.get(code, code)        # sales_target → sales_amount
    fn = _KPI_DETAIL_FNS.get(code)
    if not fn:
        return None
    d = fn(user, s, e)

    # ── 跨实例合并的处理(关键)──────────────────────────────────────────
    # 绩效表格单元格显示的是 kpi_actual() = 本端 + 对端(SG) 合并值,而明细只能列本端 ——
    # 对端数据在另一个数据库,本实例取不到。若不声明,HR 会看到「单元格 1490.05万 /
    # 明细合计 929.92万」而认为数字有错。故:合计对齐单元格(合并值),并显式拆出对端部分。
    try:
        from flask_babel import gettext as _g
        bd = kpi_actual_breakdown(user, code, s, e)
        local = float(bd.get('local') or 0)
        # 自检比【本端】值 —— 明细天然只覆盖本端,拿合并值比会永远误报
        if local and abs(d['total'] - local) / max(abs(local), 1e-9) > 0.005:
            logger.error('[kpi_detail] %s 明细合计 %.2f 与本端总额 %.2f 不一致(口径分叉!)',
                         code, d['total'], local)
            d['mismatch'] = {'detail': d['total'], 'aggregate': local}

        if bd.get('has_peer'):
            merged = float(bd.get('merged') or 0)
            peer = merged - local
            # 计数类与金额类的展示格式不同(「4 个」vs「¥560.13」),按信封声明的 kind 走
            _kind = d.get('kind')
            _f = (lambda v: f'{round(v)}') if _kind == 'count' \
                else (lambda v: f'{round(v, 1)}') if _kind == 'rate' \
                else _fmt_amount
            d['has_peer'] = True
            d['local_display'] = d['total_display']          # 本端(有明细)
            d['peer_display'] = _f(peer)                     # 对端(无明细)
            d['total'] = merged
            d['total_display'] = _f(merged)
            d['peer_note'] = _g('对端实例合并,明细需在对端系统查看')
    except Exception as _e:
        logger.warning('[kpi_detail] %s 自检/合并信息获取失败: %s', code, _e)
    return d


# ── 合格新客户 / 新项目 的下钻 ──────────────────────────────────────────
# 这类指标 HR 最无从自证:「建了 10 个客户为什么只算 6 个」的答案全藏在
# _qualified_customer_filters / _qualified_project_filters 的硬性条件里。
# 所以本组 provider 不只列合格项,更要列【未达标项 + 每个缺哪一条】——
# 让核查工具同时变成销售的整改清单。
#
# 窗口口径与采集器一致:合格按 qualified_at(达标盖戳,冻结历史)落窗口;
# 未达标项没有 qualified_at,改按 created_at 落窗口(= 本期新建但还没达标的)。

def _fmt_dt(v):
    return v.strftime('%Y-%m-%d') if v else '—'


def _detail_new_customers(scope):
    """scope(user) -> (SQL 片段, 参数)。返回合格 + 未达标(带缺项)两组。"""
    def _fn(user, s, e):
        from sqlalchemy import text
        from app import db
        from flask_babel import gettext as _g
        where, params = scope(user)
        params.update({'s': s, 'e': e})
        rows = db.session.execute(text(f"""
            SELECT c.id, c.company_name, c.created_at, c.qualified_at,
                   (c.address      IS NOT NULL AND btrim(c.address)      <> '') AS has_addr,
                   (c.company_type IS NOT NULL AND btrim(c.company_type) <> '') AS has_type,
                   (c.company_name IS NOT NULL AND btrim(c.company_name) <> '') AS has_name,
                   EXISTS (SELECT 1 FROM contacts ct WHERE ct.company_id = c.id) AS has_contact,
                   (SELECT count(*) FROM actions a WHERE a.company_id = c.id)    AS act_cnt
            FROM companies c
            WHERE c.is_deleted = false AND ({where})
              AND ( (c.qualified_at >= :s AND c.qualified_at < :e)
                 OR (c.qualified_at IS NULL AND c.created_at >= :s AND c.created_at < :e) )
            ORDER BY c.qualified_at NULLS LAST, c.created_at
        """), params).fetchall()

        ok, bad = [], []
        for r in rows:
            if r.qualified_at:
                ok.append({'name': r.company_name or f'#{r.id}',
                           'sub': _g('达标 %(d)s', d=_fmt_dt(r.qualified_at)),
                           'value_display': ''})
            else:
                miss = []
                if not r.has_name:    miss.append(_g('客户名称'))
                if not r.has_addr:    miss.append(_g('地址'))
                if not r.has_type:    miss.append(_g('客户类型'))
                if not r.has_contact: miss.append(_g('联系人'))
                if (r.act_cnt or 0) < 1: miss.append(_g('跟进记录'))
                bad.append({'name': r.company_name or f'#{r.id}',
                            'sub': _g('缺:') + '、'.join(miss) if miss else _g('待盖戳'),
                            'value_display': ''})
        return _count_envelope(
            _g('合格新客户'), ok, bad,
            _g('合格 = 名称/地址/客户类型齐全 + ≥1 联系人 + ≥1 条跟进记录;'
               '按首次达标时间计入当期,达标后不因资料变动回溯'))
    return _fn


def _detail_new_projects(scope):
    def _fn(user, s, e):
        from sqlalchemy import text
        from app import db
        from flask_babel import gettext as _g
        where, params = scope(user)
        params.update({'s': s, 'e': e})
        rows = db.session.execute(text(f"""
            SELECT p.id, p.project_name, p.created_at, p.qualified_at,
                   (p.authorization_code IS NOT NULL AND btrim(p.authorization_code) <> '') AS has_auth,
                   EXISTS (SELECT 1 FROM actions a WHERE a.project_id = p.id) AS has_act,
                   EXISTS (SELECT 1 FROM project_customer_associations pca
                            WHERE pca.project_id = p.id) AS has_cust,
                   EXISTS (SELECT 1 FROM quotations q WHERE q.project_id = p.id) AS has_quo
            FROM projects p
            WHERE p.is_deleted = false AND ({where})
              AND ( (p.qualified_at >= :s AND p.qualified_at < :e)
                 OR (p.qualified_at IS NULL AND p.created_at >= :s AND p.created_at < :e) )
            ORDER BY p.qualified_at NULLS LAST, p.created_at
        """), params).fetchall()

        ok, bad = [], []
        for r in rows:
            if r.qualified_at:
                ok.append({'name': r.project_name or f'#{r.id}',
                           'sub': _g('达标 %(d)s', d=_fmt_dt(r.qualified_at)),
                           'value_display': ''})
            else:
                miss = []
                if not r.has_auth: miss.append(_g('报备授权编号'))
                if not r.has_act:  miss.append(_g('跟进记录'))
                if not r.has_cust: miss.append(_g('关联客户'))
                if not r.has_quo:  miss.append(_g('报价单'))
                bad.append({'name': r.project_name or f'#{r.id}',
                            'sub': _g('缺:') + '、'.join(miss) if miss else _g('待盖戳'),
                            'value_display': ''})
        return _count_envelope(
            _g('合格新项目'), ok, bad,
            _g('合格 = 报备通过(有授权编号) + ≥1 条跟进 + ≥1 个关联客户 + ≥1 张报价单;'
               '按首次达标时间计入当期,达标后不因资料变动回溯'))
    return _fn


def _count_envelope(title, ok, bad, basis):
    """计数类信封:合格组(计入) + 未达标组(不计入,带缺项)。"""
    from flask_babel import gettext as _g
    groups = []
    if ok:
        groups.append({'label': _g('已达标 · 计入本期'), 'value': len(ok),
                       'value_display': f'{len(ok)} {_unit_display("count")}', 'rows': ok})
    if bad:
        groups.append({'label': _g('未达标 · 不计入'), 'value': len(bad),
                       'value_display': f'{len(bad)} {_unit_display("count")}',
                       'tone': 'warn', 'rows': bad})
    return {
        'title': title,
        'kind': 'count',
        'total': float(len(ok)),
        'total_display': str(len(ok)),
        'unit': _unit_display('count'),
        'meta': _g('本期新增 %(t)d 个,达标 %(o)d,未达标 %(b)d',
                   t=len(ok) + len(bad), o=len(ok), b=len(bad)),
        'basis': basis,
        'groups': groups,
    }


def _scope_own_company(user):
    return 'c.owner_id = :uid', {'uid': user.id}


def _scope_team_company(user):
    return 'c.owner_id = ANY(:uids)', {'uids': _dept_member_ids(user)}


def _scope_own_project(user):
    return 'p.owner_id = :uid', {'uid': user.id}


def _scope_team_project(user):
    return 'p.owner_id = ANY(:uids)', {'uids': _dept_member_ids(user)}


def _scope_channel_project(user):
    # 渠道项目归属看厂商销售负责人,不看 owner(代理商上报的项目 owner 常为他人)
    return "p.report_source = 'channel' AND p.vendor_sales_manager_id = :uid", {'uid': user.id}


_KPI_DETAIL_FNS.update({
    'new_customers':          _detail_new_customers(_scope_own_company),
    'team_new_customers':     _detail_new_customers(_scope_team_company),
    'channel_new_customers':  _detail_new_customers(_scope_own_company),   # 渠道口径同个人
    'new_projects':           _detail_new_projects(_scope_own_project),
    'team_new_projects':      _detail_new_projects(_scope_team_project),
    'channel_new_projects':   _detail_new_projects(_scope_channel_project),
})


# ── 销售额 / 植入额 的下钻(个人 / 团队 / 渠道)────────────────────────────
# 明细与采集器共用 _q_sales / _q_implant 同一个 query builder,口径不可分叉。
# 形态:项目 › 单据(批价单 / 报价单)。金额一律用元,顶部合计用万元(对齐绩效单元格)。

def _group_by_project(recs, label_of, amount_of, currency_of, sub_of):
    """把单据按项目归组。recs: [(project_name, 记录)];无项目的归到「(无关联项目)」。"""
    from flask_babel import gettext as _g
    buckets, total = {}, 0.0
    for proj_name, r in recs:
        amt = _conv_money(float(amount_of(r) or 0), currency_of(r))
        total += amt
        b = buckets.setdefault(proj_name or _g('(无关联项目)'), {'value': 0.0, 'rows': []})
        b['value'] += amt
        b['rows'].append({'name': label_of(r), 'sub': sub_of(r),
                          'value': amt, 'value_display': _fmt_amount_raw(amt)})
    groups = []
    for name, b in sorted(buckets.items(), key=lambda kv: -kv[1]['value']):
        g = {'label': name, 'value': b['value'],
             'value_display': _fmt_amount_raw(b['value'])}
        if len(b['rows']) == 1:
            # 单据只有一张时不值得多点一次展开,单号降为副标题(与植入额明细同一取舍)
            g['sub'] = b['rows'][0]['name']
            g['rows'] = b['rows']
        else:
            g['rows'] = b['rows']
        groups.append(g)
    return groups, total


def _amount_envelope(title, groups, total, meta, basis):
    return {
        'title': title, 'kind': 'amount',
        'total': total,
        'total_display': _fmt_amount(total),
        'total_raw_display': _fmt_amount_raw(total),
        'unit': _unit_display('amount'),
        'meta': meta, 'basis': basis, 'groups': groups,
    }


def _detail_sales(scope, title_key, basis_key):
    def _fn(user, s, e):
        from flask_babel import gettext as _g
        from app.models.pricing_order import PricingOrder
        rows = (_q_sales(user, s, e, scope)
                .order_by(PricingOrder.approved_at).all())
        recs = [((po.project.project_name if po.project else None), po) for po in rows]
        groups, total = _group_by_project(
            recs,
            label_of=lambda po: po.order_number or f'#{po.id}',
            amount_of=lambda po: po.pricing_total_amount,
            currency_of=lambda po: po.currency,
            sub_of=lambda po: _g('批准 %(d)s', d=_fmt_dt(po.approved_at)))
        return _amount_envelope(
            _g(title_key), groups, total,
            _g('%(p)d 个项目 · %(n)d 张批价单', p=len(groups), n=len(rows)),
            _g(basis_key))
    return _fn


def _detail_implant(scope, title_key, basis_key):
    def _fn(user, s, e):
        from flask_babel import gettext as _g
        from app.models.quotation import Quotation
        rows = (_q_implant(user, s, e, scope)
                .order_by(Quotation.created_at).all())
        recs = [((q.project.project_name if q.project else None), q) for q in rows]
        groups, total = _group_by_project(
            recs,
            label_of=lambda q: q.quotation_number or f'#{q.id}',
            amount_of=lambda q: q.implant_total_amount,
            currency_of=lambda q: q.currency,
            sub_of=lambda q: _g('确认 %(d)s', d=_fmt_dt(q.confirmed_at)))
        return _amount_envelope(
            _g(title_key), groups, total,
            _g('%(p)d 个项目 · %(n)d 张报价单', p=len(groups), n=len(rows)),
            _g(basis_key))
    return _fn


_S_BASIS_OWN  = '归属:批价单创建人本人 · 仅已批准 · 按批准时间落期'
_S_BASIS_TEAM = '归属:本部门成员创建的批价单 · 仅已批准 · 按批准时间落期'
_S_BASIS_CHAN = '归属:渠道项目(报备来源=渠道)且厂商销售负责人为本人 · 仅已批准批价单'
# 植入额与「方案植入额」同名不同义,basis 必须点破,否则 HR 对不上两个数
_I_BASIS_OWN  = ('归属:项目拥有人本人(非报价创建人) · 仅计确认过的报价 · 按报价创建时间落期;'
                 '与「方案植入额」口径不同,两者不可直接比较')
_I_BASIS_TEAM = ('归属:项目拥有人 ∈ 本部门成员 · 仅计确认过的报价 · 按报价创建时间落期')
_I_BASIS_CHAN = ('归属:渠道项目且厂商销售负责人为本人 · 仅计确认过的报价')

_KPI_DETAIL_FNS.update({
    'sales_amount':           _detail_sales('own',     '销售额',   _S_BASIS_OWN),
    'team_sales_amount':      _detail_sales('team',    '团队销售额', _S_BASIS_TEAM),
    'channel_sales_amount':   _detail_sales('channel', '渠道销售额', _S_BASIS_CHAN),
    'implant_amount':         _detail_implant('own',     '植入额',   _I_BASIS_OWN),
    'team_implant_amount':    _detail_implant('team',    '团队植入额', _I_BASIS_TEAM),
    'channel_implant_amount': _detail_implant('channel', '渠道植入额', _I_BASIS_CHAN),
})


# ── 活跃度类(率)的下钻 ──────────────────────────────────────────────────
# 率类 = 分子/分母。明细的价值全在【不计入分子的那部分】—— 哪些客户睡了、
# 哪些项目拖了多久。所以按状态分组,达标组折叠、拖后腿的组标警示色并列出天数。
#
# ⚠️ 这三项都是【快照型】:采集器完全不看 s/e(见各 _act_* 实现),点 Q1 和点 Q3
# 得到的是同一份当前状态。basis 必须写明,否则 HR 会以为各季度应该不同。

_CUST_ACTIVE = ('highly_active', 'active', 'normal')     # 计入分子的客户状态
_PROJ_STALE_DAYS = 20                                    # 项目跟进超期阈值(与待办提醒同口径)


def _rate_envelope(title, num, den, groups, basis, meta_extra=''):
    from flask_babel import gettext as _g
    pct = round(num / den * 100, 1) if den else 100.0
    meta = _g('分母 %(d)d · 计入 %(n)d', d=den, n=num)
    return {
        'title': title, 'kind': 'rate',
        'total': pct,
        'total_display': f'{pct}',
        'unit': '%',
        'meta': meta + (' · ' + meta_extra if meta_extra else ''),
        'basis': basis, 'groups': groups,
    }


def _detail_customer_activity(scope_filters):
    def _fn(user, s, e):
        from flask_babel import gettext as _g
        from sqlalchemy import func
        from app import db
        from app.models.customer import Company
        from app.models.action import Action
        rows = (Company.query.filter(Company.is_deleted == False,   # noqa: E712
                                     *scope_filters(user)).all())
        den = len(rows)
        num = sum(1 for c in rows if c.status in _CUST_ACTIVE)
        # 最后跟进日:让「为什么睡了」可执行
        last = {}
        if rows:
            ids = [c.id for c in rows]
            last = dict(db.session.query(Action.company_id, func.max(Action.date))
                        .filter(Action.company_id.in_(ids)).group_by(Action.company_id).all())
        from datetime import date as _date
        today = _date.today()

        buckets = {}
        for c in rows:
            buckets.setdefault(c.status or 'unknown', []).append(c)
        order = list(_CUST_ACTIVE) + sorted(k for k in buckets if k not in _CUST_ACTIVE)
        groups = []
        for st in order:
            lst = buckets.get(st)
            if not lst:
                continue
            rws = []
            for c in sorted(lst, key=lambda x: (last.get(x.id) or _date.min)):
                ld = last.get(c.id)
                rws.append({'name': c.company_name or f'#{c.id}',
                            'sub': (_g('最后跟进 %(d)s · %(n)d 天前',
                                       d=ld.isoformat(), n=(today - ld).days)
                                    if ld else _g('从无跟进记录')),
                            'value_display': ''})
            g = {'label': _company_status_label(st), 'value': len(lst),
                 'value_display': f'{len(lst)} {_unit_display("count")}', 'rows': rws}
            if st not in _CUST_ACTIVE:
                g['tone'] = 'warn'          # 不计入分子 = 拖后腿的,标警示色
            groups.append(g)
        return _rate_envelope(
            _g('客户活跃度'), num, den, groups,
            _g('活跃度 = 状态为「高度活跃/活跃/正常」的客户数 ÷ 名下客户总数;'
               '状态由每日 01:00 跑批按跟进新鲜度维护。'
               '【快照型指标】反映当前状态,与所选季度无关,各期数值相同'))
    return _fn


def _company_status_label(st):
    """客户活跃状态中文名 —— 复用 activity_tracker.ACTIVITY_STATUS 这份权威映射,
    不自己维护第二份(实际取值是 churned/to_follow/dormant,与直觉的 lost/pending 不同)。"""
    from flask_babel import gettext as _g
    from app.utils.activity_tracker import ACTIVITY_STATUS
    if st in ACTIVITY_STATUS:
        return _g(ACTIVITY_STATUS[st])
    return _g('未标记') if st in (None, '', 'unknown') else st


def _detail_project_activity(proj_query):
    def _fn(user, s, e):
        from flask_babel import gettext as _g
        from sqlalchemy import func
        from datetime import datetime as _dt, date as _date
        from app import db
        from app.models.action import Action
        from app.models.projectpm_stage_history import ProjectStageHistory
        projs = proj_query(user)
        den = len(projs)
        if not den:
            return _rate_envelope(_g('项目活跃度'), 0, 0, [], _PROJ_ACT_BASIS())
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
        fresh, stale = [], []
        for p in projs:
            ld = last_act.get(p.id)
            if ld:
                days = (today - ld).days
                sub = _g('最后跟进 %(d)s · %(n)d 天前', d=ld.isoformat(), n=days)
            else:
                b = since.get(p.id) or p.created_at
                days = (now - b).days if b else 0
                sub = _g('从无跟进 · 建档/推进后 %(n)d 天', n=days)
            row = {'name': p.project_name or f'#{p.id}', 'sub': sub,
                   'value': days, 'value_display': ''}
            (stale if days >= _PROJ_STALE_DAYS else fresh).append(row)
        num = len(fresh)
        groups = []
        if fresh:
            groups.append({'label': _g('跟进及时 · 计入'), 'value': len(fresh),
                           'value_display': f'{len(fresh)} {_unit_display("count")}',
                           'rows': sorted(fresh, key=lambda r: -r['value'])})
        if stale:
            groups.append({'label': _g('超期未跟进 · 不计入'), 'value': len(stale),
                           'value_display': f'{len(stale)} {_unit_display("count")}',
                           'tone': 'warn',
                           'rows': sorted(stale, key=lambda r: -r['value'])})
        worst = max((r['value'] for r in stale), default=0)
        return _rate_envelope(
            _g('项目活跃度'), num, den, groups, _PROJ_ACT_BASIS(),
            _g('最久 %(n)d 天未跟进', n=worst) if worst else '')
    return _fn


def _PROJ_ACT_BASIS():
    from flask_babel import gettext as _g
    return _g('活跃度 = 最后跟进 <20 天的项目数 ÷ 在跟项目数(已排除 签约/暂停/失败);'
              '无跟进记录的按建档或最近阶段推进时间起算。'
              '【快照型指标】反映当前状态,与所选季度无关,各期数值相同')


def _cust_scope_own(user):
    from app.models.customer import Company
    return [Company.owner_id == user.id]


def _cust_scope_team(user):
    from app.models.customer import Company
    return [Company.owner_id.in_(_dept_member_ids(user))]


def _proj_q_own(user):
    from sqlalchemy import or_
    from app.models.project import Project
    return Project.query.filter(
        Project.is_deleted == False,                       # noqa: E712
        ~Project.current_stage.in_(('signed', 'paused', 'lost')),
        or_(Project.owner_id == user.id,
            Project.vendor_sales_manager_id == user.id)).all()


def _proj_q_team(user):
    from sqlalchemy import or_
    from app.models.project import Project
    ids = _dept_member_ids(user)
    return Project.query.filter(
        Project.is_deleted == False,                       # noqa: E712
        ~Project.current_stage.in_(('signed', 'paused', 'lost')),
        or_(Project.owner_id.in_(ids),
            Project.vendor_sales_manager_id.in_(ids))).all()


def _proj_q_channel(user):
    from app.models.project import Project
    return Project.query.filter(
        *_channel_project_filter(user),
        ~Project.current_stage.in_(('signed', 'paused', 'lost'))).all()


_KPI_DETAIL_FNS.update({
    'customer_activity_rate':         _detail_customer_activity(_cust_scope_own),
    'team_customer_activity_rate':    _detail_customer_activity(_cust_scope_team),
    'channel_customer_activity_rate': _detail_customer_activity(_cust_scope_own),  # 渠道口径同个人
    'project_activity_rate':          _detail_project_activity(_proj_q_own),
    'team_project_activity_rate':     _detail_project_activity(_proj_q_team),
    'channel_project_activity_rate':  _detail_project_activity(_proj_q_channel),
})


# ═══════════════════════════════════════════════════════════════════════════
# 产品经理(product_manager)下钻明细
# 形态:金额类 = 分类 › 产品 › 单据(三层);新品上市/任务类 = 分组 + 行(两层)。
# 每个 provider 的数据来源都与对应采集器共用同一段口径(见「PM 归属口径」注释块)。
# ═══════════════════════════════════════════════════════════════════════════

def _pm_basis(kind):
    """各 PM 指标的口径说明。**三个指标归属口径互不相同**(见「PM 归属口径」注释块),
    不逐条写清楚,HR 拿两个数字横向对比必然得出错误结论。"""
    from flask_babel import gettext as _g
    return {
        'implant': _g('归属:分管产品分类 · 金额取报价单植入小计(该字段仅对厂商产品置数)'
                      ' · 期内全部报价单,按报价创建时间落期'),
        'sales':   _g('归属:产品归属人或分类负责人,且该人角色为产品经理 · 仅厂商产品'
                      ' · 仅已批准批价单,按批准时间落期'),
        'launch':  _g('计入:期内新建 + 厂商产品 + 状态为在产;'
                      '归属为产品归属人或分类负责人(不限该人角色)'),
    }[kind]


def _pm_amount_envelope(title, cats, total, meta, basis):
    """金额类三层信封:分类 › 产品 › 单据。

    cats: {分类名: {'value': float, 'prods': {产品键: {'label','sub','value','rows'}}}}

    只分管一个分类时(实测:张贺只管「应用」,苏文 2 个,施裕庚 4 个)把分类层降为
    副标题,产品直接上浮成顶层组 —— 沿用 SE 明细「不分叉的层不让用户多点一次」的
    既有约定,否则单分类的人每次都要先点开一个恒为全部的壳。
    """

    def _prod_groups(cat_name, cat):
        out = []
        for p in sorted(cat['prods'].values(), key=lambda x: -x['value']):
            g = {'label': p['label'], 'value': p['value'],
                 'value_display': _fmt_amount_raw(p['value']), 'rows': p['rows']}
            if p.get('sub') or cat_name:
                g['sub'] = ' · '.join(x for x in (p.get('sub'), cat_name) if x)
            out.append(g)
        return out

    ordered = sorted(cats.items(), key=lambda kv: -kv[1]['value'])
    if len(ordered) == 1:
        groups = _prod_groups(ordered[0][0], ordered[0][1])
    else:
        groups = [{
            'label': name,
            'value': cat['value'],
            'value_display': _fmt_amount_raw(cat['value']),
            'children': _prod_groups('', cat),
        } for name, cat in ordered]

    return {
        'title': title,
        'kind': 'amount',
        'total': total,
        'unit': _unit_display('amount'),
        'total_display': _fmt_amount(total),
        'total_raw_display': _fmt_amount_raw(total),
        'meta': meta,
        'basis': basis,
        'groups': groups,
    }


def _detail_pm_implant(user, s, e):
    """产品植入额明细:分类 › 产品 › 报价单。

    金额取 **implant_subtotal**(与采集器同字段)。不是 SE 那样的 quantity ×
    market_price —— 两者在有整单折扣/旧数据时并不相等,换字段会当场对不上。
    """
    from flask_babel import gettext as _g
    from app.models.quotation import Quotation, QuotationDetail
    from app.models.product import Product
    from app.models.product_code import ProductCategory
    from app.models.project import Project

    q = _q_pm_implant(user, s, e)
    if q is None:
        return _pm_amount_envelope(
            _g('产品植入额'), {}, 0.0,
            _g('未分管任何产品分类'), _pm_basis('implant'))

    rows = q.outerjoin(
        ProductCategory, ProductCategory.id == Product.category_id).outerjoin(
        Project, Project.id == Quotation.project_id).with_entities(
        ProductCategory.name.label('cat_name'),
        Product.product_mn.label('p_mn'),
        Product.product_name.label('p_name'),
        Project.project_name.label('proj_name'),
        Quotation.quotation_number.label('q_no'),
        Quotation.currency.label('currency'),
        QuotationDetail.quantity.label('qty'),
        QuotationDetail.implant_subtotal.label('amt'),
    ).all()

    cats, total, n_prod, n_quo = {}, 0.0, set(), set()
    for r in rows:
        amt = _conv_money(float(r.amt or 0), r.currency)
        if not amt:
            continue          # 非厂商产品行 implant_subtotal 恒为 0,列出来纯噪音
        total += amt
        cat_name = r.cat_name or _g('(未分类)')
        cat = cats.setdefault(cat_name, {'value': 0.0, 'prods': {}})
        cat['value'] += amt
        key = r.p_mn or r.p_name or '—'
        n_prod.add(key)
        n_quo.add(r.q_no)
        pg = cat['prods'].setdefault(key, {
            'label': r.p_name or r.p_mn or '—', 'sub': r.p_mn or '',
            'value': 0.0, 'rows': []})
        pg['value'] += amt
        pg['rows'].append({
            'name': r.proj_name or _g('(无关联项目)'),
            'sub': r.q_no or '',
            'qty': float(r.qty or 0),
            'value': amt,
            'value_display': _fmt_amount_raw(amt),
        })

    return _pm_amount_envelope(
        _g('产品植入额'), cats, total,
        _g('%(c)d 个分类 · %(p)d 个产品 · %(q)d 张报价单',
           c=len(cats), p=len(n_prod), q=len(n_quo)),
        _pm_basis('implant'))


def _detail_pm_sales(user, s, e):
    """产品批价额明细:分类 › 产品 › 批价单(按批准时间落窗口)。"""
    from sqlalchemy import text
    from app import db
    from flask_babel import gettext as _g

    rows = db.session.execute(text("WITH " + _PM_PRODUCT_PM_CTE + """
        SELECT COALESCE(pc.name, '') AS cat_name,
               pod.product_mn        AS p_mn,
               COALESCE(NULLIF(pod.product_name, ''), pod.product_mn) AS p_name,
               pj.project_name       AS proj_name,
               po.order_number       AS o_no,
               po.approved_at        AS approved_at,
               po.currency           AS currency,
               pod.quantity          AS qty,
               pod.total_price       AS amt
        FROM pricing_order_details pod
        JOIN pricing_orders po ON pod.pricing_order_id = po.id
        JOIN product_pm pp     ON pod.product_mn = pp.product_mn
        LEFT JOIN products p          ON p.product_mn = pod.product_mn
        LEFT JOIN product_categories pc ON pc.id = p.category_id
        LEFT JOIN projects pj         ON pj.id = po.project_id
        WHERE pp.pm_id = :uid AND po.status = 'approved'
          AND po.approved_at >= :s AND po.approved_at < :e
        ORDER BY pc.name, pod.product_mn, po.approved_at
    """), {'uid': user.id, 's': s, 'e': e}).fetchall()

    cats, total, n_prod, n_ord = {}, 0.0, set(), set()
    for r in rows:
        amt = _conv_money(float(r.amt or 0), r.currency)
        total += amt
        cat_name = r.cat_name or _g('(未分类)')
        cat = cats.setdefault(cat_name, {'value': 0.0, 'prods': {}})
        cat['value'] += amt
        key = r.p_mn or r.p_name or '—'
        n_prod.add(key)
        n_ord.add(r.o_no)
        pg = cat['prods'].setdefault(key, {
            'label': r.p_name or r.p_mn or '—', 'sub': r.p_mn or '',
            'value': 0.0, 'rows': []})
        pg['value'] += amt
        pg['rows'].append({
            'name': r.proj_name or _g('(无关联项目)'),
            # 批价单带批准时间:窗口是按 approved_at 切的,不标出来无法核对边界
            'sub': ' · '.join(x for x in (r.o_no, _fmt_dt(r.approved_at)) if x),
            'qty': float(r.qty or 0),
            'value': amt,
            'value_display': _fmt_amount_raw(amt),
        })

    return _pm_amount_envelope(
        _g('产品批价额'), cats, total,
        _g('%(c)d 个分类 · %(p)d 个产品 · %(o)d 张批价单',
           c=len(cats), p=len(n_prod), o=len(n_ord)),
        _pm_basis('sales'))


def _detail_pm_new_launch(user, s, e):
    """新品上市明细:按分类列出期内新建的厂商产品。

    未计入组列的是**期内新建但状态不在产**的产品(停产/下架/草稿)—— 采集器只数
    status='active',不把被排除的那部分摆出来,「为什么只算了 14 个」就没法自查。
    """
    from sqlalchemy import text
    from app import db
    from flask_babel import gettext as _g

    rows = db.session.execute(text(f"""
        SELECT COALESCE(pc.name, '') AS cat_name,
               p.product_mn          AS p_mn,
               p.product_name        AS p_name,
               p.status              AS status,
               p.created_at          AS created_at,
               (p.owner_id = :uid)   AS by_owner
        FROM products p
        LEFT JOIN product_categories pc ON pc.id = p.category_id
        WHERE p.is_vendor_product = true
          AND p.created_at >= :s AND p.created_at < :e
          AND {_PM_LAUNCH_WHERE}
        ORDER BY pc.name, p.created_at
    """), {'uid': user.id, 's': s, 'e': e}).fetchall()

    ok_by_cat, bad = {}, []
    n_ok = 0
    for r in rows:
        item = {
            'name': r.p_name or r.p_mn or '—',
            'sub': ' · '.join(x for x in (
                r.p_mn,
                _fmt_dt(r.created_at),
                # 归属来源:同一个人可能既是产品归属人又是分类负责人,标出来才能解释
                # 「这个产品凭什么算我的」
                _g('本人归属') if r.by_owner else _g('分管分类'),
            ) if x),
            'value_display': '',
        }
        if r.status == 'active':
            n_ok += 1
            cat = r.cat_name or _g('(未分类)')
            ok_by_cat.setdefault(cat, []).append(item)
        else:
            item['sub'] += ' · ' + _g('状态 %(st)s', st=r.status or '—')
            bad.append(item)

    groups = []
    for cat, items in sorted(ok_by_cat.items(), key=lambda kv: -len(kv[1])):
        groups.append({'label': cat, 'value': len(items),
                       'value_display': f'{len(items)} {_unit_display("count")}',
                       'rows': items})
    if bad:
        groups.append({'label': _g('非在产 · 不计入'), 'value': len(bad),
                       'value_display': f'{len(bad)} {_unit_display("count")}',
                       'tone': 'warn', 'rows': bad})

    return {
        'title': _g('新品上市'),
        'kind': 'count',
        'total': float(n_ok),
        'total_display': str(n_ok),
        'unit': _unit_display('count'),
        'meta': _g('本期新建 %(t)d 个,在产 %(o)d,非在产 %(b)d',
                   t=len(rows), o=n_ok, b=len(bad)),
        'basis': _pm_basis('launch'),
        'groups': groups,
    }


def _task_score_label(w):
    """三档评价的显示名。与 _act_task_count_reviewed 的 review_score 同源
    (旧数据无评价兜底 1.0)。**必须写成字面量 msgid**,_g(变量) pybabel 提取不到。"""
    from flask_babel import gettext as _g
    if w <= 0.5:
        return _g('低于预期')
    if w >= 1.5:
        return _g('超出预期')
    return _g('符合预期')


def _detail_pm_task(task_type, title_fn):
    """任务类明细(研发/质量/上市支持):三组 —— 已通过(计入) / 已完成待审核 / 进行中。

    ⚠️ 这三个指标的实际值**不是任务条数,是按评价档位加权求和**(低于预期 0.5 /
    符合 1 / 超出 1.5,旧数据兜底 1.0)。所以每行必须标出该条的权重,否则会出现
    「1 条任务却显示 1.50」而被当成算错(实测张贺 2026Q2 正是这种情况)。

    后两组不计入分子,但必须列 —— 点开一个 0 时能立刻区分「根本没建任务」/
    「建了没完成」/「完成了没人审核」,前两者是业务问题,第三者是流程卡壳。
    """
    def _fn(user, s, e):
        from datetime import datetime as _dtm
        from flask_babel import gettext as _g
        from app.models.task import Task
        from app.models.user import User

        base = Task.query.filter(
            Task.assignee_id == user.id,
            Task.task_type == task_type,
            Task.is_deleted == False)

        # 计入组:与采集器逐字同条件(审核通过 + 有完成时间 + 完成时间落窗口)
        done = base.filter(
            Task.review_status == 'approved',
            Task.completed_at.isnot(None),
            Task.completed_at >= s, Task.completed_at < e,
        ).order_by(Task.completed_at).all()

        # 未计入组只按完成/创建时间粗筛到本期,不要求审核通过
        pending = base.filter(
            Task.status == 'completed',
            (Task.review_status.is_(None)) | (Task.review_status != 'approved'),
            Task.completed_at.isnot(None),
            Task.completed_at >= s, Task.completed_at < e,
        ).order_by(Task.completed_at).all()

        doing = base.filter(
            Task.status != 'completed',
            Task.created_at < e,
        ).order_by(Task.due_date.is_(None), Task.due_date).all()

        reviewers = {}
        rids = [t.reviewer_id for t in done if t.reviewer_id]
        if rids:
            reviewers = {u.id: (u.real_name or u.username)
                         for u in User.query.filter(User.id.in_(rids)).all()}

        today = _dtm.now()
        total = 0.0
        ok_rows = []
        for t in done:
            w = float(t.review_score if t.review_score is not None else 1.0)
            total += w
            label = _task_score_label(w)
            ok_rows.append({
                'name': t.title,
                'sub': ' · '.join(x for x in (
                    f'{label} ×{w:g}',
                    _g('完成 %(d)s', d=_fmt_dt(t.completed_at)),
                    _g('审核 %(n)s', n=reviewers[t.reviewer_id]) if t.reviewer_id in reviewers else '',
                ) if x),
                'value_display': f'{w:g}',
            })

        pend_rows = [{
            'name': t.title,
            'sub': ' · '.join([_g('完成 %(d)s', d=_fmt_dt(t.completed_at)),
                               _g('已等 %(n)d 天', n=max(0, (today - t.completed_at).days))]),
            'value_display': '',
        } for t in pending]

        # 状态走 status_meta 的统一映射 —— 直接印 t.status 会把 in_progress 这种
        # 原始 code 摆到用户面前,也与全站徽章文案对不上。
        from app.utils.status_meta import get_status_label
        doing_rows = []
        for t in doing:
            # 创建时间必须标:本组不按窗口下界切(列的是「截至期末仍未完成」的快照),
            # 看历史季度时会混进更早创建的老任务,不标日期没法判断是不是积压。
            bits = [get_status_label(t.status, 'task'),
                    _g('建于 %(d)s', d=_fmt_dt(t.created_at))]
            if t.due_date:
                overdue = (today - t.due_date).days
                bits.append(_g('逾期 %(n)d 天', n=overdue) if overdue > 0
                            else _g('截止 %(d)s', d=_fmt_dt(t.due_date)))
            doing_rows.append({'name': t.title, 'sub': ' · '.join(bits),
                               'value_display': ''})

        groups = []
        if ok_rows:
            groups.append({'label': _g('已审核通过 · 计入本期'), 'value': total,
                           'value_display': f'{total:g}', 'rows': ok_rows})
        if pend_rows:
            groups.append({'label': _g('已完成 · 待审核(不计入)'), 'value': len(pend_rows),
                           'value_display': f'{len(pend_rows)} {_unit_display("count")}',
                           'tone': 'warn', 'rows': pend_rows})
        if doing_rows:
            groups.append({'label': _g('进行中 · 未完成(不计入)'), 'value': len(doing_rows),
                           'value_display': f'{len(doing_rows)} {_unit_display("count")}',
                           'tone': 'warn', 'rows': doing_rows})

        return {
            'title': title_fn(),
            'kind': 'count',
            'total': total,
            'total_display': f'{total:g}',
            'unit': _unit_display('count'),
            'meta': _g('计入 %(o)d 条(加权 %(w)s)· 待审核 %(p)d · 进行中 %(d)d',
                       o=len(ok_rows), w=f'{total:g}', p=len(pend_rows), d=len(doing_rows)),
            'basis': _g('计入:本人为负责人 + 已完成 + 审核通过,按完成时间落期;'
                        '数值为评价加权和(低于预期 0.5 / 符合 1 / 超出 1.5,无评价按 1)'),
            'groups': groups,
        }
    return _fn


from flask_babel import gettext as _gt   # 注册表里 lambda 用

_KPI_DETAIL_FNS.update({
    'pm_implant_amount': _detail_pm_implant,
    'pm_sales_amount':   _detail_pm_sales,
    'pm_new_launch':     _detail_pm_new_launch,
    'pm_dev_rate':       _detail_pm_task('pm_rd', lambda: _gt('研发任务')),
    'pm_quality_rate':   _detail_pm_task('pm_quality', lambda: _gt('质量处理')),
    'pm_support_count':  _detail_pm_task('pm_launch_support', lambda: _gt('上市支持')),
})
