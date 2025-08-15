#!/bin/bash

echo "🚀 启动本地应用，使用生产环境 Supabase 存储..."
echo "============================================================"

# 检查生产环境配置文件是否存在
if [ ! -f ".env.supabase.prod" ]; then
    echo "❌ 未找到生产环境配置文件 .env.supabase.prod"
    echo "💡 请确保文件存在并包含正确的 Supabase 配置"
    exit 1
fi

# 加载 Supabase 生产环境配置
echo "📁 加载生产环境 Supabase 配置..."
export $(cat .env.supabase.prod | grep -v '^#' | grep -v '^$' | xargs)

# 验证必要的环境变量是否设置
echo "🔍 验证 Supabase 配置..."
if [ -z "$SUPABASE_URL" ]; then
    echo "❌ SUPABASE_URL 未设置"
    exit 1
fi

if [ -z "$SUPABASE_KEY" ]; then
    echo "❌ SUPABASE_KEY 未设置"
    exit 1
fi

if [ -z "$SUPABASE_BUCKET_INVOICE" ]; then
    echo "❌ SUPABASE_BUCKET_INVOICE 未设置"
    exit 1
fi

echo "✅ Supabase 配置验证通过"
echo "   URL: $SUPABASE_URL"
echo "   发票存储桶: $SUPABASE_BUCKET_INVOICE"
echo "   产品存储桶: $SUPABASE_BUCKET_PRODUCT"
echo "   研发产品存储桶: $SUPABASE_BUCKET_RD_PRODUCT"
echo "   强制云端上传: $FORCE_CLOUD_UPLOAD"
echo ""

# 运行连接测试（如果测试脚本存在）
if [ -f "test_supabase_prod_connection.py" ]; then
    echo "🧪 运行 Supabase 生产环境连接测试..."
    python3 test_supabase_prod_connection.py
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "⚠️ Supabase 连接测试失败，但继续启动应用"
        echo "   请检查网络连接和 Supabase 配置"
    else
        echo "✅ Supabase 连接测试通过"
    fi
    echo ""
fi

# 显示重要提醒
echo "⚠️ 重要提醒："
echo "   - 当前使用生产环境 Supabase 存储"
echo "   - 所有文件上传将直接保存到生产环境"
echo "   - 请谨慎操作，避免上传测试数据到生产存储"
echo "   - 下载功能测试将使用真实生产数据"
echo ""

# 询问用户是否继续
read -p "是否继续启动应用？(y/N): " confirm
case $confirm in
    [yY]|[yY][eE][sS])
        echo ""
        echo "🎉 启动 PMA 应用（使用生产环境 Supabase 存储）..."
        echo ""
        
        # 启动 Flask 应用
        python3 run.py
        ;;
    *)
        echo ""
        echo "🛑 启动已取消"
        echo "💡 如需使用本地存储，请直接运行: python3 run.py"
        exit 0
        ;;
esac