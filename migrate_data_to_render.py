#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL本地数据库数据迁移到Render云数据库脚本
仅迁移数据，不创建表结构(表结构已由create_render_db_tables.py创建)

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import time
import logging
import psycopg2
from sqlalchemy import create_engine, text
from decimal import Decimal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('数据迁移')

# 默认本地数据库连接信息
LOCAL_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')

# Render数据库连接信息
RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

# 需要迁移的表列表
TABLES_TO_MIGRATE = [
    'users', 'permissions', 'dictionaries', 'data_affiliations', 
    'companies', 'contacts', 'projects', 'project_members',
    'products', 'dev_products', 'dev_product_specs', 
    'product_categories', 'product_subcategories', 'product_regions',
    'product_codes', 'product_code_fields', 'product_code_field_options', 'product_code_field_values',
    'quotations', 'quotation_details', 'affiliations', 'alembic_version'
]

def get_db_engine(db_url):
    """创建数据库引擎"""
    try:
        engine = create_engine(db_url)
        logger.info(f"成功创建数据库引擎")
        return engine
    except Exception as e:
        logger.error(f"创建数据库引擎时出错: {e}")
        return None

def get_table_names(engine):
    """获取数据库中的所有表名"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            table_names = [row[0] for row in result.fetchall()]
            return table_names
    except Exception as e:
        logger.error(f"获取表名列表时出错: {e}")
        return []

def get_table_columns(engine, table_name):
    """获取表的列定义"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
                ORDER BY ordinal_position;
            """))
            columns = [(row[0], row[1]) for row in result]
            return columns
    except Exception as e:
        logger.error(f"获取表 {table_name} 的列定义时出错: {e}")
        return []

def clear_table(engine, table_name):
    """清空表数据"""
    try:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
            logger.info(f"已清空表 {table_name}")
        return True
    except Exception as e:
        logger.warning(f"清空表 {table_name} 时出错: {e}")
        return False

def copy_table_data(source_engine, target_engine, table_name):
    """复制表数据"""
    try:
        # 获取表的列名
        columns = get_table_columns(source_engine, table_name)
        if not columns:
            logger.warning(f"表 {table_name} 没有列定义")
            return False
        
        column_names = ", ".join([col[0] for col in columns])
        
        # 查询源表数据
        with source_engine.connect() as source_conn:
            data = source_conn.execute(text(f"SELECT {column_names} FROM {table_name}")).fetchall()
        
        if not data:
            logger.info(f"表 {table_name} 没有数据需要复制")
            return True
        
        # 插入目标表
        total_rows = len(data)
        batch_size = 50  # 减小批量插入的行数，避免请求过大
        batches = (total_rows + batch_size - 1) // batch_size  # 向上取整计算批次数
        
        # 先清空目标表
        clear_table(target_engine, table_name)
        
        success_count = 0
        for i in range(batches):
            start = i * batch_size
            end = min(start + batch_size, total_rows)
            batch_data = data[start:end]
            
            if len(batch_data) == 0:
                continue
                
            try:
                with target_engine.begin() as target_conn:
                    for row in batch_data:
                        # 处理特殊类型的数据转换
                        processed_row = []
                        for j, value in enumerate(row):
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
                        target_conn.execute(text(insert_sql), params)
                
                success_count += len(batch_data)
                logger.info(f"表 {table_name}: 已复制 {end}/{total_rows} 行数据")
            except Exception as e:
                logger.error(f"插入表 {table_name} 数据批次 {i+1}/{batches} 时出错: {e}")
        
        # 验证迁移的数据量
        with target_engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            logger.info(f"表 {table_name} 迁移验证: 源数据 {total_rows} 行, 目标数据 {count} 行")
        
        return success_count == total_rows
    except Exception as e:
        logger.error(f"复制表 {table_name} 数据时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def reset_sequences(engine, table_name, id_column='id'):
    """重置序列"""
    try:
        with engine.begin() as conn:
            # 获取主键的序列名
            sequence_query = f"""
                SELECT pg_get_serial_sequence('public.{table_name}', '{id_column}')
            """
            sequence_name = conn.execute(text(sequence_query)).scalar()
            
            if sequence_name:
                # 查询当前最大ID
                max_id_query = f"SELECT COALESCE(MAX({id_column}), 0) + 1 FROM {table_name}"
                max_id = conn.execute(text(max_id_query)).scalar()
                
                # 重置序列
                if max_id:
                    reset_query = f"ALTER SEQUENCE {sequence_name} RESTART WITH {max_id}"
                    conn.execute(text(reset_query))
                    logger.info(f"已重置表 {table_name} 的序列 {sequence_name} 到 {max_id}")
            else:
                logger.info(f"表 {table_name} 没有找到序列 {table_name}_{id_column}_seq")
    except Exception as e:
        logger.error(f"重置表 {table_name} 序列时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

def migrate_database(local_db_url, render_db_url):
    """数据库迁移主函数"""
    try:
        start_time = time.time()
        logger.info("开始数据库迁移...")
        
        # 连接源数据库和目标数据库
        source_engine = get_db_engine(local_db_url)
        target_engine = get_db_engine(render_db_url)
        
        # 验证数据库连接
        source_tables = get_table_names(source_engine)
        target_tables = get_table_names(target_engine)
        
        if not source_tables:
            logger.error("源数据库中没有找到表")
            return False
        
        if not target_tables:
            logger.error("目标数据库中没有找到表")
            return False
        
        logger.info(f"源数据库有 {len(source_tables)} 张表")
        logger.info(f"目标数据库有 {len(target_tables)} 张表")
        
        # 处理每个表
        for i, table_name in enumerate(TABLES_TO_MIGRATE, 1):
            if table_name not in source_tables:
                logger.warning(f"[{i}/{len(TABLES_TO_MIGRATE)}] 表 {table_name} 在源数据库中不存在，跳过")
                continue
                
            if table_name not in target_tables:
                logger.warning(f"[{i}/{len(TABLES_TO_MIGRATE)}] 表 {table_name} 在目标数据库中不存在，跳过")
                continue
            
            logger.info(f"[{i}/{len(TABLES_TO_MIGRATE)}] 处理表 {table_name}")
            
            # 复制数据
            success = copy_table_data(source_engine, target_engine, table_name)
            
            if success:
                logger.info(f"已成功复制表 {table_name} 的数据")
                # 重置序列
                reset_sequences(target_engine, table_name)
            else:
                logger.warning(f"复制表 {table_name} 数据可能不完整")
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"数据库迁移完成! 总耗时: {duration:.2f} 秒")
        
        return True
    
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info(f"本地数据库: {LOCAL_DB_URL}")
    logger.info(f"Render数据库: {RENDER_DB_URL}")
    
    # 执行迁移
    if migrate_database(LOCAL_DB_URL, RENDER_DB_URL):
        logger.info("迁移脚本执行成功!")
        return 0
    else:
        logger.error("迁移脚本执行失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
PostgreSQL本地数据库数据迁移到Render云数据库脚本
仅迁移数据，不创建表结构(表结构已由create_render_db_tables.py创建)

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import time
import logging
import psycopg2
from sqlalchemy import create_engine, text
from decimal import Decimal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('数据迁移')

# 默认本地数据库连接信息
LOCAL_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')

# Render数据库连接信息
RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

# 需要迁移的表列表
TABLES_TO_MIGRATE = [
    'users', 'permissions', 'dictionaries', 'data_affiliations', 
    'companies', 'contacts', 'projects', 'project_members',
    'products', 'dev_products', 'dev_product_specs', 
    'product_categories', 'product_subcategories', 'product_regions',
    'product_codes', 'product_code_fields', 'product_code_field_options', 'product_code_field_values',
    'quotations', 'quotation_details', 'affiliations', 'alembic_version'
]

def get_db_engine(db_url):
    """创建数据库引擎"""
    try:
        engine = create_engine(db_url)
        logger.info(f"成功创建数据库引擎")
        return engine
    except Exception as e:
        logger.error(f"创建数据库引擎时出错: {e}")
        return None

def get_table_names(engine):
    """获取数据库中的所有表名"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            table_names = [row[0] for row in result.fetchall()]
            return table_names
    except Exception as e:
        logger.error(f"获取表名列表时出错: {e}")
        return []

def get_table_columns(engine, table_name):
    """获取表的列定义"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
                ORDER BY ordinal_position;
            """))
            columns = [(row[0], row[1]) for row in result]
            return columns
    except Exception as e:
        logger.error(f"获取表 {table_name} 的列定义时出错: {e}")
        return []

def clear_table(engine, table_name):
    """清空表数据"""
    try:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
            logger.info(f"已清空表 {table_name}")
        return True
    except Exception as e:
        logger.warning(f"清空表 {table_name} 时出错: {e}")
        return False

def copy_table_data(source_engine, target_engine, table_name):
    """复制表数据"""
    try:
        # 获取表的列名
        columns = get_table_columns(source_engine, table_name)
        if not columns:
            logger.warning(f"表 {table_name} 没有列定义")
            return False
        
        column_names = ", ".join([col[0] for col in columns])
        
        # 查询源表数据
        with source_engine.connect() as source_conn:
            data = source_conn.execute(text(f"SELECT {column_names} FROM {table_name}")).fetchall()
        
        if not data:
            logger.info(f"表 {table_name} 没有数据需要复制")
            return True
        
        # 插入目标表
        total_rows = len(data)
        batch_size = 50  # 减小批量插入的行数，避免请求过大
        batches = (total_rows + batch_size - 1) // batch_size  # 向上取整计算批次数
        
        # 先清空目标表
        clear_table(target_engine, table_name)
        
        success_count = 0
        for i in range(batches):
            start = i * batch_size
            end = min(start + batch_size, total_rows)
            batch_data = data[start:end]
            
            if len(batch_data) == 0:
                continue
                
            try:
                with target_engine.begin() as target_conn:
                    for row in batch_data:
                        # 处理特殊类型的数据转换
                        processed_row = []
                        for j, value in enumerate(row):
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
                        target_conn.execute(text(insert_sql), params)
                
                success_count += len(batch_data)
                logger.info(f"表 {table_name}: 已复制 {end}/{total_rows} 行数据")
            except Exception as e:
                logger.error(f"插入表 {table_name} 数据批次 {i+1}/{batches} 时出错: {e}")
        
        # 验证迁移的数据量
        with target_engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            logger.info(f"表 {table_name} 迁移验证: 源数据 {total_rows} 行, 目标数据 {count} 行")
        
        return success_count == total_rows
    except Exception as e:
        logger.error(f"复制表 {table_name} 数据时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def reset_sequences(engine, table_name, id_column='id'):
    """重置序列"""
    try:
        with engine.begin() as conn:
            # 获取主键的序列名
            sequence_query = f"""
                SELECT pg_get_serial_sequence('public.{table_name}', '{id_column}')
            """
            sequence_name = conn.execute(text(sequence_query)).scalar()
            
            if sequence_name:
                # 查询当前最大ID
                max_id_query = f"SELECT COALESCE(MAX({id_column}), 0) + 1 FROM {table_name}"
                max_id = conn.execute(text(max_id_query)).scalar()
                
                # 重置序列
                if max_id:
                    reset_query = f"ALTER SEQUENCE {sequence_name} RESTART WITH {max_id}"
                    conn.execute(text(reset_query))
                    logger.info(f"已重置表 {table_name} 的序列 {sequence_name} 到 {max_id}")
            else:
                logger.info(f"表 {table_name} 没有找到序列 {table_name}_{id_column}_seq")
    except Exception as e:
        logger.error(f"重置表 {table_name} 序列时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

def migrate_database(local_db_url, render_db_url):
    """数据库迁移主函数"""
    try:
        start_time = time.time()
        logger.info("开始数据库迁移...")
        
        # 连接源数据库和目标数据库
        source_engine = get_db_engine(local_db_url)
        target_engine = get_db_engine(render_db_url)
        
        # 验证数据库连接
        source_tables = get_table_names(source_engine)
        target_tables = get_table_names(target_engine)
        
        if not source_tables:
            logger.error("源数据库中没有找到表")
            return False
        
        if not target_tables:
            logger.error("目标数据库中没有找到表")
            return False
        
        logger.info(f"源数据库有 {len(source_tables)} 张表")
        logger.info(f"目标数据库有 {len(target_tables)} 张表")
        
        # 处理每个表
        for i, table_name in enumerate(TABLES_TO_MIGRATE, 1):
            if table_name not in source_tables:
                logger.warning(f"[{i}/{len(TABLES_TO_MIGRATE)}] 表 {table_name} 在源数据库中不存在，跳过")
                continue
                
            if table_name not in target_tables:
                logger.warning(f"[{i}/{len(TABLES_TO_MIGRATE)}] 表 {table_name} 在目标数据库中不存在，跳过")
                continue
            
            logger.info(f"[{i}/{len(TABLES_TO_MIGRATE)}] 处理表 {table_name}")
            
            # 复制数据
            success = copy_table_data(source_engine, target_engine, table_name)
            
            if success:
                logger.info(f"已成功复制表 {table_name} 的数据")
                # 重置序列
                reset_sequences(target_engine, table_name)
            else:
                logger.warning(f"复制表 {table_name} 数据可能不完整")
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"数据库迁移完成! 总耗时: {duration:.2f} 秒")
        
        return True
    
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info(f"本地数据库: {LOCAL_DB_URL}")
    logger.info(f"Render数据库: {RENDER_DB_URL}")
    
    # 执行迁移
    if migrate_database(LOCAL_DB_URL, RENDER_DB_URL):
        logger.info("迁移脚本执行成功!")
        return 0
    else:
        logger.error("迁移脚本执行失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 