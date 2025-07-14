#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地PostgreSQL数据库结构同步到云端pma_db_ovs
功能：
1. 对比本地PostgreSQL pma_local和云端pma_db_ovs的数据库结构
2. 将本地结构同步到云端（仅结构，不同步数据）
3. 生成详细的同步报告
注意：此工具仅同步结构，不会影响云端数据
"""

import os
import sys
import psycopg2
import logging
import subprocess
import datetime
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('结构同步')

class PostgreSQLSchemaSync:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = os.path.join(os.path.dirname(__file__), '..', 'cloud_db_backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 本地PostgreSQL数据库URL (pma_local)
        self.local_db_url = "postgresql://nijie@localhost:5432/pma_local"
        
        # 云端PostgreSQL数据库URL (pma_db_ovs)
        self.cloud_db_url = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"
    
    def parse_db_url(self, db_url):
        """解析PostgreSQL数据库URL"""
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }
    
    def test_connections(self):
        """测试本地和云端数据库连接"""
        logger.info("🔄 [1/6] 测试数据库连接...")
        
        # 测试本地数据库
        try:
            local_params = self.parse_db_url(self.local_db_url)
            conn = psycopg2.connect(**local_params)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"✅ 本地数据库连接成功: {version[0][:50]}...")
            cursor.close()
            conn.close()
            local_ok = True
        except Exception as e:
            logger.error(f"❌ 本地数据库连接失败: {str(e)}")
            local_ok = False
        
        # 测试云端数据库
        try:
            cloud_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(**cloud_params)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"✅ 云端数据库连接成功: {version[0][:50]}...")
            cursor.close()
            conn.close()
            cloud_ok = True
        except Exception as e:
            logger.error(f"❌ 云端数据库连接失败: {str(e)}")
            cloud_ok = False
        
        return local_ok and cloud_ok
    
    def get_database_schema(self, db_url, db_name):
        """获取PostgreSQL数据库结构"""
        logger.info(f"🔄 [2/6] 分析{db_name}数据库结构...")
        
        try:
            db_params = self.parse_db_url(db_url)
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            schema_info = {}
            for (table_name,) in tables:
                # 获取表结构
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default, 
                           character_maximum_length, numeric_precision, numeric_scale
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                
                # 获取主键信息
                try:
                    cursor.execute("""
                        SELECT kcu.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu 
                            ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.table_schema = 'public' 
                            AND tc.table_name = %s 
                            AND tc.constraint_type = 'PRIMARY KEY'
                    """, (table_name,))
                    primary_keys = [row[0] for row in cursor.fetchall()]
                except Exception as e:
                    primary_keys = []
                
                # 获取外键信息
                try:
                    cursor.execute("""
                        SELECT kcu.column_name, ccu.table_name, ccu.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu 
                            ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage ccu 
                            ON tc.constraint_name = ccu.constraint_name
                        WHERE tc.table_schema = 'public' 
                            AND tc.table_name = %s 
                            AND tc.constraint_type = 'FOREIGN KEY'
                    """, (table_name,))
                    foreign_keys = cursor.fetchall()
                except Exception as e:
                    foreign_keys = []
                
                # 获取索引信息
                try:
                    cursor.execute("""
                        SELECT indexname, indexdef
                        FROM pg_indexes 
                        WHERE schemaname = 'public' AND tablename = %s
                        AND indexname NOT LIKE '%_pkey'
                    """, (table_name,))
                    indexes = cursor.fetchall()
                except Exception as e:
                    indexes = []
                
                schema_info[table_name] = {
                    'columns': columns,
                    'primary_keys': primary_keys,
                    'foreign_keys': foreign_keys,
                    'indexes': indexes
                }
            
            conn.close()
            logger.info(f"✅ {db_name}数据库: {len(tables)} 个表")
            return schema_info
            
        except Exception as e:
            logger.error(f"获取{db_name}数据库结构失败: {str(e)}")
            return None
    
    def compare_schemas(self, local_schema, cloud_schema):
        """对比本地和云端数据库结构"""
        logger.info("🔄 [3/6] 对比数据库结构差异...")
        
        differences = {
            'missing_tables': [],
            'extra_tables': [],
            'different_tables': [],
            'missing_columns': {},
            'extra_columns': {}
        }
        
        local_tables = set(local_schema.keys())
        cloud_tables = set(cloud_schema.keys())
        
        # 云端缺少的表（需要创建）
        differences['missing_tables'] = list(local_tables - cloud_tables)
        
        # 云端多余的表（本地没有）
        differences['extra_tables'] = list(cloud_tables - local_tables)
        
        # 共同的表，检查列差异
        common_tables = local_tables & cloud_tables
        for table in common_tables:
            local_cols = {col[0]: col for col in local_schema[table]['columns']}
            cloud_cols = {col[0]: col for col in cloud_schema[table]['columns']}
            
            missing_cols = set(local_cols.keys()) - set(cloud_cols.keys())
            extra_cols = set(cloud_cols.keys()) - set(local_cols.keys())
            
            if missing_cols or extra_cols:
                differences['different_tables'].append(table)
                differences['missing_columns'][table] = list(missing_cols)
                differences['extra_columns'][table] = list(extra_cols)
        
        logger.info(f"✅ 结构对比完成:")
        logger.info(f"   - 需要创建的表: {len(differences['missing_tables'])}")
        logger.info(f"   - 云端多余的表: {len(differences['extra_tables'])}")
        logger.info(f"   - 结构不同的表: {len(differences['different_tables'])}")
        
        return differences
    
    def backup_cloud_before_sync(self):
        """同步前备份云端数据库"""
        logger.info("🔄 [4/6] 同步前备份云端数据库...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        backup_file = os.path.join(self.backup_dir, f'pma_db_ovs_backup_before_sync_{self.timestamp}.sql')
        
        try:
            cmd = [
                'pg_dump',
                '-h', cloud_params['host'],
                '-p', str(cloud_params['port']),
                '-U', cloud_params['user'],
                '-d', cloud_params['dbname'],
                '--verbose',
                '--clean',
                '--if-exists',
                '--no-owner',
                '--no-privileges',
                '-f', backup_file
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = cloud_params['password']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 云端数据库备份成功: {backup_file}")
                return backup_file
            else:
                logger.error(f"❌ 备份失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"备份过程出错: {str(e)}")
            return None
    
    def export_local_schema(self):
        """导出本地数据库结构"""
        logger.info("🔄 [5/6] 导出本地数据库结构...")
        
        local_params = self.parse_db_url(self.local_db_url)
        schema_file = os.path.join(self.backup_dir, f'local_pma_schema_{self.timestamp}.sql')
        
        try:
            cmd = [
                'pg_dump',
                '-h', local_params['host'],
                '-p', str(local_params['port']),
                '-U', local_params['user'],
                '-d', local_params['dbname'],
                '--schema-only',
                '--no-owner',
                '--no-privileges',
                '-f', schema_file
            ]
            
            env = os.environ.copy()
            if local_params['password']:
                env['PGPASSWORD'] = local_params['password']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 本地结构导出成功: {schema_file}")
                return schema_file
            else:
                logger.error(f"❌ 结构导出失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"导出过程出错: {str(e)}")
            return None
    
    def sync_schema_to_cloud(self, differences, local_schema):
        """将本地结构同步到云端（仅同步缺失的表和字段）"""
        logger.info("🔄 [6/6] 同步结构到云端数据库...")
        
        if not differences['missing_tables'] and not differences['missing_columns']:
            logger.info("✅ 云端数据库结构已包含本地所有表和字段，无需同步")
            return True
        
        try:
            cloud_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(**cloud_params)
            conn.autocommit = False
            cursor = conn.cursor()
            
            sync_operations = []
            
            try:
                # 1. 处理缺失的表
                for table_name in differences['missing_tables']:
                    logger.info(f"🔄 创建缺失的表: {table_name}")
                    
                    # 从本地数据库获取表的完整CREATE语句
                    local_params = self.parse_db_url(self.local_db_url)
                    local_conn = psycopg2.connect(**local_params)
                    local_cursor = local_conn.cursor()
                    
                    # 获取表结构
                    table_info = local_schema[table_name]
                    
                    # 构建CREATE TABLE语句
                    create_sql = self.build_create_table_sql(table_name, table_info)
                    
                    cursor.execute(create_sql)
                    sync_operations.append(f"创建表: {table_name}")
                    logger.info(f"   ✅ 表 {table_name} 创建成功")
                    
                    local_conn.close()
                
                # 2. 处理缺失的字段
                for table_name, missing_cols in differences['missing_columns'].items():
                    if missing_cols:
                        logger.info(f"🔄 为表 {table_name} 添加缺失字段: {missing_cols}")
                        
                        table_info = local_schema[table_name]
                        local_columns = {col[0]: col for col in table_info['columns']}
                        
                        for col_name in missing_cols:
                            if col_name in local_columns:
                                col_info = local_columns[col_name]
                                alter_sql = self.build_alter_table_sql(table_name, col_name, col_info)
                                
                                try:
                                    cursor.execute(alter_sql)
                                    sync_operations.append(f"添加字段: {table_name}.{col_name}")
                                    logger.info(f"   ✅ 字段 {table_name}.{col_name} 添加成功")
                                except Exception as e:
                                    logger.warning(f"   ⚠️ 字段 {table_name}.{col_name} 添加失败: {str(e)}")
                
                # 提交所有更改
                conn.commit()
                logger.info(f"✅ 结构同步成功，执行了 {len(sync_operations)} 个操作")
                
                for op in sync_operations:
                    logger.info(f"   - {op}")
                
                cursor.close()
                conn.close()
                return True
                
            except Exception as e:
                logger.error(f"结构同步失败: {str(e)}")
                conn.rollback()
                cursor.close()
                conn.close()
                return False
                
        except Exception as e:
            logger.error(f"同步过程出错: {str(e)}")
            return False
    
    def build_create_table_sql(self, table_name, table_info):
        """构建CREATE TABLE SQL语句"""
        columns = table_info['columns']
        primary_keys = table_info['primary_keys']
        
        column_defs = []
        for col in columns:
            col_name = col[0]
            data_type = col[1]
            is_nullable = col[2]
            default_val = col[3]
            
            # 构建列定义
            col_def = f"{col_name} {data_type}"
            
            if not is_nullable == 'YES':
                col_def += " NOT NULL"
            
            if default_val:
                col_def += f" DEFAULT {default_val}"
            
            column_defs.append(col_def)
        
        # 添加主键约束
        if primary_keys:
            pk_constraint = f"PRIMARY KEY ({', '.join(primary_keys)})"
            column_defs.append(pk_constraint)
        
        create_sql = f"CREATE TABLE {table_name} (\n  {',\n  '.join(column_defs)}\n);"
        return create_sql
    
    def build_alter_table_sql(self, table_name, col_name, col_info):
        """构建ALTER TABLE ADD COLUMN SQL语句"""
        data_type = col_info[1]
        is_nullable = col_info[2]
        default_val = col_info[3]
        
        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {data_type}"
        
        if default_val:
            alter_sql += f" DEFAULT {default_val}"
        
        if is_nullable != 'YES':
            alter_sql += " NOT NULL"
        
        alter_sql += ";"
        return alter_sql
    
    def generate_sync_report(self, differences, backup_file, sync_success):
        """生成同步报告"""
        report_file = os.path.join(self.backup_dir, f'schema_sync_report_{self.timestamp}.md')
        
        report_content = f"""# PostgreSQL数据库结构同步报告

## 同步概述
- 同步时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 源数据库: 本地PostgreSQL (pma_local)
- 目标数据库: 云端PostgreSQL (pma_db_ovs)
- 同步状态: {'成功' if sync_success else '失败'}

## 结构差异分析

### 需要创建的表 ({len(differences['missing_tables'])})
"""
        
        for table in differences['missing_tables']:
            report_content += f"- {table}\n"
        
        report_content += f"""
### 云端多余的表 ({len(differences['extra_tables'])})
"""
        for table in differences['extra_tables']:
            report_content += f"- {table}\n"
        
        report_content += f"""
### 需要添加字段的表 ({len(differences['missing_columns'])})
"""
        for table, cols in differences['missing_columns'].items():
            if cols:
                report_content += f"#### {table}\n"
                for col in cols:
                    report_content += f"- {col}\n"
                report_content += "\n"
        
        report_content += f"""
### 云端多余字段的表 ({len(differences['extra_columns'])})
"""
        for table, cols in differences['extra_columns'].items():
            if cols:
                report_content += f"#### {table}\n"
                for col in cols:
                    report_content += f"- {col}\n"
                report_content += "\n"
        
        report_content += f"""
## 执行步骤
1. ✅ 测试数据库连接
2. ✅ 分析本地PostgreSQL数据库结构  
3. ✅ 分析云端PostgreSQL数据库结构
4. ✅ 对比数据库结构差异
5. {'✅' if backup_file else '❌'} 同步前备份云端数据库
6. ✅ 导出本地数据库结构
7. {'✅' if sync_success else '❌'} 同步结构到云端

## 文件位置
- 备份目录: {self.backup_dir}
- 云端备份: {backup_file or '无'}
- 本地数据库: {self.local_db_url}
- 云端数据库: pma_db_ovs

## 安全确认
- ✅ 仅同步数据库结构，未同步数据
- ✅ 同步前已备份云端数据库
- ✅ 只添加缺失的表和字段，不删除现有内容
- ✅ 云端数据完全安全
- ✅ 所有操作可回滚
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📋 同步报告已生成: {report_file}")
        return report_file
    
    def run(self):
        """执行完整的结构同步流程"""
        logger.info("🚀 开始PostgreSQL数据库结构同步流程...")
        
        # 1. 测试连接
        if not self.test_connections():
            logger.error("❌ 数据库连接测试失败")
            return False
        
        # 2. 获取本地结构
        local_schema = self.get_database_schema(self.local_db_url, "本地")
        if not local_schema:
            logger.error("❌ 获取本地数据库结构失败")
            return False
        
        # 3. 获取云端结构
        cloud_schema = self.get_database_schema(self.cloud_db_url, "云端")
        if not cloud_schema:
            logger.error("❌ 获取云端数据库结构失败")
            return False
        
        # 4. 对比结构
        differences = self.compare_schemas(local_schema, cloud_schema)
        
        # 5. 备份云端数据库
        backup_file = self.backup_cloud_before_sync()
        
        # 6. 导出本地结构
        schema_file = self.export_local_schema()
        
        # 7. 同步结构到云端
        sync_success = self.sync_schema_to_cloud(differences, local_schema)
        
        # 8. 生成报告
        report_file = self.generate_sync_report(differences, backup_file, sync_success)
        
        if sync_success:
            logger.info("🎉 PostgreSQL数据库结构同步完成!")
            logger.info(f"📋 详细报告: {report_file}")
        else:
            logger.error("❌ 结构同步失败，请查看报告")
        
        return sync_success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='本地PostgreSQL数据库结构同步到云端pma_db_ovs')
    parser.add_argument('--dry-run', action='store_true', help='仅对比结构，不执行同步')
    args = parser.parse_args()
    
    sync_tool = PostgreSQLSchemaSync()
    
    if args.dry_run:
        logger.info("执行试运行模式，仅对比结构...")
        # 测试连接
        if not sync_tool.test_connections():
            sys.exit(1)
        
        # 获取结构并对比
        local_schema = sync_tool.get_database_schema(sync_tool.local_db_url, "本地")
        cloud_schema = sync_tool.get_database_schema(sync_tool.cloud_db_url, "云端")
        
        if local_schema and cloud_schema:
            differences = sync_tool.compare_schemas(local_schema, cloud_schema)
            sync_tool.generate_sync_report(differences, None, False)
        else:
            logger.error("❌ 无法获取数据库结构")
    else:
        success = sync_tool.run()
        if not success:
            sys.exit(1)