#!/bin/bash
# PMA DS925+ 一键更新脚本
# 在 DS925+ 上通过 SSH 执行
#
# 注意: 由于中国无法直接访问 Docker Hub，推荐使用以下方式更新:
# 方式1（推荐）: 在 Mac 上运行 remote-update.sh --rebuild
# 方式2: 在 Mac 上运行 build-and-transfer.sh 传输新镜像，然后在 NAS 上运行本脚本
# 方式3: 如果镜像加速可用，可直接在 NAS 上运行本脚本

# 自动提升为 root 权限
if [ "$EUID" -ne 0 ]; then
    exec sudo bash "$0" "$@"
fi

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA DS925+ 自动更新脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 切换到项目目录
cd /volume1/docker/pma

echo -e "\n${YELLOW}[1/4] 拉取最新代码...${NC}"
git pull origin main

echo -e "\n${YELLOW}[2/4] 切换到部署目录...${NC}"
cd deploy/synology-cn

echo -e "\n${YELLOW}[3/4] 重建并重启服务...${NC}"
echo "如果镜像已通过 build-and-transfer.sh 预构建，此步会使用本地镜像"
docker-compose up -d --build postgres pma

echo -e "\n${YELLOW}[4/4] 执行数据库迁移...${NC}"
# 等待容器就绪
sleep 5
docker exec pma-app flask db upgrade || echo "数据库迁移跳过（可能没有新迁移）"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  更新完成！${NC}"
echo -e "${GREEN}========================================${NC}"

# 显示容器状态
echo -e "\n${YELLOW}容器状态：${NC}"
docker-compose ps

echo -e "\n${YELLOW}最近日志：${NC}"
docker-compose logs --tail=10 pma
