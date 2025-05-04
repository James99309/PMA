#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite数据导出工具: 导出数据库中的所有表结构和数据
"""

import os
import sys
import json
import sqlite3
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据导出')

def get_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    cursor.close()
    return tables

def get_table_schema(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    cursor.close()
    
    columns = []
    for col in schema:
        columns.append({
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': col[3],
            'default': col[4],
            'pk': col[5]
        })
    
    return columns

def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))
    
    cursor.close()
    return data

def export_database(db_path, output_file):
    """导出整个数据库"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 获取所有表
        tables = get_tables(conn)
        logger.info(f"找到 {len(tables)} 个表")
        
        # 导出结果
        db_export = {}
        
        # 导出表结构和数据
        for table_name in tables:
            logger.info(f"导出表 {table_name}")
            
            # 获取表结构
            schema = get_table_schema(conn, table_name)
            
            # 获取表数据
            data = get_table_data(conn, table_name)
            
            # 添加到导出结果
            db_export[table_name] = data
            
            logger.info(f"表 {table_name} 导出完成，共 {len(data)} 条记录")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(db_export, f, ensure_ascii=False, indent=2)
        
        conn.close()
        logger.info(f"数据库导出完成，已保存到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"导出数据库失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='SQLite数据导出工具')
    parser.add_argument('--db', default='app.db', help='SQLite数据库文件路径')
    parser.add_argument('--output', default='db_export.json', help='导出的JSON文件路径')
    args = parser.parse_args()
    
    logger.info("=== 开始导出数据库 ===")
    
    # 检查数据库文件是否存在
    if not os.path.exists(args.db):
        logger.error(f"数据库文件 {args.db} 不存在")
        return 1
    
    # 导出数据库
    success = export_database(args.db, args.output)
    
    logger.info("=== 数据库导出结束 ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
SQLite数据导出工具: 导出数据库中的所有表结构和数据
"""

import os
import sys
import json
import sqlite3
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据导出')

def get_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    cursor.close()
    return tables

def get_table_schema(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    cursor.close()
    
    columns = []
    for col in schema:
        columns.append({
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': col[3],
            'default': col[4],
            'pk': col[5]
        })
    
    return columns

def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))
    
    cursor.close()
    return data

def export_database(db_path, output_file):
    """导出整个数据库"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 获取所有表
        tables = get_tables(conn)
        logger.info(f"找到 {len(tables)} 个表")
        
        # 导出结果
        db_export = {}
        
        # 导出表结构和数据
        for table_name in tables:
            logger.info(f"导出表 {table_name}")
            
            # 获取表结构
            schema = get_table_schema(conn, table_name)
            
            # 获取表数据
            data = get_table_data(conn, table_name)
            
            # 添加到导出结果
            db_export[table_name] = data
            
            logger.info(f"表 {table_name} 导出完成，共 {len(data)} 条记录")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(db_export, f, ensure_ascii=False, indent=2)
        
        conn.close()
        logger.info(f"数据库导出完成，已保存到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"导出数据库失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='SQLite数据导出工具')
    parser.add_argument('--db', default='app.db', help='SQLite数据库文件路径')
    parser.add_argument('--output', default='db_export.json', help='导出的JSON文件路径')
    args = parser.parse_args()
    
    logger.info("=== 开始导出数据库 ===")
    
    # 检查数据库文件是否存在
    if not os.path.exists(args.db):
        logger.error(f"数据库文件 {args.db} 不存在")
        return 1
    
    # 导出数据库
    success = export_database(args.db, args.output)
    
    logger.info("=== 数据库导出结束 ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
SQLite数据导出工具: 导出数据库中的所有表结构和数据
"""

import os
import sys
import json
import sqlite3
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据导出')

def get_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    cursor.close()
    return tables

def get_table_schema(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    cursor.close()
    
    columns = []
    for col in schema:
        columns.append({
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': col[3],
            'default': col[4],
            'pk': col[5]
        })
    
    return columns

def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))
    
    cursor.close()
    return data

def export_database(db_path, output_file):
    """导出整个数据库"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 获取所有表
        tables = get_tables(conn)
        logger.info(f"找到 {len(tables)} 个表")
        
        # 导出结果
        db_export = {}
        
        # 导出表结构和数据
        for table_name in tables:
            logger.info(f"导出表 {table_name}")
            
            # 获取表结构
            schema = get_table_schema(conn, table_name)
            
            # 获取表数据
            data = get_table_data(conn, table_name)
            
            # 添加到导出结果
            db_export[table_name] = data
            
            logger.info(f"表 {table_name} 导出完成，共 {len(data)} 条记录")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(db_export, f, ensure_ascii=False, indent=2)
        
        conn.close()
        logger.info(f"数据库导出完成，已保存到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"导出数据库失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='SQLite数据导出工具')
    parser.add_argument('--db', default='app.db', help='SQLite数据库文件路径')
    parser.add_argument('--output', default='db_export.json', help='导出的JSON文件路径')
    args = parser.parse_args()
    
    logger.info("=== 开始导出数据库 ===")
    
    # 检查数据库文件是否存在
    if not os.path.exists(args.db):
        logger.error(f"数据库文件 {args.db} 不存在")
        return 1
    
    # 导出数据库
    success = export_database(args.db, args.output)
    
    logger.info("=== 数据库导出结束 ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
SQLite数据导出工具: 导出数据库中的所有表结构和数据
"""

import os
import sys
import json
import sqlite3
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据导出')

def get_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    cursor.close()
    return tables

def get_table_schema(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    cursor.close()
    
    columns = []
    for col in schema:
        columns.append({
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': col[3],
            'default': col[4],
            'pk': col[5]
        })
    
    return columns

def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))
    
    cursor.close()
    return data

def export_database(db_path, output_file):
    """导出整个数据库"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 获取所有表
        tables = get_tables(conn)
        logger.info(f"找到 {len(tables)} 个表")
        
        # 导出结果
        db_export = {}
        
        # 导出表结构和数据
        for table_name in tables:
            logger.info(f"导出表 {table_name}")
            
            # 获取表结构
            schema = get_table_schema(conn, table_name)
            
            # 获取表数据
            data = get_table_data(conn, table_name)
            
            # 添加到导出结果
            db_export[table_name] = data
            
            logger.info(f"表 {table_name} 导出完成，共 {len(data)} 条记录")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(db_export, f, ensure_ascii=False, indent=2)
        
        conn.close()
        logger.info(f"数据库导出完成，已保存到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"导出数据库失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='SQLite数据导出工具')
    parser.add_argument('--db', default='app.db', help='SQLite数据库文件路径')
    parser.add_argument('--output', default='db_export.json', help='导出的JSON文件路径')
    args = parser.parse_args()
    
    logger.info("=== 开始导出数据库 ===")
    
    # 检查数据库文件是否存在
    if not os.path.exists(args.db):
        logger.error(f"数据库文件 {args.db} 不存在")
        return 1
    
    # 导出数据库
    success = export_database(args.db, args.output)
    
    logger.info("=== 数据库导出结束 ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 