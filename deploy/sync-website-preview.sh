#!/bin/bash
# ============================================================================
# 官网预览快照投放脚本(固定流程 —— 勿在会话里即兴拼 ssh/rsync)
#
# 为什么快照不进 git:
#   每份快照 140M+,而 CN/SG 两台 NAS 从同一个 git 仓库 `git reset --hard`。
#   一旦进 git,CN 就会被迫拉英文站、SG 被迫拉中文站(各 +140M,且语言错位)。
#   故快照按区域单独投放(见 .gitignore),仓库只保留路由代码。
#
# 投放目标是 bind mount 进容器的目录(/volume1/docker/pma/app → /app/app,只读),
# 同步完立即生效 —— 不需要重启容器,也不需要重建镜像。
# update.sh 只做 git fetch + reset --hard(无 git clean),不会删除这些未跟踪文件。
#
# 用法:
#   ./deploy/sync-website-preview.sh cn            # 本地中文站 → CN NAS(SP8D)
#   ./deploy/sync-website-preview.sh sg            # 本地英文站 → SG NAS(OVS)
#   ./deploy/sync-website-preview.sh cn --dry-run  # 只看会传哪些文件,不实际写
#
# 官网改版后的更新流程(不涉及 git、不涉及部署):
#   1. 解包新导出到本地 app/website_<cn|en>_preview/
#   2. 跑本脚本对应区域
# ============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

TARGET="${1:-}"
DRY_RUN=""
[ "${2:-}" = "--dry-run" ] && DRY_RUN="--dry-run"

# 区域 → 本地目录 / SSH 连接 / 说明(连接参数与 pma-nas-access 一致)
case "$TARGET" in
  cn)
    LOCAL_DIR="app/website_cn_preview"
    SSH_TARGET="james.sh@100.118.231.15"
    SSH_PORT="72"
    LABEL="CN-NAS(SP8D) · 中文站"
    ;;
  sg)
    LOCAL_DIR="app/website_en_preview"
    SSH_TARGET="admin@100.87.155.40"
    SSH_PORT="22"
    LABEL="SG-NAS(OVS) · 英文站"
    ;;
  *)
    echo -e "${RED}用法: $0 <cn|sg> [--dry-run]${NC}"
    echo "  cn → 本地 app/website_cn_preview → CN NAS"
    echo "  sg → 本地 app/website_en_preview → SG NAS"
    exit 1
    ;;
esac

# 从项目根目录运行(脚本在 deploy/ 下)
cd "$(dirname "$0")/.."

REMOTE_BASE="/volume1/docker/pma/app"
REMOTE_DIR="$REMOTE_BASE/$(basename "$LOCAL_DIR")"
BACKUP_BASE="/volume1/docker/pma-site-backup"
STAMP="$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$LOCAL_DIR/"*.html ] 2>/dev/null && [ ! -d "$LOCAL_DIR" ]; then
  echo -e "${RED}本地目录不存在: $LOCAL_DIR${NC}"
  exit 1
fi

FILE_COUNT=$(find "$LOCAL_DIR" -type f | wc -l | tr -d ' ')
SIZE=$(du -sh "$LOCAL_DIR" | cut -f1)

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  投放目标: $LABEL${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "  本地: $LOCAL_DIR  ($FILE_COUNT 个文件 / $SIZE)"
echo "  远端: $SSH_TARGET:$REMOTE_DIR"
[ -n "$DRY_RUN" ] && echo -e "  ${YELLOW}[DRY-RUN 模式,不会实际写入]${NC}"
echo

SSH_CMD="ssh -p $SSH_PORT -o ConnectTimeout=10 $SSH_TARGET"

# ── 0. DRY-RUN:只对比两端差异,不写任何东西 ───────────────────────────────
if [ -n "$DRY_RUN" ]; then
  echo "→ [DRY-RUN] 远端现状:"
  $SSH_CMD "sudo sh -c '
    if [ -d \"$REMOTE_DIR\" ]; then
      echo \"  远端已有 \$(find \"$REMOTE_DIR\" -type f | wc -l | tr -d \" \") 个文件\"
    else
      echo \"  远端尚无该快照(将新建)\"
    fi'"
  echo "  本地将投放 $FILE_COUNT 个文件 / $SIZE"
  echo -e "${YELLOW}DRY-RUN 结束,未做任何改动${NC}"
  exit 0
fi

# ── 1. 备份远端现有快照(若存在)───────────────────────────────────────────
if [ -z "$DRY_RUN" ]; then
  echo "→ 备份远端现有快照..."
  $SSH_CMD "sudo sh -c '
    if [ -d \"$REMOTE_DIR\" ]; then
      mkdir -p \"$BACKUP_BASE\"
      cp -a \"$REMOTE_DIR\" \"$BACKUP_BASE/$(basename "$LOCAL_DIR")-$STAMP\"
      echo \"  已备份到 $BACKUP_BASE/$(basename "$LOCAL_DIR")-$STAMP\"
      # 只保留最近 3 份备份
      ls -1dt \"$BACKUP_BASE/$(basename "$LOCAL_DIR")\"-* 2>/dev/null | tail -n +4 | xargs -r rm -rf
    else
      echo \"  远端尚无该快照,跳过备份\"
    fi'"
fi

# ── 2. 同步:tar over ssh ─────────────────────────────────────────────────
# 不用 rsync:macOS 自带的是 openrsync(协议 29),与 NAS 的 rsync 3.1.2 + sudo
# 组合会 "unexpected end of file"。tar 管道零依赖,且先落 .new 再整体替换 ——
# 中途断线不会留下半截站点。权限在远端一次性给足(避开 700 权限漂移历史坑)。
echo "→ 打包并传输(约 $SIZE,视网络需数十秒)..."
tar czf - -C "$LOCAL_DIR" . | $SSH_CMD "sudo sh -c '
  rm -rf \"$REMOTE_DIR.new\" &&
  mkdir -p \"$REMOTE_DIR.new\" &&
  tar xzf - -C \"$REMOTE_DIR.new\" &&
  chown -R 1000:1000 \"$REMOTE_DIR.new\" &&
  find \"$REMOTE_DIR.new\" -type d -exec chmod 755 {} + &&
  find \"$REMOTE_DIR.new\" -type f -exec chmod 644 {} + &&
  rm -rf \"$REMOTE_DIR\" &&
  mv \"$REMOTE_DIR.new\" \"$REMOTE_DIR\"'"

# ── 4. 校验 ──────────────────────────────────────────────────────────────
echo "→ 校验..."
REMOTE_COUNT=$($SSH_CMD "sudo find \"$REMOTE_DIR\" -type f | wc -l" | tr -d ' \r')
echo "  本地 $FILE_COUNT 个文件 / 远端 $REMOTE_COUNT 个文件"

if [ "$FILE_COUNT" = "$REMOTE_COUNT" ]; then
  echo -e "${GREEN}✅ 投放完成 —— $LABEL${NC}"
  echo -e "${GREEN}   目录已 bind mount 进容器,立即生效(无需重启)${NC}"
else
  echo -e "${RED}❌ 文件数不一致,请检查${NC}"
  exit 1
fi
