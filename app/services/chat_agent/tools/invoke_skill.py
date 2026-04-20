# -*- coding: utf-8 -*-
"""Chat Agent invoke_skill 工具

复用 CliSkill 定义，但用 execute_chat_safe_query（前端权限模型）替代
execute_safe_query（CLI 权限模型），确保 Chat 用户无需配置 cli_permissions
也能调用 skill，同时行级权限过滤仍然生效。

安全保证：execute_chat_safe_query 通过 get_viewable_data 注入 id IN (...)
过滤，用户只能看到自己权限范围内的数据行，不会暴露未授权记录。
"""
from __future__ import annotations

import logging

from app.services.cli_agent.tools import BaseTool
from app.services.cli_agent.config import CLI_TOOL_RESULT_MAX_TOKENS

logger = logging.getLogger(__name__)


class ChatInvokeSkillTool(BaseTool):
    name = 'invoke_skill'
    description = (
        '调用预定义业务技能执行多步骤复合查询。\n'
        '- 通过 skill_name 指定要调用的技能（见系统提示中的 [可用 Skill] 列表）。\n'
        '- 用户消息匹配某个 Skill 的触发场景时，优先调用此工具，比逐条 query_pma_database 更全面准确。\n'
        '- 从用户消息中提取所有参数值（人名、时间词等），映射到 params 后一次性传入，不要遗漏。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'skill_name': {
                'type': 'string',
                'description': '技能名称，如 work_summary / customer_overview 等',
            },
            'params': {
                'type': 'object',
                'description': '技能参数字典，如 {"user_name": "范敬", "period": "last_week"}',
            },
        },
        'required': ['skill_name'],
    }

    def execute(self, input_data: dict, context: dict) -> dict:
        user = context.get('user')
        skill_name = (input_data.get('skill_name') or '').strip()
        params = input_data.get('params') or {}

        if not skill_name:
            return {'error': '请提供 skill_name'}

        # 查询 Skill 定义
        try:
            from app.models.cli_skill import CliSkill
            from sqlalchemy import or_
            skill = CliSkill.query.filter_by(
                name=skill_name,
                is_active=True,
            ).first()
        except Exception as e:
            logger.exception('[Chat invoke_skill] 查询 CliSkill 失败')
            return {'error': f'查询技能定义失败: {e}'}

        if skill is None:
            return {'error': f'未找到技能 "{skill_name}"，请确认名称正确'}

        # docx/xlsx/tool 类型是样式库，不可直接调用
        if getattr(skill, 'skill_type', 'sql') in ('docx', 'xlsx', 'tool'):
            return {'error': f'"{skill_name}" 是样式库，不能直接调用'}

        # personal scope 仅创建者可用
        if skill.scope == 'personal' and skill.created_by != user.id:
            return {'error': f'技能 "{skill_name}" 是个人技能，仅创建者可使用'}

        # 执行：使用 execute_chat_safe_query（前端权限模型）
        try:
            from app.services.cli_agent.skill_engine import SkillEngine
            from app.services.chat_db_query import execute_chat_safe_query
            result = SkillEngine.execute(skill, params, user, query_fn=execute_chat_safe_query)
        except Exception as e:
            logger.exception(f'[Chat invoke_skill] 执行技能 {skill_name} 异常')
            return {'error': f'技能执行异常: {e}'}

        if not result.get('success'):
            return {'error': result.get('error', '技能执行失败')}

        output = result.get('output', '')
        response = {
            'skill_name': skill_name,
            'skill_title': skill.title,
            'output': output,
            'instruction': (
                '请将上面的 output 内容完整输出给用户，不要删减章节、'
                '不要重新排版、不要跳过表格。'
            ),
        }

        # token 安全检查：超大结果截断
        import json
        serialized = json.dumps(response, ensure_ascii=False, default=str)
        if len(serialized) // 3 > CLI_TOOL_RESULT_MAX_TOKENS:
            max_chars = CLI_TOOL_RESULT_MAX_TOKENS * 3
            response['output'] = output[:max_chars] + '\n\n（内容过长，已截断）'
            response['truncated'] = True

        return response
