# -*- coding: utf-8 -*-
"""
save_skill 工具:创建或更新 CliSkill 定义。

使用场景:
    - 用户说 "帮我做一个 Skill" / "保存这个查询为模板"
    - Agent 识别到可复用查询模式,主动建议保存为 Skill

权限:
    - admin 用户可创建 scope=global 的技能(所有用户可见)
    - 非 admin 用户只能创建 scope=personal 的技能(仅自己可用)
    - 更新时只能修改自己创建的技能(admin 可修改任何技能)

安全:
    - SQL 模板保存时不做执行,仅在 invoke_skill 调用时通过
      SkillEngine → execute_safe_query 执行(自带权限注入 + 安全校验)
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)


class SaveSkillTool(BaseTool):
    name = 'save_skill'
    description = (
        '创建或更新业务 Skill。用户说"帮我做一个Skill"或"保存这个查询为模板"时使用。\n'
        '仅 admin 可创建 global Skill,其他用户创建的为 personal Skill。\n'
        '如果同名 Skill 已存在,则更新;否则新建。\n\n'
        'SQL 模板语法(必须严格遵守):\n'
        '- 参数占位: {param_name} (下划线连接,不要用点号)\n'
        '- period 类型参数自动产生 {period_start} 和 {period_end},格式为 YYYY-MM-DD\n'
        '- 字符串参数已自动带单引号,ILIKE 用法: ILIKE \'%\' || {keyword} || \'%\'\n'
        '- 前步引用: {step_name.0.column} 取第一行某列值\n'
        '- 输出模板: {step_name.table} 渲染表格, {step_name.count} 行数\n'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'name': {
                'type': 'string',
                'description': '英文标识名,如 monthly_expense_report(仅允许小写字母、数字、下划线)',
            },
            'title': {
                'type': 'string',
                'description': '中文标题,如 "月度报销汇总"',
            },
            'description': {
                'type': 'string',
                'description': '功能描述和触发词,帮助 Agent 匹配何时调用此 Skill',
            },
            'parameters': {
                'type': 'array',
                'description': '参数定义列表',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': '参数名(英文)',
                        },
                        'type': {
                            'type': 'string',
                            'enum': ['string', 'number', 'date', 'boolean', 'period'],
                            'description': '参数类型',
                        },
                        'required': {
                            'type': 'boolean',
                            'description': '是否必填',
                        },
                        'default_value': {
                            'type': 'string',
                            'description': '默认值(字符串形式)',
                        },
                        'description': {
                            'type': 'string',
                            'description': '参数说明',
                        },
                    },
                },
            },
            'queries': {
                'type': 'array',
                'description': 'SQL 查询步骤列表,按顺序执行',
                'items': {
                    'type': 'object',
                    'properties': {
                        'sql': {
                            'type': 'string',
                            'description': 'SQL 模板(SELECT/WITH 开头),可使用 {param_name} 占位符',
                        },
                        'as_name': {
                            'type': 'string',
                            'description': '步骤名称,用于后续步骤引用和输出模板',
                        },
                        'description': {
                            'type': 'string',
                            'description': '步骤说明',
                        },
                    },
                },
            },
            'output_format': {
                'type': 'string',
                'description': (
                    'Markdown 输出模板。使用 {step_name.table} 渲染表格,'
                    '{step_name.N.field} 引用单元格,{param_name} 引用参数'
                ),
            },
            'scope': {
                'type': 'string',
                'enum': ['global', 'personal'],
                'description': '作用域。admin 默认 global,非 admin 强制 personal',
            },
        },
        'required': ['name', 'title', 'queries'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        user = context.get('user')
        if user is None:
            return {'error': '内部错误:缺少用户上下文'}

        name = (tool_input or {}).get('name', '').strip()
        title = (tool_input or {}).get('title', '').strip()
        description = (tool_input or {}).get('description', '').strip()
        parameters = (tool_input or {}).get('parameters') or []
        queries = (tool_input or {}).get('queries') or []
        output_format = (tool_input or {}).get('output_format') or ''
        requested_scope = (tool_input or {}).get('scope', '').strip()

        # --- 1. 基础校验 ---
        if not name:
            return {'error': 'name 参数不能为空'}

        # 禁止创建与内置 Skill 同名或功能重复的
        _RESERVED = {'sales_activity_report', 'customer_overview', 'project_detail',
                     'pipeline_analysis', 'sales_weekly_review', 'weekly_summary'}
        if name in _RESERVED:
            return {'error': f'"{name}" 是内置 Skill，不允许重新创建。请直接使用 invoke_skill 调用。'}
        if not title:
            return {'error': 'title 参数不能为空'}
        if not queries:
            return {'error': 'queries 参数不能为空,至少需要一个查询步骤'}

        # 校验 name 格式:仅允许小写字母、数字、下划线
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            return {
                'error': (
                    f'name "{name}" 格式不合法。'
                    '仅允许小写字母开头,包含小写字母、数字、下划线。'
                ),
            }

        # 校验 queries 结构
        for i, q in enumerate(queries):
            sql = q.get('sql', '').strip()
            if not sql:
                return {'error': f'第 {i + 1} 个查询步骤的 sql 不能为空'}
            # 基础安全检查:只允许 SELECT 或 WITH 开头
            sql_upper = sql.upper().lstrip()
            if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
                return {
                    'error': (
                        f'第 {i + 1} 个查询步骤的 sql 必须以 SELECT 或 WITH 开头。'
                        '不允许 INSERT/UPDATE/DELETE 等修改操作。'
                    ),
                }

        # --- 2. 确定 scope ---
        is_admin = getattr(user, 'role', '') == 'admin'

        if is_admin:
            # admin 可以选择 scope,默认 global
            scope = requested_scope if requested_scope in ('global', 'personal') else 'global'
        else:
            # 非 admin 强制 personal
            scope = 'personal'
            if requested_scope == 'global':
                logger.info(
                    f'[CLI Agent] 用户 {user.id} 请求 global scope 但非 admin,降级为 personal'
                )

        # --- 3. 查找是否已有同名 Skill ---
        try:
            from app.models.cli_skill import CliSkill
            from app import db

            existing = CliSkill.query.filter_by(name=name).first()
        except Exception as e:
            logger.exception('[CLI Agent] save_skill 查询已有技能异常')
            return {'error': f'查询已有技能失败: {e}'}

        if existing:
            # --- 更新已有 Skill ---
            # 权限检查:只有创建者或 admin 可以更新
            if existing.created_by != user.id and not is_admin:
                return {
                    'error': (
                        f'技能 "{name}" 已存在且由其他用户创建,您没有权限修改。'
                    ),
                }

            existing.title = title
            existing.description = description or existing.description
            existing.parameters = parameters
            existing.queries = queries
            existing.output_format = output_format or existing.output_format
            existing.scope = scope
            existing.updated_at = datetime.utcnow()

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.exception(f'[CLI Agent] save_skill 更新技能 {name} 失败')
                return {'error': f'更新技能失败: {e}'}

            logger.info(f'[CLI Agent] save_skill 更新技能: {name} (id={existing.id})')
            return {
                'action': 'updated',
                'skill_id': existing.id,
                'skill_name': name,
                'title': title,
                'scope': scope,
                'parameter_count': len(parameters),
                'query_count': len(queries),
                'message': f'技能 "{title}" (name={name}) 已更新。',
            }

        else:
            # --- 创建新 Skill ---
            new_skill = CliSkill(
                name=name,
                title=title,
                description=description or title,
                parameters=parameters,
                queries=queries,
                output_format=output_format or None,
                scope=scope,
                is_active=True,
                created_by=user.id,
            )

            try:
                db.session.add(new_skill)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.exception(f'[CLI Agent] save_skill 创建技能 {name} 失败')
                return {'error': f'创建技能失败: {e}'}

            logger.info(
                f'[CLI Agent] save_skill 创建技能: {name} '
                f'(id={new_skill.id}, scope={scope})'
            )
            return {
                'action': 'created',
                'skill_id': new_skill.id,
                'skill_name': name,
                'title': title,
                'scope': scope,
                'parameter_count': len(parameters),
                'query_count': len(queries),
                'message': f'技能 "{title}" (name={name}) 已创建,scope={scope}。',
            }
