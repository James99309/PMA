import os
import logging
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from typing import Optional, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseStorageClient:
    """Supabase 存储客户端工具类"""
    
    def __init__(self):
        """初始化Supabase客户端，从环境变量获取配置"""
        try:
            # 从Render环境变量获取配置
            self.supabase_url = os.getenv('SUPABASE_URL')
            self.supabase_key = os.getenv('SUPABASE_KEY') 
            self.bucket_name = os.getenv('SUPABASE_BUCKET')
            
            if not all([self.supabase_url, self.supabase_key, self.bucket_name]):
                raise ValueError("缺少必需的Supabase环境变量：SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET")
            
            # 创建Supabase客户端
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase客户端初始化成功")
            
        except Exception as e:
            logger.error(f"Supabase客户端初始化失败: {str(e)}")
            raise
    
    def upload_product_file(self, product_id: int, file, file_type: str) -> Optional[str]:
        """
        上传产品文件到Supabase存储
        
        Args:
            product_id: 产品ID
            file: 文件对象
            file_type: 文件类型 ('image' 或 'pdf')
            
        Returns:
            上传成功返回公开URL，失败返回None
        """
        try:
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
            
            # 读取文件内容
            file.seek(0)  # 确保从文件开头读取
            file_content = file.read()
            
            if not file_content:
                raise ValueError("文件内容为空")
            
            # 上传到Supabase
            result = self.supabase.storage.from_(self.bucket_name).upload(
                path=filename,
                file=file_content,
                file_options={
                    "content-type": self._get_content_type(file_type, file_ext),
                    "upsert": True  # 如果文件已存在则覆盖
                }
            )
            
            # 检查上传结果
            if hasattr(result, 'error') and result.error:
                logger.error(f"Supabase上传错误: {result.error}")
                return None
            
            # 获取公开URL
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(filename)
            logger.info(f"文件上传成功: {filename} -> {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return None
    
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
    
    def delete_product_file(self, product_id: int, file_type: str) -> bool:
        """
        删除产品文件
        
        Args:
            product_id: 产品ID
            file_type: 文件类型 ('image' 或 'pdf')
            
        Returns:
            删除成功返回True，失败返回False
        """
        try:
            # 生成文件名
            if file_type == 'image':
                filename = f"product_{product_id}.jpg"
            elif file_type == 'pdf':
                filename = f"product_{product_id}.pdf"
            else:
                raise ValueError("文件类型必须是 'image' 或 'pdf'")
            
            # 删除文件
            result = self.supabase.storage.from_(self.bucket_name).remove([filename])
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Supabase删除错误: {result.error}")
                return False
            
            logger.info(f"文件删除成功: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return False

# 全局Supabase客户端实例
_supabase_client = None

def get_supabase_client() -> SupabaseStorageClient:
    """获取Supabase客户端单例"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseStorageClient()
    return _supabase_client