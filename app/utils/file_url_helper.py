"""
文件URL处理辅助工具
确保在本地开发和云端部署环境中都能正确处理文件URL
"""

import os
from flask import current_app, url_for, request
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def normalize_file_url(url_or_path, file_type='image'):
    """
    标准化文件URL，确保在各环境下都能正确访问
    
    Args:
        url_or_path: 文件URL或路径
        file_type: 文件类型，用于日志记录
    
    Returns:
        标准化后的URL
    """
    if not url_or_path:
        return None
    
    try:
        # 检查是否已经是完整的HTTP/HTTPS URL
        parsed = urlparse(str(url_or_path))
        if parsed.scheme in ['http', 'https']:
            # 已经是完整URL，直接返回
            logger.debug(f"使用完整URL: {url_or_path}")
            return url_or_path
        
        # 处理相对路径的情况
        url_str = str(url_or_path)
        
        # 如果是以/static/开头的路径，转换为Flask url_for
        if url_str.startswith('/static/'):
            relative_path = url_str[8:]  # 移除'/static/'前缀
            try:
                # 使用Flask的url_for生成绝对URL
                return url_for('static', filename=relative_path, _external=True)
            except Exception as e:
                logger.warning(f"url_for生成失败，使用原始路径: {e}")
                return url_str
        
        # 如果是以static/开头的路径，添加前缀
        if url_str.startswith('static/'):
            try:
                return url_for('static', filename=url_str[7:], _external=True)
            except Exception as e:
                logger.warning(f"url_for生成失败，使用原始路径: {e}")
                return f"/{url_str}"
        
        # 如果是相对路径但不以static开头，尝试构建URL
        if not url_str.startswith('/'):
            # 假设是static下的文件
            try:
                return url_for('static', filename=url_str, _external=True)
            except Exception as e:
                logger.warning(f"url_for生成失败，使用相对路径: {e}")
                return f"/static/{url_str}"
        
        # 其他情况，返回原始路径
        return url_str
        
    except Exception as e:
        logger.error(f"URL标准化失败: {url_or_path}, 错误: {e}")
        return url_or_path


def get_invoice_image_url(invoice_data):
    """
    获取发票图片的标准化URL
    
    Args:
        invoice_data: 发票数据字典，包含url、path等字段
    
    Returns:
        标准化的图片URL
    """
    if not invoice_data:
        return None
    
    # 优先使用url字段
    if invoice_data.get('url'):
        return normalize_file_url(invoice_data['url'], 'invoice_image')
    
    # 其次使用path字段
    if invoice_data.get('path'):
        return normalize_file_url(invoice_data['path'], 'invoice_image')
    
    # 兼容其他可能的字段名
    for field in ['image_url', 'file_url', 'src']:
        if invoice_data.get(field):
            return normalize_file_url(invoice_data[field], 'invoice_image')
    
    logger.warning(f"未找到有效的图片URL: {invoice_data}")
    return None


def is_cloud_deployment():
    """
    检测是否为云端部署环境
    
    Returns:
        bool: True表示云端环境，False表示本地环境
    """
    # 检查环境变量
    if os.environ.get('FLASK_ENV') == 'production':
        return True
    
    if os.environ.get('RENDER'):  # Render平台
        return True
        
    if os.environ.get('HEROKU'):  # Heroku平台
        return True
        
    if os.environ.get('VERCEL'):  # Vercel平台
        return True
    
    # 检查请求域名
    try:
        if hasattr(request, 'host'):
            host = request.host.lower()
            cloud_indicators = [
                'render.com',
                'herokuapp.com', 
                'vercel.app',
                'railway.app',
                'fly.dev'
            ]
            for indicator in cloud_indicators:
                if indicator in host:
                    return True
    except:
        pass
    
    return False


def get_base_url():
    """
    获取应用的基础URL
    
    Returns:
        应用的基础URL
    """
    try:
        # 尝试从请求上下文获取
        if hasattr(request, 'url_root'):
            return request.url_root.rstrip('/')
    except:
        pass
    
    # 从配置获取
    try:
        if current_app.config.get('SERVER_NAME'):
            scheme = 'https' if current_app.config.get('PREFERRED_URL_SCHEME') == 'https' else 'http'
            return f"{scheme}://{current_app.config['SERVER_NAME']}"
    except:
        pass
    
    # 默认值
    return 'http://localhost:5000'


def ensure_absolute_url(url):
    """
    确保URL是绝对路径
    
    Args:
        url: 输入URL
    
    Returns:
        绝对URL
    """
    if not url:
        return None
    
    parsed = urlparse(str(url))
    if parsed.scheme:
        return url
    
    base_url = get_base_url()
    if url.startswith('/'):
        return f"{base_url}{url}"
    else:
        return f"{base_url}/{url}"


def validate_image_url(url):
    """
    验证图片URL的有效性
    
    Args:
        url: 图片URL
    
    Returns:
        bool: URL是否有效
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(str(url))
        
        # 检查是否有有效的scheme
        if not parsed.scheme and not url.startswith('/'):
            return False
        
        # 检查文件扩展名
        path = parsed.path.lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        if any(path.endswith(ext) for ext in valid_extensions):
            return True
        
        # 如果没有扩展名，但是是有效URL格式，也认为有效
        if parsed.scheme in ['http', 'https'] or url.startswith('/'):
            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"URL验证失败: {url}, 错误: {e}")
        return False