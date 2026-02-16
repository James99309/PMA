# OpenClaw 智能体集成设计

## 概述

在 PMA 聊天系统中增加 OpenClaw 智能体切换功能。管理员可以在 AI 对话中选择使用 OpenClaw（通过 WebSocket 连接新加坡 Mac 上的 Gateway）替代默认的 DeepSeek。

## 架构

```
[中国 NAS - PMA]                         [新加坡 Mac]

用户浏览器                                OpenClaw Gateway
    ↓                                    ws://100.x.x.x:18789
前端：模型选择下拉框                              ↑
    ↓                                           |
POST /chat/api/ai/stream                        |
    ↓                                    Tailscale 虚拟局域网
Flask 后端                                      |
    ├─ provider=deepseek → DeepSeek API         |
    └─ provider=openclaw → WebSocket ───────────┘
            ↓
        SSE 流式返回给前端
```

## 权限控制

- 阶段一（当前）：仅 `admin` 和 `ceo` 角色可见 OpenClaw 选项
- 阶段二（未来）：开放给所有用户，对话级切换

## 改动清单

### 1. 新增文件

**`app/services/openclaw_provider.py`**（~80-100 行）
- `stream_openclaw_response(message, conversation_history)` 生成器
- 通过 WebSocket 连接 OpenClaw Gateway
- 将 OpenClaw 响应转换为现有 SSE 格式

### 2. 修改文件

**`app/services/chat_ai_service.py`**
- `get_ai_response_stream()` 增加 `provider` 参数
- 根据 provider 路由到 DeepSeek 或 OpenClaw

**`app/views/chat.py`**
- `/chat/api/ai/stream` 接收 `provider` 字段
- 非管理员强制使用 deepseek

**`app/templates/components/tw_chat_panel.html`**
- 输入区域增加模型选择下拉框（仅管理员可见）
- 前端发送请求时携带 `provider` 字段

### 3. 环境变量

```bash
OPENCLAW_GATEWAY_URL=ws://100.x.x.x:18789
OPENCLAW_GATEWAY_TOKEN=<gateway token>
```

## 网络配置

Mac 和 NAS 通过 Tailscale 组网：
1. Mac 安装 Tailscale，OpenClaw Gateway 绑定 tailnet
2. NAS 安装 Tailscale，加入同一网络
3. PMA 通过 Tailscale IP 连接 Gateway

## 实施顺序

1. 网络：Tailscale 组网 + OpenClaw Gateway 绑定
2. 后端：openclaw_provider.py + 路由改造
3. 前端：模型选择 UI
4. 测试验证
