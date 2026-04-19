"""统一积分发放服务，所有触发点调用 award_points()"""
from datetime import datetime
from sqlalchemy import func
from app.extensions import db


def award_points(user_id, behavior_code, source_type=None, source_id=None, memo=None):
    """
    发放积分。检查 daily_cap 防刷，写入流水，更新汇总缓存。
    返回实际发放的积分数（0 表示被上限拦截或重复触发）。
    在调用方的 db.session 中执行，调用方负责 commit。
    """
    from app.models.points import PointsBehaviorConfig, PointsTransaction, UserPointsSummary

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
    """启动时调用：将 BEHAVIOR_REGISTRY 中缺失的行为写入数据库（不覆盖已有配置）。"""
    from app.services.points_registry import BEHAVIOR_REGISTRY
    from app.models.points import PointsBehaviorConfig
    changed = False
    for code, meta in BEHAVIOR_REGISTRY.items():
        if not PointsBehaviorConfig.query.filter_by(behavior_code=code).first():
            db.session.add(PointsBehaviorConfig(
                behavior_code=code,
                behavior_name=meta['name'],
                category=meta['category'],
                points=meta['default_points'],
                daily_cap=meta['default_daily_cap'],
                is_active=True,
            ))
            changed = True
    if changed:
        db.session.commit()
