#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('登录测试')

def test_login(url="http://localhost:8082"):
    """测试登录功能"""
    session = requests.Session()
    
    # 先访问登录页面获取CSRF令牌
    try:
        login_page = session.get(f"{url}/login")
        if login_page.status_code != 200:
            logger.error(f"获取登录页面失败: {login_page.status_code}")
            return False
            
        # 提取CSRF令牌
        csrf_token = None
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            logger.info(f"成功获取CSRF令牌: {csrf_token[:10]}...")
        else:
            logger.error("无法找到CSRF令牌")
            return False
        
        # 模拟登录
        login_data = {
            'username': 'admin',
            'password': '1505562299AaBb',
            'csrf_token': csrf_token
        }
        
        login_response = session.post(f"{url}/login", data=login_data, allow_redirects=True)
        
        # 检查是否登录成功(通常登录成功会重定向到首页)
        if login_response.url.endswith('/') or '/index' in login_response.url:
            logger.info(f"登录成功! 已重定向到: {login_response.url}")
            
            # 检查是否有欢迎消息或Admin权限指示
            if 'admin' in login_response.text.lower() and ('欢迎' in login_response.text or 'welcome' in login_response.text.lower()):
                logger.info("确认有admin内容在页面中")
                return True
            else:
                logger.warning("登录后未检测到admin内容，可能是部分成功")
                return True
        else:
            logger.error(f"登录失败，当前页面: {login_response.url}")
            
            # 检查是否有错误消息
            if '密码错误' in login_response.text or 'incorrect password' in login_response.text.lower():
                logger.error("错误消息: 密码错误")
            elif '用户不存在' in login_response.text or 'user not found' in login_response.text.lower():
                logger.error("错误消息: 用户不存在")
            elif '账户已禁用' in login_response.text or 'account is disabled' in login_response.text.lower():
                logger.error("错误消息: 账户已禁用")
            else:
                logger.error("未找到具体错误消息")
            return False
    
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        return False

if __name__ == "__main__":
    test_login() 
# -*- coding: utf-8 -*-

import requests
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('登录测试')

def test_login(url="http://localhost:8082"):
    """测试登录功能"""
    session = requests.Session()
    
    # 先访问登录页面获取CSRF令牌
    try:
        login_page = session.get(f"{url}/login")
        if login_page.status_code != 200:
            logger.error(f"获取登录页面失败: {login_page.status_code}")
            return False
            
        # 提取CSRF令牌
        csrf_token = None
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            logger.info(f"成功获取CSRF令牌: {csrf_token[:10]}...")
        else:
            logger.error("无法找到CSRF令牌")
            return False
        
        # 模拟登录
        login_data = {
            'username': 'admin',
            'password': '1505562299AaBb',
            'csrf_token': csrf_token
        }
        
        login_response = session.post(f"{url}/login", data=login_data, allow_redirects=True)
        
        # 检查是否登录成功(通常登录成功会重定向到首页)
        if login_response.url.endswith('/') or '/index' in login_response.url:
            logger.info(f"登录成功! 已重定向到: {login_response.url}")
            
            # 检查是否有欢迎消息或Admin权限指示
            if 'admin' in login_response.text.lower() and ('欢迎' in login_response.text or 'welcome' in login_response.text.lower()):
                logger.info("确认有admin内容在页面中")
                return True
            else:
                logger.warning("登录后未检测到admin内容，可能是部分成功")
                return True
        else:
            logger.error(f"登录失败，当前页面: {login_response.url}")
            
            # 检查是否有错误消息
            if '密码错误' in login_response.text or 'incorrect password' in login_response.text.lower():
                logger.error("错误消息: 密码错误")
            elif '用户不存在' in login_response.text or 'user not found' in login_response.text.lower():
                logger.error("错误消息: 用户不存在")
            elif '账户已禁用' in login_response.text or 'account is disabled' in login_response.text.lower():
                logger.error("错误消息: 账户已禁用")
            else:
                logger.error("未找到具体错误消息")
            return False
    
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        return False

if __name__ == "__main__":
    test_login() 