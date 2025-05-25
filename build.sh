#!/usr/bin/env bash
# Render平台构建脚本

# 退出前打印错误
set -e

# 安装Python依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 应用本地数据库结构
echo "应用本地数据库结构..."
if [ -f "apply_schema_on_render.py" ]; then
    python apply_schema_on_render.py
else
    echo "未找到apply_schema_on_render.py，跳过结构应用"
fi

# 修复数据库结构问题
echo "修复数据库结构问题..."
if [ -f "render_db_fix.py" ]; then
    python render_db_fix.py
else
    echo "未找到render_db_fix.py，跳过结构修复"
fi

# 执行数据库迁移
echo "执行数据库迁移..."
python manage.py db upgrade

# 构建完成
echo "构建完成!"
