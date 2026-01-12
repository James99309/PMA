# -*- coding: utf-8 -*-
"""
群晖WebDAV存储客户端

用于将会议录音文件存储到群晖NAS的WebDAV服务。
"""

import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin, quote
from typing import Optional, Tuple
from flask import current_app

logger = logging.getLogger(__name__)


class SynologyWebDAVClient:
    """群晖WebDAV存储客户端"""

    def __init__(self):
        """初始化WebDAV客户端"""
        self.base_url = os.getenv('SYNOLOGY_WEBDAV_URL', '')
        self.username = os.getenv('SYNOLOGY_WEBDAV_USER', '')
        self.password = os.getenv('SYNOLOGY_WEBDAV_PASSWORD', '')
        self.base_path = os.getenv('SYNOLOGY_WEBDAV_PATH', '/pma-files')

        # 是否验证SSL证书（群晖自签名证书可能需要禁用）
        self.verify_ssl = os.getenv('SYNOLOGY_WEBDAV_VERIFY_SSL', 'false').lower() == 'true'

        # 超时设置（秒）
        self.timeout = int(os.getenv('SYNOLOGY_WEBDAV_TIMEOUT', '30'))

        self._session = None

    @property
    def session(self) -> requests.Session:
        """获取或创建HTTP会话"""
        if self._session is None:
            self._session = requests.Session()
            self._session.auth = HTTPBasicAuth(self.username, self.password)
            self._session.verify = self.verify_ssl
        return self._session

    @property
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.base_url and self.username and self.password)

    def _build_url(self, remote_path: str) -> str:
        """构建完整的WebDAV URL"""
        # 确保路径以/开头
        if not remote_path.startswith('/'):
            remote_path = '/' + remote_path

        # 组合基础路径和远程路径
        full_path = self.base_path.rstrip('/') + remote_path

        # URL编码路径（保留/）
        encoded_path = '/'.join(quote(segment, safe='') for segment in full_path.split('/'))

        return urljoin(self.base_url, encoded_path)

    def test_connection(self) -> Tuple[bool, str]:
        """测试WebDAV连接

        Returns:
            (success, message) 元组
        """
        if not self.is_configured:
            return False, "WebDAV未配置，请设置环境变量"

        try:
            url = self._build_url('/')
            response = self.session.request(
                'PROPFIND',
                url,
                headers={'Depth': '0'},
                timeout=self.timeout
            )

            if response.status_code in (200, 207):
                return True, "连接成功"
            elif response.status_code == 401:
                return False, "认证失败，请检查用户名和密码"
            elif response.status_code == 403:
                return False, "访问被拒绝，请检查权限设置"
            elif response.status_code == 404:
                return False, f"路径不存在: {self.base_path}"
            else:
                return False, f"连接失败，状态码: {response.status_code}"

        except requests.exceptions.SSLError as e:
            return False, f"SSL证书验证失败: {str(e)}"
        except requests.exceptions.ConnectionError as e:
            return False, f"无法连接到服务器: {str(e)}"
        except requests.exceptions.Timeout:
            return False, "连接超时"
        except Exception as e:
            return False, f"连接错误: {str(e)}"

    def create_directory(self, remote_path: str) -> bool:
        """创建目录

        Args:
            remote_path: 远程目录路径（相对于base_path）

        Returns:
            是否成功
        """
        if not self.is_configured:
            logger.error("WebDAV未配置")
            return False

        try:
            url = self._build_url(remote_path)

            # 确保URL以/结尾（表示目录）
            if not url.endswith('/'):
                url += '/'

            response = self.session.request(
                'MKCOL',
                url,
                timeout=self.timeout
            )

            if response.status_code in (201, 405):
                # 201: 创建成功
                # 405: 目录已存在
                return True
            else:
                logger.error(f"创建目录失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"创建目录异常: {str(e)}")
            return False

    def upload_file(self, file_content: bytes, remote_path: str,
                    content_type: str = 'application/octet-stream') -> Optional[str]:
        """上传文件到群晖

        Args:
            file_content: 文件内容（字节）
            remote_path: 远程文件路径（相对于base_path）
            content_type: 文件MIME类型

        Returns:
            成功返回远程路径，失败返回None
        """
        if not self.is_configured:
            logger.error("WebDAV未配置")
            return None

        try:
            # 确保父目录存在
            parent_dir = '/'.join(remote_path.split('/')[:-1])
            if parent_dir:
                self._ensure_directory_exists(parent_dir)

            url = self._build_url(remote_path)

            response = self.session.put(
                url,
                data=file_content,
                headers={'Content-Type': content_type},
                timeout=self.timeout
            )

            if response.status_code in (200, 201, 204):
                logger.info(f"文件上传成功: {remote_path}")
                return remote_path
            else:
                logger.error(f"文件上传失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"文件上传异常: {str(e)}")
            return None

    def download_file(self, remote_path: str) -> Optional[bytes]:
        """从群晖下载文件

        Args:
            remote_path: 远程文件路径（相对于base_path）

        Returns:
            成功返回文件内容（字节），失败返回None
        """
        if not self.is_configured:
            logger.error("WebDAV未配置")
            return None

        try:
            url = self._build_url(remote_path)

            response = self.session.get(
                url,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.content
            elif response.status_code == 404:
                logger.warning(f"文件不存在: {remote_path}")
                return None
            else:
                logger.error(f"文件下载失败: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"文件下载异常: {str(e)}")
            return None

    def download_file_stream(self, remote_path: str, chunk_size: int = 8192):
        """流式下载文件（用于大文件）

        Args:
            remote_path: 远程文件路径
            chunk_size: 每次读取的块大小

        Yields:
            文件内容块
        """
        if not self.is_configured:
            logger.error("WebDAV未配置")
            return

        try:
            url = self._build_url(remote_path)

            response = self.session.get(
                url,
                stream=True,
                timeout=self.timeout
            )

            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk
            else:
                logger.error(f"流式下载失败: {response.status_code}")

        except Exception as e:
            logger.error(f"流式下载异常: {str(e)}")

    def download_file_range(self, remote_path: str, start: int, end: int) -> Optional[bytes]:
        """下载文件的指定范围（用于音频seek）

        Args:
            remote_path: 远程文件路径
            start: 开始字节位置
            end: 结束字节位置

        Returns:
            文件内容片段
        """
        if not self.is_configured:
            logger.error("WebDAV未配置")
            return None

        try:
            url = self._build_url(remote_path)

            response = self.session.get(
                url,
                headers={'Range': f'bytes={start}-{end}'},
                timeout=self.timeout
            )

            if response.status_code in (200, 206):
                return response.content
            else:
                logger.error(f"范围下载失败: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"范围下载异常: {str(e)}")
            return None

    def get_file_info(self, remote_path: str) -> Optional[dict]:
        """获取文件信息

        Args:
            remote_path: 远程文件路径

        Returns:
            包含文件信息的字典，或None
        """
        if not self.is_configured:
            return None

        try:
            url = self._build_url(remote_path)

            response = self.session.head(
                url,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return {
                    'content_length': int(response.headers.get('Content-Length', 0)),
                    'content_type': response.headers.get('Content-Type', ''),
                    'last_modified': response.headers.get('Last-Modified', ''),
                    'etag': response.headers.get('ETag', '')
                }
            else:
                return None

        except Exception as e:
            logger.error(f"获取文件信息异常: {str(e)}")
            return None

    def delete_file(self, remote_path: str) -> bool:
        """删除群晖上的文件

        Args:
            remote_path: 远程文件路径（相对于base_path）

        Returns:
            是否成功
        """
        if not self.is_configured:
            logger.error("WebDAV未配置")
            return False

        try:
            url = self._build_url(remote_path)

            response = self.session.delete(
                url,
                timeout=self.timeout
            )

            if response.status_code in (200, 204, 404):
                # 200/204: 删除成功
                # 404: 文件不存在，也算成功
                logger.info(f"文件删除成功: {remote_path}")
                return True
            else:
                logger.error(f"文件删除失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"文件删除异常: {str(e)}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        """检查文件是否存在

        Args:
            remote_path: 远程文件路径

        Returns:
            文件是否存在
        """
        if not self.is_configured:
            return False

        try:
            url = self._build_url(remote_path)

            response = self.session.head(
                url,
                timeout=self.timeout
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"检查文件存在异常: {str(e)}")
            return False

    def _ensure_directory_exists(self, dir_path: str) -> bool:
        """确保目录存在，如果不存在则递归创建

        Args:
            dir_path: 目录路径

        Returns:
            是否成功
        """
        parts = dir_path.strip('/').split('/')
        current_path = ''

        for part in parts:
            if not part:
                continue
            current_path += '/' + part
            self.create_directory(current_path)

        return True

    def get_internal_url(self, remote_path: str) -> str:
        """获取内部访问URL（需要通过后端代理）

        Args:
            remote_path: 远程文件路径

        Returns:
            内部代理URL
        """
        # 返回通过后端代理访问的URL
        # 格式: /meeting/audio/stream?path=xxx
        from urllib.parse import quote
        return f"/meeting/audio/stream?path={quote(remote_path)}"


# 单例模式
_webdav_client = None


def get_synology_webdav_client() -> SynologyWebDAVClient:
    """获取群晖WebDAV客户端单例"""
    global _webdav_client
    if _webdav_client is None:
        _webdav_client = SynologyWebDAVClient()
    return _webdav_client


def is_synology_storage_enabled() -> bool:
    """检查是否启用了群晖存储"""
    storage_type = os.getenv('MEETING_STORAGE_TYPE', 'synology').lower()
    return storage_type == 'synology'
