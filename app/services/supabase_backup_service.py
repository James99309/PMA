#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 自动备份服务
功能：
- 自动备份数据库到 Supabase Storage 或本地
- 支持环境自适应（本地/云端）
- 复用 FORCE_CLOUD_UPLOAD 环境变量
- 自动压缩和清理
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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SupabaseBackupService')


class SupabaseBackupService:
    """Supabase 自动备份服务"""

    def __init__(self):
        """初始化备份服务 - 环境自适应"""
        # 🔍 调试：记录初始化调用栈
        import traceback
        logger.info("🔍 备份服务初始化被调用")
        logger.info(f"🔍 调用栈：\n{''.join(traceback.format_stack()[-5:])}")

        # 检查是否强制使用云端存储
        force_cloud = os.getenv('FORCE_CLOUD_UPLOAD', '').lower() in ['true', '1', 'yes']
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        # 🔍 调试：记录环境变量状态
        logger.info(f"🔍 环境变量 FORCE_CLOUD_UPLOAD: {os.getenv('FORCE_CLOUD_UPLOAD')}")
        logger.info(f"🔍 环境变量 force_cloud (解析后): {force_cloud}")
        logger.info(f"🔍 环境变量 SUPABASE_URL: {supabase_url[:30] if supabase_url else None}...")
        logger.info(f"🔍 环境变量 SUPABASE_KEY: {'已设置' if supabase_key else '未设置'}")
        logger.info(f"🔍 环境变量 SUPABASE_BUCKET_BACKUP: {os.getenv('SUPABASE_BUCKET_BACKUP')}")

        # 只有在强制云端存储且配置完整时才使用云端
        if force_cloud and supabase_url and supabase_key:
            # 导入 Supabase 存储客户端
            try:
                from app.utils.supabase_client import SupabaseStorageClient
                self.storage_client = SupabaseStorageClient()
                self.use_cloud_storage = not self.storage_client.use_local_storage
                self.is_local_env = self.storage_client.is_local_env

                # 🔍 调试：记录存储客户端初始化结果
                logger.info(f"🔍 存储客户端初始化成功")
                logger.info(f"🔍 storage_client.use_local_storage: {self.storage_client.use_local_storage}")
                logger.info(f"🔍 storage_client.supabase: {type(self.storage_client.supabase) if hasattr(self.storage_client, 'supabase') else 'None'}")
                logger.info(f"🔍 self.use_cloud_storage: {self.use_cloud_storage}")

            except Exception as e:
                logger.error(f"初始化存储客户端失败: {e}")
                logger.error(f"🔍 完整错误堆栈: {traceback.format_exc()}")
                # 降级到本地存储
                self.use_cloud_storage = False
                self.is_local_env = True
                self.storage_client = None
        else:
            # 使用本地文件系统存储
            logger.info("🔍 备份服务：使用本地文件系统存储")
            logger.info(f"🔍 原因 - force_cloud: {force_cloud}, supabase_url: {'已设置' if supabase_url else '未设置'}, supabase_key: {'已设置' if supabase_key else '未设置'}")
            self.use_cloud_storage = False
            self.is_local_env = True
            self.storage_client = None

        # 配置路径
        self.project_root = self._get_project_root()
        self.backup_dir = os.path.join(self.project_root, 'cloud_db_backups')
        self.temp_dir = os.path.join(self.backup_dir, 'temp')
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        # Supabase 存储桶配置
        self.backup_bucket = os.getenv('SUPABASE_BUCKET_BACKUP', 'database-backup')

        # 子目录前缀配置（按数据库类型隔离，复用图片存储的架构模式）
        self.path_prefix = {
            'sp8d': 'sp8d/',      # SP8D 数据库备份子目录
            'ovs': 'ovs/',        # OVS 数据库备份子目录
            'local': 'local/'     # 本地数据库备份子目录
        }

        # 识别当前数据库类型
        self.current_db_type = self._detect_current_db_type()
        logger.info(f"🔍 当前数据库类型: {self.current_db_type}")

        # 备份保留天数
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))

        # 任务状态跟踪
        self.tasks = {}

        # 日志环境信息
        logger.info(f"{'='*60}")
        logger.info(f"Supabase 备份服务初始化")
        logger.info(f"{'='*60}")
        logger.info(f"运行环境: {'本地开发' if self.is_local_env else '云端生产'}")
        logger.info(f"存储位置: {'Supabase Storage' if self.use_cloud_storage else '本地文件系统'}")
        logger.info(f"备份目录: {self.backup_dir}")
        logger.info(f"保留天数: {self.retention_days} 天")
        logger.info(f"{'='*60}")

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
        db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', '')

        # 根据数据库URI识别类型
        if 'localhost' in db_uri or '127.0.0.1' in db_uri or 'sqlite' in db_uri:
            return 'local'
        elif 'iqcyimnjtnmomvfuwjzw' in db_uri:
            return 'sp8d'
        elif 'pqzviljbpfoqvyfulakl' in db_uri:
            return 'ovs'
        else:
            # 默认为本地
            logger.warning(f"无法识别数据库类型，URI: {db_uri[:50]}... 默认使用 local")
            return 'local'

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

        # 获取Flask应用上下文
        app = current_app._get_current_object()

        # 启动后台线程（传入app对象）
        thread = threading.Thread(
            target=self._create_backup_task,
            args=(task_id, db_type, app)
        )
        thread.daemon = True
        thread.start()

        return task_id

    def _create_backup_task(self, task_id: str, db_type: str, app):
        """后台备份任务"""
        # 在后台线程中创建应用上下文
        with app.app_context():
            try:
                self.tasks[task_id]['progress'] = 10
                self.tasks[task_id]['message'] = '正在备份数据库...'

                # 执行备份
                results = self.create_backup(db_type)

                # 验证备份结果
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
            # 调用通用备份脚本（读取当前DATABASE_URL配置）
            logger.info("备份当前数据库...")
            result = self._backup_current_database()
            if result:
                results.append(result)

            logger.info(f"备份完成，共 {len(results)} 个文件")
            return results

        except Exception as e:
            logger.error(f"备份过程出错: {e}")
            raise

    def _backup_current_database(self) -> Optional[Dict]:
        """备份当前DATABASE_URL指向的数据库 - 使用通用备份脚本"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 使用通用备份脚本（从DATABASE_URL读取配置）
            backup_script = os.path.join(self.project_root, 'backup_current_database.py')

            if not os.path.exists(backup_script):
                logger.error(f"通用备份脚本不存在: {backup_script}")
                return None

            # 执行备份脚本
            logger.info(f"执行通用备份脚本: {backup_script}")
            result = subprocess.run(
                [sys.executable, backup_script],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode != 0:
                logger.error(f"备份脚本执行失败: {result.stderr}")
                return None

            # 自动识别备份文件（支持 local/sp8d/ovs/unknown）
            backup_file = self._find_latest_backup_auto(timestamp)
            if not backup_file or not os.path.exists(backup_file):
                logger.error(f"未找到备份文件（timestamp: {timestamp}）")
                return None

            # 从文件名识别数据库类型
            db_type = self._extract_db_type_from_filename(backup_file)

            # 压缩备份文件
            compressed_file = self._compress_file(backup_file)

            # 根据存储环境处理
            if self.use_cloud_storage:
                # 上传到 Supabase
                uploaded_path = self._upload_to_supabase(compressed_file, db_type)
                # 删除本地临时文件
                os.remove(backup_file)
                os.remove(compressed_file)
                return {
                    'db_type': db_type,
                    'filename': os.path.basename(compressed_file),
                    'location': 'supabase',
                    'path': uploaded_path,
                    'size': 0  # 需要从 Supabase 获取
                }
            else:
                # 保存到本地
                final_path = os.path.join(self.backup_dir, os.path.basename(compressed_file))
                shutil.move(compressed_file, final_path)
                # 删除原始 SQL 文件
                os.remove(backup_file)
                return {
                    'db_type': db_type,
                    'filename': os.path.basename(final_path),
                    'location': 'local',
                    'path': final_path,
                    'size': os.path.getsize(final_path)
                }

        except Exception as e:
            logger.error(f"备份当前数据库失败: {e}")
            raise  # 向上抛出异常，让调用者处理

    def _find_latest_backup(self, db_type: str, timestamp: str) -> Optional[str]:
        """查找最新生成的备份文件（精确匹配完整时间戳）"""
        # 根据数据库类型构造精确文件名
        if db_type == 'sp8d':
            expected_filename = f'pma_db_sp8d_backup_{timestamp}.sql'
        else:
            expected_filename = f'pma_db_ovs_backup_simple_{timestamp}.sql'

        # 精确查找文件
        filepath = os.path.join(self.backup_dir, expected_filename)
        if os.path.exists(filepath):
            logger.info(f"找到备份文件: {expected_filename}")
            return filepath

        logger.error(f"未找到备份文件: {expected_filename}")
        return None

    def _find_latest_backup_auto(self, timestamp: str) -> Optional[str]:
        """自动识别最新备份文件（支持 local/sp8d/ovs/unknown）"""
        # 尝试所有可能的文件名模式
        patterns = [
            f'pma_db_local_backup_{timestamp}.sql',
            f'pma_db_local_backup_{timestamp}.db',   # SQLite
            f'pma_db_sp8d_backup_{timestamp}.sql',
            f'pma_db_ovs_backup_simple_{timestamp}.sql',
            f'pma_db_unknown_backup_{timestamp}.sql'
        ]

        for pattern in patterns:
            filepath = os.path.join(self.backup_dir, pattern)
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

        logger.info(f"压缩完成: {original_size / 1024 / 1024:.2f} MB → {compressed_size / 1024 / 1024:.2f} MB (压缩率: {compression_ratio:.1f}%)")

        return compressed_path

    def _upload_to_supabase(self, filepath: str, db_type: str) -> str:
        """上传文件到 Supabase Storage（使用子目录隔离）"""
        # 调试：检查存储客户端
        logger.info(f"🔍 调试上传 - storage_client: {self.storage_client}")
        logger.info(f"🔍 调试上传 - storage_client type: {type(self.storage_client)}")

        if not self.storage_client:
            raise Exception("Supabase 存储客户端未初始化")

        # 调试：检查 supabase 对象
        logger.info(f"🔍 调试上传 - storage_client.supabase: {self.storage_client.supabase}")
        logger.info(f"🔍 调试上传 - use_local_storage: {self.storage_client.use_local_storage}")

        if self.storage_client.use_local_storage:
            raise Exception("存储客户端配置为本地存储，无法上传到 Supabase")

        if not hasattr(self.storage_client, 'supabase') or self.storage_client.supabase is None:
            raise Exception("Supabase 客户端对象未初始化")

        filename = os.path.basename(filepath)

        # 构建带子目录的存储路径
        prefix = self.path_prefix.get(db_type, '')
        storage_path = f"{prefix}{filename}"

        logger.info(f"上传到 Supabase: {storage_path}")
        logger.info(f"🔍 调试上传 - 存储桶: {self.backup_bucket}")
        logger.info(f"🔍 调试上传 - 文件路径: {filepath}")
        logger.info(f"🔍 调试上传 - 文件大小: {os.path.getsize(filepath)} bytes")

        try:
            # 读取文件
            with open(filepath, 'rb') as f:
                file_data = f.read()

            logger.info(f"🔍 调试上传 - 读取文件成功，大小: {len(file_data)} bytes")

            # 上传到 Supabase（使用与图片上传相同的方式）
            logger.info(f"🔍 调试上传 - 开始调用 Supabase upload API...")
            # ✅ 复用图片上传的成功模式：只传递路径和数据，不传递额外参数
            result = self.storage_client.supabase.storage.from_(self.backup_bucket).upload(
                storage_path,
                file_data
            )

            logger.info(f"🔍 调试上传 - upload 返回结果: {result}")
            logger.info(f"上传成功: {storage_path}")
            return storage_path

        except Exception as e:
            logger.error(f"上传失败: {e}")
            logger.error(f"🔍 调试上传 - 错误类型: {type(e)}")
            logger.error(f"🔍 调试上传 - 错误详情: {str(e)}")
            import traceback
            logger.error(f"🔍 调试上传 - 完整堆栈:\n{traceback.format_exc()}")
            raise

    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        logger.info(f"list_backups 调用: use_cloud_storage={self.use_cloud_storage}")
        if self.use_cloud_storage:
            logger.info("使用 Supabase 备份列表")
            return self._list_supabase_backups()
        else:
            logger.info("使用本地备份列表")
            return self._list_local_backups()

    def _list_supabase_backups(self) -> List[Dict]:
        """列出 Supabase 中的备份（支持子目录遍历）"""
        # 🔍 调试：记录存储客户端状态
        logger.info(f"🔍 _list_supabase_backups 被调用")
        logger.info(f"🔍 storage_client: {self.storage_client}")
        logger.info(f"🔍 storage_client is None: {self.storage_client is None}")

        if not self.storage_client:
            logger.warning("🔍 storage_client 为 None，返回空列表")
            return []

        # 🔍 调试：检查 supabase 对象
        logger.info(f"🔍 storage_client.supabase: {self.storage_client.supabase if hasattr(self.storage_client, 'supabase') else 'NO ATTR'}")
        logger.info(f"🔍 backup_bucket: {self.backup_bucket}")

        backups = []

        # 只列出当前数据库类型的备份
        db_type = self.current_db_type
        prefix = self.path_prefix.get(db_type, '')

        if not prefix:
            logger.warning(f"🔍 未知的数据库类型: {db_type}")
            return []

        try:
            logger.info(f"🔍 只列出当前数据库类型 {db_type} 的备份，前缀: {prefix}")

            # 列出子目录下的文件
            files = self.storage_client.supabase.storage.from_(self.backup_bucket).list(prefix)
            logger.info(f"🔍 {db_type} 列出成功，文件数: {len(files)}")

            for file in files:
                # 跳过目录本身
                if file.get('id') is None:
                    continue

                backups.append({
                    'filename': file['name'],
                    'size': file.get('metadata', {}).get('size', 0),
                    'created_at': file.get('created_at', ''),
                    'location': 'supabase',
                    'db_type': db_type,  # 当前数据库类型
                    'storage_path': f"{prefix}{file['name']}"  # 完整存储路径
                })

        except Exception as e:
            import traceback
            logger.warning(f"列出 {db_type} 备份失败: {e}")
            logger.warning(f"🔍 错误类型: {type(e).__name__}")
            logger.warning(f"🔍 错误详情: {str(e)}")
            logger.warning(f"🔍 完整堆栈:\n{traceback.format_exc()}")
            return []

        return sorted(backups, key=lambda x: x['created_at'], reverse=True)

    def _list_local_backups(self) -> List[Dict]:
        """列出本地备份"""
        backups = []

        try:
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.sql.gz') or filename.endswith('.sql'):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)

                    backups.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'location': 'local',
                        'db_type': 'sp8d' if 'sp8d' in filename else 'ovs'
                    })

            return sorted(backups, key=lambda x: x['created_at'], reverse=True)

        except Exception as e:
            logger.error(f"获取本地备份列表失败: {e}")
            return []

    def get_download_url(self, storage_path: str) -> str:
        """获取下载 URL

        Args:
            storage_path: 完整存储路径（如 'sp8d/filename.sql.gz'）或文件名（本地模式）
        """
        if self.use_cloud_storage:
            return self._get_supabase_download_url(storage_path)
        else:
            # 本地模式只需要文件名
            filename = os.path.basename(storage_path)
            return f'/backup/download/{filename}'

    def _get_supabase_download_url(self, storage_path: str) -> str:
        """获取 Supabase 临时下载 URL

        Args:
            storage_path: 完整存储路径（包含子目录，如 'sp8d/filename.sql.gz'）
        """
        if not self.storage_client:
            raise Exception("Supabase 存储客户端未初始化")

        try:
            logger.info(f"生成下载 URL: {storage_path}")
            # 使用完整路径生成 1 小时有效的签名 URL
            signed_url = self.storage_client.supabase.storage.from_(self.backup_bucket).create_signed_url(
                storage_path,  # 使用完整路径（包含子目录）
                3600  # 1小时
            )
            return signed_url['signedURL']
        except Exception as e:
            logger.error(f"生成下载 URL 失败: {e}")
            raise

    def delete_backup(self, storage_path: str) -> bool:
        """删除备份

        Args:
            storage_path: 完整存储路径（如 'sp8d/filename.sql.gz'）或文件名（本地模式）
        """
        # 🔍 调试：记录接收到的路径
        logger.info(f"🔍 delete_backup 接收到的 storage_path: {storage_path}")
        logger.info(f"🔍 use_cloud_storage: {self.use_cloud_storage}")
        logger.info(f"🔍 storage_path 是否包含斜杠: {'/' in storage_path}")

        if self.use_cloud_storage:
            return self._delete_supabase_backup(storage_path)
        else:
            # 本地模式只需要文件名
            filename = os.path.basename(storage_path)
            return self._delete_local_backup(filename)

    def _delete_supabase_backup(self, storage_path: str) -> bool:
        """删除 Supabase 备份

        Args:
            storage_path: 完整存储路径（包含子目录，如 'sp8d/filename.sql.gz'）
        """
        if not self.storage_client:
            return False

        try:
            logger.info(f"删除云端备份: {storage_path}")

            # 🔍 调试：记录删除操作详情
            logger.info(f"🔍 backup_bucket: {self.backup_bucket}")
            logger.info(f"🔍 删除路径参数: {[storage_path]}")

            # 使用完整路径删除文件
            result = self.storage_client.supabase.storage.from_(self.backup_bucket).remove([storage_path])

            # 🔍 调试：记录Supabase返回结果
            logger.info(f"🔍 Supabase remove() 返回结果: {result}")

            logger.info(f"删除云端备份成功: {storage_path}")
            return True
        except Exception as e:
            import traceback
            logger.error(f"删除云端备份失败: {e}")
            logger.error(f"🔍 完整错误堆栈:\n{traceback.format_exc()}")
            return False

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
                # 使用 storage_path（云端）或 filename（本地）
                path = backup.get('storage_path', backup['filename'])
                if self.delete_backup(path):
                    deleted_count += 1

        logger.info(f"清理完成，删除了 {deleted_count} 个备份")
        return deleted_count

    def get_storage_usage(self) -> Dict:
        """获取存储使用情况"""
        backups = self.list_backups()
        total_size = sum(b['size'] for b in backups)

        return {
            'total_backups': len(backups),
            'total_size': total_size,
            'total_size_mb': total_size / 1024 / 1024,
            'location': 'Supabase Storage' if self.use_cloud_storage else '本地文件系统',
            'retention_days': self.retention_days
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

    # 🔍 调试：记录获取服务实例的调用
    logger.info("🔍 get_backup_service() 被调用")
    logger.info(f"🔍 当前 backup_service: {backup_service}")
    logger.info(f"🔍 当前环境变量 FORCE_CLOUD_UPLOAD: {os.getenv('FORCE_CLOUD_UPLOAD')}")
    logger.info(f"🔍 当前环境变量 SUPABASE_URL: {'已设置' if os.getenv('SUPABASE_URL') else '未设置'}")

    if backup_service is None:
        logger.info("🔍 backup_service 为 None，正在初始化...")
        backup_service = init_backup_service()
        logger.info(f"🔍 初始化完成，use_cloud_storage: {backup_service.use_cloud_storage}")
    else:
        logger.info(f"🔍 使用现有实例，use_cloud_storage: {backup_service.use_cloud_storage}")
        logger.info(f"🔍 现有实例 storage_client: {backup_service.storage_client}")

    return backup_service
