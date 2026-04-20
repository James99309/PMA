from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models.points import PointsBehaviorConfig, PointsTransaction, UserPointsSummary
from app.models.user import User
from app.decorators import permission_required, admin_required

points_bp = Blueprint('points', __name__, url_prefix='/points')


@points_bp.route('/')
@login_required
def index():
    departments = db.session.query(User.department).filter(
        User.department.isnot(None),
        User.is_active == True
    ).distinct().order_by(User.department).all()
    departments = [d[0] for d in departments if d[0]]
    is_admin = current_user.role == 'admin'
    return render_template('points/tw_points.html', active_page='points',
                           departments=departments, is_admin=is_admin)


@points_bp.route('/api/leaderboard')
@login_required
def api_leaderboard():
    period = request.args.get('period', 'month')
    now = datetime.utcnow()
    year = now.year
    month = now.month

    if period == 'month':
        months = [month]
    elif period == 'quarter':
        q_start = ((month - 1) // 3) * 3 + 1
        months = list(range(q_start, min(q_start + 3, 13)))
    else:
        months = list(range(1, 13))

    rows = db.session.query(
        UserPointsSummary.user_id,
        func.sum(UserPointsSummary.total_points).label('total')
    ).filter(
        UserPointsSummary.year == year,
        UserPointsSummary.month.in_(months)
    ).group_by(UserPointsSummary.user_id).order_by(
        func.sum(UserPointsSummary.total_points).desc()
    ).all()

    user_ids = [r.user_id for r in rows]
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    result = []
    rank = 1
    for row in rows:
        u = users.get(row.user_id)
        if not u:
            continue
        result.append({
            'rank': rank,
            'user_id': row.user_id,
            'name': u.real_name or u.username,
            'department': getattr(u, 'department', '') or '',
            'total_points': int(row.total or 0),
            'is_me': row.user_id == current_user.id,
        })
        rank += 1

    return jsonify({'success': True, 'data': result})


@points_bp.route('/api/my-transactions')
@login_required
def api_my_transactions():
    period = request.args.get('period', 'month')
    page = request.args.get('page', 1, type=int)
    now = datetime.utcnow()
    year, month = now.year, now.month

    if period == 'month':
        months = [month]
    elif period == 'quarter':
        q_start = ((month - 1) // 3) * 3 + 1
        months = list(range(q_start, min(q_start + 3, 13)))
    else:
        months = list(range(1, 13))

    query = PointsTransaction.query.filter_by(user_id=current_user.id, year=year)
    if len(months) == 1:
        query = query.filter_by(month=months[0])
    else:
        query = query.filter(PointsTransaction.month.in_(months))

    pagination = query.order_by(PointsTransaction.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    # 汇总指定周期内的积分
    if len(months) == 1:
        summary = UserPointsSummary.query.filter_by(
            user_id=current_user.id, year=year, month=months[0]
        ).first()
        total = summary.total_points if summary else 0
        breakdown = dict(summary.behavior_breakdown or {}) if summary else {}
    else:
        summaries = UserPointsSummary.query.filter(
            UserPointsSummary.user_id == current_user.id,
            UserPointsSummary.year == year,
            UserPointsSummary.month.in_(months)
        ).all()
        total = sum(s.total_points for s in summaries)
        breakdown = {}
        for s in summaries:
            for k, v in (s.behavior_breakdown or {}).items():
                breakdown[k] = breakdown.get(k, 0) + v

    # 排名：同周期内比当前用户总分高的人数 + 1
    if len(months) == 1:
        rank_val = db.session.query(func.count(UserPointsSummary.user_id) + 1).filter(
            UserPointsSummary.year == year,
            UserPointsSummary.month == months[0],
            UserPointsSummary.total_points > total
        ).scalar()
        total_users = db.session.query(func.count(UserPointsSummary.user_id)).filter(
            UserPointsSummary.year == year,
            UserPointsSummary.month == months[0]
        ).scalar()
    else:
        # 季度/年度排名：需要聚合
        subq = db.session.query(
            UserPointsSummary.user_id,
            func.sum(UserPointsSummary.total_points).label('period_total')
        ).filter(
            UserPointsSummary.year == year,
            UserPointsSummary.month.in_(months)
        ).group_by(UserPointsSummary.user_id).subquery()
        rank_val = db.session.query(func.count() + 1).filter(
            subq.c.period_total > total
        ).scalar()
        total_users = db.session.query(func.count()).select_from(subq).scalar()

    transactions = [{
        'id': tx.id,
        'behavior_code': tx.behavior_code,
        'points': tx.points,
        'memo': tx.memo or '',
        'created_at': tx.created_at.strftime('%Y-%m-%d %H:%M'),
    } for tx in pagination.items]

    return jsonify({
        'success': True,
        'total_points': total,
        'rank': int(rank_val or 1),
        'total_users': int(total_users or 0),
        'breakdown': breakdown,
        'transactions': transactions,
        'has_next': pagination.has_next,
        'page': page,
    })


@points_bp.route('/api/nav-summary')
@login_required
def api_nav_summary():
    now = datetime.utcnow()
    year, month = now.year, now.month
    summary = UserPointsSummary.query.filter_by(
        user_id=current_user.id, year=year, month=month
    ).first()
    total = summary.total_points if summary else 0
    categories = []
    if summary and summary.behavior_breakdown:
        cat_names = {'knowledge': '知识贡献', 'business': '业务推进',
                     'task': '任务达成', 'content': '内容创作'}
        cat_names_en = {'knowledge': 'Knowledge', 'business': 'Business',
                        'task': 'Tasks', 'content': 'Content'}
        for k, v in summary.behavior_breakdown.items():
            categories.append({'name': cat_names.get(k, k), 'name_en': cat_names_en.get(k, k), 'points': v})
    return jsonify({'success': True, 'total_points': total, 'year': year, 'categories': categories})


@points_bp.route('/api/ai-leaderboard')
@login_required
def api_ai_leaderboard():
    """AI Token 使用量排行榜，支持 period=month/quarter/year"""
    from app.services.ai_usage_stats_service import get_ai_usage_stats
    period = request.args.get('period', 'month')
    now = datetime.utcnow()
    year, month = now.year, now.month

    if period == 'month':
        months = [month]
    elif period == 'quarter':
        q_start = ((month - 1) // 3) * 3 + 1
        months = list(range(q_start, min(q_start + 3, 13)))
    else:
        months = list(range(1, month + 1))

    # 按月聚合（stats service 是月维度的）
    user_totals = {}
    for m in months:
        result = get_ai_usage_stats(year, m)
        if not result.get('success'):
            continue
        for u in result['data'].get('user_breakdown', []):
            uid = u['user_id']
            if uid not in user_totals:
                user_totals[uid] = {
                    'user_id': uid,
                    'user_name': u['user_name'],
                    'total_tokens': 0,
                    'chat_tokens': 0,
                    'cli_tokens': 0,
                    'estimated_cost': 0.0,
                }
            user_totals[uid]['total_tokens']   += u['total_tokens']
            user_totals[uid]['chat_tokens']    += u.get('chat_tokens', 0)
            user_totals[uid]['cli_tokens']     += u.get('cli_tokens', 0)
            user_totals[uid]['estimated_cost'] += u['estimated_cost']

    sorted_users = sorted(user_totals.values(), key=lambda x: x['total_tokens'], reverse=True)

    user_ids = [u['user_id'] for u in sorted_users]
    users_db = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    data = []
    for rank, u in enumerate(sorted_users, 1):
        user_obj = users_db.get(u['user_id'])
        data.append({
            'rank': rank,
            'user_id': u['user_id'],
            'name': u['user_name'],
            'department': (getattr(user_obj, 'department', '') or '') if user_obj else '',
            'total_tokens': u['total_tokens'],
            'chat_tokens': u['chat_tokens'],
            'cli_tokens': u['cli_tokens'],
            'estimated_cost': round(u['estimated_cost'], 4),
            'is_me': u['user_id'] == current_user.id,
        })

    return jsonify({'success': True, 'data': data})


@points_bp.route('/admin/config')
@login_required
@permission_required('system_settings', 'edit')
def admin_config():
    from app.services.points_registry import BEHAVIOR_REGISTRY
    configs = PointsBehaviorConfig.query.order_by(
        PointsBehaviorConfig.category, PointsBehaviorConfig.id
    ).all()
    configs_data = [{
        'id': c.id,
        'behavior_code': c.behavior_code,
        'behavior_name': c.behavior_name,
        'category': c.category,
        'points': c.points,
        'daily_cap': c.daily_cap,
        'is_active': c.is_active,
        'trigger': BEHAVIOR_REGISTRY.get(c.behavior_code, {}).get('trigger', '自定义行为'),
        'is_system': c.behavior_code in BEHAVIOR_REGISTRY,
    } for c in configs]
    return render_template('points/tw_points_admin_config.html',
                           configs=configs_data, active_page='points_config')


@points_bp.route('/admin/config/api', methods=['GET'])
@login_required
@permission_required('system_settings', 'edit')
def admin_config_api_list():
    configs = PointsBehaviorConfig.query.order_by(
        PointsBehaviorConfig.category, PointsBehaviorConfig.id
    ).all()
    return jsonify({'success': True, 'data': [{
        'id': c.id, 'behavior_code': c.behavior_code,
        'behavior_name': c.behavior_name, 'category': c.category,
        'points': c.points, 'daily_cap': c.daily_cap, 'is_active': c.is_active,
    } for c in configs]})


@points_bp.route('/admin/config/api/<int:config_id>', methods=['PUT'])
@login_required
@permission_required('system_settings', 'edit')
def admin_config_update(config_id):
    config = PointsBehaviorConfig.query.get_or_404(config_id)
    data = request.get_json()
    if 'points' in data and data['points'] is not None:
        config.points = int(data['points'])
    if 'daily_cap' in data:
        config.daily_cap = int(data['daily_cap']) if data['daily_cap'] else None
    if 'is_active' in data:
        config.is_active = bool(data['is_active'])
    if 'behavior_name' in data:
        config.behavior_name = data['behavior_name']
    db.session.commit()
    return jsonify({'success': True})


@points_bp.route('/api/admin/user-transactions/<int:user_id>')
@login_required
@admin_required
def api_admin_user_transactions(user_id):
    target_user = User.query.get_or_404(user_id)
    period = request.args.get('period', 'month')
    page = request.args.get('page', 1, type=int)
    now = datetime.utcnow()
    year, month = now.year, now.month

    if period == 'month':
        months = [month]
    elif period == 'quarter':
        q_start = ((month - 1) // 3) * 3 + 1
        months = list(range(q_start, min(q_start + 3, 13)))
    else:
        months = list(range(1, 13))

    query = PointsTransaction.query.filter_by(user_id=user_id, year=year)
    if len(months) == 1:
        query = query.filter_by(month=months[0])
    else:
        query = query.filter(PointsTransaction.month.in_(months))

    pagination = query.order_by(PointsTransaction.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    if len(months) == 1:
        summary = UserPointsSummary.query.filter_by(
            user_id=user_id, year=year, month=months[0]
        ).first()
        total = summary.total_points if summary else 0
        breakdown = dict(summary.behavior_breakdown or {}) if summary else {}
    else:
        summaries = UserPointsSummary.query.filter(
            UserPointsSummary.user_id == user_id,
            UserPointsSummary.year == year,
            UserPointsSummary.month.in_(months)
        ).all()
        total = sum(s.total_points for s in summaries)
        breakdown = {}
        for s in summaries:
            for k, v in (s.behavior_breakdown or {}).items():
                breakdown[k] = breakdown.get(k, 0) + v

    transactions = [{
        'id': tx.id,
        'behavior_code': tx.behavior_code,
        'points': tx.points,
        'memo': tx.memo or '',
        'created_at': tx.created_at.strftime('%Y-%m-%d %H:%M'),
    } for tx in pagination.items]

    return jsonify({
        'success': True,
        'user_id': user_id,
        'user_name': target_user.real_name or target_user.username,
        'total_points': total,
        'breakdown': breakdown,
        'transactions': transactions,
        'has_next': pagination.has_next,
        'page': page,
    })


@points_bp.route('/admin/config/api', methods=['POST'])
@login_required
@permission_required('system_settings', 'edit')
def admin_config_create():
    data = request.get_json()
    if PointsBehaviorConfig.query.filter_by(behavior_code=data.get('behavior_code', '')).first():
        return jsonify({'success': False, 'message': f"行为代码 '{data['behavior_code']}' 已存在"})
    config = PointsBehaviorConfig(
        behavior_code=data['behavior_code'],
        behavior_name=data['behavior_name'],
        category=data['category'],
        points=int(data.get('points', 10)),
        daily_cap=int(data['daily_cap']) if data.get('daily_cap') else None,
    )
    db.session.add(config)
    db.session.commit()
    return jsonify({'success': True, 'config': {
        'id': config.id,
        'behavior_code': config.behavior_code,
        'behavior_name': config.behavior_name,
        'category': config.category,
        'points': config.points,
        'daily_cap': config.daily_cap,
        'is_active': config.is_active,
    }})
