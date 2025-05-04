#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL数据导入工具: 将导出的JSON数据导入Render数据库
增强版本: 处理SSL连接和错误重试
"""

import os
import sys
import json
import time
import logging
import argparse
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, inspect
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_import.log')
    ]
)
logger = logging.getLogger('数据导入')

# 需要跳过的表
SKIP_TABLES = ['alembic_version', 'spatial_ref_sys']

# 基础表（优先导入）
BASE_TABLES = ['users', 'permissions', 'roles', 'departments', 'dictionaries', 'regions', 
               'product_categories', 'product_subcategories']

def mask_db_url(url):
    """隐藏数据库URL中的敏感信息"""
    if not url:
        return None
    
    parsed = urlparse(url)
    if parsed.password:
        # 替换密码部分
        masked = url.replace(parsed.password, '*' * len(parsed.password))
        return masked
    return url

def fix_database_url(database_url):
    """修正数据库URL格式，处理SSL连接"""
    if not database_url:
        logger.error("未提供数据库URL")
        return None
        
    # 修正postgres://前缀
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("将 'postgres://' 替换为 'postgresql://'")
    
    # 解析URL
    parsed = urlparse(database_url)
    
    # 检查主机名，添加Render域名后缀
    host = parsed.hostname
    if host and not host.endswith('.render.com'):
        potential_host = f"{host}.oregon-postgres.render.com"
        logger.info(f"检测到Render主机名可能不完整，尝试添加域名后缀: {potential_host}")
        
        # 构建新URL
        parts = database_url.split('@')
        if len(parts) > 1:
            domain_parts = parts[1].split('/', 1)
            if len(domain_parts) > 1:
                old_domain = domain_parts[0]
                new_domain = old_domain.replace(host, potential_host)
                database_url = database_url.replace(old_domain, new_domain)
    
    # 确保URL包含SSL参数
    if '?' not in database_url:
        database_url += '?sslmode=require'
        logger.info("添加 'sslmode=require' 参数")
    elif 'sslmode=' not in database_url:
        database_url += '&sslmode=require'
        logger.info("添加 'sslmode=require' 参数")
    
    # 设置环境变量
    os.environ['PGSSLMODE'] = 'require'
    
    logger.info(f"修正后的数据库URL: {mask_db_url(database_url)}")
    return database_url

def connect_to_db(database_url, test_query="SELECT 1"):
    """连接到PostgreSQL数据库"""
    try:
        if not database_url:
            logger.error("数据库URL为空，无法连接")
            return None
        
        # 修正URL
        database_url = fix_database_url(database_url)
        
        logger.info("正在连接到Render PostgreSQL数据库...")
        
        # 创建引擎
        engine = create_engine(
            database_url,
            connect_args={
                'connect_timeout': 30,     # 增加连接超时时间
                'keepalives': 1,           # 启用保持连接
                'keepalives_idle': 30,     # 空闲连接保持间隔
                'keepalives_interval': 10, # 保持连接检查间隔
                'keepalives_count': 5      # 保持连接重试次数
            },
            pool_size=5,                  # 连接池大小
            max_overflow=10,              # 最大溢出连接数
            pool_timeout=30,              # 连接池超时
            pool_recycle=1800             # 连接回收时间(30分钟)
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text(test_query))
            row = result.fetchone()
            logger.info(f"连接测试结果: {row}")
        
        logger.info("成功连接到Render PostgreSQL数据库")
        return engine
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        return None

def load_json_data(json_file):
    """加载JSON数据文件"""
    try:
        logger.info(f"正在加载JSON数据文件: {json_file}")
        
        if not os.path.exists(json_file):
            logger.error(f"文件不存在: {json_file}")
            return None
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 显示表信息
        tables = list(data.keys())
        table_counts = {table: len(data[table]) for table in tables}
        
        logger.info(f"成功加载JSON数据，包含 {len(tables)} 个表")
        for table, count in table_counts.items():
            logger.info(f"表 {table}: {count} 条记录")
        
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        return None

def get_table_info(engine):
    """获取PostgreSQL数据库中的表信息"""
    try:
        logger.info("正在获取目标数据库表结构...")
        
        metadata = MetaData()
        metadata.reflect(bind=engine)
        inspector = inspect(engine)
        
        tables_info = {}
        for table_name in metadata.tables:
            if table_name in SKIP_TABLES:
                continue
            
            columns = inspector.get_columns(table_name)
            primary_key = inspector.get_pk_constraint(table_name)['constrained_columns']
            
            tables_info[table_name] = {
                'columns': [col['name'] for col in columns],
                'primary_key': primary_key,
                'column_types': {col['name']: col['type'] for col in columns}
            }
        
        logger.info(f"获取到 {len(tables_info)} 个表的结构信息")
        for table in list(tables_info.keys())[:5]:
            logger.info(f"表 {table}: {len(tables_info[table]['columns'])} 列")
        
        return tables_info
    except Exception as e:
        logger.error(f"获取表信息失败: {str(e)}")
        return {}

def truncate_table(engine, table_name):
    """清空表数据"""
    try:
        logger.info(f"正在清空表 {table_name}...")
        
        with engine.begin() as conn:
            try:
                # 先尝试TRUNCATE
                conn.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE'))
                logger.info(f"已清空表 {table_name} (TRUNCATE)")
            except Exception as e:
                logger.warning(f"TRUNCATE失败，尝试使用DELETE: {str(e)}")
                # 如果TRUNCATE失败，使用DELETE
                conn.execute(text(f'DELETE FROM "{table_name}"'))
                logger.info(f"已清空表 {table_name} (DELETE)")
        
        return True
    except Exception as e:
        logger.error(f"清空表 {table_name} 失败: {str(e)}")
        return False

def import_table_data(engine, table_name, table_data, table_info, retries=3):
    """导入表数据到PostgreSQL"""
    if not table_data:
        logger.warning(f"表 {table_name} 没有数据需要导入")
        return True
    
    logger.info(f"开始导入表 {table_name} 的数据 ({len(table_data)} 条记录)...")
    
    try:
        # 转换为DataFrame
        df = pd.DataFrame(table_data)
        
        # 检查列名是否匹配
        if set(df.columns) != set(table_info['columns']):
            missing_columns = set(table_info['columns']) - set(df.columns)
            extra_columns = set(df.columns) - set(table_info['columns'])
            
            if missing_columns:
                logger.warning(f"目标表缺少以下列: {missing_columns}")
                # 为缺失的列添加默认值
                for col in missing_columns:
                    df[col] = None
            
            if extra_columns:
                logger.warning(f"源数据有额外列，将被忽略: {extra_columns}")
                # 去除多余的列
                df = df[[col for col in df.columns if col in table_info['columns']]]
        
        # 检查数据是否为空
        if df.empty:
            logger.warning(f"表 {table_name} 没有有效数据")
            return True
        
        # 尝试导入数据，出错时重试
        attempt = 0
        while attempt < retries:
            try:
                # 写入数据库
                df.to_sql(
                    name=table_name,
                    con=engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=100  # 较小的批次，减少超时风险
                )
                
                logger.info(f"成功导入表 {table_name} 的数据 ({len(df)} 条记录)")
                return True
            except Exception as e:
                attempt += 1
                logger.warning(f"导入失败 (尝试 {attempt}/{retries}): {str(e)}")
                if attempt < retries:
                    # 延迟重试
                    logger.info(f"等待 {attempt * 2} 秒后重试...")
                    time.sleep(attempt * 2)
        
        logger.error(f"导入表 {table_name} 失败，已达到最大重试次数")
        return False
    except Exception as e:
        logger.error(f"导入表 {table_name} 失败: {str(e)}")
        return False

def import_data(json_data, engine, clear_tables=False, specific_tables=None):
    """导入所有数据到PostgreSQL"""
    if not json_data or not engine:
        logger.error("无法导入数据: 数据或数据库连接无效")
        return False
    
    # 获取表结构信息
    tables_info = get_table_info(engine)
    if not tables_info:
        logger.error("无法获取目标数据库表信息，终止导入")
        return False
    
    # 确定需要导入的表
    tables_to_import = []
    
    # 如果指定了特定表
    if specific_tables:
        tables_to_import = [t for t in specific_tables if t in json_data]
        logger.info(f"将导入指定的 {len(tables_to_import)} 个表")
    else:
        # 先导入基础表，再导入其他表
        for table in BASE_TABLES:
            if table in json_data and table in tables_info:
                tables_to_import.append(table)
        
        # 添加其他表
        for table in json_data:
            if table not in tables_to_import and table in tables_info:
                tables_to_import.append(table)
        
        logger.info(f"将导入 {len(tables_to_import)} 个表")
    
    # 统计
    successful_tables = 0
    failed_tables = []
    
    # 导入数据
    for table_name in tables_to_import:
        logger.info(f"处理表: {table_name}")
        
        # 如果需要清空表
        if clear_tables:
            if not truncate_table(engine, table_name):
                logger.warning(f"无法清空表 {table_name}，跳过导入")
                failed_tables.append(table_name)
                continue
        
        # 导入数据
        if import_table_data(engine, table_name, json_data[table_name], tables_info[table_name]):
            successful_tables += 1
        else:
            failed_tables.append(table_name)
    
    # 导入总结
    logger.info(f"导入完成: 成功 {successful_tables}/{len(tables_to_import)} 个表")
    
    if failed_tables:
        logger.warning(f"以下表导入失败: {', '.join(failed_tables)}")
    
    return len(failed_tables) == 0

def main():
    parser = argparse.ArgumentParser(description='Render PostgreSQL数据导入工具')
    parser.add_argument('--json-file', required=True, help='要导入的JSON数据文件')
    parser.add_argument('--db-url', help='目标PostgreSQL数据库URL')
    parser.add_argument('--clear', action='store_true', help='导入前清空表')
    parser.add_argument('--tables', help='要导入的表，用逗号分隔')
    args = parser.parse_args()
    
    # 获取数据库URL
    db_url = args.db_url or os.environ.get('RENDER_DB_URL')
    if not db_url:
        logger.error("未指定数据库URL，请使用--db-url参数或设置RENDER_DB_URL环境变量")
        return 1
    
    # 加载JSON数据
    json_data = load_json_data(args.json_file)
    if not json_data:
        return 1
    
    # 连接数据库
    engine = connect_to_db(db_url)
    if not engine:
        return 1
    
    # 处理特定表参数
    specific_tables = None
    if args.tables:
        specific_tables = [t.strip() for t in args.tables.split(',')]
        logger.info(f"指定导入表: {', '.join(specific_tables)}")
    
    # 导入数据
    success = import_data(json_data, engine, clear_tables=args.clear, specific_tables=specific_tables)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 