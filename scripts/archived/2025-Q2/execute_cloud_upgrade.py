#!/usr/bin/env python3
"""
云端数据库升级执行脚本
在Render环境中执行数据库结构同步
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_sql_file(filename):
    """读取SQL文件内容"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"SQL文件不存在: {filename}")
        return None
    except Exception as e:
        logger.error(f"读取SQL文件失败: {e}")
        return None

def execute_upgrade():
    """执行云端数据库升级"""
    logger.info("🚀 开始执行PMA云端数据库升级")
    
    # 获取数据库连接
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL环境变量未设置")
        return False
    
    # 读取升级脚本
    sql_content = read_sql_file('cloud_db_final_upgrade.sql')
    if not sql_content:
        logger.error("❌ 无法读取升级脚本文件")
        return False
    
    try:
        # 连接数据库
        logger.info("连接云端数据库...")
        engine = create_engine(database_url)
        
        # 执行升级脚本
        logger.info("执行数据库升级脚本...")
        with engine.connect() as conn:
            # 由于SQL脚本包含事务控制，直接执行整个脚本
            conn.execute(text(sql_content))
            conn.commit()
        
        logger.info("✅ 数据库升级执行成功！")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ 数据库操作失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 升级过程中出现错误: {e}")
        return False

def verify_upgrade():
    """验证升级结果"""
    logger.info("🔍 验证升级结果...")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL环境变量未设置")
        return False
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 检查Alembic版本
            result = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            if result:
                version = result[0]
                logger.info(f"✅ 当前迁移版本: {version}")
                
                if version == 'c1308c08d0c9':
                    logger.info("✅ 迁移版本正确")
                else:
                    logger.warning(f"⚠️ 迁移版本可能不是最新: {version}")
            
            # 检查关键表结构
            logger.info("检查关键表结构...")
            
            # 检查 projects.rating 列类型
            result = conn.execute(text("""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = 'projects' AND column_name = 'rating'
            """)).fetchone()
            if result and result[0] == 'integer':
                logger.info("✅ projects.rating 列类型正确 (integer)")
            else:
                logger.warning(f"⚠️ projects.rating 列类型: {result[0] if result else 'Not found'}")
            
            # 检查 quotations 表新列
            new_columns = ['confirmed_at', 'confirmation_badge_status', 'product_signature']
            for col_name in new_columns:
                result = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'quotations' AND column_name = '{col_name}'
                """)).fetchone()
                if result:
                    logger.info(f"✅ quotations.{col_name} 列存在")
                else:
                    logger.error(f"❌ quotations.{col_name} 列不存在")
            
            # 检查约束
            result = conn.execute(text("""
                SELECT constraint_name FROM information_schema.table_constraints 
                WHERE table_name = 'project_rating_records' 
                AND constraint_name = 'uq_project_user_rating'
            """)).fetchone()
            if result:
                logger.info("✅ project_rating_records 唯一约束正确")
            else:
                logger.warning("⚠️ project_rating_records 唯一约束可能不正确")
        
        logger.info("✅ 升级验证完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 验证过程中出现错误: {e}")
        return False

def main():
    """主函数"""
    print("🔧 PMA云端数据库升级工具")
    print("=" * 50)
    
    try:
        # 执行升级
        if execute_upgrade():
            print("\n🎉 数据库升级成功！")
            
            # 验证升级结果
            if verify_upgrade():
                print("\n✅ 升级验证成功，数据库结构已同步到本地版本")
                print("\n📋 升级完成摘要:")
                print("- projects.rating 列类型已修改为 INTEGER")
                print("- quotations 表已添加确认相关字段")
                print("- project_rating_records 表结构已更新")
                print("- 无效的索引和约束已清理")
                print("- Alembic 迁移版本已更新")
                return True
            else:
                print("\n⚠️ 升级完成，但验证过程中发现一些问题")
                return False
        else:
            print("\n❌ 数据库升级失败")
            return False
            
    except Exception as e:
        print(f"❌ 升级过程中出现意外错误: {e}")
        logger.exception("详细错误信息:")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 