"""统一积分发放服务，所有触发点调用 award_points()"""
from datetime import datetime
from sqlalchemy import func
from app.extensions import db


def _build_memo(behavior_code, context=None):
    """根据数据库实例语言和行为注册表自动生成 memo。
    语言由 IS_OVS 配置决定（SG=英文，CN=中文），与请求语言无关。
    """
    from app.services.points_registry import BEHAVIOR_REGISTRY
    try:
        from flask import current_app
        is_en = current_app.config.get('IS_OVS', False)
    except Exception:
        is_en = False
    behavior = BEHAVIOR_REGISTRY.get(behavior_code, {})
    name = behavior.get('name_en' if is_en else 'name') or behavior.get('name', behavior_code)
    return f'{name}: {context}' if context else name


def award_points(user_id, behavior_code, source_type=None, source_id=None, memo=None, context=None):
    """
    发放积分。检查 daily_cap 防刷，写入流水，更新汇总缓存。
    返回实际发放的积分数（0 表示被上限拦截或重复触发）。
    在调用方的 db.session 中执行，调用方负责 commit。

    memo:    显式指定说明文字（优先级最高）
    context: 对象名称等上下文，当 memo 为 None 时自动拼接行为名称
    """
    from app.models.points import PointsBehaviorConfig, PointsTransaction, UserPointsSummary
    if memo is None:
        memo = _build_memo(behavior_code, context)

    # 统一转字符串，兼容旧调用方传入整数 id
    if source_id is not None:
        source_id = str(source_id)

    config = PointsBehaviorConfig.query.filter_by(
        behavior_code=behavior_code, is_active=True
    ).first()
    if not config:
        return 0

    now = datetime.utcnow()
    year, month = now.year, now.month

    # 防重复：同一 source 同一行为只记一次
    if source_type and source_id:
        exists = PointsTransaction.query.filter_by(
            user_id=user_id,
            behavior_code=behavior_code,
            source_type=source_type,
            source_id=source_id,
        ).first()
        if exists:
            return 0

    # daily_cap 检查
    if config.daily_cap:
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_total = db.session.query(
            func.coalesce(func.sum(PointsTransaction.points), 0)
        ).filter(
            PointsTransaction.user_id == user_id,
            PointsTransaction.behavior_code == behavior_code,
            PointsTransaction.created_at >= today_start,
        ).scalar()
        if today_total >= config.daily_cap:
            return 0

    pts = config.points

    # 写入流水
    tx = PointsTransaction(
        user_id=user_id,
        behavior_code=behavior_code,
        source_type=source_type,
        source_id=source_id,
        points=pts,
        memo=memo,
        year=year,
        month=month,
    )
    db.session.add(tx)

    # 更新汇总缓存（月度 + 年度 month=0）
    for m in [month, 0]:
        summary = UserPointsSummary.query.filter_by(
            user_id=user_id, year=year, month=m
        ).first()
        if not summary:
            summary = UserPointsSummary(
                user_id=user_id, year=year, month=m,
                total_points=0, behavior_breakdown={}
            )
            db.session.add(summary)
        summary.total_points = (summary.total_points or 0) + pts
        breakdown = dict(summary.behavior_breakdown or {})
        breakdown[config.category] = breakdown.get(config.category, 0) + pts
        summary.behavior_breakdown = breakdown
        summary.updated_at = now

    db.session.flush()
    return pts


def sync_registry_to_db():
    """启动时调用：将 BEHAVIOR_REGISTRY 同步到数据库。
    - 缺失的行为：新增
    - 已有的行为：用注册表的默认值更新（积分值、每日上限、分类）
    """
    from app.services.points_registry import BEHAVIOR_REGISTRY
    from app.models.points import PointsBehaviorConfig
    changed = False
    for code, meta in BEHAVIOR_REGISTRY.items():
        existing = PointsBehaviorConfig.query.filter_by(behavior_code=code).first()
        if not existing:
            db.session.add(PointsBehaviorConfig(
                behavior_code=code,
                behavior_name=meta['name'],
                category=meta['category'],
                points=meta['default_points'],
                daily_cap=meta['default_daily_cap'],
                is_active=True,
            ))
            changed = True
        else:
            if (existing.points != meta['default_points'] or
                    existing.daily_cap != meta['default_daily_cap'] or
                    existing.category != meta['category'] or
                    existing.behavior_name != meta['name']):
                existing.points = meta['default_points']
                existing.daily_cap = meta['default_daily_cap']
                existing.category = meta['category']
                existing.behavior_name = meta['name']
                changed = True
    if changed:
        db.session.commit()
