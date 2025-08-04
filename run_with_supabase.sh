#!/bin/bash

echo "🚀 启动本地应用，使用 Supabase 云端上传..."

# 加载 Supabase 环境变量
if [ -f ".env.supabase" ]; then
    echo "📁 加载 Supabase 配置..."
    export $(cat .env.supabase | grep -v '^#' | xargs)
    echo "✅ Supabase 配置已加载"
    echo "   SUPABASE_URL: $SUPABASE_URL"
    echo "   SUPABASE_BUCKET: $SUPABASE_BUCKET"
    echo "   FORCE_CLOUD_UPLOAD: $FORCE_CLOUD_UPLOAD"
else
    echo "❌ 未找到 .env.supabase 文件"
    exit 1
fi

echo ""
echo "🧪 运行 Supabase 上传测试..."
python3 test_supabase_upload.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Supabase 测试通过！启动应用..."
    echo ""
    
    # 启动 Flask 应用
    python3 run.py
else
    echo ""
    echo "❌ Supabase 测试失败，请检查配置"
    exit 1
fi