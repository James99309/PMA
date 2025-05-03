#!/bin/bash
# Render环境构建脚本更新
# 用于确保在Render构建过程中执行数据库修复脚本

echo "准备更新Render构建脚本..."

# 创建新的build.sh内容
cat > new_build.sh << 'EOL'
#!/usr/bin/env bash
# Render平台构建脚本

# 退出前打印错误
set -e

# 安装Python依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 修复数据库结构问题
echo "修复数据库结构问题..."
python render_db_fix.py

# 执行数据库迁移
echo "执行数据库迁移..."
python manage.py db upgrade

# 构建完成
echo "构建完成!"
EOL

# 检查当前build.sh是否存在
if [ -f build.sh ]; then
  # 备份旧的build.sh
  cp build.sh build.sh.bak
  echo "已备份原build.sh为build.sh.bak"
  
  # 替换build.sh
  mv new_build.sh build.sh
  chmod +x build.sh
  echo "已更新build.sh"
else
  # 创建新的build.sh
  mv new_build.sh build.sh
  chmod +x build.sh
  echo "已创建新的build.sh"
fi

echo "============================================================"
echo "请确保将以下文件上传到Render服务器:"
echo "1. render_db_fix.py    - 数据库修复脚本"
echo "2. build.sh            - 更新后的构建脚本"
echo "============================================================" 