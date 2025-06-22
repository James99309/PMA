#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库备份和本地结构同步脚本
功能：
1. 备份云端 pma_db_ovs 数据库
2. 获取本地数据库结构
3. 将本地结构同步到云端数据库
"""

import os
import sys
import psycopg2
import logging
import subprocess
import datetime
from urllib.parse import urlparse
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('云端数据库同步')

class CloudDatabaseSync:
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
    
    def test_connection(self, db_url, name):
        """测试数据库连接"""
        logger.info(f"测试{name}数据库连接...")
        try:
            db_params = self.parse_db_url(db_url)
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"{name}数据库连接成功: {version[0][:50]}...")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"{name}数据库连接失败: {str(e)}")
            return False
    
    def backup_cloud_database(self):
        """备份云端数据库"""
        logger.info("开始备份云端数据库...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        backup_file = os.path.join(self.backup_dir, f'pma_db_ovs_backup_{self.timestamp}.sql')
        info_file = os.path.join(self.backup_dir, f'pma_db_ovs_backup_info_{self.timestamp}.md')
        
        try:
            # 使用pg_dump备份数据库
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
            
            # 设置密码环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = cloud_params['password']
            
            logger.info(f"执行备份命令: {' '.join(cmd[:-2])} [密码已隐藏]")
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"云端数据库备份成功: {backup_file}")
                
                # 生成备份信息文件
                self.generate_backup_info(cloud_params, backup_file, info_file)
                
                return backup_file
            else:
                logger.error(f"备份失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"备份过程出错: {str(e)}")
            return None
    
    def generate_backup_info(self, db_params, backup_file, info_file):
        """生成备份信息文件"""
        try:
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            
            # 获取数据库信息
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            db_size = cursor.fetchone()[0]
            
            # 修复表统计查询
            cursor.execute("""
                SELECT schemaname, relname, n_tup_ins, n_tup_upd, n_tup_del 
                FROM pg_stat_user_tables 
                ORDER BY schemaname, relname;
            """)
            table_stats = cursor.fetchall()
            
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)
            columns_info = cursor.fetchall()
            
            # 生成信息文档
            info_content = f"""# 云端数据库备份信息

## 备份基本信息
- 备份时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 备份文件: {os.path.basename(backup_file)}
- 数据库主机: {db_params['host']}
- 数据库名称: {db_params['dbname']}
- 数据库版本: {db_version}
- 数据库大小: {db_size}

## 表统计信息
| 表名 | 插入行数 | 更新行数 | 删除行数 |
|------|----------|----------|----------|
"""
            
            for schema, table, inserts, updates, deletes in table_stats:
                info_content += f"| {table} | {inserts or 0} | {updates or 0} | {deletes or 0} |\n"
            
            info_content += "\n## 表结构信息\n"
            current_table = None
            for table, column, data_type, nullable in columns_info:
                if table != current_table:
                    info_content += f"\n### {table}\n| 字段名 | 数据类型 | 可空 |\n|--------|----------|------|\n"
                    current_table = table
                info_content += f"| {column} | {data_type} | {nullable} |\n"
            
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(info_content)
            
            logger.info(f"备份信息文件已生成: {info_file}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"生成备份信息失败: {str(e)}")
    
    def get_local_schema(self):
        """获取本地数据库结构"""
        logger.info("获取本地数据库结构...")
        
        local_params = self.parse_db_url(self.local_db_url)
        schema_file = os.path.join(self.backup_dir, f'local_schema_{self.timestamp}.sql')
        
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
                logger.info(f"本地数据库结构导出成功: {schema_file}")
                return schema_file
            else:
                logger.error(f"本地结构导出失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"获取本地结构出错: {str(e)}")
            return None
    
    def sync_schema_to_cloud(self, schema_file):
        """将本地结构同步到云端数据库"""
        logger.info("开始同步本地结构到云端数据库...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        
        try:
            # 读取结构文件
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # 连接云端数据库
            conn = psycopg2.connect(**cloud_params)
            conn.autocommit = False
            cursor = conn.cursor()
            
            try:
                # 执行结构同步
                logger.info("执行结构同步SQL...")
                cursor.execute(schema_sql)
                conn.commit()
                logger.info("结构同步成功")
                
                # 验证同步结果
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                logger.info(f"云端数据库现有表: {', '.join([t[0] for t in tables])}")
                
                return True
                
            except Exception as e:
                logger.error(f"结构同步失败: {str(e)}")
                conn.rollback()
                return False
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            logger.error(f"同步过程出错: {str(e)}")
            return False
    
    def generate_sync_report(self, backup_file, schema_file, sync_success):
        """生成同步报告"""
        report_file = os.path.join(self.backup_dir, f'sync_report_{self.timestamp}.md')
        
        report_content = f"""# 云端数据库同步报告

## 同步概述
- 同步时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 备份文件: {os.path.basename(backup_file) if backup_file else '备份失败'}
- 结构文件: {os.path.basename(schema_file) if schema_file else '结构导出失败'}
- 同步状态: {'成功' if sync_success else '失败'}

## 执行步骤
1. ✅ 测试数据库连接
2. {'✅' if backup_file else '❌'} 备份云端数据库
3. {'✅' if schema_file else '❌'} 导出本地数据库结构
4. {'✅' if sync_success else '❌'} 同步结构到云端

## 文件位置
- 备份目录: {self.backup_dir}
- 备份文件: {backup_file or '无'}
- 结构文件: {schema_file or '无'}

## 注意事项
- 云端数据库数据已备份，如需恢复请使用备份文件
- 结构同步可能会影响现有数据，请谨慎操作
- 建议在同步后验证应用功能是否正常
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"同步报告已生成: {report_file}")
        return report_file
    
    def run(self):
        """执行完整的备份和同步流程"""
        logger.info("开始云端数据库备份和同步流程...")
        
        # 1. 测试连接
        if not self.test_connection(self.local_db_url, "本地"):
            return False
        
        if not self.test_connection(self.cloud_db_url, "云端"):
            return False
        
        # 2. 备份云端数据库
        backup_file = self.backup_cloud_database()
        if not backup_file:
            logger.error("云端数据库备份失败，中止同步")
            return False
        
        # 3. 获取本地结构
        schema_file = self.get_local_schema()
        if not schema_file:
            logger.error("本地数据库结构导出失败，中止同步")
            return False
        
        # 4. 同步结构到云端
        sync_success = self.sync_schema_to_cloud(schema_file)
        
        # 5. 生成报告
        report_file = self.generate_sync_report(backup_file, schema_file, sync_success)
        
        if sync_success:
            logger.info("🎉 云端数据库备份和同步完成!")
            logger.info(f"📋 详细报告: {report_file}")
        else:
            logger.error("❌ 同步过程中出现错误，请查看日志")
        
        return sync_success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='云端数据库备份和本地结构同步')
    parser.add_argument('--dry-run', action='store_true', help='仅测试连接，不执行实际操作')
    args = parser.parse_args()
    
    sync_tool = CloudDatabaseSync()
    
    if args.dry_run:
        logger.info("执行试运行模式，仅测试连接...")
        local_ok = sync_tool.test_connection(sync_tool.local_db_url, "本地")
        cloud_ok = sync_tool.test_connection(sync_tool.cloud_db_url, "云端")
        
        if local_ok and cloud_ok:
            logger.info("✅ 所有数据库连接正常，可以执行同步")
        else:
            logger.error("❌ 数据库连接存在问题，请检查配置")
    else:
        sync_tool.run() 