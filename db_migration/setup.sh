#!/bin/bash

# 数据库迁移环境设置脚本
# 在Render环境中安装必要的依赖和准备执行环境

echo "开始设置数据库迁移环境..."

# 安装依赖项
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL="postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
export SQLALCHEMY_DATABASE_URI="$DATABASE_URL"
export RENDER=true

echo "环境设置完成，可以执行迁移脚本了"
echo "使用命令: python render_migration_run.py" 