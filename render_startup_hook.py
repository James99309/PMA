#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render启动钩子脚本
在应用启动前自动修复数据库连接信息

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('render_startup_hook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Render启动钩子')

# 正确的数据库连接信息
CORRECT_DB_INFO = {
    'host': 'dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com',
    'user': 'pma_db_sp8d_user',
    'password': 'LXNGJmR6bFrNecoaWbdbdzPpltIAd40w',
    'dbname': 'pma_db_sp8d',
    'port': 5432
}

# 错误的信息
INCORRECT_HOSTS = [
    'dpg-d0a6s03uibrs73b5nelg-a',
    'dpg-d0a6s03uibrs73b5nelg-a.singapore-postgres.render.com'
]

INCORRECT_USERS = [
    'pma_db_08cz_user'
]

def fix_environment_variables():
    """修复环境变量"""
    db_url = os.environ.get('DATABASE_URL', '')
    sqlalchemy_uri = os.environ.get('SQLALCHEMY_DATABASE_URI', '')
    
    # 打印当前环境变量（隐藏敏感信息）
    if db_url:
        masked_db_url = re.sub(r'(:)([^@]+)(@)', r'\1******\3', db_url)
        logger.info(f"原始DATABASE_URL: {masked_db_url}")
    if sqlalchemy_uri:
        masked_uri = re.sub(r'(:)([^@]+)(@)', r'\1******\3', sqlalchemy_uri)
        logger.info(f"原始SQLALCHEMY_DATABASE_URI: {masked_uri}")
    
    # 构建正确的数据库URL
    correct_db_url = f"postgresql://{CORRECT_DB_INFO['user']}:{CORRECT_DB_INFO['password']}@{CORRECT_DB_INFO['host']}/{CORRECT_DB_INFO['dbname']}"
    
    # 检查并修复DATABASE_URL
    needs_update = False
    if db_url:
        for host in INCORRECT_HOSTS:
            if host in db_url:
                needs_update = True
                logger.warning(f"发现错误的主机名: {host}")
                break
        
        for user in INCORRECT_USERS:
            if user in db_url:
                needs_update = True
                logger.warning(f"发现错误的用户名: {user}")
                break
    
    # 如果URL以postgres://开头，转换为postgresql://
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        needs_update = True
        logger.info("已将postgres://修正为postgresql://")
    
    # 如果需要更新，设置新的环境变量
    if needs_update or not db_url:
        logger.info(f"设置正确的DATABASE_URL")
        os.environ['DATABASE_URL'] = correct_db_url
        os.environ['SQLALCHEMY_DATABASE_URI'] = correct_db_url
    
    # 设置其他必要的环境变量
    os.environ['PGSSLMODE'] = 'require'
    os.environ['SSL_MODE'] = 'require'
    os.environ['RENDER'] = 'true'
    
    # 打印最终的环境变量（隐藏敏感信息）
    final_db_url = os.environ.get('DATABASE_URL', '')
    if final_db_url:
        masked_final_url = re.sub(r'(:)([^@]+)(@)', r'\1******\3', final_db_url)
        logger.info(f"最终DATABASE_URL: {masked_final_url}")

def generate_wsgi_wrapper():
    """生成WSGI包装脚本"""
    wsgi_wrapper = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
WSGI应用包装器
在启动时自动修复数据库连接
\"\"\"

import os
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wsgi_wrapper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('WSGI包装器')

# 正确的数据库连接信息
CORRECT_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

def fix_db_env():
    \"\"\"修复数据库环境变量\"\"\"
    db_url = os.environ.get('DATABASE_URL', '')
    
    # 打印当前环境变量（隐藏敏感信息）
    if db_url:
        masked_url = db_url.split('@')[0].split(':')[0] + ':******@' + db_url.split('@')[1]
        logger.info(f"原始DATABASE_URL: {masked_url}")
    
    # 设置正确的环境变量
    os.environ['DATABASE_URL'] = CORRECT_DB_URL
    os.environ['SQLALCHEMY_DATABASE_URI'] = CORRECT_DB_URL
    os.environ['PGSSLMODE'] = 'require'
    os.environ['SSL_MODE'] = 'require'
    os.environ['RENDER'] = 'true'
    
    logger.info("环境变量已修复")

# 在导入应用前修复环境变量
fix_db_env()

# 导入原始WSGI应用
sys.path.insert(0, os.path.dirname(__file__))
from wsgi import app as original_app

# 创建包装应用
app = original_app
"""
    
    with open('wsgi_wrapper.py', 'w') as f:
        f.write(wsgi_wrapper)
    
    logger.info("已生成WSGI包装脚本: wsgi_wrapper.py")

def create_render_build_script():
    """创建Render构建脚本"""
    build_script = """#!/bin/bash
# Render构建脚本
# 自动修复数据库配置并准备应用

set -e

echo "===== 开始构建 ====="

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 创建环境变量文件
echo "创建环境变量文件..."
cat > .env << EOF
DATABASE_URL=postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d
SQLALCHEMY_DATABASE_URI=postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d
PGSSLMODE=require
SSL_MODE=require
RENDER=true
EOF

# 修复wsgi.py文件
echo "检查wsgi.py文件..."
if grep -q "dpg-d0a6s03uibrs73b5nelg-a" wsgi.py; then
  echo "修复wsgi.py中的主机名..."
  sed -i 's/dpg-d0a6s03uibrs73b5nelg-a/dpg-d0b1gl1r0fns73d1jc1g-a/g' wsgi.py
fi

if grep -q "pma_db_08cz_user" wsgi.py; then
  echo "修复wsgi.py中的用户名..."
  sed -i 's/pma_db_08cz_user/pma_db_sp8d_user/g' wsgi.py
fi

# 创建启动脚本
echo "创建启动脚本..."
cat > start.sh << EOF
#!/bin/bash
# 应用启动脚本

# 设置正确的环境变量
export DATABASE_URL="postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
export SQLALCHEMY_DATABASE_URI="\$DATABASE_URL"
export PGSSLMODE="require"
export SSL_MODE="require"
export RENDER="true"

# 启动应用
exec gunicorn wsgi:app
EOF

chmod +x start.sh

echo "===== 构建完成 ====="
"""
    
    with open('render_build.sh', 'w') as f:
        f.write(build_script)
    
    os.chmod('render_build.sh', 0o755)
    logger.info("已创建Render构建脚本: render_build.sh")

def main():
    """主函数"""
    logger.info("Render启动钩子脚本开始执行...")
    
    try:
        # 修复环境变量
        fix_environment_variables()
        
        # 生成WSGI包装脚本
        generate_wsgi_wrapper()
        
        # 创建Render构建脚本
        create_render_build_script()
        
        logger.info("启动钩子脚本执行完成")
        logger.info("请在Render控制台设置以下内容:")
        logger.info("1. 构建命令: bash render_build.sh")
        logger.info("2. 启动命令: ./start.sh")
    except Exception as e:
        logger.error(f"执行过程中出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 