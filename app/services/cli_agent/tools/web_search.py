# -*- coding: utf-8 -*-
"""
web_search 工具:Anthropic 内置 server-side web_search

工作方式:
    - schema 返回 {type:'web_search_20250305', name:'web_search', max_uses}
    - Anthropic 服务端自己执行搜索,客户端收到 server_tool_use + web_search_tool_result 事件
    - execute() 永远不会被调用(server tool 不需要客户端执行)
    - 用量计入 OAuth 订阅 quota,无 Tavily 依赖

用途:
    补充 PMA 数据库里没有的公开信息,比如:
    - 客户公司的最新动态、注册地、行业背景
    - 项目所在地的政策、物流、展会
    - 行业趋势、竞品情报、标准规范
    - 事实性查询(天气、新闻、汇率等)

不要用于:
    - PMA 内部业务数据查询(这些请用 query_pma_database)
    - 闲聊、笑话、情感、创作(CLI 角色不做这些)

注册:在 tools/__init__.py 的 get_default_registry() 里默认加入
"""
from __future__ import annotations

import logging
import os
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)


# Anthropic web_search 服务端工具版本(2025-03-05)
_WEB_SEARCH_TOOL_TYPE = 'web_search_20250305'

# 单次会话最多搜索次数(防止 agent loop 失控烧 quota)
_DEFAULT_MAX_USES = int(os.environ.get('WEB_SEARCH_MAX_USES', '5'))


class WebSearchTool(BaseTool):
    name = 'web_search'
    description = (
        '搜索公网公开信息(由 Anthropic 服务端执行)。用于查询 PMA 数据库里没有的公开数据,'
        '例如:客户公司的最新动态/注册地/行业背景、项目所在地政策、'
        '竞品信息、行业标准、事实性问题(天气/新闻/汇率/地理等)。'
    )
    # Anthropic server tool 不需要客户端 input_schema,这里只为兼容 BaseTool 接口
    input_schema: dict = {}

    def to_anthropic_schema(self, enable_cache: bool = False) -> dict:
        """覆盖 BaseTool 的默认实现,返回 Anthropic server tool 规范的 schema。

        与普通客户端工具的区别:
            普通工具:{name, description, input_schema}
            server  工具:{type, name, max_uses}
        """
        schema: dict = {
            'type': _WEB_SEARCH_TOOL_TYPE,
            'name': self.name,
            'max_uses': _DEFAULT_MAX_USES,
        }
        if enable_cache:
            schema['cache_control'] = {'type': 'ephemeral'}
        return schema

    def execute(self, tool_input: dict, context: dict) -> Any:
        """理论上永远不会被调用——Anthropic 服务端执行搜索后通过
        server_tool_use / web_search_tool_result 事件返回结果,
        客户端 agent loop 不会收到 tool_use 事件,自然不会路由到 execute()。

        如果意外被调用,返回明确错误避免静默 fallback。
        """
        logger.error(
            '[CLI Agent] web_search.execute() 被调用了,这不应该发生。'
            'Anthropic server tool 由服务端执行,客户端不应路由到这里。'
        )
        return {
            'error': (
                'web_search 是 Anthropic 服务端工具,不应在客户端执行。'
                '请检查 _iter_stream_events 是否错误地把 server_tool_use yield 成了 tool_use。'
            )
        }
