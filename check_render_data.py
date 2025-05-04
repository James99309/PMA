#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据库检查工具
检查数据导入结果
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('check_render_data.log')
    ]
)
logger = logging.getLogger('数据检查')

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
    """连接到数据库"""
    logger.info("连接到Render PostgreSQL数据库...")
    try:
        conn = psycopg2.connect(**db_info)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {db_version}")
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)

def check_tables(conn):
    """检查数据库中的表和记录数"""
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"数据库中的表数量: {len(tables)}")
    
    # 检查每个表中的记录数
    logger.info("各表记录数:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count} 条记录")
        except Exception as e:
            logger.error(f"  获取表 {table} 的记录数失败: {str(e)}")
    
    # 检查核心表是否有数据
    core_tables = [
        "users", "companies", "contacts", "permissions", "projects", 
        "product_categories", "products", "quotations"
    ]
    
    logger.info("核心表状态:")
    for table in core_tables:
        if table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                status = "✅ 有数据" if count > 0 else "❌ 无数据"
                logger.info(f"  {table}: {status} ({count} 条记录)")
            except Exception as e:
                logger.error(f"  获取表 {table} 的状态失败: {str(e)}")
        else:
            logger.warning(f"  {table}: ❌ 表不存在")

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python check_render_data.py <db_url>")
        sys.exit(1)
    
    db_url = sys.argv[1]
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 连接数据库
    conn = connect_to_db(db_info)
    
    # 检查数据库
    check_tables(conn)
    
    # 关闭连接
    conn.close()
    logger.info("数据检查完成!")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据库检查工具
检查数据导入结果
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('check_render_data.log')
    ]
)
logger = logging.getLogger('数据检查')

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
    """连接到数据库"""
    logger.info("连接到Render PostgreSQL数据库...")
    try:
        conn = psycopg2.connect(**db_info)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {db_version}")
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)

def check_tables(conn):
    """检查数据库中的表和记录数"""
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"数据库中的表数量: {len(tables)}")
    
    # 检查每个表中的记录数
    logger.info("各表记录数:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count} 条记录")
        except Exception as e:
            logger.error(f"  获取表 {table} 的记录数失败: {str(e)}")
    
    # 检查核心表是否有数据
    core_tables = [
        "users", "companies", "contacts", "permissions", "projects", 
        "product_categories", "products", "quotations"
    ]
    
    logger.info("核心表状态:")
    for table in core_tables:
        if table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                status = "✅ 有数据" if count > 0 else "❌ 无数据"
                logger.info(f"  {table}: {status} ({count} 条记录)")
            except Exception as e:
                logger.error(f"  获取表 {table} 的状态失败: {str(e)}")
        else:
            logger.warning(f"  {table}: ❌ 表不存在")

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python check_render_data.py <db_url>")
        sys.exit(1)
    
    db_url = sys.argv[1]
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 连接数据库
    conn = connect_to_db(db_info)
    
    # 检查数据库
    check_tables(conn)
    
    # 关闭连接
    conn.close()
    logger.info("数据检查完成!")

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据库检查工具
检查数据导入结果
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('check_render_data.log')
    ]
)
logger = logging.getLogger('数据检查')

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
    """连接到数据库"""
    logger.info("连接到Render PostgreSQL数据库...")
    try:
        conn = psycopg2.connect(**db_info)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {db_version}")
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)

def check_tables(conn):
    """检查数据库中的表和记录数"""
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"数据库中的表数量: {len(tables)}")
    
    # 检查每个表中的记录数
    logger.info("各表记录数:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count} 条记录")
        except Exception as e:
            logger.error(f"  获取表 {table} 的记录数失败: {str(e)}")
    
    # 检查核心表是否有数据
    core_tables = [
        "users", "companies", "contacts", "permissions", "projects", 
        "product_categories", "products", "quotations"
    ]
    
    logger.info("核心表状态:")
    for table in core_tables:
        if table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                status = "✅ 有数据" if count > 0 else "❌ 无数据"
                logger.info(f"  {table}: {status} ({count} 条记录)")
            except Exception as e:
                logger.error(f"  获取表 {table} 的状态失败: {str(e)}")
        else:
            logger.warning(f"  {table}: ❌ 表不存在")

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python check_render_data.py <db_url>")
        sys.exit(1)
    
    db_url = sys.argv[1]
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 连接数据库
    conn = connect_to_db(db_info)
    
    # 检查数据库
    check_tables(conn)
    
    # 关闭连接
    conn.close()
    logger.info("数据检查完成!")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据库检查工具
检查数据导入结果
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('check_render_data.log')
    ]
)
logger = logging.getLogger('数据检查')

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
    """连接到数据库"""
    logger.info("连接到Render PostgreSQL数据库...")
    try:
        conn = psycopg2.connect(**db_info)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {db_version}")
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)

def check_tables(conn):
    """检查数据库中的表和记录数"""
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"数据库中的表数量: {len(tables)}")
    
    # 检查每个表中的记录数
    logger.info("各表记录数:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count} 条记录")
        except Exception as e:
            logger.error(f"  获取表 {table} 的记录数失败: {str(e)}")
    
    # 检查核心表是否有数据
    core_tables = [
        "users", "companies", "contacts", "permissions", "projects", 
        "product_categories", "products", "quotations"
    ]
    
    logger.info("核心表状态:")
    for table in core_tables:
        if table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                status = "✅ 有数据" if count > 0 else "❌ 无数据"
                logger.info(f"  {table}: {status} ({count} 条记录)")
            except Exception as e:
                logger.error(f"  获取表 {table} 的状态失败: {str(e)}")
        else:
            logger.warning(f"  {table}: ❌ 表不存在")

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python check_render_data.py <db_url>")
        sys.exit(1)
    
    db_url = sys.argv[1]
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 连接数据库
    conn = connect_to_db(db_info)
    
    # 检查数据库
    check_tables(conn)
    
    # 关闭连接
    conn.close()
    logger.info("数据检查完成!")

if __name__ == "__main__":
    main() 
 
 