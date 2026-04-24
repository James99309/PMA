# -*- coding: utf-8 -*-
"""
聊天翻译服务

使用 Claude Haiku 模型提供中英文消息翻译功能。
"""
import os
import logging

import anthropic

logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {
    'zh': '中文',
    'en': 'English',
}

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY'),
            base_url=os.environ.get('ANTHROPIC_BASE_URL'),
        )
    return _client


def translate_text(text, source_lang, target_lang):
    """翻译文本，失败返回 None"""
    if not text or not text.strip():
        return None
    if source_lang == target_lang:
        return text
    try:
        return _translate_with_claude(text, source_lang, target_lang)
    except Exception as e:
        logger.error(f'翻译失败: {e}')
        return None


def _translate_with_claude(text, source_lang, target_lang):
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        logger.warning('未配置 ANTHROPIC_API_KEY，无法翻译')
        return None

    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
    model = os.environ.get('CHAT_TRANSLATION_MODEL', 'claude-haiku-4-5-20251001')

    try:
        message = _get_client().messages.create(
            model=model,
            max_tokens=1024,
            system='You are a translation engine. Output ONLY the translated text. No explanations, no preamble, no commentary.',
            messages=[{
                'role': 'user',
                'content': (
                    f'Translate the following {source_name} text to {target_name}.\n'
                    f'Output ONLY the translation, nothing else.\n\n'
                    f'Text to translate:\n"""\n{text}\n"""'
                ),
            }],
        )
        return message.content[0].text.strip() or None
    except anthropic.APIStatusError as e:
        logger.error(f'Claude 翻译 API 错误: {e.status_code}')
        return None
    except anthropic.APITimeoutError:
        logger.error('Claude 翻译 API 超时')
        return None
    except Exception as e:
        logger.error(f'Claude 翻译 API 异常: {e}')
        return None
