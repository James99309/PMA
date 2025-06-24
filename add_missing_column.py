#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动添加缺失字段
"""

import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('添加字段')

def add_industry_column():
    """添加projects.industry字段"""
    cloud_db_url = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(cloud_db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path.lstrip('/')
        )
        
        cursor = conn.cursor()
        
        # 检查字段是否存在
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'projects' AND column_name = 'industry'
        """)
        
        if cursor.fetchone():
            logger.info("✅ industry字段已存在")
        else:
            logger.info("添加industry字段到projects表...")
            cursor.execute("ALTER TABLE projects ADD COLUMN industry VARCHAR(100);")
            conn.commit()
            logger.info("✅ industry字段添加成功")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ 添加字段失败: {e}")
        return False

if __name__ == "__main__":
    add_industry_column()
