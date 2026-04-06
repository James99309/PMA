# PMA CLI Agent 设计方案

**日期**: 2026-04-05
**分支**: `feature/cli-agent`
**状态**: 设计锁定,骨架已建,待实现

## 1. 背景与动机

### 1.1 问题

PMA 目前为每一类查询需求都要设计专门的前端页面和筛选 UI,而用户真正的查询需求是**开放的、长尾的、不可穷举的**。例子:

- "上个月深圳华为项目的所有报价,按金额降序"
- "最近两周没进展的项目有哪些"
- "客户'海康威视'的联系人中谁是主要对接人"

这些问题可以用现有 UI 逐个拼凑查出来,但体验割裂,且 80% 的查询场景并没有对应的前端页面。

### 1.2 现有方案的不足

PMA 已有**右下悬浮聊天面板** (`app/templates/components/tw_chat_panel.html`),背后接 OpenClaw Gateway 提供 AI 能力。但存在以下问题:

1. **交互形态**仍然是聊天窗口,缺乏命令行的"工具感"和"专注感"
2. **Agent Loop 托管在 OpenClaw**,PMA 对模型选择、工具协议、上下文管理没有控制权
3. **可查询的表只有 7 张**(companies, projects, quotations, contacts, expenses, pricing_orders, tasks),扩展靠修改 `chat_db_query.py`
4. **多会话管理缺失**,用户无法同时开几个查询线程
5. **不支持专属的业务查询 Skill 体系**

### 1.3 目标

提供一个**嵌在 PMA 内、登录即用、像 Claude Code 一样的 Web 伪终端查询界面**,让所有授权用户可以用自然语言查询 PMA 业务数据,并为将来的 Skill 系统预留扩展点。

## 2. 架构决策

### 2.1 部署形态

**Web 伪终端**,即在浏览器里用 `xterm.js` 模拟终端 UI,嵌在 PMA 主站内。

- ✅ 零安装
- ✅ 自动复用 PMA session 认证
- ✅ LLM API Key 永远留在服务器
- ✅ 工具调用可直接 import PMA 内部函数,无跨进程开销
- ✅ 与现有 Chat Panel 彻底隔离,风险低

### 2.2 Agent Loop 位置

**PMA 后端新增独立模块,直连 LLM API,不经过 OpenClaw。**

原因:
1. OpenClaw 的能力中,PMA CLI 只需要其中很小一部分(LLM 调用 + function calling)
2. 现代 LLM API(Claude、DeepSeek)原生支持 tool use 和 streaming
3. 直连可享受 Anthropic Prompt Caching 的原生能力
4. 调试、升级、换模型都不依赖第三方网关

### 2.3 架构图

```
浏览器:
  GET /cli    → terminal.html (xterm.js)
       │
       │  WebSocket / SSE 流式
       ▼
PMA 后端 (新增,独立于现有 Chat + OpenClaw):
  app/views/cli.py                    Flask Blueprint (cli_bp)
       │
  app/services/cli_agent/
       ├── agent_loop.py              核心循环: LLM ↔ 工具 ↔ 对话
       ├── llm_client.py              Anthropic Python SDK 包装
       ├── conversation.py            消息存储 (ContentBlock + tool_use_id)
       ├── compaction.py              规则化压缩 (无 LLM 调用)
       ├── prompt_builder.py          系统提示组装 (静态段 + 动态段)
       ├── usage.py                   逐轮 token 追踪
       ├── config.py                  上下文阈值常量
       └── tools/
           └── query_pma_database.py  复用 app.services.chat_db_query
       │
       └──→ 调用 Claude API (Anthropic 原生 tool use 协议)
       │
       └──→ 调用 PMA 内部函数(同进程):
              app.services.chat_db_query.execute_safe_query()
              app.services.chat_db_query.get_db_schema()
              app.services.chat_db_query.get_permission_context()

PMA 后端 (完全不动):
  openclaw_provider.py + tw_chat_panel  ← 继续服务浏览器聊天面板
```

## 3. 代码组织边界

### 3.1 新建文件(全部隔离在 CLI 自己的目录)

```
app/services/cli_agent/
├── __init__.py
├── agent_loop.py
├── llm_client.py
├── conversation.py
├── compaction.py
├── prompt_builder.py
├── usage.py
├── config.py
├── THIRD_PARTY_NOTICES.md           ← MIT 归因(claw-code 参考)
└── tools/
    ├── __init__.py
    └── query_pma_database.py

app/models/
├── cli_session.py                    ← 新模型
└── user_cli_state.py                 ← 新模型

app/views/
└── cli.py                            ← 新 Blueprint

app/templates/cli/
├── terminal.html                     ← 继承 base.html
└── _partials/
    ├── tab_bar.html
    └── status_bar.html

app/static/js/cli/
├── terminal.js
├── tabs.js
├── websocket_client.js
└── markdown_renderer.js

app/static/css/cli/
└── terminal.css

migrations/versions/
└── xxxx_add_cli_agent_tables.py
```

### 3.2 仅两个最小侵入点(必须改现有文件)

| 文件 | 改动 |
|---|---|
| `app/templates/base.html` | 主菜单加一条 `智能终端` (~6 行) |
| `app/__init__.py` | 注册 `cli_bp` Blueprint (~2 行) |

### 3.3 绝对不碰

遵循 `CLAUDE.md` 的通用组件保护协议:

- `app/templates/macros/ui_helpers.html`
- `app/static/js/data-list.js`
- `app/static/js/filter-search.js`
- `app/static/css/style.css`
- `app/templates/_archived/` 任何文件
- `app/services/openclaw_provider.py`
- `app/services/chat_ai_service.py`
- `app/templates/components/tw_chat_panel.html`

## 4. 核心模块设计

### 4.1 数据模型

#### `cli_sessions` 表

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 主键 |
| `user_id` | Integer FK | PMA 用户 |
| `title` | String(120) | 自动生成或用户重命名 |
| `status` | Enum | `ACTIVE` / `CLOSED` / `ARCHIVED` |
| `messages` | JSONB | ContentBlock 数组 |
| `usage_total` | JSONB | 累计 `input_tokens` / `output_tokens` / `cache_read` / `cache_write` |
| `compaction_meta` | JSONB | 压缩次数、最近一次摘要 |
| `created_at` | DateTime | |
| `last_active_at` | DateTime | 自动归档判断依据 |

#### `user_cli_state` 表

| 字段 | 类型 | 说明 |
|---|---|---|
| `user_id` | Integer PK | 每用户一行 |
| `active_session_ids` | JSONB | 有序数组,标签栏里从左到右 |
| `current_session_id` | UUID | 当前聚焦的那个 |
| `ui_preferences` | JSONB | 字号、主题、快捷键配置 |
| `updated_at` | DateTime | |

### 4.2 ContentBlock 结构(移植自 `conversation.rs`)

一条消息 = `{role, blocks[], usage?}`,其中 `blocks` 每个是以下三种之一:

- `{type: "text", text: "..."}`
- `{type: "tool_use", id: "...", name: "...", input: {...}}`
- `{type: "tool_result", tool_use_id: "...", content: "...", is_error: false}`

`tool_use_id` 显式配对,满足 Anthropic API 要求 tool_use 与 tool_result 必须相邻的约束。

这个结构也是 Anthropic Python SDK 的原生消息格式,**零转换成本**。

### 4.3 系统提示结构(移植自 `prompt.rs` 的 DYNAMIC_BOUNDARY 模式)

```
[系统提示]
├─ 静态段(整个 session 不变,享受 prompt caching)
│   ├─ 角色定位与回复风格
│   ├─ 查询规则(必须用 query_pma_database, 禁止编造)
│   ├─ 数据库 schema (调用 get_db_schema())
│   ├─ 输出格式约定
│   └─ "记笔记"指令(从 Claude Code 抄的):
│        "对重要数据请在回复中复述,因旧工具结果可能被清理"
│
├── DYNAMIC_BOUNDARY ───
│
└─ 动态段(session 启动时生成一次,之后稳定)
    ├─ 用户身份(user_id, user_name, role)
    ├─ 权限上下文 (调用 get_permission_context(user))
    ├─ 当前环境(SP8D / OVS)
    └─ 当前日期
```

边界以上和以下都**在 session 内稳定**,两段都应挂 `cache_control: ephemeral`,享受 Anthropic Prompt Caching。

### 4.4 上下文阈值配置(`config.py`)

| 常量 | 值 | 说明 |
|---|---|---|
| `CLI_CONTEXT_MAX_TOKENS` | 180,000 | Claude 200k 窗口,留 20k 余量 |
| `CLI_CONTEXT_SOFT_COMPACT` | 40,000 | 超过时状态条开始提示 |
| `CLI_CONTEXT_WARN` | 120,000 | Tab 数字变黄,建议 /new |
| `CLI_CONTEXT_HARD_COMPACT` | 160,000 | 强制自动规则压缩 |
| `CLI_CONTEXT_REJECT` | 190,000 | 锁定输入,强制 /new |
| `CLI_KEEP_RECENT_MESSAGES` | 8 | 压缩时保留的最新消息数 |
| `CLI_QUERY_DEFAULT_LIMIT` | 100 | SQL 查询默认行数上限 |
| `CLI_TOOL_RESULT_MAX_TOKENS` | 8,000 | 单条 tool result 上限 |
| `CLI_COMPACTION_SUMMARY_MAX_TOKENS` | 5,000 | 压缩后摘要目标大小 |
| `CLI_SESSION_ARCHIVE_HOURS` | 48 | 非活跃自动归档 |
| `CLI_MAX_ACTIVE_TABS` | 8 | 标签栏上限 |

**为什么比 claw-code 宽松 4~10 倍**:
- claw-code 为**通用编码 agent**设计,tool 结果可能很大,会话可能很长,所以 10k 触发 / 4 条保留是激进的
- PMA CLI 的 tool 结果有 `LIMIT 100` 硬边界,会话更短,可以放宽
- Claude 200k 窗口 + Prompt Caching 让长上下文代价很低,过早压缩反而浪费缓存
- **中文 token 密度约为英文的 4 倍**(1 汉字 ≈ 1~2 token vs 1 英文词 ≈ 1.3 token),绝对数值要调大

### 4.5 规则化压缩策略(移植自 `compact.rs`)

**关键原则**: **不调 LLM**,纯规则从老消息抽取:

1. **触发条件**: 累计 token ≥ `HARD_COMPACT` AND 消息数 > `KEEP_RECENT_MESSAGES`
2. **保留范围**: 最近 `KEEP_RECENT_MESSAGES` 条原样不动
3. **压缩范围**: 除保留之外的所有老消息
4. **摘要提取**(PMA 业务化,替换 claw-code 的代码特征):
   - 消息计数(user / assistant / tool_result 各多少条)
   - 用过的工具名去重
   - 最近 3 条用户请求(截断 160 字符)
   - **提到的业务实体**:从 SQL 和文本里正则提取客户 ID、项目 ID、报价单号、金额范围
   - **涉及的表**:从 SQL 提取 `FROM xxx` 的表名列表
   - 时间线(每条 role + 80 字符截断)
5. **包装**: 拼成 Markdown,用 `<compacted_summary>…</compacted_summary>` 包裹
6. **注入位置**: 作为新的一条 `role=user, type=text` 消息,插到保留段开头
7. **叠加**: 若上一次压缩摘要仍在,合并成"之前压缩的 + 新压缩的"分段,不丢弃历史

### 4.6 Token 估算(对中文校正)

**claw-code 用 `字符数 ÷ 4 + 1`,对中文严重低估。PMA CLI 必须改。**

方案(按优先级):

1. **推荐**: 首选 `anthropic.count_tokens()` API(准确但有网络开销),每 3 轮调用一次做校准,其余用离线估算
2. **离线估算**: `汉字数 × 1.5 + 英文字符数 / 4 + JSON符号数 × 0.3`,对中文精度 ~±15%
3. **备选**: `tiktoken` 的 `cl100k_base` 编码,比纯字符除法准得多但仍非 Claude 原生

### 4.7 工具注册机制(为未来 Skill 预留扩展点)

即使 v1 只有一个工具 `query_pma_database`,也用 **ToolRegistry** 模式:

```python
# 概念示例
registry = ToolRegistry()
registry.register(QueryPmaDatabaseTool())
# 未来: registry.register(InvokeSkillTool())
# 未来: registry.register(ExportToExcelTool())
```

每个工具实现统一接口:`name`, `description`, `input_schema`, `execute(input, context)`。

## 5. UI 设计

### 5.1 入口位置

`app/templates/base.html` 主菜单(约第 300 行开始)新增一条:

```html
{% if config.get('ENABLE_CLI_AGENT') or current_user.is_admin %}
<li class="nav-item">
    <a class="nav-link text-sm py-2" href="{{ url_for('cli.terminal') }}">
        <i class="fas fa-terminal me-1"></i>{{ _('智能终端') }}
    </a>
</li>
{% endif %}
```

用 `ENABLE_CLI_AGENT` 环境变量做 feature flag,初期只对 admin 可见。

### 5.2 整体布局

```
┌──────────────────────────────────────────────────────────────┐
│  PMA 顶部 navbar                                  (保留)      │
├──────┬───────────────────────────────────────────────────────┤
│      │  ╭───────────────────────────────────────────────╮    │
│      │  │ ● ● ●    pma-cli — user@sp8d     [_] [□] [✕] │    │ ← 终端标题栏
│      │  ├───────────────────────────────────────────────┤    │
│ 左侧 │  │ ▸深圳报价 ×│客户分析 ×│Session 3 ×│ ＋      │    │ ← 标签栏
│ 导航 │  ├───────────────────────────────────────────────┤    │
│ (保 │  │ session: a3f2..  📊 23k/200k  🔄 /new         │    │ ← 状态条
│  留)│  ├───────────────────────────────────────────────┤    │
│      │  │                                               │    │
│      │  │  > 查一下上个月深圳的所有报价                  │    │
│      │  │  🔍 正在查询业务数据库...                      │    │
│      │  │  找到 23 条报价,总金额 ¥5,420,000...           │    │
│      │  │                                               │    │
│      │  │  > _                                          │    │
│      │  ╰───────────────────────────────────────────────╯    │
└──────┴───────────────────────────────────────────────────────┘
```

### 5.3 视觉规范

| 元素 | 风格 |
|---|---|
| 背景 | `#0d1117` 深色,区别于 PMA 其他页面 |
| 容器圆角 | `border-radius: 12px` |
| 边框 | `1px solid #30363d`, 轻微光晕 |
| 字体 | `JetBrains Mono` / `SF Mono` / `PingFang SC` (中文) |
| 字号 | 14px |
| 主文本 | `#e6edf3` |
| 用户 prompt 符号 `>` | `#7ee787` 绿色 |
| 工具状态行 | `#8b949e` 灰色斜体 |
| 错误 | `#f85149` 红色 |
| 链接 / 业务实体 | `#79c0ff` 蓝色 |
| 光标 | `#58a6ff` 闪烁方块,2Hz |

### 5.4 关闭 vs 切换行为区分

| 动作 | 触发 | 后端 |
|---|---|---|
| **切换** | 点 PMA 菜单 | session 保持 ACTIVE,下次回来恢复 |
| **关闭** | 点 tab 的 × | session 置 CLOSED,从标签栏移除 |
| **全关** | 点终端标题栏 ✕ | 回到 PMA 上一个页面,所有 session 保持 ACTIVE |
| **显式新开** | 点 ＋ | 创建新 session |
| **浏览器关闭** | 关标签 / 关浏览器 | session 保持 ACTIVE(48h 后自动 ARCHIVE) |

### 5.5 多标签管理

- **上限**: 8 个标签
- **数据源**: `user_cli_state.active_session_ids`
- **乐观更新**: 前端先切换 UI,服务端异步持久化
- **快捷键**:
  - `Ctrl+T` 新标签
  - `Ctrl+W` 关闭当前标签
  - `Ctrl+1~8` 跳到第 N 个标签
  - `Ctrl+Tab` / `Ctrl+Shift+Tab` 下一个 / 上一个
  - `Ctrl+N` 重置当前 session
  - `Ctrl+L` 清屏(不清历史)

### 5.6 斜杠命令(前端拦截,不走 LLM)

| 命令 | 行为 |
|---|---|
| `/new` | 当前 tab 内重置 session |
| `/tokens` | 显示当前 token 用量 |
| `/history` | 列出本用户所有 session(含 CLOSED/ARCHIVED) |
| `/help` | 命令列表 |
| `/clear` | 清屏 |
| `/keep` (v2) | 把最近 N 轮结果保留进 context |

## 6. 阶段划分

### 阶段 0: 骨架(本 commit)

- 目录结构
- 设计文档(本文件)
- 所有模块的 placeholder 文件(带 docstring)
- 最小可访问的 `/cli` 空页面
- 主菜单入口
- Blueprint 注册
- THIRD_PARTY_NOTICES.md

**验证**: `flask run` 后登录访问 `/cli` 能看到一个空的深色终端页面,主导航保留。

### 阶段 1: 核心 Agent Loop(无前端美化)

- `conversation.py`: ContentBlock 数据结构
- `llm_client.py`: Anthropic SDK 包装 + 流式
- `prompt_builder.py`: 静态 + 动态段拼装
- `tools/query_pma_database.py`: 复用 execute_safe_query
- `agent_loop.py`: 主循环
- `cli_session.py` + `user_cli_state.py` Models
- Alembic migration
- 最简 WebSocket/SSE 端点
- 单元测试

**验证**: 用 `pytest` 跑一个端到端 mock LLM 测试,能完成"发问→工具调用→答复"循环。

### 阶段 2: 前端完整终端

- xterm.js 集成
- Markdown 渲染器
- 标签栏 UI
- 斜杠命令
- 快捷键
- 持久化恢复

**验证**: 浏览器手动测试,可以完成一次真实查询并看到表格返回。

### 阶段 3: 上下文管理

- `compaction.py` 完整实现
- `usage.py` token 追踪
- 软/硬压缩触发
- 工具结果截断

**验证**: 单元测试 + 压测(灌 100 轮查询不崩)。

### 阶段 4: 灰度上线

- Feature flag 开启
- 对 admin 开放
- 收集一周反馈
- 调优阈值

### 阶段 5 (v1.1): Skill 系统

- `invoke_skill` 工具
- Skill 数据表
- Skill 编辑 UI
- 基于阶段 4 的使用数据提炼首批 skill

## 7. 安全与合规

### 7.1 权限

- 所有 `/cli/*` 路由要求 `@login_required`
- 每次工具调用都附带 `user_id`,后端用 `get_permission_context(user)` 过滤数据
- v1 只读:不暴露任何 INSERT/UPDATE/DELETE 工具
- Feature flag `ENABLE_CLI_AGENT` 控制整体开关
- 初期只对 `is_admin` 用户可见

### 7.2 数据出境

| 部署环境 | LLM 选择 | 数据是否出境 |
|---|---|---|
| OVS(新加坡) | Claude API 直连 | 出境至 Anthropic(已在新加坡合规范围内) |
| SP8D(中国) | DeepSeek 或 Qwen | 不出境,满足合规 |

`llm_client.py` 设计为 provider 抽象层,两种 provider 共用同一套 agent loop。

### 7.3 审计

- 每次 LLM 调用的 (user_id, session_id, 输入消息预览, tool_use 列表) 写入 `cli_audit_log`(可选,v1.1 加)
- 敏感 SQL(包含金额、工资、成本字段)标记为"高敏"并单独日志

### 7.4 成本控制

- 逐用户 daily token 配额(v1.1):超过拒绝新消息
- admin 可在管理面板查看每日总用量

## 8. 测试策略

- **单元测试**: conversation / compaction / prompt_builder / usage 每个模块独立测
- **集成测试**: mock Anthropic SDK,跑完整 agent loop
- **端到端测试**: 用真 test API key(低额度),跑 5 个代表性查询
- **压测**: 同时 10 个用户各开 3 个 tab,连续 50 轮查询,检查内存、token 估算、压缩行为

## 9. 参考与归因

本模块的上下文管理、压缩策略、系统提示分层、对话数据结构等**设计理念**参考了以下开源项目:

- **ultraworkers/claw-code**(MIT License)
  - https://github.com/ultraworkers/claw-code
  - 详细归因见 `app/services/cli_agent/THIRD_PARTY_NOTICES.md`

参考方式:**概念和算法策略**层面的借鉴,所有 Python 代码为原创实现,不包含来自 claw-code 的任何 Rust 源代码逐行翻译。

Anthropic 原生 API 能力用于:

- Prompt Caching (`cache_control: ephemeral`)
- Native tool use protocol
- Streaming responses
- `count_tokens()` API

## 10. 开放问题(待决策)

- [ ] Provider 抽象层是否 day 1 做?还是先 hard-code Claude,阶段 4 再加 DeepSeek?
- [ ] 是否需要同一 session 跨浏览器 tab 同步(WebSocket 广播)?
- [ ] 工具结果是否要存到对象存储(大结果 > 8k 时)?
- [ ] 是否支持在 CLI 内点击业务实体链接跳回 PMA 对应详情页?
- [ ] Skill 系统的授权模型:全局 skill vs 用户私有 skill vs 团队共享 skill?
