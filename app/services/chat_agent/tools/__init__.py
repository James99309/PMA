# -*- coding: utf-8 -*-
"""
Chat Agent 工具注册表

相比 cli_agent 的工具集（query + skill + memory + web_search + export_to_word），
chat_agent 注册:

    - query_pma_database: 通过 execute_chat_safe_query 做前端权限过滤的 SQL 查询
    - save_memory / recall_memory / delete_memory:
          与 CLI agent 共享同一张 cli_memories 表,实现跨入口统一的用户画像
          （chat 里学到的"张奕是 HR 经理"在 CLI 终端也记得）
    - web_search: 有 TAVILY_API_KEY 环境变量时启用,用于查询公网信息
    - export_to_word: pandoc 可用时启用,用户可在聊天里说"导出Word"

不注册 skill 工具,聊天场景用户期望即时问答,不需要 CLI 那种技能沉淀。

工具注册说明:
    - invoke_skill: 调用 CliSkill 预定义业务技能，使用 execute_chat_safe_query（前端权限）
    - web_search: 有 TAVILY_API_KEY 环境变量时启用（与 CLI 统一用 .strip() 判断）
    - export_to_word: 无条件注册，工具内部已有 python-docx 主路径 + pandoc 兜底
    - describe_table: 配合 Tier 2 表按需查询字段，与 CLI 分级 schema 注入配合
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

        from app.services.chat_agent.tools.query_pma_database import (
            ChatQueryPmaDatabaseTool,
        )
        _chat_default_registry.register(ChatQueryPmaDatabaseTool())

        # invoke_skill（使用前端权限模型，无需 cli_permissions 配置）
        try:
            from app.services.chat_agent.tools.invoke_skill import ChatInvokeSkillTool
            _chat_default_registry.register(ChatInvokeSkillTool())
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
