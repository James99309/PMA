#!/bin/bash

# ============================================
# 启动本地SP8D测试实例（测试后可删除）
# ============================================

echo "🚀 启动本地SP8D实例（端口5002）..."
echo ""

# 加载SP8D配置
if [ ! -f .env.sp8d.local ]; then
    echo "❌ 错误：找不到 .env.sp8d.local 配置文件"
    echo "请先配置 .env.sp8d.local 文件"
    exit 1
fi

# 导出环境变量
export $(grep -v '^#' .env.sp8d.local | xargs)

# 设置WeasyPrint库路径
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib

# 启动Flask应用
echo "✅ 配置已加载"
echo "📊 数据库：SP8D（云端）"
echo "🔌 端口：5002"
echo "🔑 API密钥：${CROSS_SYSTEM_API_KEY}"
echo ""
echo "按 Ctrl+C 停止服务"
echo "================================"
echo ""

python3 run.py
