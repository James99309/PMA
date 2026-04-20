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
    def __init__(
        self,
        user,
        llm_client: BaseLLMClient | None = None,
        tools: ToolRegistry | None = None,
    ):
        self.user = user
        self.llm = llm_client or get_default_client()
        self.tools = tools  # 子类负责在 __init__ 里赋默认值

    def _run_tool(self, tu: dict) -> tuple[dict, bool]:
        """执行单个工具，返回 (output, is_error)。"""
        try:
            tool = self.tools.get(tu['name'])
            if tool is None:
                return {'error': f'未知工具: {tu["name"]}'}, True
            output = tool.execute(tu['input'], {'user': self.user})
            is_error = isinstance(output, dict) and 'error' in output
            return output, is_error
        except Exception as e:
            logger.exception(f'[Agent] 工具 {tu["name"]} 执行异常')
            return {'error': f'工具执行异常: {e}'}, True

    def _download_event(self, output: dict) -> dict | None:
        """若工具输出包含 download_url，返回 download 事件 dict，否则 None。"""
        if isinstance(output, dict) and output.get('download_url'):
            return {
                'type': 'download',
                'filename': output.get('filename', '导出文件'),
                'download_url': output['download_url'],
            }
        return None

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
