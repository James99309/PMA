#!/bin/bash
# PMA 远程更新脚本
# 从 Mac 远程更新 DS925+ 上的 PMA
# 用法: bash remote-update.sh [--rebuild]
#
# --rebuild: 在 Mac 上重新构建镜像并传输到 NAS（需要修改 Dockerfile 或依赖时）
# 无参数:   同步代码到 NAS 后重建容器（代码变更时使用）

set -e

# ============ 配置 ============

NAS_HOST="${NAS_HOST:-192.168.31.91}"
NAS_PORT="${NAS_PORT:-72}"
NAS_USER="${NAS_USER:-james.sh}"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# ============ 颜色输出 ============

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

ssh_nas() {
    ssh -p "$NAS_PORT" "$NAS_USER@$NAS_HOST" "$@"
}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA 远程更新 (Mac → DS925+)${NC}"
echo -e "${GREEN}========================================${NC}"

REBUILD=false
if [ "$1" = "--rebuild" ]; then
    REBUILD=true
    info "模式: 在 Mac 上重新构建镜像并传输"
else
    info "模式: 同步代码后在 NAS 上重建容器"
fi

# Step 1: 同步代码到 NAS
info "[1/4] 同步代码到 NAS..."

rsync -avz --delete \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude '.env.*' \
    --exclude 'node_modules' \
    --exclude 'logs/' \
    --exclude 'cloud_db_backups/' \
    --exclude 'data/' \
    --exclude '.DS_Store' \
    -e "ssh -p $NAS_PORT" \
    "$PROJECT_ROOT/" \
    "$NAS_USER@$NAS_HOST:/volume1/docker/pma/"

info "代码同步完成"

# Step 2: 构建镜像
if [ "$REBUILD" = true ]; then
    info "[2/4] 在 Mac 上重新构建镜像并传输..."
    bash "$PROJECT_ROOT/deploy/synology-cn/build-and-transfer.sh"
else
    info "[2/4] 在 NAS 上重建容器（使用同步后的代码）..."
fi

# Step 3: 重启服务（使用 --build 确保代码变更生效）
info "[3/4] 重建并重启 PMA 服务..."
ssh_nas "cd /volume1/docker/pma/deploy/synology-cn && sudo docker-compose up -d --build pma"

# Step 4: 执行数据库迁移
info "[4/4] 执行数据库迁移..."
sleep 5
ssh_nas "sudo docker exec pma-app flask db upgrade" || warn "数据库迁移跳过"

echo -e "\n${GREEN}更新完成！${NC}"
echo ""

# 显示容器状态
info "容器状态:"
ssh_nas "cd /volume1/docker/pma/deploy/synology-cn && sudo docker-compose ps"

echo ""
info "访问 PMA: http://$NAS_HOST:5001"
