# -*- coding: utf-8 -*-
"""
query_pma_database 工具:把 PMA 现有的 execute_safe_query() 包装成 Agent 工具。

与原 OpenClaw 路径(HTTP POST /chat/api/ai/db-query)不同,这里是**同进程函数调用**,
零网络开销,权限上下文通过闭包传入。

结果处理:超过 CLI_TOOL_RESULT_MAX_TOKENS 时截断并告知 LLM 收紧范围。
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


class QueryPmaDatabaseTool(BaseTool):
    name = 'query_pma_database'
    description = (
        '使用 SQL 查询 PMA 业务数据库(只读)。\n'
        '- 适用场景:查询客户、项目、报价、订单、联系人、产品、费用、用户等业务数据。\n'
        '- 参数 sql 必须是 SELECT 或 WITH 开头的一条语句。\n'
        '- 系统会自动按当前用户权限注入 WHERE 过滤,并强制 LIMIT 行数。\n'
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

    def __init__(self, query_fn=None):
        """
        query_fn: 可选查询函数，默认 execute_safe_query（CLI 权限）。
                  Chat 场景传入 execute_chat_safe_query（前端权限模型）。
        """
        self._query_fn = query_fn

    def execute(self, tool_input: dict, context: dict) -> Any:
        sql = (tool_input or {}).get('sql', '').strip()
        user = context.get('user')

        if not sql:
            return {'error': 'sql 参数不能为空'}
        if user is None:
            return {'error': '内部错误:缺少用户上下文'}

        try:
            if self._query_fn is not None:
                _query = self._query_fn
            else:
                from app.services.chat_db_query import execute_safe_query
                _query = execute_safe_query
            result = _query(sql, user)
        except Exception as e:
            logger.exception('[Agent] query_pma_database 执行异常')
            return {'error': '查询执行失败，请检查查询条件后重试。'}

        if not result.get('success'):
            raw_err = result.get('error', '查询失败')
            if '权限' in raw_err or '没有' in raw_err:
                return {'error': raw_err}
            logger.warning(f'[Agent] query_pma_database 失败: {raw_err}')
            return {'error': '查询失败，请换个方式提问或缩小查询范围。'}

        # 成功结果 → 检查大小,过大截断
        rows = result.get('rows', [])
        columns = result.get('columns', [])
        row_count = result.get('row_count', len(rows))

        # 粗估 token 数:序列化后字节数 / 3
        serialized = json.dumps({'columns': columns, 'rows': rows}, ensure_ascii=False, default=str)
        estimated_tokens = len(serialized) // 3

        truncated = False
        original_row_count = row_count
        if estimated_tokens > CLI_TOOL_RESULT_MAX_TOKENS and rows:
            # 二分收敛到预算以内
            kept = len(rows)
            while kept > 1:
                kept //= 2
                trial = json.dumps({'columns': columns, 'rows': rows[:kept]},
                                   ensure_ascii=False, default=str)
                if len(trial) // 3 <= CLI_TOOL_RESULT_MAX_TOKENS:
                    break
            rows = rows[:kept]
            truncated = True
            logger.info(
                f'[Agent] tool result 截断: {original_row_count} → {kept} 行'
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
