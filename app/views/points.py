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
                    'proxy_tokens': 0,
                    'estimated_cost': 0.0,
                }
            user_totals[uid]['total_tokens']   += u['total_tokens']
            user_totals[uid]['chat_tokens']    += u.get('chat_tokens', 0)
            user_totals[uid]['cli_tokens']     += u.get('cli_tokens', 0)
            user_totals[uid]['proxy_tokens']   += u.get('proxy_tokens', 0)
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
            'proxy_tokens': u['proxy_tokens'],
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


@points_bp.route('/api/knowledge-leaderboard')
@login_required
def api_knowledge_leaderboard():
    """知识共享贡献排行 + 最多被引用文章"""
    from app.models.knowledge import KnowledgeWikiArticle
    period = request.args.get('period', 'month')
    now = datetime.utcnow()
    year, month = now.year, now.month

    if period == 'month':
        months = [month]
    elif period == 'quarter':
        q_start = ((month - 1) // 3) * 3 + 1
        months = list(range(q_start, min(q_start + 3, 13)))
    else:
        months = list(range(1, 13))

    # ── 直接查 KnowledgeWikiArticle 统计每人的上传数和已共享数（历史数据也能正确体现）
    # 上传数：该用户 owner 的所有文章
    upload_rows = db.session.query(
        KnowledgeWikiArticle.owner_id,
        func.count(KnowledgeWikiArticle.id).label('cnt')
    ).filter(KnowledgeWikiArticle.owner_id.isnot(None)).group_by(
        KnowledgeWikiArticle.owner_id
    ).all()
    upload_map = {r.owner_id: r.cnt for r in upload_rows}

    # 已共享数：scope != personal 的文章
    shared_rows = db.session.query(
        KnowledgeWikiArticle.owner_id,
        func.count(KnowledgeWikiArticle.id).label('cnt')
    ).filter(
        KnowledgeWikiArticle.owner_id.isnot(None),
        KnowledgeWikiArticle.scope != 'personal',
    ).group_by(KnowledgeWikiArticle.owner_id).all()
    shared_map = {r.owner_id: r.cnt for r in shared_rows}

    # ── PointsTransaction 统计被引次数和被浏览次数（事件驱动，按周期过滤）
    EVENT_CODES = ['wiki_cited', 'wiki_cited_qa', 'wiki_link_opened']
    event_q = PointsTransaction.query.filter(
        PointsTransaction.behavior_code.in_(EVENT_CODES),
        PointsTransaction.year == year,
    )
    if len(months) == 1:
        event_q = event_q.filter(PointsTransaction.month == months[0])
    else:
        event_q = event_q.filter(PointsTransaction.month.in_(months))

    event_stats = {}
    for tx in event_q.all():
        uid = tx.user_id
        if uid not in event_stats:
            event_stats[uid] = {'cited': 0, 'viewed': 0, 'event_points': 0}
        event_stats[uid]['event_points'] += tx.points
        if tx.behavior_code in ('wiki_cited', 'wiki_cited_qa'):
            event_stats[uid]['cited'] += 1
        elif tx.behavior_code == 'wiki_link_opened':
            event_stats[uid]['viewed'] += 1

    # ── 合并：所有有文章的用户都要出现在排行榜中
    all_user_ids = set(upload_map.keys()) | set(shared_map.keys()) | set(event_stats.keys())
    users = {u.id: u for u in User.query.filter(User.id.in_(list(all_user_ids))).all()} if all_user_ids else {}

    user_stats = {}
    for uid in all_user_ids:
        ev = event_stats.get(uid, {'cited': 0, 'viewed': 0, 'event_points': 0})
        uploaded = upload_map.get(uid, 0)
        shared = shared_map.get(uid, 0)
        # 综合得分：上传×5 + 共享×10 + 事件积分
        score = uploaded * 5 + shared * 10 + ev['event_points']
        user_stats[uid] = {
            'uploaded': uploaded,
            'shared': shared,
            'cited': ev['cited'],
            'viewed': ev['viewed'],
            'total_points': score,
        }

    leaderboard = []
    for uid, stats in user_stats.items():
        u = users.get(uid)
        if not u or not (u.is_active if hasattr(u, 'is_active') else True):
            continue
        leaderboard.append({
            'user_id': uid,
            'name': u.real_name or u.username,
            'department': getattr(u, 'department', '') or '',
            'uploaded': stats['uploaded'],
            'shared': stats['shared'],
            'cited': stats['cited'],
            'viewed': stats['viewed'],
            'total_points': stats['total_points'],
            'is_me': uid == current_user.id,
        })

    leaderboard.sort(key=lambda x: x['total_points'], reverse=True)
    for i, item in enumerate(leaderboard, 1):
        item['rank'] = i

    # ── 最多被引用文章（按 outbound_refs 反查 inbound 数，即该文章 slug 被多少其他文章引用）
    # 用 KnowledgeWikiArticle.outbound_refs（JSON 数组）统计每个 slug 被引次数
    all_articles = KnowledgeWikiArticle.query.all()
    inbound_count = {}  # slug → count
    for art in all_articles:
        for ref in (art.outbound_refs or []):
            inbound_count[ref] = inbound_count.get(ref, 0) + 1

    # 取 top 10，关联文章元数据
    top_slugs = sorted(inbound_count.items(), key=lambda x: -x[1])[:10]
    slug_to_art = {a.topic + '/' + a.slug: a for a in all_articles}

    top_articles_list = []
    for slug, cnt in top_slugs:
        art = slug_to_art.get(slug)
        if not art:
            continue
        owner = users.get(art.owner_id)
        if owner:
            owner_name = owner.real_name or owner.username
        elif art.owner:
            owner_name = art.owner.real_name or art.owner.username
        else:
            owner_name = ''
        top_articles_list.append({
            'id': art.id,
            'title': art.title,
            'topic': art.topic,
            'scope': art.scope,
            'cite_count': cnt,
            'owner_name': owner_name,
        })

    return jsonify({'success': True, 'leaderboard': leaderboard, 'top_articles': top_articles_list})


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
