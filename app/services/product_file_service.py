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
from app.models.dev_product import DevProduct
from app.models.product_code import ProductSubcategory
from app.extensions import db
from app.utils.supabase_client import get_supabase_client
from app.utils.file_manager import get_file_manager

logger = logging.getLogger(__name__)

# 文件类型配置
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB（无实际限制）


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
        下载产品PDF文件（支持分类共享、NAS 智能存储）

        Args:
            product_id: 产品ID

        Returns:
            Response: 文件下载响应
        """
        # 强制刷新会话，确保获取最新数据（上传后立即下载场景）
        db.session.expire_all()

        product = Product.query.get_or_404(product_id)

        # 获取有效的PDF路径（产品自身或分类共享）
        effective_pdf = self.get_effective_file_path(product, 'pdf')

        if not effective_pdf:
            return jsonify({'error': '该产品没有PDF文件'}), 404

        try:
            import urllib.parse

            # 处理中文文件名
            original_filename = f"{product.product_name or product.product_mn}.pdf"
            encoded_filename = urllib.parse.quote(original_filename)

            # 处理 NAS 智能存储路径
            if effective_pdf.startswith('/storage/nas/'):
                from app.views.storage import _get_file_with_fallback
                from urllib.parse import urlparse, parse_qs

                parsed = urlparse(effective_pdf)
                path_parts = parsed.path.split('/')
                bucket_type = path_parts[3] if len(path_parts) > 3 else 'product'
                query_params = parse_qs(parsed.query)
                nas_path = query_params.get('path', [''])[0]

                if nas_path:
                    file_content, source = _get_file_with_fallback(nas_path, bucket_type)
                    if file_content:
                        logger.info(f"产品PDF从 {source} 获取成功")
                        return Response(
                            file_content,
                            mimetype='application/pdf',
                            headers={
                                'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}',
                                'Content-Length': str(len(file_content)),
                                'X-Storage-Source': source or 'unknown'
                            }
                        )
                    else:
                        return jsonify({'error': 'PDF文件不存在'}), 404

            # 如果是云端文件，通过代理方式强制下载
            elif effective_pdf.startswith('http'):
                import requests

                # 获取云端文件内容
                response = requests.get(effective_pdf, timeout=30)
                response.raise_for_status()

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
                pdf_file_path = os.path.join(current_app.static_folder, effective_pdf)
                if not os.path.exists(pdf_file_path):
                    return jsonify({'error': 'PDF文件不存在'}), 404

                from flask import send_file
                return send_file(
                    pdf_file_path,
                    as_attachment=True,
                    download_name=f"{product.product_name or product.product_mn}.pdf",
                    mimetype='application/pdf'
                )

        except Exception as e:
            logger.error(f"下载PDF文件失败: {str(e)}")
            return jsonify({'error': '下载PDF文件失败'}), 500
    
    def preview_pdf(self, product_id: int) -> Response:
        """
        预览产品PDF文件（支持分类共享、NAS 智能存储）

        Args:
            product_id: 产品ID

        Returns:
            Response: PDF预览响应
        """
        # 强制刷新会话，确保获取最新数据
        db.session.expire_all()

        product = Product.query.get_or_404(product_id)

        # 获取有效的PDF路径（产品自身或分类共享）
        effective_pdf = self.get_effective_file_path(product, 'pdf')

        if not effective_pdf:
            return jsonify({'error': 'PDF文件不存在'}), 404

        try:
            # 处理 NAS 智能存储路径
            if effective_pdf.startswith('/storage/nas/'):
                from app.views.storage import _get_file_with_fallback
                from urllib.parse import urlparse, parse_qs

                parsed = urlparse(effective_pdf)
                path_parts = parsed.path.split('/')
                bucket_type = path_parts[3] if len(path_parts) > 3 else 'product'
                query_params = parse_qs(parsed.query)
                nas_path = query_params.get('path', [''])[0]

                if nas_path:
                    file_content, source = _get_file_with_fallback(nas_path, bucket_type)
                    if file_content:
                        logger.info(f"产品PDF预览从 {source} 获取成功")
                        return Response(
                            file_content,
                            mimetype='application/pdf',
                            headers={
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'GET',
                                'Access-Control-Allow-Headers': 'Content-Type',
                                'Content-Length': str(len(file_content)),
                                'Cache-Control': 'public, max-age=3600',
                                'X-Storage-Source': source or 'unknown'
                            }
                        )
                    else:
                        return jsonify({'error': 'PDF文件不存在'}), 404

            # 处理云端文件
            elif effective_pdf.startswith('http'):
                import requests

                # 代理方式获取文件内容，确保PDF.js能正常加载
                response = requests.get(effective_pdf, timeout=30)
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
                pdf_file_path = os.path.join(current_app.static_folder, effective_pdf)
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
            logger.error(f"获取PDF预览内容失败: product_id={product_id}, effective_pdf={effective_pdf}, error={str(e)}", exc_info=True)
            return jsonify({'error': '获取PDF预览内容失败'}), 500

    def clear_file(self, product_id: int, file_type: str) -> dict:
        """
        清除产品文件（仅限产品自身文件，不影响分类共享文件）

        Args:
            product_id: 产品ID
            file_type: 'image' 或 'pdf'

        Returns:
            dict: {'success': bool, 'error': str, 'is_shared': bool}
        """
        try:
            product = Product.query.get_or_404(product_id)

            # 获取产品自身的文件路径
            file_path = product.image_path if file_type == 'image' else product.pdf_path

            # 检查是否使用子分类共享文件
            if not file_path:
                # 检查是否有子分类共享文件
                if product.subcategory_obj:
                    subcategory_file = product.subcategory_obj.image_path if file_type == 'image' else product.subcategory_obj.pdf_path
                    if subcategory_file:
                        return {'success': False, 'is_shared': True, 'error': '该文件为子分类共享文件，不能从单个产品清除'}
                return {'success': False, 'error': '没有可清除的文件'}

            # 删除存储中的文件（云端或本地）
            self.file_manager.delete_product_old_file(file_path, file_type, 'product')
            logger.info(f"🗑️ 产品 {product_id} {file_type}文件已删除: {file_path}")

            # 清空数据库字段
            if file_type == 'image':
                product.image_path = None
            else:
                product.pdf_path = None

            db.session.commit()
            logger.info(f"✅ 产品 {product_id} {file_type}文件清除成功")
            return {'success': True}

        except Exception as e:
            logger.error(f"💥 产品 {product_id} {file_type}文件清除失败: {str(e)}", exc_info=True)
            db.session.rollback()
            return {'success': False, 'error': f'清除文件失败: {str(e)}'}

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

            # 使用智能存储系统上传新文件（NAS 优先，Supabase 备份）
            from app.utils.smart_storage_manager import get_smart_product_storage
            smart_storage = get_smart_product_storage()

            new_file_url = smart_storage.upload_product_file(
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
                logger.error(f"❌ {file_type}文件上传失败: smart_storage返回None")
                return None

        except Exception as e:
            logger.error(f"💥 文件清理和上传失败: {str(e)}")
            return None

    def upload_file_with_category(self, product_id: int, file: FileStorage, file_type: str,
                                  update_category: Optional[bool] = None) -> dict:
        """
        统一处理图片/PDF上传，支持分类共享

        Args:
            product_id: 产品ID
            file: 文件对象
            file_type: 文件类型 ('image' 或 'pdf')
            update_category: True=更新分类文件, False=仅产品, None=自动判断

        Returns:
            dict: {
                'success': bool,
                'file_url': str,  # 上传成功的文件URL
                'need_confirm': bool,  # 是否需要用户确认覆盖分类文件
                'category_has_file': bool,  # 分类是否已有文件
                'error': str
            }
        """
        try:
            logger.info(f"📂 开始上传产品{file_type}: 产品ID={product_id}, 文件={file.filename}")

            # 验证产品存在
            product = Product.query.get_or_404(product_id)

            # 验证文件
            is_valid, error_msg = self._validate_file(file, file_type)
            if not is_valid:
                return {'success': False, 'error': error_msg}

            # 获取产品子分类（产品名称）
            subcategory = ProductSubcategory.query.get(product.subcategory_id) if product.subcategory_id else None
            if not subcategory:
                return {'success': False, 'error': '产品没有关联子分类'}

            # 获取子分类文件路径
            subcategory_file_path = subcategory.image_path if file_type == 'image' else subcategory.pdf_path
            product_file_path = product.image_path if file_type == 'image' else product.pdf_path

            # 场景1：子分类没有文件 → 自动设为子分类文件
            if not subcategory_file_path:
                file_url = self._cleanup_and_upload(product, file, file_type)
                if file_url:
                    # 设为子分类文件
                    if file_type == 'image':
                        subcategory.image_path = file_url
                    else:
                        subcategory.pdf_path = file_url
                    db.session.commit()
                    logger.info(f"✅ 产品 {product_id} {file_type}上传成功，已设为子分类共享文件: {file_url}")
                    return {'success': True, 'file_url': file_url, 'set_as_category': True}
                else:
                    return {'success': False, 'error': f'{file_type}上传失败'}

            # 场景2：子分类已有文件
            # 如果 update_category 为 None，需要用户确认
            if update_category is None:
                return {
                    'success': False,
                    'need_confirm': True,
                    'category_has_file': True,
                    'category_file_url': subcategory_file_path,
                    'message': '子分类已有共享文件，请选择操作方式'
                }

            # 上传文件
            file_url = self._cleanup_and_upload(product, file, file_type)
            if not file_url:
                return {'success': False, 'error': f'{file_type}上传失败'}

            if update_category:
                # 用户选择覆盖子分类文件
                old_subcategory_file = subcategory_file_path

                # 更新子分类文件
                if file_type == 'image':
                    subcategory.image_path = file_url
                    # 清空产品自身文件引用（因为_cleanup_and_upload已删除旧文件）
                    if product.image_path:
                        product.image_path = None
                else:
                    subcategory.pdf_path = file_url
                    # 清空产品自身文件引用（因为_cleanup_and_upload已删除旧文件）
                    if product.pdf_path:
                        product.pdf_path = None

                # 清理旧的子分类文件
                if old_subcategory_file:
                    self.file_manager.delete_product_old_file(
                        file_path=old_subcategory_file,
                        file_type=file_type,
                        bucket_type='product'
                    )
                    logger.info(f"🗑️ 已清理旧子分类{file_type}文件: {old_subcategory_file}")

                db.session.commit()
                logger.info(f"✅ 产品 {product_id} {file_type}上传成功，已覆盖子分类共享文件: {file_url}")
                return {'success': True, 'file_url': file_url, 'updated_category': True}
            else:
                # 用户选择仅用于此产品
                if file_type == 'image':
                    product.image_path = file_url
                else:
                    product.pdf_path = file_url

                db.session.commit()
                logger.info(f"✅ 产品 {product_id} {file_type}上传成功，仅用于此产品: {file_url}")
                return {'success': True, 'file_url': file_url, 'product_only': True}

        except Exception as e:
            logger.error(f"💥 产品 {product_id} {file_type}上传异常: {str(e)}", exc_info=True)
            db.session.rollback()
            return {'success': False, 'error': f'{file_type}上传错误: {str(e)}'}

    def check_file_exists(self, file_path: str) -> bool:
        """
        检查文件是否实际存在于存储中（NAS/本地）

        用于在页面渲染前验证数据库记录的文件路径是否真实可用，
        避免显示无法下载的文件链接。
        """
        if not file_path:
            return False

        try:
            # NAS 智能存储路径: /storage/nas/product?path=products/...
            if file_path.startswith('/storage/nas/'):
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(file_path)
                query_params = parse_qs(parsed.query)
                nas_path = query_params.get('path', [''])[0]
                if nas_path:
                    from app.utils.synology_webdav_client import get_synology_webdav_client
                    client = get_synology_webdav_client()
                    return client.file_exists(nas_path) if client and client.is_configured else False
                return False

            # 云端 URL (http/https) — 不做远程检查，信任数据库
            elif file_path.startswith('http'):
                return True

            # 本地文件
            else:
                local_path = os.path.join(current_app.static_folder, file_path)
                return os.path.exists(local_path)

        except Exception as e:
            logger.warning(f"文件存在性检查失败: {file_path}, 错误: {e}")
            return False

    def get_effective_file_path(self, product: Product, file_type: str) -> Optional[str]:
        """
        获取产品的有效文件路径（三级引用：产品自身 > 同名产品 > 子分类共享）

        Args:
            product: 产品对象
            file_type: 'image' 或 'pdf'

        Returns:
            str: 有效的文件路径，没有则返回None
        """
        from app.utils.product_helpers import get_effective_file
        return get_effective_file(product, file_type)

    def upload_file_with_category_generic(self, product_id: int, file: FileStorage, file_type: str,
                                          product_type: str = 'standard',
                                          update_category: Optional[bool] = None) -> dict:
        """
        通用文件上传方法，支持标准产品和研发产品

        Args:
            product_id: 产品ID
            file: 文件对象
            file_type: 文件类型 ('image' 或 'pdf')
            product_type: 产品类型 ('standard' 或 'research')
            update_category: True=更新分类文件, False=仅产品, None=自动判断

        Returns:
            dict: 上传结果
        """
        try:
            logger.info(f"📂 开始上传{product_type}产品{file_type}: 产品ID={product_id}, 文件={file.filename}")

            # 根据产品类型获取产品对象
            if product_type == 'research':
                product = DevProduct.query.get_or_404(product_id)
                bucket_type = 'rd_product'
            else:
                product = Product.query.get_or_404(product_id)
                bucket_type = 'product'

            # 验证文件
            is_valid, error_msg = self._validate_file(file, file_type)
            if not is_valid:
                return {'success': False, 'error': error_msg}

            # 获取产品子分类
            subcategory = ProductSubcategory.query.get(product.subcategory_id) if product.subcategory_id else None
            if not subcategory:
                return {'success': False, 'error': '产品没有关联子分类'}

            # 获取子分类文件路径
            subcategory_file_path = subcategory.image_path if file_type == 'image' else subcategory.pdf_path

            # 场景1：子分类没有文件 → 自动设为子分类文件
            if not subcategory_file_path:
                file_url = self._cleanup_and_upload_generic(product, file, file_type, bucket_type)
                if file_url:
                    # 设为子分类文件
                    if file_type == 'image':
                        subcategory.image_path = file_url
                    else:
                        subcategory.pdf_path = file_url
                    db.session.commit()
                    logger.info(f"✅ {product_type}产品 {product_id} {file_type}上传成功，已设为子分类共享文件: {file_url}")
                    return {'success': True, 'file_url': file_url, 'set_as_category': True}
                else:
                    return {'success': False, 'error': f'{file_type}上传失败'}

            # 场景2：子分类已有文件
            if update_category is None:
                return {
                    'success': False,
                    'need_confirm': True,
                    'category_has_file': True,
                    'category_file_url': subcategory_file_path,
                    'message': '子分类已有共享文件，请选择操作方式'
                }

            # 上传文件
            file_url = self._cleanup_and_upload_generic(product, file, file_type, bucket_type)
            if not file_url:
                return {'success': False, 'error': f'{file_type}上传失败'}

            # 调试：验证上传后的URL是否可访问
            if file_url.startswith('http'):
                import requests as req
                try:
                    head_resp = req.head(file_url, timeout=10)
                    logger.info(f"🔍 上传后URL验证: {file_url} -> status={head_resp.status_code}")
                    if head_resp.status_code >= 400:
                        logger.warning(f"⚠️ 上传后URL不可访问: {file_url} -> {head_resp.status_code}")
                except Exception as url_err:
                    logger.warning(f"⚠️ 上传后URL验证失败: {file_url} -> {str(url_err)}")

            if update_category:
                # 用户选择覆盖子分类文件
                old_subcategory_file = subcategory_file_path

                # 更新子分类文件
                if file_type == 'image':
                    subcategory.image_path = file_url
                else:
                    subcategory.pdf_path = file_url

                # 清理旧的子分类文件
                if old_subcategory_file:
                    self.file_manager.delete_product_old_file(
                        file_path=old_subcategory_file,
                        file_type=file_type,
                        bucket_type=bucket_type
                    )
                    logger.info(f"🗑️ 已清理旧子分类{file_type}文件: {old_subcategory_file}")

                db.session.commit()
                logger.info(f"✅ {product_type}产品 {product_id} {file_type}上传成功，已覆盖子分类共享文件: {file_url}")
                return {'success': True, 'file_url': file_url, 'updated_category': True}
            else:
                # 用户选择仅用于此产品
                if file_type == 'image':
                    product.image_path = file_url
                else:
                    product.pdf_path = file_url

                db.session.commit()
                logger.info(f"✅ {product_type}产品 {product_id} {file_type}上传成功，仅用于此产品: {file_url}")
                return {'success': True, 'file_url': file_url, 'product_only': True}

        except Exception as e:
            logger.error(f"💥 {product_type}产品 {product_id} {file_type}上传异常: {str(e)}", exc_info=True)
            db.session.rollback()
            return {'success': False, 'error': f'{file_type}上传错误: {str(e)}'}

    def _cleanup_and_upload_generic(self, product, file: FileStorage, file_type: str, bucket_type: str) -> Optional[str]:
        """
        通用清理并上传文件方法

        Args:
            product: Product或DevProduct对象
            file: 文件对象
            file_type: 'image' 或 'pdf'
            bucket_type: 'product' 或 'rd_product'

        Returns:
            str: 上传成功的文件URL，失败返回None
        """
        # 获取旧文件路径（用于清理）
        old_file_path = product.image_path if file_type == 'image' else getattr(product, 'pdf_path', None)

        # 清理旧文件
        if old_file_path:
            self.file_manager.delete_product_old_file(
                file_path=old_file_path,
                file_type=file_type,
                bucket_type=bucket_type
            )

        # 使用智能存储系统上传新文件（NAS 优先，Supabase 备份）
        from app.utils.smart_storage_manager import get_smart_product_storage
        smart_storage = get_smart_product_storage()

        return smart_storage.upload_product_file(
            product_id=product.id,
            file=file,
            file_type=file_type,
            bucket_type=bucket_type
        )

    def get_category_file_status_generic(self, product_id: int, product_type: str = 'standard') -> dict:
        """
        获取产品分类文件状态（通用方法）

        Args:
            product_id: 产品ID
            product_type: 'standard' 或 'research'

        Returns:
            dict: 分类文件状态
        """
        try:
            # 根据产品类型获取产品对象
            if product_type == 'research':
                product = DevProduct.query.get(product_id)
            else:
                product = Product.query.get(product_id)

            if not product:
                return {'success': False, 'error': '产品不存在'}

            # 获取子分类
            subcategory = ProductSubcategory.query.get(product.subcategory_id) if product.subcategory_id else None
            if not subcategory:
                return {'success': False, 'error': '产品没有关联子分类'}

            return {
                'success': True,
                'category_id': subcategory.id,
                'category_name': subcategory.name,
                'category_image': subcategory.image_path,
                'category_pdf': subcategory.pdf_path,
                'product_image': product.image_path,
                'product_pdf': getattr(product, 'pdf_path', None)
            }
        except Exception as e:
            logger.error(f"获取分类文件状态失败: {str(e)}")
            return {'success': False, 'error': str(e)}


# 创建全局服务实例
_product_file_service = None

def get_product_file_service() -> ProductFileService:
    """获取产品文件服务实例（单例模式）"""
    global _product_file_service
    if _product_file_service is None:
        _product_file_service = ProductFileService()
    return _product_file_service