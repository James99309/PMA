#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具 - 禁用SSL证书验证版本
解决证书验证失败问题
"""

import os
import sys
import logging
import argparse
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render SSL修复')

def mask_url(url):
    """隐藏敏感信息"""
    if not url:
        return None
        
    parsed = urlparse(url)
    if parsed.password:
        masked_url = url.replace(parsed.password, '********')
        return masked_url
    return url

def fix_db_url(db_url):
    """修复数据库URL格式"""
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将'postgres://'替换为'postgresql://'")
    
    # 确保主机名是完整的
    parsed = urlparse(db_url)
    hostname = parsed.hostname
    
    if hostname and '.render.com' in hostname:
        if not hostname.endswith('.oregon-postgres.render.com'):
            if 'oregon-postgres.render.com' not in hostname:
                # 得到主机名的第一部分
                host_parts = hostname.split('.render.com')
                new_hostname = f"{host_parts[0]}.oregon-postgres.render.com"
                
                # 替换URL中的主机名
                db_url = db_url.replace(hostname, new_hostname)
                logger.info(f"已修复主机名: {hostname} -> {new_hostname}")
    
    return db_url

def test_direct_connection(db_url):
    """使用psycopg2直接连接，禁用SSL证书验证"""
    logger.info(f"连接URL: {mask_url(db_url)}")
    
    # 解析URL
    parsed = urlparse(db_url)
    dbname = parsed.path.strip('/')
    user = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port or 5432
    
    try:
        # 使用直接参数连接，禁用SSL证书验证
        logger.info("尝试使用禁用SSL证书验证的方式连接...")
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            sslmode='require',   # 要求SSL但不验证证书
            sslrootcert=None,
            connect_timeout=30
        )
        
        # 测试连接
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {version}")
        
        # 测试查询表
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        logger.info(f"数据库中的表: {', '.join(table_names[:5])}...")
        logger.info(f"总共发现 {len(table_names)} 个表")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return True, "连接成功"
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description='Render PostgreSQL SSL连接修复工具')
    parser.add_argument('--db-url', help='Render数据库URL')
    args = parser.parse_args()
    
    # 获取数据库URL
    db_url = args.db_url or os.environ.get('RENDER_DB_URL')
    
    if not db_url:
        logger.error("未提供数据库URL，请使用--db-url参数或设置RENDER_DB_URL环境变量")
        return 1
    
    # 修复URL格式
    db_url = fix_db_url(db_url)
    logger.info(f"使用URL: {mask_url(db_url)}")
    
    # 测试连接
    success, message = test_direct_connection(db_url)
    
    if success:
        # 设置环境变量
        os.environ['DATABASE_URL'] = db_url
        os.environ['SQLALCHEMY_DATABASE_URI'] = db_url
        os.environ['PGSSLMODE'] = 'require'
        
        logger.info("已设置以下环境变量:")
        logger.info("DATABASE_URL")
        logger.info("SQLALCHEMY_DATABASE_URI")
        logger.info("PGSSLMODE=require")
        
        logger.info("数据库连接成功！可以进行数据迁移了。")
        return 0
    else:
        logger.error(f"数据库连接失败: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具 - 禁用SSL证书验证版本
解决证书验证失败问题
"""

import os
import sys
import logging
import argparse
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render SSL修复')

def mask_url(url):
    """隐藏敏感信息"""
    if not url:
        return None
        
    parsed = urlparse(url)
    if parsed.password:
        masked_url = url.replace(parsed.password, '********')
        return masked_url
    return url

def fix_db_url(db_url):
    """修复数据库URL格式"""
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将'postgres://'替换为'postgresql://'")
    
    # 确保主机名是完整的
    parsed = urlparse(db_url)
    hostname = parsed.hostname
    
    if hostname and '.render.com' in hostname:
        if not hostname.endswith('.oregon-postgres.render.com'):
            if 'oregon-postgres.render.com' not in hostname:
                # 得到主机名的第一部分
                host_parts = hostname.split('.render.com')
                new_hostname = f"{host_parts[0]}.oregon-postgres.render.com"
                
                # 替换URL中的主机名
                db_url = db_url.replace(hostname, new_hostname)
                logger.info(f"已修复主机名: {hostname} -> {new_hostname}")
    
    return db_url

def test_direct_connection(db_url):
    """使用psycopg2直接连接，禁用SSL证书验证"""
    logger.info(f"连接URL: {mask_url(db_url)}")
    
    # 解析URL
    parsed = urlparse(db_url)
    dbname = parsed.path.strip('/')
    user = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port or 5432
    
    try:
        # 使用直接参数连接，禁用SSL证书验证
        logger.info("尝试使用禁用SSL证书验证的方式连接...")
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            sslmode='require',   # 要求SSL但不验证证书
            sslrootcert=None,
            connect_timeout=30
        )
        
        # 测试连接
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {version}")
        
        # 测试查询表
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        logger.info(f"数据库中的表: {', '.join(table_names[:5])}...")
        logger.info(f"总共发现 {len(table_names)} 个表")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return True, "连接成功"
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description='Render PostgreSQL SSL连接修复工具')
    parser.add_argument('--db-url', help='Render数据库URL')
    args = parser.parse_args()
    
    # 获取数据库URL
    db_url = args.db_url or os.environ.get('RENDER_DB_URL')
    
    if not db_url:
        logger.error("未提供数据库URL，请使用--db-url参数或设置RENDER_DB_URL环境变量")
        return 1
    
    # 修复URL格式
    db_url = fix_db_url(db_url)
    logger.info(f"使用URL: {mask_url(db_url)}")
    
    # 测试连接
    success, message = test_direct_connection(db_url)
    
    if success:
        # 设置环境变量
        os.environ['DATABASE_URL'] = db_url
        os.environ['SQLALCHEMY_DATABASE_URI'] = db_url
        os.environ['PGSSLMODE'] = 'require'
        
        logger.info("已设置以下环境变量:")
        logger.info("DATABASE_URL")
        logger.info("SQLALCHEMY_DATABASE_URI")
        logger.info("PGSSLMODE=require")
        
        logger.info("数据库连接成功！可以进行数据迁移了。")
        return 0
    else:
        logger.error(f"数据库连接失败: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具 - 禁用SSL证书验证版本
解决证书验证失败问题
"""

import os
import sys
import logging
import argparse
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render SSL修复')

def mask_url(url):
    """隐藏敏感信息"""
    if not url:
        return None
        
    parsed = urlparse(url)
    if parsed.password:
        masked_url = url.replace(parsed.password, '********')
        return masked_url
    return url

def fix_db_url(db_url):
    """修复数据库URL格式"""
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将'postgres://'替换为'postgresql://'")
    
    # 确保主机名是完整的
    parsed = urlparse(db_url)
    hostname = parsed.hostname
    
    if hostname and '.render.com' in hostname:
        if not hostname.endswith('.oregon-postgres.render.com'):
            if 'oregon-postgres.render.com' not in hostname:
                # 得到主机名的第一部分
                host_parts = hostname.split('.render.com')
                new_hostname = f"{host_parts[0]}.oregon-postgres.render.com"
                
                # 替换URL中的主机名
                db_url = db_url.replace(hostname, new_hostname)
                logger.info(f"已修复主机名: {hostname} -> {new_hostname}")
    
    return db_url

def test_direct_connection(db_url):
    """使用psycopg2直接连接，禁用SSL证书验证"""
    logger.info(f"连接URL: {mask_url(db_url)}")
    
    # 解析URL
    parsed = urlparse(db_url)
    dbname = parsed.path.strip('/')
    user = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port or 5432
    
    try:
        # 使用直接参数连接，禁用SSL证书验证
        logger.info("尝试使用禁用SSL证书验证的方式连接...")
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            sslmode='require',   # 要求SSL但不验证证书
            sslrootcert=None,
            connect_timeout=30
        )
        
        # 测试连接
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {version}")
        
        # 测试查询表
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        logger.info(f"数据库中的表: {', '.join(table_names[:5])}...")
        logger.info(f"总共发现 {len(table_names)} 个表")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return True, "连接成功"
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description='Render PostgreSQL SSL连接修复工具')
    parser.add_argument('--db-url', help='Render数据库URL')
    args = parser.parse_args()
    
    # 获取数据库URL
    db_url = args.db_url or os.environ.get('RENDER_DB_URL')
    
    if not db_url:
        logger.error("未提供数据库URL，请使用--db-url参数或设置RENDER_DB_URL环境变量")
        return 1
    
    # 修复URL格式
    db_url = fix_db_url(db_url)
    logger.info(f"使用URL: {mask_url(db_url)}")
    
    # 测试连接
    success, message = test_direct_connection(db_url)
    
    if success:
        # 设置环境变量
        os.environ['DATABASE_URL'] = db_url
        os.environ['SQLALCHEMY_DATABASE_URI'] = db_url
        os.environ['PGSSLMODE'] = 'require'
        
        logger.info("已设置以下环境变量:")
        logger.info("DATABASE_URL")
        logger.info("SQLALCHEMY_DATABASE_URI")
        logger.info("PGSSLMODE=require")
        
        logger.info("数据库连接成功！可以进行数据迁移了。")
        return 0
    else:
        logger.error(f"数据库连接失败: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL SSL连接修复工具 - 禁用SSL证书验证版本
解决证书验证失败问题
"""

import os
import sys
import logging
import argparse
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render SSL修复')

def mask_url(url):
    """隐藏敏感信息"""
    if not url:
        return None
        
    parsed = urlparse(url)
    if parsed.password:
        masked_url = url.replace(parsed.password, '********')
        return masked_url
    return url

def fix_db_url(db_url):
    """修复数据库URL格式"""
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将'postgres://'替换为'postgresql://'")
    
    # 确保主机名是完整的
    parsed = urlparse(db_url)
    hostname = parsed.hostname
    
    if hostname and '.render.com' in hostname:
        if not hostname.endswith('.oregon-postgres.render.com'):
            if 'oregon-postgres.render.com' not in hostname:
                # 得到主机名的第一部分
                host_parts = hostname.split('.render.com')
                new_hostname = f"{host_parts[0]}.oregon-postgres.render.com"
                
                # 替换URL中的主机名
                db_url = db_url.replace(hostname, new_hostname)
                logger.info(f"已修复主机名: {hostname} -> {new_hostname}")
    
    return db_url

def test_direct_connection(db_url):
    """使用psycopg2直接连接，禁用SSL证书验证"""
    logger.info(f"连接URL: {mask_url(db_url)}")
    
    # 解析URL
    parsed = urlparse(db_url)
    dbname = parsed.path.strip('/')
    user = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port or 5432
    
    try:
        # 使用直接参数连接，禁用SSL证书验证
        logger.info("尝试使用禁用SSL证书验证的方式连接...")
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            sslmode='require',   # 要求SSL但不验证证书
            sslrootcert=None,
            connect_timeout=30
        )
        
        # 测试连接
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {version}")
        
        # 测试查询表
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        logger.info(f"数据库中的表: {', '.join(table_names[:5])}...")
        logger.info(f"总共发现 {len(table_names)} 个表")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return True, "连接成功"
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description='Render PostgreSQL SSL连接修复工具')
    parser.add_argument('--db-url', help='Render数据库URL')
    args = parser.parse_args()
    
    # 获取数据库URL
    db_url = args.db_url or os.environ.get('RENDER_DB_URL')
    
    if not db_url:
        logger.error("未提供数据库URL，请使用--db-url参数或设置RENDER_DB_URL环境变量")
        return 1
    
    # 修复URL格式
    db_url = fix_db_url(db_url)
    logger.info(f"使用URL: {mask_url(db_url)}")
    
    # 测试连接
    success, message = test_direct_connection(db_url)
    
    if success:
        # 设置环境变量
        os.environ['DATABASE_URL'] = db_url
        os.environ['SQLALCHEMY_DATABASE_URI'] = db_url
        os.environ['PGSSLMODE'] = 'require'
        
        logger.info("已设置以下环境变量:")
        logger.info("DATABASE_URL")
        logger.info("SQLALCHEMY_DATABASE_URI")
        logger.info("PGSSLMODE=require")
        
        logger.info("数据库连接成功！可以进行数据迁移了。")
        return 0
    else:
        logger.error(f"数据库连接失败: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 