# -*- coding: utf-8 -*-
"""
CLI Agent 配置常量

所有上下文管理阈值、会话限制、UI 边界值统一在这里维护。

这些值的选择基于以下事实:
1. Claude 3.5 Sonnet 上下文窗口 200,000 tokens
2. PMA 查询结果有 LIMIT 100 硬边界,单次 tool result 可控
3. 中文 token 密度约为英文的 4 倍(1 汉字 ≈ 1~2 token)
4. Anthropic Prompt Caching 使长稳定前缀成本趋近于零
5. PMA 查询场景会话较短(5~20 轮),远短于通用编码 agent

设计理由详见 docs/plans/2026-04-05-pma-cli-agent-design.md 第 4.4 节。
"""

# ─── 上下文阈值 ────────────────────────────────────────────────────────
CLI_CONTEXT_MAX_TOKENS = 180_000
"""硬上限,预留 20k 给 system prompt + 当前输入 + 模型输出"""

CLI_CONTEXT_SOFT_COMPACT = 40_000
"""软提示阈值。超过后状态条显示使用量,但不做任何压缩"""

CLI_CONTEXT_WARN = 110_000
"""警告阈值。Tab 数字变黄,AI 回答末尾附加"会话已较长"提示。
2026-05-13: 120K → 110K, 配合放大后的 LLM_MAX_TOKENS 同步下移。"""

CLI_CONTEXT_HARD_COMPACT = 150_000
"""强制规则压缩阈值。达到时自动触发 compaction。
2026-05-13: 160K → 150K, 给压缩留时间, 避免在 REJECT 时一刀切。"""

CLI_CONTEXT_REJECT = 180_000
"""拒绝阈值。达到时锁定输入框,强制用户 /new。
2026-05-13: 190K → 180K, 给放大到 16K 的 LLM 输出留余量
(180K context + 16K output = 196K, 安全留 4K 给 system prompt 等)。"""

# ─── 消息保留策略 ──────────────────────────────────────────────────────
CLI_KEEP_RECENT_MESSAGES = 8
"""压缩时保留的最新消息条数。4 对用户-AI 回合,查询场景追问链的经验值"""

CLI_COMPACTION_SUMMARY_MAX_TOKENS = 5_000
"""压缩后的摘要块目标大小"""

# ─── 工具层限制 ────────────────────────────────────────────────────────
CLI_QUERY_DEFAULT_LIMIT = 100
"""query_pma_database 工具的默认 LIMIT,AI 可覆盖但不建议 > 500"""

CLI_TOOL_RESULT_MAX_TOKENS = 24_000
"""单条 tool result 进入 context 的最大 token 数。超过会强制截断并提示 AI 缩小查询范围。
典型业务列表 ≈ 80 tokens/行 (15 列 × 60 字)，24K 容纳 ~300 行；再多用户应该筛选/分页。
2026-05-13: 8K → 24K, 原值导致 300+ 行查询被截到 150 行，AI 看到的"全量数据"不全。"""

CLI_LLM_MAX_TOKENS = 16_384
"""LLM 单轮最大输出 token 数。Sonnet 4.6 / Opus 4.7 上限 64K, 这里取保守 16K。
2026-05-13: 8192 → 16384。export 工具 (现在已用 query_results 引用而非内联) python_code
≈ 1-2K, 加 AI 中文文案 1-2K, 16K 留 4 倍冗余。"""

# ─── 会话生命周期 ──────────────────────────────────────────────────────
CLI_SESSION_ARCHIVE_HOURS = 48
"""非活跃 session 自动归档的小时数。归档不删除数据,通过 /history 可找回"""

CLI_SESSION_MAX_TURNS = 100
"""单个 session 的硬性轮次上限。防止失控"""

# ─── UI 限制 ───────────────────────────────────────────────────────────
CLI_MAX_ACTIVE_TABS = 8
"""同一用户同时打开的 tab 数上限"""

# ─── Token 估算 ────────────────────────────────────────────────────────
CLI_TOKEN_CALIBRATION_INTERVAL = 3
"""每 N 轮调用一次 anthropic.count_tokens() 做精确校准,其余轮次用离线估算"""

# ─── Prompt Caching ────────────────────────────────────────────────────
CLI_PROMPT_CACHE_ENABLED = True
"""是否对系统提示启用 Anthropic ephemeral cache_control"""

# ─── 功能开关(feature flag)────────────────────────────────────────────
CLI_FEATURE_FLAG_ENV = 'ENABLE_CLI_AGENT'
"""环境变量名。设为 'true' 后 CLI 菜单项对所有用户可见,否则仅 admin 可见"""
