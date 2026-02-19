# -*- coding: utf-8 -*-
"""
AI 对话服务

统一通过 OpenClaw Gateway 提供 AI 对话的流式响应功能。
"""
import json
import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DSML 安全清理（OpenClaw 不输出 DSML，但保险起见保留简版）
# ---------------------------------------------------------------------------

_DSML_TAG_PATTERN = re.compile(r'</?｜(?:DSML｜)?[^>]*>')


def _clean_dsml(text):
    """移除可能残留的 DSML 标签（安全兜底）"""
    if not text or ('｜' not in text and '|' not in text):
        return text
    # 半角转全角
    text = re.sub(r'<\|', '<｜', text)
    text = re.sub(r'\|>', '｜>', text)
    # 截断到第一个 DSML 块标记前
    if '｜DSML' in text:
        idx = text.find('<｜DSML')
        if idx < 0:
            idx = text.find('｜DSML')
        if idx >= 0:
            text = text[:idx]
    # 清理残留标签
    text = _DSML_TAG_PATTERN.sub('', text)
    return text.strip()


# ---------------------------------------------------------------------------
# 主入口：流式 AI 响应（统一走 OpenClaw）
# ---------------------------------------------------------------------------

def get_ai_response_stream(message, user, conversation_history=None,
                           session_id=None, conversation_id=None):
    """通过 OpenClaw 获取 AI 流式响应

    Args:
        message: 用户发送的消息文本
        user: 当前用户对象
        conversation_history: 对话历史 [{role, content}, ...]
        session_id: OpenClaw session ID
        conversation_id: 当前对话 ID（供 OpenClaw 文件上传工具使用）

    Yields:
        dict: 包含以下类型之一：
            - {'type': 'content', 'text': '...'} 内容片段
            - {'type': 'thinking', 'text': '...'} 思考过程
            - {'type': 'status', 'message': '...'} 状态更新
            - {'type': 'agent_status', 'message': '...'} Agent 工具状态
            - {'type': 'done', 'model': '...', 'prompt_tokens': N, 'completion_tokens': N}
    """
    try:
        from app.services.openclaw_provider import get_openclaw_response_stream
        yield from get_openclaw_response_stream(
            message, conversation_history, session_id,
            user=user, conversation_id=conversation_id,
            user_id=user.id if user else None,
            user_name=(user.real_name or user.username) if user else None)
    except Exception as e:
        logger.error(f'AI 流式响应异常: {e}', exc_info=True)
        yield {'type': 'content', 'text': '抱歉，AI 服务暂时不可用，请稍后重试。'}
        yield {'type': 'done', 'model': 'error', 'prompt_tokens': 0, 'completion_tokens': 0}


# ---------------------------------------------------------------------------
# 话题标题生成（通过 OpenClaw 实现）
# ---------------------------------------------------------------------------

def generate_conversation_topic(user_message, ai_response):
    """用第一轮对话生成 3-8 字的话题标题

    Args:
        user_message: 用户的第一条消息
        ai_response: AI 的第一条回复（截取前 200 字）

    Returns:
        str 或 None: 生成的话题标题，失败返回 None
    """
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return None

    model = os.environ.get('DEEPSEEK_CHAT_MODEL', 'deepseek-chat')
    base_url = os.environ.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1').rstrip('/')

    prompt = (
        '根据以下对话的第一轮内容，生成一个简短的话题标题（3-8个字，不带标点）。\n'
        f'用户：{user_message[:200]}\n'
        f'AI：{ai_response[:200]}\n'
        '只输出标题本身。'
    )

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    body = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 30,
        'temperature': 0.3,
        'stream': False,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(f'{base_url}/chat/completions', headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            topic = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            # 清理：去除引号、标点，截断到 100 字符
            topic = topic.strip('"\'""''「」【】')
            if topic and len(topic) <= 100:
                return topic
            elif topic:
                return topic[:100]
    except Exception as e:
        logger.warning(f'生成话题标题失败: {e}')

    return None
