# -*- coding: utf-8 -*-
"""
save_memory 工具：保存记忆。

两种触发方式：
1. AI 在对话中自动判断值得记住的信息 → scope=personal
2. 用户/admin 通过 /memory 命令手动保存 → scope 取决于命令

对话中 AI 自动调用时永远是 personal scope。
system/role scope 只能通过 /memory 命令创建（前端拦截）。
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)


class SaveMemoryTool(BaseTool):
    name = 'save_memory'
    description = (
        '保存或更新一条记忆。当你发现值得记住的信息时调用：\n'
        '- 用户的偏好（常查哪个人、喜欢什么格式）\n'
        '- 重要的分析结论（某人的绩效问题、项目风险）\n'
        '- 用户的反馈和纠正（"不要这样做"、"以后用这种格式"）\n\n'
        '**记忆维护规则（必须遵守）：**\n'
        '1. 用户纠正了你之前的理解时，立即更新相关记忆（传同样的 title 会自动覆盖）\n'
        '2. 保存前检查记忆索引，避免重复或矛盾\n'
        '3. 如果旧记忆已过时，用 delete_memory 删除后重新保存\n'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'title': {
                'type': 'string',
                'description': '记忆标题（简短，<50字）',
            },
            'summary': {
                'type': 'string',
                'description': '一行摘要（用于索引，<100字）',
            },
            'content': {
                'type': 'string',
                'description': '完整内容（详细信息）',
            },
            'type': {
                'type': 'string',
                'enum': ['user', 'feedback', 'knowledge', 'reference'],
                'description': '类型：user=用户身份偏好, feedback=用户纠正, knowledge=分析结论, reference=资源位置',
            },
        },
        'required': ['title', 'summary', 'content'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        user = context.get('user')
        if not user:
            return {'error': '缺少用户上下文'}

        title = (tool_input or {}).get('title', '').strip()
        summary = (tool_input or {}).get('summary', '').strip()
        content = (tool_input or {}).get('content', '').strip()
        mem_type = (tool_input or {}).get('type', 'knowledge').strip()

        if not title or not content:
            return {'error': 'title 和 content 不能为空'}
        if not summary:
            summary = content[:100]

        try:
            from app import db
            from app.models.cli_memory import CliMemory

            # 检查是否有同标题的记忆（更新而非重复创建）
            existing = CliMemory.query.filter_by(
                user_id=user.id,
                scope='personal',
                title=title,
                is_active=True,
            ).first()

            if existing:
                existing.summary = summary
                existing.content = content
                existing.type = mem_type
                existing.updated_at = datetime.utcnow()
                db.session.commit()
                logger.info(f'[CLI Agent] save_memory 更新: #{existing.id} {title}')
                return {
                    'action': 'updated',
                    'memory_id': existing.id,
                    'message': f'记忆已更新: {title}',
                }

            memory = CliMemory(
                scope='personal',
                user_id=user.id,
                type=mem_type,
                title=title[:200],
                summary=summary[:500],
                content=content,
                created_by=user.id,
            )
            db.session.add(memory)
            db.session.commit()

            logger.info(f'[CLI Agent] save_memory 创建: #{memory.id} {title}')
            return {
                'action': 'created',
                'memory_id': memory.id,
                'message': f'已记住: {title}',
            }

        except Exception as e:
            logger.exception('[CLI Agent] save_memory 异常')
            return {'error': '保存记忆失败'}
