#!/bin/bash
# 后端 Flask 一键重部署到 Mac mini
# 用法：bash scripts/redeploy-backend.sh
# 流程：本地 git push gitea → ssh Mac mini pull + 重启 Flask
set -e

echo "=== 1/3 · push to Gitea ==="
git push gitea feature/mobile-api 2>&1 | tail -3

echo
echo "=== 2/3 · Mac mini: pull + 重启 Flask ==="
ssh jing@100.110.41.83 'export PATH=/opt/homebrew/bin:$PATH
cd ~/Documents/pma-mobile-test

echo "--- backup local-only files ---"
cp .env .env.runtime-bak 2>/dev/null || true
HAS_BAK=$([ -f .env.sp8d.local.bak ] && echo yes || echo no)

echo "--- fetch + hard-reset to remote (avoid merge conflicts) ---"
git fetch origin --quiet
git reset --hard origin/feature/mobile-api 2>&1 | tail -2

echo "--- restore .env + neutralize .env.sp8d.local override ---"
[ -f .env.runtime-bak ] && mv .env.runtime-bak .env
mv .env.sp8d.local .env.sp8d.local.bak 2>/dev/null || true
mv .env.local .env.local.bak 2>/dev/null || true

echo "--- run migrations if any ---"
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib ./venv/bin/flask db upgrade heads 2>&1 | tail -2 || true

echo "--- restart Flask (force kill anything on 5099) ---"
lsof -tnP -iTCP:5099 -sTCP:LISTEN 2>/dev/null | xargs kill -9 2>/dev/null
sleep 2
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib nohup ./venv/bin/python run.py > logs/flask.log 2>&1 &
sleep 5
echo "--- port check ---"
lsof -nP -iTCP:5099 -sTCP:LISTEN 2>/dev/null | head -3
'

echo
echo "=== 3/3 · 公网 ping ==="
curl -sS -o /dev/null -w "HTTP %{http_code}\n" https://pma-test.jamesgpone.win/api/v1/auth/login -X POST -H 'Content-Type: application/json' -d '{}'
echo "✅ 完成（HTTP 400 = 后端已响应，401 = 认证逻辑就位）"
