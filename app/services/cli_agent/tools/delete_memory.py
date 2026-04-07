# -*- coding: utf-8 -*-
"""
delete_memory 工具：删除过时或错误的记忆。

AI 在发现记忆与新信息矛盾时主动调用。
只能删除 personal scope 的自己的记忆。
"""
from __future__ import annotations

import logging
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)


class DeleteMemoryTool(BaseTool):
    name = 'delete_memory'
    description = (
        '删除一条过时或错误的记忆。当用户纠正了之前的理解，或记忆内容已过时时调用。\n'
        '传入 memory_id（索引中的 #N）。只能删除自己的 personal 记忆。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'memory_id': {
                'type': 'integer',
                'description': '要删除的记忆 ID',
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
            from app import db
            from app.models.cli_memory import CliMemory

            memory = CliMemory.query.get(memory_id)
            if not memory or not memory.is_active:
                return {'error': f'记忆 #{memory_id} 不存在'}

            if memory.scope != 'personal' or memory.user_id != user.id:
                return {'error': '只能删除自己的个人记忆'}

            memory.is_active = False
            db.session.commit()

            logger.info(f'[CLI Agent] delete_memory: #{memory_id} {memory.title}')
            return {'message': f'已删除记忆 #{memory_id}: {memory.title}'}

        except Exception as e:
            logger.exception('[CLI Agent] delete_memory 异常')
            return {'error': '删除失败'}
