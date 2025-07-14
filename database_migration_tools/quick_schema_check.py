#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查云端数据库缺失字段
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('快速检查')

def quick_check():
    local_db_url = "postgresql://nijie@localhost:5432/pma_local"
    cloud_db_url = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"
    
    def parse_db_url(db_url):
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }
    
    logger.info("🔍 快速检查关键字段...")
    
    # 检查本地数据库
    local_params = parse_db_url(local_db_url)
    local_conn = psycopg2.connect(**local_params)
    local_cursor = local_conn.cursor()
    
    # 检查云端数据库
    cloud_params = parse_db_url(cloud_db_url)
    cloud_conn = psycopg2.connect(**cloud_params)
    cloud_cursor = cloud_conn.cursor()
    
    # 检查users表的account_id字段
    logger.info("📋 检查users.account_id字段...")
    
    local_cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'users' 
        AND column_name = 'account_id'
    """)
    local_account_id = local_cursor.fetchone()
    
    cloud_cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'users' 
        AND column_name = 'account_id'
    """)
    cloud_account_id = cloud_cursor.fetchone()
    
    if local_account_id:
        logger.info(f"✅ 本地users.account_id存在: {local_account_id}")
    else:
        logger.warning("⚠️ 本地users.account_id不存在")
    
    if cloud_account_id:
        logger.info(f"✅ 云端users.account_id存在: {cloud_account_id}")
    else:
        logger.error("❌ 云端users.account_id缺失!")
    
    # 检查role_permissions表的user_id字段
    logger.info("📋 检查role_permissions.user_id字段...")
    
    local_cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'role_permissions' 
        AND column_name = 'user_id'
    """)
    local_user_id = local_cursor.fetchone()
    
    cloud_cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'role_permissions' 
        AND column_name = 'user_id'
    """)
    cloud_user_id = cloud_cursor.fetchone()
    
    if local_user_id:
        logger.info(f"✅ 本地role_permissions.user_id存在: {local_user_id}")
    else:
        logger.warning("⚠️ 本地role_permissions.user_id不存在")
    
    if cloud_user_id:
        logger.info(f"✅ 云端role_permissions.user_id存在: {cloud_user_id}")
    else:
        logger.error("❌ 云端role_permissions.user_id缺失!")
    
    # 检查role_permissions表结构对比
    logger.info("📋 对比role_permissions表结构...")
    
    local_cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'role_permissions'
        ORDER BY ordinal_position
    """)
    local_rp_columns = local_cursor.fetchall()
    
    cloud_cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'role_permissions'
        ORDER BY ordinal_position
    """)
    cloud_rp_columns = cloud_cursor.fetchall()
    
    logger.info("本地role_permissions字段:")
    for col in local_rp_columns:
        logger.info(f"  - {col[0]}: {col[1]} ({'可空' if col[2] == 'YES' else '不可空'})")
    
    logger.info("云端role_permissions字段:")
    for col in cloud_rp_columns:
        logger.info(f"  - {col[0]}: {col[1]} ({'可空' if col[2] == 'YES' else '不可空'})")
    
    local_conn.close()
    cloud_conn.close()
    
    logger.info("🎯 总结:")
    logger.info("主要问题:")
    if not cloud_account_id:
        logger.error("1. ❌ 云端users表缺失account_id字段")
    if not cloud_user_id:
        logger.error("2. ❌ 云端role_permissions表缺失user_id字段")
    
    logger.info("这些缺失字段很可能是导致非admin用户500错误的根本原因")

if __name__ == "__main__":
    quick_check()