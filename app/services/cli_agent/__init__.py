# -*- coding: utf-8 -*-
"""
PMA CLI Agent 模块

提供嵌入在 PMA 系统中的 Web 伪终端查询界面,让用户用自然语言查询业务数据。

架构:
    浏览器 (xterm.js) → PMA Flask → cli_agent (本模块) → Claude API
                                      ↓
                                   复用 PMA 内部函数
                                   (chat_db_query, 权限, schema)

设计文档: docs/plans/2026-04-05-pma-cli-agent-design.md
归因: 本模块的上下文管理策略参考自 ultraworkers/claw-code (MIT)
     详见 THIRD_PARTY_NOTICES.md
"""
