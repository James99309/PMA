#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据导入脚本
使用正确的SSL参数将JSON数据导入到Render PostgreSQL数据库
"""

import os
import sys
import json
import logging
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_import.log')
    ]
)
logger = logging.getLogger('Render数据导入')

def parse_db_url(url):
    """解析数据库URL"""
    parsed = urlparse(url)
    
    db_info = {
        'dbname': parsed.path.strip('/'),
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'sslmode': 'require',
        'sslrootcert': 'none'
    }
    
    logger.info(f"数据库信息:")
    logger.info(f"  主机: {db_info['host']}")
    logger.info(f"  端口: {db_info['port']}")
    logger.info(f"  数据库: {db_info['dbname']}")
    logger.info(f"  用户: {db_info['user']}")
    
    return db_info

def connect_to_db(db_info):
    """连接到PostgreSQL数据库"""
    try:
        logger.info("连接到Render PostgreSQL数据库...")
        conn = psycopg2.connect(**db_info)
        
        # 测试连接
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {version}")
        
        return conn
    except Exception as e:
        logger.error(f"连接失败: {str(e)}")
        raise

def load_json_data(json_file):
    """从JSON文件加载数据"""
    try:
        logger.info(f"加载JSON数据文件: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"JSON数据加载成功, 包含 {len(data)} 个表")
        return data
    except Exception as e:
        logger.error(f"JSON数据加载失败: {str(e)}")
        raise

def truncate_table(conn, table_name):
    """清空表数据"""
    try:
        logger.info(f"清空表 {table_name}...")
        cursor = conn.cursor()
        cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
        conn.commit()
        logger.info(f"表 {table_name} 已清空")
    except Exception as e:
        conn.rollback()
        logger.error(f"清空表 {table_name} 失败: {str(e)}")
        raise

def disable_triggers(conn):
    """禁用所有触发器，使导入更快速"""
    try:
        logger.info("禁用触发器...")
        cursor = conn.cursor()
        cursor.execute("SET session_replication_role = 'replica';")
        conn.commit()
        logger.info("触发器已禁用")
    except Exception as e:
        conn.rollback()
        logger.error(f"禁用触发器失败: {str(e)}")
        raise

def enable_triggers(conn):
    """重新启用触发器"""
    try:
        logger.info("启用触发器...")
        cursor = conn.cursor()
        cursor.execute("SET session_replication_role = 'origin';")
        conn.commit()
        logger.info("触发器已启用")
    except Exception as e:
        conn.rollback()
        logger.error(f"启用触发器失败: {str(e)}")
        raise

def reset_sequences(conn, tables):
    """重置所有表的序列"""
    try:
        logger.info("重置序列...")
        cursor = conn.cursor()
        
        for table_name in tables:
            # 尝试查找表的主键序列
            cursor.execute("""
                SELECT column_name, column_default 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_default LIKE 'nextval%%'
            """, (table_name,))
            
            sequences = cursor.fetchall()
            for col_name, col_default in sequences:
                # 从默认值中提取序列名称
                seq_name = col_default.split("'")[1]
                
                # 查找表中最大ID值
                cursor.execute(f"SELECT COALESCE(MAX({col_name}), 0) FROM {table_name}")
                max_id = cursor.fetchone()[0]
                
                # 重置序列值
                cursor.execute(f"SELECT setval('{seq_name}', {max_id + 1}, false)")
                logger.info(f"序列 {seq_name} 已重置为 {max_id + 1}")
        
        conn.commit()
        logger.info("所有序列已重置")
    except Exception as e:
        conn.rollback()
        logger.error(f"重置序列失败: {str(e)}")
        raise

def import_table_data(conn, table_name, records):
    """导入表数据"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return
    
    try:
        logger.info(f"导入表 {table_name} 的数据，共 {len(records)} 条记录")
        cursor = conn.cursor()
        
        # 第一条记录的键作为列名
        columns = list(records[0].keys())
        
        # 构建插入语句
        columns_str = ', '.join(columns)
        values_placeholder = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
        
        # 准备数据
        values = []
        for record in records:
            row = [record.get(column) for column in columns]
            values.append(row)
        
        # 执行批量插入
        psycopg2.extras.execute_batch(cursor, insert_query, values)
        
        conn.commit()
        logger.info(f"表 {table_name} 数据导入成功")
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        # 继续执行，而不是抛出异常，以便处理其他表
        logger.info(f"跳过表 {table_name} 继续导入其他表")

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_to_render.py <数据库URL> <JSON数据文件>")
        return 1
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    
    try:
        # 解析数据库URL
        db_info = parse_db_url(db_url)
        
        # 连接数据库
        conn = connect_to_db(db_info)
        
        # 加载JSON数据
        data = load_json_data(json_file)
        
        # 禁用触发器
        disable_triggers(conn)
        
        # 按表导入数据
        for table_name, records in data.items():
            try:
                # 清空表
                truncate_table(conn, table_name)
                
                # 导入数据
                import_table_data(conn, table_name, records)
            except Exception as e:
                logger.error(f"处理表 {table_name} 时出错: {str(e)}")
                # 继续处理其他表
        
        # 重置序列
        reset_sequences(conn, data.keys())
        
        # 重新启用触发器
        enable_triggers(conn)
        
        # 关闭连接
        conn.close()
        
        logger.info("数据导入完成!")
        return 0
    except Exception as e:
        logger.error(f"数据导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 