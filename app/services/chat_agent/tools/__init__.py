# -*- coding: utf-8 -*-
"""
Chat Agent 工具注册表

相比 cli_agent 的工具集(query + skill + memory + web_search + export_to_word),
chat_agent 只注册与聊天场景相关的核心工具:

    - query_pma_database: 通过 execute_chat_safe_query 做前端权限过滤的 SQL 查询
    - export_to_word:     pandoc 可用时注册,用户可在聊天里说"导出Word"

不注册 skill/memory 类工具,因为聊天场景用户期望即时问答,
不需要 CLI 那种技能沉淀和长期记忆。
"""
from __future__ import annotations

from app.services.cli_agent.tools import BaseTool, ToolRegistry


_chat_default_registry: ToolRegistry | None = None


def get_chat_default_registry() -> ToolRegistry:
    """返回聊天场景专用的 ToolRegistry 单例(懒加载)"""
    global _chat_default_registry
    if _chat_default_registry is None:
        _chat_default_registry = ToolRegistry()

        from app.services.chat_agent.tools.query_pma_database import (
            ChatQueryPmaDatabaseTool,
        )
        _chat_default_registry.register(ChatQueryPmaDatabaseTool())

        # pandoc 可用时注册 export_to_word(复用 cli_agent 的实现)
        import shutil
        if shutil.which('pandoc'):
            try:
                from app.services.cli_agent.tools.export_to_word import ExportToWordTool
                _chat_default_registry.register(ExportToWordTool())
            except Exception:
                pass

    return _chat_default_registry


__all__ = ['BaseTool', 'ToolRegistry', 'get_chat_default_registry']
