# -*- coding: utf-8 -*-
"""Wiki 知识库服务模块

基于 Karpathy LLM Wiki 方案的知识库实现。

模块结构：
- paths.py      - 磁盘路径管理（raw/ 和 wiki/ 目录解析）
- storage.py    - Markdown 文章、原始文件、index/log 的 I/O
- claude_client.py  - Claude API 客户端（Phase 4 新增）
- prompts.py    - Ingest/Query/Lint 系统提示词（Phase 4 新增）
- compiler.py   - Ingest 编译服务（Phase 5 新增）
- querier.py    - Query 问答服务（Phase 6 新增）
- linter.py     - Lint 质检服务（Phase 7 新增）

参见 docs/plans/2026-04-09-wiki-knowledge-base.md。
"""
