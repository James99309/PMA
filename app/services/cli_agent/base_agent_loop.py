# -*- coding: utf-8 -*-
"""
BaseAgentLoop — chat_agent 和 cli_agent 共享的基类。

只提取两端真正相同的逻辑：
  - __init__ 公共参数（user, llm, tools）
  - _run_tool()：执行单个工具，统一 try/except + is_error 判断
  - _emit_download()：检测 download_url 并生成下载事件

各子类差异（事件协议、历史加载、持久化）保留在子类实现。
"""
from __future__ import annotations

import logging
from typing import Any, Iterator

from app.services.cli_agent.llm_client import BaseLLMClient, get_default_client
from app.services.cli_agent.tools import ToolRegistry

logger = logging.getLogger(__name__)


class BaseAgentLoop:
    # 单轮 run 内最多缓存几条查询结果，供 export_to_excel 等下游工具按引用使用。
    # 旧的会被挤出，避免子进程数据文件无限膨胀。
    _MAX_CACHED_QUERY_RESULTS = 10

    def __init__(
        self,
        user,
        llm_client: BaseLLMClient | None = None,
        tools: ToolRegistry | None = None,
    ):
        self.user = user
        self.llm = llm_client or get_default_client()
        self.tools = tools  # 子类负责在 __init__ 里赋默认值
        # 本轮 run 期间收集的 query_pma_database 结果，按时间顺序追加。
        # 让 export_to_excel 这类工具直接引用,无需 AI 把数据原样回灌到 tool_use.input。
        self._query_results: list[dict] = []

    def _build_tool_context(self) -> dict:
        """构造传给工具 execute() 的 context dict。子类可扩展。"""
        return {'user': self.user, 'query_results': self._query_results}

    def _run_tool(self, tu: dict) -> tuple[dict, bool]:
        """执行单个工具，返回 (output, is_error)。"""
        try:
            tool = self.tools.get(tu['name'])
            if tool is None:
                return {'error': f'未知工具: {tu["name"]}'}, True
            output = tool.execute(tu['input'], self._build_tool_context())
            is_error = isinstance(output, dict) and 'error' in output
            if not is_error and tu['name'] == 'query_pma_database':
                self._cache_query_result(tu.get('input') or {}, output)
            return output, is_error
        except Exception as e:
            logger.exception(f'[Agent] 工具 {tu["name"]} 执行异常')
            return {'error': f'工具执行异常: {e}'}, True

    def _cache_query_result(self, tool_input: dict, output: dict) -> None:
        """把成功的 query_pma_database 结果缓存到本轮 run 的内存里。"""
        if not isinstance(output, dict):
            return
        columns = output.get('columns')
        rows = output.get('rows')
        if not columns or rows is None:
            return
        self._query_results.append({
            'sql': (tool_input.get('sql') or '').strip(),
            'columns': list(columns),
            'rows': list(rows),
            'row_count': output.get('row_count', len(rows)),
            'truncated': bool(output.get('truncated')),
            'original_row_count': output.get('original_row_count'),
        })
        # 限制缓存大小
        if len(self._query_results) > self._MAX_CACHED_QUERY_RESULTS:
            self._query_results = self._query_results[-self._MAX_CACHED_QUERY_RESULTS:]

    def _download_event(self, output: dict) -> dict | None:
        """若工具输出包含 download_url，返回 download 事件 dict，否则 None。"""
        if isinstance(output, dict) and output.get('download_url'):
            return {
                'type': 'download',
                'filename': output.get('filename', '导出文件'),
                'download_url': output['download_url'],
            }
        return None

    def _auto_tabular_artifact(self, tool_name: str, output: dict, is_error: bool) -> list[dict]:
        """若工具输出含 columns/rows，自动生成 table artifact 事件。

        invoke_skill 由 _strip_artifacts 处理（SkillEngine 已生成 artifacts 字段），此处跳过。
        """
        if tool_name == 'invoke_skill' or is_error or not isinstance(output, dict):
            return []
        columns = output.get('columns', [])
        rows = output.get('rows', [])
        if not columns or len(rows) < 2:
            return []
        try:
            from app.services.cli_agent.skill_engine import build_table_artifact
            art = build_table_artifact(f'查询结果（{len(rows)} 条）', columns, rows)
            if art:
                return [{'type': 'artifact', 'title': art['title'], 'html': art['html']}]
        except Exception:
            logger.warning('[Agent] 自动生成 tabular artifact 失败', exc_info=True)
        return []

    def _strip_artifacts(self, tool_name: str, output: dict, is_error: bool) -> tuple[dict, list[dict]]:
        """invoke_skill 专用：提取 artifacts 事件列表，返回剥离后的 llm_output。

        两端（chat/CLI）完全相同的逻辑，统一放在基类。
        Returns:
            (llm_output, artifact_events)  — llm_output 不含 artifacts 字段
        """
        artifact_events: list[dict] = []
        if tool_name != 'invoke_skill' or is_error or not isinstance(output, dict):
            return output, artifact_events

        for art in (output.get('artifacts') or []):
            artifact_events.append({
                'type': 'artifact',
                'title': art.get('title', ''),
                'html': art.get('html', ''),
            })

        llm_output = {k: v for k, v in output.items() if k != 'artifacts'} if 'artifacts' in output else output
        return llm_output, artifact_events
