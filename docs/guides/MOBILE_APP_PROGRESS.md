# PMA 移动端 App 实现记录

**最后更新**：2026-05-02
**分支**：`feature/mobile-api`
**目标平台**：iOS（Capacitor），Android 同源代码理论可跑未实测

---

## 1. 技术栈

| 层 | 选型 | 备注 |
|---|---|---|
| 前端框架 | **Vue 3 + Vite** | `<script setup>` Composition API |
| 状态管理 | **Pinia** | `chat` / `auth` / `dictionaries` |
| UI / 样式 | **Tailwind CSS v4** + `@theme` | 设计 token 全局变量 |
| 路由 | Vue Router (Hash mode) | iOS WebView 友好 |
| 原生壳 | **Capacitor 8.x** | 仅 iOS 验证；Android 待测 |
| HTTP 客户端 | Axios | `src/api/client.js` |
| 字体 | 自托管 Source Serif 4 (Adobe GitHub) + Noto Serif SC | OSF 旧式数字 |
| 后端 | **Flask + flask_jwt_extended** | 复用 PMA 主系统 services |
| 实时 | SSE（AI 流式）+ 30s 轮询（消息）| WebSocket 未实装 |

---

## 2. 后端 API 矩阵（`/api/v1/mobile/*`）

### 认证
| 端点 | 说明 |
|---|---|
| `POST /auth/login` | username + password → JWT |
| `POST /auth/refresh` | 刷新 token |

### 项目（`/mobile/projects`）
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/mobile/projects` | 列表 + 筛选 + 汇总金额 |
| GET | `/mobile/projects/<id>` | 详情（含 members + discussion_conversation_id + 报价 + 联系人 + 跟进） |
| POST | `/mobile/projects/<id>/stage` | 推进阶段 |
| POST | `/mobile/projects/<id>/auth-request` | 申请授权 |
| POST | `/mobile/projects/<id>/notes` | 添加跟进 |

### 客户（`/mobile/customers`）
列表、详情、创建、编辑（已实装）。

### 聊天（`/mobile/chat`）— 16 个端点全部实装
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/conversations` | 会话列表 |
| POST | `/conversations` | 新建会话（带 sync_metadata） |
| GET | `/conversations/<id>` | 会话详情（成员 + 关联项目 + 公告） |
| DELETE | `/conversations/<id>` | 删除/退出 |
| GET | `/conversations/<id>/messages` | 消息历史 |
| POST | `/conversations/<id>/messages` | 发送文本 |
| POST | `/conversations/<id>/read` | 标记已读 |
| GET | `/unread-count` | 未读总数 |
| POST | `/conversations/<id>/participants` | 加成员（联动项目共享） |
| DELETE | `/conversations/<id>/participants/<uid>` | 移除成员 |
| POST | `/messages/<id>/recall` | 撤回（2 分钟内） |
| POST | `/messages/<id>/forward` | 转发 |
| GET | `/users/search?conversation_id=&project_id=` | 用户搜索（带 scope） |
| GET | `/entity/projects` | 项目搜索（ACL） |
| GET | `/entity/companies` | 客户搜索（ACL） |
| POST | `/ai/stream` | AI SSE 流式 |

### 字典（复用主系统）
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/dictionary/<type>?active_only=true` | 通用字典（项目阶段、行业等），JWT 兼容 |

### 推送（占位）
- `POST /mobile/push/register` 注册 device token
- `POST /mobile/push/unregister`
- ❌ 未实装服务端推送发送

---

## 3. 前端模块清单

### 核心视图（`mobile-app/src/views/`）

| 视图 | 状态 | 备注 |
|---|---|---|
| `auth/LoginView.vue` | ✅ 真 | JWT 登录 |
| `SplashView.vue` | ✅ | 启动动画 |
| `AppShell.vue` | ✅ | Tab bar（项目/客户/聊天/我的），按 route.meta 隐藏 |
| `projects/ProjectListView.vue` | ✅ 真 | 列表 + 筛选 + 汇总 |
| `projects/ProjectDetailView.vue` | ✅ 真 | 阶段 stepper / picker / 讨论卡 / 跟进 / 报价 / 创建讨论群 |
| `projects/ProjectCreateView.vue` | ✅ 真 | 新建项目 |
| `customers/CustomerListView.vue` | ✅ 真 | |
| `customers/CustomerDetailView.vue` | ✅ 真 | |
| `customers/CustomerCreateView.vue` | ✅ 真 | |
| `customers/CustomerEditView.vue` | ✅ 真 | |
| `quotations/QuotationDetailView.vue` | ✅ 真 | 只读视图 |
| `messages/ChatListView.vue` | ✅ 真 | 30s 轮询；新建 DM/群聊 picker |
| `messages/GroupChatView.vue` | ✅ 真 | @AI SSE / @scope 限定 / 长按撤回转发 / 阶段推进卡 |
| `messages/DmChatView.vue` | ✅ 真 | @AI SSE / 长按撤回转发 |
| `messages/AiChatView.vue` | ✅ 真 | AI 助手专屏 |
| `messages/ChatSettingsView.vue` | ✅ 真 | 加/删成员（联动项目共享） |
| `messages/BroadcastView.vue` | 🔴 mock | 公司广播 — 后端未实装 |
| `approval/ApprovalView.vue` | ✅ 真 | 审批中心 |
| `profile/ProfileView.vue` | ✅ 真 | |

### 共享组件（`src/components/common/`）
- **MentionPopover.vue** — `@/#/$` 三维提及，scope 限定（conv/project）
- **MessageActions.vue** — 消息长按 sheet（复制/转发/撤回）+ 转发 sheet
- **StageAdvanceCard.vue** — 阶段推进富卡
- **MessageText / MessageRefs / PendingRefsPreview** — 消息文本 + 引用卡渲染
- **PixelP / Avatar / NavBar / Section / FileCard / VoiceMsg** — 通用 UI
- **refs/** — `ProjectRefCard / CustomerRefCard / ContactRefCard`

### Composable / Store / Util
- `composables/useMention.js` — 输入框 ↔ MentionPopover 联动
- `composables/useLongPress.js` — 长按检测（500ms / 8px 移动取消）
- `stores/chat.js` — 群消息 store（projectGroup ↔ chatGroup 同源）
- `stores/auth.js` — JWT + 用户信息
- `stores/dictionaries.js` — 字典缓存（30 分钟 TTL，并发去重）
- `utils/chatTime.js` — 时间格式化（今天/昨天/周/日期）
- `utils/mentionRender.js` — 消息文字 token 着色 + 引用卡 component map

---

## 4. 关键能力联动

### 项目 ↔ 讨论群双向绑定
- 创建讨论群时，会话 `sync_metadata.project_id = X`
- 加群成员 → 自动加入 `Project.shared_with_users`（owner 跳过）
- 移除/退群 → 自动从 `shared_with_users` 移除
- 阶段切换 → 自动给绑定群发"阶段推进"富卡（`message_type='stage_advance'`）
- 项目详情显示真实 members（owner + shared_with_users）

### @ scope 权限
- 群聊 `@`：仅本群成员 + 源助手
- 私聊 `@`：仅源助手（aiOnly）
- 项目讨论卡 `@`：项目成员 + 源助手
- `#` 项目 / `$` 客户：`get_viewable_data` ACL 完整过滤

### 字典驱动 UI（2026-05-02 接入）
- `project_stage` 等字典从后端 `/dictionary/<type>` 拉取
- 30 分钟 TTL，进程内缓存
- ProjectDetailView 阶段 picker / track + FilterSheet 阶段筛选
- 后台改字典 → 移动端自动反映

---

## 5. 完成度

| 模块 | 完成度 |
|---|---|
| 登录 / JWT / 路由守卫 | 100% |
| 客户 CRUD | 100% |
| 项目 CRUD + 阶段推进 | 100% |
| 项目讨论群（创建/成员/共享联动） | 100% |
| 报价单只读 | 100% |
| 审批中心 | 100% |
| 聊天 IM（DM/群/AI/SSE） | 100% |
| 撤回 / 转发 UI | 100% |
| @/#/$ 提及（带 scope 和 ACL） | 100% |
| 字典驱动 UI | 100%（项目阶段已接入；其他字典按需扩展） |
| 推送通知**注册** | 100%（device token 注册到后端） |
| 推送通知**发送** | 0% |
| 文件 / 图片 / 语音上传 | UI 0%（FileCard/VoiceMsg 占位） |
| 公司广播 | 前端 mock，后端未做 |
| 实时消息推送 | 30s 轮询；WebSocket 未做 |

**核心 IM + AI + 项目联动 端到端可用 95%+**

---

## 6. 已知问题 / Tech Debt

| 项 | 严重度 | 备注 |
|---|---|---|
| iOS 键盘上推 NavBar 进状态栏 | 中 | 已加 main.js 全局 focusin scrollTop=0 workaround；推荐装 `@capacitor/keyboard` 设 `resize:'body'` |
| 消息列表 30s 轮询，非实时 | 中 | WebSocket 或 Server-Sent Events 是下一步 |
| 没有推送通知发送（APNs） | 高 | 用户离 App 时收不到新消息提醒 |
| 富媒体上传 | 中 | UI 已占位，需 NAS WebDAV upload endpoint |
| BroadcastView 全 mock | 低 | 待 Announcement model + endpoint |
| Android 未测 | 低 | 同源代码可 build，需 cap android 命令链 |
| `@capacitor/keyboard` 未装 | 低 | 装上更稳的键盘行为 |

---

## 7. 关键架构决策

### 复用 vs 新写
- **chat 模块** 完全复用 `app/services/chat_service.py`，只在 `app/api/v1/mobile_chat.py` 包一层 JWT
- **字典** 复用现有 `/api/v1/dictionary/<type>`，无需新写
- **项目权限** 复用 `app/utils/access_control.py:get_viewable_data` / `can_view_project`

### `sync_metadata` 字段
`ChatConversation.sync_metadata`（Text JSON）原本设计给跨系统同步，复用为通用扩展点：
- `{"project_id": 123}` 项目讨论群
- `{"announcement": "..."}` 群公告
- 未来可加 `{"customer_id":...}` 客户讨论群等

### 字典 vs UI metadata
- **后端字典**（label）：`project_stage` 来自 DB，可后台维护
- **前端 metadata**（desc / pct / 颜色）：纯 UI 性，留 `STAGE_META` 映射
- 拼装方式：`STAGES_ALL = computed(() => dict.list().map(d => ({...d, ...META[d.key]})))`

---

## 8. 部署相关文件

```
mobile-app/
├── capacitor.config.json     # appId: com.pma.mobile
├── ios/                       # Xcode 项目
│   └── App/
│       ├── App.xcodeproj
│       └── App/public/        # ← cap sync 把 dist/ 复制到这里
├── dist/                      # Vite build 产物
├── package.json
└── src/
    ├── api/                   # axios clients (auth, chat, projects, customers, dictionaries, ...)
    ├── stores/                # pinia
    ├── components/common/
    ├── composables/
    ├── utils/
    └── views/
```

### 构建 + 同步流程
```bash
cd mobile-app
npm run build           # Vite → dist/
npx cap sync ios        # dist/ → ios/App/App/public/
# 然后在 Xcode Cmd+R
```

---

## 9. 后端关键文件索引

| 文件 | 作用 |
|---|---|
| `app/api/v1/mobile_chat.py` | 16 个聊天端点 |
| `app/api/v1/mobile_projects.py` | 项目端点（含 members + discussion_conversation_id） |
| `app/api/v1/mobile_customers.py` | 客户端点 |
| `app/api/v1/mobile_quotation.py` | 报价单 |
| `app/api/v1/mobile_approval.py` | 审批 |
| `app/api/v1/mobile_push.py` | Device token 注册 |
| `app/api/v1/dictionary.py` | 字典（移动端复用） |
| `app/services/chat_service.py` | 聊天业务逻辑（含 send_system_message / find_any_project_conversation 等新增） |
| `app/services/chat_agent/agent_loop.py` | AI 对话循环 |
| `app/views/project.py` | `update_project_stage_business_logic`（含 stage_advance 系统消息 hook） |

---

## 10. V1 上线前剩余工作

### 必做
1. **推送通知发送**（APNs）— 用户离 App 时收不到消息会很尴尬
2. **富媒体上传**（图片 / 文件 / 语音）— 后端 NAS WebDAV endpoint + 前端上传 UI
3. **iOS 键盘 plugin**（`@capacitor/keyboard`）— 把 workaround 替换为正式方案

### 可选
4. **公司广播** — 真后端
5. **WebSocket 实时** — 比 30s 轮询好很多
6. **Android 适配测试**
