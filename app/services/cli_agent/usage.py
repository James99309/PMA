# -*- coding: utf-8 -*-
"""
Token 用量追踪

职责:
    1. 离线估算文本 token 数（中文优化）
    2. 估算整个对话历史的上下文大小
    3. 为 compaction 和前端展示提供 token 数据
"""
from __future__ import annotations

import re

# 中文字符正则（常见汉字区）
_CJK_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')


def estimate_tokens(text: str) -> int:
    """离线估算文本的 token 数。

    中文优化: 汉字 ≈ 1.5 token, 英文/数字 ≈ 0.25 token, JSON 符号 ≈ 0.3 token。
    比简单 len/4 对中文准确约 2 倍。
    """
    if not text:
        return 0
    cjk_count = len(_CJK_RE.findall(text))
    other_count = len(text) - cjk_count
    return int(cjk_count * 1.5 + other_count / 4) + 3  # +3 for message overhead


def estimate_messages_tokens(messages: list[dict]) -> int:
    """估算整个消息列表的 token 数。"""
    total = 0
    for msg in messages:
        content = msg.get('content', [])
        if isinstance(content, str):
            total += estimate_tokens(content)
            continue
        for block in content:
            btype = block.get('type', '')
            if btype == 'text':
                total += estimate_tokens(block.get('text', ''))
            elif btype == 'tool_use':
                total += estimate_tokens(str(block.get('input', ''))) + 20
            elif btype == 'tool_result':
                c = block.get('content', '')
                total += estimate_tokens(c if isinstance(c, str) else str(c))
        total += 4  # per-message overhead
    return total
