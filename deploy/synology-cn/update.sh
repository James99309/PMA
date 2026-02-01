#!/bin/bash
# PMA DS925+ 一键更新脚本
# 在 DS925+ 上通过 SSH 执行
#
# 用法: ./update.sh          # 拉取代码 + 重建容器 + 数据库迁移
#       ./update.sh --skip-build  # 仅拉取代码和数据库迁移，不重建容器

# 自动提升为 root 权限
if [ "$EUID" -ne 0 ]; then
    exec sudo bash "$0" "$@"
fi

set -e

# Synology 套件路径（Git、Docker 等）
export PATH="/volume1/@appstore/Git/bin:/usr/local/bin:$PATH"

# Docker 命令（Synology 需要完整路径）
DOCKER="/usr/local/bin/docker"
DOCKER_COMPOSE="$DOCKER compose"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目目录
PROJECT_DIR="/volume1/docker/pma"
DEPLOY_DIR="$PROJECT_DIR/deploy/synology-cn"

SKIP_BUILD=false
if [ "$1" = "--skip-build" ]; then
    SKIP_BUILD=true
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA DS925+ 自动更新脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查必要命令
for cmd in git docker; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}错误: $cmd 未找到${NC}"
        echo "Git 路径: /volume1/@appstore/Git/bin/git"
        echo "Docker 路径: /usr/local/bin/docker"
        exit 1
    fi
done

echo -e "\n${YELLOW}[1/4] 拉取最新代码...${NC}"
cd "$PROJECT_DIR"
git pull origin main

echo -e "\n${YELLOW}[2/4] 切换到部署目录...${NC}"
cd "$DEPLOY_DIR"

if [ "$SKIP_BUILD" = true ]; then
    echo -e "\n${YELLOW}[3/4] 跳过重建（--skip-build）...${NC}"
else
    echo -e "\n${YELLOW}[3/4] 重建并重启服务...${NC}"
    $DOCKER_COMPOSE up -d --build pma
fi

echo -e "\n${YELLOW}[4/4] 执行数据库迁移...${NC}"
sleep 5
$DOCKER exec pma-app flask db upgrade || echo -e "${YELLOW}数据库迁移跳过（可能没有新迁移）${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  更新完成！${NC}"
echo -e "${GREEN}========================================${NC}"

# 显示容器状态
echo -e "\n${YELLOW}容器状态：${NC}"
$DOCKER_COMPOSE ps

echo -e "\n${YELLOW}最近日志：${NC}"
$DOCKER_COMPOSE logs --tail=10 pma
