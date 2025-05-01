#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 设置工作目录
WORK_DIR="/Users/nijie/Documents/PMA"
PORT=8082

# 清理进程
echo "清理进程..."
pkill -f "python.*run.py"
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
sleep 2

# 检查端口
if lsof -i:$PORT > /dev/null 2>&1; then
    echo "端口 $PORT 仍然被占用"
    exit 1
fi

# 进入工作目录
cd "$WORK_DIR" || exit 1

# 设置环境变量
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_RUN_PORT=$PORT

# 启动应用
echo "启动应用..."
python3 run.py 