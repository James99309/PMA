#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据导入脚本 (简化版)
使用正确的SSL参数将JSON数据导入到Render PostgreSQL数据库，不使用触发器控制
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
        logging.FileHandler('render_import_simple.log')
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

def get_table_structure(conn, table_name):
    """获取表结构，用于验证列名"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = [row[0] for row in cursor.fetchall()]
        return columns
    except Exception as e:
        logger.error(f"获取表 {table_name} 结构失败: {str(e)}")
        return []

def import_table_data(conn, table_name, records):
    """导入表数据"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return
    
    try:
        logger.info(f"导入表 {table_name} 的数据，共 {len(records)} 条记录")
        
        # 清空表内容 (如果可能)
        try:
            logger.info(f"尝试清空表 {table_name}...")
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name};")
            conn.commit()
            logger.info(f"表 {table_name} 已清空")
        except Exception as e:
            conn.rollback()
            logger.warning(f"清空表 {table_name} 失败: {str(e)}，将尝试直接插入")
        
        # 获取表结构
        db_columns = get_table_structure(conn, table_name)
        if not db_columns:
            logger.warning(f"无法获取表 {table_name} 的结构，跳过")
            return
        
        cursor = conn.cursor()
        
        # 第一条记录的键作为列名
        json_columns = list(records[0].keys())
        
        # 只使用数据库中存在的列
        valid_columns = [col for col in json_columns if col.lower() in [c.lower() for c in db_columns]]
        
        if not valid_columns:
            logger.warning(f"表 {table_name} 没有有效的列匹配，跳过")
            return
        
        # 构建插入语句
        columns_str = ', '.join(valid_columns)
        values_placeholder = ', '.join(['%s'] * len(valid_columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
        
        # 按批次插入数据
        batch_size = 100
        total_records = len(records)
        processed = 0
        
        for i in range(0, total_records, batch_size):
            batch = records[i:i + batch_size]
            values = []
            
            for record in batch:
                row = [record.get(column) for column in valid_columns]
                values.append(row)
            
            try:
                psycopg2.extras.execute_batch(cursor, insert_query, values)
                conn.commit()
                processed += len(batch)
                logger.info(f"已导入 {processed}/{total_records} 条记录到表 {table_name}")
            except Exception as e:
                conn.rollback()
                logger.error(f"导入批次 {i//batch_size + 1} 失败: {str(e)}")
        
        logger.info(f"表 {table_name} 数据导入完成，成功导入 {processed}/{total_records} 条记录")
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        # 继续执行，而不是抛出异常，以便处理其他表
        logger.info(f"跳过表 {table_name} 继续导入其他表")

def list_tables(conn):
    """列出数据库中的所有表"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库中的表: {', '.join(tables)}")
        return tables
    except Exception as e:
        logger.error(f"获取表列表失败: {str(e)}")
        return []

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_to_render_simple.py <数据库URL> <JSON数据文件>")
        return 1
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    specific_tables = sys.argv[3:] if len(sys.argv) > 3 else None
    
    try:
        # 解析数据库URL
        db_info = parse_db_url(db_url)
        
        # 连接数据库
        conn = connect_to_db(db_info)
        
        # 列出目标数据库中的表
        existing_tables = list_tables(conn)
        
        # 加载JSON数据
        data = load_json_data(json_file)
        
        # 确定要导入的表
        tables_to_import = specific_tables or data.keys()
        
        # 检查表是否存在
        for table_name in list(tables_to_import):
            if table_name not in existing_tables:
                logger.warning(f"表 {table_name} 在目标数据库中不存在，将跳过")
                if specific_tables:
                    tables_to_import.remove(table_name)
        
        # 按表导入数据
        for table_name in tables_to_import:
            if table_name in data:
                import_table_data(conn, table_name, data[table_name])
            else:
                logger.warning(f"JSON数据中不包含表 {table_name}，跳过")
        
        # 关闭连接
        conn.close()
        
        logger.info("数据导入完成!")
        return 0
    except Exception as e:
        logger.error(f"数据导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据导入脚本 (简化版)
使用正确的SSL参数将JSON数据导入到Render PostgreSQL数据库，不使用触发器控制
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
        logging.FileHandler('render_import_simple.log')
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

def get_table_structure(conn, table_name):
    """获取表结构，用于验证列名"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = [row[0] for row in cursor.fetchall()]
        return columns
    except Exception as e:
        logger.error(f"获取表 {table_name} 结构失败: {str(e)}")
        return []

def import_table_data(conn, table_name, records):
    """导入表数据"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return
    
    try:
        logger.info(f"导入表 {table_name} 的数据，共 {len(records)} 条记录")
        
        # 清空表内容 (如果可能)
        try:
            logger.info(f"尝试清空表 {table_name}...")
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name};")
            conn.commit()
            logger.info(f"表 {table_name} 已清空")
        except Exception as e:
            conn.rollback()
            logger.warning(f"清空表 {table_name} 失败: {str(e)}，将尝试直接插入")
        
        # 获取表结构
        db_columns = get_table_structure(conn, table_name)
        if not db_columns:
            logger.warning(f"无法获取表 {table_name} 的结构，跳过")
            return
        
        cursor = conn.cursor()
        
        # 第一条记录的键作为列名
        json_columns = list(records[0].keys())
        
        # 只使用数据库中存在的列
        valid_columns = [col for col in json_columns if col.lower() in [c.lower() for c in db_columns]]
        
        if not valid_columns:
            logger.warning(f"表 {table_name} 没有有效的列匹配，跳过")
            return
        
        # 构建插入语句
        columns_str = ', '.join(valid_columns)
        values_placeholder = ', '.join(['%s'] * len(valid_columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
        
        # 按批次插入数据
        batch_size = 100
        total_records = len(records)
        processed = 0
        
        for i in range(0, total_records, batch_size):
            batch = records[i:i + batch_size]
            values = []
            
            for record in batch:
                row = [record.get(column) for column in valid_columns]
                values.append(row)
            
            try:
                psycopg2.extras.execute_batch(cursor, insert_query, values)
                conn.commit()
                processed += len(batch)
                logger.info(f"已导入 {processed}/{total_records} 条记录到表 {table_name}")
            except Exception as e:
                conn.rollback()
                logger.error(f"导入批次 {i//batch_size + 1} 失败: {str(e)}")
        
        logger.info(f"表 {table_name} 数据导入完成，成功导入 {processed}/{total_records} 条记录")
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        # 继续执行，而不是抛出异常，以便处理其他表
        logger.info(f"跳过表 {table_name} 继续导入其他表")

def list_tables(conn):
    """列出数据库中的所有表"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库中的表: {', '.join(tables)}")
        return tables
    except Exception as e:
        logger.error(f"获取表列表失败: {str(e)}")
        return []

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_to_render_simple.py <数据库URL> <JSON数据文件>")
        return 1
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    specific_tables = sys.argv[3:] if len(sys.argv) > 3 else None
    
    try:
        # 解析数据库URL
        db_info = parse_db_url(db_url)
        
        # 连接数据库
        conn = connect_to_db(db_info)
        
        # 列出目标数据库中的表
        existing_tables = list_tables(conn)
        
        # 加载JSON数据
        data = load_json_data(json_file)
        
        # 确定要导入的表
        tables_to_import = specific_tables or data.keys()
        
        # 检查表是否存在
        for table_name in list(tables_to_import):
            if table_name not in existing_tables:
                logger.warning(f"表 {table_name} 在目标数据库中不存在，将跳过")
                if specific_tables:
                    tables_to_import.remove(table_name)
        
        # 按表导入数据
        for table_name in tables_to_import:
            if table_name in data:
                import_table_data(conn, table_name, data[table_name])
            else:
                logger.warning(f"JSON数据中不包含表 {table_name}，跳过")
        
        # 关闭连接
        conn.close()
        
        logger.info("数据导入完成!")
        return 0
    except Exception as e:
        logger.error(f"数据导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据导入脚本 (简化版)
使用正确的SSL参数将JSON数据导入到Render PostgreSQL数据库，不使用触发器控制
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
        logging.FileHandler('render_import_simple.log')
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

def get_table_structure(conn, table_name):
    """获取表结构，用于验证列名"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = [row[0] for row in cursor.fetchall()]
        return columns
    except Exception as e:
        logger.error(f"获取表 {table_name} 结构失败: {str(e)}")
        return []

def import_table_data(conn, table_name, records):
    """导入表数据"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return
    
    try:
        logger.info(f"导入表 {table_name} 的数据，共 {len(records)} 条记录")
        
        # 清空表内容 (如果可能)
        try:
            logger.info(f"尝试清空表 {table_name}...")
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name};")
            conn.commit()
            logger.info(f"表 {table_name} 已清空")
        except Exception as e:
            conn.rollback()
            logger.warning(f"清空表 {table_name} 失败: {str(e)}，将尝试直接插入")
        
        # 获取表结构
        db_columns = get_table_structure(conn, table_name)
        if not db_columns:
            logger.warning(f"无法获取表 {table_name} 的结构，跳过")
            return
        
        cursor = conn.cursor()
        
        # 第一条记录的键作为列名
        json_columns = list(records[0].keys())
        
        # 只使用数据库中存在的列
        valid_columns = [col for col in json_columns if col.lower() in [c.lower() for c in db_columns]]
        
        if not valid_columns:
            logger.warning(f"表 {table_name} 没有有效的列匹配，跳过")
            return
        
        # 构建插入语句
        columns_str = ', '.join(valid_columns)
        values_placeholder = ', '.join(['%s'] * len(valid_columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
        
        # 按批次插入数据
        batch_size = 100
        total_records = len(records)
        processed = 0
        
        for i in range(0, total_records, batch_size):
            batch = records[i:i + batch_size]
            values = []
            
            for record in batch:
                row = [record.get(column) for column in valid_columns]
                values.append(row)
            
            try:
                psycopg2.extras.execute_batch(cursor, insert_query, values)
                conn.commit()
                processed += len(batch)
                logger.info(f"已导入 {processed}/{total_records} 条记录到表 {table_name}")
            except Exception as e:
                conn.rollback()
                logger.error(f"导入批次 {i//batch_size + 1} 失败: {str(e)}")
        
        logger.info(f"表 {table_name} 数据导入完成，成功导入 {processed}/{total_records} 条记录")
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        # 继续执行，而不是抛出异常，以便处理其他表
        logger.info(f"跳过表 {table_name} 继续导入其他表")

def list_tables(conn):
    """列出数据库中的所有表"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库中的表: {', '.join(tables)}")
        return tables
    except Exception as e:
        logger.error(f"获取表列表失败: {str(e)}")
        return []

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_to_render_simple.py <数据库URL> <JSON数据文件>")
        return 1
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    specific_tables = sys.argv[3:] if len(sys.argv) > 3 else None
    
    try:
        # 解析数据库URL
        db_info = parse_db_url(db_url)
        
        # 连接数据库
        conn = connect_to_db(db_info)
        
        # 列出目标数据库中的表
        existing_tables = list_tables(conn)
        
        # 加载JSON数据
        data = load_json_data(json_file)
        
        # 确定要导入的表
        tables_to_import = specific_tables or data.keys()
        
        # 检查表是否存在
        for table_name in list(tables_to_import):
            if table_name not in existing_tables:
                logger.warning(f"表 {table_name} 在目标数据库中不存在，将跳过")
                if specific_tables:
                    tables_to_import.remove(table_name)
        
        # 按表导入数据
        for table_name in tables_to_import:
            if table_name in data:
                import_table_data(conn, table_name, data[table_name])
            else:
                logger.warning(f"JSON数据中不包含表 {table_name}，跳过")
        
        # 关闭连接
        conn.close()
        
        logger.info("数据导入完成!")
        return 0
    except Exception as e:
        logger.error(f"数据导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据导入脚本 (简化版)
使用正确的SSL参数将JSON数据导入到Render PostgreSQL数据库，不使用触发器控制
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
        logging.FileHandler('render_import_simple.log')
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

def get_table_structure(conn, table_name):
    """获取表结构，用于验证列名"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = [row[0] for row in cursor.fetchall()]
        return columns
    except Exception as e:
        logger.error(f"获取表 {table_name} 结构失败: {str(e)}")
        return []

def import_table_data(conn, table_name, records):
    """导入表数据"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return
    
    try:
        logger.info(f"导入表 {table_name} 的数据，共 {len(records)} 条记录")
        
        # 清空表内容 (如果可能)
        try:
            logger.info(f"尝试清空表 {table_name}...")
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name};")
            conn.commit()
            logger.info(f"表 {table_name} 已清空")
        except Exception as e:
            conn.rollback()
            logger.warning(f"清空表 {table_name} 失败: {str(e)}，将尝试直接插入")
        
        # 获取表结构
        db_columns = get_table_structure(conn, table_name)
        if not db_columns:
            logger.warning(f"无法获取表 {table_name} 的结构，跳过")
            return
        
        cursor = conn.cursor()
        
        # 第一条记录的键作为列名
        json_columns = list(records[0].keys())
        
        # 只使用数据库中存在的列
        valid_columns = [col for col in json_columns if col.lower() in [c.lower() for c in db_columns]]
        
        if not valid_columns:
            logger.warning(f"表 {table_name} 没有有效的列匹配，跳过")
            return
        
        # 构建插入语句
        columns_str = ', '.join(valid_columns)
        values_placeholder = ', '.join(['%s'] * len(valid_columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
        
        # 按批次插入数据
        batch_size = 100
        total_records = len(records)
        processed = 0
        
        for i in range(0, total_records, batch_size):
            batch = records[i:i + batch_size]
            values = []
            
            for record in batch:
                row = [record.get(column) for column in valid_columns]
                values.append(row)
            
            try:
                psycopg2.extras.execute_batch(cursor, insert_query, values)
                conn.commit()
                processed += len(batch)
                logger.info(f"已导入 {processed}/{total_records} 条记录到表 {table_name}")
            except Exception as e:
                conn.rollback()
                logger.error(f"导入批次 {i//batch_size + 1} 失败: {str(e)}")
        
        logger.info(f"表 {table_name} 数据导入完成，成功导入 {processed}/{total_records} 条记录")
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        # 继续执行，而不是抛出异常，以便处理其他表
        logger.info(f"跳过表 {table_name} 继续导入其他表")

def list_tables(conn):
    """列出数据库中的所有表"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库中的表: {', '.join(tables)}")
        return tables
    except Exception as e:
        logger.error(f"获取表列表失败: {str(e)}")
        return []

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_to_render_simple.py <数据库URL> <JSON数据文件>")
        return 1
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    specific_tables = sys.argv[3:] if len(sys.argv) > 3 else None
    
    try:
        # 解析数据库URL
        db_info = parse_db_url(db_url)
        
        # 连接数据库
        conn = connect_to_db(db_info)
        
        # 列出目标数据库中的表
        existing_tables = list_tables(conn)
        
        # 加载JSON数据
        data = load_json_data(json_file)
        
        # 确定要导入的表
        tables_to_import = specific_tables or data.keys()
        
        # 检查表是否存在
        for table_name in list(tables_to_import):
            if table_name not in existing_tables:
                logger.warning(f"表 {table_name} 在目标数据库中不存在，将跳过")
                if specific_tables:
                    tables_to_import.remove(table_name)
        
        # 按表导入数据
        for table_name in tables_to_import:
            if table_name in data:
                import_table_data(conn, table_name, data[table_name])
            else:
                logger.warning(f"JSON数据中不包含表 {table_name}，跳过")
        
        # 关闭连接
        conn.close()
        
        logger.info("数据导入完成!")
        return 0
    except Exception as e:
        logger.error(f"数据导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 