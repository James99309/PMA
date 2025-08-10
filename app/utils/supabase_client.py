import os
import logging
from io import BytesIO
from PIL import Image
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from typing import Optional, Tuple

# 尝试导入UploadFileOptions，如果不存在则创建兼容的替代
try:
    from supabase.storage.types import UploadFileOptions
    HAS_UPLOAD_FILE_OPTIONS = True
except ImportError:
    # 对于旧版本SDK，创建一个简单的替代类
    class UploadFileOptions:
        def __init__(self, content_type: str, **kwargs):
            self.content_type = content_type
            self.__dict__.update(kwargs)
    HAS_UPLOAD_FILE_OPTIONS = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseStorageClient:
    """Supabase 存储客户端工具类"""
    
    # 配置常量
    MAX_FILE_SIZE = 12 * 1024 * 1024  # 12MB
    MAX_IMAGE_WIDTH = 1200  # 最大图片宽度
    MAX_IMAGE_HEIGHT = 1200  # 最大图片高度
    IMAGE_QUALITY = 85  # JPEG压缩质量
    
    def __init__(self):
        """使用官方推荐的方式初始化Supabase客户端"""
        try:
            # 从环境变量获取配置
            self.supabase_url = os.getenv('SUPABASE_URL')
            self.supabase_key = os.getenv('SUPABASE_KEY')
            
            # 多存储桶配置
            self.bucket_config = {
                'invoice': os.getenv('SUPABASE_BUCKET_INVOICE', 'invoice-images'),
                'product': os.getenv('SUPABASE_BUCKET_PRODUCT', 'product-images'),
                'rd_product': os.getenv('SUPABASE_BUCKET_RD_PRODUCT', 'rd-product-images'),
                'default': os.getenv('SUPABASE_BUCKET', 'invoice-images')  # 向后兼容
            }
            
            # 检查必需的环境变量
            if not self.supabase_url or not self.supabase_key:
                missing_vars = []
                if not self.supabase_url:
                    missing_vars.append('SUPABASE_URL')
                if not self.supabase_key:
                    missing_vars.append('SUPABASE_KEY')
                raise ValueError(f"缺少必需的Supabase环境变量: {', '.join(missing_vars)}")
                
            logger.info(f"Supabase配置: URL={self.supabase_url[:20]}...")
            logger.info(f"存储桶配置: {self.bucket_config}")
            
            # 使用官方推荐的create_client方法
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase客户端初始化成功")
            
        except Exception as e:
            logger.error(f"Supabase客户端初始化失败: {str(e)}")
            raise
    
    def get_bucket_name(self, bucket_type: str = 'default') -> str:
        """
        根据类型获取存储桶名称
        
        Args:
            bucket_type: 存储桶类型 ('invoice', 'product', 'rd_product', 'default')
            
        Returns:
            存储桶名称
        """
        return self.bucket_config.get(bucket_type, self.bucket_config['default'])
    
    def upload_product_file(self, product_id: int, file, file_type: str, bucket_type: str = 'product') -> Optional[str]:
        """
        上传产品文件到Supabase存储
        
        Args:
            product_id: 产品ID
            file: 文件对象
            file_type: 文件类型 ('image' 或 'pdf')
            bucket_type: 存储桶类型 ('product', 'rd_product', 'invoice', 'default')
            
        Returns:
            上传成功返回公开URL，失败返回None
        """
        try:
            # 获取对应的存储桶名称
            bucket_name = self.get_bucket_name(bucket_type)
            
            # 验证文件类型
            if file_type not in ['image', 'pdf']:
                raise ValueError("文件类型必须是 'image' 或 'pdf'")
            
            # 生成文件名
            if file_type == 'image':
                filename = f"product_{product_id}.jpg"
                allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            else:  # pdf
                filename = f"product_{product_id}.pdf"
                allowed_extensions = ['pdf']
            
            # 验证文件扩展名
            original_filename = secure_filename(file.filename)
            if not original_filename:
                raise ValueError("无效的文件名")
                
            file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            if file_ext not in allowed_extensions:
                raise ValueError(f"不支持的文件类型。{file_type}文件支持：{', '.join(allowed_extensions)}")
            
            # 验证文件大小
            file.seek(0, 2)  # 移动到文件末尾
            file_size = file.tell()
            file.seek(0)  # 重置到开头
            
            if file_size > self.MAX_FILE_SIZE:
                raise ValueError(f"文件大小超过限制。最大允许: {self.MAX_FILE_SIZE // (1024*1024)}MB")
            
            if not file_size:
                raise ValueError("文件内容为空")
            
            # 处理文件内容
            if file_type == 'image':
                file_content = self._process_image(file, file_ext)
            else:
                file.seek(0)
                file_content = file.read()
            
            # 使用版本兼容的上传方法
            try:
                # 将文件内容包装为BytesIO对象
                file_bytes = BytesIO(file_content)
                
                # 调试信息
                logger.info(f"HAS_UPLOAD_FILE_OPTIONS: {HAS_UPLOAD_FILE_OPTIONS}")
                
                # 使用多层容错机制
                upload_success = False
                
                if HAS_UPLOAD_FILE_OPTIONS:
                    try:
                        # 新版本SDK使用UploadFileOptions
                        logger.info("尝试使用UploadFileOptions方式上传")
                        options = UploadFileOptions(content_type=self._get_content_type(file_type, file_ext))
                        res = self.supabase.storage.from_(bucket_name).upload(
                            filename,
                            file_bytes,
                            options
                        )
                        upload_success = True
                        logger.info("UploadFileOptions方式上传成功")
                    except Exception as e:
                        logger.warning(f"UploadFileOptions方式失败: {e}")
                
                if not upload_success:
                    try:
                        # 尝试字典方式
                        logger.info("尝试使用字典方式上传")
                        res = self.supabase.storage.from_(bucket_name).upload(
                            filename,
                            file_bytes,
                            {"content-type": self._get_content_type(file_type, file_ext)}
                        )
                        upload_success = True
                        logger.info("字典方式上传成功")
                    except Exception as e:
                        logger.warning(f"字典方式失败: {e}")
                
                if not upload_success:
                    try:
                        # 最简化版本，不传递content-type
                        logger.info("尝试使用最简化方式上传")
                        res = self.supabase.storage.from_(bucket_name).upload(
                            filename,
                            file_bytes
                        )
                        upload_success = True
                        logger.info("最简化方式上传成功")
                    except Exception as e:
                        logger.warning(f"最简化方式失败: {e}")
                
                # 如果所有SDK方法都失败，使用HTTP API作为最后的备用方案
                if not upload_success:
                    try:
                        logger.info("所有SDK方法失败，尝试使用HTTP API直接上传")
                        import requests
                        
                        # 重置BytesIO位置
                        file_bytes.seek(0)
                        
                        # 构建上传URL
                        upload_url = f"{self.supabase_url}/storage/v1/object/{bucket_name}/{filename}"
                        
                        # 设置请求头
                        headers = {
                            'Authorization': f'Bearer {self.supabase_key}',
                            'Content-Type': self._get_content_type(file_type, file_ext),
                            'x-upsert': 'true'  # 允许覆盖文件
                        }
                        
                        # 发送POST请求上传文件
                        response = requests.post(
                            upload_url,
                            data=file_bytes.read(),
                            headers=headers,
                            timeout=30
                        )
                        
                        if response.status_code in [200, 201]:
                            logger.info("HTTP API方式上传成功")
                            upload_success = True
                            # 创建一个模拟的成功响应
                            res = {"error": None}
                        else:
                            raise Exception(f"HTTP上传失败: {response.status_code} - {response.text}")
                            
                    except Exception as e:
                        logger.error(f"HTTP API方式也失败: {e}")
                        raise e
                
                if not upload_success:
                    raise Exception("所有上传方法都失败了")
                
                # 检查上传结果
                if res and hasattr(res, 'get') and res.get("error"):
                    raise Exception("Upload failed: " + res["error"]["message"])
                
                logger.info(f"Supabase上传成功: {filename}")
                
            except Exception as upload_error:
                logger.error(f"Supabase上传失败: {upload_error}")
                raise upload_error
            
            # 构建公开URL
            public_url = f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{filename}"
            logger.info(f"文件上传成功: {filename} -> {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return None
    
    def _process_image(self, file, file_ext: str) -> bytes:
        """
        处理图片：压缩、缩放、优化
        
        Args:
            file: 文件对象
            file_ext: 文件扩展名
            
        Returns:
            处理后的图片字节数据
        """
        try:
            # 读取图片
            file.seek(0)
            image = Image.open(file)
            
            # 获取原始尺寸
            original_width, original_height = image.size
            logger.info(f"原始图片尺寸: {original_width}x{original_height}")
            
            # 转换为RGB模式（确保JPEG兼容性）
            if image.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 计算缩放尺寸（保持宽高比，确保完整显示）
            if original_width > self.MAX_IMAGE_WIDTH or original_height > self.MAX_IMAGE_HEIGHT:
                # 计算缩放比例，使用较小的比例确保图片完整显示在限制范围内
                width_ratio = self.MAX_IMAGE_WIDTH / original_width
                height_ratio = self.MAX_IMAGE_HEIGHT / original_height
                scale_ratio = min(width_ratio, height_ratio)  # 使用较小的比例保持宽高比
                
                new_width = int(original_width * scale_ratio)
                new_height = int(original_height * scale_ratio)
                
                logger.info(f"缩放计算: 原始({original_width}x{original_height}) -> 目标({new_width}x{new_height}), 比例: {scale_ratio:.3f}")
                
                # 高质量缩放 - 确保不裁切
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"图片已等比缩放至: {new_width}x{new_height}")
            else:
                logger.info(f"图片尺寸在限制范围内，无需缩放: {original_width}x{original_height}")
            
            # 保存为JPEG格式（统一格式，优化大小）
            output_buffer = BytesIO()
            
            # 根据原始格式决定输出格式
            if file_ext.lower() in ['png', 'gif'] and original_width * original_height > 500000:
                # 大图片转为JPEG以减小文件大小
                image.save(output_buffer, format='JPEG', quality=self.IMAGE_QUALITY, optimize=True)
                logger.info("图片已转换为JPEG格式以优化大小")
            elif file_ext.lower() == 'png':
                # 小PNG保持原格式
                image.save(output_buffer, format='PNG', optimize=True)
            else:
                # 其他格式转为JPEG
                image.save(output_buffer, format='JPEG', quality=self.IMAGE_QUALITY, optimize=True)
            
            # 获取处理后的文件大小
            processed_size = output_buffer.tell()
            logger.info(f"处理后文件大小: {processed_size // 1024}KB")
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"图片处理失败: {str(e)}")
            # 处理失败时返回原始文件
            file.seek(0)
            return file.read()
    
    def _get_content_type(self, file_type: str, file_ext: str) -> str:
        """获取文件的Content-Type"""
        if file_type == 'image':
            content_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg', 
                'png': 'image/png',
                'gif': 'image/gif'
            }
            return content_types.get(file_ext, 'image/jpeg')
        else:  # pdf
            return 'application/pdf'
    
    def delete_product_file(self, product_id: int, file_type: str, bucket_type: str = 'product') -> bool:
        """
        删除产品文件
        
        Args:
            product_id: 产品ID
            file_type: 文件类型 ('image' 或 'pdf')
            bucket_type: 存储桶类型 ('product', 'rd_product', 'invoice', 'default')
            
        Returns:
            删除成功返回True，失败返回False
        """
        try:
            # 获取对应的存储桶名称
            bucket_name = self.get_bucket_name(bucket_type)
            
            # 生成文件名
            if file_type == 'image':
                filename = f"product_{product_id}.jpg"
            elif file_type == 'pdf':
                filename = f"product_{product_id}.pdf"
            else:
                raise ValueError("文件类型必须是 'image' 或 'pdf'")
            
            # 删除文件
            result = self.supabase.storage.from_(bucket_name).remove([filename])
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Supabase删除错误: {result.error}")
                return False
            
            logger.info(f"文件删除成功: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return False
    
    def upload_expense_invoice(self, detail_id: int, file, filename: str, bucket_type: str = 'invoice') -> Optional[str]:
        """
        上传报销明细发票图片到Supabase存储
        
        Args:
            detail_id: 报销明细ID
            file: 文件对象
            filename: 文件名
            bucket_type: 存储桶类型 ('invoice', 'product', 'rd_product', 'default')
            
        Returns:
            成功返回公开URL，失败返回None
        """
        try:
            # 获取对应的存储桶名称
            bucket_name = self.get_bucket_name(bucket_type)
            
            # 生成存储路径
            storage_path = f"expense_invoices/{detail_id}/{filename}"
            
            # 读取并处理图片文件
            file_content = file.read()
            file.seek(0)  # 重置文件指针
            
            # 压缩图片以节省存储空间和带宽
            try:
                processed_content = self._process_invoice_image(file_content)
            except Exception as e:
                logger.warning(f"图片处理失败，使用原始文件: {str(e)}")
                processed_content = file_content
            
            # 使用版本兼容的上传方法
            try:
                # 将处理后的文件内容包装为BytesIO对象
                file_bytes = BytesIO(processed_content)
                
                # 调试信息
                logger.info(f"HAS_UPLOAD_FILE_OPTIONS: {HAS_UPLOAD_FILE_OPTIONS}")
                
                # 使用多层容错机制
                upload_success = False
                
                if HAS_UPLOAD_FILE_OPTIONS:
                    try:
                        # 新版本SDK使用UploadFileOptions
                        logger.info("尝试使用UploadFileOptions方式上传")
                        options = UploadFileOptions(
                            content_type=self._get_content_type('image', filename.split('.')[-1].lower() if '.' in filename else 'jpg')
                        )
                        res = self.supabase.storage.from_(bucket_name).upload(
                            storage_path,
                            file_bytes,
                            options
                        )
                        upload_success = True
                        logger.info("UploadFileOptions方式上传成功")
                    except Exception as e:
                        logger.warning(f"UploadFileOptions方式失败: {e}")
                
                if not upload_success:
                    try:
                        # 尝试字典方式
                        logger.info("尝试使用字典方式上传")
                        res = self.supabase.storage.from_(bucket_name).upload(
                            storage_path,
                            file_bytes,
                            {"content-type": self._get_content_type('image', filename.split('.')[-1].lower() if '.' in filename else 'jpg')}
                        )
                        upload_success = True
                        logger.info("字典方式上传成功")
                    except Exception as e:
                        logger.warning(f"字典方式失败: {e}")
                
                if not upload_success:
                    try:
                        # 最简化版本，不传递content-type
                        logger.info("尝试使用最简化方式上传")
                        res = self.supabase.storage.from_(bucket_name).upload(
                            storage_path,
                            file_bytes
                        )
                        upload_success = True
                        logger.info("最简化方式上传成功")
                    except Exception as e:
                        logger.warning(f"最简化方式失败: {e}")
                
                # 如果所有SDK方法都失败，使用HTTP API作为最后的备用方案
                if not upload_success:
                    try:
                        logger.info("所有SDK方法失败，尝试使用HTTP API直接上传")
                        import requests
                        
                        # 重置BytesIO位置
                        file_bytes.seek(0)
                        
                        # 构建上传URL
                        upload_url = f"{self.supabase_url}/storage/v1/object/{bucket_name}/{storage_path}"
                        
                        # 设置请求头
                        headers = {
                            'Authorization': f'Bearer {self.supabase_key}',
                            'Content-Type': self._get_content_type('image', filename.split('.')[-1].lower() if '.' in filename else 'jpg'),
                            'x-upsert': 'true'  # 允许覆盖文件
                        }
                        
                        # 发送POST请求上传文件
                        response = requests.post(
                            upload_url,
                            data=file_bytes.read(),
                            headers=headers,
                            timeout=30
                        )
                        
                        if response.status_code in [200, 201]:
                            logger.info("HTTP API方式上传成功")
                            upload_success = True
                            # 创建一个模拟的成功响应
                            res = {"error": None}
                        else:
                            raise Exception(f"HTTP上传失败: {response.status_code} - {response.text}")
                            
                    except Exception as e:
                        logger.error(f"HTTP API方式也失败: {e}")
                        raise e
                
                if not upload_success:
                    raise Exception("所有上传方法都失败了")
                
                # 检查上传结果
                if res and hasattr(res, 'get') and res.get("error"):
                    raise Exception("Upload failed: " + res["error"]["message"])
                
                logger.info(f"Supabase发票上传成功: {storage_path}")
                
            except Exception as upload_error:
                logger.error(f"Supabase发票上传失败: {upload_error}")
                raise upload_error
            
            # 构建公开URL
            public_url = f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
            
            logger.info(f"发票图片上传成功: {storage_path}")
            return public_url
            
        except Exception as e:
            logger.error(f"发票图片上传失败: {str(e)}")
            return None
    
    def delete_expense_invoice(self, filename: str, bucket_type: str = 'invoice') -> bool:
        """
        删除报销明细发票图片
        
        Args:
            filename: 文件名
            bucket_type: 存储桶类型 ('invoice', 'product', 'rd_product', 'default')
            
        Returns:
            删除成功返回True，失败返回False
        """
        try:
            # 获取对应的存储桶名称
            bucket_name = self.get_bucket_name(bucket_type)
            
            # 构建存储路径
            # 从filename中提取detail_id（假设filename格式为：expense_invoice_{detail_id}_{uuid}.ext）
            parts = filename.split('_')
            if len(parts) >= 3 and parts[0] == 'expense' and parts[1] == 'invoice':
                detail_id = parts[2]
                storage_path = f"expense_invoices/{detail_id}/{filename}"
            else:
                # 备选方案：直接使用filename作为路径
                storage_path = f"expense_invoices/{filename}"
            
            # 删除文件
            result = self.supabase.storage.from_(bucket_name).remove([storage_path])
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Supabase删除错误: {result.error}")
                return False
            
            logger.info(f"发票图片删除成功: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"发票图片删除失败: {str(e)}")
            return False
    
    def _process_invoice_image(self, file_content: bytes) -> bytes:
        """
        处理发票图片：压缩和调整大小
        """
        try:
            # 打开图片
            image = Image.open(BytesIO(file_content))
            
            # 转换为RGB模式（如果需要）
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # 调整大小（发票图片最大1600x1600）
            max_size = 1600
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                logger.info(f"图片大小调整为: {image.width}x{image.height}")
            
            # 压缩并保存
            output = BytesIO()
            image.save(output, format='JPEG', quality=90, optimize=True)
            compressed_content = output.getvalue()
            
            # 检查压缩效果
            original_size = len(file_content)
            compressed_size = len(compressed_content)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            logger.info(f"图片压缩: {original_size} bytes -> {compressed_size} bytes (压缩率: {compression_ratio:.1f}%)")
            
            return compressed_content
            
        except Exception as e:
            logger.error(f"图片处理失败: {str(e)}")
            raise

# 全局Supabase客户端实例
_supabase_client = None

def get_supabase_client() -> SupabaseStorageClient:
    """获取Supabase客户端单例"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseStorageClient()
    return _supabase_client