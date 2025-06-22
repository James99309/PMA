#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据库结构同步脚本
功能：
1. 比较本地和云端数据库结构差异
2. 生成增量更新SQL
3. 安全地同步结构到云端
"""

import os
import sys
import psycopg2
import logging
import subprocess
import datetime
from urllib.parse import urlparse
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('智能结构同步')

class SmartSchemaSync:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = os.path.join(os.path.dirname(__file__), '..', 'cloud_db_backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 数据库连接信息
        self.local_db_url = os.environ.get('DATABASE_URL')
        self.cloud_db_url = os.environ.get('RENDER_DB_URL')
        
        if not self.local_db_url:
            logger.error("未找到本地数据库URL，请设置DATABASE_URL环境变量")
            sys.exit(1)
            
        if not self.cloud_db_url:
            logger.error("未找到云端数据库URL，请设置RENDER_DB_URL环境变量")
            sys.exit(1)
    
    def parse_db_url(self, db_url):
        """解析数据库URL"""
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }
    
    def get_db_schema_info(self, db_params, db_name):
        """获取数据库结构信息"""
        logger.info(f"获取{db_name}数据库结构信息...")
        
        try:
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            
            schema_info = {
                'tables': {},
                'columns': {},
                'indexes': {},
                'constraints': {},
                'types': set(),
                'functions': set()
            }
            
            # 获取表信息
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            for (table_name,) in tables:
                schema_info['tables'][table_name] = True
            
            # 获取列信息
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)
            columns = cursor.fetchall()
            for table_name, column_name, data_type, is_nullable, column_default in columns:
                if table_name not in schema_info['columns']:
                    schema_info['columns'][table_name] = {}
                schema_info['columns'][table_name][column_name] = {
                    'data_type': data_type,
                    'is_nullable': is_nullable,
                    'column_default': column_default
                }
            
            # 获取自定义类型
            cursor.execute("""
                SELECT typname FROM pg_type 
                WHERE typtype = 'e' AND typnamespace = (
                    SELECT oid FROM pg_namespace WHERE nspname = 'public'
                );
            """)
            types = cursor.fetchall()
            for (type_name,) in types:
                schema_info['types'].add(type_name)
            
            # 获取索引信息
            cursor.execute("""
                SELECT indexname, tablename, indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            indexes = cursor.fetchall()
            for index_name, table_name, index_def in indexes:
                if table_name not in schema_info['indexes']:
                    schema_info['indexes'][table_name] = {}
                schema_info['indexes'][table_name][index_name] = index_def
            
            cursor.close()
            conn.close()
            
            logger.info(f"{db_name}数据库结构信息获取完成")
            logger.info(f"  - 表数量: {len(schema_info['tables'])}")
            logger.info(f"  - 自定义类型: {len(schema_info['types'])}")
            
            return schema_info
            
        except Exception as e:
            logger.error(f"获取{db_name}数据库结构失败: {str(e)}")
            return None
    
    def compare_schemas(self, local_schema, cloud_schema):
        """比较本地和云端数据库结构"""
        logger.info("比较本地和云端数据库结构...")
        
        differences = {
            'new_tables': [],
            'new_columns': [],
            'missing_types': [],
            'new_indexes': []
        }
        
        # 比较表
        for table_name in local_schema['tables']:
            if table_name not in cloud_schema['tables']:
                differences['new_tables'].append(table_name)
        
        # 比较列
        for table_name, columns in local_schema['columns'].items():
            if table_name in cloud_schema['columns']:
                cloud_columns = cloud_schema['columns'][table_name]
                for column_name, column_info in columns.items():
                    if column_name not in cloud_columns:
                        differences['new_columns'].append({
                            'table': table_name,
                            'column': column_name,
                            'info': column_info
                        })
        
        # 比较自定义类型
        for type_name in local_schema['types']:
            if type_name not in cloud_schema['types']:
                differences['missing_types'].append(type_name)
        
        # 比较索引
        for table_name, indexes in local_schema['indexes'].items():
            if table_name in cloud_schema['indexes']:
                cloud_indexes = cloud_schema['indexes'][table_name]
                for index_name, index_def in indexes.items():
                    if index_name not in cloud_indexes:
                        differences['new_indexes'].append({
                            'table': table_name,
                            'index': index_name,
                            'definition': index_def
                        })
        
        logger.info("结构比较完成:")
        logger.info(f"  - 新增表: {len(differences['new_tables'])}")
        logger.info(f"  - 新增列: {len(differences['new_columns'])}")
        logger.info(f"  - 缺失类型: {len(differences['missing_types'])}")
        logger.info(f"  - 新增索引: {len(differences['new_indexes'])}")
        
        return differences
    
    def generate_migration_sql(self, differences):
        """生成迁移SQL"""
        logger.info("生成迁移SQL...")
        
        migration_sql = []
        
        # 添加缺失的自定义类型
        if differences['missing_types']:
            migration_sql.append("-- 添加缺失的自定义类型")
            for type_name in differences['missing_types']:
                # 这里需要从本地数据库获取类型定义
                type_def = self.get_type_definition(type_name)
                if type_def:
                    migration_sql.append(f"DO $$ BEGIN")
                    migration_sql.append(f"    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN")
                    migration_sql.append(f"        {type_def};")
                    migration_sql.append(f"    END IF;")
                    migration_sql.append(f"END $$;")
                    migration_sql.append("")
        
        # 添加新增的列
        if differences['new_columns']:
            migration_sql.append("-- 添加新增的列")
            for col_info in differences['new_columns']:
                table = col_info['table']
                column = col_info['column']
                info = col_info['info']
                
                alter_sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {info['data_type']}"
                
                if info['is_nullable'] == 'NO':
                    alter_sql += " NOT NULL"
                
                if info['column_default']:
                    alter_sql += f" DEFAULT {info['column_default']}"
                
                migration_sql.append(alter_sql + ";")
            migration_sql.append("")
        
        # 添加新增的索引
        if differences['new_indexes']:
            migration_sql.append("-- 添加新增的索引")
            for idx_info in differences['new_indexes']:
                # 修改索引定义，添加IF NOT EXISTS
                index_def = idx_info['definition']
                if 'CREATE INDEX' in index_def:
                    index_def = index_def.replace('CREATE INDEX', 'CREATE INDEX IF NOT EXISTS')
                elif 'CREATE UNIQUE INDEX' in index_def:
                    index_def = index_def.replace('CREATE UNIQUE INDEX', 'CREATE UNIQUE INDEX IF NOT EXISTS')
                
                migration_sql.append(index_def + ";")
            migration_sql.append("")
        
        return "\n".join(migration_sql)
    
    def get_type_definition(self, type_name):
        """获取自定义类型定义"""
        try:
            local_params = self.parse_db_url(self.local_db_url)
            conn = psycopg2.connect(**local_params)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT string_agg(enumlabel, ''', ''' ORDER BY enumsortorder) as enum_values
                FROM pg_enum 
                WHERE enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = %s
                );
            """, (type_name,))
            
            result = cursor.fetchone()
            if result and result[0]:
                enum_values = result[0]
                type_def = f"CREATE TYPE {type_name} AS ENUM ('{enum_values}')"
                cursor.close()
                conn.close()
                return type_def
            
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"获取类型定义失败: {str(e)}")
            return None
    
    def apply_migration(self, migration_sql):
        """应用迁移SQL到云端数据库"""
        logger.info("应用迁移SQL到云端数据库...")
        
        if not migration_sql.strip():
            logger.info("没有需要迁移的结构变更")
            return True
        
        try:
            cloud_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(**cloud_params)
            conn.autocommit = False
            cursor = conn.cursor()
            
            try:
                # 执行迁移SQL
                cursor.execute(migration_sql)
                conn.commit()
                logger.info("迁移SQL执行成功")
                
                cursor.close()
                conn.close()
                return True
                
            except Exception as e:
                logger.error(f"迁移执行失败: {str(e)}")
                conn.rollback()
                cursor.close()
                conn.close()
                return False
                
        except Exception as e:
            logger.error(f"连接云端数据库失败: {str(e)}")
            return False
    
    def save_migration_files(self, migration_sql, differences):
        """保存迁移文件"""
        migration_file = os.path.join(self.backup_dir, f'migration_{self.timestamp}.sql')
        report_file = os.path.join(self.backup_dir, f'migration_report_{self.timestamp}.md')
        
        # 保存迁移SQL
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(migration_sql)
        
        # 生成迁移报告
        report_content = f"""# 数据库结构迁移报告

## 迁移概述
- 迁移时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 迁移文件: {os.path.basename(migration_file)}

## 结构变更统计
- 新增表: {len(differences['new_tables'])}
- 新增列: {len(differences['new_columns'])}
- 缺失类型: {len(differences['missing_types'])}
- 新增索引: {len(differences['new_indexes'])}

## 详细变更
"""
        
        if differences['new_tables']:
            report_content += "\n### 新增表\n"
            for table in differences['new_tables']:
                report_content += f"- {table}\n"
        
        if differences['new_columns']:
            report_content += "\n### 新增列\n"
            for col_info in differences['new_columns']:
                report_content += f"- {col_info['table']}.{col_info['column']} ({col_info['info']['data_type']})\n"
        
        if differences['missing_types']:
            report_content += "\n### 缺失类型\n"
            for type_name in differences['missing_types']:
                report_content += f"- {type_name}\n"
        
        if differences['new_indexes']:
            report_content += "\n### 新增索引\n"
            for idx_info in differences['new_indexes']:
                report_content += f"- {idx_info['table']}.{idx_info['index']}\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"迁移文件已保存: {migration_file}")
        logger.info(f"迁移报告已保存: {report_file}")
        
        return migration_file, report_file
    
    def run(self):
        """执行智能结构同步"""
        logger.info("开始智能数据库结构同步...")
        
        # 1. 获取本地数据库结构
        local_params = self.parse_db_url(self.local_db_url)
        local_schema = self.get_db_schema_info(local_params, "本地")
        if not local_schema:
            return False
        
        # 2. 获取云端数据库结构
        cloud_params = self.parse_db_url(self.cloud_db_url)
        cloud_schema = self.get_db_schema_info(cloud_params, "云端")
        if not cloud_schema:
            return False
        
        # 3. 比较结构差异
        differences = self.compare_schemas(local_schema, cloud_schema)
        
        # 4. 生成迁移SQL
        migration_sql = self.generate_migration_sql(differences)
        
        # 5. 保存迁移文件
        migration_file, report_file = self.save_migration_files(migration_sql, differences)
        
        # 6. 应用迁移
        if migration_sql.strip():
            logger.info("发现结构差异，准备应用迁移...")
            success = self.apply_migration(migration_sql)
            
            if success:
                logger.info("🎉 数据库结构同步完成!")
                logger.info(f"📋 迁移报告: {report_file}")
            else:
                logger.error("❌ 迁移应用失败")
            
            return success
        else:
            logger.info("✅ 数据库结构已同步，无需迁移")
            return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='智能数据库结构同步')
    parser.add_argument('--dry-run', action='store_true', help='仅比较结构，不执行迁移')
    args = parser.parse_args()
    
    sync_tool = SmartSchemaSync()
    
    if args.dry_run:
        logger.info("执行试运行模式，仅比较结构...")
        # 这里可以添加试运行逻辑
    else:
        sync_tool.run() 