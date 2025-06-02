#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整数据库同步解决方案

该脚本提供多种方式来同步本地和云端数据库：
1. 结构差异检测
2. 自动生成迁移SQL
3. 安全的数据库同步
4. 备份和恢复功能

用法:
python3 complete_db_sync_solution.py [选项]

选项:
--check: 仅检查差异，不执行同步
--sync: 执行完整同步
--backup: 备份云端数据库
--force: 强制执行（跳过确认）
--tables: 指定要同步的表（逗号分隔）
"""

import os
import sys
import logging
import argparse
import json
import datetime
import subprocess
from pathlib import Path
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.sql import sqltypes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('数据库同步')

class DatabaseSyncTool:
    def __init__(self):
        self.local_db_url = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
        self.render_db_url = os.environ.get('RENDER_DATABASE_URL')
        
        # 确保URL格式正确
        if self.render_db_url and self.render_db_url.startswith('postgres://'):
            self.render_db_url = self.render_db_url.replace('postgres://', 'postgresql://', 1)
        
        self.local_engine = None
        self.render_engine = None
        
        # 创建备份目录
        self.backup_dir = Path('db_backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def connect_databases(self):
        """连接到本地和云端数据库"""
        try:
            logger.info("连接本地数据库...")
            self.local_engine = create_engine(self.local_db_url)
            
            if self.render_db_url:
                logger.info("连接云端数据库...")
                self.render_engine = create_engine(self.render_db_url)
            else:
                logger.warning("未设置RENDER_DATABASE_URL，无法连接云端数据库")
                return False
            
            # 测试连接
            with self.local_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ 本地数据库连接成功")
            
            with self.render_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ 云端数据库连接成功")
            
            return True
            
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False
    
    def get_table_schema(self, engine, table_name):
        """获取表结构"""
        try:
            inspector = inspect(engine)
            if table_name not in inspector.get_table_names():
                return None
            
            schema = {
                'columns': {},
                'primary_key': [],
                'foreign_keys': [],
                'unique_constraints': [],
                'indexes': []
            }
            
            # 获取列信息
            columns = inspector.get_columns(table_name)
            for column in columns:
                schema['columns'][column['name']] = {
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': str(column['default']) if column['default'] else None,
                    'autoincrement': column.get('autoincrement', False)
                }
            
            # 获取主键
            pk = inspector.get_pk_constraint(table_name)
            if pk and 'constrained_columns' in pk:
                schema['primary_key'] = pk['constrained_columns']
            
            # 获取外键
            fks = inspector.get_foreign_keys(table_name)
            schema['foreign_keys'] = fks
            
            # 获取唯一约束
            unique_constraints = inspector.get_unique_constraints(table_name)
            schema['unique_constraints'] = unique_constraints
            
            # 获取索引
            indexes = inspector.get_indexes(table_name)
            schema['indexes'] = indexes
            
            return schema
            
        except Exception as e:
            logger.error(f"获取表 {table_name} 结构失败: {str(e)}")
            return None
    
    def get_all_tables_schema(self, engine):
        """获取所有表的结构"""
        try:
            inspector = inspect(engine)
            all_tables = inspector.get_table_names()
            schema = {}
            
            for table_name in all_tables:
                table_schema = self.get_table_schema(engine, table_name)
                if table_schema:
                    schema[table_name] = table_schema
            
            return schema
            
        except Exception as e:
            logger.error(f"获取数据库结构失败: {str(e)}")
            return None
    
    def compare_schemas(self, local_schema, render_schema):
        """比较本地和云端数据库结构"""
        differences = {
            'missing_tables': [],      # 云端缺少的表
            'extra_tables': [],        # 云端多出的表
            'table_differences': {},   # 表结构差异
            'summary': {}              # 差异摘要
        }
        
        # 检查缺少的表
        for table_name in local_schema:
            if table_name not in render_schema:
                differences['missing_tables'].append(table_name)
        
        # 检查多余的表
        for table_name in render_schema:
            if table_name not in local_schema:
                differences['extra_tables'].append(table_name)
        
        # 检查共有表的差异
        for table_name in local_schema:
            if table_name in render_schema:
                table_diff = self.compare_table_schemas(
                    local_schema[table_name], 
                    render_schema[table_name]
                )
                
                if table_diff:
                    differences['table_differences'][table_name] = table_diff
        
        # 生成摘要
        differences['summary'] = {
            'missing_tables_count': len(differences['missing_tables']),
            'extra_tables_count': len(differences['extra_tables']),
            'modified_tables_count': len(differences['table_differences']),
            'total_issues': len(differences['missing_tables']) + 
                          len(differences['extra_tables']) + 
                          len(differences['table_differences'])
        }
        
        return differences
    
    def compare_table_schemas(self, local_table, render_table):
        """比较单个表的结构"""
        diff = {
            'missing_columns': [],
            'extra_columns': [],
            'column_differences': [],
            'constraint_differences': []
        }
        
        # 检查缺少的列
        for col_name in local_table['columns']:
            if col_name not in render_table['columns']:
                diff['missing_columns'].append({
                    'name': col_name,
                    'definition': local_table['columns'][col_name]
                })
        
        # 检查多余的列
        for col_name in render_table['columns']:
            if col_name not in local_table['columns']:
                diff['extra_columns'].append({
                    'name': col_name,
                    'definition': render_table['columns'][col_name]
                })
        
        # 检查列差异
        for col_name in local_table['columns']:
            if col_name in render_table['columns']:
                local_col = local_table['columns'][col_name]
                render_col = render_table['columns'][col_name]
                
                if (local_col['type'] != render_col['type'] or
                    local_col['nullable'] != render_col['nullable']):
                    diff['column_differences'].append({
                        'name': col_name,
                        'local': local_col,
                        'render': render_col
                    })
        
        # 检查约束差异
        if (local_table['primary_key'] != render_table['primary_key']):
            diff['constraint_differences'].append({
                'type': 'primary_key',
                'local': local_table['primary_key'],
                'render': render_table['primary_key']
            })
        
        # 如果没有差异则返回None
        if not any([diff['missing_columns'], diff['extra_columns'], 
                   diff['column_differences'], diff['constraint_differences']]):
            return None
        
        return diff
    
    def generate_migration_sql(self, differences):
        """生成迁移SQL"""
        sql_statements = []
        
        # 添加注释头
        sql_statements.extend([
            "-- 数据库同步迁移脚本",
            f"-- 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-- 警告: 请在生产环境执行前仔细检查",
            "",
            "BEGIN;"
        ])
        
        # 处理缺少的表
        for table_name in differences['missing_tables']:
            sql_statements.append(f"-- 创建缺少的表: {table_name}")
            sql_statements.append(f"-- 注意: 需要手动创建表结构")
        
        # 处理表结构差异
        for table_name, table_diff in differences['table_differences'].items():
            sql_statements.append(f"")
            sql_statements.append(f"-- 修改表: {table_name}")
            
            # 添加缺少的列
            for col in table_diff['missing_columns']:
                col_name = col['name']
                col_def = col['definition']
                
                nullable = "NULL" if col_def['nullable'] else "NOT NULL"
                default_clause = f"DEFAULT {col_def['default']}" if col_def['default'] and col_def['default'] != 'None' else ""
                
                sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_def['type']} {nullable} {default_clause};"
                sql_statements.append(sql)
            
            # 修改列类型
            for col in table_diff['column_differences']:
                col_name = col['name']
                local_col = col['local']
                render_col = col['render']
                
                if local_col['type'] != render_col['type']:
                    sql = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {local_col['type']} USING {col_name}::{local_col['type']};"
                    sql_statements.append(sql)
                
                if local_col['nullable'] != render_col['nullable']:
                    if local_col['nullable']:
                        sql = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL;"
                    else:
                        sql = f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL;"
                    sql_statements.append(sql)
        
        sql_statements.append("")
        sql_statements.append("COMMIT;")
        
        return sql_statements
    
    def backup_render_database(self):
        """备份云端数据库"""
        if not self.render_db_url:
            logger.error("未设置云端数据库URL，无法备份")
            return False
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"render_backup_{timestamp}.sql"
        
        logger.info(f"备份云端数据库到: {backup_file}")
        
        try:
            # 从URL中提取连接信息
            url_parts = self.render_db_url.replace('postgresql://', '').split('/')
            conn_parts = url_parts[0].split('@')
            
            user_pass = conn_parts[0].split(':')
            host_port = conn_parts[1].split(':')
            
            username = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ''
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            dbname = url_parts[1].split('?')[0]
            
            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            # 执行pg_dump
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', dbname,
                '--verbose',
                '--clean',
                '--if-exists',
                '--no-owner',
                '--no-acl',
                '-f', str(backup_file)
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✓ 云端数据库备份成功: {backup_file}")
                return backup_file
            else:
                logger.error(f"备份失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"备份过程中出错: {str(e)}")
            return None
    
    def export_local_schema(self):
        """导出本地数据库结构"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        schema_file = f"local_schema_{timestamp}.sql"
        
        logger.info(f"导出本地数据库结构到: {schema_file}")
        
        try:
            # 从URL中提取连接信息
            url_parts = self.local_db_url.replace('postgresql://', '').split('/')
            conn_parts = url_parts[0].split('@')
            
            user_pass = conn_parts[0].split(':')
            host_port = conn_parts[1].split(':')
            
            username = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ''
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            dbname = url_parts[1].split('?')[0]
            
            # 设置环境变量
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password
            
            # 执行pg_dump
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', dbname,
                '--schema-only',
                '--verbose',
                '--clean',
                '--if-exists',
                '--no-owner',
                '--no-acl',
                '-f', schema_file
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✓ 本地数据库结构导出成功: {schema_file}")
                return schema_file
            else:
                logger.error(f"导出失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"导出过程中出错: {str(e)}")
            return None
    
    def execute_migration(self, sql_statements, dry_run=False):
        """执行迁移SQL"""
        if not self.render_engine:
            logger.error("未连接到云端数据库")
            return False
        
        if dry_run:
            logger.info("=== 预览模式：以下SQL将被执行 ===")
            for sql in sql_statements:
                if sql.strip() and not sql.startswith('--'):
                    logger.info(sql)
            return True
        
        try:
            with self.render_engine.connect() as conn:
                trans = conn.begin()
                try:
                    executed_count = 0
                    for sql in sql_statements:
                        if sql.strip() and not sql.startswith('--') and sql not in ['BEGIN;', 'COMMIT;']:
                            logger.info(f"执行: {sql}")
                            conn.execute(text(sql))
                            executed_count += 1
                    
                    trans.commit()
                    logger.info(f"✓ 成功执行 {executed_count} 条SQL语句")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f"执行迁移失败，已回滚: {str(e)}")
                    return False
                    
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return False
    
    def check_differences_only(self, tables=None):
        """仅检查差异，不执行同步"""
        if not self.connect_databases():
            return False
        
        logger.info("开始检查数据库差异...")
        
        # 获取数据库结构
        local_schema = self.get_all_tables_schema(self.local_engine)
        render_schema = self.get_all_tables_schema(self.render_engine)
        
        if not local_schema or not render_schema:
            logger.error("无法获取数据库结构")
            return False
        
        # 如果指定了特定表，只比较这些表
        if tables:
            table_list = [t.strip() for t in tables.split(',')]
            local_schema = {k: v for k, v in local_schema.items() if k in table_list}
            render_schema = {k: v for k, v in render_schema.items() if k in table_list}
            logger.info(f"仅检查指定表: {', '.join(table_list)}")
        
        # 比较结构
        differences = self.compare_schemas(local_schema, render_schema)
        
        # 显示结果
        self.display_differences(differences)
        
        # 保存差异报告
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"db_differences_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(differences, f, ensure_ascii=False, indent=2)
        
        logger.info(f"差异报告已保存: {report_file}")
        
        return differences['summary']['total_issues'] == 0
    
    def display_differences(self, differences):
        """显示差异信息"""
        summary = differences['summary']
        
        logger.info("=== 数据库差异检查结果 ===")
        logger.info(f"缺少的表: {summary['missing_tables_count']}")
        logger.info(f"多余的表: {summary['extra_tables_count']}")
        logger.info(f"结构差异的表: {summary['modified_tables_count']}")
        logger.info(f"总问题数: {summary['total_issues']}")
        
        if summary['total_issues'] == 0:
            logger.info("✓ 数据库结构完全同步")
            return
        
        # 显示详细差异
        if differences['missing_tables']:
            logger.warning(f"云端缺少的表: {', '.join(differences['missing_tables'])}")
        
        if differences['extra_tables']:
            logger.warning(f"云端多余的表: {', '.join(differences['extra_tables'])}")
        
        for table_name, table_diff in differences['table_differences'].items():
            logger.warning(f"表 {table_name} 存在差异:")
            
            if table_diff['missing_columns']:
                cols = [col['name'] for col in table_diff['missing_columns']]
                logger.warning(f"  - 缺少列: {', '.join(cols)}")
            
            if table_diff['extra_columns']:
                cols = [col['name'] for col in table_diff['extra_columns']]
                logger.warning(f"  - 多余列: {', '.join(cols)}")
            
            if table_diff['column_differences']:
                cols = [col['name'] for col in table_diff['column_differences']]
                logger.warning(f"  - 列类型差异: {', '.join(cols)}")
    
    def sync_databases(self, force=False, backup_first=True, tables=None):
        """执行完整的数据库同步"""
        if not self.connect_databases():
            return False
        
        logger.info("开始数据库同步流程...")
        
        # 1. 备份云端数据库
        if backup_first:
            backup_file = self.backup_render_database()
            if not backup_file:
                if not force:
                    logger.error("备份失败，同步中止")
                    return False
                else:
                    logger.warning("备份失败，但强制模式继续执行")
        
        # 2. 检查差异
        logger.info("检查数据库差异...")
        local_schema = self.get_all_tables_schema(self.local_engine)
        render_schema = self.get_all_tables_schema(self.render_engine)
        
        if not local_schema or not render_schema:
            logger.error("无法获取数据库结构")
            return False
        
        # 如果指定了特定表，只同步这些表
        if tables:
            table_list = [t.strip() for t in tables.split(',')]
            local_schema = {k: v for k, v in local_schema.items() if k in table_list}
            render_schema = {k: v for k, v in render_schema.items() if k in table_list}
            logger.info(f"仅同步指定表: {', '.join(table_list)}")
        
        differences = self.compare_schemas(local_schema, render_schema)
        
        if differences['summary']['total_issues'] == 0:
            logger.info("✓ 数据库已同步，无需操作")
            return True
        
        # 3. 显示差异
        self.display_differences(differences)
        
        # 4. 生成迁移SQL
        migration_sql = self.generate_migration_sql(differences)
        
        # 5. 保存SQL文件
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        sql_file = f"migration_{timestamp}.sql"
        
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(migration_sql))
        
        logger.info(f"迁移SQL已保存: {sql_file}")
        
        # 6. 预览模式
        logger.info("=== 预览将要执行的SQL ===")
        self.execute_migration(migration_sql, dry_run=True)
        
        # 7. 确认执行
        if not force:
            response = input("\n是否执行以上迁移？(y/N): ").lower()
            if response != 'y':
                logger.info("同步已取消")
                return False
        
        # 8. 执行迁移
        logger.info("开始执行迁移...")
        success = self.execute_migration(migration_sql)
        
        if success:
            logger.info("✓ 数据库同步完成")
            
            # 验证同步结果
            logger.info("验证同步结果...")
            verification_schema = self.get_all_tables_schema(self.render_engine)
            final_differences = self.compare_schemas(local_schema, verification_schema)
            
            if final_differences['summary']['total_issues'] == 0:
                logger.info("✓ 同步验证成功")
                return True
            else:
                logger.warning("⚠ 同步完成但仍有差异，请检查")
                self.display_differences(final_differences)
                return False
        else:
            logger.error("✗ 数据库同步失败")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='完整数据库同步解决方案')
    parser.add_argument('--check', action='store_true', help='仅检查差异，不执行同步')
    parser.add_argument('--sync', action='store_true', help='执行完整同步')
    parser.add_argument('--backup', action='store_true', help='仅备份云端数据库')
    parser.add_argument('--force', action='store_true', help='强制执行（跳过确认）')
    parser.add_argument('--tables', type=str, help='指定要处理的表（逗号分隔）')
    parser.add_argument('--no-backup', action='store_true', help='同步时不备份数据库')
    
    args = parser.parse_args()
    
    # 创建同步工具实例
    sync_tool = DatabaseSyncTool()
    
    try:
        if args.backup:
            # 仅备份
            backup_file = sync_tool.backup_render_database()
            if backup_file:
                logger.info(f"✓ 备份完成: {backup_file}")
                return 0
            else:
                logger.error("✗ 备份失败")
                return 1
        
        elif args.check:
            # 仅检查差异
            success = sync_tool.check_differences_only(args.tables)
            return 0 if success else 1
        
        elif args.sync:
            # 执行同步
            success = sync_tool.sync_databases(
                force=args.force,
                backup_first=not args.no_backup,
                tables=args.tables
            )
            return 0 if success else 1
        
        else:
            # 默认：检查差异
            logger.info("未指定操作，默认执行差异检查")
            logger.info("使用 --help 查看所有选项")
            success = sync_tool.check_differences_only(args.tables)
            return 0 if success else 1
    
    except KeyboardInterrupt:
        logger.info("操作被用户中断")
        return 1
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 