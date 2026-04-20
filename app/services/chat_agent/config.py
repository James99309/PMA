# -*- coding: utf-8 -*-
"""
Chat Agent 上下文预算配置。

chat 场景与 CLI 相比的区别:
    - ChatMessage 表只存文本,不存 tool_use/tool_result 块
    - 跨轮 tool 轨迹天然丢失,历史占用远低于 CLI
    - 单次 run 内的 tool 循环最多 6 轮 (_MAX_TOOL_ROUNDS_PER_RUN)
    - 每轮 tool result 硬上限 CLI_TOOL_RESULT_MAX_TOKENS=8000 tokens
      (复用 cli_agent/config 里的常量,chat 的 query_pma_database 也用它)

预算估算:
    - 分级 schema 前缀 ~4.5k + 角色规则 ~1.5k + 动态段 ~1k = 7k 静态
    - 一轮富查询工具结果可达 8k,6 轮上限 ~48k
    - 历史文本 ~8-15k
    下限约 60k,warn 设 70k 给用户足够空间;reject 维持 120k。
"""

CHAT_CONTEXT_WARN = 70_000
"""警告阈值。达到时前端状态栏显示黄色,done 事件附 context_warning=True,允许继续。"""

CHAT_CONTEXT_REJECT = 120_000
"""硬上限。达到时阻断下一轮调用,前端显示 context_exhausted,引导用户开新对话。"""
