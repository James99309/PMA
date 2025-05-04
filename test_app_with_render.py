#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序启动测试脚本
使用Render PostgreSQL数据库测试应用
"""

import os
import sys
import logging
import time
import threading
import argparse
from urllib.request import urlopen
from urllib.error import URLError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app_test.log')
    ]
)
logger = logging.getLogger('应用测试')

# 测试配置
TEST_HOST = '127.0.0.1'
TEST_PORT = 8082
TEST_URL = f'http://{TEST_HOST}:{TEST_PORT}/'
STARTUP_TIMEOUT = 30  # 等待应用启动的超时时间（秒）

def is_url_reachable(url):
    """测试URL是否可以访问"""
    try:
        response = urlopen(url, timeout=5)
        return response.getcode() == 200
    except URLError:
        return False

def run_app():
    """使用Render数据库配置运行应用程序"""
    logger.info("启动应用程序...")
    
    # 从环境变量获取数据库URL
    db_url = os.environ.get('RENDER_DB_URL')
    if not db_url:
        logger.error("未设置RENDER_DB_URL环境变量！")
        sys.exit(1)
    
    logger.info(f"正在使用数据库URL: {db_url[:20]}...{db_url[-20:]}")
    
    # 运行应用
    import app
    application = app.create_app()
    application.run(host=TEST_HOST, port=TEST_PORT, debug=False)

def test_app_startup():
    """测试应用程序是否能够启动"""
    logger.info("开始测试应用程序启动...")
    
    # 启动应用程序线程
    app_thread = threading.Thread(target=run_app)
    app_thread.daemon = True  # 设置为守护线程，使其随主线程结束而结束
    app_thread.start()
    
    # 等待应用程序启动
    logger.info(f"等待应用程序启动（最多{STARTUP_TIMEOUT}秒）...")
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        if is_url_reachable(TEST_URL):
            logger.info("应用程序已成功启动！")
            logger.info(f"可以通过 {TEST_URL} 访问应用")
            
            # 测试用户管理模块
            user_url = f"{TEST_URL}user/list"
            if is_url_reachable(user_url):
                logger.info("用户管理模块测试成功！")
            else:
                logger.warning("无法访问用户管理模块，可能需要先登录")
            
            return True
        
        logger.info("应用程序还未启动，继续等待...")
        time.sleep(2)
    
    logger.error(f"应用程序启动超时（{STARTUP_TIMEOUT}秒）")
    return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试应用程序使用Render数据库启动")
    parser.add_argument("--run", action="store_true", help="直接运行应用，而不是在单独线程中测试")
    args = parser.parse_args()
    
    if args.run:
        # 直接运行应用
        run_app()
    else:
        # 测试应用启动
        success = test_app_startup()
        if success:
            logger.info("测试成功完成，按Ctrl+C终止")
            try:
                # 保持脚本运行，直到用户按Ctrl+C
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("测试已手动终止")
        else:
            logger.error("测试失败")
            sys.exit(1)

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
应用程序启动测试脚本
使用Render PostgreSQL数据库测试应用
"""

import os
import sys
import logging
import time
import threading
import argparse
from urllib.request import urlopen
from urllib.error import URLError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app_test.log')
    ]
)
logger = logging.getLogger('应用测试')

# 测试配置
TEST_HOST = '127.0.0.1'
TEST_PORT = 8082
TEST_URL = f'http://{TEST_HOST}:{TEST_PORT}/'
STARTUP_TIMEOUT = 30  # 等待应用启动的超时时间（秒）

def is_url_reachable(url):
    """测试URL是否可以访问"""
    try:
        response = urlopen(url, timeout=5)
        return response.getcode() == 200
    except URLError:
        return False

def run_app():
    """使用Render数据库配置运行应用程序"""
    logger.info("启动应用程序...")
    
    # 从环境变量获取数据库URL
    db_url = os.environ.get('RENDER_DB_URL')
    if not db_url:
        logger.error("未设置RENDER_DB_URL环境变量！")
        sys.exit(1)
    
    logger.info(f"正在使用数据库URL: {db_url[:20]}...{db_url[-20:]}")
    
    # 运行应用
    import app
    application = app.create_app()
    application.run(host=TEST_HOST, port=TEST_PORT, debug=False)

def test_app_startup():
    """测试应用程序是否能够启动"""
    logger.info("开始测试应用程序启动...")
    
    # 启动应用程序线程
    app_thread = threading.Thread(target=run_app)
    app_thread.daemon = True  # 设置为守护线程，使其随主线程结束而结束
    app_thread.start()
    
    # 等待应用程序启动
    logger.info(f"等待应用程序启动（最多{STARTUP_TIMEOUT}秒）...")
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        if is_url_reachable(TEST_URL):
            logger.info("应用程序已成功启动！")
            logger.info(f"可以通过 {TEST_URL} 访问应用")
            
            # 测试用户管理模块
            user_url = f"{TEST_URL}user/list"
            if is_url_reachable(user_url):
                logger.info("用户管理模块测试成功！")
            else:
                logger.warning("无法访问用户管理模块，可能需要先登录")
            
            return True
        
        logger.info("应用程序还未启动，继续等待...")
        time.sleep(2)
    
    logger.error(f"应用程序启动超时（{STARTUP_TIMEOUT}秒）")
    return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试应用程序使用Render数据库启动")
    parser.add_argument("--run", action="store_true", help="直接运行应用，而不是在单独线程中测试")
    args = parser.parse_args()
    
    if args.run:
        # 直接运行应用
        run_app()
    else:
        # 测试应用启动
        success = test_app_startup()
        if success:
            logger.info("测试成功完成，按Ctrl+C终止")
            try:
                # 保持脚本运行，直到用户按Ctrl+C
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("测试已手动终止")
        else:
            logger.error("测试失败")
            sys.exit(1)

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
应用程序启动测试脚本
使用Render PostgreSQL数据库测试应用
"""

import os
import sys
import logging
import time
import threading
import argparse
from urllib.request import urlopen
from urllib.error import URLError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app_test.log')
    ]
)
logger = logging.getLogger('应用测试')

# 测试配置
TEST_HOST = '127.0.0.1'
TEST_PORT = 8082
TEST_URL = f'http://{TEST_HOST}:{TEST_PORT}/'
STARTUP_TIMEOUT = 30  # 等待应用启动的超时时间（秒）

def is_url_reachable(url):
    """测试URL是否可以访问"""
    try:
        response = urlopen(url, timeout=5)
        return response.getcode() == 200
    except URLError:
        return False

def run_app():
    """使用Render数据库配置运行应用程序"""
    logger.info("启动应用程序...")
    
    # 从环境变量获取数据库URL
    db_url = os.environ.get('RENDER_DB_URL')
    if not db_url:
        logger.error("未设置RENDER_DB_URL环境变量！")
        sys.exit(1)
    
    logger.info(f"正在使用数据库URL: {db_url[:20]}...{db_url[-20:]}")
    
    # 运行应用
    import app
    application = app.create_app()
    application.run(host=TEST_HOST, port=TEST_PORT, debug=False)

def test_app_startup():
    """测试应用程序是否能够启动"""
    logger.info("开始测试应用程序启动...")
    
    # 启动应用程序线程
    app_thread = threading.Thread(target=run_app)
    app_thread.daemon = True  # 设置为守护线程，使其随主线程结束而结束
    app_thread.start()
    
    # 等待应用程序启动
    logger.info(f"等待应用程序启动（最多{STARTUP_TIMEOUT}秒）...")
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        if is_url_reachable(TEST_URL):
            logger.info("应用程序已成功启动！")
            logger.info(f"可以通过 {TEST_URL} 访问应用")
            
            # 测试用户管理模块
            user_url = f"{TEST_URL}user/list"
            if is_url_reachable(user_url):
                logger.info("用户管理模块测试成功！")
            else:
                logger.warning("无法访问用户管理模块，可能需要先登录")
            
            return True
        
        logger.info("应用程序还未启动，继续等待...")
        time.sleep(2)
    
    logger.error(f"应用程序启动超时（{STARTUP_TIMEOUT}秒）")
    return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试应用程序使用Render数据库启动")
    parser.add_argument("--run", action="store_true", help="直接运行应用，而不是在单独线程中测试")
    args = parser.parse_args()
    
    if args.run:
        # 直接运行应用
        run_app()
    else:
        # 测试应用启动
        success = test_app_startup()
        if success:
            logger.info("测试成功完成，按Ctrl+C终止")
            try:
                # 保持脚本运行，直到用户按Ctrl+C
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("测试已手动终止")
        else:
            logger.error("测试失败")
            sys.exit(1)

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
应用程序启动测试脚本
使用Render PostgreSQL数据库测试应用
"""

import os
import sys
import logging
import time
import threading
import argparse
from urllib.request import urlopen
from urllib.error import URLError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app_test.log')
    ]
)
logger = logging.getLogger('应用测试')

# 测试配置
TEST_HOST = '127.0.0.1'
TEST_PORT = 8082
TEST_URL = f'http://{TEST_HOST}:{TEST_PORT}/'
STARTUP_TIMEOUT = 30  # 等待应用启动的超时时间（秒）

def is_url_reachable(url):
    """测试URL是否可以访问"""
    try:
        response = urlopen(url, timeout=5)
        return response.getcode() == 200
    except URLError:
        return False

def run_app():
    """使用Render数据库配置运行应用程序"""
    logger.info("启动应用程序...")
    
    # 从环境变量获取数据库URL
    db_url = os.environ.get('RENDER_DB_URL')
    if not db_url:
        logger.error("未设置RENDER_DB_URL环境变量！")
        sys.exit(1)
    
    logger.info(f"正在使用数据库URL: {db_url[:20]}...{db_url[-20:]}")
    
    # 运行应用
    import app
    application = app.create_app()
    application.run(host=TEST_HOST, port=TEST_PORT, debug=False)

def test_app_startup():
    """测试应用程序是否能够启动"""
    logger.info("开始测试应用程序启动...")
    
    # 启动应用程序线程
    app_thread = threading.Thread(target=run_app)
    app_thread.daemon = True  # 设置为守护线程，使其随主线程结束而结束
    app_thread.start()
    
    # 等待应用程序启动
    logger.info(f"等待应用程序启动（最多{STARTUP_TIMEOUT}秒）...")
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        if is_url_reachable(TEST_URL):
            logger.info("应用程序已成功启动！")
            logger.info(f"可以通过 {TEST_URL} 访问应用")
            
            # 测试用户管理模块
            user_url = f"{TEST_URL}user/list"
            if is_url_reachable(user_url):
                logger.info("用户管理模块测试成功！")
            else:
                logger.warning("无法访问用户管理模块，可能需要先登录")
            
            return True
        
        logger.info("应用程序还未启动，继续等待...")
        time.sleep(2)
    
    logger.error(f"应用程序启动超时（{STARTUP_TIMEOUT}秒）")
    return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试应用程序使用Render数据库启动")
    parser.add_argument("--run", action="store_true", help="直接运行应用，而不是在单独线程中测试")
    args = parser.parse_args()
    
    if args.run:
        # 直接运行应用
        run_app()
    else:
        # 测试应用启动
        success = test_app_startup()
        if success:
            logger.info("测试成功完成，按Ctrl+C终止")
            try:
                # 保持脚本运行，直到用户按Ctrl+C
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("测试已手动终止")
        else:
            logger.error("测试失败")
            sys.exit(1)

if __name__ == "__main__":
    main() 
 
 