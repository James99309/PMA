#!/bin/bash
# 群晖 SSH 一键连接脚本
# 用法: ./ssh-nas.sh [隧道地址]

TUNNEL_HOST="${1:-penalties-requested-bridge-gif.trycloudflare.com}"
LOCAL_PORT=2222

# 检查 cloudflared 是否安装
if ! command -v cloudflared &> /dev/null; then
    echo "正在安装 cloudflared..."
    brew install cloudflared
fi

# 杀掉之前的代理进程
pkill -f "cloudflared access tcp.*localhost:${LOCAL_PORT}" 2>/dev/null

# 后台启动代理
cloudflared access tcp --hostname ${TUNNEL_HOST} --url localhost:${LOCAL_PORT} &
PROXY_PID=$!

# 等待代理启动
sleep 2

# 检查代理是否启动成功
if ! kill -0 $PROXY_PID 2>/dev/null; then
    echo "代理启动失败"
    exit 1
fi

echo "代理已启动 (PID: $PROXY_PID)"
echo "连接到群晖..."
echo ""

# SSH 连接
ssh -o StrictHostKeyChecking=no -p ${LOCAL_PORT} admin@localhost

# SSH 断开后杀掉代理
kill $PROXY_PID 2>/dev/null
echo ""
echo "连接已断开，代理已关闭"
