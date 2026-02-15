#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份服务
功能：
- 直接执行 pg_dump 备份数据库（无 subprocess 脚本间接层）
- 自动压缩和清理
- Web UI 管理备份
- 定时备份和内部消息通知
"""
import os
import sys
import gzip
import shutil
import logging
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse
import threading
import uuid

logger = logging.getLogger('BackupService')


class BackupService:
    """数据库备份服务"""

    def __init__(self):
        """初始化备份服务"""
        # 配置路径
        self.project_root = self._get_project_root()
        self.backup_dir = os.path.join(self.project_root, 'cloud_db_backups')
        self.temp_dir = os.path.join(self.backup_dir, 'temp')
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        # 识别当前数据库类型
        self.current_db_type = self._detect_current_db_type()

        # 备份保留天数
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))

        # 任务状态跟踪
        self.tasks = {}

        # 检测是否使用 NAS WebDAV 存储
        self.use_nas_storage = self._detect_nas_storage()
        if self.use_nas_storage:
            self.nas_backup_path = f"/backup/{self.current_db_type}"
            logger.info(f"备份服务已启动 ({self.current_db_type}, NAS WebDAV {self.nas_backup_path}, 保留{self.retention_days}天)")
        else:
            self.nas_backup_path = None
            logger.info(f"备份服务已启动 ({self.current_db_type}, 本地存储, 保留{self.retention_days}天)")

    def _get_project_root(self) -> str:
        """获取项目根目录"""
        current = os.path.dirname(os.path.abspath(__file__))
        while current != '/':
            if os.path.exists(os.path.join(current, 'run.py')):
                return current
            current = os.path.dirname(current)
        return os.getcwd()

    def _detect_current_db_type(self) -> str:
        """识别当前连接的数据库类型"""
        db_type = os.getenv('PMA_DB_TYPE') or os.getenv('SUPABASE_DB_TYPE')
        if db_type and db_type in ('sp8d', 'ovs'):
            return db_type

        db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', '')
        if 'localhost' in db_uri or '127.0.0.1' in db_uri or 'sqlite' in db_uri:
            return 'local'

        return 'local'

    def _detect_nas_storage(self) -> bool:
        """检测 NAS WebDAV 是否可用于备份存储"""
        if os.getenv('NAS_STORAGE_ENABLED', 'false').lower() != 'true':
            return False
        try:
            from app.utils.synology_webdav_client import get_synology_webdav_client
            client = get_synology_webdav_client()
            return client.is_configured and client.is_available
        except Exception:
            return False

    def _get_webdav_client(self):
        """获取 WebDAV 客户端"""
        from app.utils.synology_webdav_client import get_synology_webdav_client
        return get_synology_webdav_client()

    # ==================== pg_dump 内联逻辑 ====================

    def _find_pg_dump(self) -> Optional[str]:
        """检测 pg_dump 可执行文件路径"""
        pg_dump = shutil.which('pg_dump')
        if pg_dump:
            return pg_dump

        # macOS Homebrew fallback
        fallback_paths = [
            '/opt/homebrew/opt/postgresql@17/bin/pg_dump',
            '/opt/homebrew/opt/postgresql@16/bin/pg_dump',
            '/opt/homebrew/bin/pg_dump',
            '/usr/local/bin/pg_dump',
            '/usr/bin/pg_dump',
        ]
        for path in fallback_paths:
            if os.path.exists(path):
                return path

        return None

    def _parse_database_url(self, db_url: str) -> Dict:
        """解析 DATABASE_URL 获取连接参数"""
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': str(parsed.port or 5432),
            'user': parsed.username or 'postgres',
            'password': parsed.password or '',
            'dbname': parsed.path.lstrip('/') if parsed.path else 'pma',
        }

    def _execute_pg_dump(self, task_id: Optional[str] = None, output_dir: Optional[str] = None) -> Optional[str]:
        """直接执行 pg_dump，从 Flask config 读取 DATABASE_URL"""
        from flask import current_app

        db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if not db_url or 'sqlite' in db_url:
            logger.warning("当前使用 SQLite，跳过 pg_dump")
            return None

        pg_dump = self._find_pg_dump()
        if not pg_dump:
            raise RuntimeError("未找到 pg_dump 工具，请确保 PostgreSQL 客户端已安装")

        params = self._parse_database_url(db_url)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'pma_db_{self.current_db_type}_backup_{timestamp}.sql'
        target_dir = output_dir or self.backup_dir
        output_path = os.path.join(target_dir, filename)

        if task_id and task_id in self.tasks:
            self.tasks[task_id]['progress'] = 20
            self.tasks[task_id]['message'] = '正在执行 pg_dump...'

        env = os.environ.copy()
        env['PGPASSWORD'] = params['password']

        cmd = [
            pg_dump,
            '-h', params['host'],
            '-p', params['port'],
            '-U', params['user'],
            '--no-owner',
            '--no-privileges',
            '-F', 'p',
            '-f', output_path,
            params['dbname'],
        ]

        logger.info(f"执行 pg_dump: {params['dbname']}@{params['host']}:{params['port']}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=600,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or '未知错误'
            logger.error(f"pg_dump 失败: {error_msg}")
            raise RuntimeError(f"pg_dump 执行失败: {error_msg}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("pg_dump 输出文件为空或不存在")

        logger.info(f"pg_dump 完成: {filename} ({os.path.getsize(output_path) / 1024 / 1024:.1f} MB)")
        return output_path

    # ==================== 备份核心方法 ====================

    def create_backup_async(self, db_type: str = 'both') -> str:
        """异步创建备份（返回任务ID）"""
        from flask import current_app

        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'message': '正在启动备份任务...',
            'created_at': datetime.now()
        }

        app = current_app._get_current_object()

        thread = threading.Thread(
            target=self._create_backup_task,
            args=(task_id, db_type, app)
        )
        thread.daemon = True
        thread.start()

        return task_id

    def _create_backup_task(self, task_id: str, db_type: str, app):
        """后台备份任务"""
        with app.app_context():
            try:
                self.tasks[task_id]['progress'] = 10
                self.tasks[task_id]['message'] = '正在连接数据库...'

                results = self.create_backup(db_type, task_id=task_id)

                if not results or len(results) == 0:
                    raise Exception("备份失败：未生成备份文件")

                self.tasks[task_id]['progress'] = 100
                self.tasks[task_id]['status'] = 'completed'
                self.tasks[task_id]['message'] = '备份完成'
                self.tasks[task_id]['results'] = results

                # 手动备份：总是推送通知
                self._send_backup_notification(True, results)

            except Exception as e:
                logger.error(f"备份任务失败: task_id={task_id}, error={e}", exc_info=True)
                self.tasks[task_id]['status'] = 'failed'
                self.tasks[task_id]['message'] = f'备份失败: {str(e)}'

                # 手动备份失败：推送通知
                self._send_backup_notification(False, error_message=str(e))

    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        return self.tasks.get(task_id, {
            'status': 'not_found',
            'message': '任务不存在'
        })

    def create_backup(self, db_type: str = 'auto', task_id: Optional[str] = None) -> List[Dict]:
        """创建数据库备份 - 直接执行 pg_dump"""
        results = []

        try:
            logger.info("备份当前数据库...")

            # NAS 模式：pg_dump 输出到临时目录，避免占用容器空间
            output_dir = self.temp_dir if self.use_nas_storage else None

            # 直接执行 pg_dump
            sql_file = self._execute_pg_dump(task_id=task_id, output_dir=output_dir)
            if not sql_file:
                logger.warning("pg_dump 跳过（可能是 SQLite 环境）")
                return results

            if task_id and task_id in self.tasks:
                self.tasks[task_id]['progress'] = 60
                self.tasks[task_id]['message'] = '正在压缩备份文件...'

            # 压缩
            compressed_file = self._compress_file(sql_file)

            if task_id and task_id in self.tasks:
                self.tasks[task_id]['progress'] = 85
                self.tasks[task_id]['message'] = '正在保存备份...'

            filename = os.path.basename(compressed_file)

            if self.use_nas_storage:
                # NAS 模式：上传到 WebDAV
                if task_id and task_id in self.tasks:
                    self.tasks[task_id]['message'] = '正在上传到 NAS...'

                remote_path = f"{self.nas_backup_path}/{filename}"
                client = self._get_webdav_client()
                with open(compressed_file, 'rb') as f:
                    upload_result = client.upload_file(f.read(), remote_path, 'application/gzip')

                if not upload_result:
                    raise RuntimeError(f"上传备份到 NAS 失败: {remote_path}")

                file_size = os.path.getsize(compressed_file)

                # 清理临时文件
                os.remove(compressed_file)
                if os.path.exists(sql_file):
                    os.remove(sql_file)

                result = {
                    'db_type': self.current_db_type,
                    'filename': filename,
                    'location': 'nas',
                    'path': remote_path,
                    'size': file_size
                }
            else:
                # 本地模式：移动到备份目录
                final_path = os.path.join(self.backup_dir, filename)
                if compressed_file != final_path:
                    shutil.move(compressed_file, final_path)

                # 删除原始 SQL 文件
                if os.path.exists(sql_file):
                    os.remove(sql_file)

                result = {
                    'db_type': self.current_db_type,
                    'filename': filename,
                    'location': 'local',
                    'path': final_path,
                    'size': os.path.getsize(final_path)
                }

            results.append(result)
            logger.info(f"备份完成: {result['filename']} ({result['size'] / 1024 / 1024:.1f} MB, {result['location']})")
            return results

        except Exception as e:
            logger.error(f"备份过程出错: {e}")
            raise

    # ==================== 通知 ====================

    def _send_backup_notification(self, success: bool, results=None, error_message=None):
        """备份结果推送内部消息给所有 admin 用户"""
        if os.getenv('BACKUP_NOTIFY_ENABLED', 'true').lower() != 'true':
            return

        try:
            from app.models.message import Message
            from app.models.user import User
            from app import db

            admin_users = User.query.filter_by(role='admin', is_active=True).all()
            if not admin_users:
                return

            db_type = self.current_db_type.upper()

            if success and results:
                title = f'数据库备份完成 ({db_type})'
                content = f"文件: {results[0]['filename']}, 大小: {results[0]['size'] / 1024 / 1024:.1f} MB"
                msg_type = 'backup_success'
            else:
                title = f'数据库备份失败 ({db_type})'
                content = f"错误: {error_message or '未知错误'}"
                msg_type = 'backup_failure'

            for admin in admin_users:
                msg = Message(
                    message_type=msg_type,
                    sender_id=admin.id,
                    recipient_id=admin.id,
                    title=title,
                    content=content,
                    related_object_type='backup',
                    related_object_id=0
                )
                db.session.add(msg)
            db.session.commit()
            logger.info(f"备份通知已发送给 {len(admin_users)} 个管理员")

        except Exception as e:
            logger.warning(f"发送备份通知失败（不影响备份）: {e}")

    # ==================== 文件管理 ====================

    def _compress_file(self, filepath: str) -> str:
        """压缩文件（gzip）"""
        compressed_path = filepath + '.gz'

        logger.info(f"压缩文件: {filepath}")
        with open(filepath, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

        original_size = os.path.getsize(filepath)
        compressed_size = os.path.getsize(compressed_path)
        compression_ratio = (1 - compressed_size / original_size) * 100

        logger.info(f"压缩完成: {original_size / 1024 / 1024:.2f} MB -> {compressed_size / 1024 / 1024:.2f} MB (压缩率: {compression_ratio:.1f}%)")

        return compressed_path

    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        if self.use_nas_storage:
            return self._list_nas_backups()
        return self._list_local_backups()

    def _list_nas_backups(self) -> List[Dict]:
        """列出 NAS WebDAV 上的备份"""
        try:
            client = self._get_webdav_client()
            files = client.list_directory(self.nas_backup_path, depth=1)
            backups = []

            for f in files:
                name = f.get('name', '')
                if not (name.endswith('.sql.gz') or name.endswith('.sql')):
                    continue

                # 识别 db_type from filename
                if 'sp8d' in name:
                    db_type = 'sp8d'
                elif 'ovs' in name:
                    db_type = 'ovs'
                elif 'local' in name:
                    db_type = 'local'
                else:
                    db_type = 'unknown'

                # 从文件名解析时间戳 (pma_db_sp8d_backup_20260215_030000.sql.gz)
                created_at = self._parse_backup_timestamp(name)

                backups.append({
                    'filename': name,
                    'size': int(f.get('size', 0)),
                    'created_at': created_at,
                    'location': 'nas',
                    'db_type': db_type
                })

            return sorted(backups, key=lambda x: x['created_at'], reverse=True)

        except Exception as e:
            logger.error(f"获取 NAS 备份列表失败: {e}")
            return []

    @staticmethod
    def _parse_backup_timestamp(filename: str) -> str:
        """从备份文件名解析时间戳"""
        import re
        match = re.search(r'(\d{8})_(\d{6})', filename)
        if match:
            date_str, time_str = match.group(1), match.group(2)
            try:
                dt = datetime.strptime(f"{date_str}_{time_str}", '%Y%m%d_%H%M%S')
                return dt.isoformat()
            except ValueError:
                pass
        return datetime.now().isoformat()

    def _list_local_backups(self) -> List[Dict]:
        """列出本地备份"""
        backups = []

        try:
            for filename in os.listdir(self.backup_dir):
                # 跳过子目录（如 temp/）
                filepath = os.path.join(self.backup_dir, filename)
                if not os.path.isfile(filepath):
                    continue

                if filename.endswith('.sql.gz') or filename.endswith('.sql'):
                    stat = os.stat(filepath)

                    # 识别 db_type
                    if 'sp8d' in filename:
                        db_type = 'sp8d'
                    elif 'ovs' in filename:
                        db_type = 'ovs'
                    elif 'local' in filename:
                        db_type = 'local'
                    else:
                        db_type = 'unknown'

                    backups.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'location': 'local',
                        'db_type': db_type
                    })

            return sorted(backups, key=lambda x: x['created_at'], reverse=True)

        except Exception as e:
            logger.error(f"获取本地备份列表失败: {e}")
            return []

    def get_download_url(self, storage_path: str) -> str:
        """获取下载 URL"""
        filename = os.path.basename(storage_path)
        return f'/backup/download/{filename}'

    def delete_backup(self, storage_path: str) -> bool:
        """删除备份"""
        filename = os.path.basename(storage_path)
        if self.use_nas_storage:
            return self._delete_nas_backup(filename)
        return self._delete_local_backup(filename)

    def _delete_nas_backup(self, filename: str) -> bool:
        """删除 NAS 上的备份"""
        try:
            client = self._get_webdav_client()
            remote_path = f"{self.nas_backup_path}/{filename}"
            result = client.delete_file(remote_path)
            if result:
                logger.info(f"删除 NAS 备份: {filename}")
            return result
        except Exception as e:
            logger.error(f"删除 NAS 备份失败: {e}")
            return False

    def download_backup_content(self, filename: str) -> Optional[bytes]:
        """从 NAS 下载备份文件内容"""
        if not self.use_nas_storage:
            return None
        try:
            client = self._get_webdav_client()
            remote_path = f"{self.nas_backup_path}/{filename}"
            return client.download_file(remote_path)
        except Exception as e:
            logger.error(f"下载 NAS 备份失败: {e}")
            return None

    def _delete_local_backup(self, filename: str) -> bool:
        """删除本地备份"""
        try:
            filepath = os.path.join(self.backup_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"删除本地备份: {filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除本地备份失败: {e}")
            return False

    def cleanup_old_backups(self, days: Optional[int] = None) -> int:
        """清理旧备份"""
        if days is None:
            days = self.retention_days

        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        logger.info(f"清理 {days} 天前的备份（{cutoff_date.date()} 之前）")

        backups = self.list_backups()
        for backup in backups:
            created_at = datetime.fromisoformat(backup['created_at'].replace('Z', '').replace('+00:00', ''))
            if created_at < cutoff_date:
                if self.delete_backup(backup['filename']):
                    deleted_count += 1

        logger.info(f"清理完成，删除了 {deleted_count} 个备份")
        return deleted_count

    # ==================== 统计/配置/健康 ====================

    def get_storage_usage(self) -> Dict:
        """获取存储使用情况"""
        backups = self.list_backups()
        total_size = sum(b['size'] for b in backups)

        location = f'NAS WebDAV ({self.nas_backup_path})' if self.use_nas_storage else '本地文件系统'
        return {
            'total_backups': len(backups),
            'total_size': total_size,
            'total_size_mb': total_size / 1024 / 1024,
            'location': location,
            'retention_days': self.retention_days
        }

    def get_backup_settings(self) -> Dict:
        """获取备份配置"""
        return {
            'retention_days': self.retention_days,
            'auto_backup_enabled': os.getenv('BACKUP_AUTO_ENABLED', 'true').lower() == 'true',
            'auto_backup_time': os.getenv('BACKUP_AUTO_TIME', '03:00'),
            'notify_enabled': os.getenv('BACKUP_NOTIFY_ENABLED', 'true').lower() == 'true',
            'db_type': self.current_db_type,
            'backup_dir': self.backup_dir,
            'use_nas_storage': self.use_nas_storage,
            'nas_backup_path': self.nas_backup_path,
        }

    def get_health_status(self) -> Dict:
        """获取健康状态（最近24h内是否有备份）"""
        backups = self.list_backups()
        if not backups:
            return {
                'is_healthy': False,
                'last_backup_time': None,
                'last_backup_age_hours': None,
                'message': '从未备份',
            }

        last = backups[0]
        last_time = datetime.fromisoformat(last['created_at'].replace('Z', '').replace('+00:00', ''))
        age_hours = (datetime.now() - last_time).total_seconds() / 3600

        return {
            'is_healthy': age_hours < 24,
            'last_backup_time': last['created_at'],
            'last_backup_age_hours': round(age_hours, 1),
            'message': '健康' if age_hours < 24 else f'最近 {round(age_hours)}h 无备份',
        }

    def get_backup_statistics(self) -> Dict:
        """获取备份统计数据"""
        backups = self.list_backups()
        total_size = sum(b['size'] for b in backups)
        sp8d_count = sum(1 for b in backups if b['db_type'] == 'sp8d')
        ovs_count = sum(1 for b in backups if b['db_type'] == 'ovs')
        local_count = sum(1 for b in backups if b['db_type'] == 'local')

        latest = backups[0] if backups else None

        return {
            'total_count': len(backups),
            'total_size_mb': round(total_size / 1024 / 1024, 1),
            'sp8d_count': sp8d_count,
            'ovs_count': ovs_count,
            'local_count': local_count,
            'latest_backup': latest,
        }


# 向后兼容别名
SupabaseBackupService = BackupService

# 全局备份服务实例
backup_service = None


def init_backup_service():
    """初始化备份服务"""
    global backup_service
    if backup_service is None:
        backup_service = BackupService()
    return backup_service


def get_backup_service() -> BackupService:
    """获取备份服务实例"""
    global backup_service
    if backup_service is None:
        backup_service = init_backup_service()
    return backup_service
