# -*- coding: utf-8 -*-
"""
CLI Agent 的工具注册表

每个工具实现 BaseTool 接口。Agent Loop 从 ToolRegistry 取所有工具定义,
传给 LLM;LLM 发起 tool_use 时,Registry 按 name 分发执行。

已注册的工具:
    - query_pma_database: SQL 只读查询(v1)
    - invoke_skill: 调用预定义的 CliSkill 技能
    - save_skill: 创建/更新 CliSkill 定义
    - web_search: 公网搜索(需 TAVILY_API_KEY)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """所有 CLI Agent 工具的基类"""

    name: str = ''
    description: str = ''
    input_schema: dict = {}

    @abstractmethod
    def execute(self, tool_input: dict, context: dict) -> Any:
        """执行工具。

        Args:
            tool_input: LLM 传入的参数(符合 input_schema)。
            context: 执行上下文,至少包含 {'user': User 对象}。

        Returns:
            任意可 JSON 序列化的对象,会被包装成 tool_result 块。
        """
        ...

    def to_anthropic_schema(self, enable_cache: bool = False) -> dict:
        """转成 Anthropic API tools 参数要求的 dict 格式"""
        schema = {
            'name': self.name,
            'description': self.description,
            'input_schema': self.input_schema,
        }
        if enable_cache:
            schema['cache_control'] = {'type': 'ephemeral'}
        return schema


class ToolRegistry:
    """工具注册表。单例通过 get_default_registry() 获取。"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not tool.name:
            raise ValueError('工具必须有 name')
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all(self) -> list[BaseTool]:
        return list(self._tools.values())

    def to_anthropic_tools(self, enable_cache_on_last: bool = True) -> list[dict]:
        """输出 Anthropic API tools 参数。

        按推荐做法,只在列表的最后一项挂 cache_control,
        这样整个 tools 定义作为一个缓存段。
        """
        tools = self.all()
        result = [t.to_anthropic_schema(enable_cache=False) for t in tools]
        if enable_cache_on_last and result:
            result[-1]['cache_control'] = {'type': 'ephemeral'}
        return result


_default_registry: ToolRegistry | None = None


def get_default_registry() -> ToolRegistry:
    """获取默认的 Tool Registry 单例。懒加载,首次调用时注册所有工具。"""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
        # 注册 v1 工具
        from app.services.cli_agent.tools.query_pma_database import QueryPmaDatabaseTool
        from app.services.cli_agent.tools.describe_table import DescribeTableTool
        _default_registry.register(QueryPmaDatabaseTool())
        _default_registry.register(DescribeTableTool())

        # 注册 Skill 工具(invoke + save)
        from app.services.cli_agent.tools.invoke_skill import InvokeSkillTool
        from app.services.cli_agent.tools.save_skill import SaveSkillTool
        _default_registry.register(InvokeSkillTool())
        _default_registry.register(SaveSkillTool())

        # 注册记忆工具
        from app.services.cli_agent.tools.recall_memory import RecallMemoryTool
        from app.services.cli_agent.tools.save_memory import SaveMemoryTool
        from app.services.cli_agent.tools.delete_memory import DeleteMemoryTool
        _default_registry.register(RecallMemoryTool())
        _default_registry.register(SaveMemoryTool())
        _default_registry.register(DeleteMemoryTool())

        # 注册 export_to_word（pandoc 可用时）
        import shutil
        if shutil.which('pandoc'):
            from app.services.cli_agent.tools.export_to_word import ExportToWordTool
            _default_registry.register(ExportToWordTool())

        # 注册 web_search(只在配置了 TAVILY_API_KEY 时)
        import os
        if os.environ.get('TAVILY_API_KEY', '').strip():
            from app.services.cli_agent.tools.web_search import WebSearchTool
            _default_registry.register(WebSearchTool())

    return _default_registry
