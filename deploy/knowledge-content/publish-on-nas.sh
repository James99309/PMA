#!/bin/bash
# AT 知识库内容发布 —— NAS 侧固定流程（在 NAS 宿主机上跑，不要在容器里跑）
#
# 为什么要这个包装：容器里 /app/app 是**只读**挂载，课件写不进 app/course_assets/；
# 而 DB 和 storage 又只有容器里够得着。所以分工：
#   宿主机：docker cp 送包进容器 → 容器内构建 → 把产物 cp 回宿主机的 course_assets
#   容器内：登记课程 + 文章入库（--skip-assets 跳过投放）
#
# 用法（在 NAS 上，仓库根目录）：
#   ./deploy/knowledge-content/publish-on-nas.sh cn            # 预览，不写库
#   ./deploy/knowledge-content/publish-on-nas.sh cn --commit
#   ./deploy/knowledge-content/publish-on-nas.sh en --commit --scope personal
set -euo pipefail

TARGET="${1:-}"
shift || true
EXTRA_ARGS=("$@")

if [[ "$TARGET" != "cn" && "$TARGET" != "en" ]]; then
    echo "用法: $0 cn|en [--commit] [--scope personal|company]"
    exit 1
fi

case "$TARGET" in
    cn) KEY="dgtj08-2406-2022" ;;
    en) KEY="twr-ibs-ref-en" ;;
esac

# 仓库根（本脚本在 deploy/knowledge-content/ 下）
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$REPO/deploy/knowledge-content"
APP_CONTAINER="pma-app"

# docker 路径：CN 是 /usr/local/bin/docker，SG 需要先补 PATH
if [ -x /usr/local/bin/docker ]; then
    DOCKER="sudo /usr/local/bin/docker"
else
    DOCKER="sudo docker"
fi

COMMIT=0
for a in "${EXTRA_ARGS[@]:-}"; do [ "$a" = "--commit" ] && COMMIT=1; done

echo "════════════════════════════════════════"
echo "  知识库内容发布: $TARGET  (key=$KEY)"
echo "  仓库: $REPO"
echo "  模式: $([ $COMMIT -eq 1 ] && echo '写库' || echo '预览')"
echo "════════════════════════════════════════"

echo
echo "[1/4] 送发布包进容器"
$DOCKER exec "$APP_CONTAINER" mkdir -p /app/deploy
$DOCKER cp "$PKG" "$APP_CONTAINER:/app/deploy/"
echo "   ✅ /app/deploy/knowledge-content"

echo
echo "[2/4] 容器内构建阅读器"
$DOCKER exec "$APP_CONTAINER" python3 /app/deploy/knowledge-content/lib/build_reader_entry.py "$TARGET"

echo
echo "[3/4] 取回产物并投放到宿主机 course_assets（容器内 /app/app 只读）"
ASSETS="$REPO/app/course_assets"
sudo mkdir -p "$ASSETS/$KEY.thumbs"
$DOCKER cp "$APP_CONTAINER:/app/deploy/knowledge-content/.build/$TARGET/$KEY.html" "/tmp/$KEY.html"
sudo cp "/tmp/$KEY.html" "$ASSETS/$KEY.html"
rm -f "/tmp/$KEY.html"
COVER="$PKG/assets/covers/$KEY.png"
HAS_THUMBS=""
if [ -f "$COVER" ]; then
    sudo cp "$COVER" "$ASSETS/$KEY.thumbs/1.png"
    HAS_THUMBS="--has-thumbs"
fi
# 与 app 目录保持同一属主/权限（update.sh 的 umask 022 同理，防权限漂移）
sudo chown -R 1000:1000 "$ASSETS/$KEY.html" "$ASSETS/$KEY.thumbs" 2>/dev/null || true
sudo chmod 644 "$ASSETS/$KEY.html" "$ASSETS/$KEY.thumbs/1.png" 2>/dev/null || true
sudo chmod 755 "$ASSETS/$KEY.thumbs"
ls -la "$ASSETS/$KEY.html" "$ASSETS/$KEY.thumbs/" | sed 's/^/   /'

echo
echo "[4/4] 容器内登记课程 + 文章入库"
$DOCKER exec "$APP_CONTAINER" python3 /app/deploy/knowledge-content/publish.py "$TARGET" \
    --skip-assets $HAS_THUMBS "${EXTRA_ARGS[@]:-}"

echo
echo "✅ 完成：/wiki/play/$KEY"
