# -*- coding: utf-8 -*-
"""
聊天翻译服务

使用 DeepSeek API 提供中英文消息翻译功能。
"""
import os
import logging

import httpx

logger = logging.getLogger(__name__)

# 语言名称映射
LANGUAGE_NAMES = {
    'zh': '中文',
    'en': 'English',
}


def translate_text(text, source_lang, target_lang):
    """翻译文本的主入口函数

    Args:
        text: 待翻译的文本
        source_lang: 源语言代码 ('zh' 或 'en')
        target_lang: 目标语言代码 ('zh' 或 'en')

    Returns:
        str: 翻译后的文本，失败时返回 None
    """
    # 跳过空文本
    if not text or not text.strip():
        return None

    # 源语言和目标语言相同，无需翻译
    if source_lang == target_lang:
        return text

    try:
        return _translate_with_ai(text, source_lang, target_lang)
    except Exception as e:
        logger.error(f'翻译失败: {e}')
        return None


def _translate_with_ai(text, source_lang, target_lang):
    """使用 DeepSeek API 进行翻译

    Args:
        text: 待翻译的文本
        source_lang: 源语言代码
        target_lang: 目标语言代码

    Returns:
        str: 翻译后的文本，失败时返回 None
    """
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    target_name = LANGUAGE_NAMES.get(target_lang, target_lang)

    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        logger.warning('未配置 DEEPSEEK_API_KEY，无法翻译')
        return None

    base_url = os.environ.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1').rstrip('/')
    model = os.environ.get('DEEPSEEK_CHAT_MODEL', 'deepseek-chat')

    system_prompt = (
        f'You are a translator. Translate text from {source_name} to {target_name}. '
        f'Return ONLY the translated text, nothing else.'
    )

    try:
        response = httpx.post(
            f'{base_url}/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': text},
                ],
                'temperature': 0.3,
            },
            timeout=15.0,
        )
        response.raise_for_status()

        data = response.json()
        choices = data.get('choices', [])
        if choices:
            translated = choices[0].get('message', {}).get('content', '').strip()
            if translated:
                return translated

        logger.error(f'DeepSeek API 响应格式异常: {data}')
        return None

    except httpx.TimeoutException:
        logger.error('DeepSeek 翻译 API 调用超时 (15s)')
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f'DeepSeek 翻译 API HTTP 错误: {e.response.status_code}')
        return None
    except Exception as e:
        logger.error(f'DeepSeek 翻译 API 调用异常: {e}')
        return None
