#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复云端数据库迁移问题 - 添加缺失的列
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from config import CLOUD_DB_URL

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_and_add_missing_columns():
    """检查并添加缺失的列"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        inspector = inspect(engine)
        
        with engine.connect() as conn:
            # 检查 quotation_details 表的列
            quotation_details_columns = [col['name'] for col in inspector.get_columns('quotation_details')]
            logger.info(f"quotation_details 表现有列: {quotation_details_columns}")
            
            # 检查 quotations 表的列
            quotations_columns = [col['name'] for col in inspector.get_columns('quotations')]
            logger.info(f"quotations 表现有列: {quotations_columns}")
            
            # 检查并添加 implant_subtotal 列到 quotation_details 表
            if 'implant_subtotal' not in quotation_details_columns:
                logger.info("添加 implant_subtotal 列到 quotation_details 表...")
                
                # 添加列
                conn.execute(text("""
                    ALTER TABLE quotation_details 
                    ADD COLUMN implant_subtotal NUMERIC(12,2) DEFAULT 0.00
                """))
                
                # 添加注释（PostgreSQL 语法）
                conn.execute(text("""
                    COMMENT ON COLUMN quotation_details.implant_subtotal IS 
                    '植入小计：当产品品牌是和源通信时，零售价格 * 产品数量的值'
                """))
                
                # 创建索引
                conn.execute(text("""
                    CREATE INDEX idx_quotation_details_implant_subtotal 
                    ON quotation_details (implant_subtotal)
                """))
                
                logger.info("✓ implant_subtotal 列已添加")
            else:
                logger.info("implant_subtotal 列已存在")
            
            # 检查并添加 implant_total_amount 列到 quotations 表
            if 'implant_total_amount' not in quotations_columns:
                logger.info("添加 implant_total_amount 列到 quotations 表...")
                
                # 添加列
                conn.execute(text("""
                    ALTER TABLE quotations 
                    ADD COLUMN implant_total_amount NUMERIC(12,2) DEFAULT 0.00
                """))
                
                # 添加注释（PostgreSQL 语法）
                conn.execute(text("""
                    COMMENT ON COLUMN quotations.implant_total_amount IS 
                    '植入总额合计：该报价单产品明细下所有植入小计值的合计'
                """))
                
                # 创建索引
                conn.execute(text("""
                    CREATE INDEX idx_quotations_implant_total_amount 
                    ON quotations (implant_total_amount)
                """))
                
                logger.info("✓ implant_total_amount 列已添加")
            else:
                logger.info("implant_total_amount 列已存在")
            
            # 提交变更
            conn.commit()
            logger.info("✓ 所有缺失的列已添加完成")
            
        return True
        
    except Exception as e:
        logger.error(f"添加缺失列失败: {str(e)}")
        return False

def mark_migration_as_applied():
    """将问题迁移标记为已应用"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            # 检查 alembic_version 表
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
            logger.info(f"当前迁移版本: {current_version}")
            
            # 如果当前版本不是最新的，更新它
            if current_version != '69da2a6b4ac1':
                logger.info("更新迁移版本到 69da2a6b4ac1...")
                conn.execute(text("UPDATE alembic_version SET version_num = '69da2a6b4ac1'"))
                conn.commit()
                logger.info("✓ 迁移版本已更新")
            else:
                logger.info("迁移版本已是最新")
                
        return True
        
    except Exception as e:
        logger.error(f"更新迁移版本失败: {str(e)}")
        return False

def verify_cloud_structure():
    """验证云端数据库结构"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        inspector = inspect(engine)
        
        # 获取所有表
        tables = inspector.get_table_names()
        logger.info(f"云端数据库包含 {len(tables)} 个表")
        
        # 检查关键表的结构
        key_tables = ['quotations', 'quotation_details', 'products', 'projects', 'customers', 'users']
        
        for table in key_tables:
            if table in tables:
                columns = inspector.get_columns(table)
                logger.info(f"表 {table} 包含 {len(columns)} 列")
                
                # 特别检查植入相关列
                if table == 'quotation_details':
                    col_names = [col['name'] for col in columns]
                    if 'implant_subtotal' in col_names:
                        logger.info("  ✓ implant_subtotal 列存在")
                    else:
                        logger.warning("  ✗ implant_subtotal 列缺失")
                        
                elif table == 'quotations':
                    col_names = [col['name'] for col in columns]
                    if 'implant_total_amount' in col_names:
                        logger.info("  ✓ implant_total_amount 列存在")
                    else:
                        logger.warning("  ✗ implant_total_amount 列缺失")
            else:
                logger.warning(f"表 {table} 不存在")
        
        return True
        
    except Exception as e:
        logger.error(f"验证数据库结构失败: {str(e)}")
        return False

def main():
    """主修复流程"""
    logger.info("=" * 60)
    logger.info("开始修复云端数据库迁移问题")
    logger.info("=" * 60)
    
    # 步骤1: 验证连接
    logger.info("\n步骤1: 验证云端数据库连接")
    try:
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ 连接成功: {version}")
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        return False
    
    # 步骤2: 检查并添加缺失的列
    logger.info("\n步骤2: 检查并添加缺失的列")
    if not check_and_add_missing_columns():
        logger.error("添加缺失列失败")
        return False
    
    # 步骤3: 标记迁移为已应用
    logger.info("\n步骤3: 更新迁移版本")
    if not mark_migration_as_applied():
        logger.error("更新迁移版本失败")
        return False
    
    # 步骤4: 验证修复结果
    logger.info("\n步骤4: 验证修复结果")
    if not verify_cloud_structure():
        logger.error("验证失败")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 云端数据库迁移问题修复完成!")
    logger.info("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            logger.info("修复成功完成")
            sys.exit(0)
        else:
            logger.error("修复失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n用户中断修复过程")
        sys.exit(1)
    except Exception as e:
        logger.error(f"修复过程发生异常: {str(e)}")
        sys.exit(1) 