#!/bin/bash
# Build PMA-SA Docker image on Mac and transfer to DS925+ (Singapore)
# Usage: bash build-and-transfer.sh

set -e

# ============ Configuration ============

# DS925+ SSH connection
NAS_HOST="${NAS_HOST:-192.168.1.2}"
NAS_PORT="${NAS_PORT:-22}"
NAS_USER="${NAS_USER:-admin}"
NAS_DOCKER_DIR="${NAS_DOCKER_DIR:-/volume1/docker}"

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Output file
OUTPUT_DIR="${PROJECT_ROOT}/deploy/synology-sa"
IMAGES_FILE="${OUTPUT_DIR}/pma-images.tar.gz"

# ============ Colors ============

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA-SA Image Build & Transfer${NC}"
echo -e "${GREEN}  Mac → DS925+ (Singapore)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Project dir: $PROJECT_ROOT"
echo "Target NAS:  $NAS_USER@$NAS_HOST:$NAS_PORT"
echo ""

# ============ Step 1: Check Docker ============

info "[1/5] Checking Docker environment..."

if ! command -v docker &> /dev/null; then
    error "Docker not installed. Please install Docker Desktop for Mac."
fi

if ! docker buildx version &> /dev/null; then
    error "Docker buildx not available. Please update Docker Desktop."
fi

info "Docker version: $(docker --version)"

# ============ Step 2: Build PMA image (amd64) ============

info "[2/5] Building PMA application image (linux/amd64)..."

cd "$PROJECT_ROOT"

docker buildx build \
    --platform linux/amd64 \
    -t pma-app:latest \
    -f deploy/synology-sa/Dockerfile \
    --load \
    .

info "PMA image built successfully"

# ============ Step 3: Pull PostgreSQL image (amd64) ============

info "[3/5] Pulling PostgreSQL 17 image (linux/amd64)..."

docker pull --platform linux/amd64 postgres:17-alpine

info "PostgreSQL image pulled"

# ============ Step 4: Export images ============

info "[4/5] Exporting images to tar.gz..."

# Pull autoheal image
info "Pulling autoheal image..."
docker pull --platform linux/amd64 willfarrell/autoheal:latest

SAVE_IMAGES="pma-app:latest postgres:17-alpine willfarrell/autoheal:latest"

docker save $SAVE_IMAGES | gzip > "$IMAGES_FILE"

FILE_SIZE=$(du -h "$IMAGES_FILE" | cut -f1)
info "Images exported: $IMAGES_FILE ($FILE_SIZE)"

# ============ Step 5: Transfer to NAS ============

info "[5/5] Transferring images to DS925+..."

echo ""
warn "Transfer may take some time depending on network speed"
echo "Target: $NAS_HOST:$NAS_DOCKER_DIR/"
echo ""

read -p "Start transfer? (Y/n) " confirm
if [ "$confirm" = "n" ] || [ "$confirm" = "N" ]; then
    info "Skipped. Manual transfer command:"
    echo "  scp -O -P $NAS_PORT $IMAGES_FILE $NAS_USER@$NAS_HOST:$NAS_DOCKER_DIR/"
    exit 0
fi

scp -O -P "$NAS_PORT" "$IMAGES_FILE" "$NAS_USER@$NAS_HOST:$NAS_DOCKER_DIR/"

info "Image transfer complete!"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Build & Transfer Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps on DS925+:${NC}"
echo ""
echo "  # SSH to NAS"
echo "  ssh -p $NAS_PORT $NAS_USER@$NAS_HOST"
echo ""
echo "  # Load images"
echo "  gunzip -c $NAS_DOCKER_DIR/pma-images.tar.gz | sudo docker load"
echo ""
echo "  # Verify images"
echo "  sudo docker images | grep -E 'pma-app|postgres|autoheal'"
echo ""
echo "  # Deploy"
echo "  cd $NAS_DOCKER_DIR/pma/deploy/synology-sa"
echo "  sudo bash init-deploy.sh"
