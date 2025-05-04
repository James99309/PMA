#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库修复脚本

该脚本专门用于解决Render环境中companies表缺少region列的问题。
会自动连接Render数据库并执行必要的SQL语句修复问题。

使用方法:
在Render环境中运行:
python render_db_fix.py
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_db_fix.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

def get_db_url():
    """获取数据库连接URL"""
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        return None
    
    # 如果是Render环境，数据库URL格式需要转换
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将数据库URL格式从postgres://转换为postgresql://")
    
    return db_url

def fix_database():
    """修复数据库中的问题"""
    # 获取数据库URL
    db_url = get_db_url()
    if not db_url:
        return False
    
    try:
        # 创建SQLAlchemy引擎
        logger.info("连接到数据库...")
        engine = create_engine(db_url)
        
        # 测试连接
        with engine.connect() as conn:
            logger.info("数据库连接成功")
            
            # 开始事务
            with conn.begin():
                # 执行修复SQL
                logger.info("开始执行数据库修复...")
                
                # 检查region列是否存在
                check_region_sql = text("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'companies' AND column_name = 'region'
                    ) as column_exists;
                """)
                
                region_exists = conn.execute(check_region_sql).scalar()
                
                if not region_exists:
                    logger.info("companies表中缺少region列，即将添加...")
                    add_col_sql = text("ALTER TABLE companies ADD COLUMN region VARCHAR(50);")
                    conn.execute(add_col_sql)
                    logger.info("成功添加region列")
                else:
                    logger.info("region列已存在，无需添加")
                
                # 检查province列是否存在
                check_province_sql = text("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'companies' AND column_name = 'province'
                    ) as column_exists;
                """)
                
                province_exists = conn.execute(check_province_sql).scalar()
                
                # 只有当province列存在时才迁移数据
                if province_exists:
                    logger.info("province列存在，将数据迁移到region列...")
                    update_sql = text("""
                        UPDATE companies 
                        SET region = province 
                        WHERE province IS NOT NULL AND region IS NULL;
                    """)
                    
                    update_result = conn.execute(update_sql)
                    logger.info(f"成功更新 {update_result.rowcount} 条记录")
                else:
                    logger.info("province列不存在，跳过数据迁移步骤")
                
                # 更新迁移版本
                logger.info("更新数据库迁移版本...")
                # 先检查alembic_version表是否存在
                check_alembic_sql = text("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_name = 'alembic_version'
                    ) as table_exists;
                """)
                
                alembic_exists = conn.execute(check_alembic_sql).scalar()
                
                if alembic_exists:
                    version_sql = text("""
                        UPDATE alembic_version 
                        SET version_num = 'add_missing_region_column' 
                        WHERE version_num <> 'add_missing_region_column';
                    """)
                    
                    conn.execute(version_sql)
                    logger.info("成功更新迁移版本")
                else:
                    logger.info("alembic_version表不存在，跳过版本更新")
                
                # 事务结束后会自动提交
            
            # 验证结果
            logger.info("验证修复结果...")
            total = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
            with_region = conn.execute(text("SELECT COUNT(*) FROM companies WHERE region IS NOT NULL")).scalar()
            null_region = conn.execute(text("SELECT COUNT(*) FROM companies WHERE region IS NULL")).scalar()
            
            logger.info(f"companies表共有 {total} 条记录")
            logger.info(f"region列有数据的记录: {with_region}")
            logger.info(f"region列为NULL的记录: {null_region}")
            
            logger.info("数据库修复完成!")
            return True
            
    except Exception as e:
        logger.error(f"修复数据库时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("===== 开始Render数据库修复 =====")
    
    # 检查是否在Render环境中
    is_render = os.environ.get('RENDER') == 'true'
    logger.info(f"当前环境: {'Render' if is_render else '本地'}")
    
    # 修复数据库
    success = fix_database()
    
    if success:
        logger.info("===== Render数据库修复成功 =====")
        return 0
    else:
        logger.error("===== Render数据库修复失败 =====")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
            logger.info(f"region列为NULL的记录: {null_region}")
            
            logger.info("数据库修复完成!")
            return True
            
    except Exception as e:
        logger.error(f"修复数据库时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("===== 开始Render数据库修复 =====")
    
    # 检查是否在Render环境中
    is_render = os.environ.get('RENDER') == 'true'
    logger.info(f"当前环境: {'Render' if is_render else '本地'}")
    
    # 修复数据库
    success = fix_database()
    
    if success:
        logger.info("===== Render数据库修复成功 =====")
        return 0
    else:
        logger.error("===== Render数据库修复失败 =====")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 