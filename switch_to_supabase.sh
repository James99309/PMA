#!/bin/bash
# ==================== 切换到Supabase数据库脚本 ====================
# 用于快速将应用切换到Supabase数据库

echo "🚀 开始切换到Supabase数据库..."

# 备份当前.env文件
if [ -f ".env" ]; then
    echo "📁 备份当前.env文件到.env.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# 切换到Supabase配置
echo "🔄 切换到Supabase配置..."
cp .env.supabase .env

# 验证配置
echo "✅ 验证Supabase数据库连接..."
python3 -c "
import sys
sys.path.append('.')
try:
    from config_supabase_migration import verify_database_connection
    if verify_database_connection():
        print('✅ Supabase数据库连接验证成功!')
    else:
        print('❌ Supabase数据库连接验证失败!')
        sys.exit(1)
except Exception as e:
    print(f'❌ 配置验证失败: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "🎉 成功切换到Supabase数据库!"
    echo "📋 下一步："
    echo "   1. 重启应用服务"
    echo "   2. 验证应用功能"
    echo "   3. 如需回滚，运行: bash switch_to_render.sh"
else
    echo "💥 切换失败，请检查配置"
    exit 1
fi