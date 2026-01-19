# Synology NAS Access Guide

PMA Synology NAS deployment access information.

## Quick Access

| Service | URL |
|---------|-----|
| **PMA Website** | https://garbage-lottery-hanging-biological.trycloudflare.com |
| **SSH Tunnel** | penalties-requested-bridge-gif.trycloudflare.com |
| **WebDAV** | https://medicine-maiden-concerts-interpreted.trycloudflare.com |
| **DSM** | https://structured-void-morgan-printing.trycloudflare.com |

---

## PMA Website Access

### External Access (via Cloudflare Tunnel)
```
https://garbage-lottery-hanging-biological.trycloudflare.com
```

### Internal Access (LAN)
```
http://192.168.1.2:5002
```

---

## SSH Access

### One-Click Connect (Recommended)

From PMA project root directory:
```bash
./ssh-nas.sh
```

If tunnel address changed:
```bash
./ssh-nas.sh new-address.trycloudflare.com
```

### Manual External Access (via Cloudflare Tunnel)

**Step 1: Start the proxy (keep running)**
```bash
cloudflared access tcp --hostname penalties-requested-bridge-gif.trycloudflare.com --url localhost:2222
```

**Step 2: Connect via SSH (new terminal)**
```bash
ssh -p 2222 admin@localhost
```

### Internal Access (LAN)
```bash
ssh admin@192.168.1.2
```

---

## SSH Passwordless Login (Already Configured)

SSH 密钥免密登录已配置完成，内网和外网均可免密登录。

### Configuration Details

| Item | Value |
|------|-------|
| Local Public Key | `~/.ssh/id_rsa.pub` |
| NAS Authorized Keys | `/var/services/homes/admin/.ssh/authorized_keys` |
| Sudo Passwordless | `/etc/sudoers.d/admin` |

### How It Works

1. **内网免密登录**
```bash
ssh admin@192.168.1.2
```

2. **外网免密登录**
```bash
./ssh-nas.sh
# 或手动
cloudflared access tcp --hostname penalties-requested-bridge-gif.trycloudflare.com --url localhost:2222 &
ssh -p 2222 admin@localhost
```

3. **远程执行命令（需要设置 PATH）**
```bash
# 内网
ssh admin@192.168.1.2 "sudo sh -c 'export PATH=/usr/local/bin:\$PATH && docker ps'"

# 外网（先启动代理）
ssh -p 2222 admin@localhost "sudo sh -c 'export PATH=/usr/local/bin:\$PATH && docker ps'"
```

### Reconfigure (If Needed)

如果需要重新配置免密登录（如更换电脑）：

```bash
# 1. 生成新密钥（如果没有）
ssh-keygen -t rsa -b 4096

# 2. 复制公钥到 NAS（需要密码）
cat ~/.ssh/id_rsa.pub | ssh admin@192.168.1.2 "sudo sh -c 'cat >> /var/services/homes/admin/.ssh/authorized_keys'"

# 3. 修复 homes 目录权限（如遇问题）
ssh admin@192.168.1.2 "echo 'PASSWORD' | sudo -S chmod 755 /var/services/homes/"
```

---

## Synology DSM Access

### Internal Access (LAN)
```
http://192.168.1.2:5000
```

---

## Container Status

Check running containers:
```bash
sudo docker ps
```

Expected containers:
- `pma-app` - PMA application (port 5002)
- `pma-postgres` - PostgreSQL database
- `cloudflared` - HTTP tunnel for PMA website
- `cloudflared-ssh` - SSH tunnel

---

## Tunnel Address Update

**Important:** Quick Tunnel addresses change when containers restart.

To get new addresses after restart:
```bash
# SSH tunnel address
sudo docker logs cloudflared-ssh 2>&1 | grep trycloudflare

# HTTP tunnel address
sudo docker logs cloudflared 2>&1 | grep trycloudflare
```

### Restart SSH Tunnel (on Synology)

```bash
sudo docker stop cloudflared-ssh
sudo docker rm cloudflared-ssh

sudo docker run -d --name cloudflared-ssh \
  --restart unless-stopped \
  cloudflare/cloudflared:latest \
  tunnel --no-autoupdate --url tcp://192.168.1.2:22

# Wait and get new address
sleep 8
sudo docker logs cloudflared-ssh 2>&1 | grep trycloudflare
```

---

## Useful Commands

### View PMA logs
```bash
cd /volume1/docker/pma/deploy/synology
sudo docker-compose logs -f pma
```

### Restart PMA
```bash
cd /volume1/docker/pma/deploy/synology
sudo docker-compose restart pma
```

### Database backup
```bash
sudo docker exec pma-postgres pg_dump -U pma pma > backup_$(date +%Y%m%d).sql
```

---

## Network Information

| Item | Value |
|------|-------|
| NAS IP (LAN) | 192.168.1.2 |
| PMA Port | 5002 |
| PostgreSQL Port | 5432 (internal) |
| SSH Port | 22 |
| DSM Port | 5000 |
| WebDAV HTTPS Port | 5006 |
| WebDAV HTTP Port | 5005 |

---

## WebDAV File Storage

### Internal Access (LAN)
```
http://192.168.1.2:5005/pma-files/
```

### External Access (via Cloudflare Tunnel)
```
https://medicine-maiden-concerts-interpreted.trycloudflare.com/pma-files/
```

### Test Connection
```bash
# Internal
curl -X PROPFIND -H "Depth: 1" -u pma-storage:PASSWORD http://192.168.1.2:5005/pma-files/

# External
curl -X PROPFIND -H "Depth: 1" -u pma-storage:PASSWORD https://medicine-maiden-concerts-interpreted.trycloudflare.com/pma-files/
```

### Restart WebDAV Tunnel (on Synology)
```bash
sudo docker stop cloudflared-webdav
sudo docker rm cloudflared-webdav

sudo docker run -d --name cloudflared-webdav \
  --restart unless-stopped \
  cloudflare/cloudflared:latest \
  tunnel --no-autoupdate --url http://192.168.1.2:5005

# Wait and get new address
sleep 8
sudo docker logs cloudflared-webdav 2>&1 | grep trycloudflare
```

---

## Credentials

| Service | Username | Note |
|---------|----------|------|
| SSH | admin | Synology admin account |
| PostgreSQL | pma | Database user |
| WebDAV | pma-storage | File storage user |

---

*Last Updated: 2026-01-19*
