# -*- coding: utf-8 -*-
"""
规则化上下文压缩（无 LLM 调用）

触发: estimate_messages_tokens(messages) >= CLI_CONTEXT_HARD_COMPACT
行为:
    1. 保留最近 CLI_KEEP_RECENT_MESSAGES 条消息原样不动
    2. 老消息用规则提取结构化摘要
    3. 摘要作为 system 消息插入保留段开头
    4. 与之前的压缩摘要合并
"""
from __future__ import annotations

import re
from datetime import datetime

from app.services.cli_agent.config import (
    CLI_CONTEXT_HARD_COMPACT,
    CLI_KEEP_RECENT_MESSAGES,
)
from app.services.cli_agent.usage import estimate_messages_tokens


def should_compact(messages: list[dict]) -> bool:
    """判断是否需要压缩。"""
    if len(messages) <= CLI_KEEP_RECENT_MESSAGES:
        return False
    return estimate_messages_tokens(messages) >= CLI_CONTEXT_HARD_COMPACT


def compact(messages: list[dict], previous_summary: str | None = None) -> tuple[list[dict], str]:
    """执行压缩，返回 (新消息列表, 新摘要文本)。

    Returns:
        (new_messages, summary_text)
        new_messages: [summary_msg] + 最近 N 条原样消息
        summary_text: 存入 compaction_meta 的摘要文本
    """
    keep_count = CLI_KEEP_RECENT_MESSAGES
    if len(messages) <= keep_count:
        return messages, previous_summary or ''

    old_messages = messages[:-keep_count]
    recent_messages = messages[-keep_count:]

    # 提取摘要
    summary = _summarize_old_messages(old_messages)

    # 合并历史摘要
    if previous_summary:
        full_summary = f'[之前的对话摘要]\n{previous_summary}\n\n[本次压缩的对话摘要]\n{summary}'
    else:
        full_summary = summary

    # 构建摘要消息（作为 user 消息，让 LLM 知道上下文）
    summary_msg = {
        'role': 'user',
        'content': [{
            'type': 'text',
            'text': f'<compacted_summary>\n{full_summary}\n</compacted_summary>\n\n'
                    f'以上是之前对话的摘要。最近的 {keep_count} 条消息保留原样如下。'
                    f'请继续对话，无需重新确认。',
        }],
    }

    new_messages = [summary_msg] + recent_messages
    return new_messages, full_summary


def _summarize_old_messages(messages: list[dict]) -> str:
    """从老消息中提取结构化摘要（纯规则，不调 LLM）。"""
    user_requests: list[str] = []
    entities: set[str] = set()
    tool_calls: list[str] = []
    key_data: list[str] = []
    msg_counts = {'user': 0, 'assistant': 0, 'tool': 0}

    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', [])
        if isinstance(content, str):
            blocks = [{'type': 'text', 'text': content}]
        else:
            blocks = content

        if role == 'user':
            msg_counts['user'] += 1
            for b in blocks:
                if b.get('type') == 'text':
                    text = b['text']
                    # 跳过压缩摘要消息
                    if '<compacted_summary>' in text:
                        continue
                    user_requests.append(text[:100])
                elif b.get('type') == 'tool_result':
                    msg_counts['tool'] += 1

        elif role == 'assistant':
            msg_counts['assistant'] += 1
            for b in blocks:
                if b.get('type') == 'text':
                    text = b['text']
                    # 提取加粗的业务实体
                    for m in re.findall(r'\*\*(.+?)\*\*', text):
                        if len(m) <= 30:
                            entities.add(m)
                    # 提取金额
                    for m in re.findall(r'[¥$€]\s?[\d,]+\.?\d*(?:万)?', text):
                        key_data.append(m)
                elif b.get('type') == 'tool_use':
                    tool_calls.append(b.get('name', '?'))

    lines = []
    lines.append(f'对话统计: 用户 {msg_counts["user"]} 条, AI {msg_counts["assistant"]} 条, 工具调用 {msg_counts["tool"]} 次')

    if user_requests:
        lines.append(f'用户请求摘要:')
        for i, req in enumerate(user_requests[-5:], 1):  # 最近 5 条
            lines.append(f'  {i}. {req}')

    if entities:
        lines.append(f'涉及的业务实体: {", ".join(sorted(entities)[:15])}')

    if key_data:
        unique_data = list(dict.fromkeys(key_data))[:10]
        lines.append(f'关键数据: {", ".join(unique_data)}')

    if tool_calls:
        tool_summary = {}
        for t in tool_calls:
            tool_summary[t] = tool_summary.get(t, 0) + 1
        tool_str = ', '.join(f'{k}×{v}' for k, v in tool_summary.items())
        lines.append(f'工具使用: {tool_str}')

    lines.append(f'压缩时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')

    return '\n'.join(lines)
