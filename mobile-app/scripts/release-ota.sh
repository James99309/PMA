#!/bin/bash
# 前端 OTA 发版（自托管, 单点 Mac mini, 取代 Capgo）—— 改前端 JS/HTML 时用
#
# 为什么不再用 Capgo: 平台数据面对本 app 整体冻结(Cap-go/capgo#2068/#1879),
# 管理面任何改动都不传播到设备, 用户侧无法自愈。改为自托管。
#
# 用法: bash scripts/release-ota.sh "v1.x.y 描述"
# 可用环境变量覆盖: MACMINI_SSH, MACMINI_OTA_DIR
set -e

cd "$(dirname "$0")/.."   # → mobile-app/

VERSION_NOTE="${1:-quick update $(date +%Y-%m-%d_%H:%M)}"
# 1.0.x 系列（须 ≥ native CFBundleShortVersionString=1.0），时间戳保证唯一且递增
BUNDLE_VER="1.0.$(date +%Y%m%d%H%M%S)"
ZIP_NAME="pma-${BUNDLE_VER}.zip"

# 单点中心 OTA host（类比 Capgo 的 plugin.capgo.app）
MACMINI_SSH="${MACMINI_SSH:-jing@100.110.41.83}"
MACMINI_OTA_DIR="${MACMINI_OTA_DIR:-/Users/jing/pma-ota/bundles}"

echo "=== 0/4 · i18n 护栏(无新增硬编码中文才放行)==="
node scripts/i18n-guard.mjs

echo "=== 1/4 · npm build ==="
npm run build

echo "=== 2/4 · 打包 dist（平铺, index.html 在 zip 根, 排除隐藏/资源叉文件）==="
find dist -name '.DS_Store' -delete 2>/dev/null || true
TMP_DIR="$(mktemp -d)"
TMP_ZIP="${TMP_DIR}/${ZIP_NAME}"
# 进 dist 内打包 → 条目相对 dist 根, 满足 capacitor-updater unflatFolder
( cd dist && zip -rqX "$TMP_ZIP" . -x '*.DS_Store' -x '__MACOSX*' )
CHECKSUM=$(shasum -a 256 "$TMP_ZIP" | awk '{print $1}')
echo "bundle: $BUNDLE_VER  sha256: $CHECKSUM  size: $(du -h "$TMP_ZIP" | awk '{print $1}')"

echo "=== 3/4 · 部署到 Mac mini ($MACMINI_SSH:$MACMINI_OTA_DIR) ==="
ssh "$MACMINI_SSH" "mkdir -p '$MACMINI_OTA_DIR'"
scp -q "$TMP_ZIP" "$MACMINI_SSH:$MACMINI_OTA_DIR/$ZIP_NAME"
# 原子写 latest.json（先写临时再 mv, 避免设备读到半截）
ssh "$MACMINI_SSH" "cat > '$MACMINI_OTA_DIR/latest.json.tmp' && mv '$MACMINI_OTA_DIR/latest.json.tmp' '$MACMINI_OTA_DIR/latest.json'" <<EOF
{"version":"$BUNDLE_VER","checksum":"$CHECKSUM","file":"$ZIP_NAME","note":"$VERSION_NOTE","ts":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF
rm -rf "$TMP_DIR"

echo "=== 4/4 · 完成 ==="
echo "✅ $BUNDLE_VER 已发布到自托管 OTA"
echo "   测试者下次打开 App 后台自动下载, 再次启动即新版"
echo "   验证: curl -s -X POST https://pma-test.jamesgpone.win/api/v1/ota/updates \\"
echo "         -H 'Content-Type: application/json' -d '{\"version_name\":\"builtin\"}'"
