# PMA 聊天系统设计文档

> **版本**: 1.0
> **日期**: 2026-02-14
> **分支**: `feature/chat-system`
> **状态**: 设计已确认，待实施

---

## 1. 功能概述

为 PMA 系统增加统一通讯功能，包含三种对话模式：

| 模式 | 说明 | 技术方案 |
|------|------|----------|
| **私聊** | 一对一人员沟通 | HTTP 短轮询（3秒） |
| **群聊** | 3人及以上多人讨论 | HTTP 短轮询（3秒） |
| **AI 对话** | 用户与 AI 助手交流 | SSE 流式输出 |

**核心特性**:
- 自动语言检测 + AI 翻译（原文 + 译文同时展示）
- 群聊中 @AI 触发 AI 参与讨论
- 独立 AI 对话窗口支持深度交互
- AI 可访问 PMA 业务数据（受权限控制，只读）
- 消息永久保存，支持未来分析

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────┐
│                   前端 (Alpine.js)               │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ 对话列表  │  │ 聊天区域  │  │ @ 用户搜索    │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│         │            │               │           │
│         ▼            ▼               ▼           │
│  ┌─────────────────────────────────────────────┐ │
│  │         统一 Chat API 层 (fetch)             │ │
│  └─────────────────────────────────────────────┘ │
└─────────────┬──────────────┬─────────────────────┘
              │              │
      HTTP REST API    SSE (AI流式)
              │              │
┌─────────────▼──────────────▼─────────────────────┐
│                Flask 后端                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
│  │ Chat API │  │ AI 服务  │  │ 翻译服务       │   │
│  │ (CRUD)   │  │ (SSE)    │  │ (异步AI翻译)   │   │
│  └────┬─────┘  └────┬─────┘  └──────┬────────┘   │
│       │              │               │            │
│  ┌────▼──────────────▼───────────────▼──────────┐ │
│  │              PostgreSQL                       │ │
│  │  chat_conversation | chat_participant         │ │
│  │  chat_message      | chat_translation         │ │
│  └──────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────┘
```

### 2.2 消息实时性方案（智能混合）

```
聊天窗口关闭 → 不轮询（零开销）
聊天窗口打开 → 3秒短轮询拉取新消息（体感接近实时）
AI 对话      → SSE 流式输出（逐字显示）
```

**不使用 WebSocket**：避免 gunicorn worker 更换、NAS Docker 配置变更、Cloudflare Tunnel 长连接兼容等部署改动。

---

## 3. 数据模型

### 3.1 ChatConversation（对话/群组）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 自增主键 |
| type | String(20) | `private` / `group` / `ai` |
| name | String(100), nullable | 群名称，私聊和AI对话为空 |
| created_by | Integer, FK → User | 创建者 |
| created_at | DateTime | 创建时间 (UTC) |
| updated_at | DateTime | 最后活跃时间 (UTC) |
| is_deleted | Boolean, default=False | 软删除 |

**索引**: `ix_chat_conversation_type`, `ix_chat_conversation_created_by`

### 3.2 ChatParticipant（参与者）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 自增主键 |
| conversation_id | Integer, FK → ChatConversation | 所属对话 |
| user_id | Integer, FK → User | 参与用户 |
| role | String(20), default='member' | `owner` / `member` |
| joined_at | DateTime | 加入时间 (UTC) |
| last_read_at | DateTime | 最后已读时间（用于计算未读数）|

**索引**: `uq_chat_participant_conv_user` (conversation_id, user_id) UNIQUE
**索引**: `ix_chat_participant_user_id`

### 3.3 ChatMessage（消息）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 自增主键 |
| conversation_id | Integer, FK → ChatConversation | 所属对话 |
| sender_id | Integer, FK → User, nullable | 发送者（AI消息为NULL）|
| content | Text | 原始消息文本 |
| source_language | String(10) | 检测到的源语言 `zh` / `en` |
| is_ai_response | Boolean, default=False | 是否为AI回复 |
| ai_model | String(50), nullable | AI模型标识 |
| ai_prompt_tokens | Integer, nullable | AI输入token数 |
| ai_completion_tokens | Integer, nullable | AI输出token数 |
| reply_to_id | Integer, FK → ChatMessage, nullable | 引用回复 |
| created_at | DateTime | 发送时间 (UTC) |
| is_deleted | Boolean, default=False | 软删除 |
| deleted_at | DateTime, nullable | 删除时间 |

**索引**: `ix_chat_message_conv_created` (conversation_id, created_at)
**索引**: `ix_chat_message_sender_id`

### 3.4 ChatTranslation（翻译）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 自增主键 |
| message_id | Integer, FK → ChatMessage | 关联消息 |
| target_language | String(10) | 目标语言 `zh` / `en` |
| translated_content | Text | 翻译后文本 |
| created_at | DateTime | 翻译时间 |

**索引**: `uq_chat_translation_msg_lang` (message_id, target_language) UNIQUE

---

## 4. API 设计

### 4.1 对话管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chat/api/conversations` | GET | 获取当前用户的对话列表（含未读数） |
| `/chat/api/conversations` | POST | 创建新对话（私聊/群聊/AI） |
| `/chat/api/conversations/<id>` | GET | 获取对话详情（含成员列表） |
| `/chat/api/conversations/<id>/participants` | POST | 添加群成员 |
| `/chat/api/conversations/<id>/participants/<uid>` | DELETE | 移除群成员 |

### 4.2 消息

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chat/api/conversations/<id>/messages` | GET | 获取历史消息（分页，支持 `?since=timestamp` 增量拉取） |
| `/chat/api/conversations/<id>/messages` | POST | 发送消息 |
| `/chat/api/conversations/<id>/read` | POST | 更新已读位置 |
| `/chat/api/unread-count` | GET | 获取所有对话总未读数（轻量级，供页面轮询） |

### 4.3 AI 对话

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chat/api/ai/stream` | POST | AI 对话（SSE 流式响应） |
| `/chat/api/ai/group-reply` | POST | 群聊中 @AI 触发的回复（SSE 流式） |

### 4.4 用户搜索

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chat/api/users/search` | GET | 搜索用户（`?q=keyword`），用于 @ 提及 |

### 4.5 轮询策略

```javascript
// 聊天窗口打开时启动轮询
let pollTimer = null;

function startPolling(conversationId) {
    let lastTimestamp = getLastMessageTimestamp();
    pollTimer = setInterval(async () => {
        const resp = await fetch(
            `/chat/api/conversations/${conversationId}/messages?since=${lastTimestamp}`
        );
        const newMessages = await resp.json();
        if (newMessages.length > 0) {
            appendMessages(newMessages);
            lastTimestamp = newMessages[newMessages.length - 1].created_at;
        }
    }, 3000);
}

function stopPolling() {
    clearInterval(pollTimer);
    pollTimer = null;
}
```

---

## 5. 自动翻译系统

### 5.1 语言检测

```python
def detect_language(text: str) -> str:
    """基于 CJK 字符占比检测语言，适用于中英文场景"""
    cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total = max(len(text.strip()), 1)
    return 'zh' if cjk_count / total > 0.1 else 'en'
```

### 5.2 翻译流程

```
发送消息
  ↓
detect_language(content) → source_lang
  ↓
查询对话成员的 language_preference → 得到需要的目标语言集合
  ↓
去除 source_lang → 需要翻译的语言列表（去重）
  ↓
调用 AI 翻译 API（一次调用翻译所有目标语言）
  ↓
存入 ChatTranslation 表
  ↓
下次拉取消息时，根据请求者的 language_preference 返回对应翻译
```

### 5.3 翻译显示规则

| 请求者语言 | 消息源语言 | 显示内容 |
|-----------|-----------|---------|
| zh | zh | 仅原文 |
| zh | en | 原文（英文） + 中文翻译 |
| en | zh | 原文（中文） + 英文翻译 |
| en | en | 仅原文 |

---

## 6. AI 助手设计

### 6.1 两种触发方式

| 方式 | 场景 | 行为 |
|------|------|------|
| **独立 AI 对话** | 用户新建对话不 @ 任何人 | 进入专属 AI 对话，深度交互 |
| **群聊 @AI** | 群聊中输入 `@AI 问题` | AI 在群聊上下文中回答，所有成员可见 |

### 6.2 AI 数据访问权限

```python
# AI 查询使用独立只读数据库连接
AI_DB_URI = f"{DB_URI}?options=-c%20default_transaction_read_only=on"

# AI 基于提问者权限过滤数据
def ai_query_with_permissions(user, query_intent):
    """AI 查询前注入用户权限约束"""
    viewable_data = get_viewable_data(target_model, user)
    # AI 只能在 viewable_data 范围内查询
    return execute_ai_query(viewable_data, query_intent)
```

**安全规则**:
- 数据库连接强制只读（`default_transaction_read_only=on`）
- 基于 `get_viewable_data()` 过滤用户可见数据范围
- 报销单等敏感数据严格按现有权限规则控制
- AI 回复中不暴露超出用户权限的数据

### 6.3 AI SSE 流式输出

```python
@chat_bp.route('/api/ai/stream', methods=['POST'])
@login_required
def ai_stream():
    """AI 对话 SSE 流式响应"""
    data = request.get_json()
    conversation_id = data['conversation_id']
    message = data['message']

    def generate():
        # 调用 AI API（流式）
        for chunk in call_ai_model_stream(message, current_user):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )
```

---

## 7. 前端设计

### 7.1 UI 结构

右下角浮动聊天气泡，点击展开聊天面板：

```
┌─────────────────────────────────────────────┐
│ 消息              [新建对话] [最小化] [关闭]  │
├────────────┬────────────────────────────────┤
│ [搜索对话]  │  对话头部 (名称 + 成员数)       │
│            ├────────────────────────────────┤
│ AI 助手    │                                │
│ 群聊 A  (3)│  消息气泡区域                   │
│ Bob    ●   │  - 对方消息（左侧，灰色底）      │
│ 群聊 B     │    [原文]                       │
│ 李明       │    [翻译图标 + 译文]             │
│            │  - 我的消息（右侧，蓝色底）      │
│ [+ 新对话] │    [原文]                       │
│            │    [翻译图标 + 译文]             │
│            ├────────────────────────────────┤
│            │ [输入消息...         ] [发送]   │
└────────────┴────────────────────────────────┘
```

### 7.2 新建对话交互

1. 点击「新建对话」按钮
2. 顶部出现收件人输入区
3. 输入 `@` 触发用户搜索下拉菜单
4. 选择用户后显示为标签，可继续 @ 更多
5. 不 @ 任何人 = 默认 AI 对话
6. @ 一人 = 私聊
7. @ 多人 = 群聊（可输入群名称）

### 7.3 交互原型

预览文件：`docs/temp/chat_mockup.html`（浏览器打开可交互）

---

## 8. 分期实施计划

### 一期：核心聊天功能

| 步骤 | 内容 | 优先级 |
|------|------|--------|
| 1 | 数据库模型 + 迁移 | P0 |
| 2 | 对话 CRUD API | P0 |
| 3 | 消息发送/接收 API + 3秒轮询 | P0 |
| 4 | 前端聊天面板（Alpine.js 组件） | P0 |
| 5 | 自动语言检测 + AI 翻译 | P0 |
| 6 | 独立 AI 对话（SSE 流式） | P0 |
| 7 | 群聊 @AI 功能 | P1 |
| 8 | 用户搜索 + @ 提及 | P0 |
| 9 | 未读计数 + 角标 | P0 |
| 10 | 集成到 tw_layout.html | P0 |

### 二期：增强功能

| 步骤 | 内容 | 优先级 |
|------|------|--------|
| 1 | 文件/图片发送（NAS WebDAV 存储） | P1 |
| 2 | 业务对象关联讨论（项目/报价单内嵌聊天） | P1 |
| 3 | AI 业务数据查询（产品库、报价历史等） | P1 |
| 4 | 消息搜索 | P2 |
| 5 | 沟通数据分析仪表板 | P2 |

---

## 9. 文件结构

```
app/
├── models/
│   └── chat.py                           # ChatConversation, ChatParticipant,
│                                         # ChatMessage, ChatTranslation
├── services/
│   ├── chat_service.py                   # 对话/消息业务逻辑
│   ├── chat_ai_service.py                # AI 对话 + @AI 处理
│   └── chat_translation_service.py       # 语言检测 + AI 翻译
├── views/
│   └── chat.py                           # Blueprint: /chat/api/*
├── templates/
│   └── components/
│       └── tw_chat_panel.html            # 聊天面板 Jinja2 组件
└── static/
    └── js/
        └── chat/
            ├── chat-panel.js             # 面板主逻辑 (Alpine.js)
            ├── chat-polling.js           # 轮询管理
            └── chat-sse.js              # AI SSE 流式处理
```

---

## 10. 开发隔离策略

使用 **Git Worktree** 隔离开发：

```bash
# 创建特性分支
git branch feature/chat-system

# 创建独立工作目录
git worktree add ../PMA-chat feature/chat-system

# 在 PMA-chat 目录开发，主目录正常迭代
# 开发完成后合并：
git checkout main
git merge feature/chat-system

# 清理 worktree
git worktree remove ../PMA-chat
```

**隔离保证**：
- 主分支 `main` 正常迭代和部署
- 聊天功能在 `feature/chat-system` 分支独立开发
- 两个目录互不影响，不会意外合入
- 功能完整测试后再合并到主分支一次性发布

---

## 11. 关键设计决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 实时方案 | 3秒短轮询（非WebSocket） | 无需改部署架构，体验可接受 |
| AI 响应 | SSE 流式 | 逐字输出体验好，不需要 WebSocket |
| 语言检测 | CJK 字符占比 | 中英文场景准确率接近100%，无需额外依赖 |
| 翻译方式 | AI 模型翻译 | 质量远优于传统翻译 API |
| UI 形式 | 右下角浮动面板 | 不打断当前工作流 |
| 对话组织 | 类 Claude 界面 | 用户熟悉，@ 建群直觉 |
| 消息存储 | 永久保存 + 软删除 | 支持未来数据分析 |
| AI 数据访问 | 只读 + 权限过滤 | 安全第一 |
| 文件发送 | 二期 | 一期聚焦核心聊天体验 |
| 开发隔离 | Git Worktree | 不影响主分支正常迭代 |
