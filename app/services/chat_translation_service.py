# -*- coding: utf-8 -*-
"""
聊天翻译服务

集成 Anthropic Claude 和 OpenAI API，提供中英文消息翻译功能。
优先使用 Anthropic API，如未配置则回退到 OpenAI API。
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
    """使用 AI API 进行翻译

    优先使用 Anthropic Claude API，如未配置则使用 OpenAI API。

    Args:
        text: 待翻译的文本
        source_lang: 源语言代码
        target_lang: 目标语言代码

    Returns:
        str: 翻译后的文本，失败时返回 None
    """
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    target_name = LANGUAGE_NAMES.get(target_lang, target_lang)

    # 优先使用 Anthropic API
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_key:
        result = _call_anthropic(text, source_name, target_name)
        if result is not None:
            return result
        logger.warning('Anthropic API 调用失败，尝试 OpenAI API')

    # 回退到 OpenAI API
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        return _call_openai(text, source_name, target_name)

    logger.warning('未配置任何翻译 API 密钥 (ANTHROPIC_API_KEY 或 OPENAI_API_KEY)')
    return None


def _call_anthropic(text, source_name, target_name):
    """调用 Anthropic Claude API 进行翻译

    Args:
        text: 待翻译的文本
        source_name: 源语言名称 (如 '中文')
        target_name: 目标语言名称 (如 'English')

    Returns:
        str: 翻译后的文本，失败时返回 None
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None

    prompt = (
        f'Translate the following text from {source_name} to {target_name}. '
        f'Return ONLY the translated text, nothing else.\n\n{text}'
    )

    try:
        response = httpx.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 4096,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
            },
            timeout=15.0,
        )
        response.raise_for_status()

        data = response.json()
        # Anthropic API 返回格式: {"content": [{"type": "text", "text": "..."}]}
        content_blocks = data.get('content', [])
        if content_blocks and content_blocks[0].get('type') == 'text':
            translated = content_blocks[0].get('text', '').strip()
            if translated:
                return translated

        logger.error(f'Anthropic API 响应格式异常: {data}')
        return None

    except httpx.TimeoutException:
        logger.error('Anthropic API 调用超时 (15s)')
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f'Anthropic API HTTP 错误: {e.response.status_code} - {e.response.text}')
        return None
    except Exception as e:
        logger.error(f'Anthropic API 调用异常: {e}')
        return None


def _call_openai(text, source_name, target_name):
    """调用 OpenAI API 进行翻译

    支持通过 OPENAI_API_BASE 环境变量配置自定义 API 端点。
    使用 OPENAI_CHAT_MODEL 环境变量指定模型，默认 'gpt-4o-mini'。

    Args:
        text: 待翻译的文本
        source_name: 源语言名称 (如 '中文')
        target_name: 目标语言名称 (如 'English')

    Returns:
        str: 翻译后的文本，失败时返回 None
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None

    base_url = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
    model = os.environ.get('OPENAI_CHAT_MODEL', 'gpt-4o-mini')

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
        # OpenAI API 返回格式: {"choices": [{"message": {"content": "..."}}]}
        choices = data.get('choices', [])
        if choices:
            translated = choices[0].get('message', {}).get('content', '').strip()
            if translated:
                return translated

        logger.error(f'OpenAI API 响应格式异常: {data}')
        return None

    except httpx.TimeoutException:
        logger.error('OpenAI API 调用超时 (15s)')
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f'OpenAI API HTTP 错误: {e.response.status_code} - {e.response.text}')
        return None
    except Exception as e:
        logger.error(f'OpenAI API 调用异常: {e}')
        return None
