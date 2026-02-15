# -*- coding: utf-8 -*-
"""
智能文件存储代理路由

通过应用代理访问文件，支持 NAS 优先、Supabase 回退：
1. 权限控制 - 只有登录用户能访问
2. 智能回退 - NAS 不可用时自动从 Supabase 获取
3. 统一入口 - 简化前端访问逻辑
"""

import os
import logging
from flask import Blueprint, request, Response, abort, send_file, current_app
from flask_login import login_required, current_user
from urllib.parse import unquote
from io import BytesIO

logger = logging.getLogger(__name__)

storage_bp = Blueprint('storage', __name__, url_prefix='/storage')

# NAS 子目录 → Supabase 存储桶映射
BUCKET_MAPPING = {
    'invoice': 'invoice-images',
    'product': 'product-images',
    'rd_product': 'rd-product-images',
    'meeting': 'meeting-recordings',
    'chat': 'chat-files',
}


def _get_file_with_fallback(file_path: str, bucket_type: str):
    """
    智能获取文件（NAS 优先，Supabase 回退）

    Args:
        file_path: 文件路径
        bucket_type: 存储桶类型

    Returns:
        tuple: (file_content, source) - 文件内容和来源 ('nas' 或 'supabase')
    """
    from app.utils.synology_webdav_client import get_synology_webdav_client, is_synology_storage_enabled, is_nas_available

    file_content = None
    source = None

    # 1. 尝试从 NAS 获取
    if is_synology_storage_enabled() and is_nas_available():
        try:
            client = get_synology_webdav_client()
            if client.is_configured:
                file_content = client.download_file(file_path)
                if file_content:
                    source = 'nas'
                    logger.debug(f"从 NAS 获取文件: {file_path}")
        except Exception as e:
            logger.warning(f"NAS 获取文件失败: {file_path}, 错误: {e}")

    # 2. NAS 失败，回退到 Supabase（仅非本地存储模式）
    if file_content is None:
        try:
            from app.utils.supabase_client import SupabaseStorageClient
            supabase = SupabaseStorageClient()

            if not supabase.use_local_storage:
                # 从 file_path 中提取 Supabase 存储路径
                # file_path 格式: invoices/invoice_files/LOCAL-PMA/BX.../xxx.png
                # Supabase 路径: invoice_files/LOCAL-PMA/BX.../xxx.png
                parts = file_path.split('/', 1)
                if len(parts) > 1:
                    supabase_path = parts[1]  # 去掉第一级目录
                else:
                    supabase_path = file_path

                bucket_name = BUCKET_MAPPING.get(bucket_type, 'invoice-images')
                file_content = supabase.supabase.storage.from_(bucket_name).download(supabase_path)

                if file_content:
                    source = 'supabase'
                    logger.info(f"从 Supabase 回退获取文件: {bucket_name}/{supabase_path}")
        except Exception as e:
            logger.warning(f"Supabase 获取文件也失败: {file_path}, 错误: {e}")

    # 3. 本地文件存储回退（supabase_client 本地模式上传的文件）
    if file_content is None:
        try:
            local_root = os.getenv('LOCAL_STORAGE_ROOT', './storage')
            local_path = os.path.join(local_root, file_path)
            if os.path.exists(local_path):
                with open(local_path, 'rb') as f:
                    file_content = f.read()
                source = 'local'
                logger.debug(f"从本地存储读取: {local_path}")
        except Exception as e:
            logger.warning(f"本地文件读取失败: {file_path}, 错误: {e}")

    return file_content, source


@storage_bp.route('/nas/<bucket_type>')
@login_required
def proxy_nas_file(bucket_type: str):
    """
    代理访问文件（NAS 优先，Supabase 回退）

    URL: /storage/nas/<bucket_type>?path=xxx

    Args:
        bucket_type: 存储桶类型 (invoice/product/rd_product)

    Query Params:
        path: 文件路径
    """
    file_path = request.args.get('path', '')
    if not file_path:
        abort(400, description="缺少 path 参数")

    # URL 解码
    file_path = unquote(file_path)

    # 安全检查 - 防止路径遍历（检查 ../ 或 /.. 而非单纯 .. ，避免文件名含多点号误判）
    if '/../' in file_path or file_path.startswith('../') or file_path.endswith('/..') or file_path.startswith('/'):
        abort(400, description="无效的文件路径")

    # 智能获取文件（NAS 优先，Supabase 回退）
    file_content, source = _get_file_with_fallback(file_path, bucket_type)

    if file_content is None:
        abort(404, description="文件不存在")

    # 确定 Content-Type
    content_type = _get_content_type(file_path)

    # 获取文件名（RFC 5987 编码处理中文文件名）
    filename = file_path.split('/')[-1]
    from urllib.parse import quote
    encoded_filename = quote(filename)

    # 返回文件
    return Response(
        file_content,
        mimetype=content_type,
        headers={
            'Content-Disposition': f"inline; filename*=UTF-8''{encoded_filename}",
            'Cache-Control': 'private, max-age=3600',
            'X-Storage-Source': source or 'unknown'
        }
    )


@storage_bp.route('/nas/<bucket_type>/download')
@login_required
def download_nas_file(bucket_type: str):
    """
    下载文件（强制下载，NAS 优先，Supabase 回退）

    URL: /storage/nas/<bucket_type>/download?path=xxx
    """
    file_path = request.args.get('path', '')
    if not file_path:
        abort(400, description="缺少 path 参数")

    file_path = unquote(file_path)

    if '/../' in file_path or file_path.startswith('../') or file_path.endswith('/..') or file_path.startswith('/'):
        abort(400, description="无效的文件路径")

    # 智能获取文件
    file_content, source = _get_file_with_fallback(file_path, bucket_type)

    if file_content is None:
        abort(404, description="文件不存在")

    content_type = _get_content_type(file_path)
    filename = file_path.split('/')[-1]
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return Response(
        file_content,
        mimetype=content_type,
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
            'Cache-Control': 'no-cache',
            'X-Storage-Source': source or 'unknown'
        }
    )


@storage_bp.route('/status')
@login_required
def storage_status():
    """获取存储状态"""
    from app.utils.smart_storage_manager import get_smart_storage

    storage = get_smart_storage()
    status = storage.get_status()

    return {
        'success': True,
        'status': status
    }


def _get_content_type(file_path: str) -> str:
    """根据文件扩展名获取 Content-Type"""
    ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ''

    content_types = {
        # 图片
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'heic': 'image/heic',
        'heif': 'image/heif',
        'bmp': 'image/bmp',
        # 文档
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'txt': 'text/plain',
        'csv': 'text/csv',
        'json': 'application/json',
        'xml': 'application/xml',
        # 压缩包
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed',
        # 音频
        'mp3': 'audio/mpeg',
        'm4a': 'audio/mp4',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        # 视频
        'mp4': 'video/mp4',
        'mov': 'video/quicktime',
        'avi': 'video/x-msvideo',
        'webm': 'video/webm',
        'mkv': 'video/x-matroska',
        'wmv': 'video/x-ms-wmv',
        'flv': 'video/x-flv',
    }

    return content_types.get(ext, 'application/octet-stream')
