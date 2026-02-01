#!/bin/bash
# PMA 中国 DS925+ 首次部署脚本
# 在 DS925+ 上通过 SSH 执行
# 前提: 镜像已通过 build-and-transfer.sh 加载

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA DS925+ 首次部署（中国）${NC}"
echo -e "${GREEN}========================================${NC}"

# 配置变量
INSTALL_DIR="/volume1/docker/pma"
DEPLOY_DIR="$INSTALL_DIR/deploy/synology-cn"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误：Docker 未安装，请先在 DSM 套件中心安装 Container Manager${NC}"
    exit 1
fi

# 检查镜像是否已加载
echo -e "\n${YELLOW}[1/7] 检查 Docker 镜像...${NC}"
if docker images | grep -q "pma-app"; then
    echo -e "${GREEN}✓ pma-app 镜像已存在${NC}"
else
    echo -e "${RED}pma-app 镜像未找到！${NC}"
    echo "请先在 Mac 上运行 build-and-transfer.sh 构建并传输镜像"
    echo "或在 NAS 上加载: gunzip -c /volume1/docker/pma-images.tar.gz | docker load"
    exit 1
fi

if docker images | grep -q "postgres.*17"; then
    echo -e "${GREEN}✓ postgres:17-alpine 镜像已存在${NC}"
else
    echo -e "${RED}postgres:17-alpine 镜像未找到！${NC}"
    exit 1
fi

# 检查代码目录
echo -e "\n${YELLOW}[2/7] 检查项目代码...${NC}"
if [ -d "$INSTALL_DIR/app" ]; then
    echo -e "${GREEN}✓ 项目代码已存在${NC}"
else
    echo -e "${RED}项目代码未找到: $INSTALL_DIR${NC}"
    echo "请先上传代码: scp -r -P 72 /path/to/PMA james.sh@192.168.31.91:/volume1/docker/pma"
    exit 1
fi

# 检查配置文件
echo -e "\n${YELLOW}[3/7] 检查配置文件...${NC}"
cd "$DEPLOY_DIR"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}创建 .env 配置文件...${NC}"
    cp .env.example .env
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}请编辑 .env 文件配置以下必需项：${NC}"
    echo -e "${RED}  1. POSTGRES_PASSWORD - 数据库密码${NC}"
    echo -e "${RED}  2. SECRET_KEY - Flask 密钥${NC}"
    echo -e "${RED}  3. SYNOLOGY_WEBDAV_PASSWORD - WebDAV 密码${NC}"
    echo -e "${RED}编辑完成后重新运行此脚本${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
echo -e "${GREEN}✓ .env 配置文件已存在${NC}"

# 创建 WebDAV 存储目录
echo -e "\n${YELLOW}[4/7] 创建存储目录...${NC}"
mkdir -p /volume1/pma-files
echo -e "${GREEN}✓ /volume1/pma-files 已创建${NC}"

# 启动服务（不含 FRP）
echo -e "\n${YELLOW}[5/7] 启动 PostgreSQL + PMA 服务...${NC}"
docker-compose up -d postgres pma

# 等待数据库就绪
echo -e "\n${YELLOW}[6/7] 等待数据库就绪...${NC}"
for i in $(seq 1 30); do
    if docker exec pma-postgres pg_isready -U pma -d pma_synology &>/dev/null; then
        echo -e "${GREEN}✓ 数据库已就绪${NC}"
        break
    fi
    echo "  等待中... ($i/30)"
    sleep 2
done

# 初始化数据库（如果是全新部署）
echo -e "\n${YELLOW}[7/7] 初始化数据库...${NC}"
echo "如果是从新加坡迁移数据，跳过此步骤，使用 migrate-data.sh import"
read -p "是否执行数据库初始化 (flask db upgrade)？(y/N) " init_db
if [ "$init_db" = "y" ] || [ "$init_db" = "Y" ]; then
    docker exec pma-app flask db upgrade
    echo -e "${GREEN}✓ 数据库初始化完成${NC}"
else
    echo "跳过数据库初始化"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n内网访问：http://192.168.31.91:5001"
echo ""
echo -e "${YELLOW}容器状态：${NC}"
docker-compose ps
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo "  1. 如需导入数据: 在 Mac 上运行 bash migrate-data.sh all"
echo "  2. 如需外网访问: 配置 FRP"
echo "     - 编辑 frpc.toml 填写 VPS 地址和 Token"
echo "     - 启动 FRP: docker-compose --profile frp up -d frpc"
