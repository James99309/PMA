# Evertac Cowork Marketplace — Windows 端部署完成

**日期**: 2026-05-02
**目标**: 把已运行在 Mac 的 Cowork plugin marketplace 扩展到 Windows，团队两个 OS 都能一行命令安装/同步 skill。

---

## 最终成果

| 能力 | 状态 |
|---|---|
| Mac 一键安装（`bash <(curl …) -p NAME`） | ✅ 已上线 |
| Windows 一键安装（PowerShell scriptblock） | ✅ 已上线 |
| 网页 catalog 自动检测 OS、生成对应命令 | ✅ 已上线 |
| Mac LaunchAgent + Windows 任务计划程序，每天 04:00 自动同步 | ✅ 已上线 |
| PMA 首页底部加 Skills 商店入口 | ✅ 本地已改（待部署） |

**入口**: `https://marketplace.jamesgpone.win`

---

## Windows 部署过程踩到的 5 个坑

按发现顺序记录，**对未来 Windows 团队成员的环境差异有指导意义**。

### 1. PowerShell 5.1 NativeCommandError（隐式中止）

`$ErrorActionPreference = 'Stop'` + git 把进度信息写到 stderr → PS 5.1 把它当 terminating error，整个脚本静默退出。

**修法**: 全局用 `'Continue'`，靠 `$LASTEXITCODE` 判断 git 失败。

### 2. PS 5.1 默认用 ANSI/GBK 读 UTF-8 文件

`Get-Content $json -Raw | ConvertFrom-Json` 在 Windows 中文系统会把 UTF-8 当 GBK 解码，含中文的 marketplace.json 解析炸掉。

**修法**: 所有 Get-Content 显式 `-Encoding UTF8`。

### 3. Windows MAX_PATH 260 字符上限

Cowork 路径本身就深：`%LOCALAPPDATA%\Claude-3p\local-agent-mode-sessions\<UUID>\<UUID>\cowork_plugins\marketplaces\evertac-cowork\plugins\geo-article-writer\skills\geo-article-writer\templates\cn-structure.md` 直接超 260 字符，git checkout 报 "Filename too long"。

**修法**:
- 安装前先执行 `git config --global core.longpaths true`（已写进 install.ps1，所有未来用户自动启用）

### 4. `(irm $url).Content` 是 `$null`

PS 5.1 里 `Invoke-RestMethod` 直接返回 body 字符串，没有 `.Content` 属性。`(string).Content` = `$null` → `[scriptblock]::Create($null)` 创建空 scriptblock → `& {} -Plugin pma-daily` 静默退出 1 秒，**没任何报错**。

**修法**: 用 `iwr -UseBasicParsing $url` 配合 `.Content`（IWR 返回的是 response 对象）。install.ps1 内部模板和 marketplace.html 网页给团队复制的命令都已统一改成 iwr。

**这是最难发现的坑**——脚本启动后 1 秒内退出，无任何 console 输出，只能用 `Start-Transcript` 才能确认根本没执行。

### 5. PS 5.1 的 `Set-Content -Encoding UTF8` 加 BOM

写出来的 JSON 文件首字节是 `EF BB BF` UTF-8 BOM。Cowork 的 JSON parser 不接受 BOM —— 文件**能写、能读、可校验、字段完全正确**，但 Cowork **静默忽略**整个 plugin。这是这次最隐蔽的一个 bug。

**症状**：
- `installed_plugins.json` 里有 pma-daily ✅
- `cowork_settings.json` 里 enabled ✅
- plugin 文件夹和 `plugin.json` 都在磁盘上 ✅
- **Cowork 重启后仍只显示 anthropic 自带 3 个 skill** ❌

**修法**: `Save-Json` 函数改用 `[System.IO.File]::WriteAllText($path, $json, [System.Text.UTF8Encoding]::new($false))`，显式无 BOM。

**对比 Mac**: bash redirect 写文件天然无 BOM，所以 install.sh 不存在这个坑。

---

## 关键文件

| 文件 | 作用 | 部署位置 |
|---|---|---|
| `install.sh` | Mac 安装脚本 | `https://marketplace.jamesgpone.win/install.sh` |
| `install.ps1` | Windows 安装脚本（含上述 5 个修复） | `https://marketplace.jamesgpone.win/install.ps1` |
| `marketplace.html` | 网页 catalog（含 OS 切换 + 安装步骤指引） | `https://marketplace.jamesgpone.win/` |
| `.claude-plugin/marketplace.json` | plugin 清单 + profiles | Gitea repo |
| 计划任务 `EvertacCoworkMarketplaceSync` | Windows 每日 04:00 同步 | 用户机器 |
| LaunchAgent `com.evertac.cowork-marketplace-sync` | Mac 每日 04:00 同步 | 用户机器 |

---

## 给团队的安装方式

### Mac (Terminal)
```bash
bash <(curl -fsSL https://marketplace.jamesgpone.win/install.sh) -p pma-daily
```

### Windows (PowerShell)
首次需开一次脚本执行权限（管理员）：
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

然后：
```powershell
& ([scriptblock]::Create((iwr -UseBasicParsing 'https://marketplace.jamesgpone.win/install.ps1').Content)) -Plugin pma-daily
```

装完**彻底退出 Cowork**（任务栏右键 → 退出，或杀掉所有 `claude.exe` + `cowork-svc.exe` 进程）再重新打开。

---

## 待办

- [ ] PMA 首页底部入口部署到 CN NAS（commit + ssh update.sh）
- [ ] 把 install.ps1 push 到 Gitea（凭证问题，目前只在 Mac mini 直挂的 web 服务器上）
- [ ] marketplace.html 添加更多 plugin（pma-training v2 等待补 prompts_generated 修复后回归）

---

## 历史命令 / 调试遗物

调试期间用过的辅助脚本（已用完）：
- `/tmp/check-bom.ps1` — 验证 JSON 是否带 BOM
- `/tmp/check-clean.ps1` — 验证卸载是否干净
- `/tmp/safe-clean.ps1` — 安全清理 marketplace 目录
- 在 Windows 端 `C:\Users\james\` 下也留有这些 ps1 副本

可全部删除。
