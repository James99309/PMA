# PMA 声纹分离服务（pyannote.audio）

部署在 Mac mini 上，被 PMA (CN/SG NAS) 通过 Tailscale 调用做会议录音的说话人分离。

## 一次性部署步骤

### 1. HuggingFace 准备（账号操作，一次）

1. 注册 https://huggingface.co/ 账号
2. 接受这两个模型的 license：
    - https://huggingface.co/pyannote/speaker-diarization-3.1 → 点 "Agree and access repository"
    - https://huggingface.co/pyannote/segmentation-3.0 → 同上
3. https://huggingface.co/settings/tokens → "Create new token" → role `read` → 复制 `hf_xxxxxxxx`

### 2. Mac mini 上准备（SSH 远程跑）

```bash
# 在 Mac 上跑（不是 SSH 进去再跑也行）
ssh jing@100.110.41.83 << 'EOF'
set -e
# 装 Homebrew ffmpeg（如已装跳过）
if ! command -v ffmpeg >/dev/null; then
    /opt/homebrew/bin/brew install ffmpeg
fi

# 创建工作目录
mkdir -p /Users/jing/pma-diarizer/logs

# Python 3.13 venv
/opt/homebrew/bin/python3.13 -m venv /Users/jing/pma-diarizer/venv

# 装依赖（耗时 5-10 分钟）
/Users/jing/pma-diarizer/venv/bin/pip install --upgrade pip
EOF

# 把代码 SCP 过去
scp main.py requirements.txt jing@100.110.41.83:/Users/jing/pma-diarizer/

# 装 Python 依赖
ssh jing@100.110.41.83 '/Users/jing/pma-diarizer/venv/bin/pip install -r /Users/jing/pma-diarizer/requirements.txt'
```

### 3. 配置 launchd 自启

```bash
# 改 plist 里的 REPLACE_ME_HF_TOKEN 为你的 token
sed "s/REPLACE_ME_HF_TOKEN/hf_xxxxxxxx/" com.pma.diarizer.plist > /tmp/com.pma.diarizer.plist
scp /tmp/com.pma.diarizer.plist jing@100.110.41.83:~/Library/LaunchAgents/

# 加载（开机自启）
ssh jing@100.110.41.83 'launchctl load ~/Library/LaunchAgents/com.pma.diarizer.plist'

# 看启动日志
ssh jing@100.110.41.83 'tail -f /Users/jing/pma-diarizer/logs/stderr.log'
```

首次启动会从 HuggingFace 下载模型权重（约 200MB），耗时 1-3 分钟。看到 `pipeline 加载完毕` 即就绪。

### 4. 验证

```bash
# 健康检查
curl http://100.110.41.83:8080/health
# 期望：{"ok": true, "model": "pyannote/speaker-diarization-3.1", "has_token": true}

# 真实推理（从 PMA 抓一个已有录音的 URL 测试）
curl -X POST http://100.110.41.83:8080/diarize \
  -H 'Content-Type: application/json' \
  -d '{"audio_url": "http://...nas.../recording.webm", "recording_id": 54}'
```

## PMA 端配置

在 PMA `.env.local` / `.env`：

```bash
PYANNOTE_SERVICE_URL=http://100.110.41.83:8080
# NAS WebDAV basic auth（让 Mac mini 能下载音频）
PYANNOTE_NAS_AUTH=username:password
```

CN/SG 两个 PMA 实例都加这两个变量（用各自的 NAS WebDAV 凭据）。

## 运维

```bash
# 查日志
ssh jing@100.110.41.83 'tail -f /Users/jing/pma-diarizer/logs/stderr.log'

# 重启服务
ssh jing@100.110.41.83 'launchctl unload ~/Library/LaunchAgents/com.pma.diarizer.plist && launchctl load ~/Library/LaunchAgents/com.pma.diarizer.plist'

# 停止
ssh jing@100.110.41.83 'launchctl unload ~/Library/LaunchAgents/com.pma.diarizer.plist'
```

## 性能预期（Mac mini M2 / M4 + MPS）

| 会议时长 | 推理耗时 |
|---|---|
| 5 min | 10-30s |
| 30 min | 30-90s |
| 60 min | 1-3 min |
| 2 h | 3-8 min |

服务用 `asyncio.Lock` 串行执行推理，并发请求自动排队。
