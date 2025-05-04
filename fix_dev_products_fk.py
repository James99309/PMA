#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复dev_products表的外键约束问题
删除外键约束并重新导入数据

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from decimal import Decimal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_dev_products.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('修复dev_products')

# 默认本地数据库连接信息
LOCAL_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')

# Render数据库连接信息
RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

def get_db_engine(db_url):
    """创建数据库引擎"""
    try:
        engine = create_engine(db_url)
        logger.info(f"成功创建数据库引擎")
        return engine
    except Exception as e:
        logger.error(f"创建数据库引擎时出错: {e}")
        return None

def drop_foreign_keys(engine):
    """删除外键约束"""
    try:
        with engine.begin() as conn:
            # 删除dev_product_specs表的外键约束
            conn.execute(text("ALTER TABLE dev_product_specs DROP CONSTRAINT IF EXISTS fk_dev_product_specs_product;"))
            
            # 删除dev_products表的外键约束
            conn.execute(text("ALTER TABLE dev_products DROP CONSTRAINT IF EXISTS fk_dev_products_category;"))
            conn.execute(text("ALTER TABLE dev_products DROP CONSTRAINT IF EXISTS fk_dev_products_subcategory;"))
            conn.execute(text("ALTER TABLE dev_products DROP CONSTRAINT IF EXISTS fk_dev_products_region;"))
            
            logger.info("成功删除外键约束")
        return True
    except Exception as e:
        logger.error(f"删除外键约束时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def get_table_data(engine, table_name):
    """获取表数据"""
    try:
        with engine.connect() as conn:
            # 获取表的列名
            columns_result = conn.execute(text(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
                ORDER BY ordinal_position;
            """))
            columns = [(row[0], row[1]) for row in columns_result]
            
            if not columns:
                logger.warning(f"表 {table_name} 没有列定义")
                return None, None
            
            column_names = ", ".join([col[0] for col in columns])
            
            # 查询表数据
            data = conn.execute(text(f"SELECT {column_names} FROM {table_name}")).fetchall()
            
            return columns, data
    except Exception as e:
        logger.error(f"获取表 {table_name} 数据时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

def import_data(engine, table_name, columns, data):
    """导入表数据"""
    try:
        if not data:
            logger.info(f"表 {table_name} 没有数据需要导入")
            return True
        
        column_names = ", ".join([col[0] for col in columns])
        
        # 清空表数据
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
            logger.info(f"已清空表 {table_name}")
            
            # 插入数据
            for row in data:
                # 处理特殊类型的数据转换
                processed_row = []
                for i, value in enumerate(row):
                    if isinstance(value, Decimal):
                        processed_row.append(float(value))
                    else:
                        processed_row.append(value)
                
                # 构建占位符和参数
                placeholders = ", ".join([f":{i}" for i in range(len(columns))])
                params = {str(i): processed_row[i] for i in range(len(processed_row))}
                
                # 构建INSERT语句
                insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                
                # 执行插入
                conn.execute(text(insert_sql), params)
            
            # 重置序列
            if "id" in column_names:
                if data:
                    max_id = max([row[0] for row in data]) + 1
                    sequence_name = f"{table_name}_id_seq"
                    conn.execute(text(f"SELECT setval('{sequence_name}', {max_id}, false);"))
                    logger.info(f"已重置序列 {sequence_name} 到 {max_id}")
            
            logger.info(f"成功导入 {len(data)} 行数据到表 {table_name}")
        
        return True
    except Exception as e:
        logger.error(f"导入表 {table_name} 数据时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("开始修复dev_products表的外键约束问题...")
    
    # 连接数据库
    source_engine = get_db_engine(LOCAL_DB_URL)
    target_engine = get_db_engine(RENDER_DB_URL)
    
    if not source_engine or not target_engine:
        logger.error("无法连接数据库")
        return 1
    
    # 删除外键约束
    if not drop_foreign_keys(target_engine):
        logger.error("删除外键约束失败")
        return 1
    
    # 获取dev_products表数据
    dev_products_columns, dev_products_data = get_table_data(source_engine, "dev_products")
    if not dev_products_columns or not dev_products_data:
        logger.error("获取dev_products表数据失败")
        return 1
    
    # 导入dev_products表数据
    if not import_data(target_engine, "dev_products", dev_products_columns, dev_products_data):
        logger.error("导入dev_products表数据失败")
        return 1
    
    # 获取dev_product_specs表数据
    dev_product_specs_columns, dev_product_specs_data = get_table_data(source_engine, "dev_product_specs")
    if not dev_product_specs_columns or not dev_product_specs_data:
        logger.error("获取dev_product_specs表数据失败")
        return 1
    
    # 导入dev_product_specs表数据
    if not import_data(target_engine, "dev_product_specs", dev_product_specs_columns, dev_product_specs_data):
        logger.error("导入dev_product_specs表数据失败")
        return 1
    
    logger.info("修复完成")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
修复dev_products表的外键约束问题
删除外键约束并重新导入数据

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from decimal import Decimal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_dev_products.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('修复dev_products')

# 默认本地数据库连接信息
LOCAL_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')

# Render数据库连接信息
RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

def get_db_engine(db_url):
    """创建数据库引擎"""
    try:
        engine = create_engine(db_url)
        logger.info(f"成功创建数据库引擎")
        return engine
    except Exception as e:
        logger.error(f"创建数据库引擎时出错: {e}")
        return None

def drop_foreign_keys(engine):
    """删除外键约束"""
    try:
        with engine.begin() as conn:
            # 删除dev_product_specs表的外键约束
            conn.execute(text("ALTER TABLE dev_product_specs DROP CONSTRAINT IF EXISTS fk_dev_product_specs_product;"))
            
            # 删除dev_products表的外键约束
            conn.execute(text("ALTER TABLE dev_products DROP CONSTRAINT IF EXISTS fk_dev_products_category;"))
            conn.execute(text("ALTER TABLE dev_products DROP CONSTRAINT IF EXISTS fk_dev_products_subcategory;"))
            conn.execute(text("ALTER TABLE dev_products DROP CONSTRAINT IF EXISTS fk_dev_products_region;"))
            
            logger.info("成功删除外键约束")
        return True
    except Exception as e:
        logger.error(f"删除外键约束时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def get_table_data(engine, table_name):
    """获取表数据"""
    try:
        with engine.connect() as conn:
            # 获取表的列名
            columns_result = conn.execute(text(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
                ORDER BY ordinal_position;
            """))
            columns = [(row[0], row[1]) for row in columns_result]
            
            if not columns:
                logger.warning(f"表 {table_name} 没有列定义")
                return None, None
            
            column_names = ", ".join([col[0] for col in columns])
            
            # 查询表数据
            data = conn.execute(text(f"SELECT {column_names} FROM {table_name}")).fetchall()
            
            return columns, data
    except Exception as e:
        logger.error(f"获取表 {table_name} 数据时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

def import_data(engine, table_name, columns, data):
    """导入表数据"""
    try:
        if not data:
            logger.info(f"表 {table_name} 没有数据需要导入")
            return True
        
        column_names = ", ".join([col[0] for col in columns])
        
        # 清空表数据
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
            logger.info(f"已清空表 {table_name}")
            
            # 插入数据
            for row in data:
                # 处理特殊类型的数据转换
                processed_row = []
                for i, value in enumerate(row):
                    if isinstance(value, Decimal):
                        processed_row.append(float(value))
                    else:
                        processed_row.append(value)
                
                # 构建占位符和参数
                placeholders = ", ".join([f":{i}" for i in range(len(columns))])
                params = {str(i): processed_row[i] for i in range(len(processed_row))}
                
                # 构建INSERT语句
                insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                
                # 执行插入
                conn.execute(text(insert_sql), params)
            
            # 重置序列
            if "id" in column_names:
                if data:
                    max_id = max([row[0] for row in data]) + 1
                    sequence_name = f"{table_name}_id_seq"
                    conn.execute(text(f"SELECT setval('{sequence_name}', {max_id}, false);"))
                    logger.info(f"已重置序列 {sequence_name} 到 {max_id}")
            
            logger.info(f"成功导入 {len(data)} 行数据到表 {table_name}")
        
        return True
    except Exception as e:
        logger.error(f"导入表 {table_name} 数据时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("开始修复dev_products表的外键约束问题...")
    
    # 连接数据库
    source_engine = get_db_engine(LOCAL_DB_URL)
    target_engine = get_db_engine(RENDER_DB_URL)
    
    if not source_engine or not target_engine:
        logger.error("无法连接数据库")
        return 1
    
    # 删除外键约束
    if not drop_foreign_keys(target_engine):
        logger.error("删除外键约束失败")
        return 1
    
    # 获取dev_products表数据
    dev_products_columns, dev_products_data = get_table_data(source_engine, "dev_products")
    if not dev_products_columns or not dev_products_data:
        logger.error("获取dev_products表数据失败")
        return 1
    
    # 导入dev_products表数据
    if not import_data(target_engine, "dev_products", dev_products_columns, dev_products_data):
        logger.error("导入dev_products表数据失败")
        return 1
    
    # 获取dev_product_specs表数据
    dev_product_specs_columns, dev_product_specs_data = get_table_data(source_engine, "dev_product_specs")
    if not dev_product_specs_columns or not dev_product_specs_data:
        logger.error("获取dev_product_specs表数据失败")
        return 1
    
    # 导入dev_product_specs表数据
    if not import_data(target_engine, "dev_product_specs", dev_product_specs_columns, dev_product_specs_data):
        logger.error("导入dev_product_specs表数据失败")
        return 1
    
    logger.info("修复完成")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 