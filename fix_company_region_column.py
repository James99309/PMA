#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复companies表缺少region列的问题

这个脚本会:
1. 检查companies表是否缺少region列
2. 如果缺少，添加该列
3. 同时兼容SQLite和PostgreSQL数据库

用法:
python fix_company_region_column.py
"""

import os
import sys
from flask import Flask
from sqlalchemy import inspect, text
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('修复companies表')

# 创建Flask应用实例
app = Flask(__name__)
app.config.from_object('config')

# 检查是否处于Render环境
is_render = os.environ.get('RENDER') == 'true'
if is_render:
    logger.info("检测到Render环境，使用PostgreSQL数据库")
    # 确保Render环境变量已设置
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量，无法连接数据库")
        sys.exit(1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    logger.info("本地环境，使用配置文件中的数据库设置")

# 初始化数据库
from app import db

def fix_companies_table():
    """检查并修复companies表的region列"""
    try:
        # 获取数据库连接
        conn = db.engine.connect()
        
        # 检查数据库类型
        is_postgres = 'postgresql' in db.engine.url.drivername
        is_sqlite = 'sqlite' in db.engine.url.drivername
        
        # 获取表的当前列结构
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('companies')]
        
        logger.info(f"当前companies表列: {columns}")
        
        # 检查region列是否存在
        if 'region' not in columns:
            logger.info("未找到region列，准备添加...")
            
            # 根据数据库类型选择不同的SQL
            if is_postgres:
                # PostgreSQL的添加列SQL
                alter_sql = "ALTER TABLE companies ADD COLUMN region VARCHAR(50)"
                conn.execute(text(alter_sql))
                logger.info("已在PostgreSQL中添加region列")
                
                # 检查province列是否存在（可能的旧列名）
                if 'province' in columns:
                    # 将province数据迁移到region
                    update_sql = "UPDATE companies SET region = province WHERE province IS NOT NULL"
                    conn.execute(text(update_sql))
                    logger.info("已将province列数据迁移到region列")
            
            elif is_sqlite:
                # SQLite的添加列SQL
                alter_sql = "ALTER TABLE companies ADD COLUMN region VARCHAR(50)"
                conn.execute(text(alter_sql))
                logger.info("已在SQLite中添加region列")
                
                # 检查province列是否存在
                if 'province' in columns:
                    # 将province数据迁移到region
                    update_sql = "UPDATE companies SET region = province WHERE province IS NOT NULL"
                    conn.execute(text(update_sql))
                    logger.info("已将province列数据迁移到region列")
            
            else:
                logger.warning(f"未知数据库类型: {db.engine.url.drivername}，无法自动修复")
                return False
            
            # 提交事务
            db.session.commit()
            logger.info("修复完成，companies表现在有region列")
            return True
        else:
            logger.info("companies表已有region列，无需修复")
            return True
    
    except Exception as e:
        logger.error(f"修复过程中出错: {str(e)}")
        # 回滚任何未完成的事务
        db.session.rollback()
        return False

if __name__ == "__main__":
    with app.app_context():
        success = fix_companies_table()
        if success:
            logger.info("修复脚本执行成功")
            sys.exit(0)
        else:
            logger.error("修复脚本执行失败")
            sys.exit(1) 