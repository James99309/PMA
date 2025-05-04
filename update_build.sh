#!/bin/bash
# Render构建脚本更新

# 检查是否为Render环境
if [ "$RENDER" != "true" ]; then
  echo "警告: 该脚本应该在Render环境中运行"
fi

# 添加数据库修复脚本到build.sh
cat > new_build.sh << 'EOL'
#!/usr/bin/env bash
# 用于Render平台的构建脚本

# 退出前打印错误
set -e

# 安装Python依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 修复数据库结构
echo "修复数据库结构问题..."
python fix_render_db.py

# 运行数据库迁移
echo "执行数据库迁移..."
python render_db_sync.py

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

echo "请确保fix_render_db.py已上传到Render服务器" 
# Render构建脚本更新

# 检查是否为Render环境
if [ "$RENDER" != "true" ]; then
  echo "警告: 该脚本应该在Render环境中运行"
fi

# 添加数据库修复脚本到build.sh
cat > new_build.sh << 'EOL'
#!/usr/bin/env bash
# 用于Render平台的构建脚本

# 退出前打印错误
set -e

# 安装Python依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 修复数据库结构
echo "修复数据库结构问题..."
python fix_render_db.py

# 运行数据库迁移
echo "执行数据库迁移..."
python render_db_sync.py

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

echo "请确保fix_render_db.py已上传到Render服务器" 