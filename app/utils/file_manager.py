"""
文件管理器 - 专门处理文件删除和管理操作
分离自supabase_client.py以保持代码结构清晰
"""

import os
import logging
from typing import Optional
from urllib.parse import urlparse

# 配置日志
logger = logging.getLogger(__name__)

class FileManager:
    """文件管理器 - 处理文件删除和管理操作"""
    
    def __init__(self, supabase_client=None):
        """
        初始化文件管理器
        
        Args:
            supabase_client: SupabaseStorageClient实例，用于云端文件操作
        """
        self.supabase_client = supabase_client
    
    def delete_product_old_file(self, file_path: str, file_type: str, bucket_type: str = 'product') -> bool:
        """
        删除产品旧文件的统一接口（本地和云端自适应）
        
        Args:
            file_path: 文件路径或URL
            file_type: 文件类型描述 ('图片', 'PDF', 'image', 'pdf')
            bucket_type: 存储桶类型 ('product', 'rd_product', 'invoice', 'default')
            
        Returns:
            删除成功返回True，失败返回False
        """
        if not file_path:
            logger.debug(f"文件路径为空，跳过删除")
            return True
        
        try:
            logger.info(f"🗑️ 删除旧{file_type}文件: {file_path}")
            
            if file_path.startswith('http'):
                # 云端文件，使用Supabase客户端删除
                return self._delete_cloud_file(file_path, file_type, bucket_type)
                
            elif file_path.startswith('/storage/'):
                # 本地文件，直接删除
                return self._delete_local_file(file_path, file_type)
                
            else:
                logger.warning(f"未知文件路径格式: {file_path}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ 删除旧{file_type}文件失败: {str(e)}")
            return False
    
    def _delete_cloud_file(self, file_url: str, file_type: str, bucket_type: str) -> bool:
        """
        删除云端文件
        
        Args:
            file_url: 云端文件URL
            file_type: 文件类型描述
            bucket_type: 存储桶类型
            
        Returns:
            删除成功返回True，失败返回False
        """
        if not self.supabase_client:
            logger.error("Supabase客户端未初始化，无法删除云端文件")
            return False
        
        try:
            delete_success = self.supabase_client.delete_file_by_url(
                file_url=file_url,
                bucket_type=bucket_type
            )
            if delete_success:
                logger.info(f"✅ 已删除云端旧{file_type}文件")
            else:
                logger.warning(f"⚠️ 云端旧{file_type}文件删除失败")
            return delete_success
            
        except Exception as e:
            logger.error(f"删除云端{file_type}文件失败: {str(e)}")
            return False
    
    def _delete_local_file(self, file_path: str, file_type: str) -> bool:
        """
        删除本地文件
        
        Args:
            file_path: 本地文件路径 (如: /storage/products/product_123/file.jpg)
            file_type: 文件类型描述
            
        Returns:
            删除成功返回True，失败返回False
        """
        try:
            # 构建完整的本地文件路径
            # 处理路径格式: /storage/... -> app/static/storage/...
            if file_path.startswith('/storage/'):
                local_path = os.path.join('app/static', file_path.lstrip('/'))
            elif file_path.startswith('/'):
                local_path = os.path.join('app/static', file_path.lstrip('/'))
            else:
                local_path = file_path
            
            # 检查文件是否存在
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info(f"✅ 已删除本地旧{file_type}文件: {local_path}")
                
                # 尝试删除空目录
                self._cleanup_empty_directories(local_path)
                
                return True
            else:
                logger.warning(f"本地{file_type}文件不存在: {local_path}")
                return False
                
        except Exception as e:
            logger.error(f"删除本地{file_type}文件失败: {str(e)}")
            return False
    
    def _cleanup_empty_directories(self, file_path: str) -> None:
        """
        清理空目录（递归向上清理）
        
        Args:
            file_path: 被删除的文件路径
        """
        try:
            parent_dir = os.path.dirname(file_path)
            
            # 只清理非关键目录
            if not self._is_critical_directory(parent_dir):
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                    logger.debug(f"删除空目录: {parent_dir}")
                    
                    # 递归检查父目录
                    self._cleanup_empty_directories(parent_dir)
                    
        except OSError as e:
            # 目录不为空或无法删除，忽略
            logger.debug(f"目录清理跳过: {str(e)}")
    
    def _is_critical_directory(self, dir_path: str) -> bool:
        """
        检查是否为关键目录（不应该被删除）
        
        Args:
            dir_path: 目录路径
            
        Returns:
            如果是关键目录返回True
        """
        critical_dirs = [
            'app/static',
            'app/static/storage',
            'app/static/storage/products',
            'app/static/storage/invoices',
            'app/static/storage/rd_products',
            'app',
            'storage',
        ]
        
        normalized_path = os.path.normpath(dir_path)
        return any(normalized_path.endswith(critical) for critical in critical_dirs)
    
    def delete_multiple_files(self, file_paths: list, file_type: str, bucket_type: str = 'product') -> dict:
        """
        批量删除多个文件
        
        Args:
            file_paths: 文件路径列表
            file_type: 文件类型描述
            bucket_type: 存储桶类型
            
        Returns:
            删除结果字典 {'success': int, 'failed': int, 'details': list}
        """
        result = {
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for file_path in file_paths:
            try:
                if self.delete_product_old_file(file_path, file_type, bucket_type):
                    result['success'] += 1
                    result['details'].append({'path': file_path, 'status': 'success'})
                else:
                    result['failed'] += 1
                    result['details'].append({'path': file_path, 'status': 'failed'})
            except Exception as e:
                result['failed'] += 1
                result['details'].append({'path': file_path, 'status': 'error', 'error': str(e)})
        
        logger.info(f"批量删除{file_type}文件完成: 成功{result['success']}个, 失败{result['failed']}个")
        return result
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径或URL
            
        Returns:
            文件信息字典，失败返回None
        """
        try:
            if file_path.startswith('http'):
                # 云端文件信息
                return self._get_cloud_file_info(file_path)
            elif file_path.startswith('/storage/'):
                # 本地文件信息
                return self._get_local_file_info(file_path)
            else:
                return None
                
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return None
    
    def _get_cloud_file_info(self, file_url: str) -> dict:
        """获取云端文件信息"""
        parsed_url = urlparse(file_url)
        return {
            'type': 'cloud',
            'url': file_url,
            'domain': parsed_url.netloc,
            'path': parsed_url.path,
            'exists': True  # 假设存在，实际检查需要API调用
        }
    
    def _get_local_file_info(self, file_path: str) -> dict:
        """获取本地文件信息"""
        local_path = os.path.join('app/static', file_path.lstrip('/'))
        
        info = {
            'type': 'local',
            'path': file_path,
            'local_path': local_path,
            'exists': os.path.exists(local_path)
        }
        
        if info['exists']:
            stat = os.stat(local_path)
            info.update({
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'readable': os.access(local_path, os.R_OK),
                'writable': os.access(local_path, os.W_OK)
            })
        
        return info


# 全局文件管理器实例
_file_manager = None

def get_file_manager(supabase_client=None) -> FileManager:
    """获取文件管理器单例"""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager(supabase_client)
    elif supabase_client and _file_manager.supabase_client != supabase_client:
        # 更新Supabase客户端
        _file_manager.supabase_client = supabase_client
    return _file_manager