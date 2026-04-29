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
_MAX_ITERATIONS = 10  # 最多 tool 调用轮次（降低避免上下文过大触发 api_error）
_MAX_TOKENS = 16000   # 输出 token 上限（提高避免截断）


def _log_research_usage(user_id: int, input_tokens: int, output_tokens: int) -> None:
    """将调研 token 用量写入 AIProxyUsage 表（provider='claude_research'）。"""
    if not user_id or (input_tokens + output_tokens) <= 0:
        return
    try:
        from datetime import date as date_type
        from app import db
        from app.models.ai_proxy_usage import AIProxyUsage
        today = date_type.today()
        row = AIProxyUsage.query.filter_by(
            user_id=user_id, provider='claude_research', date=today
        ).first()
        if row:
            row.input_tokens  += input_tokens
            row.output_tokens += output_tokens
            row.request_count += 1
        else:
            row = AIProxyUsage(
                user_id=user_id, provider='claude_research', date=today,
                input_tokens=input_tokens, output_tokens=output_tokens, request_count=1,
            )
            db.session.add(row)
        db.session.commit()
    except Exception as e:
        logger.warning(f'[Claude-Research] 记录用量失败 user={user_id}: {e}')


def send_claude_research_request(prompt: str, timeout: int = 300,
                                  user_id: int | None = None) -> str:
    """向 Claude 发送调研请求，自动处理 web_search 工具调用循环。

    接口与 send_openclaw_request 兼容（返回纯文本字符串）。

    Args:
        prompt:   调研提示词（已包含 web_search 指令和 JSON 格式要求）
        timeout:  超时秒数
        user_id:  触发调研的用户 ID，用于统计用量；批量自动任务传 None 则不记录

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

    system_blocks = [{'type': 'text', 'text': (
        '你是一个专业的工程项目信息调研助手。'
        '使用 web_search 工具收集信息后，最终回复必须是且仅是合法的 JSON 对象。'
        '严禁在 JSON 前后添加任何解释、总结或 markdown 代码块。'
        'JSON 字符串值内如需引用内容，必须使用中文引号「」或将双引号转义为 \\"。'
    )}]

    total_input_tokens = 0
    total_output_tokens = 0

    for iteration in range(_MAX_ITERATIONS):
        full_text = ''
        tool_uses: list[dict] = []
        stop_reason: str | None = None
        error: str | None = None

        for event in client.stream(
            system_blocks=system_blocks,
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
                usage = event.get('usage', {})
                total_input_tokens  += usage.get('input_tokens', 0) or 0
                total_output_tokens += usage.get('output_tokens', 0) or 0
            elif t == 'error':
                error = event.get('message', '未知错误')
                break

        if error:
            _log_research_usage(user_id, total_input_tokens, total_output_tokens)
            raise RuntimeError(f'Claude API 错误: {error}')

        logger.info(
            f'[Claude-Research] 轮次 {iteration + 1}: '
            f'stop={stop_reason} tools={len(tool_uses)} text_chars={len(full_text)} '
            f'tokens={total_input_tokens}+{total_output_tokens}'
        )

        # 无工具调用或自然结束
        if stop_reason == 'end_turn' or not tool_uses:
            if not full_text.strip():
                _log_research_usage(user_id, total_input_tokens, total_output_tokens)
                raise RuntimeError('Claude 返回了空响应')
            _log_research_usage(user_id, total_input_tokens, total_output_tokens)
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
    _log_research_usage(user_id, total_input_tokens, total_output_tokens)
    if not full_text.strip():
        raise RuntimeError(f'Claude 在 {_MAX_ITERATIONS} 轮后仍未返回有效内容')
    return full_text
