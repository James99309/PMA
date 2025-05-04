#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移工具: 将本地SQLite数据迁移到Render的PostgreSQL数据库
增强版本：提供详细的诊断和错误处理功能
"""

import os
import sys
import json
import logging
import argparse
import traceback
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from urllib.parse import urlparse

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('db_migration.log')
    ]
)
logger = logging.getLogger('数据库迁移')

# 需要跳过的表
SKIP_TABLES = ['alembic_version']
# 基础表（优先迁移）
BASE_TABLES = ['users', 'permissions', 'departments', 'dictionaries', 'regions', 
               'product_categories', 'product_subcategories']

def fix_database_url(database_url):
    """修正数据库URL格式"""
    if not database_url:
        logger.error("未提供数据库URL")
        return None
        
    logger.info(f"处理数据库URL: {database_url[:10]}...")
    
    # 隐藏敏感信息
    parsed = urlparse(database_url)
    if parsed.password:
        masked_url = database_url.replace(parsed.password, '********')
        logger.info(f"数据库URL格式: {masked_url[:20]}...")
    
    if database_url.startswith('postgres://'):
        fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已将postgres://转换为postgresql://")
        return fixed_url
        
    return database_url

def connect_to_db(database_url, test_query="SELECT 1"):
    """连接到数据库并进行测试"""
    try:
        if not database_url:
            logger.error("数据库URL为空，无法连接")
            return None
            
        logger.info("正在连接到数据库...")
        
        # 修正URL格式
        database_url = fix_database_url(database_url)
        
        # 解析URL
        parsed = urlparse(database_url)
        is_postgres = parsed.scheme in ('postgresql', 'postgres')
        
        # 对PostgreSQL添加SSL参数
        if is_postgres:
            # 检查URL中是否包含SSL参数
            if '?' not in database_url:
                database_url += '?sslmode=require'
            elif 'sslmode=' not in database_url:
                database_url += '&sslmode=require'
                
            logger.info(f"使用带SSL参数的URL连接")
            
            # 设置环境变量
            os.environ['PGSSLMODE'] = 'require'
            
            # 使用正确的主机名
            host = parsed.hostname
            if host and not host.endswith('.render.com'):
                potential_host = f"{host}.oregon-postgres.render.com"
                logger.info(f"Render主机名不完整，尝试使用完整主机名: {potential_host}")
                # 构建新URL
                parts = database_url.split('@')
                if len(parts) > 1:
                    domain_parts = parts[1].split('/', 1)
                    if len(domain_parts) > 1:
                        old_domain = domain_parts[0]
                        new_domain = old_domain.replace(host, potential_host)
                        database_url = database_url.replace(old_domain, new_domain)
                        logger.info(f"更新后的URL: {database_url[:10]}...")
        
        # 创建引擎时添加更多连接参数
        connect_args = {
            'connect_timeout': 30,  # 增加连接超时时间
            'keepalives': 1,        # 启用保持连接
            'keepalives_idle': 30,  # 空闲连接保持间隔
            'keepalives_interval': 10,  # 保持连接检查间隔
            'keepalives_count': 5   # 保持连接重试次数
        }
            
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_size=5,                # 连接池大小
            max_overflow=10,            # 最大溢出连接数
            pool_timeout=30,            # 连接池超时
            pool_recycle=1800           # 连接回收时间(30分钟)
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text(test_query))
            row = result.fetchone()
            logger.info(f"连接测试结果: {row}")
            
        logger.info(f"成功连接到数据库")
        return engine
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        traceback.print_exc()
        return None

def load_json_data(json_file):
    """加载导出的JSON数据"""
    try:
        if not os.path.exists(json_file):
            logger.error(f"JSON文件不存在: {json_file}")
            return None
            
        logger.info(f"加载JSON文件: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        tables = list(data.keys())
        logger.info(f"成功加载JSON数据，包含 {len(data)} 个表: {', '.join(tables[:5])}...")
        
        # 显示一些基本统计信息
        for table_name in data:
            count = len(data[table_name])
            if count > 0:
                logger.info(f"表 {table_name}: {count} 条记录")
                
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        traceback.print_exc()
        return None

def get_table_info(engine):
    """获取目标数据库中的表信息"""
    try:
        if not engine:
            logger.error("无法获取表信息：数据库引擎为空")
            return {}
            
        logger.info("获取目标数据库表结构...")
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
                'primary_key': primary_key
            }
        
        logger.info(f"获取到目标数据库中的 {len(tables_info)} 个表")
        for table_name, info in list(tables_info.items())[:5]:
            logger.info(f"表 {table_name}: {len(info['columns'])} 列")
            
        return tables_info
    except Exception as e:
        logger.error(f"获取表信息失败: {str(e)}")
        traceback.print_exc()
        return {}

def truncate_table(engine, table_name):
    """清空表数据"""
    try:
        with engine.begin() as conn:
            conn.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE'))
        logger.info(f"已清空表 {table_name}")
        return True
    except Exception as e:
        logger.error(f"清空表 {table_name} 失败: {str(e)}")
        logger.info("尝试使用DELETE语句清空表...")
        try:
            with engine.begin() as conn:
                conn.execute(text(f'DELETE FROM "{table_name}"'))
            logger.info(f"已使用DELETE清空表 {table_name}")
            return True
        except Exception as e2:
            logger.error(f"DELETE清空表失败: {str(e2)}")
            return False

def migrate_table_data(engine, table_name, table_data, table_info):
    """迁移单个表的数据"""
    if not table_data:
        logger.warning(f"表 {table_name} 没有数据需要迁移")
        return True
    
    try:
        # 将数据转换为DataFrame
        df = pd.DataFrame(table_data)
        
        # 检查列名是否匹配
        if set(df.columns) != set(table_info['columns']):
            missing_columns = set(table_info['columns']) - set(df.columns)
            extra_columns = set(df.columns) - set(table_info['columns'])
            
            if missing_columns:
                logger.warning(f"目标表缺少以下列: {missing_columns}")
            
            if extra_columns:
                logger.warning(f"源数据有额外列: {extra_columns}")
        
        # 过滤掉目标表中不存在的列
        valid_columns = [col for col in df.columns if col in table_info['columns']]
        if len(valid_columns) < len(df.columns):
            logger.warning(f"过滤掉 {len(df.columns) - len(valid_columns)} 个无效列")
            
        df = df[valid_columns]
        
        # 检查是否为空
        if df.empty:
            logger.warning(f"过滤后表 {table_name} 无有效数据")
            return True
        
        # 写入数据库
        logger.info(f"开始将 {len(df)} 条记录写入表 {table_name}")
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=500  # 分批处理，避免大表问题
        )
        
        logger.info(f"成功迁移表 {table_name} 的数据，共 {len(table_data)} 条记录")
        return True
    except Exception as e:
        logger.error(f"迁移表 {table_name} 失败: {str(e)}")
        traceback.print_exc()
        return False

def migrate_data(source_data, target_engine, specific_tables=None):
    """迁移所有表数据"""
    # 获取目标数据库表信息
    tables_info = get_table_info(target_engine)
    if not tables_info:
        logger.error("无法获取目标数据库表信息，终止迁移")
        return False
    
    # 统计
    total_tables = len(source_data)
    migrated_tables = 0
    failed_tables = []
    
    # 如果指定了特定表，仅迁移这些表
    if specific_tables:
        logger.info(f"仅迁移指定的表: {', '.join(specific_tables)}")
        base_tables = [t for t in BASE_TABLES if t in specific_tables]
        other_tables = [t for t in specific_tables if t not in BASE_TABLES]
    else:
        base_tables = BASE_TABLES
        other_tables = [t for t in source_data.keys() if t not in BASE_TABLES and t not in SKIP_TABLES]
    
    # 先迁移基础表
    for table_name in base_tables:
        if table_name not in source_data:
            logger.warning(f"源数据中不存在表 {table_name}，跳过")
            continue
            
        if table_name not in tables_info:
            logger.warning(f"目标数据库中不存在表 {table_name}，跳过")
            continue
            
        logger.info(f"开始迁移基础表: {table_name}")
        # 清空表
        truncate_table(target_engine, table_name)
        # 迁移数据
        if migrate_table_data(target_engine, table_name, source_data[table_name], tables_info[table_name]):
            migrated_tables += 1
        else:
            failed_tables.append(table_name)
    
    # 迁移其他表
    for table_name in other_tables:
        if table_name in SKIP_TABLES:
            continue
            
        if table_name not in tables_info:
            logger.warning(f"目标数据库中不存在表 {table_name}，跳过")
            continue
            
        logger.info(f"开始迁移表: {table_name}")
        # 清空表
        truncate_table(target_engine, table_name)
        # 迁移数据
        if migrate_table_data(target_engine, table_name, source_data[table_name], tables_info[table_name]):
            migrated_tables += 1
        else:
            failed_tables.append(table_name)
    
    if failed_tables:
        logger.warning(f"以下表迁移失败: {', '.join(failed_tables)}")
        
    logger.info(f"数据迁移完成，成功迁移 {migrated_tables}/{total_tables} 个表")
    return migrated_tables > 0

def main():
    parser = argparse.ArgumentParser(description='数据库迁移工具')
    parser.add_argument('--source', required=True, help='源数据JSON文件路径')
    parser.add_argument('--target', required=True, help='目标数据库URL')
    parser.add_argument('--tables', help='仅迁移指定的表，多个表用逗号分隔')
    parser.add_argument('--skip', help='跳过指定的表，多个表用逗号分隔')
    parser.add_argument('--test', action='store_true', help='测试模式，只验证连接和读取JSON，不执行迁移')
    args = parser.parse_args()
    
    logger.info("=== 开始数据库迁移 ===")
    
    # 解析额外参数
    specific_tables = args.tables.split(',') if args.tables else None
    skip_tables = args.skip.split(',') if args.skip else []
    if skip_tables:
        SKIP_TABLES.extend(skip_tables)
        logger.info(f"跳过以下表: {', '.join(SKIP_TABLES)}")
    
    # 加载源数据
    source_data = load_json_data(args.source)
    if not source_data:
        logger.error("无法加载源数据，终止迁移")
        return 1
    
    # 修正数据库URL格式
    target_url = fix_database_url(args.target)
    if not target_url:
        logger.error("无效的数据库URL，终止迁移")
        return 1
    
    # 连接目标数据库
    target_engine = connect_to_db(target_url)
    if not target_engine:
        logger.error("无法连接到目标数据库，终止迁移")
        return 1
    
    # 测试模式
    if args.test:
        logger.info("测试模式：已验证数据库连接和JSON数据，未执行实际迁移")
        return 0
    
    # 执行数据迁移
    success = migrate_data(source_data, target_engine, specific_tables)
    
    logger.info("=== 数据库迁移结束 ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

 