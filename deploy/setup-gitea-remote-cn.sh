#!/bin/bash
# PMA CN NAS — 将部署 origin 从 GitHub 改指 Mac mini Gitea（Tailscale 内网）
#
# 背景：CN NAS 直连 GitHub 长期不稳定。Mac mini 在同一 Tailnet，已装 Gitea，
#       作为 GitHub 的 pull-mirror。本脚本一次性把 CN NAS 的 git origin
#       改成 Gitea(SSH)，update.sh 逻辑无需改动即透明从 Gitea 拉取。
#
# 设计文档：docs/plans/2026-05-15-gitea-mirror-cn-deploy-design.md
#
# 用法（在 CN NAS 上执行）：
#   ./setup-gitea-remote-cn.sh            # 配置：origin -> Gitea，github 留作兜底
#   ./setup-gitea-remote-cn.sh --rollback # 回滚：origin 恢复为 GitHub
#
# 幂等：可重复运行；不破坏已正确的配置。

# 自动提升为 root（与 update.sh 一致）
if [ "$EUID" -ne 0 ]; then
    exec sudo bash "$0" "$@"
fi

set -e

export PATH="/volume1/@appstore/Git/bin:/usr/local/bin:$PATH"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

PROJECT_DIR="/volume1/docker/pma"
GITEA_URL="ssh://git@100.110.41.83:2222/admin/pma-mirror.git"
GITHUB_URL_DEFAULT="https://github.com/James99309/PMA.git"
ROOT_KEY="/root/.ssh/id_ed25519"

ROLLBACK=false
[ "$1" = "--rollback" ] && ROLLBACK=true

cd "$PROJECT_DIR"

# ---------- 回滚 ----------
if [ "$ROLLBACK" = true ]; then
    echo -e "${YELLOW}[回滚] 将 origin 恢复为 GitHub${NC}"
    GH_URL="$(git remote get-url github 2>/dev/null || echo "$GITHUB_URL_DEFAULT")"
    git remote remove origin 2>/dev/null || true
    if git remote get-url github &>/dev/null; then
        git remote rename github origin
    else
        git remote add origin "$GH_URL"
    fi
    git remote -v
    echo -e "${GREEN}✓ 已回滚：origin = $(git remote get-url origin)${NC}"
    exit 0
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  CN NAS git origin -> Mac mini Gitea${NC}"
echo -e "${GREEN}========================================${NC}"

# ---------- 1. SSH key ----------
mkdir -p /root/.ssh && chmod 700 /root/.ssh
if [ ! -f "$ROOT_KEY" ]; then
    echo -e "\n${YELLOW}[1/5] 生成 CN NAS root SSH key${NC}"
    ssh-keygen -t ed25519 -N "" -C "pma-cn-nas@gitea" -f "$ROOT_KEY"
else
    echo -e "\n${YELLOW}[1/5] 已存在 SSH key，复用 $ROOT_KEY${NC}"
fi

# ---------- 2. 提示加 Deploy Key ----------
echo -e "\n${YELLOW}[2/5] 请把下面这把公钥加到 Gitea${NC}"
echo -e "${CYAN}  Gitea → 仓库 admin/pma-mirror → Settings → Deploy Keys → Add"
echo -e "  务必勾【只读 / Read-only】，名称如 cn-nas-deploy${NC}"
echo -e "${GREEN}-------- 公钥（复制整行）--------${NC}"
cat "${ROOT_KEY}.pub"
echo -e "${GREEN}--------------------------------${NC}"
read -p "已在 Gitea 添加完该 Deploy Key？回车继续，Ctrl-C 中止 " _

# ---------- 3. 信任 Gitea 主机 + 验证 SSH ----------
# Synology DSM 不含 ssh-keyscan, 故不依赖它; 用 StrictHostKeyChecking=accept-new
# 首次自动信任 Gitea 主机键并写入 known_hosts (供后续 git fetch/ls-remote 复用),
# 已知则照常校验。 实测此法在 CN NAS 可行 (deploy key 鉴权成功)。
echo -e "\n${YELLOW}[3/5] 信任 Gitea 主机 + 验证 SSH${NC}"
mkdir -p /root/.ssh && chmod 700 /root/.ssh
touch /root/.ssh/known_hosts && chmod 644 /root/.ssh/known_hosts
if ! ssh -T -p 2222 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 git@100.110.41.83 2>&1 | grep -qiE 'gitea|authenticated|successfully'; then
    echo -e "${RED}✗ SSH 到 Gitea 失败：确认 Deploy Key 已添加、Mac mini 在 Tailnet${NC}"
    echo -e "${YELLOW}  手动诊断: ssh -T -p 2222 git@100.110.41.83${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SSH 到 Gitea 通过（主机已信任）${NC}"

# ---------- 4. 改 remote（保留 github 兜底）----------
echo -e "\n${YELLOW}[4/5] 调整 git remote${NC}"
CUR_ORIGIN="$(git remote get-url origin 2>/dev/null || echo '')"
if ! git remote get-url github &>/dev/null; then
    if [ -n "$CUR_ORIGIN" ] && echo "$CUR_ORIGIN" | grep -qi github; then
        git remote rename origin github
        echo -e "  origin(GitHub) -> 重命名为 github（兜底远程）"
    else
        git remote add github "$GITHUB_URL_DEFAULT"
        echo -e "  新增 github 兜底远程"
    fi
fi
if git remote get-url origin &>/dev/null; then
    git remote set-url origin "$GITEA_URL"
else
    git remote add origin "$GITEA_URL"
fi
echo -e "${GREEN}  origin -> $GITEA_URL${NC}"
git remote -v

# ---------- 5. 验证可拉 ----------
echo -e "\n${YELLOW}[5/5] 验证从 Gitea 拉取${NC}"
GITEA_HEAD="$(git ls-remote origin refs/heads/main 2>/dev/null | cut -f1)"
GITHUB_HEAD="$(git ls-remote github refs/heads/main 2>/dev/null | cut -f1 || echo '(github 暂不可达)')"
if [ -z "$GITEA_HEAD" ]; then
    echo -e "${RED}✗ Gitea main 为空：检查 Mac mini Gitea 镜像是否已 Synchronize Now${NC}"
    exit 1
fi
echo -e "  Gitea  main: ${GITEA_HEAD:0:12}"
echo -e "  GitHub main: ${GITHUB_HEAD:0:12}"
git fetch origin main

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ 完成。后续部署照常: ./deploy/synology-cn/update.sh${NC}"
echo -e "${GREEN}  应急兜底: git fetch github && git reset --hard github/main${NC}"
echo -e "${GREEN}  回滚: ./setup-gitea-remote-cn.sh --rollback${NC}"
echo -e "${GREEN}========================================${NC}"
