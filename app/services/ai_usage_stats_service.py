# -*- coding: utf-8 -*-
"""
AI 使用量统计服务 - 聚合 Chat 和 CLI Agent 两个来源的 AI 使用数据
"""
import logging
from datetime import datetime
from calendar import monthrange

from sqlalchemy import func, and_

from app import db
from app.models.chat import ChatMessage, ChatConversation
from app.models.cli_session import CliSession
from app.models.ai_proxy_usage import AIProxyUsage

logger = logging.getLogger(__name__)

# 模型定价 (USD per million tokens)
MODEL_PRICING = {
    # Anthropic Claude 3.5 系列
    'claude-3-5-sonnet-20241022':     {'prompt': 3.0,   'completion': 15.0},
    'claude-3-5-sonnet-latest':       {'prompt': 3.0,   'completion': 15.0},
    'claude-3-5-sonnet-20240620':     {'prompt': 3.0,   'completion': 15.0},
    'claude-3-5-haiku-20241022':      {'prompt': 0.8,   'completion': 4.0},
    'claude-3-5-haiku-latest':        {'prompt': 0.8,   'completion': 4.0},
    # Anthropic Claude 3 系列
    'claude-3-opus-20240229':         {'prompt': 15.0,  'completion': 75.0},
    'claude-3-opus-latest':           {'prompt': 15.0,  'completion': 75.0},
    'claude-3-sonnet-20240229':       {'prompt': 3.0,   'completion': 15.0},
    'claude-3-haiku-20240307':        {'prompt': 0.25,  'completion': 1.25},
    # Anthropic Claude 4 系列
    'claude-opus-4-5':                {'prompt': 15.0,  'completion': 75.0},
    'claude-sonnet-4-5':              {'prompt': 3.0,   'completion': 15.0},
    'claude-haiku-4-5':               {'prompt': 0.8,   'completion': 4.0},
    'claude-opus-4-7':                {'prompt': 15.0,  'completion': 75.0},
    'claude-sonnet-4-6':              {'prompt': 3.0,   'completion': 15.0},
    'claude-haiku-4-5-20251001':      {'prompt': 0.8,   'completion': 4.0},
    # DeepSeek
    'deepseek-chat':                  {'prompt': 0.27,  'completion': 1.10},
    'deepseek-reasoner':              {'prompt': 0.55,  'completion': 2.19},
}
DEFAULT_PRICING = {'prompt': 3.0, 'completion': 15.0}  # 未知 Claude 模型的兜底价格


def get_model_pricing(model: str | None) -> dict:
    """获取模型定价，支持前缀匹配（处理 -latest 等别名）"""
    if not model:
        return DEFAULT_PRICING
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    # 前缀模糊匹配（如 claude-3-5-sonnet → claude-3-5-sonnet-20241022）
    for key, pricing in MODEL_PRICING.items():
        if model.startswith(key) or key.startswith(model):
            return pricing
    return DEFAULT_PRICING


def calculate_cost(model, prompt_tokens, completion_tokens):
    """根据模型计算费用 (USD)"""
    pricing = get_model_pricing(model)
    return round(
        (prompt_tokens or 0) / 1e6 * pricing['prompt'] +
        (completion_tokens or 0) / 1e6 * pricing['completion'],
        6
    )


def get_ai_usage_stats(year, month, user_id=None, source=None):
    """
    获取 AI 使用量统计数据

    Args:
        year: 年份
        month: 月份 (1-12)
        user_id: 可选，按用户过滤
        source: 可选，'chat' / 'cli' / 'claude_proxy' / None(全部)

    Returns:
        dict: 包含 summary, daily_usage, model_breakdown, user_breakdown, proxy_leaderboard
    """
    try:
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, last_day, 23, 59, 59)

        proxy_only = source == 'claude_proxy'
        chat_data  = {} if source in ('cli', 'claude_proxy') else _get_chat_stats(start_date, end_date, user_id)
        cli_data   = {} if source in ('chat', 'claude_proxy') else _get_cli_stats(start_date, end_date, user_id)
        proxy_data = {} if source in ('chat', 'cli') else _get_proxy_stats(start_date, end_date, user_id)

        return _merge_stats(chat_data, cli_data, proxy_data)

    except Exception as e:
        logger.error(f"获取 AI 使用量统计失败: {str(e)}", exc_info=True)
        return _empty_result(str(e))


# ─── Chat 来源 ────────────────────────────────────────────────────────────────

def _get_chat_stats(start_date, end_date, user_id=None):
    base_filters = [
        ChatMessage.is_ai_response == True,
        ChatMessage.is_deleted == False,
        ChatMessage.created_at >= start_date,
        ChatMessage.created_at <= end_date,
    ]
    if user_id:
        base_filters.append(
            ChatMessage.conversation_id.in_(
                db.session.query(ChatConversation.id).filter(
                    ChatConversation.created_by == user_id
                )
            )
        )

    # 每日
    daily_rows = db.session.query(
        func.date(ChatMessage.created_at).label('day'),
        func.count(ChatMessage.id).label('req'),
        func.coalesce(func.sum(ChatMessage.ai_prompt_tokens), 0).label('pt'),
        func.coalesce(func.sum(ChatMessage.ai_completion_tokens), 0).label('ct'),
    ).filter(and_(*base_filters)).group_by(func.date(ChatMessage.created_at)).all()

    daily = {}
    for r in daily_rows:
        day = str(r.day)
        pt, ct = int(r.pt), int(r.ct)
        daily[day] = {
            'request_count': r.req,
            'prompt_tokens': pt,
            'completion_tokens': ct,
            'estimated_cost': _chat_daily_cost(day, base_filters),
        }

    # 模型分布
    model_rows = db.session.query(
        ChatMessage.ai_model.label('model'),
        func.count(ChatMessage.id).label('req'),
        func.coalesce(func.sum(ChatMessage.ai_prompt_tokens), 0).label('pt'),
        func.coalesce(func.sum(ChatMessage.ai_completion_tokens), 0).label('ct'),
    ).filter(and_(*base_filters)).group_by(ChatMessage.ai_model).all()

    models = []
    for r in model_rows:
        pt, ct = int(r.pt), int(r.ct)
        models.append({
            'model': r.model or 'unknown',
            'source': 'chat',
            'request_count': r.req,
            'prompt_tokens': pt,
            'completion_tokens': ct,
            'estimated_cost': calculate_cost(r.model, pt, ct),
            'pricing': get_model_pricing(r.model),
        })

    # 用户分布
    users = []
    if not user_id:
        user_rows = db.session.query(
            ChatConversation.created_by.label('uid'),
            func.count(ChatMessage.id).label('req'),
            func.coalesce(func.sum(ChatMessage.ai_prompt_tokens), 0).label('pt'),
            func.coalesce(func.sum(ChatMessage.ai_completion_tokens), 0).label('ct'),
        ).join(ChatConversation, ChatMessage.conversation_id == ChatConversation.id
        ).filter(and_(*base_filters)).group_by(ChatConversation.created_by).all()

        uid_list = [r.uid for r in user_rows]
        names = _get_user_names(uid_list)
        for r in user_rows:
            pt, ct = int(r.pt), int(r.ct)
            users.append({
                'user_id': r.uid,
                'user_name': names.get(r.uid, f'User #{r.uid}'),
                'source': 'chat',
                'request_count': r.req,
                'total_tokens': pt + ct,
                'estimated_cost': calculate_cost(None, pt, ct),
            })

    return {'daily': daily, 'models': models, 'users': users}


def _chat_daily_cost(day_str, base_filters):
    rows = db.session.query(
        ChatMessage.ai_model,
        func.coalesce(func.sum(ChatMessage.ai_prompt_tokens), 0).label('pt'),
        func.coalesce(func.sum(ChatMessage.ai_completion_tokens), 0).label('ct'),
    ).filter(
        and_(*base_filters),
        func.date(ChatMessage.created_at) == day_str,
    ).group_by(ChatMessage.ai_model).all()
    return round(sum(calculate_cost(r.ai_model, int(r.pt), int(r.ct)) for r in rows), 6)


# ─── CLI 来源 ─────────────────────────────────────────────────────────────────

def _get_cli_stats(start_date, end_date, user_id=None):
    base_filters = [
        CliSession.last_active_at >= start_date,
        CliSession.last_active_at <= end_date,
    ]
    if user_id:
        base_filters.append(CliSession.user_id == user_id)

    session_rows = db.session.query(
        CliSession.user_id,
        CliSession.model,
        func.date(CliSession.last_active_at).label('day'),
        func.count(CliSession.id).label('sessions'),
        func.coalesce(
            func.sum(
                func.cast(
                    func.coalesce(CliSession.usage_total['input_tokens'].astext, '0'),
                    db.Integer
                )
            ), 0
        ).label('pt'),
        func.coalesce(
            func.sum(
                func.cast(
                    func.coalesce(CliSession.usage_total['output_tokens'].astext, '0'),
                    db.Integer
                )
            ), 0
        ).label('ct'),
    ).filter(and_(*base_filters)).group_by(
        CliSession.user_id, CliSession.model, func.date(CliSession.last_active_at)
    ).all()

    daily = {}
    model_map = {}
    user_map = {}

    uid_set = set()
    for r in session_rows:
        uid_set.add(r.user_id)

    names = _get_user_names(list(uid_set))

    for r in session_rows:
        day = str(r.day)
        pt, ct = int(r.pt), int(r.ct)
        model = r.model or 'unknown'
        cost = calculate_cost(model, pt, ct)

        # 每日汇总
        if day not in daily:
            daily[day] = {'request_count': 0, 'prompt_tokens': 0, 'completion_tokens': 0, 'estimated_cost': 0.0}
        daily[day]['request_count'] += r.sessions
        daily[day]['prompt_tokens'] += pt
        daily[day]['completion_tokens'] += ct
        daily[day]['estimated_cost'] = round(daily[day]['estimated_cost'] + cost, 6)

        # 模型汇总
        key = ('cli', model)
        if key not in model_map:
            model_map[key] = {
                'model': model,
                'source': 'cli',
                'request_count': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'estimated_cost': 0.0,
                'pricing': get_model_pricing(model),
            }
        model_map[key]['request_count'] += r.sessions
        model_map[key]['prompt_tokens'] += pt
        model_map[key]['completion_tokens'] += ct
        model_map[key]['estimated_cost'] = round(model_map[key]['estimated_cost'] + cost, 6)

        # 用户汇总
        uid = r.user_id
        if uid not in user_map:
            user_map[uid] = {
                'user_id': uid,
                'user_name': names.get(uid, f'User #{uid}'),
                'source': 'cli',
                'request_count': 0,
                'total_tokens': 0,
                'estimated_cost': 0.0,
            }
        user_map[uid]['request_count'] += r.sessions
        user_map[uid]['total_tokens'] += pt + ct
        user_map[uid]['estimated_cost'] = round(user_map[uid]['estimated_cost'] + cost, 6)

    return {
        'daily': daily,
        'models': list(model_map.values()),
        'users': list(user_map.values()),
    }


# ─── Claude 代理来源 ──────────────────────────────────────────────────────────

def _get_proxy_stats(start_date, end_date, user_id=None):
    from app.models.user import User
    from datetime import date as date_type
    start_d = start_date.date() if hasattr(start_date, 'date') else start_date
    end_d = end_date.date() if hasattr(end_date, 'date') else end_date

    filters = [
        AIProxyUsage.provider.in_(['claude', 'claude_research']),
        AIProxyUsage.date >= start_d,
        AIProxyUsage.date <= end_d,
    ]
    if user_id:
        filters.append(AIProxyUsage.user_id == user_id)

    rows = db.session.query(
        AIProxyUsage.user_id,
        AIProxyUsage.date,
        AIProxyUsage.input_tokens,
        AIProxyUsage.output_tokens,
        AIProxyUsage.request_count,
    ).filter(and_(*filters)).all()

    uid_set = {r.user_id for r in rows}
    names = _get_user_names(list(uid_set))

    daily = {}
    user_map = {}
    total_in = total_out = total_req = 0

    for r in rows:
        day = str(r.date)
        it, ot, rc = int(r.input_tokens or 0), int(r.output_tokens or 0), int(r.request_count or 0)
        total_in += it; total_out += ot; total_req += rc

        if day not in daily:
            daily[day] = {'request_count': 0, 'prompt_tokens': 0, 'completion_tokens': 0, 'estimated_cost': 0.0}
        daily[day]['request_count'] += rc
        daily[day]['prompt_tokens'] += it
        daily[day]['completion_tokens'] += ot

        uid = r.user_id
        if uid not in user_map:
            user_map[uid] = {
                'user_id': uid,
                'user_name': names.get(uid, f'User #{uid}'),
                'source': 'claude_proxy',
                'request_count': 0,
                'total_tokens': 0,
                'estimated_cost': 0.0,
            }
        user_map[uid]['request_count'] += rc
        user_map[uid]['total_tokens'] += it + ot

    models = [{
        'model': 'claude-proxy',
        'source': 'claude_proxy',
        'request_count': total_req,
        'prompt_tokens': total_in,
        'completion_tokens': total_out,
        'estimated_cost': 0.0,
        'pricing': None,
    }] if (total_in + total_out) > 0 else []

    # 排行榜：附加配额信息
    leaderboard = []
    if uid_set:
        quota_users = User.query.filter(User.id.in_(uid_set)).all()
        default_q = 50_000_000
        try:
            import os
            default_q = int(os.environ.get('CLAUDE_AI_DEFAULT_QUOTA', 50_000_000))
        except Exception:
            pass
        quota_map = {u.id: int(u.claude_ai_quota_tokens or default_q) for u in quota_users}
        for uid, ud in user_map.items():
            quota = quota_map.get(uid, default_q)
            leaderboard.append({
                'user_id': uid,
                'user_name': ud['user_name'],
                'tokens': ud['total_tokens'],
                'requests': ud['request_count'],
                'quota': quota,
                'pct': round(ud['total_tokens'] / quota * 100, 1) if quota > 0 else 0,
            })
        leaderboard.sort(key=lambda x: x['tokens'], reverse=True)

    return {'daily': daily, 'models': models, 'users': list(user_map.values()), 'leaderboard': leaderboard}


# ─── 合并 ─────────────────────────────────────────────────────────────────────

def _merge_stats(chat_data, cli_data, proxy_data=None):
    proxy_data = proxy_data or {}
    all_days = (set(chat_data.get('daily', {}).keys()) |
                set(cli_data.get('daily', {}).keys()) |
                set(proxy_data.get('daily', {}).keys()))
    daily_usage = []
    for day in sorted(all_days):
        c = chat_data.get('daily', {}).get(day, {})
        l = cli_data.get('daily', {}).get(day, {})
        p = proxy_data.get('daily', {}).get(day, {})
        pt = c.get('prompt_tokens', 0) + l.get('prompt_tokens', 0) + p.get('prompt_tokens', 0)
        ct = c.get('completion_tokens', 0) + l.get('completion_tokens', 0) + p.get('completion_tokens', 0)
        daily_usage.append({
            'day': day,
            'request_count': c.get('request_count', 0) + l.get('request_count', 0) + p.get('request_count', 0),
            'prompt_tokens': pt,
            'completion_tokens': ct,
            'total_tokens': pt + ct,
            'estimated_cost': round(
                c.get('estimated_cost', 0.0) + l.get('estimated_cost', 0.0), 6
            ),
            'chat_tokens': c.get('prompt_tokens', 0) + c.get('completion_tokens', 0),
            'cli_tokens': l.get('prompt_tokens', 0) + l.get('completion_tokens', 0),
            'proxy_tokens': p.get('prompt_tokens', 0) + p.get('completion_tokens', 0),
            'chat_requests': c.get('request_count', 0),
            'cli_requests': l.get('request_count', 0),
            'proxy_requests': p.get('request_count', 0),
        })

    model_breakdown = chat_data.get('models', []) + cli_data.get('models', []) + proxy_data.get('models', [])

    # 用户明细：同一 user_id 的 chat+cli+proxy 合并
    user_combined = {}
    for u in chat_data.get('users', []) + cli_data.get('users', []) + proxy_data.get('users', []):
        uid = u['user_id']
        if uid not in user_combined:
            user_combined[uid] = {
                'user_id': uid,
                'user_name': u['user_name'],
                'request_count': 0,
                'total_tokens': 0,
                'estimated_cost': 0.0,
                'chat_tokens': 0,
                'cli_tokens': 0,
                'proxy_tokens': 0,
            }
        user_combined[uid]['request_count'] += u['request_count']
        user_combined[uid]['total_tokens'] += u['total_tokens']
        user_combined[uid]['estimated_cost'] = round(
            user_combined[uid]['estimated_cost'] + u['estimated_cost'], 6
        )
        src = u.get('source')
        if src == 'chat':
            user_combined[uid]['chat_tokens'] += u['total_tokens']
        elif src == 'cli':
            user_combined[uid]['cli_tokens'] += u['total_tokens']
        elif src == 'claude_proxy':
            user_combined[uid]['proxy_tokens'] += u['total_tokens']

    user_breakdown = sorted(user_combined.values(), key=lambda x: x['total_tokens'], reverse=True)

    total_req = sum(d['request_count'] for d in daily_usage)
    total_pt = sum(d['prompt_tokens'] for d in daily_usage)
    total_ct = sum(d['completion_tokens'] for d in daily_usage)
    total_cost = sum(m['estimated_cost'] for m in model_breakdown)

    return {
        'success': True,
        'data': {
            'summary': {
                'total_requests': total_req,
                'total_prompt_tokens': total_pt,
                'total_completion_tokens': total_ct,
                'total_tokens': total_pt + total_ct,
                'estimated_cost': round(total_cost, 4),
                'active_users': len(user_breakdown),
            },
            'daily_usage': daily_usage,
            'model_breakdown': model_breakdown,
            'user_breakdown': user_breakdown,
            'proxy_leaderboard': proxy_data.get('leaderboard', []),
        }
    }


def _empty_result(msg=''):
    return {
        'success': False,
        'message': f'获取统计数据失败: {msg}',
        'data': {
            'summary': {
                'total_requests': 0, 'total_prompt_tokens': 0,
                'total_completion_tokens': 0, 'total_tokens': 0,
                'estimated_cost': 0, 'active_users': 0,
            },
            'daily_usage': [], 'model_breakdown': [], 'user_breakdown': [], 'proxy_leaderboard': [],
        }
    }


def _get_user_names(user_ids):
    if not user_ids:
        return {}
    try:
        from app.models.user import User
        users = User.query.filter(User.id.in_(user_ids)).all()
        return {u.id: (u.real_name or u.username) for u in users}
    except Exception:
        return {}
