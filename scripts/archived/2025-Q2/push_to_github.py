#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMA应用修复和GitHub推送脚本

用途:
1. 执行所有修复脚本
2. 提交修改到Git仓库
3. 推送到GitHub
"""

import os
import sys
import subprocess
import logging
import datetime

# 导入修复脚本
import fix_all_issues

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('github_push.log')
    ]
)
logger = logging.getLogger('GitHub推送')

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
        logger.info(f"命令执行成功: {result.stdout.strip()}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e.stderr.strip()}")
        return False, e.stderr
    except Exception as e:
        logger.error(f"运行命令时出错: {str(e)}")
        return False, str(e)

def check_git_repository():
    """检查当前目录是否是Git仓库"""
    return run_command("git rev-parse --is-inside-work-tree")

def check_git_status():
    """检查Git仓库状态"""
    return run_command("git status")

def add_changes():
    """将所有修改添加到暂存区"""
    return run_command("git add .")

def commit_changes(message="修复Flask应用中的CSRF和权限导入问题以及模板语法错误"):
    """提交修改到本地仓库"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"{message} ({timestamp})"
    return run_command(f'git commit -m "{full_message}"')

def push_to_github(branch="main"):
    """推送修改到GitHub仓库"""
    return run_command(f"git push origin {branch}")

def check_branch():
    """获取当前分支名称"""
    status, output = run_command("git branch --show-current")
    if status:
        branch = output.strip()
        logger.info(f"当前分支: {branch}")
        return branch
    else:
        logger.error("获取分支名称失败")
        return "main"  # 默认分支

def main():
    """主函数，执行修复和推送流程"""
    logger.info("开始执行PMA应用修复和GitHub推送...")
    
    # 检查是否在Git仓库中
    status, _ = check_git_repository()
    if not status:
        logger.error("当前目录不是Git仓库，无法推送到GitHub")
        return False
    
    # 获取当前分支
    branch = check_branch()
    
    # 执行修复脚本
    logger.info("开始执行修复脚本...")
    fix_all_issues.main()
    logger.info("修复脚本执行完成")
    
    # 检查Git状态
    logger.info("检查Git状态...")
    check_git_status()
    
    # 将修改添加到暂存区
    logger.info("添加修改到暂存区...")
    status, _ = add_changes()
    if not status:
        logger.error("添加修改到暂存区失败")
        return False
    
    # 提交修改
    logger.info("提交修改到本地仓库...")
    status, _ = commit_changes()
    if not status:
        logger.error("提交修改失败")
        return False
    
    # 推送到GitHub
    logger.info(f"推送修改到GitHub ({branch})...")
    status, _ = push_to_github(branch)
    if not status:
        logger.error("推送到GitHub失败")
        return False
    
    logger.info("PMA应用修复和GitHub推送完成")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
# -*- coding: utf-8 -*-
"""
PMA应用修复和GitHub推送脚本

用途:
1. 执行所有修复脚本
2. 提交修改到Git仓库
3. 推送到GitHub
"""

import os
import sys
import subprocess
import logging
import datetime

# 导入修复脚本
import fix_all_issues

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('github_push.log')
    ]
)
logger = logging.getLogger('GitHub推送')

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
        logger.info(f"命令执行成功: {result.stdout.strip()}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e.stderr.strip()}")
        return False, e.stderr
    except Exception as e:
        logger.error(f"运行命令时出错: {str(e)}")
        return False, str(e)

def check_git_repository():
    """检查当前目录是否是Git仓库"""
    return run_command("git rev-parse --is-inside-work-tree")

def check_git_status():
    """检查Git仓库状态"""
    return run_command("git status")

def add_changes():
    """将所有修改添加到暂存区"""
    return run_command("git add .")

def commit_changes(message="修复Flask应用中的CSRF和权限导入问题以及模板语法错误"):
    """提交修改到本地仓库"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"{message} ({timestamp})"
    return run_command(f'git commit -m "{full_message}"')

def push_to_github(branch="main"):
    """推送修改到GitHub仓库"""
    return run_command(f"git push origin {branch}")

def check_branch():
    """获取当前分支名称"""
    status, output = run_command("git branch --show-current")
    if status:
        branch = output.strip()
        logger.info(f"当前分支: {branch}")
        return branch
    else:
        logger.error("获取分支名称失败")
        return "main"  # 默认分支

def main():
    """主函数，执行修复和推送流程"""
    logger.info("开始执行PMA应用修复和GitHub推送...")
    
    # 检查是否在Git仓库中
    status, _ = check_git_repository()
    if not status:
        logger.error("当前目录不是Git仓库，无法推送到GitHub")
        return False
    
    # 获取当前分支
    branch = check_branch()
    
    # 执行修复脚本
    logger.info("开始执行修复脚本...")
    fix_all_issues.main()
    logger.info("修复脚本执行完成")
    
    # 检查Git状态
    logger.info("检查Git状态...")
    check_git_status()
    
    # 将修改添加到暂存区
    logger.info("添加修改到暂存区...")
    status, _ = add_changes()
    if not status:
        logger.error("添加修改到暂存区失败")
        return False
    
    # 提交修改
    logger.info("提交修改到本地仓库...")
    status, _ = commit_changes()
    if not status:
        logger.error("提交修改失败")
        return False
    
    # 推送到GitHub
    logger.info(f"推送修改到GitHub ({branch})...")
    status, _ = push_to_github(branch)
    if not status:
        logger.error("推送到GitHub失败")
        return False
    
    logger.info("PMA应用修复和GitHub推送完成")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 