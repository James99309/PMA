#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMA应用配置文件 - Render PostgreSQL版本
适用于连接Render云平台上的PostgreSQL数据库
"""

import os
import sys
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

class Config:
    """应用配置基类"""
    # 应用基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 修复Render的数据库URL
    @staticmethod
    def fix_render_db_url(db_url):
        """修复Render PostgreSQL数据库URL的SSL和格式问题"""
        if not db_url or 'render.com' not in db_url:
            return db_url
            
        # 1. 将postgres://替换为postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
        # 2. 解析URL以添加SSL参数
        parsed = urlparse(db_url)
        
        # 3. 确保主机名包含完整的Render域名
        hostname = parsed.hostname
        if hostname and not hostname.endswith('.render.com'):
            # 自动添加缺失的域名后缀
            if '.oregon-postgres' not in hostname:
                hostname = f"{hostname}.oregon-postgres.render.com"
                # 重建netloc部分(用户名:密码@主机名:端口)
                netloc_parts = []
                if parsed.username:
                    auth = parsed.username
                    if parsed.password:
                        auth += f":{parsed.password}"
                    netloc_parts.append(auth)
                netloc_parts.append(hostname)
                if parsed.port:
                    netloc_parts.append(str(parsed.port))
                
                netloc = '@'.join([netloc_parts[0], netloc_parts[1]]) if len(netloc_parts) > 1 else netloc_parts[0]
                if len(netloc_parts) > 2:
                    netloc += f":{netloc_parts[2]}"
                
                # 重建URL
                parsed = parsed._replace(netloc=netloc)
        
        # 4. 添加SSL参数
        query_dict = parse_qs(parsed.query)
        query_dict['sslmode'] = ['require']
        
        # 5. 重新组合URL
        parsed = parsed._replace(query=urlencode(query_dict, doseq=True))
        fixed_url = urlunparse(parsed)
        
        return fixed_url
    
    # 应用启动时自动修复数据库URL
    SQLALCHEMY_DATABASE_URI = fix_render_db_url.__func__(SQLALCHEMY_DATABASE_URI)
    
    # 其他应用配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() in ['true', '1', 't']
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@example.com']
    
    # 分页配置
    POSTS_PER_PAGE = 10

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # 在生产环境中强制使用环境变量中的秘钥
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Render特有配置 - 自动从环境变量获取配置
    @classmethod
    def init_app(cls, app):
        """生产环境特定初始化"""
        # 设置日志输出到标准输出，方便Render查看日志
        if cls.LOG_TO_STDOUT:
            import logging
            from logging import StreamHandler
            file_handler = StreamHandler(sys.stdout)
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

# 配置字典，用于动态选择配置
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 获取当前环境的配置
def get_config():
    """根据环境变量获取当前配置"""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])

# 测试配置生效
if __name__ == "__main__":
    # 测试数据库URL修复函数
    test_urls = [
        "postgres://user:pass@host/dbname",
        "postgres://user:pass@host.oregon-postgres.render.com/dbname",
        "postgresql://user:pass@host/dbname",
        "postgresql://user:pass@host/dbname?ssl=true"
    ]
    
    for url in test_urls:
        fixed = Config.fix_render_db_url(url)
        print(f"原始URL: {url}")
        print(f"修复后: {fixed}")
        print("-"*50) 
# -*- coding: utf-8 -*-
"""
PMA应用配置文件 - Render PostgreSQL版本
适用于连接Render云平台上的PostgreSQL数据库
"""

import os
import sys
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

class Config:
    """应用配置基类"""
    # 应用基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 修复Render的数据库URL
    @staticmethod
    def fix_render_db_url(db_url):
        """修复Render PostgreSQL数据库URL的SSL和格式问题"""
        if not db_url or 'render.com' not in db_url:
            return db_url
            
        # 1. 将postgres://替换为postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
        # 2. 解析URL以添加SSL参数
        parsed = urlparse(db_url)
        
        # 3. 确保主机名包含完整的Render域名
        hostname = parsed.hostname
        if hostname and not hostname.endswith('.render.com'):
            # 自动添加缺失的域名后缀
            if '.oregon-postgres' not in hostname:
                hostname = f"{hostname}.oregon-postgres.render.com"
                # 重建netloc部分(用户名:密码@主机名:端口)
                netloc_parts = []
                if parsed.username:
                    auth = parsed.username
                    if parsed.password:
                        auth += f":{parsed.password}"
                    netloc_parts.append(auth)
                netloc_parts.append(hostname)
                if parsed.port:
                    netloc_parts.append(str(parsed.port))
                
                netloc = '@'.join([netloc_parts[0], netloc_parts[1]]) if len(netloc_parts) > 1 else netloc_parts[0]
                if len(netloc_parts) > 2:
                    netloc += f":{netloc_parts[2]}"
                
                # 重建URL
                parsed = parsed._replace(netloc=netloc)
        
        # 4. 添加SSL参数
        query_dict = parse_qs(parsed.query)
        query_dict['sslmode'] = ['require']
        
        # 5. 重新组合URL
        parsed = parsed._replace(query=urlencode(query_dict, doseq=True))
        fixed_url = urlunparse(parsed)
        
        return fixed_url
    
    # 应用启动时自动修复数据库URL
    SQLALCHEMY_DATABASE_URI = fix_render_db_url.__func__(SQLALCHEMY_DATABASE_URI)
    
    # 其他应用配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() in ['true', '1', 't']
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@example.com']
    
    # 分页配置
    POSTS_PER_PAGE = 10

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # 在生产环境中强制使用环境变量中的秘钥
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Render特有配置 - 自动从环境变量获取配置
    @classmethod
    def init_app(cls, app):
        """生产环境特定初始化"""
        # 设置日志输出到标准输出，方便Render查看日志
        if cls.LOG_TO_STDOUT:
            import logging
            from logging import StreamHandler
            file_handler = StreamHandler(sys.stdout)
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

# 配置字典，用于动态选择配置
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 获取当前环境的配置
def get_config():
    """根据环境变量获取当前配置"""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])

# 测试配置生效
if __name__ == "__main__":
    # 测试数据库URL修复函数
    test_urls = [
        "postgres://user:pass@host/dbname",
        "postgres://user:pass@host.oregon-postgres.render.com/dbname",
        "postgresql://user:pass@host/dbname",
        "postgresql://user:pass@host/dbname?ssl=true"
    ]
    
    for url in test_urls:
        fixed = Config.fix_render_db_url(url)
        print(f"原始URL: {url}")
        print(f"修复后: {fixed}")
        print("-"*50) 
 
 
# -*- coding: utf-8 -*-
"""
PMA应用配置文件 - Render PostgreSQL版本
适用于连接Render云平台上的PostgreSQL数据库
"""

import os
import sys
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

class Config:
    """应用配置基类"""
    # 应用基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 修复Render的数据库URL
    @staticmethod
    def fix_render_db_url(db_url):
        """修复Render PostgreSQL数据库URL的SSL和格式问题"""
        if not db_url or 'render.com' not in db_url:
            return db_url
            
        # 1. 将postgres://替换为postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
        # 2. 解析URL以添加SSL参数
        parsed = urlparse(db_url)
        
        # 3. 确保主机名包含完整的Render域名
        hostname = parsed.hostname
        if hostname and not hostname.endswith('.render.com'):
            # 自动添加缺失的域名后缀
            if '.oregon-postgres' not in hostname:
                hostname = f"{hostname}.oregon-postgres.render.com"
                # 重建netloc部分(用户名:密码@主机名:端口)
                netloc_parts = []
                if parsed.username:
                    auth = parsed.username
                    if parsed.password:
                        auth += f":{parsed.password}"
                    netloc_parts.append(auth)
                netloc_parts.append(hostname)
                if parsed.port:
                    netloc_parts.append(str(parsed.port))
                
                netloc = '@'.join([netloc_parts[0], netloc_parts[1]]) if len(netloc_parts) > 1 else netloc_parts[0]
                if len(netloc_parts) > 2:
                    netloc += f":{netloc_parts[2]}"
                
                # 重建URL
                parsed = parsed._replace(netloc=netloc)
        
        # 4. 添加SSL参数
        query_dict = parse_qs(parsed.query)
        query_dict['sslmode'] = ['require']
        
        # 5. 重新组合URL
        parsed = parsed._replace(query=urlencode(query_dict, doseq=True))
        fixed_url = urlunparse(parsed)
        
        return fixed_url
    
    # 应用启动时自动修复数据库URL
    SQLALCHEMY_DATABASE_URI = fix_render_db_url.__func__(SQLALCHEMY_DATABASE_URI)
    
    # 其他应用配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() in ['true', '1', 't']
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@example.com']
    
    # 分页配置
    POSTS_PER_PAGE = 10

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # 在生产环境中强制使用环境变量中的秘钥
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Render特有配置 - 自动从环境变量获取配置
    @classmethod
    def init_app(cls, app):
        """生产环境特定初始化"""
        # 设置日志输出到标准输出，方便Render查看日志
        if cls.LOG_TO_STDOUT:
            import logging
            from logging import StreamHandler
            file_handler = StreamHandler(sys.stdout)
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

# 配置字典，用于动态选择配置
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 获取当前环境的配置
def get_config():
    """根据环境变量获取当前配置"""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])

# 测试配置生效
if __name__ == "__main__":
    # 测试数据库URL修复函数
    test_urls = [
        "postgres://user:pass@host/dbname",
        "postgres://user:pass@host.oregon-postgres.render.com/dbname",
        "postgresql://user:pass@host/dbname",
        "postgresql://user:pass@host/dbname?ssl=true"
    ]
    
    for url in test_urls:
        fixed = Config.fix_render_db_url(url)
        print(f"原始URL: {url}")
        print(f"修复后: {fixed}")
        print("-"*50) 
# -*- coding: utf-8 -*-
"""
PMA应用配置文件 - Render PostgreSQL版本
适用于连接Render云平台上的PostgreSQL数据库
"""

import os
import sys
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

class Config:
    """应用配置基类"""
    # 应用基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 修复Render的数据库URL
    @staticmethod
    def fix_render_db_url(db_url):
        """修复Render PostgreSQL数据库URL的SSL和格式问题"""
        if not db_url or 'render.com' not in db_url:
            return db_url
            
        # 1. 将postgres://替换为postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
        # 2. 解析URL以添加SSL参数
        parsed = urlparse(db_url)
        
        # 3. 确保主机名包含完整的Render域名
        hostname = parsed.hostname
        if hostname and not hostname.endswith('.render.com'):
            # 自动添加缺失的域名后缀
            if '.oregon-postgres' not in hostname:
                hostname = f"{hostname}.oregon-postgres.render.com"
                # 重建netloc部分(用户名:密码@主机名:端口)
                netloc_parts = []
                if parsed.username:
                    auth = parsed.username
                    if parsed.password:
                        auth += f":{parsed.password}"
                    netloc_parts.append(auth)
                netloc_parts.append(hostname)
                if parsed.port:
                    netloc_parts.append(str(parsed.port))
                
                netloc = '@'.join([netloc_parts[0], netloc_parts[1]]) if len(netloc_parts) > 1 else netloc_parts[0]
                if len(netloc_parts) > 2:
                    netloc += f":{netloc_parts[2]}"
                
                # 重建URL
                parsed = parsed._replace(netloc=netloc)
        
        # 4. 添加SSL参数
        query_dict = parse_qs(parsed.query)
        query_dict['sslmode'] = ['require']
        
        # 5. 重新组合URL
        parsed = parsed._replace(query=urlencode(query_dict, doseq=True))
        fixed_url = urlunparse(parsed)
        
        return fixed_url
    
    # 应用启动时自动修复数据库URL
    SQLALCHEMY_DATABASE_URI = fix_render_db_url.__func__(SQLALCHEMY_DATABASE_URI)
    
    # 其他应用配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() in ['true', '1', 't']
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@example.com']
    
    # 分页配置
    POSTS_PER_PAGE = 10

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # 在生产环境中强制使用环境变量中的秘钥
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Render特有配置 - 自动从环境变量获取配置
    @classmethod
    def init_app(cls, app):
        """生产环境特定初始化"""
        # 设置日志输出到标准输出，方便Render查看日志
        if cls.LOG_TO_STDOUT:
            import logging
            from logging import StreamHandler
            file_handler = StreamHandler(sys.stdout)
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

# 配置字典，用于动态选择配置
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 获取当前环境的配置
def get_config():
    """根据环境变量获取当前配置"""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])

# 测试配置生效
if __name__ == "__main__":
    # 测试数据库URL修复函数
    test_urls = [
        "postgres://user:pass@host/dbname",
        "postgres://user:pass@host.oregon-postgres.render.com/dbname",
        "postgresql://user:pass@host/dbname",
        "postgresql://user:pass@host/dbname?ssl=true"
    ]
    
    for url in test_urls:
        fixed = Config.fix_render_db_url(url)
        print(f"原始URL: {url}")
        print(f"修复后: {fixed}")
        print("-"*50) 
 
 