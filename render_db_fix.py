#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render环境数据库修复脚本

这个脚本专门用于在Render环境中修复数据库问题，特别是添加缺少的region列到companies表。
此脚本会:
1. 检查companies表是否存在region列
2. 如果不存在，添加该列
3. 迁移任何已有的province列数据到region列

用法：在Render环境的构建命令中添加：
python render_db_fix.py
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render数据库修复')

def fix_companies_table():
    """修复companies表的结构"""
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        return False
    
    # 建立数据库连接
    engine = create_engine(db_url)
    
    try:
        # 连接数据库
        with engine.connect() as conn:
            # 检查companies表是否存在
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'companies' not in tables:
                logger.error("companies表不存在，无法修复")
                return False
            
            # 检查表的列
            columns = [column['name'] for column in inspector.get_columns('companies')]
            logger.info(f"companies表当前列: {columns}")
            
            # 如果region列不存在，添加它
            if 'region' not in columns:
                logger.info("添加region列到companies表...")
                conn.execute(text("ALTER TABLE companies ADD COLUMN region VARCHAR(50)"))
                conn.commit()
                logger.info("成功添加region列")
                
                # 如果province列存在，将数据迁移到region列
                if 'province' in columns:
                    logger.info("将province数据迁移到region列...")
                    conn.execute(text("UPDATE companies SET region = province WHERE province IS NOT NULL"))
                    conn.commit()
                    logger.info("province数据迁移完成")
            else:
                logger.info("region列已存在，无需修复")
        
        logger.info("companies表修复成功")
        return True
    
    except Exception as e:
        logger.error(f"修复companies表时出错: {str(e)}")
        return False

if __name__ == "__main__":
    # 仅在Render环境中执行
    if os.environ.get('RENDER') == 'true':
        logger.info("在Render环境中执行数据库修复...")
        if fix_companies_table():
            logger.info("数据库修复成功")
            sys.exit(0)
        else:
            logger.error("数据库修复失败")
            sys.exit(1)
    else:
        logger.info("非Render环境，跳过修复")
        sys.exit(0) 