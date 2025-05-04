#!/bin/bash
# Render部署修复脚本
# 在应用启动前运行，确保数据库连接正确

set -e
echo "正在运行Render部署修复脚本..."

# 显示Python版本
python --version

# 运行数据库诊断工具
echo "运行数据库诊断工具..."
python render_database_debug.py

# 运行修复脚本
echo "运行数据库修复工具..."
python fix_render_db_issues.py

# 确保wsgi.py具有执行权限
chmod +x wsgi.py

# 修复数据库URL环境变量
if [ ! -z "$DATABASE_URL" ]; then
  echo "检测到DATABASE_URL环境变量"
  
  # 保存原始URL
  ORIGINAL_URL="$DATABASE_URL"
  
  # 替换postgres://为postgresql://
  if [[ $DATABASE_URL == postgres://* ]]; then
    export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql:\/\/}"
    echo "已将DATABASE_URL从postgres://更改为postgresql://"
  fi
  
  # 检查是否包含postgres作为主机名
  if [[ $DATABASE_URL == *@postgres:* || $DATABASE_URL == *@postgres/* ]]; then
    echo "警告: DATABASE_URL包含'postgres'作为主机名，这在Render环境中不工作"
    
    # 如果有提供RENDER_DATABASE_URL，则使用它
    if [ ! -z "$RENDER_DATABASE_URL" ]; then
      export DATABASE_URL="$RENDER_DATABASE_URL"
      echo "已使用RENDER_DATABASE_URL替换DATABASE_URL"
    fi
  fi
else
  echo "警告: 未找到DATABASE_URL环境变量"
fi

# 显示关键环境变量(隐藏密码)
echo "当前环境变量:"
# 显示不含密码的数据库URL
if [ ! -z "$DATABASE_URL" ]; then
  MASKED_URL=$(echo "$DATABASE_URL" | sed -E 's/\/\/([^:]+):([^@]+)@/\/\/\1:******@/g')
  echo "DATABASE_URL=$MASKED_URL"
fi

echo "修复完成，准备启动应用..."
exec "$@" 
# Render部署修复脚本
# 在应用启动前运行，确保数据库连接正确

set -e
echo "正在运行Render部署修复脚本..."

# 显示Python版本
python --version

# 运行数据库诊断工具
echo "运行数据库诊断工具..."
python render_database_debug.py

# 运行修复脚本
echo "运行数据库修复工具..."
python fix_render_db_issues.py

# 确保wsgi.py具有执行权限
chmod +x wsgi.py

# 修复数据库URL环境变量
if [ ! -z "$DATABASE_URL" ]; then
  echo "检测到DATABASE_URL环境变量"
  
  # 保存原始URL
  ORIGINAL_URL="$DATABASE_URL"
  
  # 替换postgres://为postgresql://
  if [[ $DATABASE_URL == postgres://* ]]; then
    export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql:\/\/}"
    echo "已将DATABASE_URL从postgres://更改为postgresql://"
  fi
  
  # 检查是否包含postgres作为主机名
  if [[ $DATABASE_URL == *@postgres:* || $DATABASE_URL == *@postgres/* ]]; then
    echo "警告: DATABASE_URL包含'postgres'作为主机名，这在Render环境中不工作"
    
    # 如果有提供RENDER_DATABASE_URL，则使用它
    if [ ! -z "$RENDER_DATABASE_URL" ]; then
      export DATABASE_URL="$RENDER_DATABASE_URL"
      echo "已使用RENDER_DATABASE_URL替换DATABASE_URL"
    fi
  fi
else
  echo "警告: 未找到DATABASE_URL环境变量"
fi

# 显示关键环境变量(隐藏密码)
echo "当前环境变量:"
# 显示不含密码的数据库URL
if [ ! -z "$DATABASE_URL" ]; then
  MASKED_URL=$(echo "$DATABASE_URL" | sed -E 's/\/\/([^:]+):([^@]+)@/\/\/\1:******@/g')
  echo "DATABASE_URL=$MASKED_URL"
fi

echo "修复完成，准备启动应用..."
exec "$@" 
 
 
# Render部署修复脚本
# 在应用启动前运行，确保数据库连接正确

set -e
echo "正在运行Render部署修复脚本..."

# 显示Python版本
python --version

# 运行数据库诊断工具
echo "运行数据库诊断工具..."
python render_database_debug.py

# 运行修复脚本
echo "运行数据库修复工具..."
python fix_render_db_issues.py

# 确保wsgi.py具有执行权限
chmod +x wsgi.py

# 修复数据库URL环境变量
if [ ! -z "$DATABASE_URL" ]; then
  echo "检测到DATABASE_URL环境变量"
  
  # 保存原始URL
  ORIGINAL_URL="$DATABASE_URL"
  
  # 替换postgres://为postgresql://
  if [[ $DATABASE_URL == postgres://* ]]; then
    export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql:\/\/}"
    echo "已将DATABASE_URL从postgres://更改为postgresql://"
  fi
  
  # 检查是否包含postgres作为主机名
  if [[ $DATABASE_URL == *@postgres:* || $DATABASE_URL == *@postgres/* ]]; then
    echo "警告: DATABASE_URL包含'postgres'作为主机名，这在Render环境中不工作"
    
    # 如果有提供RENDER_DATABASE_URL，则使用它
    if [ ! -z "$RENDER_DATABASE_URL" ]; then
      export DATABASE_URL="$RENDER_DATABASE_URL"
      echo "已使用RENDER_DATABASE_URL替换DATABASE_URL"
    fi
  fi
else
  echo "警告: 未找到DATABASE_URL环境变量"
fi

# 显示关键环境变量(隐藏密码)
echo "当前环境变量:"
# 显示不含密码的数据库URL
if [ ! -z "$DATABASE_URL" ]; then
  MASKED_URL=$(echo "$DATABASE_URL" | sed -E 's/\/\/([^:]+):([^@]+)@/\/\/\1:******@/g')
  echo "DATABASE_URL=$MASKED_URL"
fi

echo "修复完成，准备启动应用..."
exec "$@" 
# Render部署修复脚本
# 在应用启动前运行，确保数据库连接正确

set -e
echo "正在运行Render部署修复脚本..."

# 显示Python版本
python --version

# 运行数据库诊断工具
echo "运行数据库诊断工具..."
python render_database_debug.py

# 运行修复脚本
echo "运行数据库修复工具..."
python fix_render_db_issues.py

# 确保wsgi.py具有执行权限
chmod +x wsgi.py

# 修复数据库URL环境变量
if [ ! -z "$DATABASE_URL" ]; then
  echo "检测到DATABASE_URL环境变量"
  
  # 保存原始URL
  ORIGINAL_URL="$DATABASE_URL"
  
  # 替换postgres://为postgresql://
  if [[ $DATABASE_URL == postgres://* ]]; then
    export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql:\/\/}"
    echo "已将DATABASE_URL从postgres://更改为postgresql://"
  fi
  
  # 检查是否包含postgres作为主机名
  if [[ $DATABASE_URL == *@postgres:* || $DATABASE_URL == *@postgres/* ]]; then
    echo "警告: DATABASE_URL包含'postgres'作为主机名，这在Render环境中不工作"
    
    # 如果有提供RENDER_DATABASE_URL，则使用它
    if [ ! -z "$RENDER_DATABASE_URL" ]; then
      export DATABASE_URL="$RENDER_DATABASE_URL"
      echo "已使用RENDER_DATABASE_URL替换DATABASE_URL"
    fi
  fi
else
  echo "警告: 未找到DATABASE_URL环境变量"
fi

# 显示关键环境变量(隐藏密码)
echo "当前环境变量:"
# 显示不含密码的数据库URL
if [ ! -z "$DATABASE_URL" ]; then
  MASKED_URL=$(echo "$DATABASE_URL" | sed -E 's/\/\/([^:]+):([^@]+)@/\/\/\1:******@/g')
  echo "DATABASE_URL=$MASKED_URL"
fi

echo "修复完成，准备启动应用..."
exec "$@" 
 
 