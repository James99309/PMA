"""
产品文件管理服务
负责产品相关文件的上传、下载、预览和管理
"""
import os
import uuid
import logging
from typing import Tuple, Optional
from flask import current_app, Response, jsonify
from flask_login import current_user
from werkzeug.datastructures import FileStorage
from app.models.product import Product
from app.extensions import db
from app.utils.supabase_client import get_supabase_client
from app.utils.file_manager import get_file_manager

logger = logging.getLogger(__name__)

# 文件类型配置
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 12 * 1024 * 1024  # 12MB


class ProductFileService:
    """产品文件管理服务类"""
    
    def __init__(self):
        self.supabase_client = get_supabase_client()
        self.file_manager = get_file_manager(self.supabase_client)
    
    def upload_image(self, product_id: int, image_file: FileStorage) -> dict:
        """
        上传产品图片
        
        Args:
            product_id: 产品ID
            image_file: 图片文件对象
            
        Returns:
            dict: 上传结果 {'success': bool, 'image_url': str, 'error': str}
        """
        try:
            logger.info(f"🖼️ 开始上传产品图片: 产品ID={product_id}, 文件={image_file.filename}")
            
            # 验证产品存在
            product = Product.query.get_or_404(product_id)
            
            # 验证文件
            is_valid, error_msg = self._validate_file(image_file, 'image')
            if not is_valid:
                return {'success': False, 'error': error_msg}
            
            # 删除旧图片并上传新图片
            image_url = self._cleanup_and_upload(product, image_file, 'image')
            
            if image_url:
                # 更新数据库
                product.image_path = image_url
                db.session.commit()
                
                logger.info(f"✅ 产品 {product_id} 图片上传成功: {image_url}")
                return {'success': True, 'image_url': image_url}
            else:
                return {'success': False, 'error': '图片上传失败'}
                
        except Exception as e:
            logger.error(f"💥 产品 {product_id} 图片上传异常: {str(e)}", exc_info=True)
            db.session.rollback()
            return {'success': False, 'error': f'图片上传错误: {str(e)}'}
    
    def upload_pdf(self, product_id: int, pdf_file: FileStorage) -> dict:
        """
        上传产品PDF文档
        
        Args:
            product_id: 产品ID
            pdf_file: PDF文件对象
            
        Returns:
            dict: 上传结果 {'success': bool, 'pdf_url': str, 'error': str}
        """
        try:
            logger.info(f"📄 开始上传产品PDF: 产品ID={product_id}, 文件={pdf_file.filename}")
            
            # 验证产品存在
            product = Product.query.get_or_404(product_id)
            
            # 验证文件
            is_valid, error_msg = self._validate_file(pdf_file, 'pdf')
            if not is_valid:
                return {'success': False, 'error': error_msg}
            
            # 删除旧PDF并上传新PDF
            pdf_url = self._cleanup_and_upload(product, pdf_file, 'pdf')
            
            if pdf_url:
                # 更新数据库
                product.pdf_path = pdf_url
                db.session.commit()
                
                logger.info(f"✅ 产品 {product_id} PDF上传成功: {pdf_url}")
                return {'success': True, 'pdf_url': pdf_url}
            else:
                return {'success': False, 'error': 'PDF上传失败'}
                
        except Exception as e:
            logger.error(f"💥 产品 {product_id} PDF上传异常: {str(e)}", exc_info=True)
            db.session.rollback()
            return {'success': False, 'error': f'PDF上传错误: {str(e)}'}
    
    def download_pdf(self, product_id: int) -> Response:
        """
        下载产品PDF文件
        
        Args:
            product_id: 产品ID
            
        Returns:
            Response: 文件下载响应
        """
        product = Product.query.get_or_404(product_id)
        
        if not product.pdf_path:
            return jsonify({'error': '该产品没有PDF文件'}), 404
        
        try:
            # 如果是云端文件，通过代理方式强制下载
            if product.pdf_path.startswith('http'):
                import requests
                import urllib.parse
                
                # 获取云端文件内容
                response = requests.get(product.pdf_path, timeout=30)
                response.raise_for_status()
                
                # 处理中文文件名
                original_filename = f"{product.name}.pdf"
                encoded_filename = urllib.parse.quote(original_filename)
                
                # 创建强制下载的响应
                return Response(
                    response.content,
                    mimetype='application/pdf',
                    headers={
                        'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}',
                        'Content-Length': str(len(response.content))
                    }
                )
            else:
                # 处理本地文件
                pdf_file_path = os.path.join(current_app.static_folder, product.pdf_path)
                if not os.path.exists(pdf_file_path):
                    return jsonify({'error': 'PDF文件不存在'}), 404
                
                from flask import send_file
                return send_file(
                    pdf_file_path,
                    as_attachment=True,
                    download_name=f"{product.name}.pdf",
                    mimetype='application/pdf'
                )
                
        except Exception as e:
            logger.error(f"下载PDF文件失败: {str(e)}")
            return jsonify({'error': '下载PDF文件失败'}), 500
    
    def preview_pdf(self, product_id: int) -> Response:
        """
        预览产品PDF文件
        
        Args:
            product_id: 产品ID
            
        Returns:
            Response: PDF预览响应
        """
        product = Product.query.get_or_404(product_id)
        
        if not product.pdf_path:
            return jsonify({'error': 'PDF文件不存在'}), 404
        
        try:
            # 处理云端文件
            if product.pdf_path.startswith('http'):
                import requests
                
                # 代理方式获取文件内容，确保PDF.js能正常加载
                response = requests.get(product.pdf_path, timeout=30)
                response.raise_for_status()
                
                # 返回PDF内容，设置正确的CORS头
                return Response(
                    response.content,
                    mimetype='application/pdf',
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Content-Length': str(len(response.content)),
                        'Cache-Control': 'public, max-age=3600'  # 缓存1小时
                    }
                )
            else:
                # 处理本地文件
                pdf_file_path = os.path.join(current_app.static_folder, product.pdf_path)
                if not os.path.exists(pdf_file_path):
                    return jsonify({'error': 'PDF文件不存在'}), 404
                
                from flask import send_file
                return send_file(
                    pdf_file_path,
                    mimetype='application/pdf',
                    as_attachment=False,  # 不强制下载
                    add_etags=True,      # 启用缓存
                    max_age=3600         # 缓存1小时
                )
                
        except Exception as e:
            logger.error(f"获取PDF预览内容失败: {str(e)}")
            return jsonify({'error': '获取PDF预览内容失败'}), 500
    
    def _validate_file(self, file: FileStorage, file_type: str) -> Tuple[bool, str]:
        """
        验证上传文件
        
        Args:
            file: 文件对象
            file_type: 文件类型 ('image' 或 'pdf')
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        if not file or not file.filename:
            return False, '请选择要上传的文件'
        
        # 检查文件类型
        filename = file.filename.lower()
        if file_type == 'image':
            allowed_extensions = ALLOWED_IMAGE_EXTENSIONS
            type_name = '图片'
        elif file_type == 'pdf':
            allowed_extensions = ALLOWED_PDF_EXTENSIONS
            type_name = 'PDF'
        else:
            return False, '不支持的文件类型'
        
        if not ('.' in filename and filename.rsplit('.', 1)[1] in allowed_extensions):
            extensions_str = ', '.join(allowed_extensions)
            return False, f'不支持的{type_name}格式！请选择 {extensions_str} 文件'
        
        # 检查文件大小
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()  # 获取文件大小
        file.seek(0)  # 重置文件指针
        
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
            return False, f'{type_name}文件太大！最大允许 {max_size_mb}MB，当前文件: {size_mb:.1f}MB'
        
        return True, ''
    
    def _cleanup_and_upload(self, product: Product, file: FileStorage, file_type: str) -> Optional[str]:
        """
        清理旧文件并上传新文件（原子操作）
        
        Args:
            product: 产品对象
            file: 新文件对象
            file_type: 文件类型 ('image' 或 'pdf')
            
        Returns:
            str: 新文件的URL，失败返回None
        """
        try:
            # 确定要清理的旧文件路径
            old_file_path = None
            if file_type == 'image' and product.image_path:
                old_file_path = product.image_path
            elif file_type == 'pdf' and product.pdf_path:
                old_file_path = product.pdf_path
            
            # 上传新文件
            new_file_url = self.supabase_client.upload_product_file(
                product_id=product.id,
                file=file,
                file_type=file_type,
                bucket_type='product'
            )
            
            if new_file_url:
                # 上传成功后清理旧文件
                if old_file_path:
                    self.file_manager.delete_product_old_file(
                        file_path=old_file_path,
                        file_type=file_type,
                        bucket_type='product'
                    )
                    logger.info(f"🗑️ 已清理旧{file_type}文件: {old_file_path}")
                
                return new_file_url
            else:
                logger.error(f"❌ {file_type}文件上传失败: supabase_client返回None")
                return None
                
        except Exception as e:
            logger.error(f"💥 文件清理和上传失败: {str(e)}")
            return None


# 创建全局服务实例
_product_file_service = None

def get_product_file_service() -> ProductFileService:
    """获取产品文件服务实例（单例模式）"""
    global _product_file_service
    if _product_file_service is None:
        _product_file_service = ProductFileService()
    return _product_file_service