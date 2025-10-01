#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具 - 环境变量设置版本
通过设置psycopg2使用的环境变量来禁用SSL验证
"""

import os
import sys
import logging
import subprocess
import tempfile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render SSL环境变量')

def setup_ssl_env():
    """设置SSL环境变量"""
    # 禁用SSL证书验证
    os.environ['PGSSLMODE'] = 'require'
    os.environ['PGSSLROOTCERT'] = 'none'  # 禁用根证书验证
    
    # 或者尝试以下设置
    # os.environ['PGSSLMODE'] = 'allow'
    # os.environ['PGSSLROOTCERT'] = ''
    
    logger.info("已设置SSL环境变量:")
    logger.info(f"PGSSLMODE={os.environ.get('PGSSLMODE')}")
    logger.info(f"PGSSLROOTCERT={os.environ.get('PGSSLROOTCERT')}")

def test_connection(db_url):
    """测试数据库连接"""
    logger.info("使用psql命令行测试连接...")
    
    # 创建一个临时文件来存储连接信息，避免密码在命令行中暴露
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp.write(f"{db_url}")
        temp_path = temp.name
    
    # 构建psql命令
    cmd = f"PGPASSFILE={temp_path} psql \"{db_url}\" -c \"SELECT version();\""
    
    try:
        # 执行命令
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 删除临时文件
        os.unlink(temp_path)
        
        if result.returncode == 0:
            logger.info("连接成功!")
            logger.info(f"PostgreSQL版本: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"连接失败: {result.stderr.strip()}")
            return False
    except Exception as e:
        # 确保删除临时文件
        os.unlink(temp_path)
        logger.error(f"连接测试异常: {str(e)}")
        return False

def main():
    # 获取数据库URL
    db_url = os.environ.get('RENDER_DB_URL')
    
    if not db_url:
        logger.error("未设置RENDER_DB_URL环境变量")
        return 1
    
    # 设置SSL环境变量
    setup_ssl_env()
    
    # 测试连接
    connection_success = test_connection(db_url)
    
    if connection_success:
        logger.info("数据库连接配置成功!")
        return 0
    else:
        logger.error("无法连接到数据库，请检查连接参数和SSL设置")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具 - 环境变量设置版本
通过设置psycopg2使用的环境变量来禁用SSL验证
"""

import os
import sys
import logging
import subprocess
import tempfile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render SSL环境变量')

def setup_ssl_env():
    """设置SSL环境变量"""
    # 禁用SSL证书验证
    os.environ['PGSSLMODE'] = 'require'
    os.environ['PGSSLROOTCERT'] = 'none'  # 禁用根证书验证
    
    # 或者尝试以下设置
    # os.environ['PGSSLMODE'] = 'allow'
    # os.environ['PGSSLROOTCERT'] = ''
    
    logger.info("已设置SSL环境变量:")
    logger.info(f"PGSSLMODE={os.environ.get('PGSSLMODE')}")
    logger.info(f"PGSSLROOTCERT={os.environ.get('PGSSLROOTCERT')}")

def test_connection(db_url):
    """测试数据库连接"""
    logger.info("使用psql命令行测试连接...")
    
    # 创建一个临时文件来存储连接信息，避免密码在命令行中暴露
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp.write(f"{db_url}")
        temp_path = temp.name
    
    # 构建psql命令
    cmd = f"PGPASSFILE={temp_path} psql \"{db_url}\" -c \"SELECT version();\""
    
    try:
        # 执行命令
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 删除临时文件
        os.unlink(temp_path)
        
        if result.returncode == 0:
            logger.info("连接成功!")
            logger.info(f"PostgreSQL版本: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"连接失败: {result.stderr.strip()}")
            return False
    except Exception as e:
        # 确保删除临时文件
        os.unlink(temp_path)
        logger.error(f"连接测试异常: {str(e)}")
        return False

def main():
    # 获取数据库URL
    db_url = os.environ.get('RENDER_DB_URL')
    
    if not db_url:
        logger.error("未设置RENDER_DB_URL环境变量")
        return 1
    
    # 设置SSL环境变量
    setup_ssl_env()
    
    # 测试连接
    connection_success = test_connection(db_url)
    
    if connection_success:
        logger.info("数据库连接配置成功!")
        return 0
    else:
        logger.error("无法连接到数据库，请检查连接参数和SSL设置")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具 - 环境变量设置版本
通过设置psycopg2使用的环境变量来禁用SSL验证
"""

import os
import sys
import logging
import subprocess
import tempfile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render SSL环境变量')

def setup_ssl_env():
    """设置SSL环境变量"""
    # 禁用SSL证书验证
    os.environ['PGSSLMODE'] = 'require'
    os.environ['PGSSLROOTCERT'] = 'none'  # 禁用根证书验证
    
    # 或者尝试以下设置
    # os.environ['PGSSLMODE'] = 'allow'
    # os.environ['PGSSLROOTCERT'] = ''
    
    logger.info("已设置SSL环境变量:")
    logger.info(f"PGSSLMODE={os.environ.get('PGSSLMODE')}")
    logger.info(f"PGSSLROOTCERT={os.environ.get('PGSSLROOTCERT')}")

def test_connection(db_url):
    """测试数据库连接"""
    logger.info("使用psql命令行测试连接...")
    
    # 创建一个临时文件来存储连接信息，避免密码在命令行中暴露
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp.write(f"{db_url}")
        temp_path = temp.name
    
    # 构建psql命令
    cmd = f"PGPASSFILE={temp_path} psql \"{db_url}\" -c \"SELECT version();\""
    
    try:
        # 执行命令
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 删除临时文件
        os.unlink(temp_path)
        
        if result.returncode == 0:
            logger.info("连接成功!")
            logger.info(f"PostgreSQL版本: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"连接失败: {result.stderr.strip()}")
            return False
    except Exception as e:
        # 确保删除临时文件
        os.unlink(temp_path)
        logger.error(f"连接测试异常: {str(e)}")
        return False

def main():
    # 获取数据库URL
    db_url = os.environ.get('RENDER_DB_URL')
    
    if not db_url:
        logger.error("未设置RENDER_DB_URL环境变量")
        return 1
    
    # 设置SSL环境变量
    setup_ssl_env()
    
    # 测试连接
    connection_success = test_connection(db_url)
    
    if connection_success:
        logger.info("数据库连接配置成功!")
        return 0
    else:
        logger.error("无法连接到数据库，请检查连接参数和SSL设置")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具 - 环境变量设置版本
通过设置psycopg2使用的环境变量来禁用SSL验证
"""

import os
import sys
import logging
import subprocess
import tempfile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render SSL环境变量')

def setup_ssl_env():
    """设置SSL环境变量"""
    # 禁用SSL证书验证
    os.environ['PGSSLMODE'] = 'require'
    os.environ['PGSSLROOTCERT'] = 'none'  # 禁用根证书验证
    
    # 或者尝试以下设置
    # os.environ['PGSSLMODE'] = 'allow'
    # os.environ['PGSSLROOTCERT'] = ''
    
    logger.info("已设置SSL环境变量:")
    logger.info(f"PGSSLMODE={os.environ.get('PGSSLMODE')}")
    logger.info(f"PGSSLROOTCERT={os.environ.get('PGSSLROOTCERT')}")

def test_connection(db_url):
    """测试数据库连接"""
    logger.info("使用psql命令行测试连接...")
    
    # 创建一个临时文件来存储连接信息，避免密码在命令行中暴露
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp.write(f"{db_url}")
        temp_path = temp.name
    
    # 构建psql命令
    cmd = f"PGPASSFILE={temp_path} psql \"{db_url}\" -c \"SELECT version();\""
    
    try:
        # 执行命令
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 删除临时文件
        os.unlink(temp_path)
        
        if result.returncode == 0:
            logger.info("连接成功!")
            logger.info(f"PostgreSQL版本: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"连接失败: {result.stderr.strip()}")
            return False
    except Exception as e:
        # 确保删除临时文件
        os.unlink(temp_path)
        logger.error(f"连接测试异常: {str(e)}")
        return False

def main():
    # 获取数据库URL
    db_url = os.environ.get('RENDER_DB_URL')
    
    if not db_url:
        logger.error("未设置RENDER_DB_URL环境变量")
        return 1
    
    # 设置SSL环境变量
    setup_ssl_env()
    
    # 测试连接
    connection_success = test_connection(db_url)
    
    if connection_success:
        logger.info("数据库连接配置成功!")
        return 0
    else:
        logger.error("无法连接到数据库，请检查连接参数和SSL设置")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 