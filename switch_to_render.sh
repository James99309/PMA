#!/bin/bash
# ==================== 切换回Render数据库脚本 ====================
# 用于快速将应用切换回Render数据库（回滚操作）

echo "🔄 开始切换回Render数据库..."

# 备份当前.env文件
if [ -f ".env" ]; then
    echo "📁 备份当前.env文件到.env.supabase.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env .env.supabase.backup.$(date +%Y%m%d_%H%M%S)
fi

# 切换回Render配置
if [ -f ".env.render.backup" ]; then
    echo "🔄 恢复Render配置..."
    cp .env.render.backup .env
    echo "✅ 已恢复到Render数据库配置"
else
    echo "❌ 未找到Render配置备份文件"
    echo "📋 请手动创建.env文件，或者："
    echo "   1. 检查是否有其他.env.backup.*文件"
    echo "   2. 手动配置Render数据库连接"
    exit 1
fi

# 验证配置
echo "✅ 验证Render数据库连接..."
python3 -c "
import sys
sys.path.append('.')
try:
    from config import verify_database_connection
    if verify_database_connection():
        print('✅ Render数据库连接验证成功!')
    else:
        print('❌ Render数据库连接验证失败!')
        sys.exit(1)
except Exception as e:
    print(f'❌ 配置验证失败: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "🎉 成功切换回Render数据库!"
    echo "📋 下一步："
    echo "   1. 重启应用服务"
    echo "   2. 验证应用功能"
else
    echo "💥 切换失败，请检查配置"
    exit 1
fi