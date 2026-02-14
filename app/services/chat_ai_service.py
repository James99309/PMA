# -*- coding: utf-8 -*-
"""
AI 对话服务

集成 Anthropic Claude 和 OpenAI API，提供 AI 对话的流式响应功能。
优先使用 Anthropic API，如未配置则回退到 OpenAI API。

- 支持 SSE（Server-Sent Events）流式输出
- 记录 token 用量（prompt_tokens / completion_tokens）用于成本追踪
- 系统提示词包含用户上下文（姓名、部门、角色）
"""
import json
import os
import logging

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 系统提示词
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    '你是 PMA（项目管理助手）系统的 AI 助手。你可以：\n'
    '1. 回答关于产品、报价、项目管理等业务问题\n'
    '2. 帮助用户进行中英文翻译\n'
    '3. 提供数据分析和业务洞察\n'
    '4. 解答技术问题和操作指引\n\n'
    '请根据用户使用的语言回复（如用户用中文提问则用中文回答，用英文提问则用英文回答）。\n'
    '回答应简洁、准确、有帮助。'
)


def _build_system_prompt(user):
    """构建包含用户上下文的系统提示词

    Args:
        user: 当前用户对象，具有 real_name, username, department, role 属性

    Returns:
        str: 完整的系统提示词
    """
    user_name = getattr(user, 'real_name', None) or getattr(user, 'username', '未知用户')
    department = getattr(user, 'department', None) or '未设置'
    role = getattr(user, 'role', None) or 'user'

    user_context = (
        f'\n\n当前用户信息：\n'
        f'- 姓名：{user_name}\n'
        f'- 部门：{department}\n'
        f'- 角色：{role}'
    )

    return SYSTEM_PROMPT + user_context


# ---------------------------------------------------------------------------
# 主入口：流式 AI 响应
# ---------------------------------------------------------------------------

def get_ai_response_stream(message, user):
    """获取 AI 流式响应的生成器

    优先使用 Anthropic API，如未配置则使用 OpenAI API。
    如果都未配置，yield 一条警告消息。

    Args:
        message: 用户发送的消息文本
        user: 当前用户对象

    Yields:
        dict: 包含以下类型之一：
            - {'type': 'content', 'text': '...'} 内容片段
            - {'type': 'done', 'model': '...', 'prompt_tokens': N, 'completion_tokens': N} 完成信号
    """
    # 优先检查 Anthropic API
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_key:
        try:
            yield from _stream_anthropic(message, user, anthropic_key)
            return
        except Exception as e:
            logger.error(f'Anthropic 流式响应异常: {e}')
            # 回退到 OpenAI
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                logger.info('Anthropic API 失败，回退到 OpenAI API')
                try:
                    yield from _stream_openai(message, user, openai_key)
                    return
                except Exception as e2:
                    logger.error(f'OpenAI 流式响应也失败: {e2}')
            # 两个都失败，yield 错误信息
            yield {'type': 'content', 'text': '抱歉，AI 服务暂时不可用，请稍后重试。'}
            yield {'type': 'done', 'model': 'error', 'prompt_tokens': 0, 'completion_tokens': 0}
            return

    # 检查 OpenAI API
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        try:
            yield from _stream_openai(message, user, openai_key)
            return
        except Exception as e:
            logger.error(f'OpenAI 流式响应异常: {e}')
            yield {'type': 'content', 'text': '抱歉，AI 服务暂时不可用，请稍后重试。'}
            yield {'type': 'done', 'model': 'error', 'prompt_tokens': 0, 'completion_tokens': 0}
            return

    # 未配置任何 API 密钥
    logger.warning('未配置 AI API 密钥 (ANTHROPIC_API_KEY 或 OPENAI_API_KEY)')
    yield {
        'type': 'content',
        'text': '⚠️ AI 功能未配置。请联系管理员设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 环境变量。'
    }
    yield {'type': 'done', 'model': 'none', 'prompt_tokens': 0, 'completion_tokens': 0}


# ---------------------------------------------------------------------------
# Anthropic Claude 流式响应
# ---------------------------------------------------------------------------

def _stream_anthropic(message, user, api_key):
    """使用 Anthropic Claude API 进行流式响应

    Args:
        message: 用户消息文本
        user: 当前用户对象
        api_key: Anthropic API 密钥

    Yields:
        dict: content 或 done 类型的响应片段
    """
    model = os.environ.get('ANTHROPIC_CHAT_MODEL', 'claude-sonnet-4-5-20250929')
    system_prompt = _build_system_prompt(user)

    request_body = {
        'model': model,
        'max_tokens': 2048,
        'system': system_prompt,
        'messages': [
            {'role': 'user', 'content': message}
        ],
        'stream': True,
    }

    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
    }

    prompt_tokens = 0
    completion_tokens = 0

    with httpx.Client(timeout=60.0) as client:
        with client.stream(
            'POST',
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=request_body,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                # SSE 格式：以 "data: " 开头
                if not line.startswith('data: '):
                    continue

                data_str = line[6:]  # 去掉 "data: " 前缀

                # 流结束标记
                if data_str.strip() == '[DONE]':
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                event_type = data.get('type', '')

                # 消息开始 - 获取 input_tokens
                if event_type == 'message_start':
                    usage = data.get('message', {}).get('usage', {})
                    prompt_tokens = usage.get('input_tokens', 0)

                # 内容块增量 - 输出文本
                elif event_type == 'content_block_delta':
                    delta = data.get('delta', {})
                    if delta.get('type') == 'text_delta':
                        text = delta.get('text', '')
                        if text:
                            yield {'type': 'content', 'text': text}

                # 消息结束增量 - 获取 output_tokens
                elif event_type == 'message_delta':
                    usage = data.get('usage', {})
                    completion_tokens = usage.get('output_tokens', 0)

    yield {
        'type': 'done',
        'model': model,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
    }


# ---------------------------------------------------------------------------
# OpenAI 流式响应
# ---------------------------------------------------------------------------

def _stream_openai(message, user, api_key):
    """使用 OpenAI API 进行流式响应

    支持通过 OPENAI_API_BASE 配置自定义端点（兼容第三方 OpenAI 兼容 API）。

    Args:
        message: 用户消息文本
        user: 当前用户对象
        api_key: OpenAI API 密钥

    Yields:
        dict: content 或 done 类型的响应片段
    """
    model = os.environ.get('OPENAI_CHAT_MODEL', 'gpt-4o-mini')
    base_url = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1').rstrip('/')
    system_prompt = _build_system_prompt(user)

    request_body = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': message},
        ],
        'max_tokens': 2048,
        'stream': True,
        'stream_options': {'include_usage': True},
    }

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    prompt_tokens = 0
    completion_tokens = 0

    with httpx.Client(timeout=60.0) as client:
        with client.stream(
            'POST',
            f'{base_url}/chat/completions',
            headers=headers,
            json=request_body,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                # SSE 格式
                if not line.startswith('data: '):
                    continue

                data_str = line[6:]

                if data_str.strip() == '[DONE]':
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                # 提取内容增量
                choices = data.get('choices', [])
                if choices:
                    delta = choices[0].get('delta', {})
                    content = delta.get('content')
                    if content:
                        yield {'type': 'content', 'text': content}

                # 提取 token 用量（stream_options.include_usage=true 时，
                # 最后一个 chunk 会包含 usage 字段）
                usage = data.get('usage')
                if usage:
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    completion_tokens = usage.get('completion_tokens', 0)

    yield {
        'type': 'done',
        'model': model,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
    }
