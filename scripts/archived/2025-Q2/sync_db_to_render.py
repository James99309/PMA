#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL数据库同步工具

该脚本用于将本地PostgreSQL数据库结构同步到Render上的数据库，
包括表结构、列、约束条件等。

特别关注：
1. 添加缺失的列（如companies表中的region列）
2. 修正列类型差异
3. 创建迁移SQL文件便于Render环境执行

用法:
python sync_db_to_render.py [--export-only] [--apply]

选项:
--export-only: 仅导出数据库结构，不连接Render数据库
--apply: 自动应用迁移，无需确认
"""

import os
import sys
import logging
import argparse
from sqlalchemy import create_engine, inspect, MetaData, Table, text
import json
import datetime
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据库同步工具')

# 数据库URL配置
LOCAL_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
RENDER_DB_URL = os.environ.get('RENDER_DATABASE_URL', None)

# 确保Render URL格式正确
if RENDER_DB_URL and RENDER_DB_URL.startswith('postgres://'):
    RENDER_DB_URL = RENDER_DB_URL.replace('postgres://', 'postgresql://', 1)

def get_db_schema(engine, include_tables=None):
    """
    获取数据库完整结构信息
    
    Args:
        engine: SQLAlchemy引擎
        include_tables: 要包含的表列表，None表示所有表
        
    Returns:
        dict: 数据库结构信息
    """
    try:
        inspector = inspect(engine)
        schema = {}
        
        # 获取所有表名
        all_tables = inspector.get_table_names()
        tables_to_process = include_tables or all_tables
        
        for table_name in tables_to_process:
            if table_name not in all_tables:
                logger.warning(f"表 {table_name} 在数据库中不存在，跳过")
                continue
                
            schema[table_name] = {
                'columns': {},
                'primary_key': [],
                'foreign_keys': [],
                'unique_constraints': [],
                'indexes': []
            }
            
            # 获取列信息
            columns = inspector.get_columns(table_name)
            for column in columns:
                schema[table_name]['columns'][column['name']] = {
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': str(column['default']) if column['default'] else None
                }
            
            # 获取主键
            pk = inspector.get_pk_constraint(table_name)
            if pk and 'constrained_columns' in pk:
                schema[table_name]['primary_key'] = pk['constrained_columns']
            
            # 获取外键
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                schema[table_name]['foreign_keys'].append({
                    'name': fk.get('name'),
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                })
            
            # 获取唯一约束
            unique_constraints = inspector.get_unique_constraints(table_name)
            for uc in unique_constraints:
                schema[table_name]['unique_constraints'].append({
                    'name': uc.get('name'),
                    'columns': uc['column_names']
                })
            
            # 获取索引
            indexes = inspector.get_indexes(table_name)
            for idx in indexes:
                schema[table_name]['indexes'].append({
                    'name': idx.get('name'),
                    'columns': idx['column_names'],
                    'unique': idx['unique']
                })
        
        return schema
    
    except Exception as e:
        logger.error(f"获取数据库结构时出错: {str(e)}")
        return None

def compare_schemas(local_schema, render_schema):
    """
    比较本地和Render数据库结构
    
    Args:
        local_schema: 本地数据库结构
        render_schema: Render数据库结构
        
    Returns:
        dict: 差异信息
    """
    differences = {
        'missing_tables': [],      # Render中缺少的表
        'extra_tables': [],        # Render中多出的表
        'table_differences': {}    # 表结构差异
    }
    
    # 1. 检查缺少的表
    for table_name in local_schema:
        if table_name not in render_schema:
            differences['missing_tables'].append(table_name)
    
    # 2. 检查多余的表
    for table_name in render_schema:
        if table_name not in local_schema:
            differences['extra_tables'].append(table_name)
    
    # 3. 检查共有表的差异
    for table_name in local_schema:
        if table_name in render_schema:
            table_diff = {
                'missing_columns': [],    # Render中缺少的列
                'extra_columns': [],      # Render中多出的列
                'column_type_diff': [],   # 列类型差异
                'constraint_diff': False  # 约束差异
            }
            
            # 3.1 检查缺少的列
            for col_name in local_schema[table_name]['columns']:
                if col_name not in render_schema[table_name]['columns']:
                    col_info = local_schema[table_name]['columns'][col_name]
                    table_diff['missing_columns'].append({
                        'name': col_name, 
                        'info': col_info
                    })
            
            # 3.2 检查多余的列
            for col_name in render_schema[table_name]['columns']:
                if col_name not in local_schema[table_name]['columns']:
                    col_info = render_schema[table_name]['columns'][col_name]
                    table_diff['extra_columns'].append({
                        'name': col_name, 
                        'info': col_info
                    })
            
            # 3.3 检查列类型差异
            for col_name in local_schema[table_name]['columns']:
                if col_name in render_schema[table_name]['columns']:
                    local_col = local_schema[table_name]['columns'][col_name]
                    render_col = render_schema[table_name]['columns'][col_name]
                    
                    if (local_col['type'] != render_col['type'] or 
                        local_col['nullable'] != render_col['nullable']):
                        table_diff['column_type_diff'].append({
                            'name': col_name,
                            'local': local_col,
                            'render': render_col
                        })
            
            # 3.4 检查约束差异
            # 简化处理：只检查是否存在差异，不详细比较
            if (local_schema[table_name]['primary_key'] != render_schema[table_name]['primary_key'] or
                len(local_schema[table_name]['foreign_keys']) != len(render_schema[table_name]['foreign_keys']) or
                len(local_schema[table_name]['unique_constraints']) != len(render_schema[table_name]['unique_constraints']) or
                len(local_schema[table_name]['indexes']) != len(render_schema[table_name]['indexes'])):
                table_diff['constraint_diff'] = True
            
            # 只添加有差异的表
            if (table_diff['missing_columns'] or 
                table_diff['extra_columns'] or 
                table_diff['column_type_diff'] or 
                table_diff['constraint_diff']):
                differences['table_differences'][table_name] = table_diff
    
    return differences

def generate_migration_sql(differences, include_drops=False):
    """
    生成迁移SQL语句
    
    Args:
        differences: 数据库差异信息
        include_drops: 是否包含删除操作（危险操作）
        
    Returns:
        list: SQL语句列表
    """
    migration_sql = []
    
    # 添加注释
    migration_sql.append("-- 自动生成的数据库迁移脚本")
    migration_sql.append(f"-- 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    migration_sql.append("-- 警告: 在应用到生产环境前，请仔细检查以下SQL语句\n")
    
    # 添加事务支持
    migration_sql.append("BEGIN;")
    
    # 处理表差异
    for table_name, diff in differences['table_differences'].items():
        migration_sql.append(f"\n-- 表 {table_name} 的修改")
        
        # 添加缺失的列
        for col in diff['missing_columns']:
            col_name = col['name']
            col_type = col['info']['type']
            nullable = "NULL" if col['info']['nullable'] else "NOT NULL"
            default = f"DEFAULT {col['info']['default']}" if col['info']['default'] else ""
            
            migration_sql.append(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_type} {nullable} {default};")
        
        # 修改列类型
        for col in diff['column_type_diff']:
            col_name = col['name']
            local_type = col['local']['type']
            render_type = col['render']['type']
            
            if local_type != render_type:
                migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {local_type} USING {col_name}::{local_type};")
            
            # 修改可空性
            if col['local']['nullable'] != col['render']['nullable']:
                if col['local']['nullable']:
                    migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL;")
                else:
                    migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL;")
        
        # 删除多余的列（危险操作）
        if include_drops and diff['extra_columns']:
            for col in diff['extra_columns']:
                migration_sql.append(f"-- 危险操作: ALTER TABLE {table_name} DROP COLUMN IF EXISTS {col['name']};")
    
    # 结束事务
    migration_sql.append("\nCOMMIT;")
    
    return migration_sql

def pg_dump_schema(output_file):
    """
    使用pg_dump导出数据库结构
    
    Args:
        output_file: 输出文件路径
        
    Returns:
        bool: 成功标志
    """
    try:
        # 从数据库URL中提取连接信息
        url_parts = LOCAL_DB_URL.replace('postgresql://', '').split('/')
        conn_parts = url_parts[0].split('@')
        
        user_pass = conn_parts[0].split(':')
        host_port = conn_parts[1].split(':')
        
        username = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ''
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else '5432'
        dbname = url_parts[1]
        
        # 设置PGPASSWORD环境变量
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # 运行pg_dump命令
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', username,
            '-d', dbname,
            '--schema-only',              # 只导出结构，不导出数据
            '--no-owner',                 # 不包含所有权设置
            '--no-acl',                   # 不包含访问权限
            '-f', output_file
        ]
        
        logger.info(f"运行pg_dump导出数据库结构: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env, check=True)
        
        if result.returncode == 0:
            logger.info(f"成功导出数据库结构到 {output_file}")
            return True
        else:
            logger.error(f"pg_dump命令执行失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"执行pg_dump时出错: {str(e)}")
        return False

def create_pg_restore_script(schema_file):
    """
    创建用于在Render上运行的恢复脚本
    
    Args:
        schema_file: 结构文件路径
        
    Returns:
        str: 脚本文件路径
    """
    script_file = 'apply_schema_on_render.py'
    
    with open(script_file, 'w') as f:
        f.write("""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Render数据库结构恢复脚本

该脚本用于在Render环境中应用本地导出的数据库结构。
\"\"\"

import os
import sys
import subprocess
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render数据库恢复')

def main():
    \"\"\"主函数\"\"\"
    # 检查是否在Render环境
    if os.environ.get('RENDER') != 'true':
        logger.warning("该脚本应该在Render环境中运行")
    
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        return 1
    
    # 转换URL格式
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    # 从数据库URL中提取连接信息
    url_parts = db_url.replace('postgresql://', '').split('/')
    conn_parts = url_parts[0].split('@')
    
    user_pass = conn_parts[0].split(':')
    host_port = conn_parts[1].split(':')
    
    username = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else '5432'
    dbname = url_parts[1].split('?')[0]  # 移除可能的查询参数
    
    # 设置PGPASSWORD环境变量
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    
    # 应用迁移SQL
    schema_file = 'db_schema.sql'
    if not os.path.exists(schema_file):
        logger.error(f"未找到结构文件 {schema_file}")
        return 1
    
    logger.info(f"开始应用数据库结构...")
    
    try:
        # 使用psql应用结构
        cmd = [
            'psql',
            '-h', host,
            '-p', port,
            '-U', username,
            '-d', dbname,
            '-f', schema_file
        ]
        
        logger.info(f"运行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env, check=True)
        
        if result.returncode == 0:
            logger.info("成功应用数据库结构")
            return 0
        else:
            logger.error("应用数据库结构失败")
            return 1
            
    except Exception as e:
        logger.error(f"应用数据库结构时出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
""")
    
    # 设置执行权限
    os.chmod(script_file, 0o755)
    
    logger.info(f"创建的恢复脚本: {script_file}")
    return script_file

def export_render_script():
    """导出用于Render环境的数据库同步脚本"""
    # 1. 导出数据库结构
    schema_file = 'db_schema.sql'
    if not pg_dump_schema(schema_file):
        return False
    
    # 2. 创建恢复脚本
    create_pg_restore_script(schema_file)
    
    # 3. 创建build.sh更新
    with open('update_build.sh', 'w') as f:
        f.write("""#!/bin/bash
# 添加到build.sh以应用数据库结构
echo "应用本地数据库结构..."
python apply_schema_on_render.py
""")
    
    logger.info("已创建以下文件:")
    logger.info(f"1. {schema_file} - 数据库结构")
    logger.info(f"2. apply_schema_on_render.py - 恢复脚本")
    logger.info(f"3. update_build.sh - build.sh更新指南")
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PostgreSQL数据库同步工具')
    parser.add_argument('--export-only', action='store_true', help='仅导出数据库结构，不连接Render数据库')
    parser.add_argument('--apply', action='store_true', help='自动应用迁移，无需确认')
    args = parser.parse_args()
    
    if args.export_only:
        logger.info("仅导出模式: 将导出数据库结构和恢复脚本")
        if export_render_script():
            logger.info("导出完成，请将生成的文件上传到Render环境")
        return 0
    
    # 检查环境变量
    if not RENDER_DB_URL:
        logger.warning("未设置RENDER_DATABASE_URL环境变量，将以导出模式运行")
        if export_render_script():
            logger.info("导出完成，请设置RENDER_DATABASE_URL后重试比较功能")
        return 0
    
    logger.info("开始同步本地和Render数据库结构...")
    
    try:
        # 连接本地数据库
        logger.info(f"连接本地数据库: {LOCAL_DB_URL}")
        local_engine = create_engine(LOCAL_DB_URL)
        
        # 连接Render数据库  
        logger.info(f"连接Render数据库: {RENDER_DB_URL}")
        render_engine = create_engine(RENDER_DB_URL)
        
        # 获取数据库结构
        logger.info("获取本地数据库结构...")
        local_schema = get_db_schema(local_engine)
        
        logger.info("获取Render数据库结构...")
        render_schema = get_db_schema(render_engine)
        
        # 比较结构差异
        logger.info("比较数据库结构差异...")
        differences = compare_schemas(local_schema, render_schema)
        
        # 输出差异摘要
        logger.info("\n=== 数据库差异摘要 ===")
        
        if differences['missing_tables']:
            logger.warning(f"Render中缺少 {len(differences['missing_tables'])} 个表")
            for table in differences['missing_tables']:
                logger.warning(f"  - {table}")
        else:
            logger.info("Render中不缺少任何表")
        
        if differences['extra_tables']:
            logger.warning(f"Render中有 {len(differences['extra_tables'])} 个额外的表")
            for table in differences['extra_tables']:
                logger.warning(f"  - {table}")
        
        table_with_diff = len(differences['table_differences'])
        if table_with_diff > 0:
            logger.warning(f"有 {table_with_diff} 个表结构存在差异")
            for table_name, diff in differences['table_differences'].items():
                missing_cols = len(diff['missing_columns'])
                extra_cols = len(diff['extra_columns'])
                type_diff = len(diff['column_type_diff'])
                
                logger.warning(f"  - {table_name}: 缺少{missing_cols}列, 多出{extra_cols}列, {type_diff}列类型不同")
                
                # 详细输出缺失的列
                if diff['missing_columns']:
                    logger.warning(f"    缺少的列:")
                    for col in diff['missing_columns']:
                        logger.warning(f"      {col['name']} ({col['info']['type']})")
        else:
            logger.info("所有表结构一致")
        
        # 如果存在差异，生成迁移SQL
        if differences['missing_tables'] or differences['table_differences']:
            logger.warning("\n需要迁移数据库结构以使Render与本地保持一致")
            
            # 生成迁移SQL
            logger.info("生成迁移SQL...")
            migration_sql = generate_migration_sql(differences)
            
            # 保存SQL到文件
            sql_file = 'migration_sql.sql'
            with open(sql_file, 'w') as f:
                f.write('\n'.join(migration_sql))
            logger.info(f"迁移SQL已保存到 {sql_file}")
            
            # 判断是否自动应用
            should_apply = args.apply
            
            if not should_apply:
                response = input("是否应用迁移? (y/n): ").lower()
                should_apply = response == 'y'
            
            if should_apply:
                logger.info("执行迁移...")
                
                # 检查是否有region列缺失且需要从province列迁移数据
                has_region_migration = False
                for table_name, diff in differences['table_differences'].items():
                    if table_name == 'companies':
                        for col in diff['missing_columns']:
                            if col['name'] == 'region':
                                has_region_migration = True
                                break
                
                with render_engine.connect() as conn:
                    # 开始事务
                    trans = conn.begin()
                    try:
                        # 执行SQL语句
                        for sql in migration_sql:
                            if sql.strip() and not sql.startswith('--') and sql != 'BEGIN;' and sql != 'COMMIT;':
                                logger.info(f"执行: {sql}")
                                conn.execute(text(sql))
                        
                        # 如果需要从province迁移数据到region
                        if has_region_migration:
                            logger.info("将province数据迁移到region列...")
                            conn.execute(text(
                                """
                                UPDATE companies 
                                SET region = province 
                                WHERE province IS NOT NULL AND region IS NULL
                                """
                            ))
                        
                        # 提交事务
                        trans.commit()
                        logger.info("迁移成功完成!")
                    except Exception as e:
                        # 回滚事务
                        trans.rollback()
                        logger.error(f"迁移失败: {str(e)}")
            else:
                logger.info("迁移已取消")
                
                # 导出脚本以便后续使用
                logger.info("导出数据库同步工具以便在Render上使用...")
                export_render_script()
        else:
            logger.info("数据库结构已同步，无需迁移")
        
    except Exception as e:
        logger.error(f"同步数据库结构时出错: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
PostgreSQL数据库同步工具

该脚本用于将本地PostgreSQL数据库结构同步到Render上的数据库，
包括表结构、列、约束条件等。

特别关注：
1. 添加缺失的列（如companies表中的region列）
2. 修正列类型差异
3. 创建迁移SQL文件便于Render环境执行

用法:
python sync_db_to_render.py [--export-only] [--apply]

选项:
--export-only: 仅导出数据库结构，不连接Render数据库
--apply: 自动应用迁移，无需确认
"""

import os
import sys
import logging
import argparse
from sqlalchemy import create_engine, inspect, MetaData, Table, text
import json
import datetime
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据库同步工具')

# 数据库URL配置
LOCAL_DB_URL = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
RENDER_DB_URL = os.environ.get('RENDER_DATABASE_URL', None)

# 确保Render URL格式正确
if RENDER_DB_URL and RENDER_DB_URL.startswith('postgres://'):
    RENDER_DB_URL = RENDER_DB_URL.replace('postgres://', 'postgresql://', 1)

def get_db_schema(engine, include_tables=None):
    """
    获取数据库完整结构信息
    
    Args:
        engine: SQLAlchemy引擎
        include_tables: 要包含的表列表，None表示所有表
        
    Returns:
        dict: 数据库结构信息
    """
    try:
        inspector = inspect(engine)
        schema = {}
        
        # 获取所有表名
        all_tables = inspector.get_table_names()
        tables_to_process = include_tables or all_tables
        
        for table_name in tables_to_process:
            if table_name not in all_tables:
                logger.warning(f"表 {table_name} 在数据库中不存在，跳过")
                continue
                
            schema[table_name] = {
                'columns': {},
                'primary_key': [],
                'foreign_keys': [],
                'unique_constraints': [],
                'indexes': []
            }
            
            # 获取列信息
            columns = inspector.get_columns(table_name)
            for column in columns:
                schema[table_name]['columns'][column['name']] = {
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': str(column['default']) if column['default'] else None
                }
            
            # 获取主键
            pk = inspector.get_pk_constraint(table_name)
            if pk and 'constrained_columns' in pk:
                schema[table_name]['primary_key'] = pk['constrained_columns']
            
            # 获取外键
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                schema[table_name]['foreign_keys'].append({
                    'name': fk.get('name'),
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                })
            
            # 获取唯一约束
            unique_constraints = inspector.get_unique_constraints(table_name)
            for uc in unique_constraints:
                schema[table_name]['unique_constraints'].append({
                    'name': uc.get('name'),
                    'columns': uc['column_names']
                })
            
            # 获取索引
            indexes = inspector.get_indexes(table_name)
            for idx in indexes:
                schema[table_name]['indexes'].append({
                    'name': idx.get('name'),
                    'columns': idx['column_names'],
                    'unique': idx['unique']
                })
        
        return schema
    
    except Exception as e:
        logger.error(f"获取数据库结构时出错: {str(e)}")
        return None

def compare_schemas(local_schema, render_schema):
    """
    比较本地和Render数据库结构
    
    Args:
        local_schema: 本地数据库结构
        render_schema: Render数据库结构
        
    Returns:
        dict: 差异信息
    """
    differences = {
        'missing_tables': [],      # Render中缺少的表
        'extra_tables': [],        # Render中多出的表
        'table_differences': {}    # 表结构差异
    }
    
    # 1. 检查缺少的表
    for table_name in local_schema:
        if table_name not in render_schema:
            differences['missing_tables'].append(table_name)
    
    # 2. 检查多余的表
    for table_name in render_schema:
        if table_name not in local_schema:
            differences['extra_tables'].append(table_name)
    
    # 3. 检查共有表的差异
    for table_name in local_schema:
        if table_name in render_schema:
            table_diff = {
                'missing_columns': [],    # Render中缺少的列
                'extra_columns': [],      # Render中多出的列
                'column_type_diff': [],   # 列类型差异
                'constraint_diff': False  # 约束差异
            }
            
            # 3.1 检查缺少的列
            for col_name in local_schema[table_name]['columns']:
                if col_name not in render_schema[table_name]['columns']:
                    col_info = local_schema[table_name]['columns'][col_name]
                    table_diff['missing_columns'].append({
                        'name': col_name, 
                        'info': col_info
                    })
            
            # 3.2 检查多余的列
            for col_name in render_schema[table_name]['columns']:
                if col_name not in local_schema[table_name]['columns']:
                    col_info = render_schema[table_name]['columns'][col_name]
                    table_diff['extra_columns'].append({
                        'name': col_name, 
                        'info': col_info
                    })
            
            # 3.3 检查列类型差异
            for col_name in local_schema[table_name]['columns']:
                if col_name in render_schema[table_name]['columns']:
                    local_col = local_schema[table_name]['columns'][col_name]
                    render_col = render_schema[table_name]['columns'][col_name]
                    
                    if (local_col['type'] != render_col['type'] or 
                        local_col['nullable'] != render_col['nullable']):
                        table_diff['column_type_diff'].append({
                            'name': col_name,
                            'local': local_col,
                            'render': render_col
                        })
            
            # 3.4 检查约束差异
            # 简化处理：只检查是否存在差异，不详细比较
            if (local_schema[table_name]['primary_key'] != render_schema[table_name]['primary_key'] or
                len(local_schema[table_name]['foreign_keys']) != len(render_schema[table_name]['foreign_keys']) or
                len(local_schema[table_name]['unique_constraints']) != len(render_schema[table_name]['unique_constraints']) or
                len(local_schema[table_name]['indexes']) != len(render_schema[table_name]['indexes'])):
                table_diff['constraint_diff'] = True
            
            # 只添加有差异的表
            if (table_diff['missing_columns'] or 
                table_diff['extra_columns'] or 
                table_diff['column_type_diff'] or 
                table_diff['constraint_diff']):
                differences['table_differences'][table_name] = table_diff
    
    return differences

def generate_migration_sql(differences, include_drops=False):
    """
    生成迁移SQL语句
    
    Args:
        differences: 数据库差异信息
        include_drops: 是否包含删除操作（危险操作）
        
    Returns:
        list: SQL语句列表
    """
    migration_sql = []
    
    # 添加注释
    migration_sql.append("-- 自动生成的数据库迁移脚本")
    migration_sql.append(f"-- 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    migration_sql.append("-- 警告: 在应用到生产环境前，请仔细检查以下SQL语句\n")
    
    # 添加事务支持
    migration_sql.append("BEGIN;")
    
    # 处理表差异
    for table_name, diff in differences['table_differences'].items():
        migration_sql.append(f"\n-- 表 {table_name} 的修改")
        
        # 添加缺失的列
        for col in diff['missing_columns']:
            col_name = col['name']
            col_type = col['info']['type']
            nullable = "NULL" if col['info']['nullable'] else "NOT NULL"
            default = f"DEFAULT {col['info']['default']}" if col['info']['default'] else ""
            
            migration_sql.append(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_type} {nullable} {default};")
        
        # 修改列类型
        for col in diff['column_type_diff']:
            col_name = col['name']
            local_type = col['local']['type']
            render_type = col['render']['type']
            
            if local_type != render_type:
                migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {local_type} USING {col_name}::{local_type};")
            
            # 修改可空性
            if col['local']['nullable'] != col['render']['nullable']:
                if col['local']['nullable']:
                    migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL;")
                else:
                    migration_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL;")
        
        # 删除多余的列（危险操作）
        if include_drops and diff['extra_columns']:
            for col in diff['extra_columns']:
                migration_sql.append(f"-- 危险操作: ALTER TABLE {table_name} DROP COLUMN IF EXISTS {col['name']};")
    
    # 结束事务
    migration_sql.append("\nCOMMIT;")
    
    return migration_sql

def pg_dump_schema(output_file):
    """
    使用pg_dump导出数据库结构
    
    Args:
        output_file: 输出文件路径
        
    Returns:
        bool: 成功标志
    """
    try:
        # 从数据库URL中提取连接信息
        url_parts = LOCAL_DB_URL.replace('postgresql://', '').split('/')
        conn_parts = url_parts[0].split('@')
        
        user_pass = conn_parts[0].split(':')
        host_port = conn_parts[1].split(':')
        
        username = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ''
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else '5432'
        dbname = url_parts[1]
        
        # 设置PGPASSWORD环境变量
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # 运行pg_dump命令
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', username,
            '-d', dbname,
            '--schema-only',              # 只导出结构，不导出数据
            '--no-owner',                 # 不包含所有权设置
            '--no-acl',                   # 不包含访问权限
            '-f', output_file
        ]
        
        logger.info(f"运行pg_dump导出数据库结构: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env, check=True)
        
        if result.returncode == 0:
            logger.info(f"成功导出数据库结构到 {output_file}")
            return True
        else:
            logger.error(f"pg_dump命令执行失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"执行pg_dump时出错: {str(e)}")
        return False

def create_pg_restore_script(schema_file):
    """
    创建用于在Render上运行的恢复脚本
    
    Args:
        schema_file: 结构文件路径
        
    Returns:
        str: 脚本文件路径
    """
    script_file = 'apply_schema_on_render.py'
    
    with open(script_file, 'w') as f:
        f.write("""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Render数据库结构恢复脚本

该脚本用于在Render环境中应用本地导出的数据库结构。
\"\"\"

import os
import sys
import subprocess
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render数据库恢复')

def main():
    \"\"\"主函数\"\"\"
    # 检查是否在Render环境
    if os.environ.get('RENDER') != 'true':
        logger.warning("该脚本应该在Render环境中运行")
    
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        return 1
    
    # 转换URL格式
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    # 从数据库URL中提取连接信息
    url_parts = db_url.replace('postgresql://', '').split('/')
    conn_parts = url_parts[0].split('@')
    
    user_pass = conn_parts[0].split(':')
    host_port = conn_parts[1].split(':')
    
    username = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else '5432'
    dbname = url_parts[1].split('?')[0]  # 移除可能的查询参数
    
    # 设置PGPASSWORD环境变量
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    
    # 应用迁移SQL
    schema_file = 'db_schema.sql'
    if not os.path.exists(schema_file):
        logger.error(f"未找到结构文件 {schema_file}")
        return 1
    
    logger.info(f"开始应用数据库结构...")
    
    try:
        # 使用psql应用结构
        cmd = [
            'psql',
            '-h', host,
            '-p', port,
            '-U', username,
            '-d', dbname,
            '-f', schema_file
        ]
        
        logger.info(f"运行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env, check=True)
        
        if result.returncode == 0:
            logger.info("成功应用数据库结构")
            return 0
        else:
            logger.error("应用数据库结构失败")
            return 1
            
    except Exception as e:
        logger.error(f"应用数据库结构时出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
""")
    
    # 设置执行权限
    os.chmod(script_file, 0o755)
    
    logger.info(f"创建的恢复脚本: {script_file}")
    return script_file

def export_render_script():
    """导出用于Render环境的数据库同步脚本"""
    # 1. 导出数据库结构
    schema_file = 'db_schema.sql'
    if not pg_dump_schema(schema_file):
        return False
    
    # 2. 创建恢复脚本
    create_pg_restore_script(schema_file)
    
    # 3. 创建build.sh更新
    with open('update_build.sh', 'w') as f:
        f.write("""#!/bin/bash
# 添加到build.sh以应用数据库结构
echo "应用本地数据库结构..."
python apply_schema_on_render.py
""")
    
    logger.info("已创建以下文件:")
    logger.info(f"1. {schema_file} - 数据库结构")
    logger.info(f"2. apply_schema_on_render.py - 恢复脚本")
    logger.info(f"3. update_build.sh - build.sh更新指南")
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PostgreSQL数据库同步工具')
    parser.add_argument('--export-only', action='store_true', help='仅导出数据库结构，不连接Render数据库')
    parser.add_argument('--apply', action='store_true', help='自动应用迁移，无需确认')
    args = parser.parse_args()
    
    if args.export_only:
        logger.info("仅导出模式: 将导出数据库结构和恢复脚本")
        if export_render_script():
            logger.info("导出完成，请将生成的文件上传到Render环境")
        return 0
    
    # 检查环境变量
    if not RENDER_DB_URL:
        logger.warning("未设置RENDER_DATABASE_URL环境变量，将以导出模式运行")
        if export_render_script():
            logger.info("导出完成，请设置RENDER_DATABASE_URL后重试比较功能")
        return 0
    
    logger.info("开始同步本地和Render数据库结构...")
    
    try:
        # 连接本地数据库
        logger.info(f"连接本地数据库: {LOCAL_DB_URL}")
        local_engine = create_engine(LOCAL_DB_URL)
        
        # 连接Render数据库  
        logger.info(f"连接Render数据库: {RENDER_DB_URL}")
        render_engine = create_engine(RENDER_DB_URL)
        
        # 获取数据库结构
        logger.info("获取本地数据库结构...")
        local_schema = get_db_schema(local_engine)
        
        logger.info("获取Render数据库结构...")
        render_schema = get_db_schema(render_engine)
        
        # 比较结构差异
        logger.info("比较数据库结构差异...")
        differences = compare_schemas(local_schema, render_schema)
        
        # 输出差异摘要
        logger.info("\n=== 数据库差异摘要 ===")
        
        if differences['missing_tables']:
            logger.warning(f"Render中缺少 {len(differences['missing_tables'])} 个表")
            for table in differences['missing_tables']:
                logger.warning(f"  - {table}")
        else:
            logger.info("Render中不缺少任何表")
        
        if differences['extra_tables']:
            logger.warning(f"Render中有 {len(differences['extra_tables'])} 个额外的表")
            for table in differences['extra_tables']:
                logger.warning(f"  - {table}")
        
        table_with_diff = len(differences['table_differences'])
        if table_with_diff > 0:
            logger.warning(f"有 {table_with_diff} 个表结构存在差异")
            for table_name, diff in differences['table_differences'].items():
                missing_cols = len(diff['missing_columns'])
                extra_cols = len(diff['extra_columns'])
                type_diff = len(diff['column_type_diff'])
                
                logger.warning(f"  - {table_name}: 缺少{missing_cols}列, 多出{extra_cols}列, {type_diff}列类型不同")
                
                # 详细输出缺失的列
                if diff['missing_columns']:
                    logger.warning(f"    缺少的列:")
                    for col in diff['missing_columns']:
                        logger.warning(f"      {col['name']} ({col['info']['type']})")
        else:
            logger.info("所有表结构一致")
        
        # 如果存在差异，生成迁移SQL
        if differences['missing_tables'] or differences['table_differences']:
            logger.warning("\n需要迁移数据库结构以使Render与本地保持一致")
            
            # 生成迁移SQL
            logger.info("生成迁移SQL...")
            migration_sql = generate_migration_sql(differences)
            
            # 保存SQL到文件
            sql_file = 'migration_sql.sql'
            with open(sql_file, 'w') as f:
                f.write('\n'.join(migration_sql))
            logger.info(f"迁移SQL已保存到 {sql_file}")
            
            # 判断是否自动应用
            should_apply = args.apply
            
            if not should_apply:
                response = input("是否应用迁移? (y/n): ").lower()
                should_apply = response == 'y'
            
            if should_apply:
                logger.info("执行迁移...")
                
                # 检查是否有region列缺失且需要从province列迁移数据
                has_region_migration = False
                for table_name, diff in differences['table_differences'].items():
                    if table_name == 'companies':
                        for col in diff['missing_columns']:
                            if col['name'] == 'region':
                                has_region_migration = True
                                break
                
                with render_engine.connect() as conn:
                    # 开始事务
                    trans = conn.begin()
                    try:
                        # 执行SQL语句
                        for sql in migration_sql:
                            if sql.strip() and not sql.startswith('--') and sql != 'BEGIN;' and sql != 'COMMIT;':
                                logger.info(f"执行: {sql}")
                                conn.execute(text(sql))
                        
                        # 如果需要从province迁移数据到region
                        if has_region_migration:
                            logger.info("将province数据迁移到region列...")
                            conn.execute(text(
                                """
                                UPDATE companies 
                                SET region = province 
                                WHERE province IS NOT NULL AND region IS NULL
                                """
                            ))
                        
                        # 提交事务
                        trans.commit()
                        logger.info("迁移成功完成!")
                    except Exception as e:
                        # 回滚事务
                        trans.rollback()
                        logger.error(f"迁移失败: {str(e)}")
            else:
                logger.info("迁移已取消")
                
                # 导出脚本以便后续使用
                logger.info("导出数据库同步工具以便在Render上使用...")
                export_render_script()
        else:
            logger.info("数据库结构已同步，无需迁移")
        
    except Exception as e:
        logger.error(f"同步数据库结构时出错: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 