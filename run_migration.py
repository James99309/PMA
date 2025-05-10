#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移脚本执行器
用于执行特定的数据库迁移脚本，添加account_id字段到project_stage_history表
"""

import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入迁移脚本
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrations.versions.add_account_id_to_project_stage_history import upgrade

def run_migration():
    """执行迁移脚本"""
    try:
        # 创建一个简单的Flask应用
        app = Flask(__name__)
        
        # 从环境变量或配置文件获取数据库连接信息
        from config import Config
        app.config.from_object(Config)
        
        # 打印配置信息
        logger.info(f"数据库配置: {app.config.get('SQLALCHEMY_DATABASE_URI', '未配置')}")
        
        # 初始化数据库
        db = SQLAlchemy(app)
        
        # 使用应用上下文
        with app.app_context():
            # 测试数据库连接
            try:
                db.session.execute(text('SELECT 1'))
                logger.info("数据库连接成功")
            except Exception as e:
                logger.error(f"数据库连接失败: {str(e)}")
                return False
            
            # 执行迁移
            logger.info("开始执行数据库迁移...")
            upgrade()
            logger.info("数据库迁移执行完成")
            
            # 验证迁移结果
            try:
                # 检查是否已添加account_id字段
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='project_stage_history' AND column_name='account_id'
                """)).fetchone()
                
                if result:
                    logger.info("迁移验证成功: account_id字段已添加到project_stage_history表")
                    return True
                else:
                    logger.error("迁移验证失败: account_id字段未添加")
                    return False
            except Exception as e:
                logger.error(f"迁移验证出错: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"执行迁移脚本时出错: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    if success:
        logger.info("迁移脚本执行成功")
        sys.exit(0)
    else:
        logger.error("迁移脚本执行失败")
        sys.exit(1) 