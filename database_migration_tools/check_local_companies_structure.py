#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查本地companies表结构
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('表结构检查')

def check_local_tables():
    local_db_url = "postgresql://nijie@localhost:5432/pma_local"
    
    def parse_db_url(db_url):
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }
    
    params = parse_db_url(local_db_url)
    conn = psycopg2.connect(**params)
    cursor = conn.cursor()
    
    # 检查companies表结构
    logger.info("🔍 检查companies表结构...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'companies'
        ORDER BY ordinal_position
    """)
    
    companies_columns = cursor.fetchall()
    if companies_columns:
        logger.info("📋 companies表字段:")
        for col in companies_columns:
            nullable = "可空" if col[2] == 'YES' else "不可空"
            logger.info(f"  - {col[0]}: {col[1]} ({nullable})")
    else:
        logger.warning("⚠️ companies表不存在或无字段")
    
    # 检查所有包含company的表
    logger.info("\n🔍 检查包含company的表...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%company%'
        OR table_name LIKE '%customer%'
        ORDER BY table_name
    """)
    
    related_tables = cursor.fetchall()
    logger.info("📋 相关表:")
    for table in related_tables:
        logger.info(f"  - {table[0]}")
    
    # 检查projects表的公司关联字段
    logger.info("\n🔍 检查projects表结构...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'projects'
        AND column_name LIKE '%company%'
        ORDER BY ordinal_position
    """)
    
    project_company_columns = cursor.fetchall()
    if project_company_columns:
        logger.info("📋 projects表中的公司相关字段:")
        for col in project_company_columns:
            nullable = "可空" if col[2] == 'YES' else "不可空"
            logger.info(f"  - {col[0]}: {col[1]} ({nullable})")
    else:
        logger.info("📋 projects表中没有公司相关字段")
    
    # 检查quotations表的公司关联字段
    logger.info("\n🔍 检查quotations表结构...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'quotations'
        AND (column_name LIKE '%company%' OR column_name LIKE '%customer%')
        ORDER BY ordinal_position
    """)
    
    quotation_company_columns = cursor.fetchall()
    if quotation_company_columns:
        logger.info("📋 quotations表中的公司相关字段:")
        for col in quotation_company_columns:
            nullable = "可空" if col[2] == 'YES' else "不可空"
            logger.info(f"  - {col[0]}: {col[1]} ({nullable})")
    else:
        logger.info("📋 quotations表中没有公司相关字段")
    
    conn.close()

if __name__ == "__main__":
    check_local_tables()