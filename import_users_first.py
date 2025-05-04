#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 用户表导入脚本
专门用于先导入用户表，解决外键依赖问题
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
        logging.FileHandler('users_import.log')
    ]
)
logger = logging.getLogger('用户表导入')

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
        
        logger.info(f"JSON数据加载成功")
        return data
    except Exception as e:
        logger.error(f"JSON数据加载失败: {str(e)}")
        raise

def get_table_structure(conn, table_name):
    """获取表结构"""
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

def truncate_table(conn, table_name):
    """清空表数据"""
    try:
        logger.info(f"清空表 {table_name}...")
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name};")
        conn.commit()
        logger.info(f"表 {table_name} 已清空")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"清空表 {table_name} 失败: {str(e)}")
        return False

def import_table_data(conn, table_name, records):
    """导入表数据"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return True
    
    try:
        logger.info(f"导入表 {table_name} 的数据，共 {len(records)} 条记录")
        
        # 获取表结构
        db_columns = get_table_structure(conn, table_name)
        if not db_columns:
            logger.warning(f"无法获取表 {table_name} 的结构，跳过")
            return False
        
        cursor = conn.cursor()
        
        # 获取JSON记录的列名
        json_columns = list(records[0].keys())
        
        # 只使用数据库中存在的列
        valid_columns = [col for col in json_columns if col.lower() in [c.lower() for c in db_columns]]
        
        if not valid_columns:
            logger.warning(f"表 {table_name} 没有有效的列匹配，跳过")
            return False
        
        # 构建插入语句
        columns_str = ', '.join(valid_columns)
        values_placeholder = ', '.join(['%s'] * len(valid_columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
        
        # 逐条插入数据
        success = 0
        for i, record in enumerate(records):
            try:
                row = [record.get(column) for column in valid_columns]
                cursor.execute(insert_query, row)
                conn.commit()
                success += 1
                if (i+1) % 10 == 0 or i+1 == len(records):
                    logger.info(f"已导入 {i+1}/{len(records)} 条记录到表 {table_name}")
            except Exception as e:
                conn.rollback()
                logger.error(f"记录 {i+1} 导入失败: {str(e)}")
                logger.error(f"问题记录: {record}")
        
        logger.info(f"表 {table_name} 数据导入完成，成功导入 {success}/{len(records)} 条记录")
        return success > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        return False

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_users_first.py <数据库URL> <JSON数据文件>")
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
        
        # 只导入用户表
        if 'users' in data:
            # 清空用户表
            if truncate_table(conn, 'users'):
                # 导入用户表数据
                import_table_data(conn, 'users', data['users'])
            else:
                logger.error("无法清空用户表，中止导入")
                return 1
        else:
            logger.error("JSON数据中不包含用户表数据")
            return 1
        
        # 导入字典表
        if 'dictionaries' in data:
            if truncate_table(conn, 'dictionaries'):
                import_table_data(conn, 'dictionaries', data['dictionaries'])
        
        # 关闭连接
        conn.close()
        
        logger.info("用户表导入完成!")
        return 0
    
    except Exception as e:
        logger.error(f"导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 用户表导入脚本
专门用于先导入用户表，解决外键依赖问题
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
        logging.FileHandler('users_import.log')
    ]
)
logger = logging.getLogger('用户表导入')

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
        
        logger.info(f"JSON数据加载成功")
        return data
    except Exception as e:
        logger.error(f"JSON数据加载失败: {str(e)}")
        raise

def get_table_structure(conn, table_name):
    """获取表结构"""
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

def truncate_table(conn, table_name):
    """清空表数据"""
    try:
        logger.info(f"清空表 {table_name}...")
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name};")
        conn.commit()
        logger.info(f"表 {table_name} 已清空")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"清空表 {table_name} 失败: {str(e)}")
        return False

def import_table_data(conn, table_name, records):
    """导入表数据"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return True
    
    try:
        logger.info(f"导入表 {table_name} 的数据，共 {len(records)} 条记录")
        
        # 获取表结构
        db_columns = get_table_structure(conn, table_name)
        if not db_columns:
            logger.warning(f"无法获取表 {table_name} 的结构，跳过")
            return False
        
        cursor = conn.cursor()
        
        # 获取JSON记录的列名
        json_columns = list(records[0].keys())
        
        # 只使用数据库中存在的列
        valid_columns = [col for col in json_columns if col.lower() in [c.lower() for c in db_columns]]
        
        if not valid_columns:
            logger.warning(f"表 {table_name} 没有有效的列匹配，跳过")
            return False
        
        # 构建插入语句
        columns_str = ', '.join(valid_columns)
        values_placeholder = ', '.join(['%s'] * len(valid_columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
        
        # 逐条插入数据
        success = 0
        for i, record in enumerate(records):
            try:
                row = [record.get(column) for column in valid_columns]
                cursor.execute(insert_query, row)
                conn.commit()
                success += 1
                if (i+1) % 10 == 0 or i+1 == len(records):
                    logger.info(f"已导入 {i+1}/{len(records)} 条记录到表 {table_name}")
            except Exception as e:
                conn.rollback()
                logger.error(f"记录 {i+1} 导入失败: {str(e)}")
                logger.error(f"问题记录: {record}")
        
        logger.info(f"表 {table_name} 数据导入完成，成功导入 {success}/{len(records)} 条记录")
        return success > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        return False

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_users_first.py <数据库URL> <JSON数据文件>")
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
        
        # 只导入用户表
        if 'users' in data:
            # 清空用户表
            if truncate_table(conn, 'users'):
                # 导入用户表数据
                import_table_data(conn, 'users', data['users'])
            else:
                logger.error("无法清空用户表，中止导入")
                return 1
        else:
            logger.error("JSON数据中不包含用户表数据")
            return 1
        
        # 导入字典表
        if 'dictionaries' in data:
            if truncate_table(conn, 'dictionaries'):
                import_table_data(conn, 'dictionaries', data['dictionaries'])
        
        # 关闭连接
        conn.close()
        
        logger.info("用户表导入完成!")
        return 0
    
    except Exception as e:
        logger.error(f"导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 用户表导入脚本
专门用于先导入用户表，解决外键依赖问题
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
        logging.FileHandler('users_import.log')
    ]
)
logger = logging.getLogger('用户表导入')

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
        
        logger.info(f"JSON数据加载成功")
        return data
    except Exception as e:
        logger.error(f"JSON数据加载失败: {str(e)}")
        raise

def get_table_structure(conn, table_name):
    """获取表结构"""
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

def truncate_table(conn, table_name):
    """清空表数据"""
    try:
        logger.info(f"清空表 {table_name}...")
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name};")
        conn.commit()
        logger.info(f"表 {table_name} 已清空")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"清空表 {table_name} 失败: {str(e)}")
        return False

def import_table_data(conn, table_name, records):
    """导入表数据"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return True
    
    try:
        logger.info(f"导入表 {table_name} 的数据，共 {len(records)} 条记录")
        
        # 获取表结构
        db_columns = get_table_structure(conn, table_name)
        if not db_columns:
            logger.warning(f"无法获取表 {table_name} 的结构，跳过")
            return False
        
        cursor = conn.cursor()
        
        # 获取JSON记录的列名
        json_columns = list(records[0].keys())
        
        # 只使用数据库中存在的列
        valid_columns = [col for col in json_columns if col.lower() in [c.lower() for c in db_columns]]
        
        if not valid_columns:
            logger.warning(f"表 {table_name} 没有有效的列匹配，跳过")
            return False
        
        # 构建插入语句
        columns_str = ', '.join(valid_columns)
        values_placeholder = ', '.join(['%s'] * len(valid_columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
        
        # 逐条插入数据
        success = 0
        for i, record in enumerate(records):
            try:
                row = [record.get(column) for column in valid_columns]
                cursor.execute(insert_query, row)
                conn.commit()
                success += 1
                if (i+1) % 10 == 0 or i+1 == len(records):
                    logger.info(f"已导入 {i+1}/{len(records)} 条记录到表 {table_name}")
            except Exception as e:
                conn.rollback()
                logger.error(f"记录 {i+1} 导入失败: {str(e)}")
                logger.error(f"问题记录: {record}")
        
        logger.info(f"表 {table_name} 数据导入完成，成功导入 {success}/{len(records)} 条记录")
        return success > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        return False

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_users_first.py <数据库URL> <JSON数据文件>")
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
        
        # 只导入用户表
        if 'users' in data:
            # 清空用户表
            if truncate_table(conn, 'users'):
                # 导入用户表数据
                import_table_data(conn, 'users', data['users'])
            else:
                logger.error("无法清空用户表，中止导入")
                return 1
        else:
            logger.error("JSON数据中不包含用户表数据")
            return 1
        
        # 导入字典表
        if 'dictionaries' in data:
            if truncate_table(conn, 'dictionaries'):
                import_table_data(conn, 'dictionaries', data['dictionaries'])
        
        # 关闭连接
        conn.close()
        
        logger.info("用户表导入完成!")
        return 0
    
    except Exception as e:
        logger.error(f"导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 用户表导入脚本
专门用于先导入用户表，解决外键依赖问题
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
        logging.FileHandler('users_import.log')
    ]
)
logger = logging.getLogger('用户表导入')

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
        
        logger.info(f"JSON数据加载成功")
        return data
    except Exception as e:
        logger.error(f"JSON数据加载失败: {str(e)}")
        raise

def get_table_structure(conn, table_name):
    """获取表结构"""
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

def truncate_table(conn, table_name):
    """清空表数据"""
    try:
        logger.info(f"清空表 {table_name}...")
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name};")
        conn.commit()
        logger.info(f"表 {table_name} 已清空")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"清空表 {table_name} 失败: {str(e)}")
        return False

def import_table_data(conn, table_name, records):
    """导入表数据"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return True
    
    try:
        logger.info(f"导入表 {table_name} 的数据，共 {len(records)} 条记录")
        
        # 获取表结构
        db_columns = get_table_structure(conn, table_name)
        if not db_columns:
            logger.warning(f"无法获取表 {table_name} 的结构，跳过")
            return False
        
        cursor = conn.cursor()
        
        # 获取JSON记录的列名
        json_columns = list(records[0].keys())
        
        # 只使用数据库中存在的列
        valid_columns = [col for col in json_columns if col.lower() in [c.lower() for c in db_columns]]
        
        if not valid_columns:
            logger.warning(f"表 {table_name} 没有有效的列匹配，跳过")
            return False
        
        # 构建插入语句
        columns_str = ', '.join(valid_columns)
        values_placeholder = ', '.join(['%s'] * len(valid_columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
        
        # 逐条插入数据
        success = 0
        for i, record in enumerate(records):
            try:
                row = [record.get(column) for column in valid_columns]
                cursor.execute(insert_query, row)
                conn.commit()
                success += 1
                if (i+1) % 10 == 0 or i+1 == len(records):
                    logger.info(f"已导入 {i+1}/{len(records)} 条记录到表 {table_name}")
            except Exception as e:
                conn.rollback()
                logger.error(f"记录 {i+1} 导入失败: {str(e)}")
                logger.error(f"问题记录: {record}")
        
        logger.info(f"表 {table_name} 数据导入完成，成功导入 {success}/{len(records)} 条记录")
        return success > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        return False

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_users_first.py <数据库URL> <JSON数据文件>")
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
        
        # 只导入用户表
        if 'users' in data:
            # 清空用户表
            if truncate_table(conn, 'users'):
                # 导入用户表数据
                import_table_data(conn, 'users', data['users'])
            else:
                logger.error("无法清空用户表，中止导入")
                return 1
        else:
            logger.error("JSON数据中不包含用户表数据")
            return 1
        
        # 导入字典表
        if 'dictionaries' in data:
            if truncate_table(conn, 'dictionaries'):
                import_table_data(conn, 'dictionaries', data['dictionaries'])
        
        # 关闭连接
        conn.close()
        
        logger.info("用户表导入完成!")
        return 0
    
    except Exception as e:
        logger.error(f"导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 