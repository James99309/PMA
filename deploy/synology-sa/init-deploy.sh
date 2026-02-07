#!/bin/bash
# PMA-SA (OVS) DS925+ First-time Deployment Script
# Run on DS925+ via SSH
# Prerequisites: Images loaded via build-and-transfer.sh
#
# IMPORTANT: This script preserves the existing cloudflared-named-tunnel.
# It creates a shared external network and connects cloudflared to it,
# so the tunnel continues serving all domains without interruption.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Docker commands (Synology needs full path)
DOCKER="/usr/local/bin/docker"
DOCKER_COMPOSE="$DOCKER compose"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA-SA (OVS) DS925+ First Deploy${NC}"
echo -e "${GREEN}  Singapore Environment${NC}"
echo -e "${GREEN}========================================${NC}"

# Configuration
INSTALL_DIR="/volume1/docker/pma"
DEPLOY_DIR="$INSTALL_DIR/deploy/synology-sa"
NETWORK_NAME="pma-network"

# ============ Step 1: Check Docker images ============

echo -e "\n${YELLOW}[1/9] Checking Docker images...${NC}"
if $DOCKER images | grep -q "pma-app"; then
    echo -e "${GREEN}✓ pma-app image found${NC}"
else
    echo -e "${RED}pma-app image not found!${NC}"
    echo "Run build-and-transfer.sh on Mac first, then load:"
    echo "  gunzip -c /volume1/docker/pma-images.tar.gz | $DOCKER load"
    exit 1
fi

if $DOCKER images | grep -q "postgres.*17"; then
    echo -e "${GREEN}✓ postgres:17-alpine image found${NC}"
else
    echo -e "${RED}postgres:17-alpine image not found!${NC}"
    exit 1
fi

# ============ Step 2: Check project code ============

echo -e "\n${YELLOW}[2/9] Checking project code...${NC}"
if [ -d "$INSTALL_DIR/app" ]; then
    echo -e "${GREEN}✓ Project code exists at $INSTALL_DIR${NC}"
else
    echo -e "${RED}Project code not found: $INSTALL_DIR${NC}"
    echo "Upload code first: scp -r -O /path/to/PMA admin@192.168.1.2:/volume1/docker/pma"
    exit 1
fi

# ============ Step 3: Check .env config ============

echo -e "\n${YELLOW}[3/9] Checking configuration...${NC}"
cd "$DEPLOY_DIR"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cp .env.example .env
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}Please edit .env and configure:${NC}"
    echo -e "${RED}  1. POSTGRES_PASSWORD - Database password${NC}"
    echo -e "${RED}  2. SECRET_KEY - Flask secret key${NC}"
    echo -e "${RED}  3. SYNOLOGY_WEBDAV_PASSWORD - WebDAV password${NC}"
    echo -e "${RED}Re-run this script after editing.${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
echo -e "${GREEN}✓ .env config exists${NC}"

# ============ Step 4: Create shared external network ============

echo -e "\n${YELLOW}[4/9] Setting up shared Docker network...${NC}"
if $DOCKER network inspect "$NETWORK_NAME" &>/dev/null; then
    echo -e "${GREEN}✓ Network '$NETWORK_NAME' already exists${NC}"
else
    echo -e "${CYAN}Creating external network '$NETWORK_NAME'...${NC}"
    $DOCKER network create "$NETWORK_NAME"
    echo -e "${GREEN}✓ Network '$NETWORK_NAME' created${NC}"
fi

# ============ Step 5: Connect cloudflared to shared network ============

echo -e "\n${YELLOW}[5/9] Connecting cloudflared to shared network...${NC}"
if $DOCKER ps --format '{{.Names}}' | grep -q "cloudflared-named-tunnel"; then
    # Check if already connected
    if $DOCKER network inspect "$NETWORK_NAME" 2>/dev/null | grep -q "cloudflared-named-tunnel"; then
        echo -e "${GREEN}✓ cloudflared-named-tunnel already on '$NETWORK_NAME'${NC}"
    else
        $DOCKER network connect "$NETWORK_NAME" cloudflared-named-tunnel
        echo -e "${GREEN}✓ Connected cloudflared-named-tunnel to '$NETWORK_NAME'${NC}"
    fi
else
    echo -e "${YELLOW}⚠ cloudflared-named-tunnel not running - tunnel routing won't work until it's started${NC}"
fi

# ============ Step 6: Stop old PMA containers (preserve cloudflared) ============

echo -e "\n${YELLOW}[6/9] Stopping old PMA containers (keeping cloudflared)...${NC}"

for container in pma-app pma-postgres pma-autoheal; do
    if $DOCKER ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "${CYAN}  Stopping and removing $container...${NC}"
        $DOCKER stop "$container" 2>/dev/null || true
        $DOCKER rm "$container" 2>/dev/null || true
    fi
done

# Remove old data volumes (fresh start with OVS data)
for vol in synology-cn_postgres_data synology-sa_postgres_data; do
    if $DOCKER volume ls -q | grep -q "^${vol}$"; then
        echo -e "${CYAN}  Removing old volume $vol...${NC}"
        $DOCKER volume rm "$vol" 2>/dev/null || true
    fi
done

echo -e "${GREEN}✓ Old containers cleaned up, cloudflared preserved${NC}"

# ============ Step 7: Create storage directory ============

echo -e "\n${YELLOW}[7/9] Creating storage directories...${NC}"
mkdir -p /volume1/pma-files
echo -e "${GREEN}✓ /volume1/pma-files ready${NC}"

# ============ Step 8: Start new services ============

echo -e "\n${YELLOW}[8/9] Starting PostgreSQL + PMA-SA services...${NC}"
cd "$DEPLOY_DIR"
$DOCKER_COMPOSE up -d postgres pma autoheal

# Wait for database
echo -e "\n${YELLOW}[9/9] Waiting for database to be ready...${NC}"
for i in $(seq 1 30); do
    if $DOCKER exec pma-postgres pg_isready -U pma -d pma_sa &>/dev/null; then
        echo -e "${GREEN}✓ Database ready${NC}"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# Ask about database initialization
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Database Initialization${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  If migrating from Supabase OVS → skip this, use migrate-database.sh"
echo "  If fresh install → run flask db upgrade"
echo ""
read -p "Run database initialization (flask db upgrade)? (y/N) " init_db
if [ "$init_db" = "y" ] || [ "$init_db" = "Y" ]; then
    $DOCKER exec pma-app flask db upgrade
    echo -e "${GREEN}✓ Database initialized${NC}"
else
    echo "Skipped - use migrate-database.sh to import OVS data"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nInternal access: http://192.168.1.2:5002"
echo -e "External access: https://sg-pma.jamesgpone.win (via Cloudflare Tunnel)"
echo ""
echo -e "${YELLOW}Container status:${NC}"
$DOCKER_COMPOSE ps
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Import OVS data: bash migrate-database.sh (run on Mac)"
echo "  2. Migrate files:   bash migrate-storage.sh (run on Mac)"
echo "  3. Verify: open https://pma.jamesgpone.win and login"
