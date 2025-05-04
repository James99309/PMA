#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL本地数据库迁移到Render云数据库脚本
用于将本地PostgreSQL数据库的结构和数据完整迁移到Render上的新数据库

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import time
import logging
import argparse
import psycopg2
from sqlalchemy import create_engine, MetaData, Table, Column, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('数据库迁移')

# 默认本地数据库连接信息（将根据实际情况从环境变量获取或配置）
LOCAL_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')

# Render数据库连接信息
RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

def get_connection_from_url(db_url):
    """从数据库URL获取psycopg2连接"""
    try:
        # 提取连接参数
        db_info = {}
        if db_url.startswith('postgresql://'):
            # 解析PostgreSQL URL
            db_url = db_url.replace('postgresql://', '')
            user_pass, host_db = db_url.split('@')
            
            if ':' in user_pass:
                db_info['user'], db_info['password'] = user_pass.split(':')
            else:
                db_info['user'] = user_pass
                db_info['password'] = ''
            
            if '/' in host_db:
                host_port, db_name = host_db.split('/')
                db_info['dbname'] = db_name
                
                if ':' in host_port:
                    db_info['host'], db_info['port'] = host_port.split(':')
                else:
                    db_info['host'] = host_port
                    db_info['port'] = '5432'
            else:
                db_info['host'] = host_db
                db_info['port'] = '5432'
                db_info['dbname'] = 'postgres'
        
        # 创建连接
        conn = psycopg2.connect(**db_info)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {e}")
        raise

def get_db_engine(db_url):
    """获取SQLAlchemy引擎"""
    return create_engine(db_url)

def get_table_names(engine):
    """获取数据库中所有表名"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        return [row[0] for row in result]

def get_table_structure(engine, table_name):
    """获取表结构"""
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT column_name, data_type, 
                   character_maximum_length, 
                   is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = '{table_name}'
            ORDER BY ordinal_position;
        """))
        
        columns = []
        for row in result:
            columns.append({
                'name': row[0],
                'type': row[1],
                'length': row[2],
                'nullable': row[3],
                'default': row[4]
            })
        
        # 获取主键信息
        result = conn.execute(text(f"""
            SELECT c.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
            JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
              AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
            WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = '{table_name}';
        """))
        
        primary_keys = [row[0] for row in result]
        
        return {
            'columns': columns,
            'primary_keys': primary_keys
        }

def generate_create_table_sql(table_name, structure):
    """生成建表SQL语句"""
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    
    for i, column in enumerate(structure['columns']):
        sql += f"    {column['name']} {column['type']}"
        
        if column['length'] is not None:
            sql += f"({column['length']})"
        
        if column['nullable'] == 'NO':
            sql += " NOT NULL"
        
        if column['default'] is not None:
            sql += f" DEFAULT {column['default']}"
        
        if i < len(structure['columns']) - 1:
            sql += ",\n"
        else:
            if structure['primary_keys']:
                sql += ",\n    PRIMARY KEY (" + ", ".join(structure['primary_keys']) + ")"
    
    sql += "\n);"
    return sql

def create_table_structure(engine, table_name, structure_sql):
    """创建表结构"""
    with engine.connect() as conn:
        conn.execute(text(structure_sql))
        conn.commit()

def copy_table_data(source_engine, target_engine, table_name):
    """复制表数据"""
    try:
        # 获取表的列名
        with source_engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
                ORDER BY ordinal_position;
            """))
            columns = [row[0] for row in result]
        
        if not columns:
            logger.warning(f"表 {table_name} 没有列定义")
            return
        
        column_names = ", ".join(columns)
        
        # 查询源表数据
        with source_engine.connect() as source_conn:
            data = source_conn.execute(text(f"SELECT {column_names} FROM {table_name}")).fetchall()
        
        if not data:
            logger.info(f"表 {table_name} 没有数据需要复制")
            return
        
        # 插入目标表
        total_rows = len(data)
        batch_size = 100  # 减小批量插入的行数，避免请求过大
        batches = (total_rows + batch_size - 1) // batch_size  # 向上取整计算批次数
        
        # 先尝试清空目标表
        try:
            with target_engine.connect() as target_conn:
                target_conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
                target_conn.commit()
                logger.info(f"已清空表 {table_name}")
        except Exception as e:
            logger.warning(f"清空表 {table_name} 时出错: {e}")
            logger.info("将尝试使用INSERT ON CONFLICT DO NOTHING语法")
        
        for i in range(batches):
            start = i * batch_size
            end = min(start + batch_size, total_rows)
            batch_data = data[start:end]
            
            if len(batch_data) == 0:
                continue
                
            try:
                # 构建单独的语句插入每一行，避免一次性构建太长的SQL
                with target_engine.connect() as target_conn:
                    for row in batch_data:
                        # 为每一列构建占位符
                        placeholders = ", ".join([":val" + str(i) for i in range(len(columns))])
                        
                        # 构建带命名参数的INSERT语句
                        insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                        
                        # 准备参数字典
                        params = {f"val{i}": value for i, value in enumerate(row)}
                        
                        # 执行插入
                        target_conn.execute(text(insert_sql), params)
                    
                    target_conn.commit()
                
                logger.info(f"表 {table_name}: 已复制 {end}/{total_rows} 行数据")
            except Exception as e:
                logger.error(f"插入表 {table_name} 数据批次 {i+1}/{batches} 时出错: {e}")
        
        return True
    except Exception as e:
        logger.error(f"复制表 {table_name} 数据时出错: {e}")
        return False

def reset_sequences(engine, table_name, primary_key='id'):
    """重置序列（假设主键是id且有序列）"""
    try:
        with engine.connect() as conn:
            # 检查序列是否存在
            seq_name = f"{table_name}_{primary_key}_seq"
            result = conn.execute(text(f"""
                SELECT 1 FROM pg_sequences WHERE sequencename = '{seq_name}';
            """))
            
            if result.rowcount > 0:
                # 重置序列
                conn.execute(text(f"""
                    SELECT setval(pg_get_serial_sequence('{table_name}', '{primary_key}'), 
                        (SELECT COALESCE(MAX({primary_key}), 1) FROM {table_name}), true);
                """))
                logger.info(f"已重置表 {table_name} 的序列 {seq_name}")
            else:
                logger.info(f"表 {table_name} 没有找到序列 {seq_name}")
    except Exception as e:
        logger.warning(f"重置表 {table_name} 的序列时出错: {e}")

def check_constraints(engine):
    """检查和修复约束"""
    with engine.connect() as conn:
        logger.info("检查和启用所有约束...")
        # 启用所有外键约束
        conn.execute(text("SET session_replication_role = 'origin';"))
        conn.commit()

def migrate_database(local_db_url, render_db_url):
    """数据库迁移主函数"""
    try:
        start_time = time.time()
        logger.info("开始数据库迁移...")
        
        # 连接源数据库和目标数据库
        source_engine = get_db_engine(local_db_url)
        target_engine = get_db_engine(render_db_url)
        
        # 获取源数据库的所有表
        table_names = get_table_names(source_engine)
        logger.info(f"找到 {len(table_names)} 个表需要迁移")
        
        # 尝试禁用外键约束，如果没有权限则跳过
        try:
            with target_engine.connect() as conn:
                conn.execute(text("SET session_replication_role = 'replica';"))
                conn.commit()
                logger.info("已暂时禁用外键约束")
        except Exception as e:
            logger.warning(f"无法禁用外键约束，将尝试直接迁移: {e}")
        
        # 处理每个表
        for i, table_name in enumerate(table_names, 1):
            logger.info(f"[{i}/{len(table_names)}] 处理表 {table_name}")
            
            # 1. 获取表结构
            structure = get_table_structure(source_engine, table_name)
            
            # 2. 生成建表SQL
            create_sql = generate_create_table_sql(table_name, structure)
            
            # 3. 在目标数据库创建表
            try:
                create_table_structure(target_engine, table_name, create_sql)
                logger.info(f"已创建表 {table_name} 的结构")
            except Exception as e:
                logger.warning(f"创建表 {table_name} 结构时出错: {e}")
                logger.info(f"尝试使用表 {table_name} 的现有结构")
            
            # 4. 复制数据
            try:
                copy_table_data(source_engine, target_engine, table_name)
                logger.info(f"已复制表 {table_name} 的数据")
            except Exception as e:
                logger.error(f"复制表 {table_name} 数据时出错: {e}")
            
            # 5. 重置序列
            if 'id' in [col['name'] for col in structure['columns']]:
                try:
                    reset_sequences(target_engine, table_name)
                except Exception as e:
                    logger.warning(f"重置表 {table_name} 序列时出错: {e}")
        
        # 尝试重新启用约束
        try:
            check_constraints(target_engine)
        except Exception as e:
            logger.warning(f"重新启用约束时出错: {e}")
        
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
    parser = argparse.ArgumentParser(description='PostgreSQL本地数据库迁移到Render')
    parser.add_argument('--local-db', help='本地数据库URL', default=LOCAL_DB_URL)
    parser.add_argument('--render-db', help='Render数据库URL', default=RENDER_DB_URL)
    args = parser.parse_args()
    
    logger.info(f"本地数据库: {args.local_db}")
    logger.info(f"Render数据库: {args.render_db}")
    
    # 执行迁移
    success = migrate_database(args.local_db, args.render_db)
    
    if success:
        logger.info("迁移脚本执行成功!")
        return 0
    else:
        logger.error("迁移脚本执行失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 