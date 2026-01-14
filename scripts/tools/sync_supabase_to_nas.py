#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase → NAS 文件同步脚本

将 Supabase 存储桶中的现有文件同步到 NAS WebDAV 存储。
支持增量同步（跳过已存在的文件）。

使用方法：
    # 预览模式（不实际执行）
    python scripts/tools/sync_supabase_to_nas.py --dry-run

    # 执行同步
    python scripts/tools/sync_supabase_to_nas.py --execute

    # 仅同步指定存储桶
    python scripts/tools/sync_supabase_to_nas.py --execute --bucket invoice
"""

import sys
import os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())
os.chdir(get_project_root())

# 加载配置文件
from dotenv import load_dotenv
load_dotenv('.env.nas')
load_dotenv('.env', override=False)

import argparse
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupabaseToNASSync:
    """Supabase → NAS 同步器"""

    # Supabase 存储桶 → NAS 子目录映射
    BUCKETS = [
        ('invoice-images', 'invoices'),
        ('product-images', 'products'),
        ('rd-product-images', 'rd_products'),
    ]

    def __init__(self):
        # 加载 Flask 应用以获取配置
        from app import create_app
        self.app = create_app()

        with self.app.app_context():
            from app.utils.synology_webdav_client import get_synology_webdav_client
            from app.utils.supabase_client import SupabaseStorageClient

            self.nas = get_synology_webdav_client()
            self.supabase = SupabaseStorageClient()

            # 测试连接
            logger.info("测试 NAS 连接...")
            success, msg = self.nas.test_connection()
            if success:
                logger.info(f"NAS 连接成功: {self.nas.base_url}")
            else:
                logger.error(f"NAS 连接失败: {msg}")
                raise RuntimeError(f"NAS 连接失败: {msg}")

            logger.info("测试 Supabase 连接...")
            if self.supabase.use_local_storage:
                logger.warning("Supabase 未配置或使用本地存储模式")
            else:
                logger.info(f"Supabase 连接成功: {self.supabase.supabase_url}")

    def sync_all(self, dry_run: bool = True, bucket_filter: str = None):
        """
        同步所有存储桶

        Args:
            dry_run: 仅预览，不实际同步
            bucket_filter: 仅同步包含此关键字的存储桶
        """
        with self.app.app_context():
            stats = {
                'total': 0,
                'synced': 0,
                'skipped': 0,
                'failed': 0,
                'start_time': datetime.now()
            }

            for supabase_bucket, nas_subdir in self.BUCKETS:
                if bucket_filter and bucket_filter not in supabase_bucket:
                    continue

                logger.info(f"\n{'='*60}")
                logger.info(f"同步存储桶: {supabase_bucket} → NAS:/{nas_subdir}")
                logger.info('='*60)

                bucket_stats = self._sync_bucket(
                    supabase_bucket, nas_subdir, dry_run
                )

                stats['total'] += bucket_stats['total']
                stats['synced'] += bucket_stats['synced']
                stats['skipped'] += bucket_stats['skipped']
                stats['failed'] += bucket_stats['failed']

            # 打印统计
            duration = datetime.now() - stats['start_time']
            logger.info(f"\n{'='*60}")
            logger.info("同步完成统计:")
            logger.info(f"  总文件数: {stats['total']}")
            logger.info(f"  已同步: {stats['synced']}")
            logger.info(f"  已跳过(已存在): {stats['skipped']}")
            logger.info(f"  失败: {stats['failed']}")
            logger.info(f"  耗时: {duration}")
            if dry_run:
                logger.info("  [DRY-RUN 模式，未实际执行]")
            logger.info('='*60)

    def _sync_bucket(self, supabase_bucket: str, nas_subdir: str, dry_run: bool) -> dict:
        """同步单个存储桶"""
        stats = {'total': 0, 'synced': 0, 'skipped': 0, 'failed': 0}

        try:
            # 列出 Supabase 文件
            logger.info(f"正在列出 Supabase 存储桶 {supabase_bucket} 的文件（可能需要一些时间）...")
            import time
            start_time = time.time()
            files = self._list_supabase_files(supabase_bucket)
            elapsed = time.time() - start_time
            stats['total'] = len(files)

            logger.info(f"发现 {len(files)} 个文件（耗时 {elapsed:.1f} 秒）")

            for i, file_info in enumerate(files, 1):
                file_path = file_info['path']
                file_size = file_info.get('size', 0)
                nas_path = f"{nas_subdir}/{file_path}"

                # 显示进度
                progress = f"[{i}/{len(files)}]"

                # 检查 NAS 是否已存在
                if self.nas.file_exists(nas_path):
                    logger.debug(f"{progress} 跳过(已存在): {nas_path}")
                    stats['skipped'] += 1
                    continue

                if dry_run:
                    size_str = self._format_size(file_size)
                    logger.info(f"{progress} [DRY-RUN] 将同步: {file_path} ({size_str})")
                    stats['synced'] += 1
                else:
                    # 下载并上传
                    success = self._sync_file(supabase_bucket, file_path, nas_path)
                    if success:
                        logger.info(f"{progress} 已同步: {file_path}")
                        stats['synced'] += 1
                    else:
                        logger.error(f"{progress} 同步失败: {file_path}")
                        stats['failed'] += 1

        except Exception as e:
            logger.error(f"同步存储桶失败: {supabase_bucket}, 错误: {e}")
            import traceback
            traceback.print_exc()

        return stats

    def _list_supabase_files(self, bucket: str, prefix: str = '', depth: int = 0) -> list:
        """递归列出 Supabase 存储桶中的所有文件"""
        all_files = []
        indent = "  " * depth

        try:
            if depth == 0:
                logger.info(f"  开始扫描存储桶根目录...")
            else:
                logger.debug(f"{indent}扫描目录: {prefix}")

            # 使用 Supabase 客户端列出文件
            response = self.supabase.supabase.storage.from_(bucket).list(prefix)

            if depth == 0:
                logger.info(f"  根目录有 {len(response)} 个项目")

            for item in response:
                item_name = item.get('name', '')
                if not item_name:
                    continue

                # 构建完整路径
                if prefix:
                    full_path = f"{prefix}/{item_name}"
                else:
                    full_path = item_name

                # 检查是否是文件（有 id）还是目录
                if item.get('id'):
                    # 是文件
                    metadata = item.get('metadata', {})
                    all_files.append({
                        'path': full_path,
                        'size': metadata.get('size', 0),
                        'content_type': metadata.get('mimetype', '')
                    })
                else:
                    # 是目录，递归
                    logger.info(f"  扫描子目录: {full_path}/")
                    all_files.extend(self._list_supabase_files(bucket, full_path, depth + 1))

        except Exception as e:
            logger.error(f"列出文件失败: {bucket}/{prefix}, 错误: {e}")

        return all_files

    def _sync_file(self, bucket: str, file_path: str, nas_path: str) -> bool:
        """同步单个文件"""
        try:
            # 从 Supabase 下载
            response = self.supabase.supabase.storage.from_(bucket).download(file_path)

            if response:
                # 确定 content_type
                ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ''
                content_type = self._get_content_type(ext)

                # 上传到 NAS
                result = self.nas.upload_file(
                    file_content=response,
                    remote_path=nas_path,
                    content_type=content_type
                )

                return result is not None
            else:
                logger.error(f"下载 Supabase 文件失败: {file_path}")
                return False

        except Exception as e:
            logger.error(f"同步文件失败: {file_path}, 错误: {e}")
            return False

    def _get_content_type(self, ext: str) -> str:
        """获取文件的 Content-Type"""
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        return content_types.get(ext, 'application/octet-stream')

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"


def main():
    parser = argparse.ArgumentParser(
        description='Supabase → NAS 文件同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --dry-run              预览要同步的文件
  %(prog)s --execute              执行同步
  %(prog)s --execute --bucket invoice  仅同步发票文件
        """
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='仅预览，不实际同步')
    parser.add_argument('--execute', action='store_true',
                        help='执行实际同步')
    parser.add_argument('--bucket', type=str,
                        help='仅同步指定存储桶（invoice/product/rd_product）')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示详细日志')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.execute and not args.dry_run:
        print("请指定 --dry-run 预览或 --execute 执行")
        print()
        parser.print_help()
        return

    try:
        syncer = SupabaseToNASSync()
        syncer.sync_all(dry_run=not args.execute, bucket_filter=args.bucket)
    except Exception as e:
        logger.error(f"同步失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
