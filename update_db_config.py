#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新数据库配置脚本
用于修改应用程序中的数据库连接信息，确保使用正确的Render数据库URL

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
import re
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_db_config.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('更新数据库配置')

# 正确的Render数据库连接信息
CORRECT_RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

# 错误的旧数据库主机名，需要被替换
OLD_HOST_PATTERN = r'dpg-d0a6s03uibrs73b5nelg-a'

# 正确的新数据库主机名
NEW_HOST = 'dpg-d0b1gl1r0fns73d1jc1g-a'

def find_config_files():
    """查找可能包含数据库配置的文件"""
    config_files = []
    
    # 常见配置文件名称
    common_config_files = [
        'config.py', 
        'settings.py', 
        '.env', 
        '.flaskenv', 
        'app/config.py',
        'app/__init__.py',
        'wsgi.py'
    ]
    
    # 检查这些文件是否存在
    for file_path in common_config_files:
        if os.path.exists(file_path):
            config_files.append(file_path)
    
    logger.info(f"找到以下可能包含配置的文件: {config_files}")
    return config_files

def update_config_files(config_files):
    """更新配置文件中的数据库连接信息"""
    for file_path in config_files:
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # 检查文件是否包含旧的主机名
            if re.search(OLD_HOST_PATTERN, content):
                # 更新内容
                new_content = re.sub(OLD_HOST_PATTERN, NEW_HOST, content)
                
                # 写入更新后的内容
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                logger.info(f"已更新文件 {file_path} 中的数据库主机名")
            else:
                logger.info(f"文件 {file_path} 不包含旧的数据库主机名")
        
        except Exception as e:
            logger.error(f"更新文件 {file_path} 时出错: {e}")

def update_env_variables():
    """生成更新环境变量的命令"""
    commands = [
        f"export DATABASE_URL='{CORRECT_RENDER_DB_URL}'",
        f"export SQLALCHEMY_DATABASE_URI='{CORRECT_RENDER_DB_URL}'"
    ]
    
    logger.info("建议手动执行以下命令更新环境变量:")
    for cmd in commands:
        logger.info(cmd)
    
    with open('update_env.sh', 'w') as file:
        file.write("#!/bin/bash\n\n")
        file.write("# 更新环境变量的脚本\n\n")
        for cmd in commands:
            file.write(f"{cmd}\n")
    
    logger.info("已创建环境变量更新脚本 update_env.sh")

def check_render_yaml():
    """检查render.yaml文件中的数据库配置"""
    if os.path.exists('render.yaml'):
        try:
            with open('render.yaml', 'r') as file:
                content = file.read()
            
            if re.search(OLD_HOST_PATTERN, content):
                new_content = re.sub(OLD_HOST_PATTERN, NEW_HOST, content)
                
                with open('render.yaml', 'w') as file:
                    file.write(new_content)
                
                logger.info("已更新 render.yaml 中的数据库主机名")
            else:
                logger.info("render.yaml 不包含旧的数据库主机名")
        
        except Exception as e:
            logger.error(f"更新 render.yaml 时出错: {e}")
    else:
        logger.info("未找到 render.yaml 文件")

def main():
    """主函数"""
    logger.info("开始更新数据库配置...")
    
    # 查找配置文件
    config_files = find_config_files()
    
    # 更新配置文件
    update_config_files(config_files)
    
    # 检查render.yaml文件
    check_render_yaml()
    
    # 生成环境变量更新命令
    update_env_variables()
    
    logger.info("数据库配置更新完成!")
    
    # 提示用户下一步操作
    logger.info("\n===== 后续步骤 =====")
    logger.info("1. 执行 'source update_env.sh' 更新环境变量")
    logger.info("2. 重启应用程序")
    logger.info("3. 检查应用日志确认数据库连接是否正常")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
更新数据库配置脚本
用于修改应用程序中的数据库连接信息，确保使用正确的Render数据库URL

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
import re
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_db_config.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('更新数据库配置')

# 正确的Render数据库连接信息
CORRECT_RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

# 错误的旧数据库主机名，需要被替换
OLD_HOST_PATTERN = r'dpg-d0a6s03uibrs73b5nelg-a'

# 正确的新数据库主机名
NEW_HOST = 'dpg-d0b1gl1r0fns73d1jc1g-a'

def find_config_files():
    """查找可能包含数据库配置的文件"""
    config_files = []
    
    # 常见配置文件名称
    common_config_files = [
        'config.py', 
        'settings.py', 
        '.env', 
        '.flaskenv', 
        'app/config.py',
        'app/__init__.py',
        'wsgi.py'
    ]
    
    # 检查这些文件是否存在
    for file_path in common_config_files:
        if os.path.exists(file_path):
            config_files.append(file_path)
    
    logger.info(f"找到以下可能包含配置的文件: {config_files}")
    return config_files

def update_config_files(config_files):
    """更新配置文件中的数据库连接信息"""
    for file_path in config_files:
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # 检查文件是否包含旧的主机名
            if re.search(OLD_HOST_PATTERN, content):
                # 更新内容
                new_content = re.sub(OLD_HOST_PATTERN, NEW_HOST, content)
                
                # 写入更新后的内容
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                logger.info(f"已更新文件 {file_path} 中的数据库主机名")
            else:
                logger.info(f"文件 {file_path} 不包含旧的数据库主机名")
        
        except Exception as e:
            logger.error(f"更新文件 {file_path} 时出错: {e}")

def update_env_variables():
    """生成更新环境变量的命令"""
    commands = [
        f"export DATABASE_URL='{CORRECT_RENDER_DB_URL}'",
        f"export SQLALCHEMY_DATABASE_URI='{CORRECT_RENDER_DB_URL}'"
    ]
    
    logger.info("建议手动执行以下命令更新环境变量:")
    for cmd in commands:
        logger.info(cmd)
    
    with open('update_env.sh', 'w') as file:
        file.write("#!/bin/bash\n\n")
        file.write("# 更新环境变量的脚本\n\n")
        for cmd in commands:
            file.write(f"{cmd}\n")
    
    logger.info("已创建环境变量更新脚本 update_env.sh")

def check_render_yaml():
    """检查render.yaml文件中的数据库配置"""
    if os.path.exists('render.yaml'):
        try:
            with open('render.yaml', 'r') as file:
                content = file.read()
            
            if re.search(OLD_HOST_PATTERN, content):
                new_content = re.sub(OLD_HOST_PATTERN, NEW_HOST, content)
                
                with open('render.yaml', 'w') as file:
                    file.write(new_content)
                
                logger.info("已更新 render.yaml 中的数据库主机名")
            else:
                logger.info("render.yaml 不包含旧的数据库主机名")
        
        except Exception as e:
            logger.error(f"更新 render.yaml 时出错: {e}")
    else:
        logger.info("未找到 render.yaml 文件")

def main():
    """主函数"""
    logger.info("开始更新数据库配置...")
    
    # 查找配置文件
    config_files = find_config_files()
    
    # 更新配置文件
    update_config_files(config_files)
    
    # 检查render.yaml文件
    check_render_yaml()
    
    # 生成环境变量更新命令
    update_env_variables()
    
    logger.info("数据库配置更新完成!")
    
    # 提示用户下一步操作
    logger.info("\n===== 后续步骤 =====")
    logger.info("1. 执行 'source update_env.sh' 更新环境变量")
    logger.info("2. 重启应用程序")
    logger.info("3. 检查应用日志确认数据库连接是否正常")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 