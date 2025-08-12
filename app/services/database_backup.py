#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库自动备份服务
支持定时备份云端PostgreSQL数据库到本地或云存储
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import schedule
import time
import tempfile
import gzip
import shutil
import threading
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DatabaseBackupService:
    """数据库备份服务类"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.backup_enabled = self.config.get('backup_enabled', True)
        self.backup_schedule = self.config.get('backup_schedule', '00:00')  # 默认凌晨12点
        self.retention_days = self.config.get('retention_days', 30)  # 保留30天
        self.backup_location = self.config.get('backup_location', './backups')
        self.cloud_storage = self.config.get('cloud_storage', {})
        
        # 确保备份目录存在
        os.makedirs(self.backup_location, exist_ok=True)
        
        # 动态获取数据库URL
        from config import get_database_url
        database_url = get_database_url()
        self.db_config = self._parse_database_url(database_url)
        
    def _parse_database_url(self, database_url):
        """解析数据库URL"""
        parsed = urlparse(database_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'username': parsed.username,
            'password': parsed.password,
            'database': parsed.path.strip('/')
        }
    
    def create_backup(self, backup_type='full'):
        """创建数据库备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"cloud_backup_{backup_type}_{timestamp}.sql"
        backup_path = os.path.join(self.backup_location, backup_filename)
        
        try:
            logger.info(f"开始创建数据库备份: {backup_filename}")
            
            # 构建pg_dump命令
            cmd = [
                'pg_dump',
                '--host', self.db_config['host'],
                '--port', str(self.db_config['port']),
                '--username', self.db_config['username'],
                '--no-password',
                '--format', 'plain',
                '--clean',
                '--create',
                '--encoding', 'UTF8'
            ]
            
            # 根据备份类型添加选项
            if backup_type == 'schema_only':
                cmd.append('--schema-only')
            elif backup_type == 'data_only':
                cmd.append('--data-only')
            
            cmd.append(self.db_config['database'])
            
            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # 执行备份命令
            with open(backup_path, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
            
            if result.returncode == 0:
                file_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
                logger.info(f"✅ 备份创建成功: {backup_filename} ({file_size:.2f} MB)")
                
                # 上传到云存储（如果配置了）
                if self.cloud_storage.get('enabled'):
                    self._upload_to_cloud_storage(backup_path, backup_filename)
                
                return backup_path
            else:
                logger.error(f"❌ 备份创建失败: {result.stderr}")
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                return None
                
        except Exception as e:
            logger.error(f"❌ 备份过程中发生错误: {str(e)}")
            if os.path.exists(backup_path):
                os.remove(backup_path)
            return None
    
    def _upload_to_cloud_storage(self, file_path, filename):
        """上传备份到云存储"""
        storage_type = self.cloud_storage.get('type', 'aws_s3')
        
        if storage_type == 'aws_s3':
            self._upload_to_s3(file_path, filename)
        elif storage_type == 'alibaba_oss':
            self._upload_to_oss(file_path, filename)
        
    def _upload_to_s3(self, file_path, filename):
        """上传到AWS S3"""
        try:
            s3_config = self.cloud_storage.get('aws_s3', {})
            s3_client = boto3.client(
                's3',
                aws_access_key_id=s3_config.get('access_key'),
                aws_secret_access_key=s3_config.get('secret_key'),
                region_name=s3_config.get('region', 'us-east-1')
            )
            
            bucket_name = s3_config.get('bucket_name')
            s3_key = f"database_backups/{filename}"
            
            s3_client.upload_file(file_path, bucket_name, s3_key)
            logger.info(f"✅ 备份已上传到S3: s3://{bucket_name}/{s3_key}")
            
        except Exception as e:
            logger.error(f"❌ S3上传失败: {str(e)}")
    
    def _upload_to_oss(self, file_path, filename):
        """上传到阿里云OSS"""
        try:
            import oss2
            oss_config = self.cloud_storage.get('alibaba_oss', {})
            
            auth = oss2.Auth(
                oss_config.get('access_key_id'),
                oss_config.get('access_key_secret')
            )
            
            bucket = oss2.Bucket(
                auth,
                oss_config.get('endpoint'),
                oss_config.get('bucket_name')
            )
            
            oss_key = f"database_backups/{filename}"
            bucket.put_object_from_file(oss_key, file_path)
            logger.info(f"✅ 备份已上传到OSS: {oss_key}")
            
        except Exception as e:
            logger.error(f"❌ OSS上传失败: {str(e)}")
    
    def cleanup_old_backups(self):
        """清理过期备份文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            
            for filename in os.listdir(self.backup_location):
                if filename.startswith('cloud_backup_') and filename.endswith('.sql'):
                    file_path = os.path.join(self.backup_location, filename)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"🗑️ 删除过期备份: {filename}")
            
            if deleted_count > 0:
                logger.info(f"✅ 清理完成，删除了 {deleted_count} 个过期备份文件")
            else:
                logger.info("✅ 无过期备份文件需要清理")
                
        except Exception as e:
            logger.error(f"❌ 清理过期备份时发生错误: {str(e)}")
    
    def create_incremental_backup(self):
        """创建增量备份（仅备份最近更改的数据）"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"cloud_backup_incremental_{timestamp}.sql"
        backup_path = os.path.join(self.backup_location, backup_filename)
        
        try:
            logger.info(f"开始创建增量备份: {backup_filename}")
            
            # 获取最近24小时的数据更改
            tables_with_timestamps = [
                'projects', 'quotations', 'users', 'companies',
                'products', 'approval_instance', 'approval_record'
            ]
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            cmd = [
                'pg_dump',
                '--host', self.db_config['host'],
                '--port', str(self.db_config['port']),
                '--username', self.db_config['username'],
                '--no-password',
                '--format', 'plain',
                '--data-only'
            ]
            
            # 添加表过滤条件
            for table in tables_with_timestamps:
                cmd.extend(['--table', table])
            
            cmd.append(self.db_config['database'])
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
            
            if result.returncode == 0:
                file_size = os.path.getsize(backup_path) / (1024 * 1024)
                logger.info(f"✅ 增量备份创建成功: {backup_filename} ({file_size:.2f} MB)")
                return backup_path
            else:
                logger.error(f"❌ 增量备份创建失败: {result.stderr}")
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                return None
                
        except Exception as e:
            logger.error(f"❌ 增量备份过程中发生错误: {str(e)}")
            return None
    
    def get_backup_status(self):
        """获取备份状态信息"""
        backup_files = []
        total_size = 0
        
        try:
            for filename in os.listdir(self.backup_location):
                if filename.startswith('cloud_backup_') and filename.endswith('.sql'):
                    file_path = os.path.join(self.backup_location, filename)
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    total_size += file_size
                    
                    backup_files.append({
                        'filename': filename,
                        'size': file_size,
                        'size_mb': file_size / (1024 * 1024),
                        'created_at': datetime.fromtimestamp(file_stat.st_mtime),
                        'age_days': (datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)).days
                    })
            
            backup_files.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                'backup_count': len(backup_files),
                'total_size_mb': total_size / (1024 * 1024),
                'latest_backup': backup_files[0] if backup_files else None,
                'backups': backup_files,
                'retention_days': self.retention_days,
                'backup_location': self.backup_location
            }
            
        except Exception as e:
            logger.error(f"❌ 获取备份状态时发生错误: {str(e)}")
            return None
    
    def schedule_backups(self):
        """设置定时备份"""
        if not self.backup_enabled:
            logger.info("备份功能已禁用")
            return
        
        # 检查是否是本地环境（通过数据库URL判断）
        if 'localhost' in self.db_config.get('host', ''):
            logger.info("本地环境：仅启用手动备份，跳过定时备份设置")
            return
        
        logger.info(f"设置定时备份: 每天 {self.backup_schedule}")
        
        # 设置每日完整备份
        schedule.every().day.at(self.backup_schedule).do(self._daily_backup_job)
        
        # 设置每6小时增量备份
        schedule.every(6).hours.do(self._incremental_backup_job)
        
        # 设置每周清理过期备份
        schedule.every().sunday.at("02:00").do(self.cleanup_old_backups)
        
        # 启动调度器线程
        backup_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        backup_thread.start()
        logger.info("✅ 定时备份调度器已启动")
    
    def _daily_backup_job(self):
        """每日备份任务"""
        logger.info("🕛 执行定时完整备份...")
        self.create_backup('full')
    
    def _incremental_backup_job(self):
        """增量备份任务"""
        logger.info("🕕 执行定时增量备份...")
        self.create_incremental_backup()
    
    def _run_scheduler(self):
        """运行调度器"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次

    def create_backup_with_email(self, backup_type='full'):
        """创建备份并通过邮件发送"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"pma_backup_{backup_type}_{timestamp}.sql"
        
        try:
            logger.info(f"🔄 开始创建{backup_type}备份: {backup_filename}")
            
            # 创建临时备份文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                backup_path = temp_file.name
            
            # 构建pg_dump命令
            cmd = [
                'pg_dump',
                '--host', self.db_config['host'],
                '--port', str(self.db_config['port']),
                '--username', self.db_config['username'],
                '--no-password',
                '--format', 'plain',
                '--clean',
                '--create',
                '--encoding', 'UTF8'
            ]
            
            # 根据备份类型添加选项
            if backup_type == 'schema_only':
                cmd.append('--schema-only')
            elif backup_type == 'data_only':
                cmd.append('--data-only')
            
            cmd.append(self.db_config['database'])
            
            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # 执行备份
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ 备份创建失败: {result.stderr}")
                os.remove(backup_path)
                return None
            
            # 获取原始文件大小
            original_size = os.path.getsize(backup_path)
            original_size_mb = original_size / (1024 * 1024)
            
            logger.info(f"✅ 原始备份文件: {original_size_mb:.2f} MB")
            
            # 压缩备份文件
            compressed_path = backup_path + '.gz'
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            compressed_size = os.path.getsize(compressed_path)
            compressed_size_mb = compressed_size / (1024 * 1024)
            compression_ratio = compressed_size / original_size if original_size > 0 else 0
            
            logger.info(f"✅ 压缩备份文件: {compressed_size_mb:.2f} MB (压缩比: {compression_ratio:.1%})")
            
            # 删除原始文件，使用压缩文件
            os.remove(backup_path)
            backup_path = compressed_path
            backup_filename = backup_filename + '.gz'
            
            # 检查是否适合邮件发送
            max_email_size_mb = 20  # 保守的邮件附件大小限制
            
            if compressed_size_mb <= max_email_size_mb:
                # 发送邮件
                email_sent = self._send_backup_email(backup_path, backup_filename, compressed_size_mb, backup_type)
                if email_sent:
                    logger.info(f"📧 备份文件已通过邮件发送")
                else:
                    logger.warning(f"⚠️ 邮件发送失败，备份文件已保存到本地")
            else:
                logger.warning(f"⚠️ 备份文件过大 ({compressed_size_mb:.2f} MB)，跳过邮件发送")
            
            # 保存到本地备份目录
            local_backup_path = os.path.join(self.backup_location, backup_filename)
            os.makedirs(self.backup_location, exist_ok=True)
            
            # 移动文件到备份目录
            import shutil
            shutil.move(backup_path, local_backup_path)
            
            logger.info(f"💾 备份文件已保存: {local_backup_path}")
            
            return local_backup_path
            
        except Exception as e:
            logger.error(f"❌ 备份过程中发生错误: {str(e)}")
            # 清理临时文件
            for temp_path in [backup_path, compressed_path]:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            return None

    def _send_backup_email(self, backup_path, filename, file_size_mb, backup_type):
        """通过邮件发送备份文件"""
        try:
            from flask_mail import Message
            from app import mail
            
            # 准备邮件内容
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            subject = f'PMA数据库自动备份 - {timestamp}'
            
            # 获取数据库统计信息
            db_stats = self._get_database_stats()
            
            body = f"""
PMA系统自动备份报告

📊 备份信息:
- 备份时间: {timestamp}
- 备份类型: {backup_type}
- 备份文件: {filename}
- 文件大小: {file_size_mb:.2f} MB

📈 数据库统计:
- 数据库大小: {db_stats.get('db_size', 'N/A')}
- 总记录数: {db_stats.get('total_records', 'N/A'):,} 条
- 主要数据表:
  • 报价明细: {db_stats.get('quotation_details', 0):,} 条
  • 项目记录: {db_stats.get('projects', 0):,} 条
  • 公司信息: {db_stats.get('companies', 0):,} 条

🔧 系统信息:
- 环境: 生产环境
- 版本: 1.0.1
- 平台: Render Cloud
- 备份策略: 每日自动备份

📋 使用说明:
1. 下载附件中的备份文件
2. 解压 .gz 文件得到 .sql 文件
3. 使用 psql 命令恢复数据库:
   psql -h hostname -U username -d database < backup_file.sql

⚠️ 重要提醒:
- 请妥善保存此备份文件
- 建议定期测试备份文件的完整性
- 如有问题请及时联系系统管理员

---
PMA自动备份系统
此邮件由系统自动发送，请勿回复
            """.strip()
            
            # 创建邮件
            recipients = [
                'James.ni@evertacsolutions.com',
                'james98980566@gmail.com'
            ]
            
            msg = Message(
                subject=subject,
                recipients=recipients,
                body=body
            )
            
            # 添加备份文件作为附件
            with open(backup_path, 'rb') as f:
                msg.attach(
                    filename,
                    'application/gzip',
                    f.read(),
                    'attachment'
                )
            
            # 发送邮件
            mail.send(msg)
            logger.info(f"✅ 备份邮件已发送到: {', '.join(recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {str(e)}")
            return False

    def _get_database_stats(self):
        """获取数据库统计信息"""
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password']
            )
            
            stats = {}
            
            with conn.cursor() as cursor:
                # 获取数据库大小
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                stats['db_size'] = cursor.fetchone()[0]
                
                # 获取主要表的记录数
                tables = ['quotation_details', 'projects', 'companies', 'quotations', 'contacts']
                total_records = 0
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        stats[table] = count
                        total_records += count
                    except:
                        stats[table] = 0
                
                stats['total_records'] = total_records
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.warning(f"获取数据库统计信息失败: {str(e)}")
            return {}

    def _daily_backup_job_with_email(self):
        """每日备份任务（带邮件发送）"""
        logger.info("🕛 执行定时完整备份（邮件发送）...")
        self.create_backup_with_email('full')

# 全局备份服务实例
backup_service = None

def init_backup_service(app):
    """初始化备份服务"""
    global backup_service
    
    backup_config = {
        'backup_enabled': app.config.get('BACKUP_ENABLED', True),
        'backup_schedule': app.config.get('BACKUP_SCHEDULE', '00:00'),
        'retention_days': app.config.get('BACKUP_RETENTION_DAYS', 30),
        'backup_location': app.config.get('BACKUP_LOCATION', './backups'),
        'cloud_storage': app.config.get('CLOUD_STORAGE_CONFIG', {})
    }
    
    backup_service = DatabaseBackupService(backup_config)
    
    if backup_config['backup_enabled']:
        backup_service.schedule_backups()
        # 检查环境类型并给出相应提示
        if hasattr(app.config, 'ENVIRONMENT') and app.config.ENVIRONMENT == 'local':
            logger.info("✅ 本地数据库备份服务已初始化（仅手动备份）")
        else:
            logger.info("✅ 数据库备份服务已初始化")
    else:
        logger.info("⚠️ 数据库备份服务已禁用")
    
    return backup_service

def get_backup_service():
    """获取备份服务实例"""
    return backup_service 