#!/bin/bash
# PMA-SA (OVS) DS925+ Update Script (Hot Reload)
# Run on DS925+ via SSH
#
# Usage: ./update.sh               # Smart update: detect changes, prefer hot reload
#        ./update.sh --force-build  # Force rebuild containers
#        ./update.sh --skip-git     # Skip git pull

# Auto-elevate to root
if [ "$EUID" -ne 0 ]; then
    exec sudo bash "$0" "$@"
fi

set -e

# Synology package paths (Git, Docker, etc.)
export PATH="/volume1/@appstore/Git/bin:/usr/local/bin:$PATH"

# Docker commands (Synology needs full path)
DOCKER="/usr/local/bin/docker"
DOCKER_COMPOSE="$DOCKER compose"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Directories
PROJECT_DIR="/volume1/docker/pma"
DEPLOY_DIR="$PROJECT_DIR/deploy/synology-sa"

# Parse arguments
FORCE_BUILD=false
SKIP_GIT=false
for arg in "$@"; do
    case "$arg" in
        --force-build) FORCE_BUILD=true ;;
        --skip-git)    SKIP_GIT=true ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA-SA (OVS) Smart Update${NC}"
echo -e "${GREEN}========================================${NC}"

# Check required commands
for cmd in git docker; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd not found${NC}"
        exit 1
    fi
done

# Record pre-update requirements.txt hash
cd "$PROJECT_DIR"
OLD_REQ_HASH=""
if [ -f "requirements.txt" ]; then
    OLD_REQ_HASH=$(md5sum requirements.txt 2>/dev/null | cut -d' ' -f1 || echo "")
fi

echo -e "\n${YELLOW}[1/4] Pulling latest code...${NC}"
if [ "$SKIP_GIT" = true ]; then
    echo -e "${YELLOW}Skipped git pull (--skip-git)${NC}"
else
    git config --global http.version HTTP/1.1
    git pull origin main
    # Fix file permissions: git pull runs as root, but container runs as pma(1000)
    chown -R 1000:1000 "$PROJECT_DIR"
fi

# Check if requirements.txt changed
NEW_REQ_HASH=""
if [ -f "requirements.txt" ]; then
    NEW_REQ_HASH=$(md5sum requirements.txt 2>/dev/null | cut -d' ' -f1 || echo "")
fi

NEED_REBUILD=false
if [ "$FORCE_BUILD" = true ]; then
    NEED_REBUILD=true
    echo -e "${CYAN}[Detect] Force rebuild mode${NC}"
elif [ "$OLD_REQ_HASH" != "$NEW_REQ_HASH" ] && [ -n "$OLD_REQ_HASH" ]; then
    echo -e "${YELLOW}[Detect] requirements.txt changed!${NC}"
    echo ""
    echo -e "${RED}Dependencies updated - container rebuild needed.${NC}"
    echo -e "${RED}Service will be briefly interrupted (~1-2 min).${NC}"
    echo ""
    read -p "Rebuild now? [y/N] " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        NEED_REBUILD=true
    else
        echo -e "${YELLOW}Skipped rebuild. New dependencies won't take effect!${NC}"
    fi
else
    echo -e "${GREEN}[Detect] requirements.txt unchanged, using hot reload${NC}"
fi

cd "$DEPLOY_DIR"

if [ "$NEED_REBUILD" = true ]; then
    echo -e "\n${YELLOW}[2/4] Rebuilding containers...${NC}"
    $DOCKER_COMPOSE up -d --build pma

    echo -e "\n${YELLOW}[3/4] Waiting for health check...${NC}"
    MAX_WAIT=60
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        HEALTH=$($DOCKER inspect --format='{{.State.Health.Status}}' pma-app 2>/dev/null || echo "unknown")
        if [ "$HEALTH" = "healthy" ]; then
            echo -e "${GREEN}✓ Container ready (${WAITED}s)${NC}"
            break
        fi
        echo -e "  Waiting... ($HEALTH) ${WAITED}s/${MAX_WAIT}s"
        sleep 3
        WAITED=$((WAITED + 3))
    done
else
    echo -e "\n${YELLOW}[2/4] Recreating container (refresh file mounts)...${NC}"
    # Use force-recreate to ensure config.py file bind mount is refreshed
    cd "$DEPLOY_DIR"
    $DOCKER_COMPOSE up -d --force-recreate pma
    echo -e "${GREEN}✓ Container recreated${NC}"

    echo -e "\n${YELLOW}[3/4] Waiting for health check...${NC}"
    MAX_WAIT=60
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        HEALTH=$($DOCKER inspect --format='{{.State.Health.Status}}' pma-app 2>/dev/null || echo "unknown")
        if [ "$HEALTH" = "healthy" ]; then
            echo -e "${GREEN}✓ Container ready (${WAITED}s)${NC}"
            break
        fi
        echo -e "  Waiting... ($HEALTH) ${WAITED}s/${MAX_WAIT}s"
        sleep 3
        WAITED=$((WAITED + 3))
    done
fi

echo -e "\n${YELLOW}[4/4] Running database migrations...${NC}"
$DOCKER exec pma-app flask db upgrade || echo -e "${YELLOW}No new migrations${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Update Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Container status:${NC}"
$DOCKER_COMPOSE ps

echo -e "\n${YELLOW}Recent logs:${NC}"
$DOCKER_COMPOSE logs --tail=5 pma
