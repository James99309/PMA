#!/bin/bash

# PMA快速启动脚本 - 本地开发专用
# 简化版本，快速启动本地开发环境

echo "🚀 PMA本地开发快速启动"
echo "======================"

# 确保安全锁定文件存在
if [ ! -f ".cloud_db_locked" ]; then
    echo "🔒 创建安全锁定文件..."
    echo "CLOUD_DB_ACCESS=DISABLED" > .cloud_db_locked
fi

# 强力关闭现有进程
echo "🔄 关闭现有进程..."
# 简单粗暴但有效的方法
killall python3 2>/dev/null || true
sleep 2
echo "   ✅ 进程清理完成"

# 查找可用端口的改进版本
find_port() {
    echo "🔍 查找可用端口..."
    for port in 5001 5002 5003 5004 5005 5006 5007 5008 8001 8002 8003; do
        # 使用nc命令检查端口，更可靠
        if ! nc -z localhost $port 2>/dev/null; then
            echo "   ✅ 端口 $port 可用"
            echo $port
            return 0
        else
            echo "   ❌ 端口 $port 被占用"
        fi
    done
    echo "   ⚠️  所有端口都被占用，使用默认端口 5001"
    echo 5001
    return 1
}

PORT=$(find_port)
echo "📍 使用端口: $PORT"

# 设置环境变量
export DATABASE_URL="postgresql://localhost/pma_local"
export FLASK_ENV="development"
export FLASK_DEBUG="1"
export LOCAL_ONLY_MODE="1"
export CLOUD_DB_ACCESS="DISABLED"

echo "🔒 本地安全模式已启用"
echo "📍 访问地址: http://localhost:$PORT"
echo "📍 网络地址: http://192.168.1.14:$PORT"
echo "======================"

# 最后检查端口是否真的可用
if nc -z localhost $PORT 2>/dev/null; then
    echo "❌ 端口 $PORT 仍然被占用，尝试强制清理..."
    # 尝试找到并杀死占用端口的进程
    PID=$(lsof -ti:$PORT 2>/dev/null)
    if [ ! -z "$PID" ]; then
        kill -9 $PID 2>/dev/null || true
        sleep 2
    fi
fi

# 启动应用
echo "🚀 启动应用..."
python3 run.py --port $PORT 