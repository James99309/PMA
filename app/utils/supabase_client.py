import os
import logging
from io import BytesIO
from datetime import datetime
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
        """智能初始化存储客户端（本地/云端自动切换）"""
        try:
            # 检测运行环境
            self.is_local_env = self._detect_local_environment()
            self.use_local_storage = self._should_use_local_storage()
            
            if self.use_local_storage:
                logger.info("📁 使用本地文件存储系统")
                self._init_local_storage()
            else:
                logger.info("☁️ 使用云端Supabase存储系统")
                self._init_supabase_storage()
                
        except Exception as e:
            logger.error(f"存储客户端初始化失败: {str(e)}")
            # 降级到本地存储
            logger.warning("降级到本地文件存储")
            self._init_local_storage()
    
    def _detect_local_environment(self) -> bool:
        """检测是否为本地开发环境"""
        
        # 🔥 修复云端环境检测：检查所有可能的云端环境变量
        cloud_indicators = [
            os.getenv('RENDER_SERVICE_NAME'),  # Render环境
            os.getenv('RENDER'),
            os.getenv('RAILWAY'),
            os.getenv('VERCEL'),
            os.getenv('DYNO'),  # Heroku
            os.getenv('NETLIFY'),
            os.getenv('FIREBASE_PROJECT_ID'),  # Firebase
        ]
        
        # 如果检测到任何云端环境变量，就不是本地环境
        has_cloud_env = any(cloud_indicators)
        
        local_indicators = [
            os.getenv('FLASK_ENV') == 'development',
            'localhost' in os.getenv('SERVER_NAME', ''),
            '127.0.0.1' in os.getenv('SERVER_NAME', ''),
            os.path.exists('./run.py'),  # 本地开发文件存在
        ]
        
        local_count = sum(local_indicators)
        
        # 优先级：有云端环境变量就是云端，否则根据本地指标判断
        if has_cloud_env:
            is_local = False
            logger.info(f"🌐 检测到云端环境变量，判定为云端环境")
        else:
            is_local = local_count >= 2
            logger.info(f"🏠 未检测到云端环境变量，本地指标 {local_count}/4, 判定为: {'本地' if is_local else '云端'}")
            
        # 安全的云端环境变量显示
        try:
            env_names = ['RENDER_SERVICE_NAME', 'RENDER', 'RAILWAY', 'VERCEL', 'DYNO', 'NETLIFY', 'FIREBASE_PROJECT_ID']
            active_envs = [name for name, value in zip(env_names, cloud_indicators) if value]
            logger.info(f"环境检测结果: {'本地' if is_local else '云端'}, 活跃云端环境变量: {active_envs}")
        except Exception as e:
            logger.warning(f"环境变量显示失败: {e}")
        
        return is_local
    
    def _should_use_local_storage(self) -> bool:
        """决定是否使用本地存储"""
        # 强制云端存储的环境变量
        force_cloud = os.getenv('FORCE_CLOUD_UPLOAD', '').lower() in ['true', '1', 'yes']
        if force_cloud:
            logger.info("🚀 FORCE_CLOUD_UPLOAD=true, 强制使用云端存储")
            return False
            
        # 强制本地存储的环境变量
        force_local = os.getenv('FORCE_LOCAL_STORAGE', '').lower() in ['true', '1', 'yes']
        if force_local:
            logger.info("📁 FORCE_LOCAL_STORAGE=true, 强制使用本地存储")
            return True
        
        # 检查Supabase配置是否可用
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.info("📁 Supabase配置不完整，使用本地存储")
            return True
        
        # 本地环境默认使用本地存储，云端环境默认使用云端存储
        return self.is_local_env
    
    def _init_local_storage(self):
        """初始化本地文件存储"""
        self.use_local_storage = True
        self.supabase = None
        
        # 本地存储根目录
        self.local_storage_root = os.getenv('LOCAL_STORAGE_ROOT', './storage')
        
        # 本地存储桶映射（目录名）
        self.local_bucket_config = {
            'invoice': 'invoices',
            'product': 'products', 
            'rd_product': 'rd_products',
            'default': 'invoices'
        }
        
        # 确保本地存储目录存在
        for bucket_type, dir_name in self.local_bucket_config.items():
            local_dir = os.path.join(self.local_storage_root, dir_name)
            os.makedirs(local_dir, exist_ok=True)
            
        logger.info(f"📁 本地存储根目录: {self.local_storage_root}")
        logger.info(f"📂 本地桶映射: {self.local_bucket_config}")
    
    def _init_supabase_storage(self):
        """初始化Supabase云端存储"""
        self.use_local_storage = False
        
        # 从环境变量获取配置
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        # 云端存储桶配置
        self.bucket_config = {
            'invoice': os.getenv('SUPABASE_BUCKET_INVOICE', 'invoice-images'),
            'product': os.getenv('SUPABASE_BUCKET_PRODUCT', 'product-images'),
            'rd_product': os.getenv('SUPABASE_BUCKET_RD_PRODUCT', 'rd-product-images'),
            'default': os.getenv('SUPABASE_BUCKET', 'invoice-images')
        }
        
        # 检查必需的环境变量
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(f"缺少Supabase环境变量: SUPABASE_URL或SUPABASE_KEY")
            
        logger.info(f"☁️ Supabase URL: {self.supabase_url[:20]}...")
        logger.info(f"📦 云端桶配置: {self.bucket_config}")
        
        # 创建Supabase客户端
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        logger.info("✅ Supabase客户端初始化成功")
    
    def get_bucket_name(self, bucket_type: str = 'default') -> str:
        """
        根据类型获取存储桶名称或本地目录名
        
        Args:
            bucket_type: 存储桶类型 ('invoice', 'product', 'rd_product', 'default')
            
        Returns:
            存储桶名称（云端）或目录名（本地）
        """
        if self.use_local_storage:
            return self.local_bucket_config.get(bucket_type, self.local_bucket_config['default'])
        else:
            return self.bucket_config.get(bucket_type, self.bucket_config['default'])
    
    def upload_product_file(self, product_id: int, file, file_type: str, bucket_type: str = 'product') -> Optional[str]:
        """
        上传产品文件（支持本地/云端智能切换）
        
        Args:
            product_id: 产品ID
            file: 文件对象
            file_type: 文件类型 ('image' 或 'pdf')
            bucket_type: 存储桶类型 ('product', 'rd_product', 'invoice', 'default')
            
        Returns:
            上传成功返回访问URL，失败返回None
        """
        try:
            # 根据存储类型路由到对应的上传方法
            if self.use_local_storage:
                return self._upload_product_file_local(product_id, file, file_type, bucket_type)
            else:
                return self._upload_product_file_cloud(product_id, file, file_type, bucket_type)
            
        except Exception as e:
            logger.error(f"产品文件上传失败: {str(e)}")
            return None
    
    def _upload_product_file_local(self, product_id: int, file, file_type: str, bucket_type: str) -> Optional[str]:
        """
        上传产品文件到本地文件系统
        """
        try:
            # 验证文件类型
            if file_type not in ['image', 'pdf']:
                raise ValueError("文件类型必须是 'image' 或 'pdf'")
            
            # 验证文件扩展名
            original_filename = secure_filename(file.filename)
            if not original_filename:
                raise ValueError("无效的文件名")
                
            file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            
            if file_type == 'image':
                allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            else:  # pdf
                allowed_extensions = ['pdf']
            
            if file_ext not in allowed_extensions:
                raise ValueError(f"不支持的文件类型。{file_type}文件支持：{', '.join(allowed_extensions)}")
            
            # 验证文件大小
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > self.MAX_FILE_SIZE:
                raise ValueError(f"文件大小超过限制。最大允许: {self.MAX_FILE_SIZE // (1024*1024)}MB")
            
            if not file_size:
                raise ValueError("文件内容为空")
            
            # 生成标准化文件名和路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"product_{product_id}_{timestamp}.{file_ext}"
            
            # 获取对应的本地存储目录
            bucket_dir = self.get_bucket_name(bucket_type)
            storage_path = f"{bucket_dir}/product_{product_id}/{filename}"
            
            # 构建完整的本地文件路径
            local_file_path = os.path.join(self.local_storage_root, storage_path)
            local_dir = os.path.dirname(local_file_path)
            
            # 确保目录存在
            os.makedirs(local_dir, exist_ok=True)
            
            # 处理文件内容
            if file_type == 'image':
                try:
                    processed_content = self._process_image(file, file_ext)
                except Exception as e:
                    logger.warning(f"图片处理失败，使用原始文件: {str(e)}")
                    file.seek(0)
                    processed_content = file.read()
            else:
                file.seek(0)
                processed_content = file.read()
            
            # 保存到本地文件系统
            with open(local_file_path, 'wb') as f:
                f.write(processed_content)
            
            # 生成本地访问URL
            local_url = f"/storage/{storage_path}"
            
            logger.info(f"✅ 产品文件保存到本地: {local_file_path}")
            logger.info(f"🔗 本地访问URL: {local_url}")
            
            return local_url
            
        except Exception as e:
            logger.error(f"本地产品文件上传失败: {str(e)}")
            return None
    
    def _upload_product_file_cloud(self, product_id: int, file, file_type: str, bucket_type: str) -> Optional[str]:
        """
        上传产品文件到云端Supabase存储
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
    
    def upload_expense_invoice(self, detail_id: int, file, filename: str, bucket_type: str = 'invoice', detail_sequence: int = None):
        """
        上传报销明细发票图片（本地/云端自适应）
        
        Args:
            detail_id: 报销明细ID
            file: 文件对象
            filename: 原始文件名
            bucket_type: 存储桶类型 ('invoice', 'product', 'rd_product', 'default')
            detail_sequence: 明细序号（可选，用于新建报销单时避免序号冲突）
            
        Returns:
            成功返回文件信息字典或URL字符串（向下兼容），失败返回None
            文件信息字典格式:
            {
                'url': '访问URL',
                'filename': '规范化文件名',
                'storage_path': '存储路径',
                'original_filename': '原始文件名',
                'standardized': True/False
            }
        """
        try:
            if self.use_local_storage:
                return self._upload_expense_invoice_local(detail_id, file, filename, bucket_type, detail_sequence)
            else:
                return self._upload_expense_invoice_cloud(detail_id, file, filename, bucket_type, detail_sequence)
        except Exception as e:
            logger.error(f"发票上传失败: {str(e)}")
            return None
    
    def _upload_expense_invoice_local(self, detail_id: int, file, filename: str, bucket_type: str, detail_sequence: int = None) -> Optional[str]:
        """
        上传发票到本地文件系统
        """
        try:
            # 获取本地目录名
            local_dir_name = self.get_bucket_name(bucket_type)
            
            # 生成规范化的文件名和存储路径
            standardized_info = self._generate_standardized_invoice_name(detail_id, filename, detail_sequence)
            if not standardized_info:
                logger.warning(f"生成规范化文件名失败，使用简化命名")
                # 简化的本地存储路径
                local_subdir = os.path.join(self.local_storage_root, local_dir_name, f"expense_{detail_id}")
                os.makedirs(local_subdir, exist_ok=True)
                
                # 生成唯一文件名避免冲突
                import uuid
                name, ext = os.path.splitext(filename)
                safe_filename = f"invoice_{detail_id}_{uuid.uuid4().hex[:8]}{ext}"
                local_file_path = os.path.join(local_subdir, safe_filename)
                storage_path = f"{local_dir_name}/expense_{detail_id}/{safe_filename}"
            else:
                # 使用规范化路径
                storage_path = standardized_info['storage_path']
                local_file_path = os.path.join(self.local_storage_root, storage_path)
                safe_filename = standardized_info['filename']
                
                # 确保目录存在
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
            logger.info(f"📁 本地存储路径: {local_file_path}")
            
            # 处理并保存图片文件
            file_content = file.read()
            file.seek(0)
            
            try:
                # 处理图片（压缩等）
                processed_content = self._process_invoice_image(file_content, filename)
            except Exception as e:
                logger.warning(f"图片处理失败，使用原始文件: {str(e)}")
                processed_content = file_content
            
            # 保存到本地文件
            with open(local_file_path, 'wb') as f:
                f.write(processed_content)
            
            # 生成本地访问URL（相对于应用根目录）
            local_url = f"/storage/{storage_path}"
            
            logger.info(f"✅ 发票保存到本地: {local_file_path}")
            logger.info(f"🔗 本地访问URL: {local_url}")
            
            # 返回详细的文件信息
            return {
                'url': local_url,
                'filename': safe_filename,
                'storage_path': storage_path,
                'original_filename': filename,
                'standardized': standardized_info is not None
            }
            
        except Exception as e:
            logger.error(f"本地发票上传失败: {str(e)}")
            return None
    
    def _upload_expense_invoice_cloud(self, detail_id: int, file, filename: str, bucket_type: str, detail_sequence: int = None) -> Optional[str]:
        """
        上传发票到云端Supabase存储
        """
        try:
            # 获取对应的存储桶名称
            bucket_name = self.get_bucket_name(bucket_type)
            
            # 生成规范化的文件名和存储路径
            standardized_info = self._generate_standardized_invoice_name(detail_id, filename, detail_sequence)
            if not standardized_info:
                logger.error(f"生成规范化文件名失败，使用原始命名: {filename}")
                storage_path = f"expense_invoices/{detail_id}/{filename}"
            else:
                storage_path = standardized_info['storage_path']
                standardized_filename = standardized_info['filename']
                logger.info(f"生成规范化文件名: {standardized_filename}")
                logger.info(f"☁️ 云端存储路径: {storage_path}")
            
            # 读取并处理图片文件
            file_content = file.read()
            file.seek(0)  # 重置文件指针
            
            # 压缩图片以节省存储空间和带宽
            try:
                processed_content = self._process_invoice_image(file_content, filename)
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
                        # 根据原始文件扩展名设置Content-Type
                        original_ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
                        options = UploadFileOptions(
                            content_type=self._get_content_type('image', original_ext)
                        )
                        res = self.supabase.storage.from_(bucket_name).upload(
                            storage_path,
                            processed_content
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
                            processed_content
                        )
                        upload_success = True
                        logger.info("字典方式上传成功")
                    except Exception as e:
                        logger.warning(f"字典方式失败: {e}")
                
                if not upload_success:
                    try:
                        # 最简化版本，使用新版SDK格式
                        logger.info("尝试使用最简化方式上传")
                        res = self.supabase.storage.from_(bucket_name).upload(
                            storage_path,
                            processed_content  # 直接使用字节内容而不是BytesIO
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
            
            # 返回详细的文件信息
            if standardized_info:
                return {
                    'url': public_url,
                    'filename': standardized_info['filename'],
                    'storage_path': storage_path,
                    'original_filename': filename,
                    'standardized': True
                }
            else:
                return {
                    'url': public_url,
                    'filename': filename,
                    'storage_path': storage_path,
                    'original_filename': filename,
                    'standardized': False
                }
            
        except Exception as e:
            logger.error(f"发票图片上传失败: {str(e)}")
            return None
    
    def delete_expense_invoice(self, filename: str, bucket_type: str = 'invoice') -> bool:
        """
        删除报销明细发票图片（支持新旧命名格式）
        
        Args:
            filename: 文件名或完整URL
            bucket_type: 存储桶类型 ('invoice', 'product', 'rd_product', 'default')
            
        Returns:
            删除成功返回True，失败返回False
        """
        try:
            # 获取对应的存储桶名称
            bucket_name = self.get_bucket_name(bucket_type)
            
            storage_paths = []
            
            # 如果是完整URL，提取路径
            if filename.startswith('http'):
                try:
                    from urllib.parse import urlparse
                    parsed_url = urlparse(filename)
                    path_parts = parsed_url.path.split('/')
                    if len(path_parts) > 6:  # /storage/v1/object/public/bucket/...
                        storage_paths.append('/'.join(path_parts[6:]))
                except Exception as e:
                    logger.warning(f"解析URL失败: {e}")
            
            # 新格式：规范化命名（项目_报销单_明细_文件.ext）
            if '_' in filename and filename.count('_') >= 3:
                # 尝试解析规范化文件名 PMA_BX2025081015_01_01.heic
                try:
                    parts = filename.split('_')
                    if len(parts) >= 4:
                        system_id = parts[0]  # PMA
                        expense_number = parts[1]  # BX2025081015
                        # 新格式存储路径
                        storage_paths.append(f"invoice_files/{system_id}/{expense_number}/{filename}")
                        logger.debug(f"生成新格式删除路径: invoice_files/{system_id}/{expense_number}/{filename}")
                except Exception as e:
                    logger.debug(f"解析规范化文件名失败: {e}")
            
            # 旧格式：传统命名（expense_invoice_{detail_id}_{uuid}.ext）
            if filename.startswith('expense_invoice_'):
                parts = filename.split('_')
                if len(parts) >= 3:
                    try:
                        detail_id = parts[2].split('.')[0] if '.' in parts[2] else parts[2]  # 移除文件扩展名
                        if detail_id.isdigit():
                            storage_paths.append(f"expense_invoices/{detail_id}/{filename}")
                    except Exception as e:
                        logger.debug(f"解析传统文件名失败: {e}")
            
            # 如果没有匹配的路径，尝试常见路径
            if not storage_paths:
                storage_paths = [
                    f"expense_invoices/{filename}",  # 直接在expense_invoices目录
                    filename  # 根目录
                ]
            
            # 尝试删除所有可能的路径
            deleted = False
            for storage_path in storage_paths:
                try:
                    logger.info(f"尝试删除路径: {storage_path}")
                    result = self.supabase.storage.from_(bucket_name).remove([storage_path])
                    
                    # 🔍 详细日志：查看删除结果
                    logger.info(f"删除API响应: {result}")
                    logger.info(f"响应类型: {type(result)}")
                    if hasattr(result, 'data'):
                        logger.info(f"响应数据: {result.data}")
                    if hasattr(result, 'error'):
                        logger.info(f"响应错误: {result.error}")
                    
                    if not (hasattr(result, 'error') and result.error):
                        logger.info(f"发票图片删除成功: {storage_path}")
                        deleted = True
                        break  # 成功删除一个路径就够了
                    else:
                        logger.debug(f"删除路径失败: {storage_path} - {result.error}")
                        
                except Exception as e:
                    logger.debug(f"删除路径异常: {storage_path} - {str(e)}")
                    continue
            
            return deleted
            
        except Exception as e:
            logger.error(f"发票图片删除失败: {str(e)}")
            return False
    
    def _process_invoice_image(self, file_content: bytes, filename: str = '') -> bytes:
        """
        处理发票图片：压缩和调整大小，保留原始格式
        """
        try:
            # 获取文件扩展名来预判格式
            file_ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
            
            # 🔥 HEIC/HEIF格式特殊处理：PIL可能无法识别，但我们仍需要保存
            if file_ext in ['heic', 'heif']:
                try:
                    # 尝试用PIL打开HEIC文件
                    image = Image.open(BytesIO(file_content))
                    original_format = image.format or 'HEIC'
                    logger.info(f"成功识别HEIC格式文件")
                except Exception as heic_error:
                    # PIL无法识别HEIC时，直接返回原始文件内容
                    logger.warning(f"PIL无法处理HEIC文件，保留原始文件内容: {heic_error}")
                    return file_content
            else:
                # 其他格式正常处理
                image = Image.open(BytesIO(file_content))
                original_format = image.format or 'JPEG'
            
            # 调整大小（发票图片最大1600x1600）
            max_size = 1600
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                logger.info(f"图片大小调整为: {image.width}x{image.height}")
            
            # 保持原始格式，只做压缩处理
            output = BytesIO()
            
            # 根据文件扩展名确定保存格式
            if file_ext in ['png']:
                # PNG格式：保持透明度
                image.save(output, format='PNG', optimize=True)
                logger.info(f"PNG文件保持原始格式")
            elif file_ext in ['gif']:
                # GIF格式：保持调色板  
                image.save(output, format='GIF', optimize=True)
                logger.info(f"GIF文件保持原始格式")
            elif file_ext in ['webp']:
                # WEBP格式：保持原始格式
                image.save(output, format='WEBP', quality=90, optimize=True)
                logger.info(f"WEBP文件保持原始格式")
            elif file_ext in ['bmp']:
                # BMP格式：保持原始格式
                image.save(output, format='BMP')
                logger.info(f"BMP文件保持原始格式")
            elif file_ext in ['heic', 'heif']:
                # HEIC/HEIF格式：由于PIL支持有限，转换为JPEG内容但保持扩展名
                if image.mode not in ('RGB', 'L'):
                    image = image.convert('RGB')
                image.save(output, format='JPEG', quality=90, optimize=True)
                logger.info(f"HEIC/HEIF文件内容处理为JPEG但保持原始扩展名")
            else:
                # JPG/JPEG和其他格式：保存为JPEG
                if image.mode not in ('RGB', 'L'):
                    image = image.convert('RGB')
                image.save(output, format='JPEG', quality=90, optimize=True)
                logger.info(f"文件处理为JPEG格式")
            
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
    
    def _generate_standardized_invoice_name(self, detail_id: int, original_filename: str, detail_sequence: int = None) -> Optional[dict]:
        """
        生成规范化的发票文件名和存储路径
        
        命名规范: {项目代码}-{客户简称}-{报销单号}-{明细序号}-{文件序号}.{扩展名}
        存储路径: invoice_files/{项目代码}/{客户简称}/{报销单号}/{文件名}
        
        Args:
            detail_id: 报销明细ID
            original_filename: 原始文件名
            
        Returns:
            dict: 包含filename和storage_path的字典，失败返回None
        """
        try:
            from app.models.expense import ExpenseDetail, Expense
            from app.models.customer import Company
            from app.models.project import Project
            
            # 获取报销明细信息
            detail = ExpenseDetail.query.get(detail_id)
            if not detail or not detail.expense:
                logger.error(f"未找到报销明细或报销单: detail_id={detail_id}")
                return None
            
            expense = detail.expense
            
            # 保留原始文件扩展名
            file_ext = 'jpg'  # 默认扩展名
            if '.' in original_filename:
                file_ext = original_filename.rsplit('.', 1)[1].lower()
            
            # 1. 系统标识
            system_id = self._get_system_identifier()
            
            # 2. 报销单编号
            logger.info(f"🔍 调试文件名生成: 原始报销单编号={expense.expense_number}")
            expense_number = self._clean_filename_part(expense.expense_number)
            logger.info(f"🔍 调试文件名生成: 清理后报销单编号={expense_number}")
            
            # 3. 明细序号（在该报销单中的位置，2位数）
            if detail_sequence is None:
                detail_sequence = self._get_detail_sequence(expense, detail_id)
            else:
                # 使用传递的序号（从0开始转换为从1开始）
                detail_sequence = detail_sequence + 1
            
            # 4. 文件序号（该明细的第几个文件，2位数）
            file_sequence = self._get_file_sequence_for_detail(detail_id)
            
            # 生成规范化文件名
            # 格式: PMA-SA_BX20250810_01_02.jpg
            standardized_filename = f"{system_id}_{expense_number}_{detail_sequence:02d}_{file_sequence:02d}.{file_ext}"
            
            # 生成存储路径
            # 格式: invoice_files/PMA-SA/BX20250810/PMA-SA_BX20250810_01_02.jpg
            storage_path = f"invoice_files/{system_id}/{expense_number}/{standardized_filename}"
            
            return {
                'filename': standardized_filename,
                'storage_path': storage_path,
                'system_id': system_id,
                'expense_number': expense_number,
                'detail_sequence': detail_sequence,
                'file_sequence': file_sequence
            }
            
        except Exception as e:
            logger.error(f"生成规范化文件名失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return None
    
    def _get_system_identifier(self) -> str:
        """
        获取系统标识
        
        Returns:
            系统标识字符串 (PMA-SA, PMA, LOCAL-PMA)
        """
        # 检查是否为云端部署
        if not self.is_local_env:
            # 云端环境，根据Supabase URL判断是PMA还是PMA-SA
            supabase_url = os.getenv('SUPABASE_URL', '')
            if 'pqzviljbpfoqvyfulakl' in supabase_url:  # PMA-SA项目URL标识
                return 'PMA-SA'
            else:
                return 'PMA'  # 默认云端PMA项目
        else:
            # 本地环境
            return 'LOCAL-PMA'
    
    def _clean_filename_part(self, text: str) -> str:
        """
        清理文件名部分，移除不安全字符
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return "UNKNOWN"
        
        # 移除或替换不安全字符
        import re
        # 保留字母、数字、中文字符
        cleaned = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
        
        # 如果清理后为空，返回默认值
        if not cleaned:
            return "UNKNOWN"
        
        # 保持完整长度，但限制合理范围（报销单编号通常不会超过20个字符）
        return cleaned[:20].upper()
    
    def _get_detail_sequence(self, expense, detail_id: int) -> int:
        """
        获取明细在报销单中的序号
        
        Args:
            expense: 报销单对象
            detail_id: 明细ID
            
        Returns:
            序号（从1开始）
        """
        try:
            # 按创建时间排序，获取序号
            sorted_details = sorted(expense.details, key=lambda d: d.created_at or d.id)
            for i, detail in enumerate(sorted_details):
                if detail.id == detail_id:
                    return i + 1
            return 1  # 默认返回1
        except Exception as e:
            logger.error(f"获取明细序号失败: {str(e)}")
            return 1
    
    def _get_file_sequence_for_detail(self, detail_id: int) -> int:
        """
        获取该明细当前应该使用的文件序号
        
        Args:
            detail_id: 明细ID
            
        Returns:
            文件序号（从1开始）
        """
        try:
            from app.models.expense import ExpenseDetail
            
            detail = ExpenseDetail.query.get(detail_id)
            if not detail:
                return 1
            
            # 解析现有的发票图片数量
            existing_images = detail.invoice_images_list
            return len(existing_images) + 1
            
        except Exception as e:
            logger.error(f"获取文件序号失败: {str(e)}")
            return 1

# 全局Supabase客户端实例
_supabase_client = None

def get_supabase_client() -> SupabaseStorageClient:
    """获取Supabase客户端单例"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseStorageClient()
    return _supabase_client