#!/bin/bash
# SG only: publish the APAC data-centre English interactive course + PPT download.
# Run from the SG NAS repository checkout after the code deployment completes.
set -euo pipefail

if [[ "${1:-}" != "--commit" ]]; then
    echo "Usage: $0 --commit"
    exit 1
fi

KEY="apac-data-center-critical-comms-en"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PKG="$REPO/deploy/knowledge-content"
COURSE_ASSETS="${PMA_COURSE_ASSETS-$REPO/app/course_assets}"
APP_CONTAINER="pma-app"
SUDO_BIN="${PMA_SUDO_BIN-sudo}"
DOCKER_BIN="${PMA_DOCKER_BIN-docker}"

run_sudo() {
    if [[ -n "$SUDO_BIN" ]]; then
        "$SUDO_BIN" "$@"
    else
        "$@"
    fi
}

run_docker() {
    if [[ -n "$SUDO_BIN" ]]; then
        "$SUDO_BIN" sh -c 'export PATH=/usr/local/bin:$PATH; exec "$@"' sh "$DOCKER_BIN" "$@"
    else
        "$DOCKER_BIN" "$@"
    fi
}

assert_sg_target() {
    if ! run_docker exec "$APP_CONTAINER" sh -c \
        'test "${PMA_DB_TYPE:-}" = "ovs" && case "${DATABASE_URL:-}" in */pma_sa) exit 0 ;; *) exit 1 ;; esac'; then
        echo "Refusing publication: current container is not SG/OVS with the pma_sa database."
        exit 2
    fi
}

# Fail closed before any container or host filesystem write.
assert_sg_target

echo "[SG-NAS/pma_sa] Publishing APAC data-center critical-communications English course"

echo "[1/4] Copying the versioned content package into the application container"
run_docker exec "$APP_CONTAINER" mkdir -p /app/deploy
run_docker cp "$PKG" "$APP_CONTAINER:/app/deploy/"

echo "[2/4] Building the 26-module self-contained interactive course"
run_docker exec "$APP_CONTAINER" python3 \
    /app/deploy/knowledge-content/publish_apac_dc.py --market sg

echo "[3/4] Staging the interactive course and thumbnails on the host"
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
    "$APP_CONTAINER:/app/deploy/knowledge-content/.build/apac-sg/$KEY.html" \
    "$TMP_HTML"
run_sudo cp "$TMP_HTML" "$STAGED_HTML"
if ! run_sudo test -s "$STAGED_HTML"; then
    echo "The interactive course build is empty; stopping publication."
    exit 1
fi

run_sudo mkdir -p "$STAGED_THUMBS"
page=1
for thumb in "$PKG"/assets/apac-dc-en/thumbs/page-*.png; do
    run_sudo cp "$thumb" "$STAGED_THUMBS/$page.png"
    page=$((page + 1))
done
if [[ "$page" -ne 27 ]]; then
    echo "Thumbnail count mismatch: expected 26, got $((page - 1))"
    exit 1
fi
run_sudo chown -R 1000:1000 "$STAGED_HTML" "$STAGED_THUMBS" 2>/dev/null || true
run_sudo chmod 644 "$STAGED_HTML" "$STAGED_THUMBS"/*.png
run_sudo chmod 755 "$STAGED_THUMBS"

if run_sudo test -f "$LIVE_HTML"; then
    run_sudo mv "$LIVE_HTML" "$OLD_HTML"
    HAD_HTML=1
fi
if run_sudo test -d "$LIVE_THUMBS"; then
    if ! run_sudo mv "$LIVE_THUMBS" "$OLD_THUMBS"; then
        if [[ "$HAD_HTML" -eq 1 ]]; then
            run_sudo mv "$OLD_HTML" "$LIVE_HTML"
        fi
        echo "Could not stage the previous thumbnails; course assets were not switched."
        exit 1
    fi
    HAD_THUMBS=1
fi

SWITCH_ACTIVE=1
run_sudo mv "$STAGED_HTML" "$LIVE_HTML"
run_sudo mv "$STAGED_THUMBS" "$LIVE_THUMBS"

echo "[4/4] Uploading the original PPT, registering both courses and deriving the Wiki article"
run_docker exec "$APP_CONTAINER" python3 \
    /app/deploy/knowledge-content/publish_apac_dc.py \
    --market sg --commit --skip-assets --has-thumbs

SWITCH_ACTIVE=0
run_sudo rm -f "$OLD_HTML" "$TMP_HTML"
run_sudo rm -rf "$OLD_THUMBS"
trap - EXIT

echo "[SG-NAS/pma_sa] Complete: /wiki/play/$KEY"
