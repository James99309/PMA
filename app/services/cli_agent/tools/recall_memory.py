# -*- coding: utf-8 -*-
"""
recall_memory 工具：按 ID 读取记忆详情。

LLM 在 prompt 中看到记忆索引后，判断需要哪条记忆的完整内容，
调用此工具按 ID 读取。
"""
from __future__ import annotations

import logging
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)


class RecallMemoryTool(BaseTool):
    name = 'recall_memory'
    description = (
        '读取记忆详情。当你在记忆索引中看到相关条目，需要了解完整内容时调用。\n'
        '传入 memory_id（索引中的 #N 编号）。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'memory_id': {
                'type': 'integer',
                'description': '记忆 ID（索引中的 #N）',
            },
        },
        'required': ['memory_id'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        memory_id = (tool_input or {}).get('memory_id')
        user = context.get('user')

        if not memory_id:
            return {'error': 'memory_id 不能为空'}

        try:
            from app.models.cli_memory import CliMemory
            memory = CliMemory.query.get(memory_id)
        except Exception as e:
            logger.exception('[CLI Agent] recall_memory 查询异常')
            return {'error': '读取记忆失败'}

        if not memory or not memory.is_active:
            return {'error': f'记忆 #{memory_id} 不存在或已删除'}

        # 权限检查：personal 只能读自己的
        if memory.scope == 'personal' and memory.user_id != user.id:
            return {'error': '无权读取此记忆'}

        # role scope 检查
        if memory.scope.startswith('role:'):
            required_role = memory.scope.split(':', 1)[1]
            if getattr(user, 'role', '') != required_role:
                return {'error': '无权读取此角色记忆'}

        return {
            'id': memory.id,
            'title': memory.title,
            'type': memory.type,
            'content': memory.content,
        }
