#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render环境数据库修复脚本

该脚本专门针对Render环境的PostgreSQL数据库，用于解决region列缺失问题。

执行步骤:
1. 检查companies表是否存在region列
2. 如果不存在，添加该列
3. 迁移province列的数据到region列
4. 记录详细日志

用法:
在Render环境中运行:
python fix_render_db.py
"""

import os
import sys
import logging
import traceback
from sqlalchemy import create_engine, inspect, text, Table, MetaData, Column, String, Boolean

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_render_db.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

def get_db_url():
    """
    获取数据库连接URL
    
    Returns:
        str: 数据库连接URL
    """
    # 获取环境变量中的数据库URL
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        return None
    
    # 如果是Render环境，数据库URL格式需要转换
    # Render使用postgres://，SQLAlchemy需要postgresql://
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将数据库URL格式从postgres://转换为postgresql://")
    
    return db_url

def check_and_fix_companies_table(engine):
    """
    检查并修复companies表
    
    Args:
        engine: SQLAlchemy引擎
        
    Returns:
        bool: 是否成功修复
    """
    try:
        # 获取数据库检查器
        inspector = inspect(engine)
        
        # 检查companies表是否存在
        tables = inspector.get_table_names()
        if 'companies' not in tables:
            logger.error("companies表不存在，无法修复")
            return False
        
        # 获取companies表的列
        columns = [column['name'] for column in inspector.get_columns('companies')]
        logger.info(f"companies表现有列: {', '.join(columns)}")
        
        # 检查region列是否存在
        if 'region' in columns:
            logger.info("region列已存在，无需添加")
            
            # 检查region列是否有数据
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM companies WHERE region IS NOT NULL")).scalar()
                logger.info(f"region列有 {result} 条非空数据")
                
                # 如果region列没有数据但province列存在，尝试迁移数据
                if result == 0 and 'province' in columns:
                    logger.info("region列为空，尝试从province列迁移数据")
                    conn.execute(text("UPDATE companies SET region = province WHERE province IS NOT NULL"))
                    conn.commit()
                    
                    # 验证迁移结果
                    migrated = conn.execute(text("SELECT COUNT(*) FROM companies WHERE region IS NOT NULL")).scalar()
                    logger.info(f"成功迁移 {migrated} 条数据从province到region")
            
            return True
        
        # 如果region列不存在，添加它
        logger.info("region列不存在，开始添加...")
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                # 添加region列
                conn.execute(text("ALTER TABLE companies ADD COLUMN region VARCHAR(50)"))
                
                # 如果存在province列，复制数据
                if 'province' in columns:
                    logger.info("从province列复制数据到region列...")
                    conn.execute(text("UPDATE companies SET region = province WHERE province IS NOT NULL"))
                
                trans.commit()
                logger.info("成功添加region列并迁移数据")
                return True
            except Exception as e:
                trans.rollback()
                logger.error(f"添加region列失败: {str(e)}")
                logger.error(traceback.format_exc())
                return False
                
    except Exception as e:
        logger.error(f"检查companies表时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def check_all_tables(engine):
    """
    检查所有表结构，输出摘要信息
    
    Args:
        engine: SQLAlchemy引擎
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"数据库中共有 {len(tables)} 个表")
        
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            logger.info(f"表 {table_name}: {len(columns)} 列")
            
            for column in columns:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                logger.debug(f"  - {column['name']} ({column['type']}) {nullable}")
    
    except Exception as e:
        logger.error(f"检查所有表时出错: {str(e)}")

def fix_migrations_table(engine):
    """
    修复alembic_version表，确保包含最新的迁移版本
    
    Args:
        engine: SQLAlchemy引擎
        
    Returns:
        bool: 是否成功修复
    """
    try:
        inspector = inspect(engine)
        
        # 检查alembic_version表是否存在
        if 'alembic_version' not in inspector.get_table_names():
            logger.warning("alembic_version表不存在，无法修复迁移状态")
            return False
        
        # 设置最新的迁移版本
        latest_version = 'add_missing_region_column'
        
        # 检查并更新迁移版本
        with engine.connect() as conn:
            # 获取当前版本
            current_version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            logger.info(f"当前迁移版本: {current_version}")
            
            if current_version != latest_version:
                # 更新到最新版本
                trans = conn.begin()
                try:
                    conn.execute(text(f"UPDATE alembic_version SET version_num = '{latest_version}'"))
                    trans.commit()
                    logger.info(f"成功更新迁移版本到 {latest_version}")
                    return True
                except Exception as e:
                    trans.rollback()
                    logger.error(f"更新迁移版本失败: {str(e)}")
                    return False
            else:
                logger.info("迁移版本已是最新")
                return True
    
    except Exception as e:
        logger.error(f"修复迁移表时出错: {str(e)}")
        return False

def verify_region_column(engine):
    """
    验证region列的数据是否正确
    
    Args:
        engine: SQLAlchemy引擎
        
    Returns:
        bool: 验证是否通过
    """
    try:
        with engine.connect() as conn:
            # 获取companies表中的总记录数
            total_rows = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
            logger.info(f"companies表共有 {total_rows} 条记录")
            
            # 获取region列为NULL的记录数
            null_region = conn.execute(text("SELECT COUNT(*) FROM companies WHERE region IS NULL")).scalar()
            logger.info(f"region列为NULL的记录数: {null_region}")
            
            # 获取province列为NULL的记录数
            has_province_col = 'province' in [col['name'] for col in inspect(engine).get_columns('companies')]
            if has_province_col:
                null_province = conn.execute(text("SELECT COUNT(*) FROM companies WHERE province IS NULL")).scalar()
                logger.info(f"province列为NULL的记录数: {null_province}")
                
                # 验证province列的数据是否已正确迁移到region列
                mismatched = conn.execute(text(
                    """
                    SELECT COUNT(*) FROM companies 
                    WHERE province IS NOT NULL AND region IS NULL
                    """
                )).scalar()
                
                if mismatched > 0:
                    logger.warning(f"有 {mismatched} 条记录的province值未成功迁移到region")
                    return False
            
            return True
    
    except Exception as e:
        logger.error(f"验证region列时出错: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("===== 开始Render数据库修复 =====")
    
    # 检查是否在Render环境中
    is_render = os.environ.get('RENDER') == 'true'
    logger.info(f"当前环境: {'Render' if is_render else '本地'}")
    
    # 获取数据库URL
    db_url = get_db_url()
    if not db_url:
        logger.error("无法获取有效的数据库URL")
        return 1
    
    try:
        # 创建SQLAlchemy引擎
        logger.info("连接到数据库...")
        engine = create_engine(db_url)
        
        # 测试连接
        with engine.connect() as conn:
            logger.info("数据库连接成功")
        
        # 输出数据库概览
        check_all_tables(engine)
        
        # 修复companies表的region列
        logger.info("开始修复companies表...")
        if check_and_fix_companies_table(engine):
            logger.info("companies表修复成功")
        else:
            logger.error("companies表修复失败")
            return 1
        
        # 验证region列
        logger.info("验证region列...")
        if verify_region_column(engine):
            logger.info("region列验证通过")
        else:
            logger.warning("region列验证未通过，可能需要手动检查")
        
        # 修复迁移表
        logger.info("修复迁移表...")
        if fix_migrations_table(engine):
            logger.info("迁移表修复成功")
        else:
            logger.warning("迁移表修复失败，可能需要手动操作")
        
        logger.info("===== Render数据库修复完成 =====")
        return 0
        
    except Exception as e:
        logger.error(f"数据库修复过程中发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 