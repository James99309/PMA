"""产品积分计算工具函数

积分 = 系数 × retail_price
系数从初始值按时间衰减至底线值
"""
from datetime import datetime, timezone

# === 硬编码算法参数 ===
INITIAL_COEFFICIENT = 3.0        # 默认初始系数
DECAY_RATE = 0.5                 # 每周期衰减量
DECAY_INTERVAL_MONTHS = 3        # 衰减周期(月)
FLOOR_COEFFICIENT = 1.0          # 系数底线

# 积分等级阈值
TIER_GOLD_MIN = 10_000_000
TIER_SILVER_MIN = 1_000_000
TIER_BRONZE_MIN = 100_000


def calculate_decaying_coefficient(start_value=None, start_time=None):
    """统一衰减计算：从start_value开始，按时间衰减至floor

    Args:
        start_value: 起始系数(None则用INITIAL_COEFFICIENT)
        start_time: 衰减起始时间(None则不衰减，返回start_value)
    """
    if start_value is None:
        start_value = INITIAL_COEFFICIENT
    if not start_time:
        return max(start_value, FLOOR_COEFFICIENT)

    # 处理 timezone-naive datetime
    now = datetime.now(timezone.utc)
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)

    months = (now - start_time).days / 30.44
    periods = int(months / DECAY_INTERVAL_MONTHS)
    coeff = start_value - DECAY_RATE * periods
    return max(coeff, FLOOR_COEFFICIENT)


def get_points_tier(points):
    """根据积分值返回等级: 'gold'/'silver'/'bronze'/'none'"""
    if points >= TIER_GOLD_MIN:
        return 'gold'
    elif points >= TIER_SILVER_MIN:
        return 'silver'
    elif points >= TIER_BRONZE_MIN:
        return 'bronze'
    return 'none'


def format_points_display(points):
    """缩位显示积分，金币颜色代表单位

    gold (>=10M): ÷10,000,000 → 2位小数
    silver (>=1M): ÷1,000,000 → 1位小数
    bronze (>=100K): ÷100,000 → 1位小数
    none (<100K): 原数带千分位
    """
    if points >= TIER_GOLD_MIN:
        return '{:.2f}'.format(points / TIER_GOLD_MIN)
    elif points >= TIER_SILVER_MIN:
        return '{:.1f}'.format(points / TIER_SILVER_MIN)
    elif points >= TIER_BRONZE_MIN:
        return '{:.1f}'.format(points / TIER_BRONZE_MIN)
    return '{:,.0f}'.format(points)


def get_tier_color_class(tier):
    """Tailwind CSS文字色类"""
    return {
        'gold': 'text-yellow-600',
        'silver': 'text-zinc-500',
        'bronze': 'text-orange-500',
        'none': 'text-slate-600'
    }.get(tier, 'text-slate-600')


def calculate_points_for_quotation_details(details):
    """批量计算报价单明细积分(通过product_mn批量查询,避免N+1)

    Args:
        details: QuotationDetail列表

    Returns:
        (detail_points_map, total_points)
        detail_points_map: {detail.id: points}
        total_points: 总积分
    """
    from app.models.product import Product

    # 收集所有product_mn
    mn_set = set()
    for d in details:
        if d.product_mn:
            mn_set.add(d.product_mn)

    if not mn_set:
        return {}, 0

    # 批量查询产品
    products = Product.query.filter(Product.product_mn.in_(mn_set)).all()
    product_map = {p.product_mn: p for p in products}

    detail_points_map = {}
    total_points = 0
    for d in details:
        pts = 0
        if d.product_mn and d.product_mn in product_map:
            p = product_map[d.product_mn]
            pts = p.points
        detail_points_map[d.id] = pts
        total_points += pts

    return detail_points_map, total_points


def sync_quotation_points(quotation):
    """报价单积分快照 → 按明细年份分组写入/更新 ledger

    同一报价单可在不同年份各有一条 ledger 记录，
    年份取自 QuotationDetail.created_at.year。
    """
    from app.models.product import Product
    from app.models.user_points_ledger import UserPointsLedger
    from app.extensions import db

    user_id = quotation.owner_id

    # 按 detail.created_at.year 分组计算积分
    year_points = {}  # {year: total_points}
    if quotation.details:
        mn_set = {d.product_mn for d in quotation.details if d.product_mn}
        if mn_set:
            products = Product.query.filter(Product.product_mn.in_(mn_set)).all()
            product_map = {p.product_mn: p for p in products}
            for d in quotation.details:
                yr = d.created_at.year if d.created_at else quotation.created_at.year
                pts = product_map[d.product_mn].points if (d.product_mn and d.product_mn in product_map) else 0
                year_points[yr] = year_points.get(yr, 0) + pts

    # 查出该报价单已有的所有 ledger 条目
    existing = UserPointsLedger.query.filter_by(
        user_id=user_id, source_type='quotation', source_id=quotation.id
    ).all()
    existing_map = {e.year: e for e in existing}

    # upsert 每个年份
    for yr, pts in year_points.items():
        if yr in existing_map:
            existing_map[yr].points = pts
            del existing_map[yr]
        else:
            db.session.add(UserPointsLedger(
                user_id=user_id, year=yr,
                source_type='quotation', source_id=quotation.id,
                points=pts, memo=f'Q#{quotation.quotation_number}'
            ))

    # 删除不再有积分的年份条目
    for leftover in existing_map.values():
        db.session.delete(leftover)


def delete_quotation_points(quotation_id):
    """删除报价单对应的积分记录（销售 + PM + SE）"""
    from app.models.user_points_ledger import UserPointsLedger
    from app.extensions import db
    UserPointsLedger.query.filter(
        UserPointsLedger.source_id == quotation_id,
        UserPointsLedger.source_type.in_(['quotation', 'pm_category', 'se_project'])
    ).delete(synchronize_session=False)


def sync_pm_category_points(quotation):
    """报价单中产品经理负责分类的积分 → 按明细年份分组写入/更新 ledger

    先按 detail.created_at.year 分组，再按 category → PM 汇总，
    每个 (PM user, year) 一条 ledger。
    """
    from app.models.product import Product
    from app.models.product_code import ProductCategory
    from app.models.user_points_ledger import UserPointsLedger
    from app.extensions import db

    if not quotation.details:
        # 无明细则清除该报价单所有旧 PM 积分
        UserPointsLedger.query.filter_by(
            source_type='pm_category', source_id=quotation.id
        ).delete()
        return

    # 收集所有 product_mn
    mn_set = {d.product_mn for d in quotation.details if d.product_mn}
    if not mn_set:
        UserPointsLedger.query.filter_by(
            source_type='pm_category', source_id=quotation.id
        ).delete()
        return

    # 批量查产品 → 拿到 category_id 和 points
    products = Product.query.filter(Product.product_mn.in_(mn_set)).all()
    product_map = {p.product_mn: p for p in products}

    # 按 (year, category_id) 汇总积分
    year_cat_points = {}  # {(year, category_id): total_points}
    for d in quotation.details:
        if d.product_mn and d.product_mn in product_map:
            p = product_map[d.product_mn]
            if p.category_id:
                yr = d.created_at.year if d.created_at else quotation.created_at.year
                key = (yr, p.category_id)
                year_cat_points[key] = year_cat_points.get(key, 0) + p.points

    if not year_cat_points:
        UserPointsLedger.query.filter_by(
            source_type='pm_category', source_id=quotation.id
        ).delete()
        return

    # 批量查分类 → 拿到 manager_id
    cat_ids = {cat_id for _, cat_id in year_cat_points.keys()}
    categories = ProductCategory.query.filter(
        ProductCategory.id.in_(cat_ids)
    ).all()
    cat_manager = {c.id: c.manager_id for c in categories if c.manager_id}

    # 按 (PM, year) 汇总
    pm_year_points = {}  # {(user_id, year): total_points}
    for (yr, cat_id), pts in year_cat_points.items():
        mgr = cat_manager.get(cat_id)
        if mgr:
            key = (mgr, yr)
            pm_year_points[key] = pm_year_points.get(key, 0) + pts

    # 查出该报价单已有的所有 PM ledger 条目
    existing = UserPointsLedger.query.filter_by(
        source_type='pm_category', source_id=quotation.id
    ).all()
    existing_map = {(e.user_id, e.year): e for e in existing}

    # upsert 每个 (PM, year)
    for (uid, yr), pts in pm_year_points.items():
        if (uid, yr) in existing_map:
            existing_map[(uid, yr)].points = pts
            del existing_map[(uid, yr)]
        else:
            db.session.add(UserPointsLedger(
                user_id=uid, year=yr,
                source_type='pm_category', source_id=quotation.id,
                points=pts, memo=f'PM:Q#{quotation.quotation_number}'
            ))

    # 删除不再需要的条目
    for leftover in existing_map.values():
        db.session.delete(leftover)


# SE 合格项目互动门槛
QUALIFIED_INTERACTION_MIN = 3


def sync_se_project_points(quotation):
    """SE项目积分：合格项目中厂商产品的积分 → 按明细年份写入 ledger

    流程:
    1. 获取 quotation.project_id，无则跳过
    2. 查 project_members 找 role='solution_engineer' 的用户
    3. 对每个 SE 计算互动数 (work_items created + shared + actions)
    4. 互动 ≥3 → 合格 → 累加该报价单中厂商产品的 product.points
    5. 按 (SE user_id, year) upsert ledger
    """
    from app.models.product import Product
    from app.models.relation import ProjectMember
    from app.models.worklog import WorkItem
    from app.models.action import Action
    from app.models.user_points_ledger import UserPointsLedger
    from app.extensions import db
    from sqlalchemy import func, cast, Integer
    from sqlalchemy.dialects.postgresql import JSONB

    project_id = quotation.project_id
    if not project_id:
        # 无关联项目 → 清除该报价单所有旧 SE 积分
        UserPointsLedger.query.filter_by(
            source_type='se_project', source_id=quotation.id
        ).delete()
        return

    # 找该项目的 SE 成员
    se_members = ProjectMember.query.filter_by(
        project_id=project_id, role='solution_engineer'
    ).all()
    se_user_ids = [m.user_id for m in se_members]

    if not se_user_ids:
        UserPointsLedger.query.filter_by(
            source_type='se_project', source_id=quotation.id
        ).delete()
        return

    # 批量计算每个 SE 的互动数（3 个 COUNT 合并为一次查询）
    # 互动 = 创建的 work_items + 被分享的 work_items + 创建的 actions
    qualified_ses = set()
    for uid in se_user_ids:
        # work_items created by SE for this project
        wi_created = WorkItem.query.filter_by(
            owner_id=uid, project_id=project_id
        ).count()

        # work_items shared with SE for this project
        wi_shared = WorkItem.query.filter(
            WorkItem.project_id == project_id,
            WorkItem.shared_with_users.cast(db.Text).contains(str(uid))
        ).count()

        # actions created by SE for this project
        act_count = Action.query.filter_by(
            owner_id=uid, project_id=project_id
        ).count()

        if wi_created + wi_shared + act_count >= QUALIFIED_INTERACTION_MIN:
            qualified_ses.add(uid)

    if not qualified_ses:
        UserPointsLedger.query.filter_by(
            source_type='se_project', source_id=quotation.id
        ).delete()
        return

    # 计算厂商产品积分（按明细年份分组）
    if not quotation.details:
        UserPointsLedger.query.filter_by(
            source_type='se_project', source_id=quotation.id
        ).delete()
        return

    mn_set = {d.product_mn for d in quotation.details if d.product_mn}
    if not mn_set:
        UserPointsLedger.query.filter_by(
            source_type='se_project', source_id=quotation.id
        ).delete()
        return

    products = Product.query.filter(
        Product.product_mn.in_(mn_set),
        Product.is_vendor_product == True
    ).all()
    product_map = {p.product_mn: p for p in products}

    # 按年份汇总厂商产品积分
    year_points = {}
    for d in quotation.details:
        if d.product_mn and d.product_mn in product_map:
            yr = d.created_at.year if d.created_at else quotation.created_at.year
            year_points[yr] = year_points.get(yr, 0) + product_map[d.product_mn].points

    if not year_points:
        UserPointsLedger.query.filter_by(
            source_type='se_project', source_id=quotation.id
        ).delete()
        return

    # 每个合格 SE 都获得同样的积分 → 按 (SE, year) upsert
    se_year_points = {}
    for uid in qualified_ses:
        for yr, pts in year_points.items():
            se_year_points[(uid, yr)] = pts

    existing = UserPointsLedger.query.filter_by(
        source_type='se_project', source_id=quotation.id
    ).all()
    existing_map = {(e.user_id, e.year): e for e in existing}

    for (uid, yr), pts in se_year_points.items():
        if (uid, yr) in existing_map:
            existing_map[(uid, yr)].points = pts
            del existing_map[(uid, yr)]
        else:
            db.session.add(UserPointsLedger(
                user_id=uid, year=yr,
                source_type='se_project', source_id=quotation.id,
                points=pts, memo=f'SE:Q#{quotation.quotation_number}'
            ))

    # 删除不再需要的条目（SE 不再合格或积分归零）
    for leftover in existing_map.values():
        db.session.delete(leftover)


def transfer_quotation_points(quotation, new_owner_id):
    """报价单转移所有权时更新积分归属（可能有多条不同年份的条目）"""
    from app.models.user_points_ledger import UserPointsLedger
    entries = UserPointsLedger.query.filter_by(
        source_type='quotation', source_id=quotation.id
    ).all()
    for entry in entries:
        entry.user_id = new_owner_id
