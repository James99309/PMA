# -*- coding: utf-8 -*-
"""describe_table 工具:按需返回某张表的字段详情。

配合 table_catalog 的分级 schema 使用:
- Tier 1 字段已在 system prompt 里列全,调 describe_table 也可获取详情
- Tier 2 字段未列在 prompt,LLM 需要字段时必须调此工具
- Tier 3 直接拒绝

权限双层:
1) 白名单: 必须在 Tier 1 ∪ Tier 2 内;Tier 3 或完全未知的表直接拒
2) CLI 模块权限: 必须能通过 cli_table_modules + has_cli_permission 检查
   (与 query_pma_database 的表级门禁一致)
"""
from __future__ import annotations

import logging
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)


class DescribeTableTool(BaseTool):
    name = 'describe_table'
    description = (
        '查询某张 PMA 数据库表的字段详情(字段名、类型、是否主键/外键)。\n'
        '- 适用场景:system prompt 中 Tier 2 表没有列字段,写 SQL 前先用此工具拿字段。\n'
        '- 参数 table_name 必须是 Tier 1 或 Tier 2 目录中的表名。\n'
        '- 返回 JSON,含 table、description、columns(含 pk/fk/type);\n'
        '  无权限或表不可见时返回 error 字段。\n'
        '- Tier 3 基础设施表(alembic_version, chat_messages 等)会被拒绝。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'table_name': {
                'type': 'string',
                'description': '要查询的表名(小写,例如 approval_instance)',
            },
        },
        'required': ['table_name'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        table = (tool_input or {}).get('table_name', '').strip().lower()
        user = context.get('user')

        if not table:
            return {'error': 'table_name 参数不能为空'}
        if user is None:
            return {'error': '内部错误:缺少用户上下文'}

        from app.services.cli_agent.table_catalog import (
            is_table_visible,
            is_table_blocked,
            get_table_description,
            _reflect_columns_with_types,
        )

        # 1) Tier 3 硬屏蔽
        if is_table_blocked(table):
            return {'error': f'表 {table} 属于系统基础设施,不对 CLI 查询开放'}

        # 2) 不在 Tier 1/2 目录
        if not is_table_visible(table):
            return {'error': f'未知表 {table},请从 Tier 1/Tier 2 目录中选择'}

        # 3) CLI 模块权限(与 query_pma_database 一致)
        from app.services.cli_agent.table_registry import check_table_access
        access_error = check_table_access(user, [table])
        if access_error:
            user_name = getattr(user, 'real_name', None) or getattr(user, 'username', '?')
            logger.info(f'[describe_table] 权限拒绝 user={user_name} table={table}: {access_error}')
            return {'error': access_error}

        # 4) 反射字段
        columns = _reflect_columns_with_types(table)
        if not columns:
            return {'error': f'表 {table} 反射失败,可能不存在或连接异常'}

        return {
            'table': table,
            'description': get_table_description(table),
            'columns': columns,
            'column_count': len(columns),
        }
