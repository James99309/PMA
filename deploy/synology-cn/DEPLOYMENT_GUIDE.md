# PMA 中国 DS925+ 部署指南

从新加坡 NAS 迁移到中国 DS925+ 的完整操作手册。

## 目录

- [环境概览](#环境概览)
- [阶段一：DS925+ 环境准备](#阶段一ds925-环境准备)
- [阶段二：预构建镜像](#阶段二预构建镜像在-mac-上)
- [阶段三：部署应用](#阶段三部署应用)
- [阶段四：数据迁移](#阶段四数据迁移周末执行)
- [阶段五：外网访问 Cloudflare Tunnel](#阶段五外网访问-cloudflare-tunnel)
- [阶段五（备选）：外网访问 FRP](#阶段五备选外网访问-frp)
- [阶段六：验证](#阶段六验证)
- [日常维护](#日常维护)
- [回滚计划](#回滚计划)
- [故障排除](#故障排除)

---

## 环境概览

| 项目 | 源（新加坡） | 目标（中国） |
|------|------------|------------|
| 设备 | Synology NAS | DS925+ (DSM 7.3.2) |
| 内网 IP | 192.168.1.2 | 192.168.31.91 |
| SSH 端口 | 22 (外网通过 cloudflared) | 72 |
| SSH 用户 | admin | james.sh |
| PMA 端口 | 5002 | 5001 |
| 数据库 | PostgreSQL 17 (Docker) | PostgreSQL 17 (Docker) |
| 外网 | Cloudflare Tunnel | Cloudflare Tunnel（推荐）/ FRP + 国内 VPS（备选） |
| 时区 | Asia/Singapore | Asia/Shanghai |

### 文件清单

```
deploy/synology-cn/
├── Dockerfile              # 中国优化 Dockerfile（清华/阿里云镜像源）
├── docker-compose.yml      # Docker Compose（含 Cloudflare Tunnel + FRP 客户端）
├── .env.example            # 环境变量模板
├── frpc.toml               # FRP 客户端配置
├── frps.toml               # FRP 服务端配置（部署到 VPS）
├── build-and-transfer.sh   # Mac 上构建镜像并传输
├── init-deploy.sh          # DS925+ 首次部署
├── update.sh               # DS925+ 一键更新
├── remote-update.sh        # 从 Mac 远程更新
├── migrate-data.sh         # 数据迁移工具
├── setup-vps.sh            # VPS 一键部署 FRP+Nginx+HTTPS
└── DEPLOYMENT_GUIDE.md     # 本文档
```

---

## 阶段一：DS925+ 环境准备

### 1.1 安装 Container Manager

1. DSM 套件中心 → 搜索 **Container Manager** → 安装

### 1.2 配置 Docker 镜像加速（中国网络）

SSH 连接到 DS925+：
```bash
ssh -p 72 james.sh@192.168.31.91
```

编辑 Docker 配置：
```bash
sudo vi /etc/docker/daemon.json
```

内容：
```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
```

重启 Docker：
```bash
sudo synoservicectl --restart pkgctl-ContainerManager
```

### 1.3 创建共享文件夹

在 DSM **控制面板 → 共享文件夹** 中创建：
- `/docker/pma` — 部署文件
- `/pma-files` — WebDAV 文件存储

### 1.4 启用 WebDAV 服务

1. **控制面板 → 文件服务 → WebDAV**
2. 启用 WebDAV，HTTP 端口 `5005`，HTTPS 端口 `5006`
3. 创建用户 `pma-storage`，授权 `/pma-files` 读写权限

### 1.5 内存建议

| 配置 | 4GB 内存 | 8GB+ 内存（推荐） |
|------|---------|-----------------|
| PostgreSQL | 512M 限制 | 768M 限制 |
| PMA App | 768M 限制 | 1G 限制 |
| Workers | 2 | 2-3 |
| 15+ 用户 | 高峰期可能 OOM | 充裕 |

DS925+ 支持 DDR5 SO-DIMM，加装 4GB 约 100-200 元，**强烈建议升级到 8GB+**。

---

## 阶段二：预构建镜像（在 Mac 上）

中国无法直接访问 Docker Hub，需在 Mac 上预构建镜像传输到 NAS。

### 方法一：一键脚本

```bash
cd /Users/nijie/Documents/PMA
bash deploy/synology-cn/build-and-transfer.sh
```

脚本自动完成：
1. 构建 `pma-app:latest` (linux/amd64)
2. 拉取 `postgres:17-alpine` (linux/amd64)
3. 导出为 `pma-images.tar.gz`
4. SCP 传输到 DS925+

### 方法二：手动操作

```bash
# 构建 PMA 镜像
cd /Users/nijie/Documents/PMA
docker buildx build --platform linux/amd64 -t pma-app:latest -f deploy/synology-cn/Dockerfile --load .

# 拉取 PostgreSQL 镜像
docker pull --platform linux/amd64 postgres:17-alpine

# 导出
docker save pma-app:latest postgres:17-alpine | gzip > pma-images.tar.gz

# 传输
scp -P 72 pma-images.tar.gz james.sh@192.168.31.91:/volume1/docker/

# 在 NAS 上加载
ssh -p 72 james.sh@192.168.31.91 "gunzip -c /volume1/docker/pma-images.tar.gz | sudo docker load"
```

---

## 阶段三：部署应用

### 3.1 上传代码到 NAS

```bash
# 从 Mac 同步代码（排除不需要的文件）
rsync -avz --delete \
    --exclude '.git' --exclude 'venv' --exclude '__pycache__' \
    --exclude '.env' --exclude '.env.*' --exclude 'node_modules' \
    --exclude 'logs/' --exclude 'cloud_db_backups/' --exclude 'data/' \
    -e "ssh -p 72" \
    /Users/nijie/Documents/PMA/ \
    james.sh@192.168.31.91:/volume1/docker/pma/
```

### 3.2 配置环境变量

```bash
ssh -p 72 james.sh@192.168.31.91
cd /volume1/docker/pma/deploy/synology-cn
cp .env.example .env
vi .env  # 修改必需配置
```

必须修改：
- `POSTGRES_PASSWORD` — 数据库强密码
- `SECRET_KEY` — 随机字符串（至少32位）
- `SYNOLOGY_WEBDAV_PASSWORD` — WebDAV 用户密码

### 3.3 首次部署

```bash
sudo bash init-deploy.sh
```

或手动启动：
```bash
cd /volume1/docker/pma/deploy/synology-cn
sudo docker-compose up -d postgres pma
```

### 3.4 验证

```bash
# 检查容器状态
sudo docker-compose ps

# 查看日志
sudo docker-compose logs -f pma

# 测试访问
curl http://192.168.31.91:5001/
```

---

## 阶段四：数据迁移（周末执行）

### 迁移前准备

1. 通知用户停机维护
2. 在新加坡 NAS 上将 PMA 设为只读或停止写入
3. 确保 DS925+ 上容器已正常运行

### 一键迁移

在 Mac 上执行：

```bash
cd /Users/nijie/Documents/PMA
bash deploy/synology-cn/migrate-data.sh all
```

### 分步执行

```bash
# Step 1: 从新加坡导出
bash deploy/synology-cn/migrate-data.sh export

# Step 2: 传输到 DS925+
bash deploy/synology-cn/migrate-data.sh transfer

# Step 3: 在 DS925+ 上导入
bash deploy/synology-cn/migrate-data.sh import

# Step 4: 验证数据
bash deploy/synology-cn/migrate-data.sh verify
```

### 迁移后检查

- 对比源和目标的各表行数
- 登录 PMA 检查关键数据
- 测试各功能模块

---

## 阶段五：外网访问 Cloudflare Tunnel

零成本、免备案的外网访问方案。通过 Cloudflare Tunnel 将 PMA 暴露到 `pma.jamesgpone.win`。

### 5.1 创建 Cloudflare Tunnel

1. 登录 [Cloudflare Zero Trust](https://one.dash.cloudflare.com)
2. 进入 **Networks → Tunnels**
3. 点击 **Create a tunnel**，选择 **Cloudflared** 类型
4. 命名为 `pma-ds925`（或其他名称）
5. 记录生成的 **Tunnel Token**
6. 配置 Public Hostname：
   - **Subdomain**: `pma`
   - **Domain**: `jamesgpone.win`
   - **Service**: `http://pma-app:5000`（容器内部地址）

### 5.2 配置 DS925+ 环境变量

```bash
ssh -p 72 james.sh@192.168.31.91
cd /volume1/docker/pma/deploy/synology-cn
vi .env
```

添加：
```bash
# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=<从 Cloudflare Dashboard 获取的 token>

# 外部访问地址
EXTERNAL_URL=https://pma.jamesgpone.win
```

### 5.3 启动 cloudflared 容器

```bash
cd /volume1/docker/pma/deploy/synology-cn

# 启动 cloudflared（docker-compose.yml 中已配置）
sudo docker-compose up -d cloudflared

# 查看日志确认连接成功
sudo docker-compose logs -f cloudflared
```

日志中出现 `Registered tunnel connection` 即表示连接成功。

### 5.4 验证外网访问

```bash
# 测试访问（返回 200 即成功）
curl -s -o /dev/null -w '%{http_code}' https://pma.jamesgpone.win/auth/login
```

### 注意事项

- cloudflared 镜像约 30MB，运行内存约 30-50MB
- Cloudflare 自动提供 HTTPS，无需配置证书
- 国内访问 Cloudflare 速度可能偏慢，如不满意可切换到 FRP 方案
- cloudflared 容器在 `pma-network` 中，通过容器名 `pma-app:5000` 直接访问 PMA

---

## 阶段五（备选）：外网访问 FRP

### 5.1 购买 VPS

推荐：
- 腾讯云 / 阿里云轻量应用服务器
- 配置：1核2G，5Mbps 带宽
- 系统：Ubuntu 22.04
- 年费约 300-600 元

### 5.2 域名配置

将域名解析到 VPS IP：
```
pma.yourdomain.com → A记录 → VPS公网IP
```

### 5.3 VPS 一键部署

SSH 到 VPS 执行：
```bash
# 上传脚本
scp deploy/synology-cn/setup-vps.sh root@YOUR_VPS_IP:/root/

# 修改配置后执行
ssh root@YOUR_VPS_IP

# 编辑配置
export DOMAIN="pma.yourdomain.com"
export FRP_TOKEN="your-secure-token"
export CERT_EMAIL="your-email@example.com"

# 运行部署
bash setup-vps.sh
```

自动完成：
1. 安装 FRP 服务端 + systemd 服务
2. 配置 Nginx 反向代理
3. 申请 Let's Encrypt HTTPS 证书
4. 配置防火墙规则

### 5.4 DS925+ 配置 FRP 客户端

编辑 FRP 客户端配置：
```bash
ssh -p 72 james.sh@192.168.31.91
cd /volume1/docker/pma/deploy/synology-cn
vi frpc.toml
```

修改：
```toml
server_addr = "YOUR_VPS_IP"   # 改为 VPS 公网 IP
auth.token = "your-secure-token"  # 与 VPS 端一致
```

启动 FRP 客户端容器：
```bash
sudo docker-compose --profile frp up -d frpc
```

### 5.5 验证外网访问

```bash
curl https://pma.yourdomain.com
```

---

## 阶段六：验证

### 验证清单

- [ ] `docker-compose ps` 所有容器运行正常
- [ ] 数据库表数和行数与源一致
- [ ] 用户登录/登出正常
- [ ] 客户 CRUD 正常
- [ ] 项目 CRUD 正常
- [ ] 报价 CRUD 正常
- [ ] PDF 导出正常 (WeasyPrint)
- [ ] 审批流程正常
- [ ] 文件上传/下载正常 (WebDAV)
- [ ] 中英文切换正常
- [ ] 外网 Cloudflare Tunnel 访问稳定（`https://pma.jamesgpone.win`）
- [ ] 连续运行 24 小时无异常

---

## 日常维护

### 更新应用

**方法一：在 NAS 上执行**
```bash
cd /volume1/docker/pma/deploy/synology-cn
sudo bash update.sh
```

**方法二：从 Mac 远程更新**
```bash
# 仅同步代码并重启
bash deploy/synology-cn/remote-update.sh

# 重新构建镜像并更新
bash deploy/synology-cn/remote-update.sh --rebuild
```

### 数据库备份

```bash
# 手动备份
sudo docker exec pma-postgres pg_dump -U pma pma_synology > backup_$(date +%Y%m%d).sql

# Custom 格式（推荐，支持并行恢复）
sudo docker exec pma-postgres pg_dump -U pma -Fc pma_synology > backup_$(date +%Y%m%d).dump
```

### 查看日志

```bash
# PMA 应用日志
sudo docker-compose logs -f pma

# PostgreSQL 日志
sudo docker-compose logs -f postgres

# Cloudflare Tunnel 日志
sudo docker-compose logs -f cloudflared

# FRP 客户端日志
sudo docker-compose logs -f frpc

# 内存使用
sudo docker stats --no-stream
```

### 重启服务

```bash
cd /volume1/docker/pma/deploy/synology-cn

# 重启所有
sudo docker-compose restart

# 仅重启 PMA
sudo docker-compose restart pma

# 停止所有
sudo docker-compose down

# 启动所有
sudo docker-compose up -d postgres pma cloudflared
sudo docker-compose --profile frp up -d frpc  # 如使用 FRP（备选方案）
```

---

## 回滚计划

### 快速回滚（5分钟内）

1. 新加坡 NAS 保持运行至少 **30 天**
2. 切换前旧系统设为只读
3. 如 DS925+ 部署失败：
   - 停止 DS925+ 的 PMA
   - 恢复新加坡 NAS 的写入权限
   - DNS/FRP 切回新加坡

### 数据保险

- 新加坡 NAS 数据库完整保留
- Supabase 云端始终保留最新备份
- 本地 Mac 保留迁移时的备份文件

---

## 故障排除

### Docker Hub 无法访问

已通过 `build-and-transfer.sh` 在 Mac 上预构建镜像解决。如需在 NAS 上直接拉取，配置镜像加速：
```json
// /etc/docker/daemon.json
{
  "registry-mirrors": ["https://docker.1ms.run"]
}
```

### pip 安装超时

Dockerfile 已配置清华镜像源。如仍超时，检查 NAS 网络。

### 内存不足 (OOM)

```bash
# 查看内存使用
sudo docker stats --no-stream

# 临时方案：减少 Worker
# 在 docker-compose.yml 的 pma 服务中修改 CMD

# 长期方案：升级内存到 8GB+
```

### Cloudflare Tunnel 连接失败

```bash
# 检查日志
sudo docker-compose logs -f cloudflared

# 常见原因：
# 1. CLOUDFLARE_TUNNEL_TOKEN 未设置或错误 → 检查 .env 文件
# 2. DNS 未生效 → 在 Cloudflare Dashboard 检查 Tunnel 状态
# 3. 网络问题 → 确认 DS925+ 可访问外网

# 重启 cloudflared
sudo docker-compose restart cloudflared
```

### FRP 连接不稳定

```bash
# 检查 FRP 客户端日志
sudo docker-compose logs -f frpc

# 检查 VPS 端 FRP 服务
ssh root@YOUR_VPS_IP
systemctl status frps
tail -f /var/log/frps.log

# 重启 FRP 客户端
sudo docker-compose --profile frp restart frpc
```

### WebDAV 连接失败

```bash
# 测试 WebDAV（从 NAS 本机）
curl -u pma-storage:PASSWORD http://192.168.31.91:5005/pma-files/

# 检查 WebDAV 服务
# DSM → 控制面板 → 文件服务 → WebDAV
```

### 时区问题

数据库存储 UTC 时间不受影响。PMA 应用已配置 `TZ=Asia/Shanghai`，显示时自动转换。

---

*创建日期: 2026-01-30*
