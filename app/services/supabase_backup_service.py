#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地数据库备份服务
功能：
- 备份数据库到本地文件系统或 NAS WebDAV
- 自动压缩和清理
- Web UI 管理备份
"""
import os
import sys
import gzip
import shutil
import logging
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import threading
import uuid

logger = logging.getLogger('BackupService')


class SupabaseBackupService:
    """本地数据库备份服务（支持 NAS WebDAV 持久化）"""

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
        """获取 WebDAV 客户端单例"""
        from app.utils.synology_webdav_client import get_synology_webdav_client
        return get_synology_webdav_client()

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
                self.tasks[task_id]['message'] = '正在备份数据库...'

                results = self.create_backup(db_type)

                if not results or len(results) == 0:
                    raise Exception("备份失败：未生成备份文件")

                self.tasks[task_id]['progress'] = 100
                self.tasks[task_id]['status'] = 'completed'
                self.tasks[task_id]['message'] = '备份完成'
                self.tasks[task_id]['results'] = results

            except Exception as e:
                logger.error(f"备份任务失败: task_id={task_id}, error={e}", exc_info=True)
                self.tasks[task_id]['status'] = 'failed'
                self.tasks[task_id]['message'] = f'备份失败: {str(e)}'

    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        return self.tasks.get(task_id, {
            'status': 'not_found',
            'message': '任务不存在'
        })

    def create_backup(self, db_type: str = 'auto') -> List[Dict]:
        """创建数据库备份 - 备份当前DATABASE_URL指向的数据库"""
        results = []

        try:
            logger.info("备份当前数据库...")

            # NAS 模式：输出到临时目录，上传后删除
            output_dir = self.temp_dir if self.use_nas_storage else None

            result = self._backup_current_database(output_dir=output_dir)
            if result:
                results.append(result)

            logger.info(f"备份完成，共 {len(results)} 个文件")
            return results

        except Exception as e:
            logger.error(f"备份过程出错: {e}")
            raise

    def _backup_current_database(self, output_dir: Optional[str] = None) -> Optional[Dict]:
        """备份当前DATABASE_URL指向的数据库 - 使用通用备份脚本"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            backup_script = os.path.join(self.project_root, 'backup_current_database.py')

            if not os.path.exists(backup_script):
                logger.error(f"通用备份脚本不存在: {backup_script}")
                return None

            # 如果指定了输出目录，通过环境变量传递
            env = os.environ.copy()
            if output_dir:
                env['BACKUP_OUTPUT_DIR'] = output_dir

            logger.info(f"执行通用备份脚本: {backup_script}")
            result = subprocess.run(
                [sys.executable, backup_script],
                capture_output=True,
                text=True,
                timeout=600,
                env=env
            )

            if result.returncode != 0:
                logger.error(f"备份脚本执行失败: {result.stderr}")
                return None

            # 在指定输出目录或默认备份目录中查找
            search_dir = output_dir or self.backup_dir
            backup_file = self._find_latest_backup_auto(timestamp, search_dir)
            if not backup_file or not os.path.exists(backup_file):
                # 回退：在默认备份目录中查找（脚本可能忽略了 BACKUP_OUTPUT_DIR）
                if output_dir:
                    backup_file = self._find_latest_backup_auto(timestamp, self.backup_dir)
                if not backup_file or not os.path.exists(backup_file):
                    logger.error(f"未找到备份文件（timestamp: {timestamp}）")
                    return None

            db_type = self._extract_db_type_from_filename(backup_file)
            compressed_file = self._compress_file(backup_file)
            filename = os.path.basename(compressed_file)

            if self.use_nas_storage:
                # NAS 模式：上传到 WebDAV
                remote_path = f"{self.nas_backup_path}/{filename}"
                client = self._get_webdav_client()

                with open(compressed_file, 'rb') as f:
                    upload_result = client.upload_file(f.read(), remote_path, 'application/gzip')

                if not upload_result:
                    raise RuntimeError(f"上传备份到 NAS 失败: {remote_path}")

                file_size = os.path.getsize(compressed_file)

                # 清理临时文件
                os.remove(compressed_file)
                if os.path.exists(backup_file):
                    os.remove(backup_file)

                logger.info(f"备份已上传到 NAS: {remote_path} ({file_size / 1024 / 1024:.1f} MB)")
                return {
                    'db_type': db_type,
                    'filename': filename,
                    'location': 'nas',
                    'path': remote_path,
                    'size': file_size
                }
            else:
                # 本地模式：保存到备份目录
                final_path = os.path.join(self.backup_dir, filename)
                if compressed_file != final_path:
                    shutil.move(compressed_file, final_path)
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                return {
                    'db_type': db_type,
                    'filename': filename,
                    'location': 'local',
                    'path': final_path,
                    'size': os.path.getsize(final_path)
                }

        except Exception as e:
            logger.error(f"备份当前数据库失败: {e}")
            raise

    def _find_latest_backup(self, db_type: str, timestamp: str) -> Optional[str]:
        """查找最新生成的备份文件（精确匹配完整时间戳）"""
        if db_type == 'sp8d':
            expected_filename = f'pma_db_sp8d_backup_{timestamp}.sql'
        else:
            expected_filename = f'pma_db_ovs_backup_{timestamp}.sql'

        filepath = os.path.join(self.backup_dir, expected_filename)
        if os.path.exists(filepath):
            logger.info(f"找到备份文件: {expected_filename}")
            return filepath

        logger.error(f"未找到备份文件: {expected_filename}")
        return None

    def _find_latest_backup_auto(self, timestamp: str, search_dir: Optional[str] = None) -> Optional[str]:
        """自动识别最新备份文件（支持 local/sp8d/ovs/unknown）"""
        target_dir = search_dir or self.backup_dir
        patterns = [
            f'pma_db_local_backup_{timestamp}.sql',
            f'pma_db_local_backup_{timestamp}.db',
            f'pma_db_sp8d_backup_{timestamp}.sql',
            f'pma_db_ovs_backup_{timestamp}.sql',
            f'pma_db_unknown_backup_{timestamp}.sql'
        ]

        for pattern in patterns:
            filepath = os.path.join(target_dir, pattern)
            if os.path.exists(filepath):
                logger.info(f"找到备份文件: {pattern}")
                return filepath

        logger.error(f"未找到任何备份文件（timestamp: {timestamp}）")
        return None

    def _extract_db_type_from_filename(self, filepath: str) -> str:
        """从文件名提取数据库类型"""
        filename = os.path.basename(filepath)

        if 'local' in filename:
            return 'local'
        elif 'sp8d' in filename:
            return 'sp8d'
        elif 'ovs' in filename:
            return 'ovs'
        else:
            return 'unknown'

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

    # ==================== 列表/下载/删除 ====================

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

                db_type = self._extract_db_type_from_filename(name)
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
                filepath = os.path.join(self.backup_dir, filename)
                if not os.path.isfile(filepath):
                    continue
                if filename.endswith('.sql.gz') or filename.endswith('.sql'):
                    stat = os.stat(filepath)

                    backups.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'location': 'local',
                        'db_type': self._extract_db_type_from_filename(filename)
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
        """从 NAS 下载备份文件内容（返回 bytes）"""
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
            created_at = datetime.fromisoformat(backup['created_at'].replace('Z', '+00:00'))
            if created_at < cutoff_date:
                if self.delete_backup(backup['filename']):
                    deleted_count += 1

        logger.info(f"清理完成，删除了 {deleted_count} 个备份")
        return deleted_count

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
            'db_type': self.current_db_type,
            'backup_dir': self.backup_dir,
            'use_nas_storage': self.use_nas_storage,
            'nas_backup_path': self.nas_backup_path,
        }


# 全局备份服务实例
backup_service = None


def init_backup_service():
    """初始化备份服务"""
    global backup_service
    if backup_service is None:
        backup_service = SupabaseBackupService()
    return backup_service


def get_backup_service() -> SupabaseBackupService:
    """获取备份服务实例"""
    global backup_service
    if backup_service is None:
        backup_service = init_backup_service()
    return backup_service
