# -*- coding: utf-8 -*-
"""
AI 对话辅助工具

聊天的主对话流现在由 app.services.chat_agent.ChatAgentLoop 直接驱动
(见 app/views/chat.py:ai_stream)。本模块保留两个辅助函数:

- _clean_dsml: 残留 DSML 标签的兜底清理
- generate_conversation_topic: 用 DeepSeek 给新对话生成 3-8 字话题标题
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
# 话题标题生成（走 DeepSeek)
# ---------------------------------------------------------------------------

def generate_conversation_topic(user_message, ai_response=None):
    """用用户首条消息生成 3-8 字的话题标题

    Args:
        user_message: 用户的第一条消息
        ai_response: 已废弃，保留参数兼容性

    Returns:
        str 或 None: 生成的话题标题，失败返回 None
    """
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return None

    model = os.environ.get('DEEPSEEK_CHAT_MODEL', 'deepseek-chat')
    base_url = os.environ.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1').rstrip('/')

    prompt = (
        '根据用户的消息，生成一个简短的话题标题（3-8个字，不带标点）。\n'
        '要求：概括用户的意图或需求，不要包含结果、状态或情感判断。\n'
        f'用户：{user_message[:200]}\n'
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
