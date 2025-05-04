#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render部署环境数据库诊断工具
"""

import os
import sys
import socket
import logging
import platform
import json
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def inspect_database_config():
    """检查数据库配置信息"""
    logger.info("=== 数据库配置信息 ===")
    
    # 检查环境变量
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # 隐藏密码部分
        parsed = urlparse(database_url)
        if parsed.password:
            masked_url = database_url.replace(parsed.password, '********')
            logger.info(f"DATABASE_URL: {masked_url}")
        else:
            logger.info(f"DATABASE_URL: {database_url}")
        
        # 检查URL格式
        if database_url.startswith('postgres://'):
            logger.warning("DATABASE_URL使用的是postgres://前缀，SQLAlchemy需要postgresql://")
        
        # 提取主机名和端口
        try:
            parsed = urlparse(database_url)
            hostname = parsed.hostname
            port = parsed.port or 5432
            database = parsed.path.lstrip('/')
            
            logger.info(f"数据库主机: {hostname}")
            logger.info(f"数据库端口: {port}")
            logger.info(f"数据库名称: {database}")
            
            # 尝试解析主机名
            try:
                ip_address = socket.gethostbyname(hostname)
                logger.info(f"解析到的IP地址: {ip_address}")
            except socket.gaierror:
                logger.error(f"无法解析主机名 '{hostname}' 到IP地址")
        except Exception as e:
            logger.error(f"解析DATABASE_URL时出错: {str(e)}")
    else:
        logger.warning("未找到DATABASE_URL环境变量")
    
    # 检查config.py文件
    if os.path.exists('config.py'):
        try:
            from config import Config
            db_uri = getattr(Config, 'SQLALCHEMY_DATABASE_URI', None)
            if db_uri:
                # 隐藏密码
                parsed = urlparse(db_uri)
                if parsed.password:
                    masked_uri = db_uri.replace(parsed.password, '********')
                    logger.info(f"Config.SQLALCHEMY_DATABASE_URI: {masked_uri}")
                else:
                    logger.info(f"Config.SQLALCHEMY_DATABASE_URI: {db_uri}")
                
                # 检查是否包含硬编码的postgres主机
                if 'postgres:5432' in db_uri or '@postgres/' in db_uri:
                    logger.error("发现硬编码的postgres主机名，这在Render环境中无法工作")
            else:
                logger.warning("Config.SQLALCHEMY_DATABASE_URI未定义")
        except (ImportError, AttributeError) as e:
            logger.error(f"读取配置文件时出错: {str(e)}")

def search_postgres_references():
    """搜索代码库中的postgres硬编码引用"""
    logger.info("=== 搜索硬编码的postgres引用 ===")
    
    files_to_check = []
    
    # 检查常见配置文件
    for root_dir in ['.', 'app']:
        for file_path in ['config.py', '__init__.py', 'models.py', 'database.py']:
            full_path = os.path.join(root_dir, file_path)
            if os.path.exists(full_path):
                files_to_check.append(full_path)
    
    # 检查/app目录下的其他Python文件
    if os.path.exists('app'):
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py') and file not in ['__pycache__']:
                    files_to_check.append(os.path.join(root, file))
    
    found_references = []
    
    # 搜索文件中的硬编码引用
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # 查找可能的硬编码引用
                if ('host="postgres"' in content or 
                    "host='postgres'" in content or 
                    '@postgres:' in content or
                    '@postgres/' in content or
                    'postgresql://postgres:postgres@postgres:5432' in content):
                    
                    found_references.append({
                        'file': file_path,
                        'content': content
                    })
        except Exception as e:
            logger.error(f"读取文件 {file_path} 时出错: {str(e)}")
    
    if found_references:
        logger.warning(f"发现 {len(found_references)} 个文件包含硬编码的postgres引用:")
        for ref in found_references:
            logger.warning(f"- {ref['file']}")
    else:
        logger.info("未发现硬编码的postgres引用")

def test_database_connection():
    """测试数据库连接"""
    logger.info("=== 测试数据库连接 ===")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量，无法测试连接")
        return False
    
    # 修复URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        logger.info("尝试使用psycopg2直接连接...")
        import psycopg2
        
        # 从URL解析连接参数
        parsed = urlparse(database_url)
        dbname = parsed.path.lstrip('/')
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        
        # 创建连接字符串
        conn_string = f"dbname='{dbname}' user='{user}' password='{password}' host='{host}' port='{port}'"
        logger.info(f"连接参数: dbname='{dbname}' user='{user}' host='{host}' port='{port}'")
        
        # 尝试连接
        conn = psycopg2.connect(conn_string)
        conn.close()
        logger.info("psycopg2连接成功!")
        
        # 尝试使用SQLAlchemy连接
        logger.info("尝试使用SQLAlchemy连接...")
        from sqlalchemy import create_engine
        
        engine = create_engine(database_url)
        connection = engine.connect()
        connection.close()
        logger.info("SQLAlchemy连接成功!")
        
        return True
    except ImportError as e:
        logger.error(f"导入数据库驱动程序时出错: {str(e)}")
        logger.error("请确保安装了psycopg2和sqlalchemy: pip install psycopg2-binary sqlalchemy")
        return False
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info(f"=== Render数据库诊断工具 ===")
    logger.info(f"Python版本: {platform.python_version()}")
    logger.info(f"操作系统: {platform.platform()}")
    
    # 检查是否在Render环境中
    if os.environ.get('RENDER'):
        logger.info("检测到Render环境")
    else:
        logger.warning("未检测到Render环境变量，可能不在Render平台上运行")
    
    # 运行诊断
    inspect_database_config()
    search_postgres_references()
    test_database_connection()
    
    logger.info("数据库诊断完成") 
# -*- coding: utf-8 -*-
"""
Render部署环境数据库诊断工具
"""

import os
import sys
import socket
import logging
import platform
import json
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def inspect_database_config():
    """检查数据库配置信息"""
    logger.info("=== 数据库配置信息 ===")
    
    # 检查环境变量
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # 隐藏密码部分
        parsed = urlparse(database_url)
        if parsed.password:
            masked_url = database_url.replace(parsed.password, '********')
            logger.info(f"DATABASE_URL: {masked_url}")
        else:
            logger.info(f"DATABASE_URL: {database_url}")
        
        # 检查URL格式
        if database_url.startswith('postgres://'):
            logger.warning("DATABASE_URL使用的是postgres://前缀，SQLAlchemy需要postgresql://")
        
        # 提取主机名和端口
        try:
            parsed = urlparse(database_url)
            hostname = parsed.hostname
            port = parsed.port or 5432
            database = parsed.path.lstrip('/')
            
            logger.info(f"数据库主机: {hostname}")
            logger.info(f"数据库端口: {port}")
            logger.info(f"数据库名称: {database}")
            
            # 尝试解析主机名
            try:
                ip_address = socket.gethostbyname(hostname)
                logger.info(f"解析到的IP地址: {ip_address}")
            except socket.gaierror:
                logger.error(f"无法解析主机名 '{hostname}' 到IP地址")
        except Exception as e:
            logger.error(f"解析DATABASE_URL时出错: {str(e)}")
    else:
        logger.warning("未找到DATABASE_URL环境变量")
    
    # 检查config.py文件
    if os.path.exists('config.py'):
        try:
            from config import Config
            db_uri = getattr(Config, 'SQLALCHEMY_DATABASE_URI', None)
            if db_uri:
                # 隐藏密码
                parsed = urlparse(db_uri)
                if parsed.password:
                    masked_uri = db_uri.replace(parsed.password, '********')
                    logger.info(f"Config.SQLALCHEMY_DATABASE_URI: {masked_uri}")
                else:
                    logger.info(f"Config.SQLALCHEMY_DATABASE_URI: {db_uri}")
                
                # 检查是否包含硬编码的postgres主机
                if 'postgres:5432' in db_uri or '@postgres/' in db_uri:
                    logger.error("发现硬编码的postgres主机名，这在Render环境中无法工作")
            else:
                logger.warning("Config.SQLALCHEMY_DATABASE_URI未定义")
        except (ImportError, AttributeError) as e:
            logger.error(f"读取配置文件时出错: {str(e)}")

def search_postgres_references():
    """搜索代码库中的postgres硬编码引用"""
    logger.info("=== 搜索硬编码的postgres引用 ===")
    
    files_to_check = []
    
    # 检查常见配置文件
    for root_dir in ['.', 'app']:
        for file_path in ['config.py', '__init__.py', 'models.py', 'database.py']:
            full_path = os.path.join(root_dir, file_path)
            if os.path.exists(full_path):
                files_to_check.append(full_path)
    
    # 检查/app目录下的其他Python文件
    if os.path.exists('app'):
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py') and file not in ['__pycache__']:
                    files_to_check.append(os.path.join(root, file))
    
    found_references = []
    
    # 搜索文件中的硬编码引用
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # 查找可能的硬编码引用
                if ('host="postgres"' in content or 
                    "host='postgres'" in content or 
                    '@postgres:' in content or
                    '@postgres/' in content or
                    'postgresql://postgres:postgres@postgres:5432' in content):
                    
                    found_references.append({
                        'file': file_path,
                        'content': content
                    })
        except Exception as e:
            logger.error(f"读取文件 {file_path} 时出错: {str(e)}")
    
    if found_references:
        logger.warning(f"发现 {len(found_references)} 个文件包含硬编码的postgres引用:")
        for ref in found_references:
            logger.warning(f"- {ref['file']}")
    else:
        logger.info("未发现硬编码的postgres引用")

def test_database_connection():
    """测试数据库连接"""
    logger.info("=== 测试数据库连接 ===")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量，无法测试连接")
        return False
    
    # 修复URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        logger.info("尝试使用psycopg2直接连接...")
        import psycopg2
        
        # 从URL解析连接参数
        parsed = urlparse(database_url)
        dbname = parsed.path.lstrip('/')
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        
        # 创建连接字符串
        conn_string = f"dbname='{dbname}' user='{user}' password='{password}' host='{host}' port='{port}'"
        logger.info(f"连接参数: dbname='{dbname}' user='{user}' host='{host}' port='{port}'")
        
        # 尝试连接
        conn = psycopg2.connect(conn_string)
        conn.close()
        logger.info("psycopg2连接成功!")
        
        # 尝试使用SQLAlchemy连接
        logger.info("尝试使用SQLAlchemy连接...")
        from sqlalchemy import create_engine
        
        engine = create_engine(database_url)
        connection = engine.connect()
        connection.close()
        logger.info("SQLAlchemy连接成功!")
        
        return True
    except ImportError as e:
        logger.error(f"导入数据库驱动程序时出错: {str(e)}")
        logger.error("请确保安装了psycopg2和sqlalchemy: pip install psycopg2-binary sqlalchemy")
        return False
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info(f"=== Render数据库诊断工具 ===")
    logger.info(f"Python版本: {platform.python_version()}")
    logger.info(f"操作系统: {platform.platform()}")
    
    # 检查是否在Render环境中
    if os.environ.get('RENDER'):
        logger.info("检测到Render环境")
    else:
        logger.warning("未检测到Render环境变量，可能不在Render平台上运行")
    
    # 运行诊断
    inspect_database_config()
    search_postgres_references()
    test_database_connection()
    
    logger.info("数据库诊断完成") 
 
 
# -*- coding: utf-8 -*-
"""
Render部署环境数据库诊断工具
"""

import os
import sys
import socket
import logging
import platform
import json
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def inspect_database_config():
    """检查数据库配置信息"""
    logger.info("=== 数据库配置信息 ===")
    
    # 检查环境变量
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # 隐藏密码部分
        parsed = urlparse(database_url)
        if parsed.password:
            masked_url = database_url.replace(parsed.password, '********')
            logger.info(f"DATABASE_URL: {masked_url}")
        else:
            logger.info(f"DATABASE_URL: {database_url}")
        
        # 检查URL格式
        if database_url.startswith('postgres://'):
            logger.warning("DATABASE_URL使用的是postgres://前缀，SQLAlchemy需要postgresql://")
        
        # 提取主机名和端口
        try:
            parsed = urlparse(database_url)
            hostname = parsed.hostname
            port = parsed.port or 5432
            database = parsed.path.lstrip('/')
            
            logger.info(f"数据库主机: {hostname}")
            logger.info(f"数据库端口: {port}")
            logger.info(f"数据库名称: {database}")
            
            # 尝试解析主机名
            try:
                ip_address = socket.gethostbyname(hostname)
                logger.info(f"解析到的IP地址: {ip_address}")
            except socket.gaierror:
                logger.error(f"无法解析主机名 '{hostname}' 到IP地址")
        except Exception as e:
            logger.error(f"解析DATABASE_URL时出错: {str(e)}")
    else:
        logger.warning("未找到DATABASE_URL环境变量")
    
    # 检查config.py文件
    if os.path.exists('config.py'):
        try:
            from config import Config
            db_uri = getattr(Config, 'SQLALCHEMY_DATABASE_URI', None)
            if db_uri:
                # 隐藏密码
                parsed = urlparse(db_uri)
                if parsed.password:
                    masked_uri = db_uri.replace(parsed.password, '********')
                    logger.info(f"Config.SQLALCHEMY_DATABASE_URI: {masked_uri}")
                else:
                    logger.info(f"Config.SQLALCHEMY_DATABASE_URI: {db_uri}")
                
                # 检查是否包含硬编码的postgres主机
                if 'postgres:5432' in db_uri or '@postgres/' in db_uri:
                    logger.error("发现硬编码的postgres主机名，这在Render环境中无法工作")
            else:
                logger.warning("Config.SQLALCHEMY_DATABASE_URI未定义")
        except (ImportError, AttributeError) as e:
            logger.error(f"读取配置文件时出错: {str(e)}")

def search_postgres_references():
    """搜索代码库中的postgres硬编码引用"""
    logger.info("=== 搜索硬编码的postgres引用 ===")
    
    files_to_check = []
    
    # 检查常见配置文件
    for root_dir in ['.', 'app']:
        for file_path in ['config.py', '__init__.py', 'models.py', 'database.py']:
            full_path = os.path.join(root_dir, file_path)
            if os.path.exists(full_path):
                files_to_check.append(full_path)
    
    # 检查/app目录下的其他Python文件
    if os.path.exists('app'):
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py') and file not in ['__pycache__']:
                    files_to_check.append(os.path.join(root, file))
    
    found_references = []
    
    # 搜索文件中的硬编码引用
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # 查找可能的硬编码引用
                if ('host="postgres"' in content or 
                    "host='postgres'" in content or 
                    '@postgres:' in content or
                    '@postgres/' in content or
                    'postgresql://postgres:postgres@postgres:5432' in content):
                    
                    found_references.append({
                        'file': file_path,
                        'content': content
                    })
        except Exception as e:
            logger.error(f"读取文件 {file_path} 时出错: {str(e)}")
    
    if found_references:
        logger.warning(f"发现 {len(found_references)} 个文件包含硬编码的postgres引用:")
        for ref in found_references:
            logger.warning(f"- {ref['file']}")
    else:
        logger.info("未发现硬编码的postgres引用")

def test_database_connection():
    """测试数据库连接"""
    logger.info("=== 测试数据库连接 ===")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量，无法测试连接")
        return False
    
    # 修复URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        logger.info("尝试使用psycopg2直接连接...")
        import psycopg2
        
        # 从URL解析连接参数
        parsed = urlparse(database_url)
        dbname = parsed.path.lstrip('/')
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        
        # 创建连接字符串
        conn_string = f"dbname='{dbname}' user='{user}' password='{password}' host='{host}' port='{port}'"
        logger.info(f"连接参数: dbname='{dbname}' user='{user}' host='{host}' port='{port}'")
        
        # 尝试连接
        conn = psycopg2.connect(conn_string)
        conn.close()
        logger.info("psycopg2连接成功!")
        
        # 尝试使用SQLAlchemy连接
        logger.info("尝试使用SQLAlchemy连接...")
        from sqlalchemy import create_engine
        
        engine = create_engine(database_url)
        connection = engine.connect()
        connection.close()
        logger.info("SQLAlchemy连接成功!")
        
        return True
    except ImportError as e:
        logger.error(f"导入数据库驱动程序时出错: {str(e)}")
        logger.error("请确保安装了psycopg2和sqlalchemy: pip install psycopg2-binary sqlalchemy")
        return False
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info(f"=== Render数据库诊断工具 ===")
    logger.info(f"Python版本: {platform.python_version()}")
    logger.info(f"操作系统: {platform.platform()}")
    
    # 检查是否在Render环境中
    if os.environ.get('RENDER'):
        logger.info("检测到Render环境")
    else:
        logger.warning("未检测到Render环境变量，可能不在Render平台上运行")
    
    # 运行诊断
    inspect_database_config()
    search_postgres_references()
    test_database_connection()
    
    logger.info("数据库诊断完成") 
# -*- coding: utf-8 -*-
"""
Render部署环境数据库诊断工具
"""

import os
import sys
import socket
import logging
import platform
import json
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def inspect_database_config():
    """检查数据库配置信息"""
    logger.info("=== 数据库配置信息 ===")
    
    # 检查环境变量
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # 隐藏密码部分
        parsed = urlparse(database_url)
        if parsed.password:
            masked_url = database_url.replace(parsed.password, '********')
            logger.info(f"DATABASE_URL: {masked_url}")
        else:
            logger.info(f"DATABASE_URL: {database_url}")
        
        # 检查URL格式
        if database_url.startswith('postgres://'):
            logger.warning("DATABASE_URL使用的是postgres://前缀，SQLAlchemy需要postgresql://")
        
        # 提取主机名和端口
        try:
            parsed = urlparse(database_url)
            hostname = parsed.hostname
            port = parsed.port or 5432
            database = parsed.path.lstrip('/')
            
            logger.info(f"数据库主机: {hostname}")
            logger.info(f"数据库端口: {port}")
            logger.info(f"数据库名称: {database}")
            
            # 尝试解析主机名
            try:
                ip_address = socket.gethostbyname(hostname)
                logger.info(f"解析到的IP地址: {ip_address}")
            except socket.gaierror:
                logger.error(f"无法解析主机名 '{hostname}' 到IP地址")
        except Exception as e:
            logger.error(f"解析DATABASE_URL时出错: {str(e)}")
    else:
        logger.warning("未找到DATABASE_URL环境变量")
    
    # 检查config.py文件
    if os.path.exists('config.py'):
        try:
            from config import Config
            db_uri = getattr(Config, 'SQLALCHEMY_DATABASE_URI', None)
            if db_uri:
                # 隐藏密码
                parsed = urlparse(db_uri)
                if parsed.password:
                    masked_uri = db_uri.replace(parsed.password, '********')
                    logger.info(f"Config.SQLALCHEMY_DATABASE_URI: {masked_uri}")
                else:
                    logger.info(f"Config.SQLALCHEMY_DATABASE_URI: {db_uri}")
                
                # 检查是否包含硬编码的postgres主机
                if 'postgres:5432' in db_uri or '@postgres/' in db_uri:
                    logger.error("发现硬编码的postgres主机名，这在Render环境中无法工作")
            else:
                logger.warning("Config.SQLALCHEMY_DATABASE_URI未定义")
        except (ImportError, AttributeError) as e:
            logger.error(f"读取配置文件时出错: {str(e)}")

def search_postgres_references():
    """搜索代码库中的postgres硬编码引用"""
    logger.info("=== 搜索硬编码的postgres引用 ===")
    
    files_to_check = []
    
    # 检查常见配置文件
    for root_dir in ['.', 'app']:
        for file_path in ['config.py', '__init__.py', 'models.py', 'database.py']:
            full_path = os.path.join(root_dir, file_path)
            if os.path.exists(full_path):
                files_to_check.append(full_path)
    
    # 检查/app目录下的其他Python文件
    if os.path.exists('app'):
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py') and file not in ['__pycache__']:
                    files_to_check.append(os.path.join(root, file))
    
    found_references = []
    
    # 搜索文件中的硬编码引用
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # 查找可能的硬编码引用
                if ('host="postgres"' in content or 
                    "host='postgres'" in content or 
                    '@postgres:' in content or
                    '@postgres/' in content or
                    'postgresql://postgres:postgres@postgres:5432' in content):
                    
                    found_references.append({
                        'file': file_path,
                        'content': content
                    })
        except Exception as e:
            logger.error(f"读取文件 {file_path} 时出错: {str(e)}")
    
    if found_references:
        logger.warning(f"发现 {len(found_references)} 个文件包含硬编码的postgres引用:")
        for ref in found_references:
            logger.warning(f"- {ref['file']}")
    else:
        logger.info("未发现硬编码的postgres引用")

def test_database_connection():
    """测试数据库连接"""
    logger.info("=== 测试数据库连接 ===")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量，无法测试连接")
        return False
    
    # 修复URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        logger.info("尝试使用psycopg2直接连接...")
        import psycopg2
        
        # 从URL解析连接参数
        parsed = urlparse(database_url)
        dbname = parsed.path.lstrip('/')
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        
        # 创建连接字符串
        conn_string = f"dbname='{dbname}' user='{user}' password='{password}' host='{host}' port='{port}'"
        logger.info(f"连接参数: dbname='{dbname}' user='{user}' host='{host}' port='{port}'")
        
        # 尝试连接
        conn = psycopg2.connect(conn_string)
        conn.close()
        logger.info("psycopg2连接成功!")
        
        # 尝试使用SQLAlchemy连接
        logger.info("尝试使用SQLAlchemy连接...")
        from sqlalchemy import create_engine
        
        engine = create_engine(database_url)
        connection = engine.connect()
        connection.close()
        logger.info("SQLAlchemy连接成功!")
        
        return True
    except ImportError as e:
        logger.error(f"导入数据库驱动程序时出错: {str(e)}")
        logger.error("请确保安装了psycopg2和sqlalchemy: pip install psycopg2-binary sqlalchemy")
        return False
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info(f"=== Render数据库诊断工具 ===")
    logger.info(f"Python版本: {platform.python_version()}")
    logger.info(f"操作系统: {platform.platform()}")
    
    # 检查是否在Render环境中
    if os.environ.get('RENDER'):
        logger.info("检测到Render环境")
    else:
        logger.warning("未检测到Render环境变量，可能不在Render平台上运行")
    
    # 运行诊断
    inspect_database_config()
    search_postgres_references()
    test_database_connection()
    
    logger.info("数据库诊断完成") 
 
 