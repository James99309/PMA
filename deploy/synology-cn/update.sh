#!/bin/bash
# PMA DS925+ 一键更新脚本（热重载版）
# 在 DS925+ 上通过 SSH 执行
#
# 用法: ./update.sh               # 智能更新：检测变化，优先热重载
#       ./update.sh --force-build # 强制重建容器
#       ./update.sh --skip-git    # 跳过 git pull

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
CYAN='\033[0;36m'
NC='\033[0m'

# 项目目录
PROJECT_DIR="/volume1/docker/pma"
DEPLOY_DIR="$PROJECT_DIR/deploy/synology-cn"

# 解析参数
FORCE_BUILD=false
SKIP_GIT=false
for arg in "$@"; do
    case "$arg" in
        --force-build) FORCE_BUILD=true ;;
        --skip-git)    SKIP_GIT=true ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA DS925+ 智能更新脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查必要命令
for cmd in git docker; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}错误: $cmd 未找到${NC}"
        exit 1
    fi
done

# 记录更新前的 requirements.txt 哈希
cd "$PROJECT_DIR"
OLD_REQ_HASH=""
if [ -f "requirements.txt" ]; then
    OLD_REQ_HASH=$(md5sum requirements.txt 2>/dev/null | cut -d' ' -f1 || echo "")
fi

echo -e "\n${YELLOW}[1/4] 拉取最新代码...${NC}"
if [ "$SKIP_GIT" = true ]; then
    echo -e "${YELLOW}跳过 git pull（--skip-git）${NC}"
else
    # 修复 HTTP/2 协议问题
    git config --global http.version HTTP/1.1
    git pull origin main
    # 修复文件权限：git pull 以 root 运行，但容器以 pma(1000) 用户运行
    chown -R 1000:1000 "$PROJECT_DIR"
fi

# 检查 requirements.txt 是否变化
NEW_REQ_HASH=""
if [ -f "requirements.txt" ]; then
    NEW_REQ_HASH=$(md5sum requirements.txt 2>/dev/null | cut -d' ' -f1 || echo "")
fi

NEED_REBUILD=false
if [ "$FORCE_BUILD" = true ]; then
    NEED_REBUILD=true
    echo -e "${CYAN}[检测] 强制重建模式${NC}"
elif [ "$OLD_REQ_HASH" != "$NEW_REQ_HASH" ] && [ -n "$OLD_REQ_HASH" ]; then
    echo -e "${YELLOW}[检测] requirements.txt 已变化！${NC}"
    echo -e "${YELLOW}旧哈希: $OLD_REQ_HASH${NC}"
    echo -e "${YELLOW}新哈希: $NEW_REQ_HASH${NC}"
    echo ""
    echo -e "${RED}⚠️  依赖文件已更新，需要重建容器才能生效。${NC}"
    echo -e "${RED}   重建期间服务会短暂中断（约1-2分钟）。${NC}"
    echo ""
    read -p "是否现在重建容器？[y/N] " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        NEED_REBUILD=true
    else
        echo -e "${YELLOW}已跳过重建。注意：新依赖将不会生效！${NC}"
    fi
else
    echo -e "${GREEN}[检测] requirements.txt 无变化，使用热重载${NC}"
fi

cd "$DEPLOY_DIR"

if [ "$NEED_REBUILD" = true ]; then
    echo -e "\n${YELLOW}[2/4] 重建容器...${NC}"
    $DOCKER_COMPOSE up -d --build pma

    echo -e "\n${YELLOW}[3/4] 等待容器健康检查...${NC}"
    MAX_WAIT=60
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        HEALTH=$($DOCKER inspect --format='{{.State.Health.Status}}' pma-app 2>/dev/null || echo "unknown")
        if [ "$HEALTH" = "healthy" ]; then
            echo -e "${GREEN}✓ 容器已就绪 (${WAITED}秒)${NC}"
            break
        fi
        echo -e "  等待中... ($HEALTH) ${WAITED}s/${MAX_WAIT}s"
        sleep 3
        WAITED=$((WAITED + 3))
    done
else
    echo -e "\n${YELLOW}[2/4] 热重载应用...${NC}"
    # 发送 HUP 信号让 gunicorn 重新加载
    $DOCKER kill --signal=HUP pma-app 2>/dev/null || {
        echo -e "${YELLOW}热重载失败，尝试重启容器...${NC}"
        $DOCKER restart pma-app
    }
    echo -e "${GREEN}✓ 热重载完成（约2-3秒生效）${NC}"

    echo -e "\n${YELLOW}[3/4] 等待服务就绪...${NC}"
    sleep 3
fi

echo -e "\n${YELLOW}[4/4] 执行数据库迁移...${NC}"
$DOCKER exec pma-app flask db upgrade || echo -e "${YELLOW}数据库迁移跳过（可能没有新迁移）${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  更新完成！${NC}"
echo -e "${GREEN}========================================${NC}"

# 显示容器状态
echo -e "\n${YELLOW}容器状态：${NC}"
$DOCKER_COMPOSE ps

echo -e "\n${YELLOW}最近日志：${NC}"
$DOCKER_COMPOSE logs --tail=5 pma
