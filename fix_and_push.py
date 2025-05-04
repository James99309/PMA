#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库问题并推送到GitHub的脚本

用法:
python fix_and_push.py
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_and_push.log')
    ]
)
logger = logging.getLogger('修复和推送')

def run_command(command, cwd=None):
    """执行shell命令并返回结果"""
    try:
        logger.info(f"执行命令: {command}")
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            encoding='utf-8'
        )
        logger.info(f"命令执行成功: {result.stdout}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e.stderr}")
        return False, e.stderr

def fix_database_issues():
    """执行数据库修复脚本"""
    logger.info("开始执行数据库修复脚本...")
    
    # 执行修复脚本
    success, output = run_command("python fix_company_region_column.py")
    if not success:
        logger.error("数据库修复失败")
        return False
    
    # 执行数据库迁移
    success, output = run_command("flask db upgrade")
    if not success:
        logger.error("数据库迁移失败")
        return False
    
    logger.info("数据库修复完成")
    return True

def commit_changes():
    """提交修改到Git仓库"""
    logger.info("提交修改到Git仓库...")
    
    # 添加修改的文件
    files_to_add = [
        "migrations/versions/add_missing_region_column.py",
        "fix_company_region_column.py",
        "fix_render_schema.py"
    ]
    
    for file in files_to_add:
        success, output = run_command(f"git add {file}")
        if not success:
            logger.error(f"无法添加文件 {file} 到Git索引")
            return False
    
    # 提交修改
    commit_message = f"修复companies表缺少region列的问题 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    success, output = run_command(f'git commit -m "{commit_message}"')
    if not success:
        logger.error("提交修改失败")
        return False
    
    logger.info("修改已提交到本地Git仓库")
    return True

def push_to_github():
    """推送修改到GitHub"""
    logger.info("推送修改到GitHub...")
    
    # 推送到远程仓库
    success, output = run_command("git push origin main")
    if not success:
        logger.error("推送到GitHub失败")
        return False
    
    logger.info("修改已成功推送到GitHub")
    return True

def main():
    """主函数，执行修复和推送流程"""
    logger.info("开始执行修复和推送流程...")
    
    # 1. 修复数据库问题
    if not fix_database_issues():
        logger.error("修复数据库问题失败，终止推送")
        return False
    
    # 2. 提交修改
    if not commit_changes():
        logger.error("提交修改失败，终止推送")
        return False
    
    # 3. 推送到GitHub
    if not push_to_github():
        logger.error("推送到GitHub失败")
        return False
    
    logger.info("修复和推送流程成功完成")
    return True

if __name__ == "__main__":
    try:
        if main():
            logger.info("脚本执行成功")
            sys.exit(0)
        else:
            logger.error("脚本执行失败")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"脚本执行时发生未处理的异常: {str(e)}")
        sys.exit(1) 
# -*- coding: utf-8 -*-
"""
修复数据库问题并推送到GitHub的脚本

用法:
python fix_and_push.py
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_and_push.log')
    ]
)
logger = logging.getLogger('修复和推送')

def run_command(command, cwd=None):
    """执行shell命令并返回结果"""
    try:
        logger.info(f"执行命令: {command}")
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            encoding='utf-8'
        )
        logger.info(f"命令执行成功: {result.stdout}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e.stderr}")
        return False, e.stderr

def fix_database_issues():
    """执行数据库修复脚本"""
    logger.info("开始执行数据库修复脚本...")
    
    # 执行修复脚本
    success, output = run_command("python fix_company_region_column.py")
    if not success:
        logger.error("数据库修复失败")
        return False
    
    # 执行数据库迁移
    success, output = run_command("flask db upgrade")
    if not success:
        logger.error("数据库迁移失败")
        return False
    
    logger.info("数据库修复完成")
    return True

def commit_changes():
    """提交修改到Git仓库"""
    logger.info("提交修改到Git仓库...")
    
    # 添加修改的文件
    files_to_add = [
        "migrations/versions/add_missing_region_column.py",
        "fix_company_region_column.py",
        "fix_render_schema.py"
    ]
    
    for file in files_to_add:
        success, output = run_command(f"git add {file}")
        if not success:
            logger.error(f"无法添加文件 {file} 到Git索引")
            return False
    
    # 提交修改
    commit_message = f"修复companies表缺少region列的问题 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    success, output = run_command(f'git commit -m "{commit_message}"')
    if not success:
        logger.error("提交修改失败")
        return False
    
    logger.info("修改已提交到本地Git仓库")
    return True

def push_to_github():
    """推送修改到GitHub"""
    logger.info("推送修改到GitHub...")
    
    # 推送到远程仓库
    success, output = run_command("git push origin main")
    if not success:
        logger.error("推送到GitHub失败")
        return False
    
    logger.info("修改已成功推送到GitHub")
    return True

def main():
    """主函数，执行修复和推送流程"""
    logger.info("开始执行修复和推送流程...")
    
    # 1. 修复数据库问题
    if not fix_database_issues():
        logger.error("修复数据库问题失败，终止推送")
        return False
    
    # 2. 提交修改
    if not commit_changes():
        logger.error("提交修改失败，终止推送")
        return False
    
    # 3. 推送到GitHub
    if not push_to_github():
        logger.error("推送到GitHub失败")
        return False
    
    logger.info("修复和推送流程成功完成")
    return True

if __name__ == "__main__":
    try:
        if main():
            logger.info("脚本执行成功")
            sys.exit(0)
        else:
            logger.error("脚本执行失败")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"脚本执行时发生未处理的异常: {str(e)}")
        sys.exit(1) 