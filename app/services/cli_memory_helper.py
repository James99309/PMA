# -*- coding: utf-8 -*-
"""
CliMemory 索引构建器（CLI + Chat 共用）

把 cli_memories 表里当前用户可见的记忆（system / role:xxx / personal）
拼成一段 prompt 文本，放进 system prompt 的动态段让 LLM 看到索引。
LLM 判断需要哪条的完整内容时调 recall_memory 工具按 id 读取。

注：表名 cli_memories / 类名 CliMemory 是历史遗留（起于 CLI），
现在已成为用户级通用记忆表。CLI 终端和 Chat 助手共享同一张表，
一个用户一套画像。
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def build_memory_index_section(user) -> str:
    """加载用户可见的记忆索引，返回用于插入 system prompt 的文本段。

    返回空字符串如果没有任何可见记忆（避免塞一段空的 "[记忆索引]" 进去）。
    """
    try:
        from app.models.cli_memory import CliMemory
        from sqlalchemy import or_, and_

        user_role = getattr(user, 'role', '')
        memories = (
            CliMemory.query.filter(
                CliMemory.is_active == True,
                or_(
                    CliMemory.scope == 'system',
                    CliMemory.scope == f'role:{user_role}',
                    and_(
                        CliMemory.scope == 'personal',
                        CliMemory.user_id == user.id,
                    ),
                ),
            )
            .order_by(CliMemory.scope, CliMemory.id)
            .limit(50)
            .all()
        )
    except Exception as e:
        logger.warning(f'[memory_helper] 加载记忆索引失败: {e}')
        return ''

    if not memories:
        return ''

    lines = ['\n[记忆索引（如需详情调用 recall_memory(id)）]']
    for m in memories:
        lines.append(m.to_index_line())
    return '\n'.join(lines) + '\n'
