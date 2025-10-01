#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库结构比较工具

该脚本用于比较本地PostgreSQL数据库和Render上的PostgreSQL数据库结构，
特别关注companies表的结构差异。

用法:
python compare_db_schemas.py
"""

import os
import sys
import logging
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, String, Integer, text
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据库结构比较')

# 数据库URL配置
LOCAL_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
RENDER_DB_URL = os.environ.get('RENDER_DATABASE_URL', None)

if not RENDER_DB_URL:
    logger.warning("未设置RENDER_DATABASE_URL环境变量，请设置后重试")
    logger.info("可以运行以下命令设置临时环境变量:")
    logger.info("export RENDER_DATABASE_URL='您的Render数据库URL'")
    sys.exit(1)

def get_table_schema(engine, table_name):
    """获取指定表的结构信息"""
    try:
        inspector = inspect(engine)
        
        # 检查表是否存在
        if table_name not in inspector.get_table_names():
            logger.error(f"表 {table_name} 在数据库中不存在")
            return None
        
        # 获取表的列信息
        columns = inspector.get_columns(table_name)
        column_details = {}
        
        for column in columns:
            column_details[column['name']] = {
                'type': str(column['type']),
                'nullable': column['nullable']
            }
        
        return column_details
    
    except Exception as e:
        logger.error(f"获取表 {table_name} 结构时出错: {str(e)}")
        return None

def compare_table_schemas(local_schema, render_schema, table_name):
    """比较两个数据库中指定表的结构差异"""
    if not local_schema or not render_schema:
        logger.error("无法比较表结构，本地或Render schema为空")
        return False
    
    logger.info(f"\n=== 表 {table_name} 结构比较 ===")
    
    # 找出本地有但Render没有的列
    missing_in_render = []
    for col_name, col_detail in local_schema.items():
        if col_name not in render_schema:
            missing_in_render.append({
                'name': col_name,
                'type': col_detail['type'],
                'nullable': col_detail['nullable']
            })
    
    if missing_in_render:
        logger.warning(f"Render中缺少以下列: {json.dumps(missing_in_render, indent=2)}")
    else:
        logger.info("Render中不缺少任何本地数据库中的列")
    
    # 找出Render有但本地没有的列
    extra_in_render = []
    for col_name, col_detail in render_schema.items():
        if col_name not in local_schema:
            extra_in_render.append({
                'name': col_name,
                'type': col_detail['type'],
                'nullable': col_detail['nullable']
            })
    
    if extra_in_render:
        logger.warning(f"Render中有以下额外的列: {json.dumps(extra_in_render, indent=2)}")
    else:
        logger.info("Render中没有本地数据库中不存在的列")
    
    # 检查类型和可空性差异
    type_differences = []
    for col_name, col_detail in local_schema.items():
        if col_name in render_schema:
            render_detail = render_schema[col_name]
            if col_detail['type'] != render_detail['type'] or col_detail['nullable'] != render_detail['nullable']:
                type_differences.append({
                    'name': col_name,
                    'local': col_detail,
                    'render': render_detail
                })
    
    if type_differences:
        logger.warning(f"以下列有类型或可空性差异: {json.dumps(type_differences, indent=2)}")
    else:
        logger.info("所有共同列的类型和可空性都一致")
    
    # 检查是否需要迁移
    needs_migration = bool(missing_in_render or type_differences)
    return needs_migration

def generate_migration_sql(local_schema, render_schema, table_name):
    """生成将Render数据库迁移到与本地一致的SQL语句"""
    migration_sql = []
    
    # 添加缺失的列
    for col_name, col_detail in local_schema.items():
        if col_name not in render_schema:
            col_type = col_detail['type']
            nullable = "NULL" if col_detail['nullable'] else "NOT NULL"
            migration_sql.append(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable};")
    
    # 修改类型不一致的列
    for col_name, col_detail in local_schema.items():
        if col_name in render_schema:
            render_detail = render_schema[col_name]
            if col_detail['type'] != render_detail['type']:
                migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {col_detail['type']} USING {col_name}::{col_detail['type']};")
            
            # 修改可空性
            if col_detail['nullable'] != render_detail['nullable']:
                if col_detail['nullable']:
                    migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL;")
                else:
                    migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL;")
    
    return migration_sql

def main():
    """主函数"""
    logger.info("开始比较本地和Render数据库结构...")
    
    try:
        # 连接本地数据库
        logger.info(f"连接本地数据库: {LOCAL_DB_URL}")
        local_engine = create_engine(LOCAL_DB_URL)
        
        # 连接Render数据库
        logger.info(f"连接Render数据库: {RENDER_DB_URL}")
        render_engine = create_engine(RENDER_DB_URL)
        
        # 比较companies表
        table_name = 'companies'
        local_schema = get_table_schema(local_engine, table_name)
        render_schema = get_table_schema(render_engine, table_name)
        
        needs_migration = compare_table_schemas(local_schema, render_schema, table_name)
        
        if needs_migration:
            logger.warning("需要迁移数据库结构以使Render与本地保持一致")
            
            # 生成迁移SQL
            migration_sql = generate_migration_sql(local_schema, render_schema, table_name)
            
            if migration_sql:
                logger.info("\n=== 迁移SQL ===")
                for sql in migration_sql:
                    logger.info(sql)
                
                # 保存SQL到文件
                with open('migration_sql.sql', 'w') as f:
                    f.write('\n'.join(migration_sql))
                logger.info("迁移SQL已保存到 migration_sql.sql")
                
                # 询问是否执行迁移
                if input("是否执行迁移? (y/n): ").lower() == 'y':
                    logger.info("执行迁移...")
                    with render_engine.connect() as conn:
                        for sql in migration_sql:
                            conn.execute(text(sql))
                        conn.commit()
                    logger.info("迁移完成!")
                else:
                    logger.info("迁移已取消")
            else:
                logger.info("没有生成迁移SQL，可能只是值的差异")
        else:
            logger.info("数据库结构一致，不需要迁移")
        
    except Exception as e:
        logger.error(f"比较数据库结构时出错: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
数据库结构比较工具

该脚本用于比较本地PostgreSQL数据库和Render上的PostgreSQL数据库结构，
特别关注companies表的结构差异。

用法:
python compare_db_schemas.py
"""

import os
import sys
import logging
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, String, Integer, text
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据库结构比较')

# 数据库URL配置
LOCAL_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
RENDER_DB_URL = os.environ.get('RENDER_DATABASE_URL', None)

if not RENDER_DB_URL:
    logger.warning("未设置RENDER_DATABASE_URL环境变量，请设置后重试")
    logger.info("可以运行以下命令设置临时环境变量:")
    logger.info("export RENDER_DATABASE_URL='您的Render数据库URL'")
    sys.exit(1)

def get_table_schema(engine, table_name):
    """获取指定表的结构信息"""
    try:
        inspector = inspect(engine)
        
        # 检查表是否存在
        if table_name not in inspector.get_table_names():
            logger.error(f"表 {table_name} 在数据库中不存在")
            return None
        
        # 获取表的列信息
        columns = inspector.get_columns(table_name)
        column_details = {}
        
        for column in columns:
            column_details[column['name']] = {
                'type': str(column['type']),
                'nullable': column['nullable']
            }
        
        return column_details
    
    except Exception as e:
        logger.error(f"获取表 {table_name} 结构时出错: {str(e)}")
        return None

def compare_table_schemas(local_schema, render_schema, table_name):
    """比较两个数据库中指定表的结构差异"""
    if not local_schema or not render_schema:
        logger.error("无法比较表结构，本地或Render schema为空")
        return False
    
    logger.info(f"\n=== 表 {table_name} 结构比较 ===")
    
    # 找出本地有但Render没有的列
    missing_in_render = []
    for col_name, col_detail in local_schema.items():
        if col_name not in render_schema:
            missing_in_render.append({
                'name': col_name,
                'type': col_detail['type'],
                'nullable': col_detail['nullable']
            })
    
    if missing_in_render:
        logger.warning(f"Render中缺少以下列: {json.dumps(missing_in_render, indent=2)}")
    else:
        logger.info("Render中不缺少任何本地数据库中的列")
    
    # 找出Render有但本地没有的列
    extra_in_render = []
    for col_name, col_detail in render_schema.items():
        if col_name not in local_schema:
            extra_in_render.append({
                'name': col_name,
                'type': col_detail['type'],
                'nullable': col_detail['nullable']
            })
    
    if extra_in_render:
        logger.warning(f"Render中有以下额外的列: {json.dumps(extra_in_render, indent=2)}")
    else:
        logger.info("Render中没有本地数据库中不存在的列")
    
    # 检查类型和可空性差异
    type_differences = []
    for col_name, col_detail in local_schema.items():
        if col_name in render_schema:
            render_detail = render_schema[col_name]
            if col_detail['type'] != render_detail['type'] or col_detail['nullable'] != render_detail['nullable']:
                type_differences.append({
                    'name': col_name,
                    'local': col_detail,
                    'render': render_detail
                })
    
    if type_differences:
        logger.warning(f"以下列有类型或可空性差异: {json.dumps(type_differences, indent=2)}")
    else:
        logger.info("所有共同列的类型和可空性都一致")
    
    # 检查是否需要迁移
    needs_migration = bool(missing_in_render or type_differences)
    return needs_migration

def generate_migration_sql(local_schema, render_schema, table_name):
    """生成将Render数据库迁移到与本地一致的SQL语句"""
    migration_sql = []
    
    # 添加缺失的列
    for col_name, col_detail in local_schema.items():
        if col_name not in render_schema:
            col_type = col_detail['type']
            nullable = "NULL" if col_detail['nullable'] else "NOT NULL"
            migration_sql.append(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable};")
    
    # 修改类型不一致的列
    for col_name, col_detail in local_schema.items():
        if col_name in render_schema:
            render_detail = render_schema[col_name]
            if col_detail['type'] != render_detail['type']:
                migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {col_detail['type']} USING {col_name}::{col_detail['type']};")
            
            # 修改可空性
            if col_detail['nullable'] != render_detail['nullable']:
                if col_detail['nullable']:
                    migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL;")
                else:
                    migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL;")
    
    return migration_sql

def main():
    """主函数"""
    logger.info("开始比较本地和Render数据库结构...")
    
    try:
        # 连接本地数据库
        logger.info(f"连接本地数据库: {LOCAL_DB_URL}")
        local_engine = create_engine(LOCAL_DB_URL)
        
        # 连接Render数据库
        logger.info(f"连接Render数据库: {RENDER_DB_URL}")
        render_engine = create_engine(RENDER_DB_URL)
        
        # 比较companies表
        table_name = 'companies'
        local_schema = get_table_schema(local_engine, table_name)
        render_schema = get_table_schema(render_engine, table_name)
        
        needs_migration = compare_table_schemas(local_schema, render_schema, table_name)
        
        if needs_migration:
            logger.warning("需要迁移数据库结构以使Render与本地保持一致")
            
            # 生成迁移SQL
            migration_sql = generate_migration_sql(local_schema, render_schema, table_name)
            
            if migration_sql:
                logger.info("\n=== 迁移SQL ===")
                for sql in migration_sql:
                    logger.info(sql)
                
                # 保存SQL到文件
                with open('migration_sql.sql', 'w') as f:
                    f.write('\n'.join(migration_sql))
                logger.info("迁移SQL已保存到 migration_sql.sql")
                
                # 询问是否执行迁移
                if input("是否执行迁移? (y/n): ").lower() == 'y':
                    logger.info("执行迁移...")
                    with render_engine.connect() as conn:
                        for sql in migration_sql:
                            conn.execute(text(sql))
                        conn.commit()
                    logger.info("迁移完成!")
                else:
                    logger.info("迁移已取消")
            else:
                logger.info("没有生成迁移SQL，可能只是值的差异")
        else:
            logger.info("数据库结构一致，不需要迁移")
        
    except Exception as e:
        logger.error(f"比较数据库结构时出错: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 