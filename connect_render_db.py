#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的Render PostgreSQL连接测试脚本
"""

import os
import sys
import psycopg2
import logging
import subprocess
from urllib.parse import urlparse, parse_qs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render数据库连接测试')

def test_connection(db_url=None, disable_ssl_verify=False):
    """测试数据库连接"""
    if not db_url:
        db_url = os.environ.get('RENDER_DB_URL')
        if not db_url:
            logger.error("未提供数据库URL，请设置RENDER_DB_URL环境变量或作为参数传入")
            return False
    
    logger.info(f"尝试连接到数据库...")
    
    # 屏蔽敏感信息
    masked_url = db_url
    if '@' in db_url:
        parts = db_url.split('@')
        credentials = parts[0].split('//')
        if len(credentials) > 1:
            user_pass = credentials[1].split(':')
            if len(user_pass) > 1:
                masked_pass = '*' * len(user_pass[1]) if len(user_pass) > 1 else ''
                masked_url = f"{credentials[0]}//{user_pass[0]}:{masked_pass}@{parts[1]}"
    
    logger.info(f"连接URL: {masked_url}")
    
    try:
        # 解析URL
        parsed_url = urlparse(db_url)
        db_params = {
            'dbname': parsed_url.path.lstrip('/'),
            'user': parsed_url.username,
            'password': parsed_url.password,
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432,
        }
        
        # 清除任何环境变量影响
        if 'PGSSLMODE' in os.environ:
            logger.info(f"清除PGSSLMODE环境变量，之前的值: {os.environ['PGSSLMODE']}")
            del os.environ['PGSSLMODE']
        
        if 'PGSSLROOTCERT' in os.environ:
            logger.info(f"清除PGSSLROOTCERT环境变量，之前的值: {os.environ['PGSSLROOTCERT']}")
            del os.environ['PGSSLROOTCERT']
        
        # 添加SSL选项
        if disable_ssl_verify:
            logger.info("禁用SSL证书验证")
            logger.info("尝试在连接字符串中使用sslmode=disable")
            
            # 方法1: 在连接字符串中添加参数
            db_params['sslmode'] = 'disable'
            
            # 方法2: 使用环境变量
            logger.info("同时设置环境变量PGSSLMODE=disable")
            os.environ['PGSSLMODE'] = 'disable'
        else:
            # 从URL查询参数中解析SSL模式
            query_params = parse_qs(parsed_url.query)
            if 'sslmode' in query_params:
                db_params['sslmode'] = query_params['sslmode'][0]
        
        logger.info(f"连接参数: {db_params}")
        
        # 尝试代替的命令行方式连接
        if disable_ssl_verify:
            try:
                logger.info("尝试使用psql命令行连接...")
                cmd = [
                    "PGSSLMODE=disable", 
                    "psql", 
                    "-h", db_params['host'],
                    "-p", str(db_params['port']),
                    "-U", db_params['user'],
                    "-d", db_params['dbname'],
                    "-c", "SELECT version();"
                ]
                logger.info(f"执行命令: {' '.join(cmd)}")
                
                # 由于psql会提示输入密码，我们不能直接运行
                logger.info("注意：命令行方式需要手动输入密码")
            except Exception as e:
                logger.error(f"命令行连接准备失败: {str(e)}")
        
        # 尝试连接
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # 执行简单查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        logger.info("连接成功!")
        logger.info(f"PostgreSQL版本: {version[0]}")
        
        # 查询数据库大小
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        db_size = cursor.fetchone()
        logger.info(f"数据库大小: {db_size[0]}")
        
        # 尝试查询表
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' LIMIT 5;")
        tables = cursor.fetchall()
        if tables:
            logger.info(f"数据库包含的表(前5个): {', '.join([t[0] for t in tables])}")
        else:
            logger.info("数据库中没有表或无法访问")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        
        # 如果失败且使用了SSL，尝试更新连接字符串
        if not disable_ssl_verify:
            logger.info("连接失败，尝试使用--disable-ssl-verify参数重新连接")
        
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='测试Render PostgreSQL数据库连接')
    parser.add_argument('--db-url', help='数据库连接URL')
    parser.add_argument('--disable-ssl-verify', action='store_true', help='禁用SSL证书验证')
    args = parser.parse_args()
    
    test_connection(args.db_url, args.disable_ssl_verify) 
# -*- coding: utf-8 -*-
"""
简单的Render PostgreSQL连接测试脚本
"""

import os
import sys
import psycopg2
import logging
import subprocess
from urllib.parse import urlparse, parse_qs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render数据库连接测试')

def test_connection(db_url=None, disable_ssl_verify=False):
    """测试数据库连接"""
    if not db_url:
        db_url = os.environ.get('RENDER_DB_URL')
        if not db_url:
            logger.error("未提供数据库URL，请设置RENDER_DB_URL环境变量或作为参数传入")
            return False
    
    logger.info(f"尝试连接到数据库...")
    
    # 屏蔽敏感信息
    masked_url = db_url
    if '@' in db_url:
        parts = db_url.split('@')
        credentials = parts[0].split('//')
        if len(credentials) > 1:
            user_pass = credentials[1].split(':')
            if len(user_pass) > 1:
                masked_pass = '*' * len(user_pass[1]) if len(user_pass) > 1 else ''
                masked_url = f"{credentials[0]}//{user_pass[0]}:{masked_pass}@{parts[1]}"
    
    logger.info(f"连接URL: {masked_url}")
    
    try:
        # 解析URL
        parsed_url = urlparse(db_url)
        db_params = {
            'dbname': parsed_url.path.lstrip('/'),
            'user': parsed_url.username,
            'password': parsed_url.password,
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432,
        }
        
        # 清除任何环境变量影响
        if 'PGSSLMODE' in os.environ:
            logger.info(f"清除PGSSLMODE环境变量，之前的值: {os.environ['PGSSLMODE']}")
            del os.environ['PGSSLMODE']
        
        if 'PGSSLROOTCERT' in os.environ:
            logger.info(f"清除PGSSLROOTCERT环境变量，之前的值: {os.environ['PGSSLROOTCERT']}")
            del os.environ['PGSSLROOTCERT']
        
        # 添加SSL选项
        if disable_ssl_verify:
            logger.info("禁用SSL证书验证")
            logger.info("尝试在连接字符串中使用sslmode=disable")
            
            # 方法1: 在连接字符串中添加参数
            db_params['sslmode'] = 'disable'
            
            # 方法2: 使用环境变量
            logger.info("同时设置环境变量PGSSLMODE=disable")
            os.environ['PGSSLMODE'] = 'disable'
        else:
            # 从URL查询参数中解析SSL模式
            query_params = parse_qs(parsed_url.query)
            if 'sslmode' in query_params:
                db_params['sslmode'] = query_params['sslmode'][0]
        
        logger.info(f"连接参数: {db_params}")
        
        # 尝试代替的命令行方式连接
        if disable_ssl_verify:
            try:
                logger.info("尝试使用psql命令行连接...")
                cmd = [
                    "PGSSLMODE=disable", 
                    "psql", 
                    "-h", db_params['host'],
                    "-p", str(db_params['port']),
                    "-U", db_params['user'],
                    "-d", db_params['dbname'],
                    "-c", "SELECT version();"
                ]
                logger.info(f"执行命令: {' '.join(cmd)}")
                
                # 由于psql会提示输入密码，我们不能直接运行
                logger.info("注意：命令行方式需要手动输入密码")
            except Exception as e:
                logger.error(f"命令行连接准备失败: {str(e)}")
        
        # 尝试连接
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # 执行简单查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        logger.info("连接成功!")
        logger.info(f"PostgreSQL版本: {version[0]}")
        
        # 查询数据库大小
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        db_size = cursor.fetchone()
        logger.info(f"数据库大小: {db_size[0]}")
        
        # 尝试查询表
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' LIMIT 5;")
        tables = cursor.fetchall()
        if tables:
            logger.info(f"数据库包含的表(前5个): {', '.join([t[0] for t in tables])}")
        else:
            logger.info("数据库中没有表或无法访问")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        
        # 如果失败且使用了SSL，尝试更新连接字符串
        if not disable_ssl_verify:
            logger.info("连接失败，尝试使用--disable-ssl-verify参数重新连接")
        
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='测试Render PostgreSQL数据库连接')
    parser.add_argument('--db-url', help='数据库连接URL')
    parser.add_argument('--disable-ssl-verify', action='store_true', help='禁用SSL证书验证')
    args = parser.parse_args()
    
    test_connection(args.db_url, args.disable_ssl_verify) 
 
 
            
            # 方法2: 使用环境变量
            logger.info("同时设置环境变量PGSSLMODE=disable")
            os.environ['PGSSLMODE'] = 'disable'
        else:
            # 从URL查询参数中解析SSL模式
            query_params = parse_qs(parsed_url.query)
            if 'sslmode' in query_params:
                db_params['sslmode'] = query_params['sslmode'][0]
        
        logger.info(f"连接参数: {db_params}")
        
        # 尝试代替的命令行方式连接
        if disable_ssl_verify:
            try:
                logger.info("尝试使用psql命令行连接...")
                cmd = [
                    "PGSSLMODE=disable", 
                    "psql", 
                    "-h", db_params['host'],
                    "-p", str(db_params['port']),
                    "-U", db_params['user'],
                    "-d", db_params['dbname'],
                    "-c", "SELECT version();"
                ]
                logger.info(f"执行命令: {' '.join(cmd)}")
                
                # 由于psql会提示输入密码，我们不能直接运行
                logger.info("注意：命令行方式需要手动输入密码")
            except Exception as e:
                logger.error(f"命令行连接准备失败: {str(e)}")
        
        # 尝试连接
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # 执行简单查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        logger.info("连接成功!")
        logger.info(f"PostgreSQL版本: {version[0]}")
        
        # 查询数据库大小
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        db_size = cursor.fetchone()
        logger.info(f"数据库大小: {db_size[0]}")
        
        # 尝试查询表
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' LIMIT 5;")
        tables = cursor.fetchall()
        if tables:
            logger.info(f"数据库包含的表(前5个): {', '.join([t[0] for t in tables])}")
        else:
            logger.info("数据库中没有表或无法访问")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        
        # 如果失败且使用了SSL，尝试更新连接字符串
        if not disable_ssl_verify:
            logger.info("连接失败，尝试使用--disable-ssl-verify参数重新连接")
        
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='测试Render PostgreSQL数据库连接')
    parser.add_argument('--db-url', help='数据库连接URL')
    parser.add_argument('--disable-ssl-verify', action='store_true', help='禁用SSL证书验证')
    args = parser.parse_args()
    
    test_connection(args.db_url, args.disable_ssl_verify) 
# -*- coding: utf-8 -*-
"""
简单的Render PostgreSQL连接测试脚本
"""

import os
import sys
import psycopg2
import logging
import subprocess
from urllib.parse import urlparse, parse_qs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render数据库连接测试')

def test_connection(db_url=None, disable_ssl_verify=False):
    """测试数据库连接"""
    if not db_url:
        db_url = os.environ.get('RENDER_DB_URL')
        if not db_url:
            logger.error("未提供数据库URL，请设置RENDER_DB_URL环境变量或作为参数传入")
            return False
    
    logger.info(f"尝试连接到数据库...")
    
    # 屏蔽敏感信息
    masked_url = db_url
    if '@' in db_url:
        parts = db_url.split('@')
        credentials = parts[0].split('//')
        if len(credentials) > 1:
            user_pass = credentials[1].split(':')
            if len(user_pass) > 1:
                masked_pass = '*' * len(user_pass[1]) if len(user_pass) > 1 else ''
                masked_url = f"{credentials[0]}//{user_pass[0]}:{masked_pass}@{parts[1]}"
    
    logger.info(f"连接URL: {masked_url}")
    
    try:
        # 解析URL
        parsed_url = urlparse(db_url)
        db_params = {
            'dbname': parsed_url.path.lstrip('/'),
            'user': parsed_url.username,
            'password': parsed_url.password,
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432,
        }
        
        # 清除任何环境变量影响
        if 'PGSSLMODE' in os.environ:
            logger.info(f"清除PGSSLMODE环境变量，之前的值: {os.environ['PGSSLMODE']}")
            del os.environ['PGSSLMODE']
        
        if 'PGSSLROOTCERT' in os.environ:
            logger.info(f"清除PGSSLROOTCERT环境变量，之前的值: {os.environ['PGSSLROOTCERT']}")
            del os.environ['PGSSLROOTCERT']
        
        # 添加SSL选项
        if disable_ssl_verify:
            logger.info("禁用SSL证书验证")
            logger.info("尝试在连接字符串中使用sslmode=disable")
            
            # 方法1: 在连接字符串中添加参数
            db_params['sslmode'] = 'disable'
            
            # 方法2: 使用环境变量
            logger.info("同时设置环境变量PGSSLMODE=disable")
            os.environ['PGSSLMODE'] = 'disable'
        else:
            # 从URL查询参数中解析SSL模式
            query_params = parse_qs(parsed_url.query)
            if 'sslmode' in query_params:
                db_params['sslmode'] = query_params['sslmode'][0]
        
        logger.info(f"连接参数: {db_params}")
        
        # 尝试代替的命令行方式连接
        if disable_ssl_verify:
            try:
                logger.info("尝试使用psql命令行连接...")
                cmd = [
                    "PGSSLMODE=disable", 
                    "psql", 
                    "-h", db_params['host'],
                    "-p", str(db_params['port']),
                    "-U", db_params['user'],
                    "-d", db_params['dbname'],
                    "-c", "SELECT version();"
                ]
                logger.info(f"执行命令: {' '.join(cmd)}")
                
                # 由于psql会提示输入密码，我们不能直接运行
                logger.info("注意：命令行方式需要手动输入密码")
            except Exception as e:
                logger.error(f"命令行连接准备失败: {str(e)}")
        
        # 尝试连接
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # 执行简单查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        logger.info("连接成功!")
        logger.info(f"PostgreSQL版本: {version[0]}")
        
        # 查询数据库大小
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        db_size = cursor.fetchone()
        logger.info(f"数据库大小: {db_size[0]}")
        
        # 尝试查询表
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' LIMIT 5;")
        tables = cursor.fetchall()
        if tables:
            logger.info(f"数据库包含的表(前5个): {', '.join([t[0] for t in tables])}")
        else:
            logger.info("数据库中没有表或无法访问")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        
        # 如果失败且使用了SSL，尝试更新连接字符串
        if not disable_ssl_verify:
            logger.info("连接失败，尝试使用--disable-ssl-verify参数重新连接")
        
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='测试Render PostgreSQL数据库连接')
    parser.add_argument('--db-url', help='数据库连接URL')
    parser.add_argument('--disable-ssl-verify', action='store_true', help='禁用SSL证书验证')
    args = parser.parse_args()
    
    test_connection(args.db_url, args.disable_ssl_verify) 
 
 