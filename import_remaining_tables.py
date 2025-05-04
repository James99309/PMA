#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 剩余表导入工具
处理权限表导入问题
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
        logging.FileHandler('remaining_tables_import.log')
    ]
)
logger = logging.getLogger('剩余表导入')

# 专注于导入的表（按导入顺序）
FOCUS_TABLES = [
    "permissions",
    "product_code_fields",
    "product_code_field_options"
]

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
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {db_version}")
        
        # 获取所有表
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库中的表: {', '.join(tables)}")
        
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)

def load_json_data(json_file):
    """加载JSON数据文件"""
    logger.info(f"加载JSON数据文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON数据加载成功, 包含 {len(data)} 个表")
        return data
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        sys.exit(1)

def get_existing_ids(conn, table_name):
    """获取表中现有的ID列表"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table_name};")
    ids = [row[0] for row in cursor.fetchall()]
    return set(ids)

def get_column_names(conn, table_name):
    """获取表的列名"""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    return [row[0] for row in cursor.fetchall()]

def import_table_data(conn, table_name, records, existing_ids=None):
    """导入表数据，跳过已存在的记录"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return 0

    if existing_ids is None:
        existing_ids = set()
    
    # 获取表结构
    columns = get_column_names(conn, table_name)
    logger.info(f"表 {table_name} 的列: {columns}")
    
    cursor = conn.cursor()
    success_count = 0
    
    # 每批处理50条记录
    batch_size = 50
    total_records = len(records)
    
    # 过滤掉已存在ID的记录
    new_records = [r for r in records if r.get('id') not in existing_ids]
    logger.info(f"过滤后导入记录数: {len(new_records)}/{total_records}")
    
    if not new_records:
        logger.info(f"表 {table_name} 中的所有记录ID已存在，无需导入")
        return 0
    
    for i in range(0, len(new_records), batch_size):
        batch = new_records[i:i+batch_size]
        
        try:
            # 构建插入语句
            for record in batch:
                # 只包含表中存在的列
                record_filtered = {k: v for k, v in record.items() if k in columns}
                
                columns_str = ', '.join(record_filtered.keys())
                placeholders = ', '.join(['%s'] * len(record_filtered))
                
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                cursor.execute(query, list(record_filtered.values()))
                success_count += 1
                
            conn.commit()
            logger.info(f"已导入 {success_count}/{len(new_records)} 条记录到表 {table_name}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"导入批次 {i//batch_size + 1} 失败: {str(e)}")
            
            # 尝试逐个导入这批记录
            for idx, record in enumerate(batch):
                try:
                    # 只包含表中存在的列
                    record_filtered = {k: v for k, v in record.items() if k in columns}
                    
                    columns_str = ', '.join(record_filtered.keys())
                    placeholders = ', '.join(['%s'] * len(record_filtered))
                    
                    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    
                    cursor.execute(query, list(record_filtered.values()))
                    conn.commit()
                    success_count += 1
                except Exception as e2:
                    conn.rollback()
                    logger.error(f"批次 {i//batch_size + 1} 中第 {idx + 1} 条记录导入失败: {str(e2)}")
    
    return success_count

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python import_remaining_tables.py <db_url> <json_file>")
        sys.exit(1)
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 连接数据库
    conn = connect_to_db(db_info)
    
    # 加载JSON数据
    data = load_json_data(json_file)
    
    # 导入数据
    for table_name in FOCUS_TABLES:
        if table_name not in data:
            logger.warning(f"表 {table_name} 在JSON数据中不存在，跳过")
            continue
            
        logger.info(f"处理表 {table_name}...")
        
        # 获取已存在的ID
        existing_ids = get_existing_ids(conn, table_name)
        logger.info(f"表 {table_name} 中已有 {len(existing_ids)} 条记录")
        
        # 导入数据
        records = data[table_name]
        success_count = import_table_data(conn, table_name, records, existing_ids)
        logger.info(f"表 {table_name} 导入完成，成功导入 {success_count}/{len(records)} 条记录")
    
    # 关闭连接
    conn.close()
    logger.info("导入完成！")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 剩余表导入工具
处理权限表导入问题
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
        logging.FileHandler('remaining_tables_import.log')
    ]
)
logger = logging.getLogger('剩余表导入')

# 专注于导入的表（按导入顺序）
FOCUS_TABLES = [
    "permissions",
    "product_code_fields",
    "product_code_field_options"
]

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
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {db_version}")
        
        # 获取所有表
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库中的表: {', '.join(tables)}")
        
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)

def load_json_data(json_file):
    """加载JSON数据文件"""
    logger.info(f"加载JSON数据文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON数据加载成功, 包含 {len(data)} 个表")
        return data
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        sys.exit(1)

def get_existing_ids(conn, table_name):
    """获取表中现有的ID列表"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table_name};")
    ids = [row[0] for row in cursor.fetchall()]
    return set(ids)

def get_column_names(conn, table_name):
    """获取表的列名"""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    return [row[0] for row in cursor.fetchall()]

def import_table_data(conn, table_name, records, existing_ids=None):
    """导入表数据，跳过已存在的记录"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return 0

    if existing_ids is None:
        existing_ids = set()
    
    # 获取表结构
    columns = get_column_names(conn, table_name)
    logger.info(f"表 {table_name} 的列: {columns}")
    
    cursor = conn.cursor()
    success_count = 0
    
    # 每批处理50条记录
    batch_size = 50
    total_records = len(records)
    
    # 过滤掉已存在ID的记录
    new_records = [r for r in records if r.get('id') not in existing_ids]
    logger.info(f"过滤后导入记录数: {len(new_records)}/{total_records}")
    
    if not new_records:
        logger.info(f"表 {table_name} 中的所有记录ID已存在，无需导入")
        return 0
    
    for i in range(0, len(new_records), batch_size):
        batch = new_records[i:i+batch_size]
        
        try:
            # 构建插入语句
            for record in batch:
                # 只包含表中存在的列
                record_filtered = {k: v for k, v in record.items() if k in columns}
                
                columns_str = ', '.join(record_filtered.keys())
                placeholders = ', '.join(['%s'] * len(record_filtered))
                
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                cursor.execute(query, list(record_filtered.values()))
                success_count += 1
                
            conn.commit()
            logger.info(f"已导入 {success_count}/{len(new_records)} 条记录到表 {table_name}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"导入批次 {i//batch_size + 1} 失败: {str(e)}")
            
            # 尝试逐个导入这批记录
            for idx, record in enumerate(batch):
                try:
                    # 只包含表中存在的列
                    record_filtered = {k: v for k, v in record.items() if k in columns}
                    
                    columns_str = ', '.join(record_filtered.keys())
                    placeholders = ', '.join(['%s'] * len(record_filtered))
                    
                    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    
                    cursor.execute(query, list(record_filtered.values()))
                    conn.commit()
                    success_count += 1
                except Exception as e2:
                    conn.rollback()
                    logger.error(f"批次 {i//batch_size + 1} 中第 {idx + 1} 条记录导入失败: {str(e2)}")
    
    return success_count

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python import_remaining_tables.py <db_url> <json_file>")
        sys.exit(1)
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 连接数据库
    conn = connect_to_db(db_info)
    
    # 加载JSON数据
    data = load_json_data(json_file)
    
    # 导入数据
    for table_name in FOCUS_TABLES:
        if table_name not in data:
            logger.warning(f"表 {table_name} 在JSON数据中不存在，跳过")
            continue
            
        logger.info(f"处理表 {table_name}...")
        
        # 获取已存在的ID
        existing_ids = get_existing_ids(conn, table_name)
        logger.info(f"表 {table_name} 中已有 {len(existing_ids)} 条记录")
        
        # 导入数据
        records = data[table_name]
        success_count = import_table_data(conn, table_name, records, existing_ids)
        logger.info(f"表 {table_name} 导入完成，成功导入 {success_count}/{len(records)} 条记录")
    
    # 关闭连接
    conn.close()
    logger.info("导入完成！")

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 剩余表导入工具
处理权限表导入问题
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
        logging.FileHandler('remaining_tables_import.log')
    ]
)
logger = logging.getLogger('剩余表导入')

# 专注于导入的表（按导入顺序）
FOCUS_TABLES = [
    "permissions",
    "product_code_fields",
    "product_code_field_options"
]

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
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {db_version}")
        
        # 获取所有表
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库中的表: {', '.join(tables)}")
        
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)

def load_json_data(json_file):
    """加载JSON数据文件"""
    logger.info(f"加载JSON数据文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON数据加载成功, 包含 {len(data)} 个表")
        return data
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        sys.exit(1)

def get_existing_ids(conn, table_name):
    """获取表中现有的ID列表"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table_name};")
    ids = [row[0] for row in cursor.fetchall()]
    return set(ids)

def get_column_names(conn, table_name):
    """获取表的列名"""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    return [row[0] for row in cursor.fetchall()]

def import_table_data(conn, table_name, records, existing_ids=None):
    """导入表数据，跳过已存在的记录"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return 0

    if existing_ids is None:
        existing_ids = set()
    
    # 获取表结构
    columns = get_column_names(conn, table_name)
    logger.info(f"表 {table_name} 的列: {columns}")
    
    cursor = conn.cursor()
    success_count = 0
    
    # 每批处理50条记录
    batch_size = 50
    total_records = len(records)
    
    # 过滤掉已存在ID的记录
    new_records = [r for r in records if r.get('id') not in existing_ids]
    logger.info(f"过滤后导入记录数: {len(new_records)}/{total_records}")
    
    if not new_records:
        logger.info(f"表 {table_name} 中的所有记录ID已存在，无需导入")
        return 0
    
    for i in range(0, len(new_records), batch_size):
        batch = new_records[i:i+batch_size]
        
        try:
            # 构建插入语句
            for record in batch:
                # 只包含表中存在的列
                record_filtered = {k: v for k, v in record.items() if k in columns}
                
                columns_str = ', '.join(record_filtered.keys())
                placeholders = ', '.join(['%s'] * len(record_filtered))
                
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                cursor.execute(query, list(record_filtered.values()))
                success_count += 1
                
            conn.commit()
            logger.info(f"已导入 {success_count}/{len(new_records)} 条记录到表 {table_name}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"导入批次 {i//batch_size + 1} 失败: {str(e)}")
            
            # 尝试逐个导入这批记录
            for idx, record in enumerate(batch):
                try:
                    # 只包含表中存在的列
                    record_filtered = {k: v for k, v in record.items() if k in columns}
                    
                    columns_str = ', '.join(record_filtered.keys())
                    placeholders = ', '.join(['%s'] * len(record_filtered))
                    
                    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    
                    cursor.execute(query, list(record_filtered.values()))
                    conn.commit()
                    success_count += 1
                except Exception as e2:
                    conn.rollback()
                    logger.error(f"批次 {i//batch_size + 1} 中第 {idx + 1} 条记录导入失败: {str(e2)}")
    
    return success_count

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python import_remaining_tables.py <db_url> <json_file>")
        sys.exit(1)
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 连接数据库
    conn = connect_to_db(db_info)
    
    # 加载JSON数据
    data = load_json_data(json_file)
    
    # 导入数据
    for table_name in FOCUS_TABLES:
        if table_name not in data:
            logger.warning(f"表 {table_name} 在JSON数据中不存在，跳过")
            continue
            
        logger.info(f"处理表 {table_name}...")
        
        # 获取已存在的ID
        existing_ids = get_existing_ids(conn, table_name)
        logger.info(f"表 {table_name} 中已有 {len(existing_ids)} 条记录")
        
        # 导入数据
        records = data[table_name]
        success_count = import_table_data(conn, table_name, records, existing_ids)
        logger.info(f"表 {table_name} 导入完成，成功导入 {success_count}/{len(records)} 条记录")
    
    # 关闭连接
    conn.close()
    logger.info("导入完成！")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 剩余表导入工具
处理权限表导入问题
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
        logging.FileHandler('remaining_tables_import.log')
    ]
)
logger = logging.getLogger('剩余表导入')

# 专注于导入的表（按导入顺序）
FOCUS_TABLES = [
    "permissions",
    "product_code_fields",
    "product_code_field_options"
]

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
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {db_version}")
        
        # 获取所有表
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"数据库中的表: {', '.join(tables)}")
        
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)

def load_json_data(json_file):
    """加载JSON数据文件"""
    logger.info(f"加载JSON数据文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON数据加载成功, 包含 {len(data)} 个表")
        return data
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        sys.exit(1)

def get_existing_ids(conn, table_name):
    """获取表中现有的ID列表"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {table_name};")
    ids = [row[0] for row in cursor.fetchall()]
    return set(ids)

def get_column_names(conn, table_name):
    """获取表的列名"""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    return [row[0] for row in cursor.fetchall()]

def import_table_data(conn, table_name, records, existing_ids=None):
    """导入表数据，跳过已存在的记录"""
    if not records:
        logger.info(f"表 {table_name} 没有数据，跳过")
        return 0

    if existing_ids is None:
        existing_ids = set()
    
    # 获取表结构
    columns = get_column_names(conn, table_name)
    logger.info(f"表 {table_name} 的列: {columns}")
    
    cursor = conn.cursor()
    success_count = 0
    
    # 每批处理50条记录
    batch_size = 50
    total_records = len(records)
    
    # 过滤掉已存在ID的记录
    new_records = [r for r in records if r.get('id') not in existing_ids]
    logger.info(f"过滤后导入记录数: {len(new_records)}/{total_records}")
    
    if not new_records:
        logger.info(f"表 {table_name} 中的所有记录ID已存在，无需导入")
        return 0
    
    for i in range(0, len(new_records), batch_size):
        batch = new_records[i:i+batch_size]
        
        try:
            # 构建插入语句
            for record in batch:
                # 只包含表中存在的列
                record_filtered = {k: v for k, v in record.items() if k in columns}
                
                columns_str = ', '.join(record_filtered.keys())
                placeholders = ', '.join(['%s'] * len(record_filtered))
                
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                cursor.execute(query, list(record_filtered.values()))
                success_count += 1
                
            conn.commit()
            logger.info(f"已导入 {success_count}/{len(new_records)} 条记录到表 {table_name}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"导入批次 {i//batch_size + 1} 失败: {str(e)}")
            
            # 尝试逐个导入这批记录
            for idx, record in enumerate(batch):
                try:
                    # 只包含表中存在的列
                    record_filtered = {k: v for k, v in record.items() if k in columns}
                    
                    columns_str = ', '.join(record_filtered.keys())
                    placeholders = ', '.join(['%s'] * len(record_filtered))
                    
                    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    
                    cursor.execute(query, list(record_filtered.values()))
                    conn.commit()
                    success_count += 1
                except Exception as e2:
                    conn.rollback()
                    logger.error(f"批次 {i//batch_size + 1} 中第 {idx + 1} 条记录导入失败: {str(e2)}")
    
    return success_count

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python import_remaining_tables.py <db_url> <json_file>")
        sys.exit(1)
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 连接数据库
    conn = connect_to_db(db_info)
    
    # 加载JSON数据
    data = load_json_data(json_file)
    
    # 导入数据
    for table_name in FOCUS_TABLES:
        if table_name not in data:
            logger.warning(f"表 {table_name} 在JSON数据中不存在，跳过")
            continue
            
        logger.info(f"处理表 {table_name}...")
        
        # 获取已存在的ID
        existing_ids = get_existing_ids(conn, table_name)
        logger.info(f"表 {table_name} 中已有 {len(existing_ids)} 条记录")
        
        # 导入数据
        records = data[table_name]
        success_count = import_table_data(conn, table_name, records, existing_ids)
        logger.info(f"表 {table_name} 导入完成，成功导入 {success_count}/{len(records)} 条记录")
    
    # 关闭连接
    conn.close()
    logger.info("导入完成！")

if __name__ == "__main__":
    main() 
 
 