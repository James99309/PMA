# Synology NAS Access Guide

PMA Synology NAS deployment access information.

## Quick Access

| Service | URL |
|---------|-----|
| **PMA Website** | https://garbage-lottery-hanging-biological.trycloudflare.com |
| **SSH Tunnel** | penalties-requested-bridge-gif.trycloudflare.com |

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
| WebDAV Port | 5006 |

---

## Credentials

| Service | Username | Note |
|---------|----------|------|
| SSH | admin | Synology admin account |
| PostgreSQL | pma | Database user |
| WebDAV | pma-storage | File storage user |

---

*Last Updated: 2026-01-12*
