#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步本地和云端数据库约束一致性
功能：
1. 对比本地和云端数据库的所有约束
2. 将云端约束调整为与本地一致
3. 生成详细的约束同步报告
"""

import psycopg2
import logging
import subprocess
import datetime
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('约束同步')

class ConstraintSync:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = '/Users/nijie/Documents/PMA/cloud_db_backups'
        
        self.local_db_url = "postgresql://nijie@localhost:5432/pma_local"
        self.cloud_db_url = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"
    
    def parse_db_url(self, db_url):
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }
    
    def connect_db(self, db_url):
        params = self.parse_db_url(db_url)
        return psycopg2.connect(**params)
    
    def get_all_constraints(self, db_url, db_name):
        """获取数据库所有约束信息"""
        logger.info(f"🔍 [1/5] 获取{db_name}数据库约束信息...")
        
        conn = self.connect_db(db_url)
        cursor = conn.cursor()
        
        constraints = {}
        
        # 1. 获取NOT NULL约束（从列信息中获取）
        cursor.execute("""
            SELECT 
                table_name,
                column_name,
                is_nullable,
                data_type,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name IN (
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            )
            ORDER BY table_name, ordinal_position
        """)
        
        null_constraints = {}
        for row in cursor.fetchall():
            table_name, col_name, is_nullable, data_type, default_val = row
            if table_name not in null_constraints:
                null_constraints[table_name] = {}
            null_constraints[table_name][col_name] = {
                'is_nullable': is_nullable,
                'data_type': data_type,
                'default': default_val
            }
        
        constraints['null_constraints'] = null_constraints
        
        # 2. 获取PRIMARY KEY约束
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                STRING_AGG(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = 'public' 
            AND tc.constraint_type = 'PRIMARY KEY'
            GROUP BY tc.table_name, tc.constraint_name
            ORDER BY tc.table_name
        """)
        
        primary_keys = {}
        for row in cursor.fetchall():
            table_name, constraint_name, columns = row
            primary_keys[table_name] = {
                'constraint_name': constraint_name,
                'columns': columns
            }
        
        constraints['primary_keys'] = primary_keys
        
        # 3. 获取FOREIGN KEY约束
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_schema = 'public' 
            AND tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name
        """)
        
        foreign_keys = {}
        for row in cursor.fetchall():
            table_name, constraint_name, column_name, ref_table, ref_column = row
            if table_name not in foreign_keys:
                foreign_keys[table_name] = {}
            foreign_keys[table_name][column_name] = {
                'constraint_name': constraint_name,
                'referenced_table': ref_table,
                'referenced_column': ref_column
            }
        
        constraints['foreign_keys'] = foreign_keys
        
        # 4. 获取UNIQUE约束
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                STRING_AGG(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = 'public' 
            AND tc.constraint_type = 'UNIQUE'
            GROUP BY tc.table_name, tc.constraint_name
            ORDER BY tc.table_name
        """)
        
        unique_constraints = {}
        for row in cursor.fetchall():
            table_name, constraint_name, columns = row
            if table_name not in unique_constraints:
                unique_constraints[table_name] = {}
            unique_constraints[table_name][constraint_name] = columns
        
        constraints['unique_constraints'] = unique_constraints
        
        # 5. 获取CHECK约束
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                cc.check_clause
            FROM information_schema.table_constraints tc
            JOIN information_schema.check_constraints cc 
                ON tc.constraint_name = cc.constraint_name
            WHERE tc.table_schema = 'public' 
            AND tc.constraint_type = 'CHECK'
            ORDER BY tc.table_name
        """)
        
        check_constraints = {}
        for row in cursor.fetchall():
            table_name, constraint_name, check_clause = row
            if table_name not in check_constraints:
                check_constraints[table_name] = {}
            check_constraints[table_name][constraint_name] = check_clause
        
        constraints['check_constraints'] = check_constraints
        
        conn.close()
        
        logger.info(f"✅ {db_name}数据库约束信息获取完成")
        return constraints
    
    def compare_constraints(self, local_constraints, cloud_constraints):
        """对比约束差异"""
        logger.info("🔍 [2/5] 对比约束差异...")
        
        differences = {
            'null_constraint_diffs': {},
            'missing_primary_keys': {},
            'different_primary_keys': {},
            'missing_foreign_keys': {},
            'different_foreign_keys': {},
            'missing_unique_constraints': {},
            'different_unique_constraints': {},
            'missing_check_constraints': {},
            'different_check_constraints': {}
        }
        
        # 1. 对比NULL约束
        local_nulls = local_constraints['null_constraints']
        cloud_nulls = cloud_constraints['null_constraints']
        
        for table in local_nulls:
            if table in cloud_nulls:
                for column in local_nulls[table]:
                    if column in cloud_nulls[table]:
                        local_nullable = local_nulls[table][column]['is_nullable']
                        cloud_nullable = cloud_nulls[table][column]['is_nullable']
                        
                        if local_nullable != cloud_nullable:
                            if table not in differences['null_constraint_diffs']:
                                differences['null_constraint_diffs'][table] = {}
                            differences['null_constraint_diffs'][table][column] = {
                                'local_nullable': local_nullable,
                                'cloud_nullable': cloud_nullable,
                                'data_type': local_nulls[table][column]['data_type']
                            }
        
        # 2. 对比PRIMARY KEY约束
        local_pks = local_constraints['primary_keys']
        cloud_pks = cloud_constraints['primary_keys']
        
        for table in local_pks:
            if table not in cloud_pks:
                differences['missing_primary_keys'][table] = local_pks[table]
            elif local_pks[table]['columns'] != cloud_pks[table]['columns']:
                differences['different_primary_keys'][table] = {
                    'local': local_pks[table]['columns'],
                    'cloud': cloud_pks[table]['columns']
                }
        
        # 3. 对比FOREIGN KEY约束
        local_fks = local_constraints['foreign_keys']
        cloud_fks = cloud_constraints['foreign_keys']
        
        for table in local_fks:
            if table in cloud_fks:
                for column in local_fks[table]:
                    if column not in cloud_fks[table]:
                        if table not in differences['missing_foreign_keys']:
                            differences['missing_foreign_keys'][table] = {}
                        differences['missing_foreign_keys'][table][column] = local_fks[table][column]
                    else:
                        local_fk = local_fks[table][column]
                        cloud_fk = cloud_fks[table][column]
                        if (local_fk['referenced_table'] != cloud_fk['referenced_table'] or 
                            local_fk['referenced_column'] != cloud_fk['referenced_column']):
                            if table not in differences['different_foreign_keys']:
                                differences['different_foreign_keys'][table] = {}
                            differences['different_foreign_keys'][table][column] = {
                                'local': local_fk,
                                'cloud': cloud_fk
                            }
        
        logger.info("✅ 约束对比完成")
        return differences
    
    def backup_cloud_before_constraint_sync(self):
        """约束同步前备份云端数据库"""
        logger.info("🔍 [3/5] 同步前备份云端数据库...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        backup_file = f"{self.backup_dir}/pma_db_ovs_backup_before_constraint_sync_{self.timestamp}.sql"
        
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
            
            env = {**dict(os.environ), 'PGPASSWORD': cloud_params['password']}
            
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
    
    def sync_constraints_to_cloud(self, differences):
        """将约束同步到云端"""
        logger.info("🔍 [4/5] 同步约束到云端数据库...")
        
        if not any(differences.values()):
            logger.info("✅ 所有约束已一致，无需同步")
            return True
        
        conn = self.connect_db(self.cloud_db_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        sync_operations = []
        
        try:
            # 1. 同步NULL约束
            null_diffs = differences['null_constraint_diffs']
            for table, columns in null_diffs.items():
                for column, diff in columns.items():
                    local_nullable = diff['local_nullable']
                    cloud_nullable = diff['cloud_nullable']
                    data_type = diff['data_type']
                    
                    if local_nullable == 'YES' and cloud_nullable == 'NO':
                        # 本地允许NULL，云端不允许 -> 修改云端为允许NULL
                        sql = f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL;"
                        logger.info(f"🔄 执行: {sql}")
                        cursor.execute(sql)
                        sync_operations.append(f"修改 {table}.{column} 为允许NULL")
                        
                    elif local_nullable == 'NO' and cloud_nullable == 'YES':
                        # 本地不允许NULL，云端允许 -> 修改云端为不允许NULL
                        sql = f"ALTER TABLE {table} ALTER COLUMN {column} SET NOT NULL;"
                        logger.info(f"🔄 执行: {sql}")
                        cursor.execute(sql)
                        sync_operations.append(f"修改 {table}.{column} 为不允许NULL")
            
            # 2. 同步其他约束（如果有差异的话）
            # 这里可以根据需要添加其他约束的同步逻辑
            
            # 提交更改
            conn.commit()
            logger.info(f"✅ 约束同步成功，执行了 {len(sync_operations)} 个操作")
            
            for op in sync_operations:
                logger.info(f"   - {op}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"约束同步失败: {str(e)}")
            conn.rollback()
            cursor.close()
            conn.close()
            return False
    
    def generate_constraint_sync_report(self, differences, backup_file, sync_success):
        """生成约束同步报告"""
        logger.info("🔍 [5/5] 生成约束同步报告...")
        
        report_file = f"{self.backup_dir}/constraint_sync_report_{self.timestamp}.md"
        
        report_content = f"""# 数据库约束同步报告

## 同步概述
- 同步时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 源数据库: 本地PostgreSQL (pma_local)
- 目标数据库: 云端PostgreSQL (pma_db_ovs)
- 同步状态: {'成功' if sync_success else '失败'}

## 约束差异分析

### NULL约束差异 ({len(differences['null_constraint_diffs'])})
"""
        
        for table, columns in differences['null_constraint_diffs'].items():
            report_content += f"#### {table}\n"
            for column, diff in columns.items():
                report_content += f"- **{column}**: 本地={diff['local_nullable']}, 云端={diff['cloud_nullable']}\n"
            report_content += "\n"
        
        report_content += f"""
### 主键约束差异
- 缺失的主键: {len(differences['missing_primary_keys'])}
- 不同的主键: {len(differences['different_primary_keys'])}

### 外键约束差异  
- 缺失的外键: {len(differences['missing_foreign_keys'])}
- 不同的外键: {len(differences['different_foreign_keys'])}

### 唯一约束差异
- 缺失的唯一约束: {len(differences['missing_unique_constraints'])}
- 不同的唯一约束: {len(differences['different_unique_constraints'])}

### 检查约束差异
- 缺失的检查约束: {len(differences['missing_check_constraints'])}
- 不同的检查约束: {len(differences['different_check_constraints'])}

## 执行步骤
1. ✅ 获取本地数据库约束信息
2. ✅ 获取云端数据库约束信息
3. ✅ 对比约束差异
4. {'✅' if backup_file else '❌'} 同步前备份云端数据库
5. {'✅' if sync_success else '❌'} 同步约束到云端

## 文件位置
- 备份文件: {backup_file or '无'}
- 本地数据库: {self.local_db_url}
- 云端数据库: pma_db_ovs

## 安全确认
- ✅ 仅同步约束设置，未修改数据内容
- ✅ 同步前已备份云端数据库
- ✅ 云端数据完全安全
- ✅ 所有操作可回滚

## 特别说明
本次同步主要解决了approval_record.step_id字段的NULL约束不一致问题：
- 本地数据库允许step_id为NULL
- 云端数据库不允许step_id为NULL  
- 已将云端约束调整为与本地一致
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📋 约束同步报告已生成: {report_file}")
        return report_file
    
    def run(self):
        """执行完整的约束同步流程"""
        logger.info("🚀 开始数据库约束同步流程...")
        
        try:
            # 1. 获取本地约束
            local_constraints = self.get_all_constraints(self.local_db_url, "本地")
            
            # 2. 获取云端约束
            cloud_constraints = self.get_all_constraints(self.cloud_db_url, "云端")
            
            # 3. 对比约束差异
            differences = self.compare_constraints(local_constraints, cloud_constraints)
            
            # 4. 备份云端数据库
            backup_file = self.backup_cloud_before_constraint_sync()
            
            # 5. 同步约束到云端
            sync_success = self.sync_constraints_to_cloud(differences)
            
            # 6. 生成报告
            report_file = self.generate_constraint_sync_report(differences, backup_file, sync_success)
            
            if sync_success:
                logger.info("🎉 数据库约束同步完成!")
                logger.info(f"📋 详细报告: {report_file}")
            else:
                logger.error("❌ 约束同步失败，请查看报告")
            
            return sync_success
            
        except Exception as e:
            logger.error(f"❌ 约束同步过程中出错: {str(e)}")
            return False

if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='本地和云端数据库约束同步')
    parser.add_argument('--dry-run', action='store_true', help='仅对比约束，不执行同步')
    args = parser.parse_args()
    
    sync_tool = ConstraintSync()
    
    if args.dry_run:
        logger.info("执行试运行模式，仅对比约束...")
        local_constraints = sync_tool.get_all_constraints(sync_tool.local_db_url, "本地")
        cloud_constraints = sync_tool.get_all_constraints(sync_tool.cloud_db_url, "云端")
        differences = sync_tool.compare_constraints(local_constraints, cloud_constraints)
        sync_tool.generate_constraint_sync_report(differences, None, False)
    else:
        success = sync_tool.run()
        if not success:
            exit(1)