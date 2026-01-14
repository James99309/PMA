# -*- coding: utf-8 -*-
"""
智能存储管理器

实现 NAS 优先、Supabase 备份的存储策略：
1. 上传时优先使用 NAS，成功后异步同步到 Supabase
2. NAS 不可用时回退到 Supabase
3. 用户访问时优先从 NAS 获取
"""

import os
import logging
import threading
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Union
from io import BytesIO

logger = logging.getLogger(__name__)


class SmartStorageManager:
    """
    智能存储管理器 - NAS 优先，Supabase 备份

    上传策略：
    1. NAS 可用 → 上传 NAS → 异步同步 Supabase
    2. NAS 不可用 → 直接上传 Supabase（回退）

    访问策略：
    1. 优先返回 NAS URL（通过应用代理）
    2. NAS 不可用 → 返回 Supabase URL
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 配置
        self.sync_to_supabase = os.getenv('NAS_SYNC_TO_SUPABASE', 'true').lower() == 'true'
        self.fallback_enabled = os.getenv('NAS_FALLBACK_TO_SUPABASE', 'true').lower() == 'true'
        self.nas_enabled = os.getenv('NAS_STORAGE_ENABLED', 'true').lower() == 'true'

        # 存储桶映射（NAS 子目录 → Supabase 存储桶）
        self.bucket_mapping = {
            'invoice': 'invoices',
            'product': 'products',
            'rd_product': 'rd_products',
            'meeting': 'meetings',
        }

        self._initialized = True
        logger.info(f"SmartStorageManager 初始化: NAS={self.nas_enabled}, 同步={self.sync_to_supabase}, 回退={self.fallback_enabled}")

    @property
    def nas_client(self):
        """获取 NAS WebDAV 客户端"""
        from app.utils.synology_webdav_client import get_synology_webdav_client
        return get_synology_webdav_client()

    @property
    def supabase_client(self):
        """获取 Supabase 存储客户端"""
        from app.utils.supabase_client import SupabaseStorageClient
        return SupabaseStorageClient()

    def is_nas_available(self) -> bool:
        """检查 NAS 是否可用"""
        if not self.nas_enabled:
            return False
        from app.utils.synology_webdav_client import is_nas_available
        return is_nas_available()

    def upload_file(
        self,
        object_id: int,
        file: Union[bytes, Any],
        filename: str,
        file_type: str = 'image',
        bucket_type: str = 'invoice',
        business_type: str = 'expense',
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        智能上传文件

        Args:
            object_id: 业务对象ID
            file: 文件内容（bytes）或文件对象
            filename: 文件名
            file_type: 文件类型（image/pdf/attachment）
            bucket_type: 存储桶类型（invoice/product/rd_product/meeting）
            business_type: 业务类型（expense/product/rd_product/meeting）
            **kwargs: 其他参数

        Returns:
            {
                'url': '访问URL',
                'nas_path': 'NAS路径（如有）',
                'supabase_url': 'Supabase URL（如有）',
                'storage': 'nas' 或 'supabase',
                'synced': 是否已同步到Supabase,
                'filename': '存储文件名',
                'storage_path': '存储路径'
            }
        """
        # 读取文件数据
        if hasattr(file, 'read'):
            file.seek(0)
            file_data = file.read()
            file.seek(0)
        else:
            file_data = file

        result = {
            'url': None,
            'nas_path': None,
            'supabase_url': None,
            'storage': None,
            'synced': False,
            'filename': filename,
            'file_type': file_type,
            'storage_path': None
        }

        # 生成存储路径
        storage_path = self._generate_storage_path(
            object_id, filename, file_type, bucket_type, business_type, **kwargs
        )
        result['storage_path'] = storage_path

        # 尝试上传到 NAS
        if self.nas_enabled and self.is_nas_available():
            nas_subdir = self.bucket_mapping.get(bucket_type, bucket_type)
            nas_path = f"{nas_subdir}/{storage_path}"

            try:
                # 确定 content_type
                content_type = self._get_content_type(filename, file_type)

                # 上传到 NAS
                uploaded_path = self.nas_client.upload_file(
                    file_content=file_data,
                    remote_path=nas_path,
                    content_type=content_type
                )

                if uploaded_path:
                    result['nas_path'] = nas_path
                    result['url'] = self._get_nas_access_url(nas_path, bucket_type)
                    result['storage'] = 'nas'

                    logger.info(f"文件上传到 NAS: {nas_path}")

                    # 异步同步到 Supabase
                    if self.sync_to_supabase:
                        self._async_sync_to_supabase(
                            storage_path, file_data, bucket_type, result
                        )

                    return result
                else:
                    logger.warning(f"NAS 上传返回空，尝试回退到 Supabase")

            except Exception as e:
                logger.error(f"NAS 上传异常: {e}, 尝试回退到 Supabase")

        # NAS 不可用或失败，回退到 Supabase
        if self.fallback_enabled:
            try:
                # 重置文件指针
                if hasattr(file, 'seek'):
                    file.seek(0)

                supabase_result = self.supabase_client.upload_file(
                    object_id=object_id,
                    file=file if hasattr(file, 'read') else BytesIO(file_data),
                    filename=filename,
                    file_type=file_type,
                    bucket_type=bucket_type,
                    business_type=business_type,
                    **kwargs
                )

                if supabase_result:
                    result['supabase_url'] = supabase_result.get('url')
                    result['url'] = result['supabase_url']
                    result['storage'] = 'supabase'
                    result['storage_path'] = supabase_result.get('storage_path', storage_path)
                    result['synced'] = True  # 已在 Supabase

                    logger.info(f"文件回退上传到 Supabase: {result['storage_path']}")
                    return result

            except Exception as e:
                logger.error(f"Supabase 回退上传失败: {e}")

        logger.error("文件上传失败：NAS 和 Supabase 都不可用")
        return None

    def _generate_storage_path(
        self,
        object_id: int,
        filename: str,
        file_type: str,
        bucket_type: str,
        business_type: str,
        **kwargs
    ) -> str:
        """生成存储路径"""
        # 获取系统标识
        system_id = os.getenv('SYSTEM_IDENTIFIER', 'LOCAL-PMA')

        # 生成安全文件名
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{file_type}_{object_id}_{timestamp}_{unique_id}.{ext}"

        # 根据业务类型生成路径
        if business_type == 'expense':
            expense_number = kwargs.get('expense_number', f'EXP{object_id}')
            path = f"{system_id}/{expense_number}/{safe_filename}"
        elif business_type in ('product', 'rd_product'):
            path = f"{system_id}/{object_id}/{safe_filename}"
        elif business_type == 'meeting':
            meeting_id = kwargs.get('meeting_id', object_id)
            path = f"{system_id}/{meeting_id}/{safe_filename}"
        else:
            path = f"{system_id}/{business_type}_{object_id}/{safe_filename}"

        return path

    def _get_content_type(self, filename: str, file_type: str) -> str:
        """获取文件的 Content-Type"""
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'mp3': 'audio/mpeg',
            'm4a': 'audio/mp4',
            'wav': 'audio/wav',
        }

        return content_types.get(ext, 'application/octet-stream')

    def _get_nas_access_url(self, nas_path: str, bucket_type: str) -> str:
        """获取 NAS 文件的访问 URL（通过应用代理）"""
        from urllib.parse import quote
        # 通过应用代理访问，确保权限控制
        return f"/storage/nas/{bucket_type}?path={quote(nas_path)}"

    def _async_sync_to_supabase(
        self,
        storage_path: str,
        file_data: bytes,
        bucket_type: str,
        result: dict
    ):
        """异步同步文件到 Supabase"""
        try:
            from flask import current_app
            app = current_app._get_current_object()
        except RuntimeError:
            logger.warning("无法获取 Flask 应用上下文，跳过异步同步")
            return

        def sync_task():
            with app.app_context():
                try:
                    file_obj = BytesIO(file_data)

                    # 使用 Supabase 客户端上传
                    supabase = self.supabase_client
                    bucket_name = supabase.bucket_config.get(bucket_type, supabase.bucket_config['default'])

                    # 直接使用 Supabase SDK 上传
                    try:
                        supabase.supabase.storage.from_(bucket_name).upload(
                            storage_path,
                            file_obj.read(),
                            {'content-type': 'application/octet-stream', 'x-upsert': 'true'}
                        )
                        # 生成公开 URL
                        url = f"{supabase.supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
                        result['supabase_url'] = url
                        result['synced'] = True
                        logger.info(f"异步同步到 Supabase 成功: {storage_path}")
                    except Exception as upload_err:
                        logger.warning(f"异步同步到 Supabase 失败: {upload_err}")

                except Exception as e:
                    logger.error(f"异步同步到 Supabase 异常: {e}")

        thread = threading.Thread(target=sync_task, daemon=True)
        thread.start()

    def download_file(self, storage_path: str, bucket_type: str = 'invoice') -> Optional[bytes]:
        """
        下载文件（优先 NAS）

        Args:
            storage_path: 存储路径
            bucket_type: 存储桶类型

        Returns:
            文件内容（bytes）
        """
        # 优先从 NAS 下载
        if self.nas_enabled and self.is_nas_available():
            try:
                nas_subdir = self.bucket_mapping.get(bucket_type, bucket_type)
                nas_path = f"{nas_subdir}/{storage_path}"
                data = self.nas_client.download_file(nas_path)
                if data:
                    logger.debug(f"从 NAS 下载文件: {nas_path}")
                    return data
            except Exception as e:
                logger.warning(f"NAS 下载失败: {e}, 尝试从 Supabase 下载")

        # 从 Supabase 下载
        if self.fallback_enabled:
            try:
                supabase = self.supabase_client
                bucket_name = supabase.bucket_config.get(bucket_type, supabase.bucket_config['default'])
                data = supabase.supabase.storage.from_(bucket_name).download(storage_path)
                if data:
                    logger.debug(f"从 Supabase 下载文件: {storage_path}")
                    return data
            except Exception as e:
                logger.error(f"Supabase 下载也失败: {e}")

        return None

    def delete_file(self, storage_path: str, bucket_type: str = 'invoice') -> bool:
        """
        删除文件（同时删除 NAS 和 Supabase）

        Args:
            storage_path: 存储路径
            bucket_type: 存储桶类型

        Returns:
            是否成功
        """
        nas_deleted = False
        supabase_deleted = False

        # 删除 NAS
        if self.nas_enabled:
            try:
                nas_subdir = self.bucket_mapping.get(bucket_type, bucket_type)
                nas_path = f"{nas_subdir}/{storage_path}"
                nas_deleted = self.nas_client.delete_file(nas_path)
            except Exception as e:
                logger.warning(f"NAS 删除失败: {e}")

        # 删除 Supabase
        try:
            supabase = self.supabase_client
            bucket_name = supabase.bucket_config.get(bucket_type, supabase.bucket_config['default'])
            supabase.supabase.storage.from_(bucket_name).remove([storage_path])
            supabase_deleted = True
        except Exception as e:
            logger.warning(f"Supabase 删除失败: {e}")

        return nas_deleted or supabase_deleted

    def file_exists(self, storage_path: str, bucket_type: str = 'invoice') -> bool:
        """检查文件是否存在（任一存储有即可）"""
        # 检查 NAS
        if self.nas_enabled and self.is_nas_available():
            try:
                nas_subdir = self.bucket_mapping.get(bucket_type, bucket_type)
                nas_path = f"{nas_subdir}/{storage_path}"
                if self.nas_client.file_exists(nas_path):
                    return True
            except:
                pass

        # 检查 Supabase
        try:
            supabase = self.supabase_client
            bucket_name = supabase.bucket_config.get(bucket_type, supabase.bucket_config['default'])
            # 尝试获取文件信息
            result = supabase.supabase.storage.from_(bucket_name).list(
                path='/'.join(storage_path.split('/')[:-1]) or ''
            )
            filename = storage_path.split('/')[-1]
            for item in result:
                if item.get('name') == filename:
                    return True
        except:
            pass

        return False

    def get_file_url(
        self,
        storage_path: str,
        bucket_type: str = 'invoice',
        prefer_nas: bool = True
    ) -> Optional[str]:
        """
        获取文件访问 URL

        Args:
            storage_path: 存储路径
            bucket_type: 存储桶类型
            prefer_nas: 是否优先 NAS

        Returns:
            访问 URL
        """
        if prefer_nas and self.nas_enabled and self.is_nas_available():
            nas_subdir = self.bucket_mapping.get(bucket_type, bucket_type)
            nas_path = f"{nas_subdir}/{storage_path}"
            return self._get_nas_access_url(nas_path, bucket_type)

        # 返回 Supabase URL
        try:
            supabase = self.supabase_client
            bucket_name = supabase.bucket_config.get(bucket_type, supabase.bucket_config['default'])
            return f"{supabase.supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
        except:
            return None

    def get_status(self) -> Dict[str, Any]:
        """获取存储状态"""
        nas_available = self.is_nas_available()
        nas_using_internal = False

        if nas_available:
            nas_using_internal = self.nas_client.is_using_internal()

        return {
            'nas_enabled': self.nas_enabled,
            'nas_available': nas_available,
            'nas_using_internal': nas_using_internal,
            'sync_to_supabase': self.sync_to_supabase,
            'fallback_enabled': self.fallback_enabled
        }


# 便捷函数
_smart_storage = None


def get_smart_storage() -> SmartStorageManager:
    """获取智能存储管理器实例"""
    global _smart_storage
    if _smart_storage is None:
        _smart_storage = SmartStorageManager()
    return _smart_storage


def reset_smart_storage():
    """重置智能存储管理器"""
    global _smart_storage
    _smart_storage = None


class SmartExpenseStorage:
    """
    报销单发票存储 - 专用于报销单发票的智能存储

    整合 SmartStorageManager 和 SupabaseStorageClient 的发票命名逻辑
    """

    def __init__(self):
        self.storage = get_smart_storage()

    def upload_expense_invoice(
        self,
        detail_id: int,
        file,
        filename: str,
        bucket_type: str = 'invoice',
        detail_sequence: int = None,
        file_sequence: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        上传报销明细发票图片（NAS 优先，Supabase 备份）

        Args:
            detail_id: 报销明细ID
            file: 文件对象
            filename: 原始文件名
            bucket_type: 存储桶类型
            detail_sequence: 明细序号（可选）
            file_sequence: 文件序号（可选）

        Returns:
            成功返回文件信息字典，失败返回 None
        """
        try:
            # 读取文件内容
            if hasattr(file, 'read'):
                file.seek(0)
                file_data = file.read()
                file.seek(0)
            else:
                file_data = file

            # 使用 Supabase 客户端的标准化命名逻辑
            from app.utils.supabase_client import SupabaseStorageClient
            supabase_client = SupabaseStorageClient()

            # 生成规范化的文件名和存储路径
            standardized_info = supabase_client._generate_standardized_invoice_name(
                detail_id, filename, detail_sequence, file_sequence, file_data
            )

            if standardized_info:
                standardized_filename = standardized_info['filename']
                storage_path = standardized_info['storage_path']
            else:
                # 使用简化命名
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_id = str(uuid.uuid4())[:8]
                standardized_filename = f"invoice_{detail_id}_{timestamp}_{unique_id}.{ext}"
                storage_path = f"expense_invoices/{detail_id}/{standardized_filename}"

            # 确定 content_type
            content_type = self.storage._get_content_type(standardized_filename, 'image')

            result = {
                'url': None,
                'nas_path': None,
                'supabase_url': None,
                'storage': None,
                'synced': False,
                'filename': standardized_filename,
                'original_filename': filename,
                'storage_path': storage_path,
                'standardized': standardized_info is not None
            }

            # 尝试上传到 NAS
            if self.storage.nas_enabled and self.storage.is_nas_available():
                nas_subdir = self.storage.bucket_mapping.get(bucket_type, bucket_type)
                nas_path = f"{nas_subdir}/{storage_path}"

                try:
                    uploaded_path = self.storage.nas_client.upload_file(
                        file_content=file_data,
                        remote_path=nas_path,
                        content_type=content_type
                    )

                    if uploaded_path:
                        result['nas_path'] = nas_path
                        result['url'] = self.storage._get_nas_access_url(nas_path, bucket_type)
                        result['storage'] = 'nas'

                        logger.info(f"发票上传到 NAS: {nas_path}")

                        # 异步同步到 Supabase
                        if self.storage.sync_to_supabase:
                            self._async_sync_invoice_to_supabase(
                                storage_path, file_data, bucket_type, result
                            )

                        return result
                    else:
                        logger.warning("NAS 上传返回空，尝试回退到 Supabase")

                except Exception as e:
                    logger.error(f"NAS 上传异常: {e}, 尝试回退到 Supabase")

            # NAS 不可用或失败，回退到 Supabase
            if self.storage.fallback_enabled:
                try:
                    # 重置文件指针
                    if hasattr(file, 'seek'):
                        file.seek(0)

                    # 使用 SupabaseStorageClient 的原有上传逻辑
                    supabase_result = supabase_client.upload_expense_invoice(
                        detail_id, file, filename, bucket_type,
                        detail_sequence, file_sequence
                    )

                    if supabase_result:
                        # 处理返回结果（支持新旧格式）
                        if isinstance(supabase_result, dict):
                            result['supabase_url'] = supabase_result.get('url')
                            result['url'] = result['supabase_url']
                            result['filename'] = supabase_result.get('filename', standardized_filename)
                            result['storage_path'] = supabase_result.get('storage_path', storage_path)
                        else:
                            result['supabase_url'] = supabase_result
                            result['url'] = supabase_result

                        result['storage'] = 'supabase'
                        result['synced'] = True

                        logger.info(f"发票回退上传到 Supabase: {result.get('storage_path')}")
                        return result

                except Exception as e:
                    logger.error(f"Supabase 回退上传失败: {e}")

            logger.error("发票上传失败：NAS 和 Supabase 都不可用")
            return None

        except Exception as e:
            logger.error(f"upload_expense_invoice 异常: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _async_sync_invoice_to_supabase(
        self,
        storage_path: str,
        file_data: bytes,
        bucket_type: str,
        result: dict
    ):
        """异步同步发票到 Supabase"""
        try:
            from flask import current_app
            app = current_app._get_current_object()
        except RuntimeError:
            logger.warning("无法获取 Flask 应用上下文，跳过异步同步")
            return

        def sync_task():
            with app.app_context():
                try:
                    from app.utils.supabase_client import SupabaseStorageClient
                    supabase = SupabaseStorageClient()
                    bucket_name = supabase.bucket_config.get(bucket_type, supabase.bucket_config['default'])

                    # 上传到 Supabase
                    try:
                        supabase.supabase.storage.from_(bucket_name).upload(
                            storage_path,
                            file_data,
                            {'content-type': 'application/octet-stream', 'x-upsert': 'true'}
                        )
                        # 生成公开 URL
                        url = f"{supabase.supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
                        result['supabase_url'] = url
                        result['synced'] = True
                        logger.info(f"发票异步同步到 Supabase 成功: {storage_path}")
                    except Exception as upload_err:
                        logger.warning(f"发票异步同步到 Supabase 失败: {upload_err}")

                except Exception as e:
                    logger.error(f"发票异步同步异常: {e}")

        thread = threading.Thread(target=sync_task, daemon=True)
        thread.start()


def get_smart_expense_storage() -> SmartExpenseStorage:
    """获取报销单专用存储实例"""
    return SmartExpenseStorage()


class SmartProductStorage:
    """
    产品文件存储 - 专用于产品的智能存储

    NAS 优先，Supabase 备份
    """

    def __init__(self):
        self.storage = get_smart_storage()

    def upload_product_file(
        self,
        product_id: int,
        file,
        file_type: str,
        bucket_type: str = 'product'
    ) -> Optional[str]:
        """
        上传产品文件（NAS 优先，Supabase 备份）

        Args:
            product_id: 产品ID
            file: 文件对象
            file_type: 文件类型 ('image' 或 'pdf')
            bucket_type: 存储桶类型 ('product' 或 'rd_product')

        Returns:
            成功返回文件 URL，失败返回 None
        """
        try:
            filename = file.filename if hasattr(file, 'filename') else 'unnamed'

            # 读取文件内容
            if hasattr(file, 'read'):
                file.seek(0)
                file_data = file.read()
                file.seek(0)
            else:
                file_data = file

            # 生成存储路径
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            safe_filename = f"{file_type}_{product_id}_{timestamp}_{unique_id}.{ext}"
            storage_path = f"{bucket_type}_{product_id}/{safe_filename}"

            # 确定 content_type
            content_type = self.storage._get_content_type(filename, file_type)

            # 尝试上传到 NAS
            if self.storage.nas_enabled and self.storage.is_nas_available():
                nas_subdir = self.storage.bucket_mapping.get(bucket_type, bucket_type)
                nas_path = f"{nas_subdir}/{storage_path}"

                try:
                    uploaded_path = self.storage.nas_client.upload_file(
                        file_content=file_data,
                        remote_path=nas_path,
                        content_type=content_type
                    )

                    if uploaded_path:
                        url = self.storage._get_nas_access_url(nas_path, bucket_type)
                        logger.info(f"产品文件上传到 NAS: {nas_path}")

                        # 异步同步到 Supabase
                        if self.storage.sync_to_supabase:
                            self._async_sync_to_supabase(storage_path, file_data, bucket_type)

                        return url
                    else:
                        logger.warning("NAS 上传返回空，尝试回退到 Supabase")

                except Exception as e:
                    logger.error(f"NAS 上传异常: {e}, 尝试回退到 Supabase")

            # NAS 不可用或失败，回退到 Supabase
            if self.storage.fallback_enabled:
                try:
                    # 重置文件指针
                    if hasattr(file, 'seek'):
                        file.seek(0)

                    from app.utils.supabase_client import SupabaseStorageClient
                    supabase_client = SupabaseStorageClient()

                    url = supabase_client.upload_product_file(
                        product_id, file, file_type, bucket_type
                    )

                    if url:
                        logger.info(f"产品文件回退上传到 Supabase: {url}")
                        return url

                except Exception as e:
                    logger.error(f"Supabase 回退上传失败: {e}")

            logger.error("产品文件上传失败：NAS 和 Supabase 都不可用")
            return None

        except Exception as e:
            logger.error(f"upload_product_file 异常: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _async_sync_to_supabase(
        self,
        storage_path: str,
        file_data: bytes,
        bucket_type: str
    ):
        """异步同步产品文件到 Supabase"""
        try:
            from flask import current_app
            app = current_app._get_current_object()
        except RuntimeError:
            logger.warning("无法获取 Flask 应用上下文，跳过异步同步")
            return

        def sync_task():
            with app.app_context():
                try:
                    from app.utils.supabase_client import SupabaseStorageClient
                    supabase = SupabaseStorageClient()
                    bucket_name = supabase.bucket_config.get(bucket_type, supabase.bucket_config['default'])

                    try:
                        supabase.supabase.storage.from_(bucket_name).upload(
                            storage_path,
                            file_data,
                            {'content-type': 'application/octet-stream', 'x-upsert': 'true'}
                        )
                        logger.info(f"产品文件异步同步到 Supabase 成功: {storage_path}")
                    except Exception as upload_err:
                        logger.warning(f"产品文件异步同步到 Supabase 失败: {upload_err}")

                except Exception as e:
                    logger.error(f"产品文件异步同步异常: {e}")

        thread = threading.Thread(target=sync_task, daemon=True)
        thread.start()


def get_smart_product_storage() -> SmartProductStorage:
    """获取产品专用存储实例"""
    return SmartProductStorage()
