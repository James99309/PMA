#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL数据库连接测试脚本
尝试不同的SSL连接方式解决连接问题
"""

import os
import sys
import logging
import json
import psycopg2
from urllib.parse import urlparse, parse_qs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PostgreSQL连接测试')

# 测试的数据库URL - 已更新为正确的URL
TEST_DB_URL = os.environ.get('RENDER_DB_URL', 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d')

def mask_url(url):
    """隐藏敏感信息"""
    if '@' in url:
        parts = url.split('@')
        auth_part = parts[0]
        if ':' in auth_part:
            auth_parts = auth_part.split(':')
            if len(auth_parts) > 2:
                # 多个:的情况
                user = auth_parts[0]
                masked = f"{user}:{'*' * 10}"
                return f"{masked}@{parts[1]}"
            else:
                # 标准格式
                user = auth_parts[0]
                masked = f"{user}:{'*' * 10}"
                return f"{masked}@{parts[1]}"
    return url

def test_direct_connect():
    """测试直接连接"""
    logger.info("====== 测试直接连接 ======")
    try:
        logger.info(f"连接URL: {mask_url(TEST_DB_URL)}")
        conn = psycopg2.connect(TEST_DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"连接成功! PostgreSQL版本: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False

def test_with_sslmode():
    """测试添加sslmode参数"""
    logger.info("====== 测试添加sslmode=require ======")
    try:
        db_url = TEST_DB_URL
        if '?' not in db_url:
            db_url += '?sslmode=require'
        elif 'sslmode=' not in db_url:
            db_url += '&sslmode=require'
        
        logger.info(f"连接URL: {mask_url(db_url)}")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"连接成功! PostgreSQL版本: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False

def test_with_param_connect():
    """测试使用参数方式连接"""
    logger.info("====== 测试使用参数方式连接 ======")
    try:
        # 解析URL
        parsed = urlparse(TEST_DB_URL)
        dbname = parsed.path.lstrip('/')
        
        # 准备连接参数
        conn_params = {
            'dbname': dbname,
            'user': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'sslmode': 'require'
        }
        
        logger.info(f"连接参数: {json.dumps({k: v if k != 'password' else '****' for k, v in conn_params.items()})}")
        
        # 使用连接参数连接
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"连接成功! PostgreSQL版本: {version[0]}")
        
        # 检索表信息
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = cursor.fetchall()
        logger.info(f"数据库中的表: {', '.join([t[0] for t in tables][:5])}...")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False

def test_with_env_vars():
    """测试使用环境变量方式连接"""
    logger.info("====== 测试使用环境变量方式连接 ======")
    
    # 保存原始环境变量
    old_ssl_mode = os.environ.get('PGSSLMODE')
    old_ssl_root_cert = os.environ.get('PGSSLROOTCERT')
    
    try:
        # 设置环境变量
        os.environ['PGSSLMODE'] = 'require'
        
        # 去除URL中的SSL参数
        parsed = urlparse(TEST_DB_URL)
        query_params = parse_qs(parsed.query)
        
        # 删除sslmode参数
        if 'sslmode' in query_params:
            del query_params['sslmode']
        
        # 重建URL
        from urllib.parse import urlencode, urlunparse
        parts = list(parsed)
        parts[4] = urlencode(query_params, doseq=True)
        clean_url = urlunparse(parts)
        
        logger.info(f"环境变量: PGSSLMODE=require")
        logger.info(f"连接URL: {mask_url(clean_url)}")
        
        conn = psycopg2.connect(clean_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"连接成功! PostgreSQL版本: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False
    finally:
        # 恢复环境变量
        if old_ssl_mode:
            os.environ['PGSSLMODE'] = old_ssl_mode
        elif 'PGSSLMODE' in os.environ:
            del os.environ['PGSSLMODE']
            
        if old_ssl_root_cert:
            os.environ['PGSSLROOTCERT'] = old_ssl_root_cert
        elif 'PGSSLROOTCERT' in os.environ:
            del os.environ['PGSSLROOTCERT']

def main():
    """运行所有测试"""
    logger.info("开始测试Render PostgreSQL数据库连接")
    
    # 存储测试结果
    results = {}
    
    # 测试直接连接
    results['direct_connect'] = test_direct_connect()
    
    # 测试添加sslmode参数
    results['with_sslmode'] = test_with_sslmode()
    
    # 测试使用参数方式连接
    results['with_param_connect'] = test_with_param_connect()
    
    # 测试使用环境变量方式连接
    results['with_env_vars'] = test_with_env_vars()
    
    # 显示测试结果摘要
    logger.info("====== 测试结果摘要 ======")
    for test_name, result in results.items():
        status = "成功" if result else "失败"
        logger.info(f"{test_name}: {status}")
    
    # 推荐使用的连接方式
    successful_methods = [k for k, v in results.items() if v]
    if successful_methods:
        logger.info(f"推荐使用的连接方式: {successful_methods[0]}")
        return 0
    else:
        logger.error("所有连接方式均失败，请检查数据库URL和网络连接")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL数据库连接测试脚本
尝试不同的SSL连接方式解决连接问题
"""

import os
import sys
import logging
import json
import psycopg2
from urllib.parse import urlparse, parse_qs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PostgreSQL连接测试')

# 测试的数据库URL - 已更新为正确的URL
TEST_DB_URL = os.environ.get('RENDER_DB_URL', 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d')

def mask_url(url):
    """隐藏敏感信息"""
    if '@' in url:
        parts = url.split('@')
        auth_part = parts[0]
        if ':' in auth_part:
            auth_parts = auth_part.split(':')
            if len(auth_parts) > 2:
                # 多个:的情况
                user = auth_parts[0]
                masked = f"{user}:{'*' * 10}"
                return f"{masked}@{parts[1]}"
            else:
                # 标准格式
                user = auth_parts[0]
                masked = f"{user}:{'*' * 10}"
                return f"{masked}@{parts[1]}"
    return url

def test_direct_connect():
    """测试直接连接"""
    logger.info("====== 测试直接连接 ======")
    try:
        logger.info(f"连接URL: {mask_url(TEST_DB_URL)}")
        conn = psycopg2.connect(TEST_DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"连接成功! PostgreSQL版本: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False

def test_with_sslmode():
    """测试添加sslmode参数"""
    logger.info("====== 测试添加sslmode=require ======")
    try:
        db_url = TEST_DB_URL
        if '?' not in db_url:
            db_url += '?sslmode=require'
        elif 'sslmode=' not in db_url:
            db_url += '&sslmode=require'
        
        logger.info(f"连接URL: {mask_url(db_url)}")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"连接成功! PostgreSQL版本: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False

def test_with_param_connect():
    """测试使用参数方式连接"""
    logger.info("====== 测试使用参数方式连接 ======")
    try:
        # 解析URL
        parsed = urlparse(TEST_DB_URL)
        dbname = parsed.path.lstrip('/')
        
        # 准备连接参数
        conn_params = {
            'dbname': dbname,
            'user': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'sslmode': 'require'
        }
        
        logger.info(f"连接参数: {json.dumps({k: v if k != 'password' else '****' for k, v in conn_params.items()})}")
        
        # 使用连接参数连接
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"连接成功! PostgreSQL版本: {version[0]}")
        
        # 检索表信息
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = cursor.fetchall()
        logger.info(f"数据库中的表: {', '.join([t[0] for t in tables][:5])}...")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False

def test_with_env_vars():
    """测试使用环境变量方式连接"""
    logger.info("====== 测试使用环境变量方式连接 ======")
    
    # 保存原始环境变量
    old_ssl_mode = os.environ.get('PGSSLMODE')
    old_ssl_root_cert = os.environ.get('PGSSLROOTCERT')
    
    try:
        # 设置环境变量
        os.environ['PGSSLMODE'] = 'require'
        
        # 去除URL中的SSL参数
        parsed = urlparse(TEST_DB_URL)
        query_params = parse_qs(parsed.query)
        
        # 删除sslmode参数
        if 'sslmode' in query_params:
            del query_params['sslmode']
        
        # 重建URL
        from urllib.parse import urlencode, urlunparse
        parts = list(parsed)
        parts[4] = urlencode(query_params, doseq=True)
        clean_url = urlunparse(parts)
        
        logger.info(f"环境变量: PGSSLMODE=require")
        logger.info(f"连接URL: {mask_url(clean_url)}")
        
        conn = psycopg2.connect(clean_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"连接成功! PostgreSQL版本: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False
    finally:
        # 恢复环境变量
        if old_ssl_mode:
            os.environ['PGSSLMODE'] = old_ssl_mode
        elif 'PGSSLMODE' in os.environ:
            del os.environ['PGSSLMODE']
            
        if old_ssl_root_cert:
            os.environ['PGSSLROOTCERT'] = old_ssl_root_cert
        elif 'PGSSLROOTCERT' in os.environ:
            del os.environ['PGSSLROOTCERT']

def main():
    """运行所有测试"""
    logger.info("开始测试Render PostgreSQL数据库连接")
    
    # 存储测试结果
    results = {}
    
    # 测试直接连接
    results['direct_connect'] = test_direct_connect()
    
    # 测试添加sslmode参数
    results['with_sslmode'] = test_with_sslmode()
    
    # 测试使用参数方式连接
    results['with_param_connect'] = test_with_param_connect()
    
    # 测试使用环境变量方式连接
    results['with_env_vars'] = test_with_env_vars()
    
    # 显示测试结果摘要
    logger.info("====== 测试结果摘要 ======")
    for test_name, result in results.items():
        status = "成功" if result else "失败"
        logger.info(f"{test_name}: {status}")
    
    # 推荐使用的连接方式
    successful_methods = [k for k, v in results.items() if v]
    if successful_methods:
        logger.info(f"推荐使用的连接方式: {successful_methods[0]}")
        return 0
    else:
        logger.error("所有连接方式均失败，请检查数据库URL和网络连接")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 