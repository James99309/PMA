#!/usr/bin/env python3
"""
修复 ApprovalRecord 表中 step_id 字段的 NOT NULL 约束
支持模板快照情况下的 NULL 值

Created: 2025-06-27
Author: Assistant
Purpose: 修复审批记录中的step_id类型错误，支持模板快照
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from flask import Flask
from app import create_app, db
from app.models.approval import ApprovalRecord
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_approval_record_step_id():
    """修改 approval_record 表的 step_id 字段，允许 NULL 值"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # 获取数据库连接
            connection = db.engine.connect()
            trans = connection.begin()
            
            logger.info("开始修改 approval_record 表的 step_id 字段...")
            
            # 检查当前数据库类型
            db_type = db.engine.dialect.name
            logger.info(f"数据库类型: {db_type}")
            
            if db_type == 'postgresql':
                # PostgreSQL 语法
                alter_sql = """
                ALTER TABLE approval_record 
                ALTER COLUMN step_id DROP NOT NULL;
                """
            elif db_type == 'sqlite':
                # SQLite 不支持直接修改列约束，需要重建表
                logger.warning("SQLite 数据库不支持直接修改列约束，跳过此修改")
                logger.warning("请在生产环境的 PostgreSQL 数据库中运行此修改")
                trans.rollback()
                connection.close()
                return True
            else:
                # MySQL 语法
                alter_sql = """
                ALTER TABLE approval_record 
                MODIFY COLUMN step_id INTEGER NULL;
                """
            
            # 执行 SQL
            if db_type != 'sqlite':
                from sqlalchemy import text
                connection.execute(text(alter_sql))
                logger.info("成功修改 step_id 字段约束")
            
                # 验证修改结果
                result = connection.execute(text("""
                    SELECT column_name, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'approval_record' 
                    AND column_name = 'step_id';
                """))
                
                for row in result:
                    logger.info(f"验证结果 - 字段: {row[0]}, 可为空: {row[1]}")
            
            trans.commit()
            connection.close()
            
            logger.info("数据库修改完成！")
            return True
            
        except Exception as e:
            logger.error(f"修改数据库时发生错误: {str(e)}")
            try:
                trans.rollback()
                connection.close()
            except:
                pass
            return False

def check_current_schema():
    """检查当前数据库中的表结构"""
    
    app = create_app()
    
    with app.app_context():
        try:
            connection = db.engine.connect()
            
            logger.info("检查当前 approval_record 表结构...")
            
            # 检查表是否存在
            from sqlalchemy import text
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'approval_record'
                );
            """))
            
            table_exists = result.fetchone()[0]
            logger.info(f"approval_record 表存在: {table_exists}")
            
            if table_exists:
                # 检查字段信息
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'approval_record'
                    ORDER BY ordinal_position;
                """))
                
                logger.info("当前表结构:")
                for row in result:
                    logger.info(f"  {row[0]}: {row[1]}, 可为空: {row[2]}, 默认值: {row[3]}")
            
            connection.close()
            
        except Exception as e:
            logger.error(f"检查数据库结构时发生错误: {str(e)}")
            if 'connection' in locals():
                connection.close()

def main():
    """主函数"""
    print("=== ApprovalRecord step_id 字段修复工具 ===")
    print()
    
    # 检查当前结构
    check_current_schema()
    print()
    
    # 询问是否继续
    response = input("是否继续修改 step_id 字段约束？(y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("操作已取消")
        return
    
    # 执行修改
    success = fix_approval_record_step_id()
    
    if success:
        print("\n✅ step_id 字段修复完成！")
        print("现在可以处理模板快照的审批记录了。")
    else:
        print("\n❌ step_id 字段修复失败！")
        print("请检查日志并手动修复。")

if __name__ == '__main__':
    main() 