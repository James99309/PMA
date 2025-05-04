#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Render环境用户模块更新脚本

此脚本用于更新Render环境中的用户模块代码。
版本: 20250504084516
"""

import os
import logging
import json
import sys
import time
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_update.log')
    ]
)
logger = logging.getLogger(__name__)

# 要更新的文件列表
USER_MODULE_FILES = ['app/views/user.py', 'app/models/user.py', 'app/permissions.py', 'app/utils/permissions.py', 'app/templates/user/list.html', 'app/templates/user/edit.html', 'app/templates/user/permissions.html', 'app/templates/user/affiliations.html']

def backup_file(filepath):
    """备份文件"""
    if not os.path.exists(filepath):
        logger.warning(f"文件不存在，无法备份: {filepath}")
        return
        
    backup_path = f"{filepath}.bak.{int(time.time())}"
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"已备份文件: {backup_path}")
    except Exception as e:
        logger.error(f"备份文件失败: {str(e)}")

def ensure_directory(filepath):
    """确保目录存在"""
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"创建目录: {directory}")
        except Exception as e:
            logger.error(f"创建目录失败: {str(e)}")
            return False
    return True

def update_file(filepath, content):
    """更新文件内容"""
    try:
        # 备份原文件
        if os.path.exists(filepath):
            backup_file(filepath)
        
        # 确保目录存在
        if not ensure_directory(filepath):
            return False
        
        # 写入新内容
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"文件更新成功: {filepath}")
        return True
    except Exception as e:
        logger.error(f"更新文件失败: {filepath}, 错误: {str(e)}")
        return False

def update_render_files():
    """更新Render环境文件"""
    success_count = 0
    failed_files = []
    
    for filepath in USER_MODULE_FILES:
        logger.info(f"处理文件: {filepath}")
        
        try:
            # 检查文件是否存在于部署包中
            package_filepath = os.path.join("package", filepath)
            if not os.path.exists(package_filepath):
                logger.warning(f"部署包中不存在文件: {package_filepath}")
                failed_files.append(filepath)
                continue
            
            # 读取部署包中的文件内容
            with open(package_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新文件
            if update_file(filepath, content):
                success_count += 1
            else:
                failed_files.append(filepath)
        except Exception as e:
            logger.error(f"处理文件时出错: {filepath}, 错误: {str(e)}")
            failed_files.append(filepath)
    
    logger.info(f"文件更新完成。成功: {success_count}, 失败: {len(failed_files)}")
    if failed_files:
        logger.warning(f"更新失败的文件: {failed_files}")
    
    return success_count, failed_files

def main():
    """主函数"""
    logger.info("开始更新Render环境用户模块...")
    
    # 检查package目录是否存在
    if not os.path.exists("package"):
        logger.error("部署包目录不存在。请确保部署包已解压到'package'目录。")
        return 1
    
    # 更新文件
    success_count, failed_files = update_render_files()
    
    # 输出结果
    print(f"\n更新结果:")
    print(f"成功更新 {success_count} 个文件")
    if failed_files:
        print(f"更新失败 {len(failed_files)} 个文件: {', '.join(failed_files)}")
    
    return 0 if not failed_files else 1

if __name__ == "__main__":
    sys.exit(main())
