#!/bin/bash

# PMA 项目云端存储模式启动脚本
# 使用 Supabase 云端配置启动本地开发服务器

echo "🚀 启动 PMA 应用（使用云端存储配置）"
echo "============================================"

# 检查配置文件是否存在
if [ ! -f ".env.supabase.storage" ]; then
    echo "❌ 错误：未找到 .env.supabase.storage 配置文件"
    echo "   请确保该文件存在于项目根目录"
    exit 1
fi

echo "📁 正在加载 Supabase 存储配置..."
export $(cat .env.supabase.storage | grep -v '^#' | xargs)

# 验证关键配置是否加载
if [ -z "$SUPABASE_URL" ]; then
    echo "❌ 错误：SUPABASE_URL 未设置"
    exit 1
fi

if [ -z "$SUPABASE_KEY" ]; then
    echo "❌ 错误：SUPABASE_KEY 未设置"
    exit 1
fi

echo "✅ 配置加载完成"
echo "   📡 Supabase URL: ${SUPABASE_URL:0:30}..."
echo "   🔑 Supabase Key: ${SUPABASE_KEY:0:8}...${SUPABASE_KEY: -4}"
echo "   ☁️  强制云端上传: $FORCE_CLOUD_UPLOAD"
echo "   📦 产品存储桶: $SUPABASE_BUCKET_PRODUCT"
echo "   📦 研发产品存储桶: $SUPABASE_BUCKET_RD_PRODUCT"

echo ""
echo "🌟 启动应用服务器..."
echo "   端口: 5016"
echo "   模式: 云端存储"
echo "   访问地址: http://localhost:5016"
echo ""

# 启动应用
python3 run.py --port 5016

echo ""
echo "👋 应用已停止"