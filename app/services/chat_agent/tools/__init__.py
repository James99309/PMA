# -*- coding: utf-8 -*-
"""
Chat Agent 工具注册表

所有工具均复用 cli_agent/tools/ 的统一实现，通过构造参数 query_fn
传入 execute_chat_safe_query（前端权限模型），无需维护 chat 专用工具文件。

工具注册说明:
    - query_pma_database: 传入 execute_chat_safe_query（前端权限）
    - invoke_skill: 传入 execute_chat_safe_query（前端权限）
    - memory 三件套: 与 CLI 共享同一张 cli_memories 表
    - query_wiki: Chat 独有，公司内部知识库问答
    - web_search: 有 TAVILY_API_KEY 环境变量时启用
    - export_to_word / export_to_excel / export_quotation_to_excel: 直接复用
    - describe_table: 配合 Tier 2 表按需查询字段
"""
from __future__ import annotations

import os

from app.services.cli_agent.tools import BaseTool, ToolRegistry


_chat_default_registry: ToolRegistry | None = None


def get_chat_default_registry() -> ToolRegistry:
    """返回聊天场景专用的 ToolRegistry 单例（懒加载）"""
    global _chat_default_registry
    if _chat_default_registry is None:
        _chat_default_registry = ToolRegistry()

        from app.services.chat_db_query import execute_chat_safe_query
        from app.services.cli_agent.tools.query_pma_database import QueryPmaDatabaseTool
        _chat_default_registry.register(QueryPmaDatabaseTool(query_fn=execute_chat_safe_query))

        # invoke_skill（使用前端权限模型）
        try:
            from app.services.cli_agent.tools.invoke_skill import InvokeSkillTool
            _chat_default_registry.register(InvokeSkillTool(query_fn=execute_chat_safe_query))
        except Exception:
            pass

        # memory 工具（与 CLI agent 共享 cli_memories 表）
        try:
            from app.services.cli_agent.tools.save_memory import SaveMemoryTool
            from app.services.cli_agent.tools.recall_memory import RecallMemoryTool
            from app.services.cli_agent.tools.delete_memory import DeleteMemoryTool
            _chat_default_registry.register(SaveMemoryTool())
            _chat_default_registry.register(RecallMemoryTool())
            _chat_default_registry.register(DeleteMemoryTool())
        except Exception:
            pass

        # wiki 知识库问答（复用 wiki querier）
        try:
            from app.services.chat_agent.tools.query_wiki import QueryWikiTool
            _chat_default_registry.register(QueryWikiTool())
        except Exception:
            pass

        # web_search（有 TAVILY_API_KEY 才注册）
        if os.environ.get('TAVILY_API_KEY', '').strip():
            try:
                from app.services.cli_agent.tools.web_search import WebSearchTool
                _chat_default_registry.register(WebSearchTool())
            except Exception:
                pass

        # export_to_word（无条件注册，工具内部已有 python-docx 主路径 + pandoc 兜底）
        try:
            from app.services.cli_agent.tools.export_to_word import ExportToWordTool
            _chat_default_registry.register(ExportToWordTool())
        except Exception:
            pass

        # export_to_excel（openpyxl，含 PMA 样式库）
        try:
            from app.services.cli_agent.tools.export_to_excel import ExportToExcelTool
            _chat_default_registry.register(ExportToExcelTool())
        except Exception:
            pass

        # export_quotation_to_excel（按模板格式导出报价单）
        try:
            from app.services.cli_agent.tools.export_quotation_to_excel import ExportQuotationToExcelTool
            _chat_default_registry.register(ExportQuotationToExcelTool())
        except Exception:
            pass

        # describe_table（配合 Tier 2 按需查询表的字段）
        try:
            from app.services.cli_agent.tools.describe_table import DescribeTableTool
            _chat_default_registry.register(DescribeTableTool())
        except Exception:
            pass

    return _chat_default_registry


__all__ = ['BaseTool', 'ToolRegistry', 'get_chat_default_registry']
