#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render环境数据库模式修复工具

用于解决Render环境中的数据库模式不一致问题，特别是:
1. 检查并添加缺少的列
2. 执行必要的数据迁移

用法:
python fix_render_schema.py
"""

import os
import sys
import logging
import sqlalchemy as sa
from flask import Flask
from sqlalchemy import text, inspect

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render数据库修复')

# 创建应用实例
app = Flask(__name__)

# 配置数据库
if os.environ.get('RENDER') == 'true':
    # Render环境
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量")
        sys.exit(1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    logger.info("使用Render环境数据库配置")
else:
    # 本地环境
    app.config.from_object('config')
    logger.info("使用本地环境数据库配置")

# 初始化数据库
from app import db

def fix_companies_table():
    """修复companies表的结构问题"""
    try:
        conn = db.engine.connect()
        inspector = inspect(db.engine)
        
        # 检查companies表是否存在
        has_table = 'companies' in inspector.get_table_names()
        if not has_table:
            logger.warning("companies表不存在，无法修复")
            return False
        
        # 获取表的列
        columns = [column['name'] for column in inspector.get_columns('companies')]
        logger.info(f"当前companies表列: {columns}")
        
        # 1. 修复region列缺失问题
        if 'region' not in columns:
            logger.info("未找到region列，正在添加...")
            conn.execute(text("ALTER TABLE companies ADD COLUMN region VARCHAR(50)"))
            
            # 检查province列是否存在（旧列名）
            if 'province' in columns:
                logger.info("正在将province数据迁移到region...")
                conn.execute(text("UPDATE companies SET region = province WHERE province IS NOT NULL"))
            
            logger.info("region列修复完成")
        else:
            logger.info("region列已存在，无需修复")
        
        # 提交修改
        db.session.commit()
        return True
        
    except Exception as e:
        logger.error(f"修复companies表时出错: {str(e)}")
        db.session.rollback()
        return False

def execute_migrations():
    """执行所有必要的数据库迁移"""
    from flask_migrate import upgrade
    
    try:
        # 执行数据库迁移
        logger.info("正在执行数据库迁移...")
        with app.app_context():
            upgrade()
        logger.info("数据库迁移完成")
        return True
    except Exception as e:
        logger.error(f"执行数据库迁移时出错: {str(e)}")
        return False

def main():
    """主函数，执行所有修复步骤"""
    with app.app_context():
        success = True
        
        # 1. 修复companies表
        logger.info("开始修复companies表...")
        if not fix_companies_table():
            success = False
            logger.error("修复companies表失败")
        
        # 2. 执行所有迁移
        logger.info("开始执行数据库迁移...")
        if not execute_migrations():
            success = False
            logger.error("执行数据库迁移失败")
        
        if success:
            logger.info("所有修复步骤成功完成")
        else:
            logger.warning("部分修复步骤失败，请检查日志")
        
        return success

if __name__ == "__main__":
    try:
        if main():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        logger.critical(f"执行修复脚本时发生未处理的异常: {str(e)}")
        sys.exit(1) 