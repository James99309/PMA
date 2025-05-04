#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render应用重启工具

在Render部署环境中，创建触发文件重启应用程序
"""

import os
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render重启')

def restart_render_app():
    """重启Render应用"""
    logger.info("===== 开始重启Render应用 =====")
    
    # 应用根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Render重启触发目录
    tmp_dir = os.path.join(base_dir, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        logger.info(f"创建临时目录: {tmp_dir}")
    
    # 创建重启触发文件
    restart_file = os.path.join(tmp_dir, 'restart.txt')
    with open(restart_file, 'w') as f:
        f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info(f"创建重启触发文件: {restart_file}")
    logger.info("Render将检测到此文件并重启应用")
    logger.info("===== 重启触发完成 =====")
    
    return True

if __name__ == "__main__":
    restart_render_app() 
# -*- coding: utf-8 -*-
"""
Render应用重启工具

在Render部署环境中，创建触发文件重启应用程序
"""

import os
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render重启')

def restart_render_app():
    """重启Render应用"""
    logger.info("===== 开始重启Render应用 =====")
    
    # 应用根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Render重启触发目录
    tmp_dir = os.path.join(base_dir, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        logger.info(f"创建临时目录: {tmp_dir}")
    
    # 创建重启触发文件
    restart_file = os.path.join(tmp_dir, 'restart.txt')
    with open(restart_file, 'w') as f:
        f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info(f"创建重启触发文件: {restart_file}")
    logger.info("Render将检测到此文件并重启应用")
    logger.info("===== 重启触发完成 =====")
    
    return True

if __name__ == "__main__":
    restart_render_app() 
 
 
# -*- coding: utf-8 -*-
"""
Render应用重启工具

在Render部署环境中，创建触发文件重启应用程序
"""

import os
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render重启')

def restart_render_app():
    """重启Render应用"""
    logger.info("===== 开始重启Render应用 =====")
    
    # 应用根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Render重启触发目录
    tmp_dir = os.path.join(base_dir, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        logger.info(f"创建临时目录: {tmp_dir}")
    
    # 创建重启触发文件
    restart_file = os.path.join(tmp_dir, 'restart.txt')
    with open(restart_file, 'w') as f:
        f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info(f"创建重启触发文件: {restart_file}")
    logger.info("Render将检测到此文件并重启应用")
    logger.info("===== 重启触发完成 =====")
    
    return True

if __name__ == "__main__":
    restart_render_app() 
# -*- coding: utf-8 -*-
"""
Render应用重启工具

在Render部署环境中，创建触发文件重启应用程序
"""

import os
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render重启')

def restart_render_app():
    """重启Render应用"""
    logger.info("===== 开始重启Render应用 =====")
    
    # 应用根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Render重启触发目录
    tmp_dir = os.path.join(base_dir, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        logger.info(f"创建临时目录: {tmp_dir}")
    
    # 创建重启触发文件
    restart_file = os.path.join(tmp_dir, 'restart.txt')
    with open(restart_file, 'w') as f:
        f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info(f"创建重启触发文件: {restart_file}")
    logger.info("Render将检测到此文件并重启应用")
    logger.info("===== 重启触发完成 =====")
    
    return True

if __name__ == "__main__":
    restart_render_app() 
 
 