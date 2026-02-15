# -*- coding: utf-8 -*-
"""
AI 使用量统计服务 - 聚合查询 ChatMessage 中的 AI 使用数据
"""
import logging
from datetime import datetime
from calendar import monthrange

from sqlalchemy import func, and_

from app import db
from app.models.chat import ChatMessage, ChatConversation

logger = logging.getLogger(__name__)

# 模型定价 (USD per million tokens)
MODEL_PRICING = {
    'deepseek-chat': {'prompt': 0.27, 'completion': 1.10},
}
DEFAULT_PRICING = {'prompt': 1.0, 'completion': 2.0}


def calculate_cost(model, prompt_tokens, completion_tokens):
    """根据模型计算费用 (USD)"""
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING) if model else DEFAULT_PRICING
    return round(
        (prompt_tokens or 0) / 1e6 * pricing['prompt'] +
        (completion_tokens or 0) / 1e6 * pricing['completion'],
        4
    )


def get_ai_usage_stats(year, month, user_id=None):
    """
    获取 AI 使用量统计数据

    Args:
        year: 年份
        month: 月份 (1-12)
        user_id: 可选，按用户过滤

    Returns:
        dict: 包含 summary, daily_usage, model_breakdown, user_breakdown
    """
    try:
        # 计算日期范围
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, last_day, 23, 59, 59)

        # 基础过滤条件
        base_filters = [
            ChatMessage.is_ai_response == True,
            ChatMessage.is_deleted == False,
            ChatMessage.created_at >= start_date,
            ChatMessage.created_at <= end_date,
        ]

        # 按用户过滤: 通过 conversation 的 created_by 字段
        if user_id:
            base_filters.append(
                ChatMessage.conversation_id.in_(
                    db.session.query(ChatConversation.id).filter(
                        ChatConversation.created_by == user_id
                    )
                )
            )

        # === 每日统计 ===
        daily_query = db.session.query(
            func.date(ChatMessage.created_at).label('day'),
            func.count(ChatMessage.id).label('request_count'),
            func.coalesce(func.sum(ChatMessage.ai_prompt_tokens), 0).label('prompt_tokens'),
            func.coalesce(func.sum(ChatMessage.ai_completion_tokens), 0).label('completion_tokens'),
        ).filter(
            and_(*base_filters)
        ).group_by(
            func.date(ChatMessage.created_at)
        ).order_by(
            func.date(ChatMessage.created_at)
        ).all()

        daily_usage = []
        for row in daily_query:
            day_str = str(row.day)
            prompt_t = int(row.prompt_tokens)
            completion_t = int(row.completion_tokens)
            daily_usage.append({
                'day': day_str,
                'request_count': row.request_count,
                'prompt_tokens': prompt_t,
                'completion_tokens': completion_t,
                'total_tokens': prompt_t + completion_t,
                'estimated_cost': _estimate_daily_cost(day_str, base_filters),
            })

        # === 模型分布 ===
        model_query = db.session.query(
            ChatMessage.ai_model.label('model'),
            func.count(ChatMessage.id).label('request_count'),
            func.coalesce(func.sum(ChatMessage.ai_prompt_tokens), 0).label('prompt_tokens'),
            func.coalesce(func.sum(ChatMessage.ai_completion_tokens), 0).label('completion_tokens'),
        ).filter(
            and_(*base_filters)
        ).group_by(
            ChatMessage.ai_model
        ).all()

        model_breakdown = []
        for row in model_query:
            prompt_t = int(row.prompt_tokens)
            completion_t = int(row.completion_tokens)
            model_breakdown.append({
                'model': row.model or 'unknown',
                'request_count': row.request_count,
                'prompt_tokens': prompt_t,
                'completion_tokens': completion_t,
                'estimated_cost': calculate_cost(row.model, prompt_t, completion_t),
            })

        # === 用户分布（仅全部用户视图） ===
        user_breakdown = []
        if not user_id:
            user_query = db.session.query(
                ChatConversation.created_by.label('user_id'),
                func.count(ChatMessage.id).label('request_count'),
                func.coalesce(func.sum(ChatMessage.ai_prompt_tokens), 0).label('prompt_tokens'),
                func.coalesce(func.sum(ChatMessage.ai_completion_tokens), 0).label('completion_tokens'),
            ).join(
                ChatConversation,
                ChatMessage.conversation_id == ChatConversation.id
            ).filter(
                and_(*base_filters)
            ).group_by(
                ChatConversation.created_by
            ).all()

            # 批量获取用户名
            user_ids = [row.user_id for row in user_query]
            user_names = _get_user_names(user_ids)

            for row in user_query:
                prompt_t = int(row.prompt_tokens)
                completion_t = int(row.completion_tokens)
                total_t = prompt_t + completion_t
                user_breakdown.append({
                    'user_id': row.user_id,
                    'user_name': user_names.get(row.user_id, f'User #{row.user_id}'),
                    'request_count': row.request_count,
                    'total_tokens': total_t,
                    'estimated_cost': calculate_cost(None, prompt_t, completion_t),
                })

            user_breakdown.sort(key=lambda x: x['total_tokens'], reverse=True)

        # === 汇总 ===
        total_requests = sum(d['request_count'] for d in daily_usage)
        total_prompt = sum(d['prompt_tokens'] for d in daily_usage)
        total_completion = sum(d['completion_tokens'] for d in daily_usage)
        total_cost = sum(m['estimated_cost'] for m in model_breakdown)
        active_users = len(user_breakdown) if user_breakdown else (1 if user_id and total_requests > 0 else 0)

        return {
            'success': True,
            'data': {
                'summary': {
                    'total_requests': total_requests,
                    'total_prompt_tokens': total_prompt,
                    'total_completion_tokens': total_completion,
                    'total_tokens': total_prompt + total_completion,
                    'estimated_cost': round(total_cost, 4),
                    'active_users': active_users,
                },
                'daily_usage': daily_usage,
                'model_breakdown': model_breakdown,
                'user_breakdown': user_breakdown,
            }
        }

    except Exception as e:
        logger.error(f"获取 AI 使用量统计失败: {str(e)}", exc_info=True)
        return {
            'success': False,
            'message': f'获取统计数据失败: {str(e)}',
            'data': {
                'summary': {
                    'total_requests': 0,
                    'total_prompt_tokens': 0,
                    'total_completion_tokens': 0,
                    'total_tokens': 0,
                    'estimated_cost': 0,
                    'active_users': 0,
                },
                'daily_usage': [],
                'model_breakdown': [],
                'user_breakdown': [],
            }
        }


def _estimate_daily_cost(day_str, base_filters):
    """计算某天的费用（按模型分组计算）"""
    try:
        rows = db.session.query(
            ChatMessage.ai_model,
            func.coalesce(func.sum(ChatMessage.ai_prompt_tokens), 0).label('pt'),
            func.coalesce(func.sum(ChatMessage.ai_completion_tokens), 0).label('ct'),
        ).filter(
            and_(*base_filters),
            func.date(ChatMessage.created_at) == day_str,
        ).group_by(
            ChatMessage.ai_model
        ).all()

        return round(sum(calculate_cost(r.ai_model, int(r.pt), int(r.ct)) for r in rows), 4)
    except Exception:
        return 0.0


def _get_user_names(user_ids):
    """批量获取用户名"""
    if not user_ids:
        return {}
    try:
        from app.models.user import User
        users = User.query.filter(User.id.in_(user_ids)).all()
        return {u.id: (u.real_name or u.username) for u in users}
    except Exception:
        return {}
