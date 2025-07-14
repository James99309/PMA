#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端pma_db_sp8d数据库备份脚本
功能：
1. 备份云端 pma_db_sp8d 数据库到本地
2. 生成详细的备份信息报告
注意：此工具仅进行备份操作，不会修改云端数据库
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
logger = logging.getLogger('SP8D数据库备份')

class SP8DCloudDatabaseBackup:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = os.path.join(os.path.dirname(__file__), '..', 'cloud_db_backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 云端数据库连接信息 (pma_db_sp8d)
        self.cloud_db_url = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
    
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
    
    def test_connection(self):
        """测试云端数据库连接（只读操作）"""
        logger.info("测试云端pma_db_sp8d数据库连接...")
        try:
            db_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"云端数据库连接成功: {version[0][:50]}...")
            
            # 获取数据库基本信息
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            db_size = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            
            logger.info(f"数据库大小: {db_size}, 表数量: {table_count}")
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"云端数据库连接失败: {str(e)}")
            return False
    
    def backup_cloud_database(self):
        """备份云端pma_db_sp8d数据库（只读操作，不会修改数据）"""
        logger.info("开始备份云端pma_db_sp8d数据库...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        backup_file = os.path.join(self.backup_dir, f'pma_db_sp8d_backup_{self.timestamp}.sql')
        info_file = os.path.join(self.backup_dir, f'pma_db_sp8d_backup_info_{self.timestamp}.md')
        
        try:
            # 使用pg_dump备份数据库（只读操作）
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
            
            logger.info(f"🔄 [1/3] 执行备份命令（数据库: {cloud_params['dbname']}）...")
            
            # 使用Popen来实时监控进度
            import time
            process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, text=True)
            
            # 监控进度
            start_time = time.time()
            while process.poll() is None:
                elapsed = int(time.time() - start_time)
                if elapsed > 0 and elapsed % 30 == 0:  # 每30秒显示一次进度
                    logger.info(f"⏱️  备份进行中... 已耗时 {elapsed} 秒")
                time.sleep(5)
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                elapsed_total = int(time.time() - start_time)
                logger.info(f"✅ [2/3] pma_db_sp8d备份成功: {backup_file} (耗时: {elapsed_total}秒)")
                
                # 生成备份信息文件
                logger.info("🔄 [3/3] 生成备份信息文件...")
                self.generate_backup_info(cloud_params, backup_file, info_file)
                
                return backup_file
            else:
                logger.error(f"备份失败: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f"备份过程出错: {str(e)}")
            return None
    
    def generate_backup_info(self, db_params, backup_file, info_file):
        """生成备份信息文件（只读操作）"""
        try:
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            
            # 获取数据库信息（只读查询）
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            db_size = cursor.fetchone()[0]
            
            # 获取表统计信息（只读查询）
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            table_stats = []
            total_rows = 0
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    table_stats.append((table_name, count))
                    total_rows += count
                except Exception as e:
                    logger.warning(f"无法获取表 {table_name} 的行数: {e}")
                    table_stats.append((table_name, 0))
            
            # 获取表结构信息（只读查询）
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)
            columns_info = cursor.fetchall()
            
            # 生成信息文档
            info_content = f"""# pma_db_sp8d数据库备份信息

## 备份基本信息
- 备份时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 备份文件: {os.path.basename(backup_file)}
- 数据库主机: {db_params['host']}
- 数据库名称: {db_params['dbname']}
- 数据库版本: {db_version}
- 数据库大小: {db_size}

## 表数据统计
| 表名 | 行数 |
|------|------|
"""
            
            for table_name, row_count in table_stats:
                info_content += f"| {table_name} | {row_count:,} |\n"
            
            info_content += f"| **总计** | **{total_rows:,}** |\n"
            
            info_content += "\n## 表结构信息\n"
            current_table = None
            for table, column, data_type, nullable in columns_info:
                if table != current_table:
                    info_content += f"\n### {table}\n| 字段名 | 数据类型 | 可空 |\n|--------|----------|------|\n"
                    current_table = table
                info_content += f"| {column} | {data_type} | {nullable} |\n"
            
            info_content += f"""
## 安全性确认
- ✅ 此备份操作仅执行只读查询
- ✅ 不会修改云端数据库的任何数据或结构
- ✅ 使用标准pg_dump工具进行备份
- ✅ 云端数据库完全安全
"""
            
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(info_content)
            
            logger.info(f"备份信息文件已生成: {info_file}")
            logger.info(f"数据库总行数: {total_rows:,}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"生成备份信息失败: {str(e)}")
    
    def run(self):
        """执行备份流程（纯备份，不修改云端数据）"""
        logger.info("🚀 开始pma_db_sp8d数据库备份流程...")
        
        # 1. 测试连接
        if not self.test_connection():
            logger.error("❌ 云端数据库连接失败")
            return False
        
        # 2. 备份云端数据库（只读操作）
        backup_file = self.backup_cloud_database()
        if not backup_file:
            logger.error("❌ 云端数据库备份失败")
            return False
        
        logger.info("🎉 pma_db_sp8d数据库备份完成!")
        logger.info(f"📁 备份文件: {backup_file}")
        logger.info("✅ 云端数据库未受任何影响，完全安全")
        
        return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='pma_db_sp8d数据库备份工具（只备份，不修改云端数据）')
    parser.add_argument('--dry-run', action='store_true', help='仅测试连接，不执行实际备份')
    args = parser.parse_args()
    
    backup_tool = SP8DCloudDatabaseBackup()
    
    if args.dry_run:
        logger.info("执行试运行模式，仅测试连接...")
        if backup_tool.test_connection():
            logger.info("✅ 数据库连接正常，可以执行备份")
        else:
            logger.error("❌ 数据库连接存在问题，请检查配置")
    else:
        success = backup_tool.run()
        if success:
            logger.info("🎯 备份操作成功完成!")
        else:
            logger.error("💥 备份操作失败!")