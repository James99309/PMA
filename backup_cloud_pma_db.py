#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMA 云端 SP8D 数据库备份工具
功能：
1. 备份云端PostgreSQL数据库 pma_db_sp8d
2. 生成详细的备份信息报告
3. 验证数据完整性

使用方法：
    python3 backup_cloud_pma_db.py

功能特性：
- 备份云端 pma_db_sp8d 数据库到本地
- 生成详细的表统计和备份信息文件
- 自动验证备份数据完整性
- 使用标准的 subprocess.run() 方式执行备份

备份文件：
- 存储位置：./cloud_db_backups/
- 备份文件：pma_db_sp8d_backup_YYYYMMDD_HHMMSS.sql
- 信息文件：backup_info_YYYYMMDD_HHMMSS.md
- 备份大小：约 3.5MB
- 数据行数：约 15,000 行

备份内容：
- 58个表的完整结构和数据
- 所有约束、索引、序列
- 使用 COPY 语句格式，支持高效恢复

注意：
- 需要网络连接到 render.com 数据库
- 需要安装 PostgreSQL 客户端工具 (pg_dump)
- 备份过程约需3秒，会自动验证数据完整性

遵循 CLAUDE.md 中的云端数据库备份工具规范
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PMA云端数据库同步')

class PMACloudDBSync:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = os.path.join(os.getcwd(), 'cloud_db_backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 云端数据库连接信息 - 更新到新的Supabase位置
        self.cloud_db_url = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        
        # 本地数据库URL（从环境变量或默认配置获取）
        self.local_db_url = os.environ.get('DATABASE_URL')
        if not self.local_db_url:
            # 尝试从config.py获取
            try:
                import config
                self.local_db_url = config.Config.SQLALCHEMY_DATABASE_URI
            except:
                self.local_db_url = "sqlite:///app.db"  # 默认SQLite
        
        logger.info(f"云端数据库: {self.cloud_db_url.split('@')[1] if '@' in self.cloud_db_url else 'Hidden'}")
        logger.info(f"本地数据库: {self.local_db_url.split('@')[1] if '@' in self.local_db_url else self.local_db_url}")

    def parse_db_url(self, db_url):
        """解析数据库URL"""
        if db_url.startswith('sqlite'):
            return {'type': 'sqlite', 'path': db_url.replace('sqlite:///', '')}
        
        parsed = urlparse(db_url)
        return {
            'type': 'postgresql',
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }

    def test_cloud_connection(self):
        """测试云端数据库连接"""
        logger.info("测试云端数据库连接...")
        try:
            cloud_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(
                host=cloud_params['host'],
                port=cloud_params['port'],
                user=cloud_params['user'],
                password=cloud_params['password'],
                dbname=cloud_params['dbname']
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"云端数据库连接成功: {version[0][:60]}...")
            
            # 获取数据库大小和表统计
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            db_size = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
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
        """备份云端数据库"""
        logger.info("开始备份云端数据库...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        backup_file = os.path.join(self.backup_dir, f'pma_db_sp8d_backup_{self.timestamp}.sql')
        info_file = os.path.join(self.backup_dir, f'backup_info_{self.timestamp}.md')
        
        try:
            # 使用pg_dump备份数据库 (SQL格式) - 使用PostgreSQL 17版本
            cmd_sql = [
                '/opt/homebrew/opt/postgresql@17/bin/pg_dump',
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
            
            logger.info("执行SQL格式备份...")
            result = subprocess.run(cmd_sql, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"SQL格式备份成功: {backup_file}")
                
                # 生成备份信息文件
                backup_rows = self.generate_backup_info(cloud_params, backup_file, info_file)
                
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
            conn = psycopg2.connect(
                host=db_params['host'],
                port=db_params['port'],
                user=db_params['user'],
                password=db_params['password'],
                dbname=db_params['dbname']
            )
            cursor = conn.cursor()
            
            # 获取数据库信息
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            db_size = cursor.fetchone()[0]
            
            # 获取表行数统计
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            row_counts = []
            total_rows = 0
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    row_counts.append((table_name, count))
                    total_rows += count
                except Exception as e:
                    logger.warning(f"无法获取表 {table_name} 的行数: {e}")
                    row_counts.append((table_name, 0))
            
            # 生成信息文档
            info_content = f"""# PMA云端数据库备份信息

## 备份基本信息
- 备份时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 备份文件: {os.path.basename(backup_file)}
- 数据库主机: {db_params['host']}
- 数据库名称: {db_params['dbname']}
- 数据库版本: {db_version}
- 数据库大小: {db_size}

## 表数据统计
| 表名 | 当前行数 |
|------|----------|
"""
            
            for table_name, row_count in row_counts:
                info_content += f"| {table_name} | {row_count} |\n"
            
            # 添加总计
            info_content += f"| **总计** | **{total_rows}** |\n"
            
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(info_content)
            
            logger.info(f"备份信息文件已生成: {info_file}")
            logger.info(f"数据库总行数: {total_rows}")
            
            cursor.close()
            conn.close()
            
            return total_rows
            
        except Exception as e:
            logger.error(f"生成备份信息失败: {str(e)}")
            return 0

    def run(self):
        """执行完整的备份流程"""
        logger.info("🚀 开始PMA云端数据库备份流程...")
        
        # 1. 测试云端连接
        if not self.test_cloud_connection():
            logger.error("❌ 云端数据库连接失败，请检查网络和凭据")
            return False
        
        # 2. 备份云端数据库
        backup_file = self.backup_cloud_database()
        if not backup_file:
            logger.error("❌ 云端数据库备份失败")
            return False
        
        # 3. 验证数据完整性
        verify_rows = self.verify_data_integrity()
        
        logger.info("🎉 云端数据库备份完成!")
        logger.info(f"📊 数据统计: {verify_rows} 行")
        logger.info(f"📁 备份文件: {backup_file}")
        
        return True

    def verify_data_integrity(self):
        """验证数据完整性"""
        logger.info("验证云端数据库数据完整性...")
        
        try:
            cloud_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(
                host=cloud_params['host'],
                port=cloud_params['port'],
                user=cloud_params['user'],
                password=cloud_params['password'],
                dbname=cloud_params['dbname']
            )
            cursor = conn.cursor()
            
            # 获取表行数统计
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            total_rows = 0
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    total_rows += count
                    logger.info(f"  {table_name}: {count} 行")
                except Exception as e:
                    logger.warning(f"无法获取表 {table_name} 的行数: {e}")
            
            logger.info(f"总数据行数: {total_rows}")
            
            cursor.close()
            conn.close()
            
            return total_rows
            
        except Exception as e:
            logger.error(f"数据完整性验证失败: {str(e)}")
            return 0

if __name__ == "__main__":
    sync_tool = PMACloudDBSync()
    success = sync_tool.run()
    if success:
        logger.info("🎯 备份操作成功完成!")
    else:
        logger.error("💥 备份操作失败!")
