#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加报价审核字段迁移脚本
为quotations表添加approval_status、approved_stages和approval_history字段
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text, Column, String, JSON
from sqlalchemy.exc import SQLAlchemyError
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(table_name, column_name):
    """检查表中是否存在指定列"""
    try:
        result = db.session.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            AND column_name = '{column_name}'
        """))
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"检查列存在性失败: {e}")
        return False

def add_quotation_approval_fields():
    """为quotations表添加审核相关字段"""
    try:
        logger.info("开始添加报价审核字段...")
        
        # 检查并添加approval_status字段
        if not check_column_exists('quotations', 'approval_status'):
            logger.info("添加approval_status字段...")
            db.session.execute(text("""
                ALTER TABLE quotations 
                ADD COLUMN approval_status VARCHAR(50) DEFAULT 'pending'
            """))
            logger.info("approval_status字段添加成功")
        else:
            logger.info("approval_status字段已存在，跳过")
        
        # 检查并添加approved_stages字段
        if not check_column_exists('quotations', 'approved_stages'):
            logger.info("添加approved_stages字段...")
            # PostgreSQL使用JSON类型
            db.session.execute(text("""
                ALTER TABLE quotations 
                ADD COLUMN approved_stages JSON DEFAULT '[]'::json
            """))
            logger.info("approved_stages字段添加成功")
        else:
            logger.info("approved_stages字段已存在，跳过")
        
        # 检查并添加approval_history字段
        if not check_column_exists('quotations', 'approval_history'):
            logger.info("添加approval_history字段...")
            # PostgreSQL使用JSON类型
            db.session.execute(text("""
                ALTER TABLE quotations 
                ADD COLUMN approval_history JSON DEFAULT '[]'::json
            """))
            logger.info("approval_history字段添加成功")
        else:
            logger.info("approval_history字段已存在，跳过")
        
        # 提交更改
        db.session.commit()
        logger.info("报价审核字段添加完成！")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加报价审核字段失败: {e}")
        return False

def rollback_quotation_approval_fields():
    """回滚报价审核字段"""
    try:
        logger.info("开始回滚报价审核字段...")
        
        # 删除approval_history字段
        if check_column_exists('quotations', 'approval_history'):
            logger.info("删除approval_history字段...")
            db.session.execute(text("ALTER TABLE quotations DROP COLUMN approval_history"))
            logger.info("approval_history字段删除成功")
        
        # 删除approved_stages字段
        if check_column_exists('quotations', 'approved_stages'):
            logger.info("删除approved_stages字段...")
            db.session.execute(text("ALTER TABLE quotations DROP COLUMN approved_stages"))
            logger.info("approved_stages字段删除成功")
        
        # 删除approval_status字段
        if check_column_exists('quotations', 'approval_status'):
            logger.info("删除approval_status字段...")
            db.session.execute(text("ALTER TABLE quotations DROP COLUMN approval_status"))
            logger.info("approval_status字段删除成功")
        
        # 提交更改
        db.session.commit()
        logger.info("报价审核字段回滚完成！")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"回滚报价审核字段失败: {e}")
        return False

def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        try:
            # 测试数据库连接
            db.session.execute(text("SELECT 1"))
            logger.info("数据库连接成功")
            
            # 获取命令行参数
            if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
                # 执行回滚
                success = rollback_quotation_approval_fields()
            else:
                # 执行迁移
                success = add_quotation_approval_fields()
            
            if success:
                logger.info("迁移操作完成")
            else:
                logger.error("迁移操作失败")
                sys.exit(1)
                
        except SQLAlchemyError as e:
            logger.error(f"数据库操作失败: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"未知错误: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main() 