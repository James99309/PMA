#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库连接诊断和修复工具
用于检查和测试Render环境中的数据库连接
"""

import os
import sys
import socket
import logging
import argparse
import subprocess
import requests
import traceback
import json
from urllib.parse import urlparse
from sqlalchemy import create_engine, text

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_db_check.log')
    ]
)
logger = logging.getLogger('DB诊断')

def fix_database_url(database_url):
    """修正数据库URL格式"""
    if not database_url:
        logger.error("未提供数据库URL")
        return None
        
    logger.info("处理数据库URL...")
    
    # 隐藏敏感信息用于日志
    parsed = urlparse(database_url)
    masked_url = database_url
    if parsed.password:
        masked_url = database_url.replace(parsed.password, '********')
    logger.info(f"数据库URL格式: {masked_url}")
    
    if database_url.startswith('postgres://'):
        fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将postgres://转换为postgresql://")
        database_url = fixed_url
    
    # 添加SSL参数
    if '?' not in database_url:
        database_url += '?sslmode=require'
        logger.info("已添加SSL参数: sslmode=require")
    elif 'sslmode=' not in database_url:
        database_url += '&sslmode=require'
        logger.info("已添加SSL参数: sslmode=require")
    else:
        logger.info("URL已包含SSL参数")
        
    return database_url

def test_dns_resolution(hostname):
    """测试DNS解析"""
    try:
        logger.info(f"解析主机名: {hostname}")
        ip_address = socket.gethostbyname(hostname)
        logger.info(f"解析成功: {hostname} -> {ip_address}")
        return True, ip_address
    except socket.gaierror as e:
        logger.error(f"DNS解析失败: {str(e)}")
        return False, None

def ping_host(hostname):
    """Ping主机"""
    try:
        logger.info(f"Ping主机: {hostname}")
        result = subprocess.run(['ping', '-c', '3', hostname], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        if result.returncode == 0:
            logger.info(f"Ping成功: {hostname}")
            return True
        else:
            logger.error(f"Ping失败: {hostname}")
            logger.debug(result.stdout)
            return False
    except Exception as e:
        logger.error(f"Ping异常: {str(e)}")
        return False

def test_database_connection(database_url):
    """测试数据库连接"""
    try:
        logger.info("测试数据库连接...")
        engine = create_engine(
            database_url,
            connect_args={
                'connect_timeout': 30,
                'application_name': 'PMA诊断工具',
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            }
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"数据库连接成功: {version}")
            
            # 测试查询表结构
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = [row[0] for row in result]
            logger.info(f"数据库表数量: {len(tables)}")
            if tables:
                logger.info(f"表示例: {', '.join(tables[:5])}")
                
        return True, version, tables
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        traceback.print_exc()
        return False, None, None

def check_database_schema(engine, required_tables=None):
    """检查数据库模式"""
    if required_tables is None:
        required_tables = ['users', 'permissions', 'departments']
        
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = [row[0] for row in result]
            
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                logger.warning(f"缺少必要的表: {', '.join(missing_tables)}")
                return False
            else:
                logger.info("数据库模式验证通过")
                return True
    except Exception as e:
        logger.error(f"检查数据库模式失败: {str(e)}")
        return False

def check_render_services():
    """检查Render服务"""
    logger.info("检查Render环境变量...")
    render_api_key = os.environ.get('RENDER_API_KEY')
    if not render_api_key:
        logger.warning("未找到RENDER_API_KEY环境变量")
        return

    service_id = os.environ.get('RENDER_SERVICE_ID')
    if not service_id:
        logger.warning("未找到RENDER_SERVICE_ID环境变量")
        return
        
    try:
        headers = {
            'Authorization': f'Bearer {render_api_key}',
            'Content-Type': 'application/json'
        }
        
        # 获取服务信息
        response = requests.get(
            f'https://api.render.com/v1/services/{service_id}',
            headers=headers
        )
        
        if response.status_code == 200:
            service_info = response.json()
            logger.info(f"服务名称: {service_info.get('name')}")
            logger.info(f"服务类型: {service_info.get('type')}")
            logger.info(f"服务状态: {service_info.get('status')}")
        else:
            logger.error(f"获取服务信息失败: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"查询Render API失败: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Render数据库连接诊断工具')
    parser.add_argument('--db-url', help='数据库URL，如果不提供将使用环境变量DATABASE_URL')
    parser.add_argument('--check-render', action='store_true', help='检查Render服务')
    args = parser.parse_args()
    
    logger.info("=== 开始数据库连接诊断 ===")
    
    # 获取数据库URL
    database_url = args.db_url or os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到数据库URL，请提供--db-url参数或设置DATABASE_URL环境变量")
        return 1
    
    # 修正数据库URL格式
    database_url = fix_database_url(database_url)
    
    # 解析URL
    parsed_url = urlparse(database_url)
    hostname = parsed_url.hostname
    
    if not hostname:
        logger.error(f"无法从数据库URL中提取主机名")
        return 1
    
    # 测试DNS解析
    dns_success, ip_address = test_dns_resolution(hostname)
    
    # 测试Ping
    if dns_success:
        ping_success = ping_host(hostname)
    
    # 测试数据库连接
    db_success, version, tables = test_database_connection(database_url)
    
    # 检查Render服务
    if args.check_render:
        check_render_services()
    
    # 输出总结
    logger.info("\n=== 诊断总结 ===")
    logger.info(f"DNS解析: {'成功' if dns_success else '失败'}")
    if dns_success:
        logger.info(f"Ping测试: {'成功' if ping_success else '失败'}")
    logger.info(f"数据库连接: {'成功' if db_success else '失败'}")
    
    if db_success:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 