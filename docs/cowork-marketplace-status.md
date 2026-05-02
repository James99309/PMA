# Evertac Cowork Marketplace — 项目状态

最后更新：2026-05-02

## 目标

让 Evertac 团队成员能在自己的 Claude Cowork 里**自助安装/管理团队私有 skill**：
- 团队成员浏览网页 catalog → 点 Copy → Terminal 粘贴回车 → skill 装好
- 已装 skill 每天 04:00 自动同步最新版（不强加新 plugin）
- 单点更新：维护者只 push 到 Mac mini Gitea，团队自动收到
- 跨 Mac + Windows（Windows 支持待做）

## 整体架构

```
┌────────────────────── Mac mini (jing@100.110.41.83) ──────────────────────┐
│                                                                            │
│  Gitea  127.0.0.1:3000   ←──── 维护者 git push                            │
│    └─ repo: evertac/cowork-marketplace.git                                 │
│       ├─ .claude-plugin/marketplace.json   (plugin 元数据 + categories)    │
│       ├─ install.sh                        (Mac 一键脚本)                  │
│       ├─ marketplace.html                  (catalog 网页)                  │
│       ├─ assets/evertac-logo-cn.png                                        │
│       └─ plugins/<name>/skills/<name>/SKILL.md  (实际 skill 内容)         │
│                                                                            │
│  cowork-marketplace-www/  (本地 git clone, 5 分钟自动 pull)               │
│    └─ Python http.server 127.0.0.1:3001  (serve 静态文件)                  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓ Cloudflare Tunnel
                              ↓ (tunnel id: 58e9ab52-88ee-4d6d-9084-7d19a91cfa3e)
                              ↓
                              ├─ gitea.jamesgpone.win → :3000  (git push/pull)
                              ├─ marketplace.jamesgpone.win → :3001  (浏览页 + install.sh 短地址)
                              └─ pma-mcp.jamesgpone.win → :8765  (PMA MCP 服务，已有)
                              ↓
                              ↓ HTTPS
                  ┌───────────┴───────────┐
                  │                       │
              Mac 团队成员            Windows 团队成员（待做）
                  │                       │
                  ↓                       ↓
            install.sh              install.ps1（待写）
                  │                       │
                  ↓                       ↓
            cowork_plugins/         待确认 Windows 路径
            注入 3 个 JSON
                  │
                  ↓
            launchd 每天 04:00 sync
```

## 当前状态

### ✅ 已完成

| 项 | 状态 | 备注 |
|----|------|------|
| Mac mini 上 Gitea 1.26.1 部署 | ✅ | `~/.gitea/`, SQLite, launchctl 守护 `com.jing.gitea` |
| Cloudflare Tunnel 路由 gitea.jamesgpone.win → :3000 | ✅ | macmini-proxy.yml 已加 |
| 仓库 evertac/cowork-marketplace 创建 | ✅ | 公开仓库，主分支 main |
| install.sh（Mac/Linux 版）| ✅ | 支持 -P/-p/-u/list/sync/browse；写 3 个 JSON；部署 launchd |
| marketplace.html 设计实现 | ✅ | 按 Anthropic Design 暖色主题 React + Babel inline |
| logo 资源 | ✅ | assets/evertac-logo-cn.png |
| Python http.server (127.0.0.1:3001) | ✅ | launchctl `com.jing.cowork-marketplace-www` |
| 5 分钟自动 git pull www 目录 | ✅ | launchctl `com.jing.cowork-marketplace-www-sync` |
| Cloudflare Tunnel marketplace.jamesgpone.win → :3001 | ✅ |  |
| 第一个真实 skill：geo-article-writer | ✅ | category=marketing, GEO 优化文章生成器 |
| 维护者本机已装该 skill | ✅ | Cowork Personal plugins 里能看到 |

### ⚠️ 待办

| 项 | 优先级 | 说明 |
|----|-------|------|
| **Windows 版 install.ps1** | 高 | 团队有 Windows 用户。Cowork 在 Windows 上确实存在（用户纠正我之前的推断），需要查清 Windows 上数据路径再写 |
| 加更多 skill 到 marketplace | 中 | 目前只有 1 个；pma-training 可以迁过来；marketing-doc 待开发 |
| README.md 完善 | 低 | 写给团队成员的入门指南 |

## 关键文件路径

### Mac mini 上

| 文件 | 说明 |
|------|------|
| `/opt/homebrew/var/gitea/` | Gitea 数据目录 |
| `/opt/homebrew/var/gitea/custom/conf/app.ini` | Gitea 配置 |
| `/opt/homebrew/var/gitea/repos/evertac/cowork-marketplace.git` | 仓库 bare repo |
| `/opt/homebrew/var/cowork-marketplace-www/` | www 服务的 working tree（5 分钟 pull）|
| `/opt/homebrew/var/cowork-marketplace-www/server.py` | HTTP server 代码 |
| `~/Library/LaunchAgents/com.jing.gitea.plist` | Gitea 守护 |
| `~/Library/LaunchAgents/com.jing.cowork-marketplace-www.plist` | www server 守护 |
| `~/Library/LaunchAgents/com.jing.cowork-marketplace-www-sync.plist` | www 同步任务 |
| `~/.cloudflared/macmini-proxy.yml` | Cloudflare Tunnel 配置 |

### 团队成员 Mac 上

| 文件 | 说明 |
|------|------|
| `~/Library/Application Support/Claude-3p/local-agent-mode-sessions/<account-uuid>/<org-uuid>/cowork_plugins/known_marketplaces.json` | marketplace 注册表 |
| `~/Library/Application Support/Claude-3p/local-agent-mode-sessions/<account-uuid>/<org-uuid>/cowork_plugins/installed_plugins.json` | 已装 plugin 注册表 |
| `~/Library/Application Support/Claude-3p/local-agent-mode-sessions/<account-uuid>/<org-uuid>/cowork_settings.json` | enabledPlugins 设置 |
| `~/Library/Application Support/Claude-3p/local-agent-mode-sessions/<account-uuid>/<org-uuid>/cowork_plugins/marketplaces/evertac-cowork/` | git clone 的 marketplace 内容 |
| `~/Library/LaunchAgents/com.evertac.cowork-marketplace-sync.plist` | 每天 04:00 自动 sync |

## 命令清单（Mac 团队成员）

短地址：`https://marketplace.jamesgpone.win/install.sh`

```bash
# 浏览（浏览器打开）
https://marketplace.jamesgpone.win/

# 按角色装一套
bash <(curl -fsSL https://marketplace.jamesgpone.win/install.sh) -P marketing

# 单装某个
bash <(curl -fsSL https://marketplace.jamesgpone.win/install.sh) -p geo-article-writer

# 看本机已装
bash <(curl -fsSL https://marketplace.jamesgpone.win/install.sh) list

# 立即同步
bash <(curl -fsSL https://marketplace.jamesgpone.win/install.sh) sync

# 卸载
bash <(curl -fsSL https://marketplace.jamesgpone.win/install.sh) -u geo-article-writer

# 浏览 marketplace 全部
bash <(curl -fsSL https://marketplace.jamesgpone.win/install.sh) browse
```

## 维护者改动后必须升版本号 ⚠️

每次改了 SKILL.md 或 plugin 内容，**必须同时升 `plugin.json` 的 version**（也建议同步更新 `marketplace.json` plugins[] 里的 version），否则：
- Cowork Settings → Personal plugins 里看到的版本号不变
- 团队成员不知道新版来了
- launchd sync 拉了新文件但用户感知不到差别

按 semver 约定：
- `1.0.0` → `1.0.1` — bug 修复 / typo 调整
- `1.0.0` → `1.1.0` — 加新功能 / 流程调整
- `1.0.0` → `2.0.0` — 大改、breaking 变化

**版本号有两处必须同步改**：
```
plugins/<name>/.claude-plugin/plugin.json     ← Cowork 实际读的（Settings 显示）
.claude-plugin/marketplace.json plugins[].version  ← 网页 catalog 显示的
```

---

## 维护者工作流（你 push 新 skill）

```bash
# 1. 在自己 Mac 上的 ~/.claude/skills/ 写好新 skill 测试

# 2. clone 仓库到本地工作目录（一次性）
ssh jing@100.110.41.83 'cd /tmp/cm-clone && git pull --quiet'
# 实际上每次干活前都 git pull

# 3. 把新 skill 加进去：
#    a) 复制 SKILL.md 到 plugins/<name>/skills/<name>/
#    b) 加 .claude-plugin/plugin.json
#    c) 编辑 .claude-plugin/marketplace.json:
#       - plugins[] 数组里加新 plugin 元数据（含 title/feats/category 等）
#       - profiles{} 加到对应角色

# 4. git commit + git push
ssh jing@100.110.41.83 'cd /tmp/cm-clone && git add -A && git commit -m "add: <name>" && git push'

# 5. www 5 分钟内自动同步，团队浏览页立即看到
# 6. 已装老 plugin 的成员第二天 04:00 自动拉新版
# 7. 想装新 plugin 的成员主动跑 -p <name>
```

## marketplace.json 加 skill 的字段模板

```json
{
  "name": "skill-name",
  "source": "./plugins/skill-name",
  "version": "1.0.0",
  "category": "marketing",
  "title": "中文显示标题",
  "description": "一句话简介",
  "feats": ["亮点 1", "亮点 2", "亮点 3"],
  "badge": "NEW",
  "updatedAt": "2026-05-02",
  "tags": ["marketing"]
}
```

可用 category：`marketing` / `engineering` / `sales` / `ops` / `internal`

## 下次继续：Windows 支持

### 已请 Windows 同事跑的命令（等回复）

```powershell
@(
  "$env:APPDATA\Claude-3p",
  "$env:LOCALAPPDATA\Claude-3p",
  "$env:APPDATA\Claude",
  "$env:LOCALAPPDATA\AnthropicClaude"
) | ForEach-Object {
  if (Test-Path $_) {
    Write-Host "FOUND: $_" -ForegroundColor Green
    Get-ChildItem $_ -Directory -ErrorAction SilentlyContinue | Select-Object Name, FullName | Format-Table -AutoSize
  } else {
    Write-Host "NOT FOUND: $_" -ForegroundColor Gray
  }
}
Get-ChildItem -Recurse -Filter "cowork_plugins" "$env:APPDATA","$env:LOCALAPPDATA" -ErrorAction SilentlyContinue 2>$null | Select-Object FullName
```

### 拿到路径后要写的 install.ps1

预期框架（路径占位待填）：

```powershell
param(
    [string]$Profile,
    [string[]]$Plugin,
    [string[]]$Uninstall,
    [switch]$List,
    [switch]$Sync,
    [switch]$Browse
)

$REPO_URL = "https://gitea.jamesgpone.win/evertac/cowork-marketplace.git"
$MARKETPLACE_NAME = "evertac-cowork"

# 1. 路径自动发现 — 等 Windows 同事确认后填 ↓
$COWORK_BASE = "$env:APPDATA\Claude-3p\local-agent-mode-sessions"  # 推测
# ...

# 2. git clone/pull marketplace 仓库
# 3. 解析参数
# 4. 写 3 个 JSON
# 5. 注册任务计划程序每天 04:00 跑 sync
#    使用 Register-ScheduledTask 或 schtasks /create /tn ...
# 6. 输出结果
```

调用方式：
```powershell
iwr -UseBasicParsing https://marketplace.jamesgpone.win/install.ps1 | iex
# 或带参数（用 scriptblock 包一层）
& ([scriptblock]::Create((iwr -UseBasicParsing https://marketplace.jamesgpone.win/install.ps1).Content)) -Profile marketing
```

### Windows 版还要做

- `marketplace.html` 顶部命令框提供 PowerShell 版命令（系统检测 / 默认显示两套）
- `install.ps1` 部署到 Mac mini www 目录，让 `https://marketplace.jamesgpone.win/install.ps1` 可访问
- 任务计划程序的 XML 定义（每天 04:00 跑 sync）

## 重要技术决策（已落定，不要再讨论）

1. **不要再纠结 "Cowork UI 内显示自定义 marketplace"**——已用代码确认 `listRemotePluginsPage` 只读 Anthropic 服务端，本地 directory marketplace 永远不会出现在 "Browse plugins" UI 里。所以做了外部 catalog 网页 + 文件注入的组合方案。

2. **不要用 GitHub**——中国访问受限，已自托管 Gitea on Mac mini。

3. **不要用 Docker**——Mac mini 内存紧张（24GB 已用 23GB），用原生 Gitea binary（仅 ~150MB）。

4. **不要修改 Cowork app.asar**——违反 ToS 风险，且每次 Cowork 更新失效。

5. **不要试图打开 GrowthBook gate**（`claudeai_cowork_backend_marketplaces` flag 720735283）——这是 Anthropic 服务端控制的，绕过等于黑客行为，且即使开了 gate，UI 还是只读 Anthropic 后端的 org marketplaces。

6. **设计风格采用了 Anthropic 官方 Design 包**——暖色 #f0eee9 / 朱红 #c96442 / Inter+Instrument Serif+JetBrains Mono 三字体。不要换。

## 调试用 access token

Mac mini 上 Gitea 管理员 token（用于 API 操作）：
```
TOKEN=88df4932d70e05931aaf4dd984b26294ab4f28a6
```
（仅本机访问，写在脚本里就够了）

## 已知问题

- macOS 系统 keychain 偶尔会报 `failed to store: -25308` warning，git push 时打印但**不影响功能**，可忽略
- 初次跑 install.sh 时如果用户的本地 DNS 缓存还没刷新到 marketplace.jamesgpone.win 的 CNAME，会失败一次。等几分钟再跑就好

## 下次接续要做的事（按优先级）

1. **拿到 Windows 同事查的路径** → 写 install.ps1
2. **测 install.ps1** 在至少一个 Windows 团队成员机器
3. **更新 marketplace.html** 让命令框根据浏览器 OS 自动展示 bash 或 PowerShell 命令
4. **部署 install.ps1 到 www** 让 `https://marketplace.jamesgpone.win/install.ps1` 可访问
5. （之后）把现有 pma_training（在 PMA MCP 服务里的）迁成独立 skill 加到 marketplace
6. （之后）写更详细的团队入门 README
