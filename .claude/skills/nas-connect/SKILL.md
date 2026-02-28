---
name: nas-connect
description: "Connect to NAS servers (China SP8D or Singapore OVS) via Tailscale SSH. Use when: deploying code, checking logs, managing Docker containers, database operations, file management on NAS. Triggers: NAS, nas, deploy, server, container, docker logs, restart container, database backup on server."
user_invocable: true
---

# NAS Connect - Remote Server Management

Connect to PMA production NAS servers via Tailscale SSH for deployment, monitoring, and management tasks.

## Connection Configuration

### SG NAS (Singapore DS925+ / OVS)
- **SSH Alias**: `sg-nas`
- **Tailscale IP**: `100.87.155.40`
- **User**: `admin`
- **Port**: 22 (default)
- **Docker**: direct access (no sudo needed)
- **DB Container**: `pma-postgres`
- **DB Name**: `pma_sa`
- **DB User**: `pma`
- **PMA Container**: `pma-app`
- **Project Dir**: `/volume1/docker/pma`
- **Deploy Dir**: `/volume1/docker/pma/deploy/synology-sa`
- **External URL**: `https://sg-pma.jamesgpone.win`

### CN NAS (China DS925+ / SP8D)
- **SSH Alias**: `cn-nas`
- **Tailscale IP**: `100.118.231.15`
- **User**: `james.sh`
- **Port**: 72
- **Docker**: requires `sudo /usr/local/bin/docker`
- **DB Container**: `pma-postgres`
- **DB Name**: `pma_synology`
- **DB User**: `pma`
- **PMA Container**: `pma-app`
- **Project Dir**: `/volume1/docker/pma`
- **Deploy Dir**: `/volume1/docker/pma/deploy/synology-cn`
- **External URL**: `https://pma.jamesgpone.win`

## When Invoked

1. **Ask the user which NAS to connect to** using AskUserQuestion:
   - SG NAS (Singapore / OVS)
   - CN NAS (China / SP8D)
   - Both (execute on both servers)

2. **Verify connectivity** before executing any commands:
   ```bash
   ssh sg-nas 'echo ok' 2>&1    # for SG
   ssh cn-nas 'echo ok' 2>&1    # for CN
   ```

3. **Execute the requested task** on the selected NAS.

## Docker Command Patterns

### SG NAS (admin user, direct docker access)
```bash
# View containers
ssh sg-nas 'docker ps --format "table {{.Names}}\t{{.Status}}"'

# View logs
ssh sg-nas 'docker logs --tail=50 pma-app'

# Restart container
ssh sg-nas 'docker restart pma-app'

# Database operations
ssh sg-nas 'docker exec pma-postgres psql -U pma -d pma_sa -c "SELECT 1"'

# Run flask commands
ssh sg-nas 'docker exec pma-app flask db upgrade'

# Update code (hot reload)
ssh sg-nas 'cd /volume1/docker/pma/deploy/synology-sa && sudo bash update.sh'
```

### CN NAS (james.sh user, needs sudo for docker)
```bash
# View containers
ssh cn-nas 'sudo /usr/local/bin/docker ps --format "table {{.Names}}\t{{.Status}}"'

# View logs
ssh cn-nas 'sudo /usr/local/bin/docker logs --tail=50 pma-app'

# Restart container
ssh cn-nas 'sudo /usr/local/bin/docker restart pma-app'

# Database operations
ssh cn-nas 'sudo /usr/local/bin/docker exec pma-postgres psql -U pma -d pma_synology -c "SELECT 1"'

# Run flask commands
ssh cn-nas 'sudo /usr/local/bin/docker exec pma-app flask db upgrade'

# Update code (hot reload)
ssh cn-nas 'cd /volume1/docker/pma/deploy/synology-cn && sudo bash update.sh'
```

## Common Tasks

### Check server status
```bash
ssh {alias} 'hostname && uptime'
```

### Check PMA health
```bash
# SG
ssh sg-nas 'docker inspect --format="{{.State.Health.Status}}" pma-app'
# CN
ssh cn-nas 'sudo /usr/local/bin/docker inspect --format="{{.State.Health.Status}}" pma-app'
```

### Database backup
```bash
# SG
ssh sg-nas 'docker exec pma-postgres pg_dump -U pma pma_sa > /tmp/backup.sql'
# CN
ssh cn-nas 'sudo /usr/local/bin/docker exec pma-postgres pg_dump -U pma pma_synology > /tmp/backup.sql'
```

### Deploy update (git pull + hot reload)
```bash
# SG
ssh sg-nas 'cd /volume1/docker/pma/deploy/synology-sa && sudo bash update.sh'
# CN
ssh cn-nas 'cd /volume1/docker/pma/deploy/synology-cn && sudo bash update.sh'
```

## Important Notes

- Always verify connection before executing destructive operations
- CN NAS docker commands MUST use `sudo /usr/local/bin/docker` (not just `docker`)
- For deployment updates, prefer `update.sh` which handles git pull + smart reload
- Database backups should be done before any migration operations
- PMA_DB_TYPE: `ovs` for SG, `sp8d` for CN
