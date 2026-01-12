#!/bin/bash
# PMA 一键更新脚本
# 在群晖上执行此脚本即可完成更新

# 自动提升为 root 权限
if [ "$EUID" -ne 0 ]; then
    exec sudo bash "$0" "$@"
fi

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}       PMA 自动更新脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 切换到项目目录
cd /volume1/docker/pma

echo -e "\n${YELLOW}[1/5] 拉取最新代码...${NC}"
git pull origin main

echo -e "\n${YELLOW}[2/5] 切换到部署目录...${NC}"
cd deploy/synology

echo -e "\n${YELLOW}[3/5] 重新构建镜像...${NC}"
docker-compose build pma

echo -e "\n${YELLOW}[4/5] 重启服务...${NC}"
docker-compose up -d

echo -e "\n${YELLOW}[5/5] 执行数据库迁移...${NC}"
docker exec pma-app flask db upgrade || echo "数据库迁移跳过（可能没有新迁移）"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}       更新完成！${NC}"
echo -e "${GREEN}========================================${NC}"

# 显示容器状态
echo -e "\n${YELLOW}容器状态：${NC}"
docker-compose ps

echo -e "\n${YELLOW}最近日志：${NC}"
docker-compose logs --tail=10 pma
