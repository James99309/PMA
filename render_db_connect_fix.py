#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具
全面解决Render数据库连接问题的综合解决方案
"""

import os
import sys
import logging
import argparse
import json
import traceback
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_db_fix.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

def mask_url(url):
    """隐藏敏感信息"""
    if not url:
        return None
        
    parsed = urlparse(url)
    if parsed.password:
        masked_url = url.replace(parsed.password, '********')
        return masked_url
    return url

def fix_database_url(database_url):
    """修复数据库URL格式问题"""
    if not database_url:
        logger.error("未提供数据库URL")
        return None
    
    logger.info(f"修复数据库URL: {mask_url(database_url)}")
    
    # 修复协议前缀
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将'postgres://'替换为'postgresql://'")
    
    # 解析URL
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # 修复主机名
    hostname = parsed.hostname
    if hostname and '.render.com' in hostname:
        # 检查是否包含完整的Render主机名
        if not hostname.endswith('.oregon-postgres.render.com') and not hostname.endswith('.oregon-postgres.render.com/'):
            if 'oregon-postgres.render.com' not in hostname:
                # 找到第一个.render.com前的部分
                host_parts = hostname.split('.render.com')
                new_hostname = f"{host_parts[0]}.oregon-postgres.render.com"
                
                # 替换主机名
                netloc_parts = parsed.netloc.split('@')
                if len(netloc_parts) > 1:
                    auth, old_host = netloc_parts
                    if ':' in old_host:  # 包含端口
                        old_host_parts = old_host.split(':')
                        new_netloc = f"{auth}@{new_hostname}:{old_host_parts[1]}"
                    else:
                        new_netloc = f"{auth}@{new_hostname}"
                else:
                    if ':' in parsed.netloc:  # 包含端口
                        host_port = parsed.netloc.split(':')
                        new_netloc = f"{new_hostname}:{host_port[1]}"
                    else:
                        new_netloc = new_hostname
                
                # 重建URL
                parts = list(parsed)
                parts[1] = new_netloc
                database_url = urlunparse(parts)
                logger.info(f"已修复主机名: {hostname} -> {new_hostname}")
    
    # 修复SSL参数
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # 检查是否已有SSL参数
    has_ssl_mode = 'sslmode' in query_params
    
    if not has_ssl_mode:
        # 添加SSL参数
        query_params['sslmode'] = ['require']
        
        # 重建URL
        parts = list(parsed)
        parts[4] = urlencode(query_params, doseq=True)
        database_url = urlunparse(parts)
        logger.info("已添加'sslmode=require'参数")
    
    logger.info(f"修复后的URL: {mask_url(database_url)}")
    return database_url

def test_connection(database_url):
    """测试数据库连接"""
    try:
        logger.info("测试数据库连接...")
        
        # 尝试导入所需库
        try:
            from sqlalchemy import create_engine, text
        except ImportError:
            logger.error("缺少SQLAlchemy库。请安装：pip install sqlalchemy psycopg2-binary")
            return False
        
        # 创建SQLAlchemy引擎
        connect_args = {
            'connect_timeout': 30,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
        
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,  # 检查连接是否有效
            pool_recycle=300     # 5分钟后回收连接
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功! PostgreSQL版本: {version}")
            
            # 获取数据库信息
            logger.info("获取数据库表信息...")
            tables_result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in tables_result]
            logger.info(f"数据库中的表: {', '.join(tables[:5])}...")
        
        logger.info("数据库连接测试成功!")
        return True
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        traceback.print_exc()
        
        # 错误分析和故障排除
        error_msg = str(e).lower()
        if "ssl connection has been closed unexpectedly" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请确保URL中包含正确的SSL参数: ?sslmode=require")
            logger.info("2. 检查您的网络环境是否限制SSL连接")
            logger.info("3. 尝试设置环境变量: export PGSSLMODE=require")
        elif "password authentication failed" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请检查URL中的用户名和密码是否正确")
            logger.info("2. 确认Render数据库的访问凭证是最新的")
        elif "could not translate host name" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请检查主机名格式是否正确")
            logger.info("2. 确保主机名包含完整的Render域名后缀")
        
        return False

def setup_connection_in_env(database_url):
    """设置连接参数到环境变量"""
    os.environ['DATABASE_URL'] = database_url
    os.environ['SQLALCHEMY_DATABASE_URI'] = database_url
    os.environ['PGSSLMODE'] = 'require'
    
    logger.info("已设置以下环境变量:")
    logger.info("DATABASE_URL")
    logger.info("SQLALCHEMY_DATABASE_URI")
    logger.info("PGSSLMODE=require")
    
    return True

def update_config_py(database_url):
    """更新config.py文件中的数据库URL"""
    config_file = 'config.py'
    if not os.path.exists(config_file):
        logger.warning(f"未找到{config_file}文件，跳过更新")
        return False
    
    logger.info(f"更新{config_file}文件...")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找数据库URL
        import re
        patterns = [
            r'(SQLALCHEMY_DATABASE_URI\s*=\s*[\'"])[^\'"]+([\'"])',
            r'(DATABASE_URL\s*=\s*[\'"])[^\'"]+([\'"])'
        ]
        
        updated = False
        for pattern in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, r'\1' + database_url + r'\2', content)
                updated = True
        
        if updated:
            # 备份原文件
            backup_file = f"{config_file}.bak"
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 写入更新
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"已更新{config_file}文件，原文件已备份为{backup_file}")
            return True
        else:
            logger.warning(f"在{config_file}中未找到数据库URL配置")
            return False
    except Exception as e:
        logger.error(f"更新{config_file}文件失败: {str(e)}")
        return False

def generate_connection_examples(database_url):
    """生成不同框架的连接示例"""
    logger.info("\n=== 连接示例 ===")
    
    # Flask-SQLAlchemy示例
    logger.info("Flask-SQLAlchemy连接示例:")
    logger.info(f"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = '{database_url}'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {{
    'pool_pre_ping': True,  # 检查连接是否有效
    'pool_recycle': 300,    # 5分钟后回收连接
    'connect_args': {{'sslmode': 'require'}}
}}
db = SQLAlchemy(app)
    """.strip())
    
    # SQLAlchemy示例
    logger.info("\nSQLAlchemy直接连接示例:")
    logger.info(f"""
from sqlalchemy import create_engine

engine = create_engine(
    '{database_url}',
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={{'sslmode': 'require'}}
)
    """.strip())
    
    # Psycopg2示例
    logger.info("\nPsycopg2连接示例:")
    logger.info(f"""
import psycopg2

conn = psycopg2.connect('{database_url}')
    """.strip())

def main():
    parser = argparse.ArgumentParser(description='Render PostgreSQL SSL连接修复工具')
    parser.add_argument('--db-url', help='Render数据库URL')
    parser.add_argument('--test', action='store_true', help='仅测试连接')
    parser.add_argument('--update-config', action='store_true', help='更新config.py文件')
    parser.add_argument('--set-env', action='store_true', help='设置环境变量')
    args = parser.parse_args()
    
    # 获取数据库URL
    database_url = args.db_url or os.environ.get('DATABASE_URL') or os.environ.get('RENDER_DB_URL')
    
    if not database_url:
        logger.error("未提供数据库URL，请使用--db-url参数或设置DATABASE_URL环境变量")
        return 1
    
    # 修复数据库URL
    fixed_url = fix_database_url(database_url)
    if not fixed_url:
        logger.error("修复数据库URL失败")
        return 1
    
    # 仅测试连接
    if args.test:
        success = test_connection(fixed_url)
        return 0 if success else 1
    
    # 设置环境变量
    if args.set_env:
        setup_connection_in_env(fixed_url)
    
    # 更新config.py
    if args.update_config:
        update_config_py(fixed_url)
    
    # 测试连接
    success = test_connection(fixed_url)
    
    # 生成连接示例
    if success:
        generate_connection_examples(fixed_url)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具
全面解决Render数据库连接问题的综合解决方案
"""

import os
import sys
import logging
import argparse
import json
import traceback
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_db_fix.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

def mask_url(url):
    """隐藏敏感信息"""
    if not url:
        return None
        
    parsed = urlparse(url)
    if parsed.password:
        masked_url = url.replace(parsed.password, '********')
        return masked_url
    return url

def fix_database_url(database_url):
    """修复数据库URL格式问题"""
    if not database_url:
        logger.error("未提供数据库URL")
        return None
    
    logger.info(f"修复数据库URL: {mask_url(database_url)}")
    
    # 修复协议前缀
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将'postgres://'替换为'postgresql://'")
    
    # 解析URL
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # 修复主机名
    hostname = parsed.hostname
    if hostname and '.render.com' in hostname:
        # 检查是否包含完整的Render主机名
        if not hostname.endswith('.oregon-postgres.render.com') and not hostname.endswith('.oregon-postgres.render.com/'):
            if 'oregon-postgres.render.com' not in hostname:
                # 找到第一个.render.com前的部分
                host_parts = hostname.split('.render.com')
                new_hostname = f"{host_parts[0]}.oregon-postgres.render.com"
                
                # 替换主机名
                netloc_parts = parsed.netloc.split('@')
                if len(netloc_parts) > 1:
                    auth, old_host = netloc_parts
                    if ':' in old_host:  # 包含端口
                        old_host_parts = old_host.split(':')
                        new_netloc = f"{auth}@{new_hostname}:{old_host_parts[1]}"
                    else:
                        new_netloc = f"{auth}@{new_hostname}"
                else:
                    if ':' in parsed.netloc:  # 包含端口
                        host_port = parsed.netloc.split(':')
                        new_netloc = f"{new_hostname}:{host_port[1]}"
                    else:
                        new_netloc = new_hostname
                
                # 重建URL
                parts = list(parsed)
                parts[1] = new_netloc
                database_url = urlunparse(parts)
                logger.info(f"已修复主机名: {hostname} -> {new_hostname}")
    
    # 修复SSL参数
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # 检查是否已有SSL参数
    has_ssl_mode = 'sslmode' in query_params
    
    if not has_ssl_mode:
        # 添加SSL参数
        query_params['sslmode'] = ['require']
        
        # 重建URL
        parts = list(parsed)
        parts[4] = urlencode(query_params, doseq=True)
        database_url = urlunparse(parts)
        logger.info("已添加'sslmode=require'参数")
    
    logger.info(f"修复后的URL: {mask_url(database_url)}")
    return database_url

def test_connection(database_url):
    """测试数据库连接"""
    try:
        logger.info("测试数据库连接...")
        
        # 尝试导入所需库
        try:
            from sqlalchemy import create_engine, text
        except ImportError:
            logger.error("缺少SQLAlchemy库。请安装：pip install sqlalchemy psycopg2-binary")
            return False
        
        # 创建SQLAlchemy引擎
        connect_args = {
            'connect_timeout': 30,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
        
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,  # 检查连接是否有效
            pool_recycle=300     # 5分钟后回收连接
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功! PostgreSQL版本: {version}")
            
            # 获取数据库信息
            logger.info("获取数据库表信息...")
            tables_result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in tables_result]
            logger.info(f"数据库中的表: {', '.join(tables[:5])}...")
        
        logger.info("数据库连接测试成功!")
        return True
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        traceback.print_exc()
        
        # 错误分析和故障排除
        error_msg = str(e).lower()
        if "ssl connection has been closed unexpectedly" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请确保URL中包含正确的SSL参数: ?sslmode=require")
            logger.info("2. 检查您的网络环境是否限制SSL连接")
            logger.info("3. 尝试设置环境变量: export PGSSLMODE=require")
        elif "password authentication failed" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请检查URL中的用户名和密码是否正确")
            logger.info("2. 确认Render数据库的访问凭证是最新的")
        elif "could not translate host name" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请检查主机名格式是否正确")
            logger.info("2. 确保主机名包含完整的Render域名后缀")
        
        return False

def setup_connection_in_env(database_url):
    """设置连接参数到环境变量"""
    os.environ['DATABASE_URL'] = database_url
    os.environ['SQLALCHEMY_DATABASE_URI'] = database_url
    os.environ['PGSSLMODE'] = 'require'
    
    logger.info("已设置以下环境变量:")
    logger.info("DATABASE_URL")
    logger.info("SQLALCHEMY_DATABASE_URI")
    logger.info("PGSSLMODE=require")
    
    return True

def update_config_py(database_url):
    """更新config.py文件中的数据库URL"""
    config_file = 'config.py'
    if not os.path.exists(config_file):
        logger.warning(f"未找到{config_file}文件，跳过更新")
        return False
    
    logger.info(f"更新{config_file}文件...")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找数据库URL
        import re
        patterns = [
            r'(SQLALCHEMY_DATABASE_URI\s*=\s*[\'"])[^\'"]+([\'"])',
            r'(DATABASE_URL\s*=\s*[\'"])[^\'"]+([\'"])'
        ]
        
        updated = False
        for pattern in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, r'\1' + database_url + r'\2', content)
                updated = True
        
        if updated:
            # 备份原文件
            backup_file = f"{config_file}.bak"
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 写入更新
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"已更新{config_file}文件，原文件已备份为{backup_file}")
            return True
        else:
            logger.warning(f"在{config_file}中未找到数据库URL配置")
            return False
    except Exception as e:
        logger.error(f"更新{config_file}文件失败: {str(e)}")
        return False

def generate_connection_examples(database_url):
    """生成不同框架的连接示例"""
    logger.info("\n=== 连接示例 ===")
    
    # Flask-SQLAlchemy示例
    logger.info("Flask-SQLAlchemy连接示例:")
    logger.info(f"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = '{database_url}'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {{
    'pool_pre_ping': True,  # 检查连接是否有效
    'pool_recycle': 300,    # 5分钟后回收连接
    'connect_args': {{'sslmode': 'require'}}
}}
db = SQLAlchemy(app)
    """.strip())
    
    # SQLAlchemy示例
    logger.info("\nSQLAlchemy直接连接示例:")
    logger.info(f"""
from sqlalchemy import create_engine

engine = create_engine(
    '{database_url}',
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={{'sslmode': 'require'}}
)
    """.strip())
    
    # Psycopg2示例
    logger.info("\nPsycopg2连接示例:")
    logger.info(f"""
import psycopg2

conn = psycopg2.connect('{database_url}')
    """.strip())

def main():
    parser = argparse.ArgumentParser(description='Render PostgreSQL SSL连接修复工具')
    parser.add_argument('--db-url', help='Render数据库URL')
    parser.add_argument('--test', action='store_true', help='仅测试连接')
    parser.add_argument('--update-config', action='store_true', help='更新config.py文件')
    parser.add_argument('--set-env', action='store_true', help='设置环境变量')
    args = parser.parse_args()
    
    # 获取数据库URL
    database_url = args.db_url or os.environ.get('DATABASE_URL') or os.environ.get('RENDER_DB_URL')
    
    if not database_url:
        logger.error("未提供数据库URL，请使用--db-url参数或设置DATABASE_URL环境变量")
        return 1
    
    # 修复数据库URL
    fixed_url = fix_database_url(database_url)
    if not fixed_url:
        logger.error("修复数据库URL失败")
        return 1
    
    # 仅测试连接
    if args.test:
        success = test_connection(fixed_url)
        return 0 if success else 1
    
    # 设置环境变量
    if args.set_env:
        setup_connection_in_env(fixed_url)
    
    # 更新config.py
    if args.update_config:
        update_config_py(fixed_url)
    
    # 测试连接
    success = test_connection(fixed_url)
    
    # 生成连接示例
    if success:
        generate_connection_examples(fixed_url)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具
全面解决Render数据库连接问题的综合解决方案
"""

import os
import sys
import logging
import argparse
import json
import traceback
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_db_fix.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

def mask_url(url):
    """隐藏敏感信息"""
    if not url:
        return None
        
    parsed = urlparse(url)
    if parsed.password:
        masked_url = url.replace(parsed.password, '********')
        return masked_url
    return url

def fix_database_url(database_url):
    """修复数据库URL格式问题"""
    if not database_url:
        logger.error("未提供数据库URL")
        return None
    
    logger.info(f"修复数据库URL: {mask_url(database_url)}")
    
    # 修复协议前缀
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将'postgres://'替换为'postgresql://'")
    
    # 解析URL
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # 修复主机名
    hostname = parsed.hostname
    if hostname and '.render.com' in hostname:
        # 检查是否包含完整的Render主机名
        if not hostname.endswith('.oregon-postgres.render.com') and not hostname.endswith('.oregon-postgres.render.com/'):
            if 'oregon-postgres.render.com' not in hostname:
                # 找到第一个.render.com前的部分
                host_parts = hostname.split('.render.com')
                new_hostname = f"{host_parts[0]}.oregon-postgres.render.com"
                
                # 替换主机名
                netloc_parts = parsed.netloc.split('@')
                if len(netloc_parts) > 1:
                    auth, old_host = netloc_parts
                    if ':' in old_host:  # 包含端口
                        old_host_parts = old_host.split(':')
                        new_netloc = f"{auth}@{new_hostname}:{old_host_parts[1]}"
                    else:
                        new_netloc = f"{auth}@{new_hostname}"
                else:
                    if ':' in parsed.netloc:  # 包含端口
                        host_port = parsed.netloc.split(':')
                        new_netloc = f"{new_hostname}:{host_port[1]}"
                    else:
                        new_netloc = new_hostname
                
                # 重建URL
                parts = list(parsed)
                parts[1] = new_netloc
                database_url = urlunparse(parts)
                logger.info(f"已修复主机名: {hostname} -> {new_hostname}")
    
    # 修复SSL参数
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # 检查是否已有SSL参数
    has_ssl_mode = 'sslmode' in query_params
    
    if not has_ssl_mode:
        # 添加SSL参数
        query_params['sslmode'] = ['require']
        
        # 重建URL
        parts = list(parsed)
        parts[4] = urlencode(query_params, doseq=True)
        database_url = urlunparse(parts)
        logger.info("已添加'sslmode=require'参数")
    
    logger.info(f"修复后的URL: {mask_url(database_url)}")
    return database_url

def test_connection(database_url):
    """测试数据库连接"""
    try:
        logger.info("测试数据库连接...")
        
        # 尝试导入所需库
        try:
            from sqlalchemy import create_engine, text
        except ImportError:
            logger.error("缺少SQLAlchemy库。请安装：pip install sqlalchemy psycopg2-binary")
            return False
        
        # 创建SQLAlchemy引擎
        connect_args = {
            'connect_timeout': 30,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
        
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,  # 检查连接是否有效
            pool_recycle=300     # 5分钟后回收连接
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功! PostgreSQL版本: {version}")
            
            # 获取数据库信息
            logger.info("获取数据库表信息...")
            tables_result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in tables_result]
            logger.info(f"数据库中的表: {', '.join(tables[:5])}...")
        
        logger.info("数据库连接测试成功!")
        return True
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        traceback.print_exc()
        
        # 错误分析和故障排除
        error_msg = str(e).lower()
        if "ssl connection has been closed unexpectedly" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请确保URL中包含正确的SSL参数: ?sslmode=require")
            logger.info("2. 检查您的网络环境是否限制SSL连接")
            logger.info("3. 尝试设置环境变量: export PGSSLMODE=require")
        elif "password authentication failed" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请检查URL中的用户名和密码是否正确")
            logger.info("2. 确认Render数据库的访问凭证是最新的")
        elif "could not translate host name" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请检查主机名格式是否正确")
            logger.info("2. 确保主机名包含完整的Render域名后缀")
        
        return False

def setup_connection_in_env(database_url):
    """设置连接参数到环境变量"""
    os.environ['DATABASE_URL'] = database_url
    os.environ['SQLALCHEMY_DATABASE_URI'] = database_url
    os.environ['PGSSLMODE'] = 'require'
    
    logger.info("已设置以下环境变量:")
    logger.info("DATABASE_URL")
    logger.info("SQLALCHEMY_DATABASE_URI")
    logger.info("PGSSLMODE=require")
    
    return True

def update_config_py(database_url):
    """更新config.py文件中的数据库URL"""
    config_file = 'config.py'
    if not os.path.exists(config_file):
        logger.warning(f"未找到{config_file}文件，跳过更新")
        return False
    
    logger.info(f"更新{config_file}文件...")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找数据库URL
        import re
        patterns = [
            r'(SQLALCHEMY_DATABASE_URI\s*=\s*[\'"])[^\'"]+([\'"])',
            r'(DATABASE_URL\s*=\s*[\'"])[^\'"]+([\'"])'
        ]
        
        updated = False
        for pattern in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, r'\1' + database_url + r'\2', content)
                updated = True
        
        if updated:
            # 备份原文件
            backup_file = f"{config_file}.bak"
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 写入更新
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"已更新{config_file}文件，原文件已备份为{backup_file}")
            return True
        else:
            logger.warning(f"在{config_file}中未找到数据库URL配置")
            return False
    except Exception as e:
        logger.error(f"更新{config_file}文件失败: {str(e)}")
        return False

def generate_connection_examples(database_url):
    """生成不同框架的连接示例"""
    logger.info("\n=== 连接示例 ===")
    
    # Flask-SQLAlchemy示例
    logger.info("Flask-SQLAlchemy连接示例:")
    logger.info(f"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = '{database_url}'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {{
    'pool_pre_ping': True,  # 检查连接是否有效
    'pool_recycle': 300,    # 5分钟后回收连接
    'connect_args': {{'sslmode': 'require'}}
}}
db = SQLAlchemy(app)
    """.strip())
    
    # SQLAlchemy示例
    logger.info("\nSQLAlchemy直接连接示例:")
    logger.info(f"""
from sqlalchemy import create_engine

engine = create_engine(
    '{database_url}',
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={{'sslmode': 'require'}}
)
    """.strip())
    
    # Psycopg2示例
    logger.info("\nPsycopg2连接示例:")
    logger.info(f"""
import psycopg2

conn = psycopg2.connect('{database_url}')
    """.strip())

def main():
    parser = argparse.ArgumentParser(description='Render PostgreSQL SSL连接修复工具')
    parser.add_argument('--db-url', help='Render数据库URL')
    parser.add_argument('--test', action='store_true', help='仅测试连接')
    parser.add_argument('--update-config', action='store_true', help='更新config.py文件')
    parser.add_argument('--set-env', action='store_true', help='设置环境变量')
    args = parser.parse_args()
    
    # 获取数据库URL
    database_url = args.db_url or os.environ.get('DATABASE_URL') or os.environ.get('RENDER_DB_URL')
    
    if not database_url:
        logger.error("未提供数据库URL，请使用--db-url参数或设置DATABASE_URL环境变量")
        return 1
    
    # 修复数据库URL
    fixed_url = fix_database_url(database_url)
    if not fixed_url:
        logger.error("修复数据库URL失败")
        return 1
    
    # 仅测试连接
    if args.test:
        success = test_connection(fixed_url)
        return 0 if success else 1
    
    # 设置环境变量
    if args.set_env:
        setup_connection_in_env(fixed_url)
    
    # 更新config.py
    if args.update_config:
        update_config_py(fixed_url)
    
    # 测试连接
    success = test_connection(fixed_url)
    
    # 生成连接示例
    if success:
        generate_connection_examples(fixed_url)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具
全面解决Render数据库连接问题的综合解决方案
"""

import os
import sys
import logging
import argparse
import json
import traceback
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_db_fix.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

def mask_url(url):
    """隐藏敏感信息"""
    if not url:
        return None
        
    parsed = urlparse(url)
    if parsed.password:
        masked_url = url.replace(parsed.password, '********')
        return masked_url
    return url

def fix_database_url(database_url):
    """修复数据库URL格式问题"""
    if not database_url:
        logger.error("未提供数据库URL")
        return None
    
    logger.info(f"修复数据库URL: {mask_url(database_url)}")
    
    # 修复协议前缀
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将'postgres://'替换为'postgresql://'")
    
    # 解析URL
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # 修复主机名
    hostname = parsed.hostname
    if hostname and '.render.com' in hostname:
        # 检查是否包含完整的Render主机名
        if not hostname.endswith('.oregon-postgres.render.com') and not hostname.endswith('.oregon-postgres.render.com/'):
            if 'oregon-postgres.render.com' not in hostname:
                # 找到第一个.render.com前的部分
                host_parts = hostname.split('.render.com')
                new_hostname = f"{host_parts[0]}.oregon-postgres.render.com"
                
                # 替换主机名
                netloc_parts = parsed.netloc.split('@')
                if len(netloc_parts) > 1:
                    auth, old_host = netloc_parts
                    if ':' in old_host:  # 包含端口
                        old_host_parts = old_host.split(':')
                        new_netloc = f"{auth}@{new_hostname}:{old_host_parts[1]}"
                    else:
                        new_netloc = f"{auth}@{new_hostname}"
                else:
                    if ':' in parsed.netloc:  # 包含端口
                        host_port = parsed.netloc.split(':')
                        new_netloc = f"{new_hostname}:{host_port[1]}"
                    else:
                        new_netloc = new_hostname
                
                # 重建URL
                parts = list(parsed)
                parts[1] = new_netloc
                database_url = urlunparse(parts)
                logger.info(f"已修复主机名: {hostname} -> {new_hostname}")
    
    # 修复SSL参数
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # 检查是否已有SSL参数
    has_ssl_mode = 'sslmode' in query_params
    
    if not has_ssl_mode:
        # 添加SSL参数
        query_params['sslmode'] = ['require']
        
        # 重建URL
        parts = list(parsed)
        parts[4] = urlencode(query_params, doseq=True)
        database_url = urlunparse(parts)
        logger.info("已添加'sslmode=require'参数")
    
    logger.info(f"修复后的URL: {mask_url(database_url)}")
    return database_url

def test_connection(database_url):
    """测试数据库连接"""
    try:
        logger.info("测试数据库连接...")
        
        # 尝试导入所需库
        try:
            from sqlalchemy import create_engine, text
        except ImportError:
            logger.error("缺少SQLAlchemy库。请安装：pip install sqlalchemy psycopg2-binary")
            return False
        
        # 创建SQLAlchemy引擎
        connect_args = {
            'connect_timeout': 30,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
        
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,  # 检查连接是否有效
            pool_recycle=300     # 5分钟后回收连接
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功! PostgreSQL版本: {version}")
            
            # 获取数据库信息
            logger.info("获取数据库表信息...")
            tables_result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in tables_result]
            logger.info(f"数据库中的表: {', '.join(tables[:5])}...")
        
        logger.info("数据库连接测试成功!")
        return True
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        traceback.print_exc()
        
        # 错误分析和故障排除
        error_msg = str(e).lower()
        if "ssl connection has been closed unexpectedly" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请确保URL中包含正确的SSL参数: ?sslmode=require")
            logger.info("2. 检查您的网络环境是否限制SSL连接")
            logger.info("3. 尝试设置环境变量: export PGSSLMODE=require")
        elif "password authentication failed" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请检查URL中的用户名和密码是否正确")
            logger.info("2. 确认Render数据库的访问凭证是最新的")
        elif "could not translate host name" in error_msg:
            logger.info("\n解决方案建议:")
            logger.info("1. 请检查主机名格式是否正确")
            logger.info("2. 确保主机名包含完整的Render域名后缀")
        
        return False

def setup_connection_in_env(database_url):
    """设置连接参数到环境变量"""
    os.environ['DATABASE_URL'] = database_url
    os.environ['SQLALCHEMY_DATABASE_URI'] = database_url
    os.environ['PGSSLMODE'] = 'require'
    
    logger.info("已设置以下环境变量:")
    logger.info("DATABASE_URL")
    logger.info("SQLALCHEMY_DATABASE_URI")
    logger.info("PGSSLMODE=require")
    
    return True

def update_config_py(database_url):
    """更新config.py文件中的数据库URL"""
    config_file = 'config.py'
    if not os.path.exists(config_file):
        logger.warning(f"未找到{config_file}文件，跳过更新")
        return False
    
    logger.info(f"更新{config_file}文件...")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找数据库URL
        import re
        patterns = [
            r'(SQLALCHEMY_DATABASE_URI\s*=\s*[\'"])[^\'"]+([\'"])',
            r'(DATABASE_URL\s*=\s*[\'"])[^\'"]+([\'"])'
        ]
        
        updated = False
        for pattern in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, r'\1' + database_url + r'\2', content)
                updated = True
        
        if updated:
            # 备份原文件
            backup_file = f"{config_file}.bak"
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 写入更新
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"已更新{config_file}文件，原文件已备份为{backup_file}")
            return True
        else:
            logger.warning(f"在{config_file}中未找到数据库URL配置")
            return False
    except Exception as e:
        logger.error(f"更新{config_file}文件失败: {str(e)}")
        return False

def generate_connection_examples(database_url):
    """生成不同框架的连接示例"""
    logger.info("\n=== 连接示例 ===")
    
    # Flask-SQLAlchemy示例
    logger.info("Flask-SQLAlchemy连接示例:")
    logger.info(f"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = '{database_url}'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {{
    'pool_pre_ping': True,  # 检查连接是否有效
    'pool_recycle': 300,    # 5分钟后回收连接
    'connect_args': {{'sslmode': 'require'}}
}}
db = SQLAlchemy(app)
    """.strip())
    
    # SQLAlchemy示例
    logger.info("\nSQLAlchemy直接连接示例:")
    logger.info(f"""
from sqlalchemy import create_engine

engine = create_engine(
    '{database_url}',
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={{'sslmode': 'require'}}
)
    """.strip())
    
    # Psycopg2示例
    logger.info("\nPsycopg2连接示例:")
    logger.info(f"""
import psycopg2

conn = psycopg2.connect('{database_url}')
    """.strip())

def main():
    parser = argparse.ArgumentParser(description='Render PostgreSQL SSL连接修复工具')
    parser.add_argument('--db-url', help='Render数据库URL')
    parser.add_argument('--test', action='store_true', help='仅测试连接')
    parser.add_argument('--update-config', action='store_true', help='更新config.py文件')
    parser.add_argument('--set-env', action='store_true', help='设置环境变量')
    args = parser.parse_args()
    
    # 获取数据库URL
    database_url = args.db_url or os.environ.get('DATABASE_URL') or os.environ.get('RENDER_DB_URL')
    
    if not database_url:
        logger.error("未提供数据库URL，请使用--db-url参数或设置DATABASE_URL环境变量")
        return 1
    
    # 修复数据库URL
    fixed_url = fix_database_url(database_url)
    if not fixed_url:
        logger.error("修复数据库URL失败")
        return 1
    
    # 仅测试连接
    if args.test:
        success = test_connection(fixed_url)
        return 0 if success else 1
    
    # 设置环境变量
    if args.set_env:
        setup_connection_in_env(fixed_url)
    
    # 更新config.py
    if args.update_config:
        update_config_py(fixed_url)
    
    # 测试连接
    success = test_connection(fixed_url)
    
    # 生成连接示例
    if success:
        generate_connection_examples(fixed_url)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 