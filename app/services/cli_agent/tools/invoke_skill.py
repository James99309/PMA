# -*- coding: utf-8 -*-
"""
invoke_skill 工具:调用 CliSkill 定义的预构建业务查询技能。

当 Agent 匹配到已有的 Skill 时,优先使用此工具而非 query_pma_database,
因为 Skill 的 SQL 模板经过预先验证,结果格式更统一、准确。

执行链路:
    LLM tool_use(invoke_skill) → 本工具 → SkillEngine.execute()
                                          → execute_safe_query()(带权限注入)
                                          → Markdown 格式化输出
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.services.cli_agent.tools import BaseTool
from app.services.cli_agent.config import CLI_TOOL_RESULT_MAX_TOKENS

logger = logging.getLogger(__name__)


class InvokeSkillTool(BaseTool):
    name = 'invoke_skill'
    description = (
        '调用预定义的业务查询 Skill。匹配已有 Skill 时优先使用,结果比 query_pma_database 更准确一致。\n'
        '- 通过 skill_name 指定要调用的技能(见系统提示中的可用 Skill 列表)。\n'
        '- parameters 是技能所需的参数键值对(参考各 Skill 的参数定义)。\n'
        '- 返回 Markdown 格式的结果输出;如果失败,返回含 error 字段的 JSON。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'skill_name': {
                'type': 'string',
                'description': 'Skill 标识名',
            },
            'user_name': {
                'type': 'string',
                'description': '人员姓名(如果 Skill 需要)',
            },
            'keyword': {
                'type': 'string',
                'description': '搜索关键词(如果 Skill 需要)',
            },
            'period': {
                'type': 'string',
                'description': '时间周期: this_week/last_week/this_month/last_month/this_quarter/last_quarter/this_year/last_year',
            },
        },
        'required': ['skill_name'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        raw_name = (tool_input or {}).get('skill_name', '').strip()
        skill_name = raw_name.split('(')[0].strip()
        user = context.get('user')

        # 参数提取：优先从 parameters 嵌套对象，fallback 从顶层提取
        params = (tool_input or {}).get('parameters') or {}
        if not params:
            reserved = {'skill_name', 'parameters'}
            params = {k: v for k, v in (tool_input or {}).items() if k not in reserved and v}

        logger.info(f'[CLI Agent] invoke_skill 收到: skill_name={skill_name}, params={params}, raw_input={tool_input}')

        if not skill_name:
            return {'error': 'skill_name 参数不能为空'}
        if user is None:
            return {'error': '内部错误:缺少用户上下文'}

        # --- 1. 从数据库查找 Skill ---
        try:
            from app.models.cli_skill import CliSkill
            skill = CliSkill.query.filter_by(
                name=skill_name,
                is_active=True,
            ).first()
        except Exception as e:
            logger.exception('[CLI Agent] invoke_skill 查询 CliSkill 异常')
            return {'error': f'查询技能定义失败: {e}'}

        if skill is None:
            return {
                'error': f'未找到名为 "{skill_name}" 的活跃技能。请检查名称或使用 query_pma_database 直接查询。',
            }

        # --- 2a. docx 类型是样式库，不可直接调用 ---
        if getattr(skill, 'skill_type', 'sql') == 'docx':
            return {
                'error': f'"{skill_name}" 是样式库，不能直接调用。'
                         f'请使用 export_to_word 工具生成 Word 文档。',
            }

        # --- 2. 权限检查:personal scope 只限创建者使用 ---
        if skill.scope == CliSkill.SCOPE_PERSONAL and skill.created_by != user.id:
            return {
                'error': f'技能 "{skill_name}" 是个人技能,仅创建者可使用。',
            }

        # --- 3. 调用 SkillEngine 执行 ---
        try:
            from app.services.cli_agent.skill_engine import SkillEngine
            result = SkillEngine.execute(skill, params, user)
        except Exception as e:
            logger.exception(f'[CLI Agent] invoke_skill 执行技能 {skill_name} 异常')
            return {'error': f'技能执行异常: {e}'}

        if not result.get('success'):
            return {'error': result.get('error', '技能执行失败')}

        # --- 4. 组装输出,检查大小 ---
        output = result.get('output', '')
        artifacts = result.get('artifacts', [])
        raw_results = result.get('raw_results', {})

        # 构建返回体
        response: dict = {
            'skill_name': skill_name,
            'skill_title': skill.title,
            'output': output,
            'artifacts': artifacts,
            'instruction': '请将上面的 output 内容完整输出给用户，不要删减章节、不要重新排版、不要跳过表格。',
        }

        # 附加各步骤行数统计
        step_summary = {}
        for step_name, step_data in raw_results.items():
            step_summary[step_name] = step_data.get('row_count', 0)
        if step_summary:
            response['step_row_counts'] = step_summary

        # token 安全:过大则截断 output
        serialized = json.dumps(response, ensure_ascii=False, default=str)
        estimated_tokens = len(serialized) // 3
        if estimated_tokens > CLI_TOOL_RESULT_MAX_TOKENS:
            # 截断 output 文本,保留前 N 字符
            max_output_chars = CLI_TOOL_RESULT_MAX_TOKENS * 2  # 粗估:1 token ≈ 2 中文字符
            response['output'] = output[:max_output_chars] + '\n\n...(输出过长已截断,请缩小查询范围)'
            response['truncated'] = True

        logger.info(
            f'[CLI Agent] invoke_skill 完成: skill={skill_name}, '
            f'steps={len(raw_results)}, output_chars={len(output)}'
        )
        return response
