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
    """根据积分值返回等级: 'gold'/'silver'/'bronze'"""
    if points >= TIER_GOLD_MIN:
        return 'gold'
    elif points >= TIER_SILVER_MIN:
        return 'silver'
    return 'bronze'


def get_tier_color_class(tier):
    """Tailwind CSS文字色类"""
    return {
        'gold': 'text-yellow-600',
        'silver': 'text-zinc-500',
        'bronze': 'text-orange-500'
    }.get(tier, 'text-orange-500')


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
    """报价单积分快照 → 写入/更新 ledger"""
    from app.models.user_points_ledger import UserPointsLedger
    from app.extensions import db

    total_points = 0
    if quotation.details:
        _, total_points = calculate_points_for_quotation_details(quotation.details)

    year = quotation.created_at.year
    user_id = quotation.owner_id

    entry = UserPointsLedger.query.filter_by(
        user_id=user_id, source_type='quotation', source_id=quotation.id
    ).first()

    if entry:
        entry.points = total_points
        entry.year = year
    else:
        entry = UserPointsLedger(
            user_id=user_id, year=year,
            source_type='quotation', source_id=quotation.id,
            points=total_points,
            memo=f'Q#{quotation.quotation_number}'
        )
        db.session.add(entry)


def delete_quotation_points(quotation_id):
    """删除报价单对应的积分记录"""
    from app.models.user_points_ledger import UserPointsLedger
    from app.extensions import db
    UserPointsLedger.query.filter_by(
        source_type='quotation', source_id=quotation_id
    ).delete()


def transfer_quotation_points(quotation, new_owner_id):
    """报价单转移所有权时更新积分归属"""
    from app.models.user_points_ledger import UserPointsLedger
    entry = UserPointsLedger.query.filter_by(
        source_type='quotation', source_id=quotation.id
    ).first()
    if entry:
        entry.user_id = new_owner_id
