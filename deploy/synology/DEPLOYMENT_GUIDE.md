# PMA 群晖 NAS 部署指南

本指南适用于将 PMA 系统部署到群晖 NAS（DS920+ 或类似型号）。

## 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 群晖型号 | DS220+ 及以上 | DS920+ |
| 内存 | 4GB | 8GB |
| 存储空间 | 10GB | 50GB+ |
| Docker | Container Manager | 最新版本 |

## 部署步骤

### 步骤 1：准备群晖环境

#### 1.1 安装 Container Manager

1. 打开 **套件中心**
2. 搜索 **Container Manager**（或 Docker）
3. 点击安装

#### 1.2 创建共享文件夹

在 **控制面板 → 共享文件夹** 中创建：

```
/docker/pma          # PMA 部署文件
/pma-files           # 会议录音存储（WebDAV）
```

#### 1.3 启用 WebDAV（用于会议录音存储）

1. **控制面板 → 文件服务 → WebDAV**
2. 勾选「启用 WebDAV」
3. HTTPS 端口设为 `5006`
4. 点击「应用」

#### 1.4 创建 WebDAV 用户（推荐）

1. **控制面板 → 用户与群组**
2. 创建用户 `pma-storage`
3. 设置密码
4. 授予 `/pma-files` 文件夹读写权限

---

### 步骤 2：上传部署文件

#### 2.1 通过 File Station 上传

将以下文件上传到 `/docker/pma/`：

```
/docker/pma/
├── docker-compose.yml
├── .env                    # 从 .env.example 复制并修改
├── Dockerfile              # 项目根目录的 Dockerfile
├── requirements.txt
├── app/                    # 整个 app 目录
├── migrations/             # 数据库迁移文件
├── config.py
├── wsgi.py
└── run.py
```

#### 2.2 或通过 Git 克隆（需要 SSH）

```bash
ssh admin@192.168.1.2
cd /volume1/docker
git clone https://github.com/your-repo/pma.git
cd pma
```

---

### 步骤 3：配置环境变量

#### 3.1 创建 .env 文件

```bash
cd /volume1/docker/pma/deploy/synology
cp .env.example .env
```

#### 3.2 编辑 .env 文件

```bash
# 必须修改的配置
POSTGRES_PASSWORD=你的强密码
SECRET_KEY=随机字符串至少32位
SYNOLOGY_WEBDAV_PASSWORD=WebDAV用户密码

# 可选配置
OPENAI_API_KEY=sk-xxxxx    # 会议纪要功能需要
```

---

### 步骤 4：构建并启动

#### 4.1 通过 SSH 命令行

```bash
cd /volume1/docker/pma/deploy/synology

# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 4.2 通过 Container Manager 界面

1. 打开 **Container Manager**
2. 进入 **项目** 标签
3. 点击 **创建**
4. 选择 `/docker/pma/deploy/synology/docker-compose.yml`
5. 点击 **构建** 并 **启动**

---

### 步骤 5：初始化数据库

首次部署需要初始化数据库：

```bash
# 进入 PMA 容器
docker exec -it pma-app bash

# 初始化数据库
flask db upgrade

# 退出容器
exit
```

---

### 步骤 6：配置外网访问

#### 方案 A：直接端口映射（有公网 IP）

1. 进入 **路由器管理界面**
2. 设置端口转发：
   - 外部端口：`5001`（或其他）
   - 内部 IP：`192.168.1.2`（群晖 IP）
   - 内部端口：`5001`

3. 访问地址：`http://128.106.150.105:5001`

#### 方案 B：使用群晖反向代理 + HTTPS

1. **控制面板 → 登录门户 → 高级 → 反向代理**
2. 创建规则：
   - 来源：HTTPS, 端口 443, 主机名 `pma.yourdomain.com`
   - 目的地：HTTP, 端口 5001, 127.0.0.1

3. 配置 DDNS 或域名解析

---

## 常用命令

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f pma
docker-compose logs -f postgres

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新应用
git pull
docker-compose build
docker-compose up -d

# 备份数据库
docker exec pma-postgres pg_dump -U pma pma > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i pma-postgres psql -U pma pma < backup.sql
```

---

## 数据迁移（从 Render/Supabase）

如果你要从现有的云端环境迁移数据：

### 1. 导出云端数据库

```bash
# Supabase 数据库导出
pg_dump "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres" > cloud_backup.sql
```

### 2. 导入到群晖 PostgreSQL

```bash
# 上传 backup.sql 到群晖
scp cloud_backup.sql admin@192.168.1.2:/volume1/docker/pma/

# 导入数据
docker exec -i pma-postgres psql -U pma pma < /volume1/docker/pma/cloud_backup.sql
```

---

## 故障排除

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs --tail=100 pma

# 检查端口占用
netstat -tlnp | grep 5001
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 容器状态
docker-compose ps postgres

# 测试数据库连接
docker exec pma-postgres pg_isready -U pma
```

### 内存不足

```bash
# 查看内存使用
docker stats

# 如果内存不足，可以调整 docker-compose.yml 中的内存限制
# 或考虑升级群晖内存到 8GB
```

### WebDAV 连接失败

```bash
# 测试 WebDAV 连接
curl -k -u pma-storage:password https://192.168.1.2:5006/pma-files/

# 检查用户权限
# 确保 pma-storage 用户有 /pma-files 的读写权限
```

---

## 性能优化建议

### 4GB 内存优化

1. **减少 Worker 数量**：在 Dockerfile 中将 `--workers 2` 改为 `--workers 1`
2. **限制 PostgreSQL 内存**：docker-compose.yml 中已设置 512M 限制
3. **关闭不必要的群晖套件**：释放更多内存给 Docker

### 升级到 8GB 内存后

可以适当放宽内存限制：

```yaml
# docker-compose.yml
pma:
  deploy:
    resources:
      limits:
        memory: 1G

postgres:
  deploy:
    resources:
      limits:
        memory: 768M
```

---

## 安全建议

1. **修改默认密码**：务必修改 PostgreSQL 和 SECRET_KEY
2. **启用 HTTPS**：使用群晖反向代理配置 SSL
3. **限制端口访问**：只开放必要端口
4. **定期备份**：设置定时任务备份数据库
5. **更新维护**：定期更新 Docker 镜像和应用代码

---

## 更新日志

- **2026-01-11**：初始版本，支持 DS920+ 部署
