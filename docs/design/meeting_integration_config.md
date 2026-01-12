# 会议录音纪要功能 - 集成配置指南

## 概述

会议录音纪要功能需要以下外部服务：

| 服务 | 用途 | 必需 |
|------|------|------|
| OpenAI API | Whisper 语音转录 + GPT 纪要生成 | ✅ 是 |
| 群晖 NAS (WebDAV) | 音频文件存储（推荐） | ✅ 三选一 |
| Supabase Storage | 音频文件云端存储 | ✅ 三选一 |
| 本地存储 | 音频文件本地存储（开发测试） | ✅ 三选一 |
| Anthropic API | Claude 纪要生成（可选替代） | ❌ 否 |

## 存储方案选择

系统支持三种存储方案，通过 `MEETING_STORAGE_TYPE` 环境变量选择：

| 存储类型 | 环境变量值 | 适用场景 | 费用 |
|---------|-----------|---------|------|
| **群晖 NAS** | `synology` | 内部团队使用，有 NAS 设备 | 免费 |
| **Supabase** | `supabase` | 云端部署，需要公网访问 | 按量付费 |
| **本地存储** | `local` | 开发测试 | 免费 |

## 环境变量配置

### 1. OpenAI API（必需）

用于 Whisper 语音转录和 GPT 纪要生成。

```bash
# OpenAI API 密钥
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 可选：指定纪要生成使用的模型（默认 gpt-4o）
MEETING_AI_MODEL=gpt-4o
```

**获取方式**：
1. 访问 https://platform.openai.com/
2. 登录或注册账号
3. 进入 API Keys 页面
4. 创建新的 API Key

**费用参考**（2024年）：
- Whisper: $0.006/分钟
- GPT-4o: $5/1M input tokens, $15/1M output tokens
- 预估：1小时会议约 $0.50-1.00

### 2. 群晖 NAS WebDAV 存储（推荐）

使用群晖 NAS 的 WebDAV 服务存储会议录音文件，无需支付云存储费用。

```bash
# 存储类型选择
MEETING_STORAGE_TYPE=synology

# 群晖 WebDAV 配置
SYNOLOGY_WEBDAV_URL=https://192.168.1.2:5006
SYNOLOGY_WEBDAV_USER=pma-storage
SYNOLOGY_WEBDAV_PASSWORD=your-password
SYNOLOGY_WEBDAV_PATH=/pma-files

# 可选：是否验证 SSL 证书（群晖自签名证书设为 false）
SYNOLOGY_WEBDAV_VERIFY_SSL=false

# 可选：超时设置（秒）
SYNOLOGY_WEBDAV_TIMEOUT=30
```

**群晖 NAS 配置步骤**：

1. **启用 WebDAV 服务**
   - 登录群晖 DSM
   - 进入 控制面板 → 文件服务 → WebDAV
   - 勾选「启用 WebDAV」
   - 设置 HTTPS 端口（默认 5006）
   - 点击「应用」

2. **创建专用账户**（推荐）
   - 进入 控制面板 → 用户与群组
   - 创建新用户，如 `pma-storage`
   - 设置密码
   - 仅授予 WebDAV 访问权限

3. **创建共享文件夹**
   - 进入 控制面板 → 共享文件夹
   - 创建文件夹，如 `pma-files`
   - 授予 `pma-storage` 用户读写权限

4. **目录结构**
   ```
   /pma-files/
   └── meetings/
       └── {recording_id}/
           ├── chunk_0001_xxx.webm
           ├── chunk_0002_xxx.webm
           └── recording_xxx.webm
   ```

**外网访问方案**（部署在 Render 等云平台时）：

| 方案 | 说明 | 配置复杂度 |
|-----|------|----------|
| QuickConnect | 群晖官方内网穿透 | 简单 |
| Cloudflare Tunnel | 通过 CF 隧道暴露 WebDAV | 中等 |
| 内网穿透 (frp) | 自建穿透服务 | 复杂 |

### 3. Supabase Storage

用于云端存储会议录音文件。

```bash
# 存储类型选择
MEETING_STORAGE_TYPE=supabase

# Supabase 项目配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# 会议录音存储桶（需要在 Supabase 中创建）
SUPABASE_BUCKET_MEETING=meeting-recordings
```

**创建存储桶步骤**：
1. 登录 Supabase Dashboard
2. 进入 Storage 页面
3. 点击 "New Bucket"
4. 名称填写 `meeting-recordings`
5. 设置为 Public（或根据需要配置 RLS）

**RLS 策略建议**：
```sql
-- 允许已认证用户上传
CREATE POLICY "Authenticated users can upload"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'meeting-recordings');

-- 允许公开读取
CREATE POLICY "Public read access"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'meeting-recordings');
```

### 4. 本地存储

适用于开发测试。

```bash
# 存储类型选择
MEETING_STORAGE_TYPE=local

# 本地存储根目录（可选，默认 ./storage）
LOCAL_STORAGE_ROOT=./storage
```

录音文件将保存在 `./storage/meetings/` 目录。

### 5. Anthropic API（可选）

如果希望使用 Claude 生成纪要（替代 GPT）。

```bash
# Anthropic API 密钥
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 指定使用 Anthropic 作为 AI 提供商
AI_PROVIDER=anthropic
```

## 配置验证

启动应用后，可以通过以下 API 验证配置状态：

```bash
# 检查配置状态
curl http://localhost:5001/meeting/api/config-status
```

返回示例：
```json
{
  "success": true,
  "openai": {
    "configured": true,
    "features": ["whisper_transcription", "gpt_minutes"]
  },
  "anthropic": {
    "configured": false,
    "features": ["claude_minutes"]
  },
  "supabase": {
    "configured": false,
    "features": ["audio_storage"]
  },
  "synology": {
    "configured": true,
    "features": ["audio_storage"],
    "storage_type": "webdav"
  },
  "current_storage": "synology",
  "storage_ready": true,
  "all_configured": true,
  "minutes_ready": true
}
```

## 完整 .env 示例

### 使用群晖 NAS 存储（推荐）

```bash
# ============ 会议录音纪要配置 ============

# 存储类型
MEETING_STORAGE_TYPE=synology

# 群晖 WebDAV
SYNOLOGY_WEBDAV_URL=https://192.168.1.2:5006
SYNOLOGY_WEBDAV_USER=pma-storage
SYNOLOGY_WEBDAV_PASSWORD=your-password
SYNOLOGY_WEBDAV_PATH=/pma-files
SYNOLOGY_WEBDAV_VERIFY_SSL=false

# OpenAI（必需）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MEETING_AI_MODEL=gpt-4o

# 可选：使用 Claude 生成纪要
# ANTHROPIC_API_KEY=sk-ant-xxxxx
# AI_PROVIDER=anthropic
```

### 使用 Supabase 存储

```bash
# ============ 会议录音纪要配置 ============

# 存储类型
MEETING_STORAGE_TYPE=supabase

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_BUCKET_MEETING=meeting-recordings

# OpenAI（必需）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MEETING_AI_MODEL=gpt-4o
```

## 故障排除

### 1. Whisper 转录失败

**错误**：`openai 库未安装`
```bash
pip install openai
```

**错误**：`OPENAI_API_KEY 未配置`
- 检查环境变量是否正确设置
- 重启应用

### 2. 群晖 WebDAV 连接失败

**错误**：`WebDAV未配置`
- 检查环境变量 SYNOLOGY_WEBDAV_URL、SYNOLOGY_WEBDAV_USER、SYNOLOGY_WEBDAV_PASSWORD 是否设置

**错误**：`认证失败`
- 检查用户名和密码是否正确
- 确认用户有 WebDAV 访问权限

**错误**：`SSL证书验证失败`
- 设置 `SYNOLOGY_WEBDAV_VERIFY_SSL=false`（群晖使用自签名证书）

**错误**：`路径不存在`
- 检查 SYNOLOGY_WEBDAV_PATH 是否正确
- 确认共享文件夹已创建

### 3. Supabase 上传失败

**错误**：`Supabase 上传失败`
- 检查 SUPABASE_URL 和 SUPABASE_KEY
- 确认存储桶 `meeting-recordings` 已创建
- 检查 RLS 策略

### 4. 纪要生成失败

**错误**：`AI 服务未配置`
- 至少配置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY
- 检查 API 密钥是否有效

## 安全建议

1. **永不提交 API 密钥到代码仓库**
2. 使用 `.env` 文件管理密钥，并确保在 `.gitignore` 中
3. 生产环境使用环境变量注入（如 Render Environment Variables）
4. 定期轮换 API 密钥
5. 设置 API 使用限额避免意外费用
6. 群晖 NAS 建议创建专用账户，仅授予必要权限

## 音频访问 API

音频文件通过后端代理访问（支持 Range 请求用于播放器 seek）：

| API | 说明 |
|-----|------|
| `GET /meeting/audio/{recording_id}` | 通过录音ID获取音频流 |
| `GET /meeting/audio/stream?path=xxx` | 通过路径获取音频流 |
| `GET /meeting/audio/{recording_id}/info` | 获取音频文件信息 |

所有音频 API 都需要登录认证，并自动检查访问权限。
