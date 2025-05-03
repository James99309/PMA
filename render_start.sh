#!/bin/bash
# Render环境启动脚本 - 设置环境变量并启动应用
# 作者: Claude
# 创建日期: 2025-05-03

echo "========================="
echo "Render应用启动脚本"
echo "========================="

# 设置工作目录
cd /opt/render/project/src

# 设置环境变量
echo "设置数据库环境变量..."
export DATABASE_URL="postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
export SQLALCHEMY_DATABASE_URI="$DATABASE_URL"
export FLASK_ENV="production"
export PORT="${PORT:-10000}"
export SSL_MODE="require"
export PGSSLMODE="require"
export RENDER="true"

# 修正数据库URL（如果需要）
if [[ "$DATABASE_URL" == postgres://* ]]; then
  export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql:\/\/}"
  export SQLALCHEMY_DATABASE_URI="$DATABASE_URL"
  echo "修正数据库URL: postgres:// -> postgresql://"
fi

# 打印环境信息
echo "当前工作目录: $(pwd)"
echo "Python版本: $(python --version)"
echo "数据库URL: ${DATABASE_URL/postgresql:\/\/*@/postgresql:\/\/****@}"
echo "当前时间: $(date)"

# 测试数据库连接
echo "测试数据库连接..."
python -c "
import psycopg2
import os
try:
    db_url = os.environ.get('DATABASE_URL')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(db_url, sslmode='require')
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    print(f'成功连接到数据库: {version}')
    cursor.close()
    conn.close()
    exit(0)
except Exception as e:
    print(f'数据库连接失败: {e}')
    exit(1)
" || { echo "数据库连接测试失败，请检查配置"; exit 1; }

# 启动应用
echo "启动应用..."
exec gunicorn --log-level info wsgi:app 