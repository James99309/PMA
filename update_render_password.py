#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库密码修复工具
用于解决密码验证失败的问题

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
import configparser
import json
import re
from urllib.parse import urlparse, parse_qs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('密码修复工具')

# 正确的数据库连接信息
CORRECT_DB_INFO = {
    'host': 'dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com',
    'user': 'pma_db_sp8d_user',
    'password': 'LXNGJmR6bFrNecoaWbdbdzPpltIAd40w',
    'dbname': 'pma_db_sp8d',
    'port': 5432
}

# 错误的数据库用户
INCORRECT_USERS = [
    'pma_db_08cz_user'
]

def parse_db_url(url):
    """解析数据库URL"""
    if not url:
        return {}
    
    # 确保URL是postgresql://开头
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    
    try:
        result = urlparse(url)
        username = result.username
        password = result.password
        host = result.hostname
        port = result.port or 5432
        dbname = result.path.lstrip('/')
        
        return {
            'user': username,
            'password': password,
            'host': host,
            'port': port,
            'dbname': dbname
        }
    except Exception as e:
        logger.error(f"解析数据库URL错误: {e}")
        return {}

def get_db_info_from_env():
    """从环境变量获取数据库连接信息"""
    db_url = os.environ.get('DATABASE_URL', '')
    sqlalchemy_uri = os.environ.get('SQLALCHEMY_DATABASE_URI', '')
    
    logger.info(f"当前数据库URL: {mask_sensitive_info(db_url)}")
    
    db_info = parse_db_url(db_url) or parse_db_url(sqlalchemy_uri)
    return db_info

def mask_sensitive_info(url):
    """掩盖敏感信息"""
    if not url:
        return ""
    
    if '@' in url:
        # 掩盖密码部分
        parts = url.split('@')
        auth_part = parts[0]
        if ':' in auth_part:
            username_part = auth_part.split(':')[0]
            masked_url = f"{username_part}:******@{parts[1]}"
            return masked_url
    
    return url

def find_config_files():
    """查找可能包含数据库配置的文件"""
    config_files = []
    for dirpath, _, filenames in os.walk('.'):
        for filename in filenames:
            if filename.endswith(('.py', '.ini', '.cfg', '.json', '.env')):
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    try:
                        content = f.read()
                        if any(user in content for user in INCORRECT_USERS):
                            config_files.append(filepath)
                            logger.info(f"找到包含错误用户的文件: {filepath}")
                    except Exception as e:
                        logger.error(f"读取文件 {filepath} 时出错: {e}")
    return config_files

def update_config_file(filepath):
    """更新配置文件中的数据库信息"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 更新用户名
    for user in INCORRECT_USERS:
        content = content.replace(user, CORRECT_DB_INFO['user'])
    
    # 通用数据库URL模式替换
    db_url_pattern = r'(postgres(?:ql)?://)[^:]+:[^@]+@([^/]+)/([^?]+)'
    replacement = f"\\1{CORRECT_DB_INFO['user']}:{CORRECT_DB_INFO['password']}@{CORRECT_DB_INFO['host']}/{CORRECT_DB_INFO['dbname']}"
    content = re.sub(db_url_pattern, replacement, content)
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"已更新文件 {filepath}")

def create_direct_update_script():
    """创建直接在服务器上更新数据库URL的脚本"""
    correct_db_url = f"postgresql://{CORRECT_DB_INFO['user']}:{CORRECT_DB_INFO['password']}@{CORRECT_DB_INFO['host']}/{CORRECT_DB_INFO['dbname']}"
    
    script = f"""#!/bin/bash
# 直接更新数据库URL

# 设置正确的环境变量
export DATABASE_URL="{correct_db_url}"
export SQLALCHEMY_DATABASE_URI="{correct_db_url}"
export PGSSLMODE="require"
export SSL_MODE="require"

# 输出更新后的信息
echo "环境变量已更新:"
echo "DATABASE_URL=${DATABASE_URL}"
echo "SQLALCHEMY_DATABASE_URI=${SQLALCHEMY_DATABASE_URI}"

# 应用启动准备
echo "数据库环境已准备完成"
"""
    
    with open('direct_db_update.sh', 'w') as f:
        f.write(script)
    
    os.chmod('direct_db_update.sh', 0o755)
    logger.info("已创建服务器直接更新脚本: direct_db_update.sh")

def update_render_env_vars():
    """生成用于更新Render环境变量的JSON"""
    correct_db_url = f"postgresql://{CORRECT_DB_INFO['user']}:{CORRECT_DB_INFO['password']}@{CORRECT_DB_INFO['host']}/{CORRECT_DB_INFO['dbname']}"
    
    env_vars = {
        "DATABASE_URL": correct_db_url,
        "SQLALCHEMY_DATABASE_URI": correct_db_url,
        "PGSSLMODE": "require",
        "SSL_MODE": "require",
        "RENDER": "true"
    }
    
    with open("render_env_vars.json", "w") as f:
        json.dump({"envVars": env_vars}, f, indent=2)
    
    logger.info("已生成Render环境变量JSON文件: render_env_vars.json")
    logger.info("请在Render控制台导入这些环境变量")

def main():
    """主函数"""
    logger.info("开始修复数据库密码问题...")
    
    # 获取当前数据库信息
    db_info = get_db_info_from_env()
    if db_info:
        logger.info(f"当前数据库用户: {db_info.get('user')}")
        logger.info(f"当前数据库主机: {db_info.get('host')}")
        
        if db_info.get('user') in INCORRECT_USERS:
            logger.warning(f"检测到错误的数据库用户: {db_info.get('user')}")
    
    # 查找包含错误配置的文件
    config_files = find_config_files()
    
    # 更新配置文件
    for filepath in config_files:
        update_config_file(filepath)
    
    # 创建直接更新脚本
    create_direct_update_script()
    
    # 生成Render环境变量JSON
    update_render_env_vars()
    
    logger.info("密码修复完成。请执行以下步骤:")
    logger.info("1. 在Render服务器上运行: source direct_db_update.sh")
    logger.info("2. 在Render控制台更新环境变量")
    logger.info("3. 重新部署应用")

if __name__ == "__main__":
    main() 