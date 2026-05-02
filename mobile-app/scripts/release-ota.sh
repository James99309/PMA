#!/bin/bash
# 前端 OTA 发版（Capgo）—— 改前端 JS/HTML 时用
# 用法：bash scripts/release-ota.sh "v1.x.y 描述"
set -e

cd "$(dirname "$0")/.."

VERSION_NOTE="${1:-quick update $(date +%Y-%m-%d_%H:%M)}"

echo "=== 1/3 · npm build ==="
npm run build

echo "=== 2/3 · 上传 bundle 到 Capgo ==="
# 1.0.x 系列（须 ≥ native CFBundleShortVersionString=1.0），用时间戳保证唯一
BUNDLE_VER="1.0.$(date +%Y%m%d%H%M%S)"
echo "bundle version: $BUNDLE_VER"
npx @capgo/cli@latest bundle upload \
  --bundle "$BUNDLE_VER" \
  --comment "$VERSION_NOTE" \
  --channel production

echo
echo "=== 3/3 · 完成 ==="
echo "✅ 测试者下次打开 App 后台自动下载，再次启动即新版"
echo "（可登录 https://web.capgo.app 查看分发进度）"
