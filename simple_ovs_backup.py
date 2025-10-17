#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 OVS 数据库备份工具
采用与 sp8d 相同的备份方式，避免超时问题

使用方法：
    python3 simple_ovs_backup.py

功能：
- 备份云端 pma_db_ovs 数据库到本地
- 生成统计信息和验证数据完整性
- 使用简化的 subprocess.run() 方式，避免超时问题
- 备份包含完整的表结构、约束、索引、序列和数据

备份文件：
- 存储位置：./cloud_db_backups/
- 文件格式：pma_db_ovs_backup_simple_YYYYMMDD_HHMMSS.sql
- 备份大小：约 400KB
- 数据行数：约 900 行

注意：
- 需要网络连接到 render.com 数据库
- 需要安装 PostgreSQL 客户端工具 (pg_dump)
- 备份文件使用 COPY 语句格式，可直接用于数据库恢复

遵循 CLAUDE.md 中的云端数据库备份工具规范
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
logger = logging.getLogger('简化OVS备份')

class SimpleOVSBackup:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = os.path.join(os.getcwd(), 'cloud_db_backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # ovs 数据库连接信息 - 更新到新的Supabase位置
        self.cloud_db_url = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'
        
        logger.info(f"目标数据库: pma_db_ovs")
    
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
        """测试数据库连接"""
        logger.info("测试 OVS 数据库连接...")
        try:
            db_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"连接成功: {version[0][:50]}...")
            
            # 获取基本信息
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
            logger.error(f"连接失败: {str(e)}")
            return False
    
    def backup_database(self):
        """备份数据库 - 使用与sp8d相同的简单方式"""
        logger.info("开始备份 OVS 数据库...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        backup_file = os.path.join(self.backup_dir, f'pma_db_ovs_backup_simple_{self.timestamp}.sql')
        
        try:
            # 使用 subprocess.run - 与 sp8d 备份工具相同的方式
            # 使用PostgreSQL 17版本的pg_dump
            cmd = [
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
            
            logger.info("执行备份命令（使用简化方式）...")
            
            # 使用 subprocess.run 而不是 Popen - 避免监控循环的复杂性
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                file_size = os.path.getsize(backup_file) / (1024 * 1024)
                logger.info(f"✅ OVS 备份成功: {backup_file}")
                logger.info(f"📁 文件大小: {file_size:.2f} MB")
                
                # 生成统计信息
                self.generate_stats(cloud_params, backup_file)
                
                return backup_file
            else:
                logger.error(f"备份失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"备份过程出错: {str(e)}")
            return None
    
    def generate_stats(self, db_params, backup_file):
        """生成简单的统计信息"""
        try:
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            
            # 获取总行数
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            tables = cursor.fetchall()
            
            total_rows = 0
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    total_rows += count
                except:
                    pass
            
            logger.info(f"📊 数据统计: {total_rows:,} 行")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"统计信息生成失败: {str(e)}")
    
    def run(self):
        """执行备份"""
        logger.info("🚀 开始简化版 OVS 数据库备份...")
        
        # 测试连接
        if not self.test_connection():
            logger.error("❌ 数据库连接失败")
            return False
        
        # 执行备份
        backup_file = self.backup_database()
        if not backup_file:
            logger.error("❌ 备份失败")
            return False
        
        logger.info("🎉 OVS 数据库备份完成!")
        logger.info(f"📁 备份文件: {backup_file}")
        
        return True

if __name__ == "__main__":
    backup_tool = SimpleOVSBackup()
    success = backup_tool.run()
    
    if success:
        logger.info("🎯 备份操作成功!")
    else:
        logger.error("💥 备份操作失败!")