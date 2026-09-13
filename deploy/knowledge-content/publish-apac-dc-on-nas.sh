#!/bin/bash
# CN only: publish the APAC data-centre interactive course + PPT download.
# Run from the CN NAS repository checkout after the code deployment completes.
set -euo pipefail

if [[ "${1:-}" != "--commit" ]]; then
    echo "用法: $0 --commit"
    exit 1
fi

KEY="apac-data-center-critical-comms-cn"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$REPO/deploy/knowledge-content"
COURSE_ASSETS="${PMA_COURSE_ASSETS-$REPO/app/course_assets}"
APP_CONTAINER="pma-app"
SUDO_BIN="${PMA_SUDO_BIN-sudo}"
DOCKER_BIN="${PMA_DOCKER_BIN-/usr/local/bin/docker}"

run_sudo() {
    if [[ -n "$SUDO_BIN" ]]; then
        "$SUDO_BIN" "$@"
    else
        "$@"
    fi
}

run_docker() {
    run_sudo "$DOCKER_BIN" "$@"
}

assert_cn_target() {
    if ! run_docker exec "$APP_CONTAINER" sh -c \
        'test "${PMA_DB_TYPE:-}" = "sp8d" && case "${DATABASE_URL:-}" in */pma_synology) exit 0 ;; *) exit 1 ;; esac'; then
        echo "拒绝发布：当前容器不是 CN/SP8D 的 pma_synology 数据库。"
        exit 2
    fi
}

# Fail closed before any container or host filesystem write.
assert_cn_target

echo "[CN-NAS/pma_synology] 发布亚太数据中心关键通信中文课程"

echo "[1/4] 复制版本化内容包到应用容器"
run_docker exec "$APP_CONTAINER" mkdir -p /app/deploy
run_docker cp "$PKG" "$APP_CONTAINER:/app/deploy/"

echo "[2/4] 在容器内构建 26 页自包含互动课件"
run_docker exec "$APP_CONTAINER" python3 \
    /app/deploy/knowledge-content/publish_apac_dc.py

echo "[3/4] 投放互动课件与封面到宿主机"
run_sudo mkdir -p "$COURSE_ASSETS"
TMP_HTML="/tmp/$KEY.$$.html"
LIVE_HTML="$COURSE_ASSETS/$KEY.html"
STAGED_HTML="$COURSE_ASSETS/.$KEY.html.$$"
OLD_HTML="$COURSE_ASSETS/.$KEY.html.old.$$"
LIVE_THUMBS="$COURSE_ASSETS/$KEY.thumbs"
STAGED_THUMBS="$COURSE_ASSETS/.$KEY.thumbs.$$"
OLD_THUMBS="$COURSE_ASSETS/.$KEY.thumbs.old.$$"
HAD_HTML=0
HAD_THUMBS=0
SWITCH_ACTIVE=0

restore_previous_assets() {
    run_sudo rm -f "$LIVE_HTML" 2>/dev/null || true
    run_sudo rm -rf "$LIVE_THUMBS" 2>/dev/null || true
    if [[ "$HAD_HTML" -eq 1 ]]; then
        run_sudo mv "$OLD_HTML" "$LIVE_HTML" 2>/dev/null || true
    fi
    if [[ "$HAD_THUMBS" -eq 1 ]]; then
        run_sudo mv "$OLD_THUMBS" "$LIVE_THUMBS" 2>/dev/null || true
    fi
}

cleanup() {
    if [[ "$SWITCH_ACTIVE" -eq 1 ]]; then
        restore_previous_assets
    fi
    run_sudo rm -f "$TMP_HTML" "$STAGED_HTML" 2>/dev/null || true
    run_sudo rm -rf "$STAGED_THUMBS" 2>/dev/null || true
}
trap cleanup EXIT

run_docker cp \
    "$APP_CONTAINER:/app/deploy/knowledge-content/.build/apac-cn/$KEY.html" \
    "$TMP_HTML"
run_sudo cp "$TMP_HTML" "$STAGED_HTML"
if ! run_sudo test -s "$STAGED_HTML"; then
    echo "互动课件构建结果为空，停止发布。"
    exit 1
fi

run_sudo mkdir -p "$STAGED_THUMBS"
page=1
for thumb in "$PKG"/assets/apac-dc-cn/thumbs/page-*.png; do
    run_sudo cp "$thumb" "$STAGED_THUMBS/$page.png"
    page=$((page + 1))
done
if [[ "$page" -ne 27 ]]; then
    echo "缩略图数量错误: 期望 26，实际 $((page - 1))"
    exit 1
fi
run_sudo chown -R 1000:1000 "$STAGED_HTML" "$STAGED_THUMBS" 2>/dev/null || true
run_sudo chmod 644 "$STAGED_HTML" "$STAGED_THUMBS"/*.png
run_sudo chmod 755 "$STAGED_THUMBS"

# Back up both live assets first so any later failure restores one coherent version.
if run_sudo test -f "$LIVE_HTML"; then
    run_sudo mv "$LIVE_HTML" "$OLD_HTML"
    HAD_HTML=1
fi
if run_sudo test -d "$LIVE_THUMBS"; then
    if ! run_sudo mv "$LIVE_THUMBS" "$OLD_THUMBS"; then
        if [[ "$HAD_HTML" -eq 1 ]]; then
            run_sudo mv "$OLD_HTML" "$LIVE_HTML"
        fi
        echo "旧版缩略图暂存失败，未切换课程资源。"
        exit 1
    fi
    HAD_THUMBS=1
fi

SWITCH_ACTIVE=1
run_sudo mv "$STAGED_HTML" "$LIVE_HTML"
run_sudo mv "$STAGED_THUMBS" "$LIVE_THUMBS"

echo "[4/4] 上传原始 PPT、登记课程并析出 Wiki 文章"
run_docker exec "$APP_CONTAINER" python3 \
    /app/deploy/knowledge-content/publish_apac_dc.py \
    --commit --skip-assets --has-thumbs

SWITCH_ACTIVE=0
run_sudo rm -f "$OLD_HTML" "$TMP_HTML"
run_sudo rm -rf "$OLD_THUMBS"
trap - EXIT

echo "[CN-NAS/pma_synology] 完成: /wiki/play/$KEY"
