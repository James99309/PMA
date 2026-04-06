# PMA CLI Agent 阶段 2 — 前端完整终端

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将阶段 1 的简易 HTML 终端升级为功能完整的前端终端，支持 Markdown 渲染、多标签管理、斜杠命令、快捷键和会话恢复。

**Architecture:** 保持 HTML + CSS 方案（不用 xterm.js），用 marked.js（已有 vendor）渲染 Markdown 富内容。将 terminal.html 中的 250 行内联脚本提取为模块化 JS 文件。后端新增 session title 更新和历史查询 API。

**Tech Stack:** marked.js (vendor), vanilla JS (ES2020+), CSS custom properties, SSE streaming

**设计文档:** `docs/plans/2026-04-05-pma-cli-agent-design.md` 第 5-6 节

---

## Task 1: Markdown 渲染器

**Files:**
- Create: `app/static/js/cli/markdown-renderer.js`
- Modify: `app/static/css/cli/terminal.css` (添加 markdown 样式)

**目标:** 创建 `CliMarkdownRenderer` 类，包装 marked.js，输出安全的 HTML。

**功能:**
- GFM 表格 → 带样式的 `<table>`
- 代码块 → `<pre><code>` 带语言标签和复制按钮
- 行内代码 → `<code>` 带高亮底色
- 列表、标题、粗体、斜体
- 链接 → `target="_blank" rel="noopener"`
- XSS 防护：用白名单过滤标签
- 业务实体高亮：金额（¥/$）、百分比自动着色

**CSS 新增:**
- `.cli-md` 容器：表格、代码块、列表的终端暗色主题样式
- `.cli-code-block`：深色背景 + 复制按钮
- `.cli-table`：紧凑表格，交替行色

**验证:** 在终端中输入"帮我查上个月的报价"，AI 返回的表格数据应以格式化表格展示。

---

## Task 2: Terminal App 核心重构

**Files:**
- Create: `app/static/js/cli/terminal-app.js`
- Modify: `app/templates/cli/terminal.html` (移除内联脚本，引入新 JS)

**目标:** 将内联脚本提取为 `CliTerminalApp` 类，保持现有功能不变。

**类结构:**
```javascript
class CliTerminalApp {
  constructor(config)      // DOM 元素引用、API 路径、CSRF token
  // 状态
  sessions = new Map()     // sessionId → {title, messages, usage, status}
  activeSessionId = null
  tabs = []                // 有序 tab 列表 [{id, title}]
  isStreaming = false

  // 核心方法
  async init()             // 加载 sessions、渲染 tabs、恢复当前 session
  async sendMessage(text)  // 发送 + SSE 流式接收
  handleEvent(evt)         // SSE 事件分发

  // 渲染
  renderMessage(role, blocks)   // 用 CliMarkdownRenderer 渲染
  appendUserLine(text)
  appendAssistantText(text, streaming)
  appendToolStatus(text)
  appendErrorLine(text)
  scrollToBottom()
}
```

**验证:** 提取后功能与阶段 1 完全一致，无回归。

---

## Task 3: 多标签管理

**Files:**
- Modify: `app/static/js/cli/terminal-app.js` (添加 tab 方法)
- Modify: `app/templates/cli/terminal.html` (tab 模板结构)
- Modify: `app/views/cli.py` (title 更新 API)

**功能:**
- `createTab()` → POST /api/sessions → 新标签 + 切换
- `closeTab(sessionId)` → POST /api/sessions/:id/close → 移除标签
- `switchTab(sessionId)` → POST /api/sessions/:id/focus → 切换 + 加载消息
- `renderTabs()` → 根据 sessions 状态重绘标签栏
- 自动标题：取用户第一条消息的前 20 字符
- 最多 8 个标签，超出提示

**后端新增:**
```python
@cli_bp.route('/api/sessions/<session_id>/title', methods=['PATCH'])
def update_session_title(session_id):
    # 接收 {"title": "..."}, 更新 session.title
```

**验证:** 可以新建 3 个标签，来回切换，每个标签的对话独立，关闭标签后消失。

---

## Task 4: 斜杠命令

**Files:**
- Modify: `app/static/js/cli/terminal-app.js` (添加命令解析)
- Modify: `app/views/cli.py` (历史 API)

**命令列表（前端拦截，不走 LLM）:**

| 命令 | 行为 |
|------|------|
| `/new` | 当前 tab 重置 session（新建 session 替换当前 tab） |
| `/tokens` | 显示当前 session 的 token 用量明细 |
| `/history` | 列出所有 session（含 CLOSED/ARCHIVED），显示创建时间和消息数 |
| `/help` | 显示命令列表和快捷键 |
| `/clear` | 清屏（不清消息历史，仅视觉清理） |

**命令解析:**
```javascript
parseSlashCommand(text) {
  const match = text.match(/^\/(\w+)\s*(.*)/);
  if (!match) return null;
  return { command: match[1], args: match[2].trim() };
}
```

**后端新增:**
```python
@cli_bp.route('/api/sessions/history', methods=['GET'])
def session_history():
    # 返回当前用户所有 session（含 CLOSED），按 last_active_at 降序
```

**验证:** 输入 `/help` 显示命令列表，`/tokens` 显示 usage，`/history` 显示所有会话。

---

## Task 5: 键盘快捷键

**Files:**
- Modify: `app/static/js/cli/terminal-app.js` (添加 keydown 监听)

**快捷键映射:**

| 快捷键 | 行为 |
|--------|------|
| `Ctrl+T` | 新标签 |
| `Ctrl+W` | 关闭当前标签 |
| `Ctrl+1~8` | 跳到第 N 个标签 |
| `Ctrl+Tab` | 下一个标签 |
| `Ctrl+Shift+Tab` | 上一个标签 |
| `Ctrl+N` | 当前 tab 重置（同 /new） |
| `Ctrl+L` | 清屏（同 /clear） |
| `Enter` | 发送（已有） |
| `Shift+Enter` | 换行（已有） |

**注意:** `Ctrl+T` 和 `Ctrl+W` 会被浏览器拦截，需要 `e.preventDefault()`。如果浏览器不允许覆盖，降级为 `Alt+T` / `Alt+W`。

**验证:** 按 Ctrl+L 清屏，Ctrl+N 重置，Ctrl+1/2 切换标签。

---

## Task 6: 会话恢复 + Loading 状态

**Files:**
- Modify: `app/static/js/cli/terminal-app.js`
- Modify: `app/static/css/cli/terminal.css` (loading + token 阈值样式)

**会话恢复:**
- 页面加载时，从 GET /api/sessions 获取所有 active session
- 渲染标签栏，恢复 current_session 的消息
- 切换标签时，如果该 session 的消息已缓存（Map 中有），直接显示；否则 fetch

**Loading 状态:**
- 流式响应期间：输入框禁用 + 光标动画（三个跳动的点）
- 工具调用期间：显示旋转图标 + 工具名
- 标签切换：短暂 loading 骨架屏

**Token 阈值颜色:**
- `< 120k`：正常灰色
- `120k ~ 160k`：黄色 ⚠️
- `> 160k`：红色 🔴

**验证:** 刷新页面后，之前的标签和对话完整恢复。流式回复时有可见的 loading 动画。

---

## Task 7: 整合测试 + commit

**验证清单:**
- [ ] 发送自然语言问题，AI 返回 Markdown 格式的表格 ✅
- [ ] 新建 3 个标签，来回切换，对话独立 ✅
- [ ] 关闭标签，标签消失，切到相邻标签 ✅
- [ ] `/help` 显示所有命令 ✅
- [ ] `/tokens` 显示 usage ✅
- [ ] `/clear` 清屏 ✅
- [ ] `/new` 重置当前 tab ✅
- [ ] `/history` 列出历史 session ✅
- [ ] Ctrl+L 清屏，Ctrl+N 重置 ✅
- [ ] 刷新页面后标签和对话恢复 ✅
- [ ] 流式回复有 loading 动画 ✅
- [ ] Token 超 120k 显示黄色警告 ✅
