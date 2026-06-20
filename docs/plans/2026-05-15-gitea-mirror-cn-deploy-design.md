# CN NAS 经 Mac mini Gitea 镜像部署 — 设计文档

- 日期: 2026-05-15
- 状态: 设计已验证，待用户实施
- 背景: CN NAS 从 GitHub 拉取长期不稳定（国内网络），部署慢/失败。Mac mini 在同一 Tailnet 且可正常访问 GitHub，已装 Gitea。

## 1. 目标与非目标

**目标**
- CN NAS 部署不再直连 GitHub，改从 Mac mini Gitea（Tailscale 内网）拉取，秒级、稳定
- dev 工作流零改动（照旧 `git push origin` 到 GitHub）
- 流程固化为版本化脚本 + skill，杜绝 AI 即兴 SSH 拼命令

**非目标**
- 不改 SG NAS（新加坡连 GitHub 正常，继续直连 GitHub）
- 不把 Mac mini Gitea 公开（仅内部，走 SSH）
- 不替代 GitHub 作为真源（GitHub 仍是唯一 source of truth + 云备份）

## 2. 架构与数据流

```
dev Mac ──git push origin──▶ GitHub James99309/PMA (公开, 唯一真源)
                                  │
                    Mac mini Gitea pull-mirror
                    (每 10min 自动 fetch; Mac mini 公网正常)
                                  ▼
              Mac mini Gitea  admin/pma-mirror.git  (新建专用镜像仓, 内部, 仅 SSH)
                                  │
        CN NAS ──Tailscale ssh://git@100.110.41.83:2222──▶ 拉取
                                  │
                  update.sh: git fetch origin / reset --hard origin/main
```

已验证事实（2026-05-15）：
- GitHub PMA 公开（HTTP 200）→ Gitea 镜像无需 GitHub token
- Mac mini Gitea = Homebrew 安装，进程 `jing`，config `/opt/homebrew/var/gitea/custom/conf/app.ini`，repos 目录 `/opt/homebrew/var/gitea/repos/admin/`
- ⚠️ **已存在的 `admin/evertac-pma.git` 非空**（1442 commit、382M、有 `refs/heads/feature/mobile-api`，无 `main`，疑似用户既有内部推送仓）→ **绝不删除/改动它**；改为新建专用镜像仓 `admin/pma-mirror`，零破坏
- Gitea admin 用户 = `admin`（james99309@hotmail.com），创建 mirror/Deploy Key 需其 token 或 Web 登录
- CN NAS → Mac mini `100.110.41.83:2222` Tailscale **可达**
- CN NAS root 无 ed25519 key（需生成）
- CN NAS 当前 `origin` = `https://github.com/James99309/PMA.git`

## 3. 关键设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| 拓扑 | A: Gitea 做 GitHub pull-mirror | dev 零改动，GitHub 保真源，只动 CN 一台 |
| 同步机制 | Gitea 原生 pull-mirror，间隔 10min | 零脚本零维护；急用「Synchronize Now」手动触发 |
| 传输 | SSH deploy key，走已验证可达的 2222 | Gitea 不公开；钥匙一次性配；稳健通用 |
| update.sh 改动 | **不改逻辑**，仅一次性把 CN 本地 `origin` URL 改指 Gitea | SA/SG 本地 origin 仍 GitHub，自动不受影响，无需脚本分支 |
| 权限加固 | 保留本次已加的 `umask 022` + 目录 chmod 兜底 | 与本方案正交的独立修复，叠加生效 |
| 兜底 | CN 保留 `github` 为第二远程 | Mac mini/Gitea 宕机时可手动 `git fetch github && git reset --hard github/main` 应急 |

## 4. 交付物（固定，非即兴）

### 4.1 一次性 setup 脚本 — `deploy/setup-gitea-remote-cn.sh`
在 CN NAS 上以 root 跑一次，幂等：
1. CN NAS root 无 key 则生成 `~/.ssh/id_ed25519`（注释 `pma-cn-nas@gitea`）
2. 打印公钥，**暂停**提示用户去 Gitea 把它加为 `admin/pma-mirror` 的 **Deploy Key（只读）**
3. 用户确认后：`git remote rename origin github`（保留兜底）+ `git remote add origin ssh://git@100.110.41.83:2222/admin/pma-mirror.git`
4. `ssh -T -p 2222 git@100.110.41.83` 验证 key 通；`git fetch origin` 验证可拉
5. 打印 `git ls-remote origin main` 与期望 HEAD 对比，成功/失败明确退出码
- 回滚：`git remote remove origin && git remote rename github origin`（脚本带 `--rollback`）

### 4.2 Mac mini Gitea 镜像 — runbook（一次性，UI 为主）
🚫 **绝不删除既有 `admin/evertac-pma`（1442 commit，疑似用户内部推送仓）。新建独立镜像仓：**
1. Gitea Web（admin 登录）→ **+ New Migration**
2. 源 `https://github.com/James99309/PMA.git`，Owner `admin`，Repo Name **`pma-mirror`**
3. 勾 **This repository will be a mirror**；公开仓无需账密；建议设 Private
4. 仓库 Settings → Mirror → 间隔 `10m`（Gitea 默认 MIN_INTERVAL=10m，本机 app.ini 无 `[mirror]` 段=用默认，10m 直接可用，无需改 app.ini）
5. Settings → **Synchronize Now**，`git ls-remote ssh://git@100.110.41.83:2222/admin/pma-mirror.git refs/heads/main` 应出当前 GitHub HEAD（如 `6bc23a9e`）
- 可选脚本化：`gitea admin user generate-access-token --username admin ...` 造 token + `POST /api/v1/repos/migrate`（被 auto-mode gate，由用户手动跑或 Web 操作）

### 4.3 复用 — `deploy/synology-cn/update.sh`
**逻辑不变**。origin 一旦改指 Gitea，脚本透明从 Gitea 拉。本次已加的 `umask 022` 与目录 chmod 兜底保留。

### 4.4 Skill — `pma-deploy`（封装递归部署，杜绝即兴）
职责：把「部署 PMA 到 NAS」固化为可调流程，AI 只能调脚本不能自拟命令。
- 首次操作 AskUserQuestion 确认目标 NAS（沿用 pma-nas-access 安全规则）
- CN：①（可选）触发 Gitea Synchronize Now（API curl）② SSH 到 CN 跑 `update.sh` ③ 验证容器 healthy + 关键页 200
- SG：直接 SSH 跑 `deploy/synology-sa/update.sh`（仍 GitHub）
- 引用 pma-nas-access 取连接参数，不重复造连接逻辑
- 内置本次根因记忆引用：部署后扫 `find app -type d ! -perm -005`

## 5. 上线步骤（用户实施，全部可回滚）

0. **前置（必做）**：先解决 CN NAS 未提交的 APNS docker-compose 改动（见 §6 / §7 待办），否则步骤 3 的 `update.sh`(git reset --hard) 会抹掉它，iOS 推送当场失效
1. Mac mini：按 4.2 **新建** `admin/pma-mirror` migration mirror（10m）→ Synchronize Now → 验证 `git ls-remote .../pma-mirror.git refs/heads/main` 出当前 HEAD（**不动 evertac-pma**）
2. CN NAS：跑 `deploy/setup-gitea-remote-cn.sh`，按提示把 deploy key 加进 Gitea `admin/pma-mirror`（脚本只 `git fetch` 不 reset，不碰 APNS）
3. 验证：CN `git ls-remote origin main` 命中；解决 §0 后再跑 `update.sh` 确认容器 healthy
4. 固化：提交 setup 脚本 + update.sh 加固 + 新增 `pma-deploy` skill
5. 回滚（任意步）：`setup-gitea-remote-cn.sh --rollback` 一条命令恢复 origin=GitHub；Mac mini 侧删 `pma-mirror` 即可（evertac-pma 全程未动）

## 6. 风险与缓解

| 风险 | 缓解 |
|---|---|
| Mac mini 单点（宕则 CN 拉不到） | 保留 `github` 第二远程手动兜底；Mac mini 本就是测试宿主需保活 |
| 镜像滞后 ≤10min | 急用 Gitea Synchronize Now + 立即 update.sh；skill 内置该触发 |
| Gitea MIN_INTERVAL | 本机 app.ini 无 `[mirror]` 段=默认 10m，直接可用，无需改 |
| 误删 evertac-pma（1442 commit） | 已改方案：不删任何仓，新建独立 `pma-mirror`；全程零破坏 |
| deploy key 泄露 | 设只读 Deploy Key，scope 限该仓；Gitea 不公开 |
| 与权限加固耦合误判 | 文档明确二者正交；update.sh 加固独立保留 |
| update.sh 抹掉 CN APNS 配置 | §5 步骤 0 设为前置：先固化 APNS 再首次部署 |

## 7. 关联

- 权限漂移根因: memory `project-deploy-dir-perm-drift`
- CN NAS 部署约定: memory `feedback-nas-deployment`（代码在 /volume1/docker/pma，用 update.sh）
- 连接参数: skill `pma-nas-access`
- 待办（本方案外，已发现需单独处理）: CN NAS 未提交的 APNS docker-compose 改动会被下次 `git reset --hard` 抹掉
