#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 顺序数据导入脚本
按照表依赖关系顺序导入数据，避免外键约束问题
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
        logging.FileHandler('render_import_ordered.log')
    ]
)
logger = logging.getLogger('Render顺序导入')

# 表依赖关系定义 - 按照正确的导入顺序排列
TABLES_ORDER = [
    "users",                    # 1. 用户表，大多数表依赖它
    "dictionaries",             # 2. 字典表，基础数据
    "companies",                # 3. 公司表
    "contacts",                 # 4. 联系人表，依赖公司表
    "permissions",              # 5. 权限表，依赖用户表
    "data_affiliations",        # 6. 数据权限表，依赖用户表
    "affiliations",             # 7. 会员表
    "product_categories",       # 8. 产品分类表
    "product_subcategories",    # 9. 产品子分类表，依赖产品分类表
    "product_regions",          # 10. 产品区域表
    "product_code_fields",      # 11. 产品代码字段表
    "product_code_field_options", # 12. 产品代码字段选项表，依赖产品代码字段表
    "product_code_field_values", # 13. 产品代码字段值表，依赖产品代码字段表和选项表
    "product_codes",            # 14. 产品代码表，依赖上述产品相关表
    "products",                 # 15. 产品表，依赖分类表和用户表
    "dev_products",             # 16. 开发产品表，依赖产品分类表
    "dev_product_specs",        # 17. 开发产品规格表，依赖开发产品表
    "projects",                 # 18. 项目表，依赖公司表和用户表
    "project_members",          # 19. 项目成员表，依赖项目表和用户表
    "quotations",               # 20. 报价单表，依赖项目表
    "quotation_details",        # 21. 报价单明细表，依赖报价单表和产品表
    "actions",                  # 22. 操作表，可能依赖多个表
    "alembic_version",          # 23. 数据库版本表
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

def truncate_table(conn, table_name):
    """清空表数据"""
    try:
        logger.info(f"清空表 {table_name}...")
        cursor = conn.cursor()
        # 禁用外键约束
        cursor.execute("SET session_replication_role = 'replica';")
        cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
        # 重新启用外键约束
        cursor.execute("SET session_replication_role = 'origin';")
        conn.commit()
        logger.info(f"表 {table_name} 已清空")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"清空表 {table_name} 失败: {str(e)}")
        logger.warning(f"尝试使用DELETE清空表 {table_name}...")
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name};")
            conn.commit()
            logger.info(f"表 {table_name} 已使用DELETE清空")
            return True
        except Exception as e2:
            conn.rollback()
            logger.error(f"使用DELETE清空表 {table_name} 也失败: {str(e2)}")
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
        
        # 按批次插入数据
        batch_size = 50
        total_records = len(records)
        processed = 0
        success = 0
        
        for i in range(0, total_records, batch_size):
            batch = records[i:i + batch_size]
            values = []
            
            for record in batch:
                row = [record.get(column) for column in valid_columns]
                values.append(row)
            
            try:
                psycopg2.extras.execute_batch(cursor, insert_query, values)
                conn.commit()
                success += len(batch)
                processed += len(batch)
                logger.info(f"已导入 {processed}/{total_records} 条记录到表 {table_name}")
            except Exception as e:
                conn.rollback()
                processed += len(batch)
                logger.error(f"导入批次 {i//batch_size + 1} 失败: {str(e)}")
                # 尝试逐条插入，跳过错误记录
                for j, record in enumerate(batch):
                    try:
                        row = [record.get(column) for column in valid_columns]
                        cursor.execute(insert_query, row)
                        conn.commit()
                        success += 1
                    except Exception as e2:
                        conn.rollback()
                        logger.error(f"批次 {i//batch_size + 1} 中第 {j+1} 条记录导入失败: {str(e2)}")
        
        logger.info(f"表 {table_name} 数据导入完成，成功导入 {success}/{total_records} 条记录")
        return success > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"导入表 {table_name} 数据失败: {str(e)}")
        return False

def import_data_in_order(conn, data, existing_tables):
    """按照定义的顺序导入数据"""
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    # 记录成功导入的表
    successful_tables = []
    failed_tables = []
    
    # 禁用外键约束
    try:
        cursor = conn.cursor()
        cursor.execute("SET session_replication_role = 'replica';")
        conn.commit()
        logger.info("已禁用外键约束进行导入")
    except Exception as e:
        logger.warning(f"无法禁用外键约束: {str(e)}，将尝试正常导入")
    
    # 按顺序导入表
    for table_name in TABLES_ORDER:
        if table_name not in existing_tables:
            logger.warning(f"表 {table_name} 在目标数据库中不存在，跳过")
            skipped_count += 1
            continue
        
        if table_name not in data:
            logger.warning(f"表 {table_name} 在JSON数据中不存在，跳过")
            skipped_count += 1
            continue
        
        # 清空表
        if not truncate_table(conn, table_name):
            logger.warning(f"无法清空表 {table_name}，将尝试直接插入")
        
        # 导入数据
        if import_table_data(conn, table_name, data[table_name]):
            success_count += 1
            successful_tables.append(table_name)
        else:
            failed_count += 1
            failed_tables.append(table_name)
    
    # 启用外键约束
    try:
        cursor = conn.cursor()
        cursor.execute("SET session_replication_role = 'origin';")
        conn.commit()
        logger.info("已重新启用外键约束")
    except Exception as e:
        logger.warning(f"无法重新启用外键约束: {str(e)}")
    
    # 处理没有在预定义顺序中的表
    other_tables = [t for t in data.keys() if t not in TABLES_ORDER]
    if other_tables:
        logger.info(f"处理剩余的 {len(other_tables)} 个表...")
        
        for table_name in other_tables:
            if table_name not in existing_tables:
                logger.warning(f"表 {table_name} 在目标数据库中不存在，跳过")
                skipped_count += 1
                continue
            
            logger.info(f"尝试导入额外表: {table_name}")
            
            # 清空表
            if not truncate_table(conn, table_name):
                logger.warning(f"无法清空表 {table_name}，将尝试直接插入")
            
            # 导入数据
            if import_table_data(conn, table_name, data[table_name]):
                success_count += 1
                successful_tables.append(table_name)
            else:
                failed_count += 1
                failed_tables.append(table_name)
    
    # 输出导入统计
    logger.info("="*50)
    logger.info("数据导入统计:")
    logger.info(f"成功导入表: {success_count}")
    logger.info(f"导入失败表: {failed_count}")
    logger.info(f"跳过的表: {skipped_count}")
    logger.info(f"成功导入的表: {', '.join(successful_tables)}")
    
    if failed_tables:
        logger.warning(f"导入失败的表: {', '.join(failed_tables)}")
    
    logger.info("="*50)
    
    return success_count, failed_count, skipped_count

def main():
    # 获取数据库URL
    if len(sys.argv) < 3:
        logger.error("用法: python import_to_render_ordered.py <数据库URL> <JSON数据文件>")
        return 1
    
    db_url = sys.argv[1]
    json_file = sys.argv[2]
    
    try:
        # 解析数据库URL
        db_info = parse_db_url(db_url)
        
        # 连接数据库
        conn = connect_to_db(db_info)
        
        # 列出目标数据库中的表
        existing_tables = list_tables(conn)
        
        # 加载JSON数据
        data = load_json_data(json_file)
        
        # 按表依赖顺序导入数据
        success_count, failed_count, skipped_count = import_data_in_order(conn, data, existing_tables)
        
        # 关闭连接
        conn.close()
        
        logger.info("数据导入完成!")
        
        # 如果有失败的表，返回非零状态码
        if failed_count > 0:
            logger.warning(f"有 {failed_count} 个表导入失败")
            return 2
        
        return 0
    
    except Exception as e:
        logger.error(f"数据导入失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 