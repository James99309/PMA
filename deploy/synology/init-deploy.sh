#!/bin/bash
# PMA 首次部署脚本
# 在群晖上执行此脚本完成首次部署

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}       PMA 首次部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 配置变量
INSTALL_DIR="/volume1/docker/pma"
REPO_URL="${1:-https://github.com/your-username/pma.git}"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误：Docker 未安装，请先安装 Container Manager${NC}"
    exit 1
fi

# 创建目录
echo -e "\n${YELLOW}[1/7] 创建安装目录...${NC}"
mkdir -p $INSTALL_DIR
cd /volume1/docker

# 克隆代码（如果目录已存在则跳过）
if [ -d "$INSTALL_DIR/.git" ]; then
    echo -e "\n${YELLOW}[2/7] 代码已存在，拉取更新...${NC}"
    cd $INSTALL_DIR
    git pull
else
    echo -e "\n${YELLOW}[2/7] 克隆代码仓库...${NC}"
    git clone $REPO_URL pma
    cd $INSTALL_DIR
fi

# 检查配置文件
echo -e "\n${YELLOW}[3/7] 检查配置文件...${NC}"
cd deploy/synology
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}创建 .env 配置文件...${NC}"
    cp .env.example .env
    echo -e "${RED}请编辑 .env 文件配置密码和 API Key！${NC}"
    echo -e "${RED}编辑完成后重新运行此脚本${NC}"
    exit 1
fi

# 构建镜像
echo -e "\n${YELLOW}[4/7] 构建 Docker 镜像...${NC}"
docker-compose build

# 启动服务
echo -e "\n${YELLOW}[5/7] 启动服务...${NC}"
docker-compose up -d

# 等待数据库就绪
echo -e "\n${YELLOW}[6/7] 等待数据库就绪...${NC}"
sleep 10

# 初始化数据库
echo -e "\n${YELLOW}[7/7] 初始化数据库...${NC}"
docker exec pma-app flask db upgrade

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}       部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n内网访问：http://192.168.1.2:5001"
echo -e "外网访问：http://你的公网IP:5001"
echo -e "\n${YELLOW}容器状态：${NC}"
docker-compose ps
