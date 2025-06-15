#!/bin/bash

echo "🚀 PMA简单启动"
echo "=============="

# 创建安全锁定
echo "CLOUD_DB_ACCESS=DISABLED" > .cloud_db_locked

# 清理进程
echo "🔄 清理进程..."
killall python3 2>/dev/null || true
sleep 2

# 查找端口
echo "🔍 查找端口..."
for port in 5001 5002 5003 5004 5005; do
    if ! nc -z localhost $port 2>/dev/null; then
        echo "✅ 使用端口: $port"
        break
    fi
done

# 设置环境
export DATABASE_URL="postgresql://localhost/pma_local"
export FLASK_ENV="development"
export LOCAL_ONLY_MODE="1"

echo "🚀 启动中..."
echo "📍 访问: http://localhost:$port"
echo "=============="

# 启动
python3 run.py --port $port 