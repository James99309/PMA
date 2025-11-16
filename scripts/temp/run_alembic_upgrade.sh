#!/bin/bash
# 简单的Alembic迁移升级脚本

cd /Users/nijie/Documents/PMA

# 从.env文件读取数据库配置
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep DATABASE_URL | xargs)
fi

# 显示当前配置
echo "📋 数据库配置："
echo "DATABASE_URL: ${DATABASE_URL}"

# 显示当前版本
echo -e "\n📌 当前数据库版本："
alembic -c migrations/alembic.ini current

# 执行升级
echo -e "\n🚀 执行迁移升级..."
alembic -c migrations/alembic.ini upgrade head

# 显示新版本
echo -e "\n✅ 升级完成，新版本："
alembic -c migrations/alembic.ini current
