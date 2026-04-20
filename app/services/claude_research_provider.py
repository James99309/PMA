# -*- coding: utf-8 -*-
"""
Claude 直接调研提供者

使用和 CLI 相同的方式调用 Claude API（OAuth identity prefix + 工具调用），
替代 OpenClaw 网关做 AI 调研任务。

环境变量:
    AI_RESEARCH_MODEL  模型 ID，默认 claude-sonnet-4-6
    ANTHROPIC_API_KEY  必填
"""
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = 'claude-sonnet-4-6'
_MAX_ITERATIONS = 15  # 最多 tool 调用轮次
_MAX_TOKENS = 8192


def send_claude_research_request(prompt: str, timeout: int = 300) -> str:
    """向 Claude 发送调研请求，自动处理 web_search 工具调用循环。

    接口与 send_openclaw_request 兼容（返回纯文本字符串）。

    Args:
        prompt: 调研提示词（已包含 web_search 指令和 JSON 格式要求）
        timeout: 超时秒数（当前实现为 httpx 连接级超时，由 ClaudeClient 控制）

    Returns:
        str: Claude 的最终文本回复

    Raises:
        RuntimeError: API 错误或空回复
    """
    from app.services.cli_agent.llm_client import ClaudeClient, LLMClientError
    from app.services.cli_agent.tools.web_search import WebSearchTool

    model = os.environ.get('AI_RESEARCH_MODEL', _DEFAULT_MODEL).strip()
    logger.info(f'[Claude-Research] 开始调研 model={model} prompt_chars={len(prompt)}')

    try:
        client = ClaudeClient(model=model)
    except LLMClientError as e:
        raise RuntimeError(f'Claude 客户端初始化失败: {e}') from e

    web_search = WebSearchTool()
    tools = [web_search.to_anthropic_schema()]
    messages: list[dict] = [{'role': 'user', 'content': prompt}]

    for iteration in range(_MAX_ITERATIONS):
        full_text = ''
        tool_uses: list[dict] = []
        stop_reason: str | None = None
        error: str | None = None

        for event in client.stream(
            system_blocks=[],
            tools=tools,
            messages=messages,
            max_tokens=_MAX_TOKENS,
        ):
            t = event['type']
            if t == 'text_delta':
                full_text += event['text']
            elif t == 'tool_use':
                tool_uses.append(event)
            elif t == 'message_stop':
                stop_reason = event.get('stop_reason')
            elif t == 'error':
                error = event.get('message', '未知错误')
                break

        if error:
            raise RuntimeError(f'Claude API 错误: {error}')

        logger.info(
            f'[Claude-Research] 轮次 {iteration + 1}: '
            f'stop={stop_reason} tools={len(tool_uses)} text_chars={len(full_text)}'
        )

        # 无工具调用或自然结束
        if stop_reason == 'end_turn' or not tool_uses:
            if not full_text.strip():
                raise RuntimeError('Claude 返回了空响应')
            return full_text

        # 构造 assistant 轮（包含文本 + tool_use 块）
        assistant_content: list[dict] = []
        if full_text:
            assistant_content.append({'type': 'text', 'text': full_text})
        for tu in tool_uses:
            assistant_content.append({
                'type': 'tool_use',
                'id': tu['id'],
                'name': tu['name'],
                'input': tu['input'],
            })
        messages.append({'role': 'assistant', 'content': assistant_content})

        # 执行工具并收集结果
        tool_results: list[dict] = []
        for tu in tool_uses:
            logger.info(f'[Claude-Research] 执行工具 {tu["name"]}: {str(tu["input"])[:100]}')
            try:
                result = web_search.execute(tu['input'], context={})
            except Exception as e:
                logger.warning(f'[Claude-Research] 工具执行失败: {e}')
                result = {'error': str(e)}
            tool_results.append({
                'type': 'tool_result',
                'tool_use_id': tu['id'],
                'content': json.dumps(result, ensure_ascii=False, default=str),
            })
        messages.append({'role': 'user', 'content': tool_results})

    # 超出最大轮次，返回已有内容
    logger.warning(f'[Claude-Research] 达到最大轮次 {_MAX_ITERATIONS}，返回当前内容')
    if not full_text.strip():
        raise RuntimeError(f'Claude 在 {_MAX_ITERATIONS} 轮后仍未返回有效内容')
    return full_text
