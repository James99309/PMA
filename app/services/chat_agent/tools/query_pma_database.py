# -*- coding: utf-8 -*-
"""
Chat 版 query_pma_database 工具。

与 cli_agent 版唯一的差异:**调 execute_chat_safe_query 而不是 execute_safe_query**。
execute_chat_safe_query 按前端权限(access_control.get_viewable_data)过滤数据,
包含共享、归属关系、联系人授权等全量权限语义;
而 execute_safe_query 走 cli_agent 的独立 cli_table_modules 白名单 + owner 级过滤。

其他逻辑(JSON schema、错误脱敏、大结果截断)完全一致。
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.services.cli_agent.tools import BaseTool
from app.services.cli_agent.config import (
    CLI_QUERY_DEFAULT_LIMIT,
    CLI_TOOL_RESULT_MAX_TOKENS,
)

logger = logging.getLogger(__name__)


class ChatQueryPmaDatabaseTool(BaseTool):
    name = 'query_pma_database'
    description = (
        '使用 SQL 查询 PMA 业务数据库(只读)。\n'
        '- 适用场景:查询客户、项目、报价、订单、联系人、产品、费用、用户等业务数据。\n'
        '- 参数 sql 必须是 SELECT 或 WITH 开头的一条语句。\n'
        '- 系统会按当前用户的前端权限(含共享、归属关系、联系人授权)自动注入 WHERE 过滤,并强制 LIMIT 行数。\n'
        '- 返回 JSON,含 columns、rows、row_count 字段;如果查询失败,含 error 字段。\n'
        f'- 单条查询默认 LIMIT {CLI_QUERY_DEFAULT_LIMIT},超大结果会被截断,此时请加严 WHERE。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'sql': {
                'type': 'string',
                'description': '要执行的 SELECT 或 WITH 开头的只读 SQL 语句',
            },
        },
        'required': ['sql'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        sql = (tool_input or {}).get('sql', '').strip()
        user = context.get('user')

        if not sql:
            return {'error': 'sql 参数不能为空'}
        if user is None:
            return {'error': '内部错误:缺少用户上下文'}

        try:
            from app.services.chat_db_query import execute_chat_safe_query
            result = execute_chat_safe_query(sql, user)
        except Exception as e:
            logger.exception('[Chat Agent] query_pma_database 执行异常')
            return {'error': '查询执行失败,请检查查询条件后重试。'}

        if not result.get('success'):
            raw_err = result.get('error', '查询失败')
            if '权限' in raw_err or '没有' in raw_err:
                return {'error': raw_err}
            logger.warning(f'[Chat Agent] query_pma_database 失败: {raw_err}')
            return {'error': '查询失败,请换个方式提问或缩小查询范围。'}

        rows = result.get('rows', [])
        columns = result.get('columns', [])
        row_count = result.get('row_count', len(rows))

        serialized = json.dumps(
            {'columns': columns, 'rows': rows},
            ensure_ascii=False, default=str,
        )
        estimated_tokens = len(serialized) // 3

        truncated = False
        original_row_count = row_count
        if estimated_tokens > CLI_TOOL_RESULT_MAX_TOKENS and rows:
            kept = len(rows)
            while kept > 1:
                kept //= 2
                trial = json.dumps(
                    {'columns': columns, 'rows': rows[:kept]},
                    ensure_ascii=False, default=str,
                )
                if len(trial) // 3 <= CLI_TOOL_RESULT_MAX_TOKENS:
                    break
            rows = rows[:kept]
            truncated = True
            logger.info(
                f'[Chat Agent] tool result 截断: {original_row_count} → {kept} 行'
            )

        output: dict = {
            'columns': columns,
            'rows': rows,
            'row_count': len(rows),
        }
        if truncated:
            output['truncated'] = True
            output['original_row_count'] = original_row_count
            output['hint'] = (
                f'结果过大已截断,原始 {original_row_count} 行,展示前 {len(rows)} 行。'
                f'如需完整数据请加严 WHERE 条件或降低 LIMIT。'
            )
        if result.get('hint'):
            output['server_hint'] = result['hint']

        return output
