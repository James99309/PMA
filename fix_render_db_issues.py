#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Render部署中的数据库连接问题

该脚本专门用于解决"could not translate host name 'postgres' to address"问题，
检查并修复所有可能的硬编码数据库配置。
"""

import os
import sys
import re
import logging
from sqlalchemy import create_engine, text
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def fix_database_url():
    """
    修复环境变量中的数据库URL
    """
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量!")
        return None
    
    logger.info(f"原始DATABASE_URL: {database_url}")
    
    # 修复协议
    if database_url.startswith('postgres://'):
        fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info(f"修复后的DATABASE_URL: {fixed_url}")
        os.environ['DATABASE_URL'] = fixed_url
        return fixed_url
    
    return database_url

def patch_app_configuration():
    """
    在运行时修复应用程序配置
    """
    # 修补配置文件
    config_path = 'config.py'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            content = f.read()
        
        # 检查是否有硬编码的postgres主机引用
        if 'host="postgres"' in content or "host='postgres'" in content:
            logger.warning("发现硬编码的postgres主机配置")
            
            # 替换硬编码的postgres主机
            patched_content = re.sub(
                r'host\s*=\s*[\'"]postgres[\'"]', 
                'host=os.environ.get("DATABASE_HOST", "localhost")', 
                content
            )
            
            with open(config_path, 'w') as f:
                f.write(patched_content)
            
            logger.info(f"已修复 {config_path} 中的硬编码主机名")
    
    # 检查app/__init__.py文件
    init_path = os.path.join('app', '__init__.py')
    if os.path.exists(init_path):
        with open(init_path, 'r') as f:
            content = f.read()
        
        # 检查是否有硬编码的postgres引用
        if 'postgres' in content and ('host="postgres"' in content or "host='postgres'" in content):
            logger.warning(f"发现 {init_path} 中硬编码的postgres主机配置")
            
            # 替换硬编码的postgres主机
            patched_content = re.sub(
                r'host\s*=\s*[\'"]postgres[\'"]', 
                'host=os.environ.get("DATABASE_HOST", "localhost")', 
                content
            )
            
            with open(init_path, 'w') as f:
                f.write(patched_content)
            
            logger.info(f"已修复 {init_path} 中的硬编码主机名")

def create_database_environment_file():
    """
    创建一个包含正确数据库配置的临时.env文件
    """
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量，无法创建环境文件")
        return
    
    # 修复URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # 从URL提取组件
    # 格式: postgresql://username:password@host:port/database
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if not match:
        logger.error(f"无法解析数据库URL: {database_url}")
        return
    
    username, password, host, port, database = match.groups()
    
    # 创建环境变量文件
    env_content = f"""# 数据库配置
DATABASE_URL={database_url}
DATABASE_HOST={host}
DATABASE_PORT={port}
DATABASE_NAME={database}
DATABASE_USER={username}
DATABASE_PASSWORD={password}
"""
    
    with open('.env.db', 'w') as f:
        f.write(env_content)
    
    logger.info("已创建数据库环境文件 .env.db")
    logger.info(f"主机名: {host}")
    logger.info(f"端口: {port}")
    logger.info(f"数据库名: {database}")

def patch_wsgi_for_render():
    """
    修补wsgi.py文件，确保在Render环境中正确加载数据库配置
    """
    wsgi_path = 'wsgi.py'
    if not os.path.exists(wsgi_path):
        logger.error(f"找不到wsgi.py文件")
        return
    
    with open(wsgi_path, 'r') as f:
        content = f.read()
    
    # 检查内容，确保我们不会重复添加修复代码
    if 'RENDER环境数据库修复' in content:
        logger.info("wsgi.py已包含数据库修复代码，跳过")
        return
    
    # 在导入前添加修复代码
    patch_code = """
# RENDER环境数据库修复
import os
import re

# 修复数据库URL
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
    os.environ['DATABASE_URL'] = fixed_url
    print(f"已修复DATABASE_URL: {fixed_url}")

"""
    
    # 在第一个导入语句之前添加修复代码
    import_match = re.search(r'^import', content, re.MULTILINE)
    if import_match:
        insert_pos = import_match.start()
        patched_content = content[:insert_pos] + patch_code + content[insert_pos:]
        
        with open(wsgi_path, 'w') as f:
            f.write(patched_content)
        
        logger.info(f"已修补 {wsgi_path} 添加数据库URL修复")
    else:
        logger.warning(f"无法在 {wsgi_path} 中找到适当的位置添加修复代码")

def test_connection(url=None):
    """测试数据库连接"""
    if not url:
        url = os.environ.get('DATABASE_URL')
        if not url:
            logger.error("未找到数据库URL，无法测试连接")
            return False
        
        # 修复URL格式
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
    
    try:
        logger.info(f"测试连接到: {url}")
        engine = create_engine(url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("数据库连接成功!")
                return True
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
    
    return False

def print_render_environment():
    """打印Render环境信息"""
    logger.info("=== Render环境信息 ===")
    
    # 打印相关环境变量
    env_vars = [
        'DATABASE_URL', 'RENDER', 'RENDER_SERVICE_ID', 
        'RENDER_INSTANCE_ID', 'RENDER_SERVICE_TYPE'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # 隐藏敏感信息
            if var == 'DATABASE_URL' and 'postgres' in value:
                # 隐藏密码
                value = re.sub(r':[^@]+@', ':******@', value)
            logger.info(f"{var}: {value}")
    
    # 打印主机名
    try:
        hostname = subprocess.check_output(['hostname'], text=True).strip()
        logger.info(f"主机名: {hostname}")
    except:
        pass
    
    # 打印网络信息
    try:
        dns_info = subprocess.check_output(['cat', '/etc/resolv.conf'], text=True).strip()
        logger.info(f"DNS配置:\n{dns_info}")
    except:
        pass

if __name__ == "__main__":
    logger.info("开始修复Render数据库连接问题...")
    print_render_environment()
    
    # 修复环境变量
    fixed_url = fix_database_url()
    
    # 修补应用配置
    patch_app_configuration()
    
    # 创建数据库环境文件
    create_database_environment_file()
    
    # 修补wsgi.py
    patch_wsgi_for_render()
    
    # 测试连接
    if fixed_url:
        test_connection(fixed_url)
    
    logger.info("数据库连接问题修复完成") 