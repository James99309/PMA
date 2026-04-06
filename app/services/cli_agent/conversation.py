# -*- coding: utf-8 -*-
"""
对话数据结构:ContentBlock + Message + Conversation

与 Anthropic Python SDK 原生消息格式兼容,可以直接传给
client.messages.create(messages=...) 的 messages 参数。

设计参考: claw-code runtime/src/conversation.rs (MIT, 见 THIRD_PARTY_NOTICES.md)
但这里是针对 PMA 场景的 Python 全新实现,不是 Rust 的翻译。
"""
from __future__ import annotations

import uuid
from typing import Any


# ─── Content block 构造器(纯函数,返回 dict)─────────────────────────────

def text_block(text: str) -> dict:
    """文本块"""
    return {'type': 'text', 'text': text}


def tool_use_block(name: str, tool_input: dict, tool_use_id: str | None = None) -> dict:
    """LLM 发起工具调用"""
    return {
        'type': 'tool_use',
        'id': tool_use_id or f'toolu_{uuid.uuid4().hex[:16]}',
        'name': name,
        'input': tool_input,
    }


def tool_result_block(tool_use_id: str, content: Any, is_error: bool = False) -> dict:
    """工具执行结果,与上一条 tool_use 通过 id 配对"""
    if isinstance(content, (dict, list)):
        import json
        content_str = json.dumps(content, ensure_ascii=False, default=str)
    else:
        content_str = str(content)
    return {
        'type': 'tool_result',
        'tool_use_id': tool_use_id,
        'content': content_str,
        'is_error': is_error,
    }


# ─── Conversation 辅助函数 ──────────────────────────────────────────────

def new_user_message(text: str) -> dict:
    """构造一条用户纯文本消息"""
    return {'role': 'user', 'content': [text_block(text)]}


def new_assistant_message(blocks: list[dict]) -> dict:
    """构造一条 assistant 消息(可含文本和 tool_use)"""
    return {'role': 'assistant', 'content': blocks}


def new_tool_result_message(tool_results: list[dict]) -> dict:
    """构造一条工具结果消息(按 Anthropic 规范,以 user role 承载 tool_result)"""
    return {'role': 'user', 'content': tool_results}


def extract_tool_uses(message: dict) -> list[dict]:
    """从一条 assistant 消息里找出所有 tool_use 块"""
    content = message.get('content', [])
    if isinstance(content, str):
        return []
    return [b for b in content if isinstance(b, dict) and b.get('type') == 'tool_use']


def extract_text(message: dict) -> str:
    """把一条消息中的所有 text 块拼成一个字符串(方便显示)"""
    content = message.get('content', [])
    if isinstance(content, str):
        return content
    return ''.join(b.get('text', '') for b in content
                   if isinstance(b, dict) and b.get('type') == 'text')


def validate_tool_use_result_pairing(messages: list[dict]) -> None:
    """校验 tool_use 和 tool_result 的 id 配对。违反会抛 ValueError。

    Anthropic API 要求:每个 assistant 消息里的 tool_use,必须在
    **下一条 user 消息里**立即出现对应 id 的 tool_result。
    """
    pending_ids: set[str] = set()
    for i, msg in enumerate(messages):
        role = msg.get('role')
        blocks = msg.get('content', [])
        if isinstance(blocks, str):
            continue

        if role == 'assistant':
            if pending_ids:
                raise ValueError(
                    f'消息 {i}: assistant 消息前存在未响应的 tool_use: {pending_ids}'
                )
            for b in blocks:
                if b.get('type') == 'tool_use':
                    pending_ids.add(b['id'])
        elif role == 'user':
            for b in blocks:
                if isinstance(b, dict) and b.get('type') == 'tool_result':
                    tid = b.get('tool_use_id')
                    if tid in pending_ids:
                        pending_ids.discard(tid)
                    else:
                        raise ValueError(
                            f'消息 {i}: tool_result 指向不存在的 tool_use_id: {tid}'
                        )
            # 必须清空(所有之前的 tool_use 都得响应)
            if pending_ids and any(b.get('type') != 'tool_result'
                                   for b in blocks if isinstance(b, dict)):
                raise ValueError(
                    f'消息 {i}: user 消息必须先响应未完成的 tool_use: {pending_ids}'
                )
    if pending_ids:
        raise ValueError(f'对话末尾仍有未响应的 tool_use: {pending_ids}')
