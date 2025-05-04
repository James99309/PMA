#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
import json
import logging
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger('登录测试')

def direct_login_test(username="admin", password="1505562299AaBb", url="http://localhost:8082"):
    """直接测试登录API"""
    
    session = requests.Session()
    
    # 获取CSRF令牌
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
            logger.warning("未找到CSRF令牌，尝试直接登录")
    
        # 构建登录数据
        login_data = {
            "username": username,
            "password": password,
            "remember": "y"
        }
        
        if csrf_token:
            login_data["csrf_token"] = csrf_token
        
        # 提交登录请求
        login_response = session.post(
            f"{url}/login", 
            data=login_data,
            allow_redirects=True
        )
        
        # 检查登录响应
        logger.info(f"登录响应状态码: {login_response.status_code}")
        logger.info(f"登录后重定向URL: {login_response.url}")
        
        # 如果重定向到首页，表示登录成功
        if login_response.url.endswith("/"):
            logger.info("登录成功，已重定向到首页")
            return True
        
        # 检查是否有错误消息
        error_match = re.search(r'alert-danger">\s*([^<]+)<', login_response.text)
        if error_match:
            error_msg = error_match.group(1).strip()
            logger.error(f"登录失败，错误消息: {error_msg}")
        
        # 尝试API登录作为后备方案
        try:
            api_login_response = session.post(
                f"{url}/api/auth/login",
                json={"username": username, "password": password}
            )
            
            if api_login_response.status_code == 200:
                api_data = api_login_response.json()
                logger.info(f"API登录响应: {json.dumps(api_data, indent=2)}")
                if api_data.get("success"):
                    logger.info("API登录成功")
                    return True
            else:
                logger.error(f"API登录失败: {api_login_response.status_code}")
        except Exception as e:
            logger.error(f"API登录尝试失败: {e}")
        
        return False
    
    except Exception as e:
        logger.error(f"登录测试出错: {e}")
        return False

if __name__ == "__main__":
    # 从命令行获取参数，默认为admin/1505562299AaBb
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "1505562299AaBb"
    
    logger.info(f"测试登录用户: {username}")
    result = direct_login_test(username, password)
    
    if result:
        logger.info("✅ 登录测试成功")
        sys.exit(0)
    else:
        logger.error("❌ 登录测试失败")
        sys.exit(1) 
# -*- coding: utf-8 -*-

import requests
import re
import json
import logging
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger('登录测试')

def direct_login_test(username="admin", password="1505562299AaBb", url="http://localhost:8082"):
    """直接测试登录API"""
    
    session = requests.Session()
    
    # 获取CSRF令牌
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
            logger.warning("未找到CSRF令牌，尝试直接登录")
    
        # 构建登录数据
        login_data = {
            "username": username,
            "password": password,
            "remember": "y"
        }
        
        if csrf_token:
            login_data["csrf_token"] = csrf_token
        
        # 提交登录请求
        login_response = session.post(
            f"{url}/login", 
            data=login_data,
            allow_redirects=True
        )
        
        # 检查登录响应
        logger.info(f"登录响应状态码: {login_response.status_code}")
        logger.info(f"登录后重定向URL: {login_response.url}")
        
        # 如果重定向到首页，表示登录成功
        if login_response.url.endswith("/"):
            logger.info("登录成功，已重定向到首页")
            return True
        
        # 检查是否有错误消息
        error_match = re.search(r'alert-danger">\s*([^<]+)<', login_response.text)
        if error_match:
            error_msg = error_match.group(1).strip()
            logger.error(f"登录失败，错误消息: {error_msg}")
        
        # 尝试API登录作为后备方案
        try:
            api_login_response = session.post(
                f"{url}/api/auth/login",
                json={"username": username, "password": password}
            )
            
            if api_login_response.status_code == 200:
                api_data = api_login_response.json()
                logger.info(f"API登录响应: {json.dumps(api_data, indent=2)}")
                if api_data.get("success"):
                    logger.info("API登录成功")
                    return True
            else:
                logger.error(f"API登录失败: {api_login_response.status_code}")
        except Exception as e:
            logger.error(f"API登录尝试失败: {e}")
        
        return False
    
    except Exception as e:
        logger.error(f"登录测试出错: {e}")
        return False

if __name__ == "__main__":
    # 从命令行获取参数，默认为admin/1505562299AaBb
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "1505562299AaBb"
    
    logger.info(f"测试登录用户: {username}")
    result = direct_login_test(username, password)
    
    if result:
        logger.info("✅ 登录测试成功")
        sys.exit(0)
    else:
        logger.error("❌ 登录测试失败")
        sys.exit(1) 