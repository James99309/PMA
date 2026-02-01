#!/bin/bash
# 在 Mac 上预构建 Docker 镜像并传输到 DS925+
# 用途: 绕过中国 Docker Hub 无法访问的问题
# 用法: bash build-and-transfer.sh

set -e

# ============ 配置 ============

# DS925+ SSH 连接信息
NAS_HOST="${NAS_HOST:-192.168.31.91}"
NAS_PORT="${NAS_PORT:-72}"
NAS_USER="${NAS_USER:-james.sh}"
NAS_DOCKER_DIR="${NAS_DOCKER_DIR:-/volume1/docker}"

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# 输出文件
OUTPUT_DIR="${PROJECT_ROOT}/deploy/synology-cn"
IMAGES_FILE="${OUTPUT_DIR}/pma-images.tar.gz"

# ============ 颜色输出 ============

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA 镜像构建 & 传输工具${NC}"
echo -e "${GREEN}  Mac → DS925+${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "项目目录: $PROJECT_ROOT"
echo "目标 NAS: $NAS_USER@$NAS_HOST:$NAS_PORT"
echo ""

# ============ Step 1: 检查 Docker ============

info "[1/5] 检查 Docker 环境..."

if ! command -v docker &> /dev/null; then
    error "Docker 未安装，请先安装 Docker Desktop for Mac"
fi

# 检查 buildx 支持
if ! docker buildx version &> /dev/null; then
    error "Docker buildx 不可用，请更新 Docker Desktop"
fi

info "Docker 版本: $(docker --version)"

# ============ Step 2: 构建 PMA 镜像 (amd64) ============

info "[2/5] 构建 PMA 应用镜像 (linux/amd64)..."

cd "$PROJECT_ROOT"

# 使用中国优化的 Dockerfile 构建 amd64 镜像
docker buildx build \
    --platform linux/amd64 \
    -t pma-app:latest \
    -f deploy/synology-cn/Dockerfile \
    --load \
    .

info "PMA 镜像构建完成"

# ============ Step 3: 拉取 PostgreSQL 镜像 (amd64) ============

info "[3/5] 拉取 PostgreSQL 17 镜像 (linux/amd64)..."

docker pull --platform linux/amd64 postgres:17-alpine

info "PostgreSQL 镜像拉取完成"

# ============ Step 4: 导出镜像 ============

info "[4/5] 导出镜像为 tar.gz..."

# 拉取 cloudflared 镜像（Cloudflare Tunnel）
info "拉取 cloudflared 镜像..."
docker pull --platform linux/amd64 cloudflare/cloudflared:latest

SAVE_IMAGES="pma-app:latest postgres:17-alpine cloudflare/cloudflared:latest"

# 检查是否需要 FRP 镜像
read -p "是否需要包含 FRP 客户端镜像？(y/N) " include_frp
if [ "$include_frp" = "y" ] || [ "$include_frp" = "Y" ]; then
    info "拉取 FRP 客户端镜像..."
    docker pull --platform linux/amd64 snowdreamtech/frpc:latest
    SAVE_IMAGES="$SAVE_IMAGES snowdreamtech/frpc:latest"
fi

docker save $SAVE_IMAGES | gzip > "$IMAGES_FILE"

FILE_SIZE=$(du -h "$IMAGES_FILE" | cut -f1)
info "镜像文件已导出: $IMAGES_FILE ($FILE_SIZE)"

# ============ Step 5: 传输到 NAS ============

info "[5/5] 传输镜像到 DS925+..."

echo ""
warn "传输可能需要较长时间，取决于网络速度"
echo "目标路径: $NAS_HOST:$NAS_DOCKER_DIR/"
echo ""

read -p "开始传输？(Y/n) " confirm
if [ "$confirm" = "n" ] || [ "$confirm" = "N" ]; then
    info "跳过传输。手动传输命令:"
    echo "  scp -P $NAS_PORT $IMAGES_FILE $NAS_USER@$NAS_HOST:$NAS_DOCKER_DIR/"
    exit 0
fi

scp -P "$NAS_PORT" "$IMAGES_FILE" "$NAS_USER@$NAS_HOST:$NAS_DOCKER_DIR/"

info "镜像传输完成！"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  镜像构建与传输完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}下一步 - 在 DS925+ 上执行:${NC}"
echo ""
echo "  # SSH 连接 NAS"
echo "  ssh -p $NAS_PORT $NAS_USER@$NAS_HOST"
echo ""
echo "  # 加载镜像"
echo "  gunzip -c $NAS_DOCKER_DIR/pma-images.tar.gz | sudo docker load"
echo ""
echo "  # 验证镜像"
echo "  sudo docker images | grep -E 'pma-app|postgres|cloudflared'"
echo ""
echo "  # 上传代码并启动"
echo "  cd $NAS_DOCKER_DIR/pma/deploy/synology-cn"
echo "  sudo docker-compose up -d"
