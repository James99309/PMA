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
        '保存或更新一条结构化记忆。\n\n'
        '**何时调用：**\n'
        '- 用户身份信息（姓名、角色、部门 → type=user）\n'
        '- 用户纠正你的错误（"不对，应该用XX" → type=feedback）\n'
        '- 用户偏好（常查谁、喜欢什么格式 → type=user）\n'
        '- 重要分析结论（某人绩效差距、项目风险 → type=knowledge）\n'
        '- 业务规则澄清（植入额=报价单 → type=feedback）\n\n'
        '**何时不调用：**\n'
        '- 一次性查询（今天天气、某个数字）\n'
        '- 系统记忆已有的常识\n'
        '- 临时性数据\n\n'
        '**维护规则：**\n'
        '- 同 title 自动覆盖旧记忆\n'
        '- 发现矛盾时先 delete_memory 再保存新的\n'
        '- 保存前检查索引避免重复\n'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'type': {
                'type': 'string',
                'enum': ['user', 'feedback', 'knowledge', 'reference'],
                'description': 'user=用户画像(姓名/角色/偏好), feedback=用户纠正, knowledge=分析结论, reference=数据位置',
            },
            'title': {
                'type': 'string',
                'description': '记忆标题（简短，如"张奕是HR经理"、"植入额计算规则"）',
            },
            'facts': {
                'type': 'array',
                'items': {'type': 'string'},
                'description': '关键事实列表，每条独立可理解（如["张奕是HR经理","常查李华伟周报"]）',
            },
            'content': {
                'type': 'string',
                'description': '完整上下文说明（可选，补充 facts 的背景）',
            },
        },
        'required': ['type', 'title', 'facts'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        user = context.get('user')
        if not user:
            return {'error': '缺少用户上下文'}

        title = (tool_input or {}).get('title', '').strip()
        facts = (tool_input or {}).get('facts') or []
        content = (tool_input or {}).get('content', '').strip()
        mem_type = (tool_input or {}).get('type', 'knowledge').strip()

        if not title:
            return {'error': 'title 不能为空'}
        if not facts and not content:
            return {'error': 'facts 或 content 至少需要一个'}

        # 从 facts 生成 summary 和 content
        if facts:
            summary = '; '.join(facts[:3])[:500]
            if not content:
                content = '\n'.join(f'- {f}' for f in facts)
        else:
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
