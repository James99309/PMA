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

echo "=== 0/5 · git 未提交护栏(防止未固化代码静默发版) ==="
# 历史教训: 之前 49 个 bundle 持续发版, 但 push.js / utils/pdfPreview.js /
# ota_server.py / iOS 推送 native 改动等 30+ 文件全程未 commit, 一旦 worktree
# 被 checkout/reset 就丢光。强制要求发版前先 commit 到分支。
DIRTY="$(git status --porcelain)"
if [ -n "$DIRTY" ] && [ "${ALLOW_DIRTY:-0}" != "1" ]; then
  echo "❌ 检测到未提交改动, 拒绝发版:" >&2
  echo "$DIRTY" >&2
  echo "" >&2
  echo "请先 commit 到分支再发版:" >&2
  echo "  git add ... && git commit -m '...'" >&2
  echo "" >&2
  echo "如确需带脏工作目录发版(临时调试):" >&2
  echo "  ALLOW_DIRTY=1 bash scripts/release-ota.sh \"$VERSION_NOTE\"" >&2
  exit 1
fi
GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
[ -n "$DIRTY" ] && GIT_SHA="${GIT_SHA}-dirty"
echo "  git: $GIT_BRANCH @ $GIT_SHA"

echo "=== 1/5 · i18n 护栏(无新增硬编码中文才放行)==="
node scripts/i18n-guard.mjs

echo "=== 2/5 · npm build ==="
npm run build

echo "=== 3/5 · 打包 dist（平铺, index.html 在 zip 根, 排除隐藏/资源叉文件）==="
find dist -name '.DS_Store' -delete 2>/dev/null || true
TMP_DIR="$(mktemp -d)"
TMP_ZIP="${TMP_DIR}/${ZIP_NAME}"
# 进 dist 内打包 → 条目相对 dist 根, 满足 capacitor-updater unflatFolder
( cd dist && zip -rqX "$TMP_ZIP" . -x '*.DS_Store' -x '__MACOSX*' )
CHECKSUM=$(shasum -a 256 "$TMP_ZIP" | awk '{print $1}')
echo "bundle: $BUNDLE_VER  sha256: $CHECKSUM  size: $(du -h "$TMP_ZIP" | awk '{print $1}')"

echo "=== 4/5 · 部署到 Mac mini ($MACMINI_SSH:$MACMINI_OTA_DIR) ==="
ssh "$MACMINI_SSH" "mkdir -p '$MACMINI_OTA_DIR'"
scp -q "$TMP_ZIP" "$MACMINI_SSH:$MACMINI_OTA_DIR/$ZIP_NAME"
# 原子写 latest.json（先写临时再 mv, 避免设备读到半截）
ssh "$MACMINI_SSH" "cat > '$MACMINI_OTA_DIR/latest.json.tmp' && mv '$MACMINI_OTA_DIR/latest.json.tmp' '$MACMINI_OTA_DIR/latest.json'" <<EOF
{"version":"$BUNDLE_VER","checksum":"$CHECKSUM","file":"$ZIP_NAME","note":"$VERSION_NOTE","ts":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","git_sha":"$GIT_SHA","git_branch":"$GIT_BRANCH"}
EOF
rm -rf "$TMP_DIR"

echo "=== 5/5 · 完成 ==="
echo "✅ $BUNDLE_VER 已发布到自托管 OTA"
echo "   git: $GIT_BRANCH @ $GIT_SHA"
echo "   测试者下次打开 App 后台自动下载, 再次启动即新版"
echo "   验证: curl -s -X POST https://pma-test.jamesgpone.win/api/v1/ota/updates \\"
echo "         -H 'Content-Type: application/json' -d '{\"version_name\":\"builtin\"}'"
