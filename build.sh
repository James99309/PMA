#!/usr/bin/env bash
# 用于Render平台的构建脚本

# 退出前打印错误
set -e

# 安装Python依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 运行数据库迁移
echo "执行数据库迁移..."
python render_db_sync.py

# 构建完成
echo "构建完成!" 