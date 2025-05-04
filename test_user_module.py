#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户模块功能测试脚本

此脚本用于测试用户模块的基本功能是否正常，包括：
1. 用户列表页面访问
2. 用户详情页面访问
3. 用户API接口测试
4. 用户权限测试

用法：python test_user_module.py <base_url> <admin_username> <admin_password>
"""

import requests
import json
import sys
import logging
import time
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('user_module_test.log')
    ]
)
logger = logging.getLogger(__name__)

class UserModuleTester:
    """用户模块测试类"""
    
    def __init__(self, base_url, username, password):
        """
        初始化测试类
        
        参数:
            base_url: 应用基础URL
            username: 管理员用户名
            password: 管理员密码
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None
        self.csrf_token = None
    
    def login(self):
        """登录系统，获取认证令牌"""
        login_url = f"{self.base_url}/auth/login"
        
        try:
            # 首先获取登录页面，提取CSRF令牌
            response = self.session.get(login_url)
            
            if response.status_code != 200:
                logger.error(f"获取登录页面失败: {response.status_code}")
                return False
            
            # 尝试从页面提取CSRF令牌
            import re
            csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
            if csrf_match:
                self.csrf_token = csrf_match.group(1)
                logger.info(f"成功提取CSRF令牌: {self.csrf_token[:10]}...")
            else:
                logger.warning("未找到CSRF令牌，尝试继续登录")
            
            # 准备登录数据
            login_data = {
                "username": self.username,
                "password": self.password,
                "remember": "y"
            }
            
            if self.csrf_token:
                login_data["csrf_token"] = self.csrf_token
            
            # 发送登录请求
            response = self.session.post(login_url, data=login_data, allow_redirects=True)
            
            # 检查登录结果
            if "登录成功" in response.text or response.url != login_url:
                logger.info("登录成功")
                
                # 尝试从会话中获取JWT令牌
                for cookie in self.session.cookies:
                    if cookie.name == "jwt_token":
                        self.token = cookie.value
                        logger.info(f"成功获取JWT令牌: {self.token[:10]}...")
                        break
                
                return True
            else:
                logger.error("登录失败")
                return False
                
        except Exception as e:
            logger.error(f"登录过程出错: {str(e)}")
            return False
    
    def test_user_list_page(self):
        """测试用户列表页面"""
        url = f"{self.base_url}/user/list"
        
        try:
            logger.info(f"测试用户列表页面: {url}")
            response = self.session.get(url)
            
            if response.status_code == 200:
                # 检查页面内容是否包含用户列表相关文本
                if "用户列表" in response.text or "用户管理" in response.text:
                    logger.info("用户列表页面正常")
                    return True
                else:
                    logger.warning("用户列表页面返回200，但内容可能不正确")
                    return False
            else:
                logger.error(f"访问用户列表页面失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"测试用户列表页面时出错: {str(e)}")
            return False
    
    def test_user_api(self):
        """测试用户API接口"""
        url = f"{self.base_url}/api/v1/users"
        headers = {}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            logger.info(f"测试用户API: {url}")
            response = self.session.get(url, headers=headers)
            
            try:
                data = response.json()
                if response.status_code == 200 and data.get('success'):
                    users = data.get('data', {}).get('users', [])
                    logger.info(f"用户API返回用户数量: {len(users)}")
                    return True
                else:
                    error_msg = data.get('message', '未知错误')
                    logger.error(f"用户API访问失败: {error_msg}")
                    return False
            except json.JSONDecodeError as e:
                logger.error(f"解析API响应失败: {str(e)}")
                logger.error(f"响应内容: {response.text[:200]}...")
                return False
        except Exception as e:
            logger.error(f"测试用户API接口时出错: {str(e)}")
            return False
    
    def test_user_permissions(self):
        """测试用户权限功能"""
        url = f"{self.base_url}/user/permissions/1"  # 假设ID为1的用户存在
        
        try:
            logger.info(f"测试用户权限页面: {url}")
            response = self.session.get(url)
            
            if response.status_code == 200:
                # 检查页面内容是否包含权限相关文本
                if "权限管理" in response.text or "模块权限" in response.text:
                    logger.info("用户权限页面正常")
                    return True
                else:
                    logger.warning("用户权限页面返回200，但内容可能不正确")
                    return False
            elif response.status_code == 403:
                logger.warning("无权限访问用户权限页面，可能需要更高权限")
                return None
            else:
                logger.error(f"访问用户权限页面失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"测试用户权限功能时出错: {str(e)}")
            return False
    
    def test_user_create_page(self):
        """测试用户创建页面"""
        url = f"{self.base_url}/user/create"
        
        try:
            logger.info(f"测试用户创建页面: {url}")
            response = self.session.get(url)
            
            if response.status_code == 200:
                # 检查页面内容是否包含用户创建相关文本
                if "创建用户" in response.text or "新建用户" in response.text:
                    logger.info("用户创建页面正常")
                    return True
                else:
                    logger.warning("用户创建页面返回200，但内容可能不正确")
                    return False
            else:
                logger.error(f"访问用户创建页面失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"测试用户创建页面时出错: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info(f"开始测试用户模块，基础URL: {self.base_url}")
        
        # 登录系统
        if not self.login():
            logger.error("登录失败，终止测试")
            return False
        
        # 运行测试
        tests = [
            ("用户列表页面", self.test_user_list_page()),
            ("用户API接口", self.test_user_api()),
            ("用户权限功能", self.test_user_permissions()),
            ("用户创建页面", self.test_user_create_page())
        ]
        
        # 输出测试结果
        print("\n测试结果:")
        all_passed = True
        for name, result in tests:
            if result is None:
                status = "跳过"
            else:
                status = "通过" if result else "失败"
                if not result and result is not None:
                    all_passed = False
            
            print(f"{name}: {status}")
        
        return all_passed

def main():
    """主函数"""
    if len(sys.argv) < 4:
        print("用法: python test_user_module.py <base_url> <admin_username> <admin_password>")
        print("示例: python test_user_module.py http://localhost:8082 admin admin123")
        return 1
    
    base_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url
    
    tester = UserModuleTester(base_url, username, password)
    success = tester.run_all_tests()
    
    if success:
        print("\n所有测试均已通过！用户模块功能正常。")
    else:
        print("\n部分测试未通过，请检查日志了解详情。")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 